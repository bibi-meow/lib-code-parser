"""DIA-06 return-value substitution (N-level, cycle-safe) over native-Enum FSMs.

When a transition assigns a NON-literal value — ``self.state = self._next()`` —
the explicit native-Enum matcher (``_fsm_detect.detect_native_enum``) cannot
resolve the target, because the assigned value is a method call rather than a
literal ``EnumClass.MEMBER``. This module resolves the callee's return
statements intra-class to recover the concrete target state(s).

Algorithm (RESEARCH §Return-Value Substitution Algorithm, deterministic,
intra-procedural, N-level recursive, cycle-safe):

1. **Resolve callee**: ``self._next()`` → look up method ``_next`` in the *same
   class* (intra-class only; cross-class/external = unresolvable).
2. **Collect returns**: walk the callee body for ``ast.Return`` nodes.
   - ``return EnumClass.MEMBER`` / ``ast.Constant`` → resolved literal state.
   - ``return self._other()`` → recurse with a ``visited: set[str]`` of method
     names (cycle detection — re-entry stops that branch).
   - conditional / ternary / variable → unresolved fragment.
3. **Cycle detection**: a ``visited`` set of method names guarantees
   termination; recursion is additionally bounded by the finite method count
   (T-03-07 DoS mitigation — the phase's one real recursion vector).
4. **Emit**:
   - Fully resolved (every path → a literal) → one concrete ``transitions_to``
     edge per distinct resolved target.
   - Unresolvable (any path can't reduce, or callee external/not-in-class) →
     exactly ONE placeholder ``GraphEdge`` with ``source_unresolved=True`` (the
     Plan 01 marker home — GraphEdge has no ``attributes`` field).

Traces: DIA-06, DET-04
"""

from __future__ import annotations

import ast

from lib_code_parser.models.evaluations.graph_base import GraphEdge

__all__ = ["resolve_substitution_edges"]


def _enum_class_names(module: ast.Module) -> frozenset[str]:
    """Names of classes that subclass Enum (the resolvable-literal targets)."""
    names: set[str] = set()
    for node in module.body:
        if isinstance(node, ast.ClassDef) and any(
            (isinstance(b, ast.Name) and b.id == "Enum")
            or (isinstance(b, ast.Attribute) and b.attr == "Enum")
            for b in node.bases
        ):
            names.add(node.name)
    return frozenset(names)


def _self_method_call(value: ast.expr) -> str | None:
    """``self._method()`` → method name; else None."""
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and isinstance(value.func.value, ast.Name)
        and value.func.value.id == "self"
        and not value.args
    ):
        return value.func.attr
    return None


def _external_call_label(call: ast.Call) -> str:
    """Deterministic label for an unresolvable external call's placeholder edge."""
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return "unresolved"


def _literal_enum_member(value: ast.expr, enum_names: frozenset[str]) -> str | None:
    """``EnumClass.MEMBER`` → MEMBER (when EnumClass is a known Enum); else None."""
    if (
        isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Name)
        and value.value.id in enum_names
    ):
        return value.attr
    return None


def _class_methods(class_node: ast.ClassDef) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Map ``{method_name: FunctionDef}`` for the class's own methods."""
    methods: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[item.name] = item
    return methods


def _resolve_method_returns(
    method_name: str,
    methods: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    enum_names: frozenset[str],
    visited: set[str],
) -> tuple[list[str], bool]:
    """Resolve a method's return targets intra-class.

    Returns ``(resolved_literals, fully_resolved)``:
      • ``resolved_literals`` — distinct literal state names reachable via returns
        (ordered by first appearance, deduped).
      • ``fully_resolved`` — True iff EVERY return path reduced to a literal (no
        unresolved fragment, no external/missing callee, no cycle dead-end).
    """
    if method_name in visited:
        # Cycle re-entry — this branch yields no new literal and is not a
        # "fully resolved" success (the cycle path can't reduce to a literal).
        return [], False
    method = methods.get(method_name)
    if method is None:
        # External / not-in-class callee → unresolvable.
        return [], False

    visited = visited | {method_name}
    literals: list[str] = []
    seen: set[str] = set()
    fully_resolved = True
    saw_return = False

    for node in ast.walk(method):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        saw_return = True
        value = node.value

        member = _literal_enum_member(value, enum_names)
        if member is not None:
            if member not in seen:
                literals.append(member)
                seen.add(member)
            continue

        callee = _self_method_call(value)
        if callee is not None:
            sub_literals, sub_full = _resolve_method_returns(callee, methods, enum_names, visited)
            for lit in sub_literals:
                if lit not in seen:
                    literals.append(lit)
                    seen.add(lit)
            if not sub_full:
                fully_resolved = False
            continue

        # Conditional / variable / other expr → unresolved fragment.
        fully_resolved = False

    if not saw_return:
        fully_resolved = False
    return literals, fully_resolved


def resolve_substitution_edges(module: ast.Module) -> tuple[list[str], list[GraphEdge]]:
    """Return (extra_state_ids, extra_edges) from non-literal state mutations.

    For each ``self.<attr> = self._method()`` (non-literal Call) inside a class,
    resolve ``_method`` intra-class. Fully resolved → concrete edges to each
    literal target; otherwise → exactly one ``source_unresolved=True`` placeholder.
    """
    enum_names = _enum_class_names(module)
    if not enum_names:
        return [], []

    extra_states: list[str] = []
    extra_edges: list[GraphEdge] = []
    seen_states: set[str] = set()

    for class_node in module.body:
        if not isinstance(class_node, ast.ClassDef):
            continue
        methods = _class_methods(class_node)

        # CR-02: scan only THIS class's direct method bodies. A full
        # ast.walk(class_node) descends into nested ClassDefs, so an inner
        # class's `self.state = self._compute()` would resolve `_compute`
        # against the OUTER class's methods dict (a different `self`),
        # emitting a phantom resolved/placeholder edge for the outer class.
        method_nodes = (
            node
            for method in methods.values()
            for node in ast.walk(method)
        )
        for node in method_nodes:
            if not isinstance(node, ast.Assign):
                continue
            # Target must be `self.<attr> = ...`.
            is_self_attr = any(
                isinstance(t, ast.Attribute)
                and isinstance(t.value, ast.Name)
                and t.value.id == "self"
                for t in node.targets
            )
            if not is_self_attr:
                continue
            # Only non-literal Call RHS triggers substitution. Literal
            # `self.state = Enum.MEMBER` forms are handled by detect_native_enum;
            # non-Call RHS (variables, etc.) are not state transitions here.
            if not isinstance(node.value, ast.Call):
                continue
            if _literal_enum_member(node.value, enum_names) is not None:
                continue  # (Call that is somehow a literal member — defensive.)

            callee = _self_method_call(node.value)
            if callee is not None:
                literals, fully_resolved = _resolve_method_returns(
                    callee, methods, enum_names, set()
                )
            else:
                # Non-self call (e.g. `helper.compute()`) → external → unresolvable.
                literals, fully_resolved = [], False

            if fully_resolved and literals:
                for lit in literals:
                    if lit not in seen_states:
                        extra_states.append(lit)
                        seen_states.add(lit)
                    extra_edges.append(GraphEdge(source="", target=lit, edge_type="transitions_to"))
            else:
                # Unresolvable → exactly ONE placeholder edge (DIA-06 contract).
                placeholder_target = (
                    callee if callee is not None else _external_call_label(node.value)
                )
                extra_edges.append(
                    GraphEdge(
                        source="",
                        target=placeholder_target,
                        edge_type="transitions_to",
                        source_unresolved=True,
                    )
                )

    return extra_states, extra_edges
