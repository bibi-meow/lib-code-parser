"""DIA-01 class diagram extractor (inheritance + composition/aggregation/association).

Emits ``GraphNode(node_type="class")`` per ClassDef and four edge kinds derived
purely from type annotations (py2puml-style annotation-only rule — assigned
values are never evaluated):

- ``class B(A)`` → ``inherits`` edge B → A.
- ``x: Engine`` (direct known class) → ``composes`` (owned, lifetime-bound).
- ``y: Optional[Engine]`` / ``z: list[Engine]`` / ``X | None`` → ``aggregates``
  (has-a, no lifetime) over the inner known class.
- ``w: Unknown`` / ``Any`` / TypeVar / unresolved forward ref → ``associates``
  (the undecidable fallback — NEVER a catch-all ``uses`` edge).
- ``n: int`` / ``s: str`` (builtin/primitive) → NO edge (a plain field, skipped).

D-03: edges keep this lib's own vocabulary (inherits / composes / aggregates /
associates); they are NOT renamed to the sibling lib-diagram-parser spelling
(``inheritance`` / ``dependency``). The verifier resolves the physical↔logical
vocabulary gap.

"Known class" resolution is structural (T-03-03): the inner annotation name must
be a ClassDef in this module OR an imported class-like name. Unknown names are
``associates`` (explicit), never a fabricated edge and never silently dropped.

DET-04: nodes sorted by ``node_id``; edges sorted by
``(source, target, edge_type, label)`` on exit → byte-identical across
PYTHONHASHSEED.

Implements: DIA-01, DIA-07
Traces: DIA-01, DIA-07, US-25, US-32
"""

from __future__ import annotations

import ast
import re

from lib_code_parser._paths import get_module_name
from lib_code_parser.models.evaluations.graph_base import GraphEdge, GraphModel, GraphNode
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]

# Container subscript names whose inner element type is an AGGREGATION (has-a,
# no shared lifetime). Optional is included: Optional[X] is has-a-or-nothing.
_AGGREGATING_CONTAINERS: frozenset[str] = frozenset(
    {
        "Optional",
        "list",
        "List",
        "set",
        "Set",
        "frozenset",
        "FrozenSet",
        "dict",
        "Dict",
        "tuple",
        "Tuple",
        "Sequence",
        "Iterable",
        "Mapping",
    }
)

# Builtin / primitive annotation names that are plain fields, never edges.
_PRIMITIVE_NAMES: frozenset[str] = frozenset(
    {"int", "str", "float", "bool", "bytes", "complex", "None", "Any", "object"}
)

# WR-06: typing special forms that are NOT classes — they must never produce a
# composes/associates edge (e.g. `x: ClassVar`, `y: Type`). The aggregating
# container forms (Optional/Union/List/...) are handled by the subscript path
# in _AGGREGATING_CONTAINERS; these are the non-container typing names that
# would otherwise leak through the bare-Name / Attribute branches.
_TYPING_NAMES: frozenset[str] = frozenset(
    {
        "Type",
        "ClassVar",
        "Final",
        "Annotated",
        "TypeVar",
        "Protocol",
        "Callable",
        "Awaitable",
        "Generator",
        "AsyncGenerator",
        "ContextManager",
        "AsyncContextManager",
        "Generic",
        "NoReturn",
        "Never",
        "Self",
    }
)


def _collect_known_classes(tree: ast.Module, module_name: str) -> set[str]:
    """Class-like names resolvable in this module (ClassDefs + imported classes).

    Imported names are admitted when they look class-like (uppercase first
    letter — v0.1.0 type_deps heuristic) so cross-module composition resolves
    without guessing arbitrary names (T-03-03 structural resolution).
    """
    known: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            known.add(node.name)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local = alias.asname or alias.name
                if local and local[0].isupper():
                    known.add(local)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name
                # `import pkg.Thing` → local top segment; rarely class-like.
                top = local.split(".")[0]
                if top and top[0].isupper():
                    known.add(top)
    return known


def _classify_name(name: str, known: set[str]) -> list[tuple[str, str]]:
    """Classify a single resolved identifier into zero or one edge.

      • builtin / primitive / typing special form → [] (plain field, no edge)
      • direct known class                         → [("composes", name)]
      • undecidable / unknown name                 → [("associates", name)]
    """
    if name in _PRIMITIVE_NAMES or name in _TYPING_NAMES:
        return []
    if name in known:
        return [("composes", name)]
    return [("associates", name)]


def _classify_annotation(annotation: ast.expr, known: set[str]) -> list[tuple[str, str]]:
    """Return the list of (edge_type, target_class) edges for an annotation.

    Decision rule (RESEARCH §composition-vs-aggregation):
      • direct known class            → [("composes", name)]
      • Optional[X] / X | None / list[X] / set[X] / dict[K,V] of a known class
                                       → [("aggregates", inner)]
      • X | Y union of classes        → one edge per resolvable operand (WR-03)
      • builtin / primitive / typing   → [] (plain field, no edge)
      • undecidable / unknown name    → [("associates", name)]
    """
    # Direct name: `x: Engine` or `n: int`.
    if isinstance(annotation, ast.Name):
        return _classify_name(annotation.id, known)

    # Forward-ref string: `w: "Engine"` / `w: "list[Engine] | None"`.
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        inner = annotation.value.strip()
        return _classify_annotation_from_text(inner, known)

    # `X | None` / `X | Y` union.
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return _classify_union(annotation, known)

    # Subscript: Optional[X] / list[X] / dict[K, V] / etc.
    if isinstance(annotation, ast.Subscript):
        return _classify_subscript(annotation, known)

    # Attribute form `mod.Engine`: use the attribute name.
    if isinstance(annotation, ast.Attribute):
        return _classify_name(annotation.attr, known)

    # Anything else (Tuple-of-types without subscript, complex exprs) → skip
    # rather than fabricate an edge.
    return []


def _classify_text_token(
    token: str, known: set[str], *, in_union: bool
) -> list[tuple[str, str]]:
    """Classify one token from a forward-ref string, handling `container[Inner]`.

    CR-04: a string forward-ref like ``"list[Engine]"`` must extract the inner
    class ``Engine`` (→ aggregates), not emit the literal composite string.

    ``in_union``: a token that is one operand of a ``|`` union is has-a
    (Optional-equivalent), so a bare known class resolves to ``aggregates``
    rather than ``composes`` (parity with the AST union path and v0.1.0).
    """
    token = token.strip()
    if not token or token == "None" or token in _PRIMITIVE_NAMES or token in _TYPING_NAMES:
        return []
    base = token.split("[", 1)[0].strip()
    if "[" in token and base in _AGGREGATING_CONTAINERS:
        inner = token[len(base):].strip().lstrip("[").rstrip("]").strip()
        # Inner may itself be a union or comma list — take the first resolvable.
        for piece in re.split(r"[|,]", inner):
            piece = piece.strip()
            if not piece or piece == "None" or piece in _PRIMITIVE_NAMES:
                continue
            inner_base = piece.split("[", 1)[0].strip()
            if inner_base in known:
                return [("aggregates", inner_base)]
            if inner_base and inner_base not in _TYPING_NAMES:
                return [("associates", inner_base)]
        return []
    # Non-aggregating subscript or bare name: classify by the base identifier.
    if base in known:
        # Bare known class: composes for a direct forward-ref, aggregates when
        # it is a union operand or carries a subscript (has-a semantics).
        aggregating = in_union or "[" in token
        return [("aggregates" if aggregating else "composes", base)]
    if base in _PRIMITIVE_NAMES or base in _TYPING_NAMES:
        return []
    return [("associates", base)]


def _classify_annotation_from_text(text: str, known: set[str]) -> list[tuple[str, str]]:
    """Classify a forward-ref string annotation (handles unions + subscripts)."""
    # `Wheel | None` / `Engine | Wheel` inside a string → one edge per operand.
    if "|" in text:
        results: list[tuple[str, str]] = []
        for part in text.split("|"):
            results.extend(_classify_text_token(part, known, in_union=True))
        return results
    return _classify_text_token(text, known, in_union=False)


def _classify_union(node: ast.BinOp, known: set[str]) -> list[tuple[str, str]]:
    """`X | None` / `X | Y` → one ``aggregates``/``associates`` edge per operand.

    A union is has-a (no shared lifetime) → ``aggregates`` for known classes.
    WR-03: ALL non-None, non-primitive operands produce an edge (previously
    only the first operand was emitted, silently dropping ``Wheel`` in
    ``Engine | Wheel``).
    """
    operands: list[ast.expr] = []

    def _flatten(expr: ast.expr) -> None:
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.BitOr):
            _flatten(expr.left)
            _flatten(expr.right)
        else:
            operands.append(expr)

    _flatten(node)
    results: list[tuple[str, str]] = []
    for operand in operands:
        name = _name_of(operand)
        if name is None or name == "None" or name in _PRIMITIVE_NAMES or name in _TYPING_NAMES:
            continue
        results.append(("aggregates" if name in known else "associates", name))
    return results


def _classify_subscript(node: ast.Subscript, known: set[str]) -> list[tuple[str, str]]:
    """Optional[X] / list[X] / dict[K, V] → aggregates the inner known class."""
    container = _name_of(node.value)
    if container not in _AGGREGATING_CONTAINERS:
        # Unknown generic / parametrized unknown → undecidable → associates by
        # the container name (do not fabricate composition).
        if (
            container is not None
            and container not in _PRIMITIVE_NAMES
            and container not in _TYPING_NAMES
        ):
            return [("composes" if container in known else "associates", container)]
        return []

    inner_names = _subscript_inner_names(node.slice)
    for name in inner_names:
        if name in (None, "None") or name in _PRIMITIVE_NAMES:
            continue
        if name in known:
            return [("aggregates", name)]
    # Container of unknown / builtin only → undecidable: associate the first
    # non-primitive unknown if present, else skip.
    for name in inner_names:
        if name and name != "None" and name not in _PRIMITIVE_NAMES:
            return [("associates", name)]
    return []


def _subscript_inner_names(slice_node: ast.expr) -> list[str | None]:
    """Extract candidate type names from a subscript slice (handles Tuple)."""
    if isinstance(slice_node, ast.Tuple):
        return [_name_of(elt) for elt in slice_node.elts]
    return [_name_of(slice_node)]


def _name_of(expr: ast.expr) -> str | None:
    """Leading identifier of a type expression (Name.id / Attribute.attr / str)."""
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value.strip()
    if isinstance(expr, ast.Subscript):
        return _name_of(expr.value)
    return None


def _class_attr_annotations(class_node: ast.ClassDef) -> list[ast.expr]:
    """Declared instance-attribute annotations: class-body + __init__ self.x: T."""
    annotations: list[ast.expr] = []
    # (1) class-body annotated assignments: `x: T` (with or without value).
    for item in class_node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            annotations.append(item.annotation)
    # (2) __init__ self-attribute annotations: `self.x: T = ...`.
    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
            for stmt in ast.walk(item):
                if (
                    isinstance(stmt, ast.AnnAssign)
                    and isinstance(stmt.target, ast.Attribute)
                    and isinstance(stmt.target.value, ast.Name)
                    and stmt.target.value.id == "self"
                ):
                    annotations.append(stmt.annotation)
    return annotations


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """DIA-01: emit a class GraphModel (class nodes + relationship edges) from cav.

    Inheritance from ``ClassDef.bases``; composition/aggregation/association from
    declared instance-attribute type annotations (class-body AnnAssign + __init__
    self-attribute AnnAssign). Known-class resolution is structural over the
    module's ClassDefs + imported class-like names.
    """
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"class_diagram extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )
    module_name = get_module_name(cav.path)
    known = _collect_known_classes(tree, module_name)

    node_ids: list[str] = []
    edges: list[GraphEdge] = []

    for class_node in tree.body:
        if not isinstance(class_node, ast.ClassDef):
            continue
        class_name = class_node.name
        node_ids.append(class_name)

        # Inheritance edges from bases (Name / Attribute forms).
        for base in class_node.bases:
            base_name = _name_of(base)
            if base_name and base_name != "object":
                edges.append(GraphEdge(source=class_name, target=base_name, edge_type="inherits"))

        # Relationship edges from declared attribute annotations. One annotation
        # may yield multiple edges (e.g. a `X | Y` union — WR-03).
        for annotation in _class_attr_annotations(class_node):
            for edge_type, target in _classify_annotation(annotation, known):
                edges.append(
                    GraphEdge(source=class_name, target=target, edge_type=edge_type)  # type: ignore[arg-type]
                )

    node_ids = list(dict.fromkeys(node_ids))
    nodes = [GraphNode(node_id=nid, node_type="class", label=nid) for nid in node_ids]

    # DET-04 sort-on-exit with stable composite keys.
    nodes.sort(key=lambda n: n.node_id)
    edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))

    return GraphModel(nodes=nodes, edges=edges)
