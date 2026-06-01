"""FSM detection matchers (DIA-05) — import-provenance-gated, stdlib-only.

Three explicit FSM families are detected deterministically over an ``ast.Module``
(RESEARCH §FSM Detection AST Patterns):

- **Family A** — ``transitions.Machine(...)`` library call: states + transitions
  from keyword args (list-of-dicts AND list-of-list forms). Detected only when
  ``Machine`` resolves via import-provenance to the ``transitions`` package.
- **Family B** — ``python-statemachine`` ``StateMachine``/``StateChart`` subclass:
  ``State()`` attrs + ``src.to(dst)`` transitions (event = LHS attr name),
  ``|``-combine into one event, ``target.from_(src)`` reverse form. Detected only
  when the class base resolves via import-provenance to ``statemachine``.
- **Family C** — native ``Enum``-typed state attr + literal
  ``self.<attr> = EnumClass.MEMBER`` reassignment. Family C REQUIRES BOTH an
  Enum-typed state attribute AND >=1 transition assignment — this is what makes a
  bare ``Color(Enum)`` a 0-FSM negative case (SC3).

D-10: the target libraries are NEVER imported — they are AST detection targets.
The import statements in user source are matched as provenance text only.

T-03-08 false-positive defense: a user's own ``Machine``/``State`` with NO
import of ``transitions``/``statemachine`` is NOT classified (mirrors the
contracts.py provenance trio). T-03-09: ``ast.literal_eval`` is used ONLY on
``ast.Constant`` nodes, never arbitrary AST.

Traces: DIA-05, US-25, US-32
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

__all__ = [
    "Transition",
    "MachineModel",
    "resolve_aliases",
    "detect_transitions_machine",
    "detect_python_statemachine",
    "detect_native_enum",
]

# Target packages for import-provenance (D-10 detection-only — NEVER imported).
_TRANSITIONS_PKGS: frozenset[str] = frozenset({"transitions"})
_STATEMACHINE_PKGS: frozenset[str] = frozenset({"statemachine", "python_statemachine"})
_STATEMACHINE_BASES: frozenset[str] = frozenset({"StateMachine", "StateChart"})


@dataclass
class Transition:
    """A single FSM transition (source state → target state, optional event)."""

    source: str
    target: str
    event: str = ""
    source_unresolved: bool = False


@dataclass
class MachineModel:
    """Detected FSM: ordered state names + transitions (pre-DET-04-sort)."""

    states: list[str] = field(default_factory=list)
    transitions: list[Transition] = field(default_factory=list)


def resolve_aliases(module: ast.Module, target_pkgs: frozenset[str]) -> dict[str, str]:
    """Build ``{local_name: imported_name}`` from ``from <target_pkg> import ...``.

    Mirrors contracts.py ``_resolve_decorator_aliases`` provenance discipline:
    only ``from <pkg>[.X] import ...`` where ``<pkg>`` (top segment) is in
    ``target_pkgs`` is in scope, so a same-name symbol from another library is
    never falsely classified (T-03-08).
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            top = mod.split(".")[0]
            if top in target_pkgs:
                for alias in node.names:
                    local = alias.asname or alias.name
                    aliases[local] = alias.name

    return aliases


def _imported_packages(module: ast.Module, target_pkgs: frozenset[str]) -> dict[str, str]:
    """Build ``{bound_name: package}`` from ``import <target_pkg>[ as alias]``."""
    bound: dict[str, str] = {}
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in target_pkgs:
                    bound[alias.asname or top] = top
    return bound


# ---------------------------------------------------------------------------
# Family A — transitions.Machine(...)
# ---------------------------------------------------------------------------
def _machine_call_has_provenance(
    call: ast.Call, name_aliases: dict[str, str], pkg_bound: dict[str, str]
) -> bool:
    """True iff this Call's func resolves to ``transitions.Machine`` by provenance."""
    func = call.func
    # Bare `Machine(...)` resolved via the `from <pkg>` name-alias map.
    if isinstance(func, ast.Name):
        return name_aliases.get(func.id) == "Machine"
    # Attribute `<pkg>.Machine(...)` resolved via the plain-import binding map.
    if isinstance(func, ast.Attribute) and func.attr == "Machine":
        base = func.value
        if isinstance(base, ast.Name):
            return base.id in pkg_bound
    return False


def _resolve_machine_kwargs(call: ast.Call) -> tuple[list[str], list[dict[str, str]]]:
    """Lift states + transitions from a Machine(...) call (literals only).

    Handles list-of-dicts ``{'trigger','source','dest'}`` AND list-of-lists
    ``[trigger, source, dest]``. Only ``ast.Constant`` str literals are
    resolvable (variables/comprehensions are statically undecidable → skipped).
    """
    states: list[str] = []
    transitions: list[dict[str, str]] = []
    for kw in call.keywords:
        if kw.arg == "states" and isinstance(kw.value, ast.List):
            for elt in kw.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    states.append(elt.value)
                elif isinstance(elt, ast.Dict):
                    for k, v in zip(elt.keys, elt.values):
                        if (
                            isinstance(k, ast.Constant)
                            and k.value == "name"
                            and isinstance(v, ast.Constant)
                            and isinstance(v.value, str)
                        ):
                            states.append(v.value)
        elif kw.arg == "transitions" and isinstance(kw.value, ast.List):
            for elt in kw.value.elts:
                if isinstance(elt, ast.Dict):
                    d: dict[str, str] = {}
                    for k, v in zip(elt.keys, elt.values):
                        if (
                            isinstance(k, ast.Constant)
                            and isinstance(k.value, str)
                            and isinstance(v, ast.Constant)
                            and isinstance(v.value, str)
                        ):
                            d[k.value] = v.value
                    if {"trigger", "source", "dest"} <= set(d):
                        transitions.append(d)
                elif isinstance(elt, ast.List) and len(elt.elts) >= 3:
                    vals = [
                        e.value
                        for e in elt.elts
                        if isinstance(e, ast.Constant) and isinstance(e.value, str)
                    ]
                    if len(vals) >= 3:
                        transitions.append({"trigger": vals[0], "source": vals[1], "dest": vals[2]})
    return states, transitions


def detect_transitions_machine(module: ast.Module) -> list[MachineModel]:
    """Family A: detect every provenance-resolved ``transitions.Machine(...)``."""
    name_aliases = resolve_aliases(module, _TRANSITIONS_PKGS)
    pkg_bound = _imported_packages(module, _TRANSITIONS_PKGS)
    if not name_aliases and not pkg_bound:
        return []  # no transitions import → no provenance → not an FSM.

    machines: list[MachineModel] = []
    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        if not _machine_call_has_provenance(node, name_aliases, pkg_bound):
            continue
        states, raw_trans = _resolve_machine_kwargs(node)
        model = MachineModel(states=list(states))
        seen = set(model.states)
        for d in raw_trans:
            src, dst = d["source"], d["dest"]
            for s in (src, dst):
                if s not in seen:
                    model.states.append(s)
                    seen.add(s)
            model.transitions.append(Transition(source=src, target=dst, event=d["trigger"]))
        machines.append(model)
    return machines


# ---------------------------------------------------------------------------
# Family B — python-statemachine StateMachine subclass
# ---------------------------------------------------------------------------
def _class_has_statemachine_base(
    class_node: ast.ClassDef, name_aliases: dict[str, str], pkg_bound: dict[str, str]
) -> bool:
    """True iff a base resolves to statemachine.StateMachine/StateChart."""
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            if name_aliases.get(base.id) in _STATEMACHINE_BASES:
                return True
        elif isinstance(base, ast.Attribute) and base.attr in _STATEMACHINE_BASES:
            inner = base.value
            if isinstance(inner, ast.Name) and inner.id in pkg_bound:
                return True
    return False


def _is_state_decl(value: ast.expr) -> bool:
    """True for ``State(...)`` call (the python-statemachine state declaration)."""
    if not isinstance(value, ast.Call):
        return False
    func = value.func
    if isinstance(func, ast.Name):
        return func.id == "State"
    if isinstance(func, ast.Attribute):
        return func.attr == "State"
    return False


def _to_transition(value: ast.expr) -> tuple[str, str] | None:
    """``src.to(dst)`` → (src, dst); ``dst.from_(src)`` → (src, dst) reverse."""
    if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)):
        return None
    attr = value.func.attr
    base = value.func.value
    if not (isinstance(base, ast.Name) and value.args and isinstance(value.args[0], ast.Name)):
        return None
    other = value.args[0].id
    if attr == "to":
        return base.id, other  # src.to(dst): source=base, target=arg
    if attr == "from_":
        return other, base.id  # dst.from_(src): source=arg, target=base
    return None


def _collect_to_transitions(value: ast.expr) -> list[tuple[str, str]]:
    """Flatten ``a.to(b) | a.to(c)`` BinOp combine into multiple (src, dst)."""
    if isinstance(value, ast.BinOp) and isinstance(value.op, ast.BitOr):
        return _collect_to_transitions(value.left) + _collect_to_transitions(value.right)
    single = _to_transition(value)
    return [single] if single is not None else []


def detect_python_statemachine(module: ast.Module) -> list[MachineModel]:
    """Family B: detect StateMachine subclasses (State() attrs + .to()/.from_())."""
    name_aliases = resolve_aliases(module, _STATEMACHINE_PKGS)
    pkg_bound = _imported_packages(module, _STATEMACHINE_PKGS)
    if not name_aliases and not pkg_bound:
        return []

    machines: list[MachineModel] = []
    for node in ast.walk(module):
        if not isinstance(node, ast.ClassDef):
            continue
        if not _class_has_statemachine_base(node, name_aliases, pkg_bound):
            continue
        model = MachineModel()
        seen: set[str] = set()
        for item in node.body:
            if not (isinstance(item, ast.Assign) and len(item.targets) == 1):
                continue
            target = item.targets[0]
            if not isinstance(target, ast.Name):
                continue
            if _is_state_decl(item.value):
                if target.id not in seen:
                    model.states.append(target.id)
                    seen.add(target.id)
            else:
                for src, dst in _collect_to_transitions(item.value):
                    model.transitions.append(Transition(source=src, target=dst, event=target.id))
        if model.states or model.transitions:
            machines.append(model)
    return machines


# ---------------------------------------------------------------------------
# Family C — native Enum-typed state attr + literal self.state = Enum.MEMBER
# ---------------------------------------------------------------------------
def _enum_classes(module: ast.Module) -> dict[str, list[str]]:
    """Map ``{EnumClassName: [member, ...]}`` for classes subclassing Enum."""
    enums: dict[str, list[str]] = {}
    for node in module.body:
        if not isinstance(node, ast.ClassDef):
            continue
        is_enum = any(
            (isinstance(b, ast.Name) and b.id == "Enum")
            or (isinstance(b, ast.Attribute) and b.attr == "Enum")
            for b in node.bases
        )
        if not is_enum:
            continue
        members: list[str] = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for t in item.targets:
                    if isinstance(t, ast.Name):
                        members.append(t.id)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                members.append(item.target.id)
        enums[node.name] = members
    return enums


def _literal_enum_assign(value: ast.expr, enum_names: frozenset[str]) -> str | None:
    """``EnumClass.MEMBER`` literal → MEMBER name, when EnumClass is a known Enum."""
    if (
        isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Name)
        and value.value.id in enum_names
    ):
        return value.attr
    return None


def detect_native_enum(module: ast.Module) -> list[MachineModel]:
    """Family C: Enum state attr + literal ``self.<attr> = EnumClass.MEMBER``.

    REQUIRES BOTH a known Enum class AND >=1 literal transition assignment — a
    bare ``Color(Enum)`` with no reassignment yields ZERO state machines (SC3).
    Non-literal ``self.<attr> = self._next()`` forms are left for the DIA-06
    return-value-substitution pass (Task 3) and produce no states here.
    """
    enums = _enum_classes(module)
    if not enums:
        return []
    enum_names = frozenset(enums)

    machines: list[MachineModel] = []
    for node in module.body:
        if not isinstance(node, ast.ClassDef):
            continue
        model = MachineModel()
        seen: set[str] = set()
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Assign):
                continue
            for tgt in sub.targets:
                if not (
                    isinstance(tgt, ast.Attribute)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "self"
                ):
                    continue
                member = _literal_enum_assign(sub.value, enum_names)
                if member is None:
                    continue
                if member not in seen:
                    model.states.append(member)
                    seen.add(member)
                model.transitions.append(Transition(source="", target=member, event=tgt.attr))
        # Family C requires at least one literal transition assignment.
        if model.transitions:
            machines.append(model)
    return machines
