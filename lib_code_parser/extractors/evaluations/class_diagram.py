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


def _classify_annotation(annotation: ast.expr, known: set[str]) -> tuple[str, str] | None:
    """Return (edge_type, target_class) for an annotation, or None to skip.

    Decision rule (RESEARCH §composition-vs-aggregation):
      • direct known class            → ("composes", name)
      • Optional[X] / X | None / list[X] / set[X] / dict[K,V] of a known class
                                       → ("aggregates", inner)
      • builtin / primitive           → None (plain field, no edge)
      • undecidable / unknown name    → ("associates", name)
    """
    # Direct name: `x: Engine` or `n: int`.
    if isinstance(annotation, ast.Name):
        name = annotation.id
        if name in _PRIMITIVE_NAMES:
            return None
        if name in known:
            return "composes", name
        # Unknown bare name → undecidable → association fallback.
        return "associates", name

    # Forward-ref string: `w: "Engine"` / `w: "Unknown"`.
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
        name = annotation.attr
        if name in _PRIMITIVE_NAMES:
            return None
        if name in known:
            return "composes", name
        return "associates", name

    # Anything else (Tuple-of-types without subscript, complex exprs) → skip
    # rather than fabricate an edge.
    return None


def _classify_annotation_from_text(text: str, known: set[str]) -> tuple[str, str] | None:
    """Classify a forward-ref string annotation by its leading identifier."""
    # `Wheel | None` inside a string.
    if "|" in text:
        for part in (p.strip() for p in text.split("|")):
            if part and part != "None" and part not in _PRIMITIVE_NAMES:
                if part in known:
                    return "aggregates", part
                return "associates", part
        return None
    if text in _PRIMITIVE_NAMES:
        return None
    if text in known:
        return "composes", text
    return "associates", text


def _classify_union(node: ast.BinOp, known: set[str]) -> tuple[str, str] | None:
    """`X | None` / `X | Y` → aggregates the first non-None known class.

    A union with None (Optional-equivalent) is has-a → aggregates. The inner
    class is the first non-None operand.
    """
    operands: list[ast.expr] = []

    def _flatten(expr: ast.expr) -> None:
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.BitOr):
            _flatten(expr.left)
            _flatten(expr.right)
        else:
            operands.append(expr)

    _flatten(node)
    for operand in operands:
        name = _name_of(operand)
        if name is None or name == "None" or name in _PRIMITIVE_NAMES:
            continue
        if name in known:
            return "aggregates", name
        return "associates", name
    return None


def _classify_subscript(node: ast.Subscript, known: set[str]) -> tuple[str, str] | None:
    """Optional[X] / list[X] / dict[K, V] → aggregates the inner known class."""
    container = _name_of(node.value)
    if container not in _AGGREGATING_CONTAINERS:
        # Unknown generic / parametrized unknown → undecidable → associates by
        # the container name (do not fabricate composition).
        if container is not None and container not in _PRIMITIVE_NAMES:
            if container in known:
                return "composes", container
            return "associates", container
        return None

    inner_names = _subscript_inner_names(node.slice)
    for name in inner_names:
        if name in (None, "None") or name in _PRIMITIVE_NAMES:
            continue
        if name in known:
            return "aggregates", name
    # Container of unknown / builtin only → undecidable: associate the first
    # non-primitive unknown if present, else skip.
    for name in inner_names:
        if name and name != "None" and name not in _PRIMITIVE_NAMES:
            return "associates", name
    return None


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

        # Relationship edges from declared attribute annotations.
        for annotation in _class_attr_annotations(class_node):
            classified = _classify_annotation(annotation, known)
            if classified is None:
                continue
            edge_type, target = classified
            edges.append(
                GraphEdge(source=class_name, target=target, edge_type=edge_type)  # type: ignore[arg-type]
            )

    node_ids = list(dict.fromkeys(node_ids))
    nodes = [GraphNode(node_id=nid, node_type="class", label=nid) for nid in node_ids]

    # DET-04 sort-on-exit with stable composite keys.
    nodes.sort(key=lambda n: n.node_id)
    edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))

    return GraphModel(nodes=nodes, edges=edges)
