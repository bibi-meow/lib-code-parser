r"""D-04 C++ class diagram extractor (inheritance + composes/aggregates/associates).

The C++ analog of ``evaluations/class_diagram.py`` (LNG-04 parity): emits a
verifier-facing ``GraphModel`` from the cpp CAV's ``clang.cindex.TranslationUnit``
payload with the SAME ``GraphNode``/``GraphEdge`` slots as the Python sibling.

- ``GraphNode(node_type="class")`` per main-file CLASS_DECL / STRUCT_DECL.
- one ``inherits`` edge per ``CXX_BASE_SPECIFIER`` child (multiple inheritance =>
  multiple edges — RESEARCH verified).
- composes / aggregates / associates edges from each ``FIELD_DECL`` via the
  shared ``_cpp_cursor.field_relation`` classifier (value member of a known class
  -> composes; pointer/reference of a known class -> aggregates; unknown type ->
  associates the explicit undecidable fallback; builtin primitive -> no edge).

D-03: ``edge_type`` keeps THIS lib's own vocabulary (inherits / composes /
aggregates / associates) — never renamed to the sibling lib-diagram-parser
spelling, and NEVER a catch-all ``"uses"`` / ``"other"`` (T-04-12: a fabricated
value would fail the closed EdgeKind Literal at construction). ``"associates"``
is the explicit undecidable fallback, not a catch-all.

DET-04: nodes sorted by ``node_id``; edges sorted by
``(source, target, edge_type, label)`` on exit -> byte-identical across
libclang's nondeterministic cursor-traversal order. ``dict.fromkeys`` gives
ordered dedup before sorting.

Implements: LNG-04
Traces: LNG-04, US-25, US-32
"""

from __future__ import annotations

import clang.cindex
from clang.cindex import Cursor, CursorKind

from lib_code_parser import _cpp_cursor
from lib_code_parser.models.evaluations.graph_base import GraphEdge, GraphModel, GraphNode
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]

_CLASS_KINDS = (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL)


def _collect_known_classes(tu_cursor: Cursor, path: str) -> set[str]:
    """Main-file class/struct spellings (the resolvable-as-edge-target set).

    Mirrors the Python ``class_diagram._collect_known_classes`` role: a relation
    edge target is a known class only when it is declared in the parsed main
    file (Pitfall 3 main-file filter). Unknown targets become ``associates``.
    """
    known: set[str] = set()
    for cursor in tu_cursor.walk_preorder():
        if cursor.kind in _CLASS_KINDS and _cpp_cursor._in_main_file(cursor, path):
            if cursor.spelling:
                known.add(cursor.spelling)
    return known


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """LNG-04 / DET-04: emit a class GraphModel (class nodes + relationship edges).

    Inheritance from ``CXX_BASE_SPECIFIER`` children; composition/aggregation/
    association from ``FIELD_DECL`` member types via ``_cpp_cursor.field_relation``.
    Known-class resolution is structural over the main-file CLASS/STRUCT decls.
    Asserts a TranslationUnit payload and NEVER branches on ``cav.language``
    (invariant #2).
    """
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit), (
        "cpp_class_diagram extractor requires C++ CAV (TranslationUnit payload), "
        f"got {type(tu).__name__}"
    )
    path = cav.path
    known = _collect_known_classes(tu.cursor, path)

    node_ids: list[str] = []
    edges: list[GraphEdge] = []

    for cursor in tu.cursor.walk_preorder():
        if cursor.kind not in _CLASS_KINDS:
            continue
        if not _cpp_cursor._in_main_file(cursor, path):
            continue
        if not cursor.spelling:
            continue
        class_id = cursor.spelling
        node_ids.append(class_id)

        for child in cursor.get_children():
            # Inheritance: one edge per base specifier (multiple inheritance =>
            # multiple CXX_BASE_SPECIFIER children).
            if child.kind == CursorKind.CXX_BASE_SPECIFIER:
                base_name = child.spelling.replace("class ", "").replace("struct ", "")
                base_name = base_name.split("::")[-1].strip()
                if base_name:
                    edges.append(GraphEdge(source=class_id, target=base_name, edge_type="inherits"))
            # Relationship edges from member fields.
            elif child.kind == CursorKind.FIELD_DECL:
                relation = _cpp_cursor.field_relation(child, known)
                if relation is None:
                    continue  # builtin primitive member -> no edge
                edge_type, target = relation
                edges.append(
                    GraphEdge(source=class_id, target=target, edge_type=edge_type)  # type: ignore[arg-type]
                )

    node_ids = list(dict.fromkeys(node_ids))
    nodes = [GraphNode(node_id=nid, node_type="class", label=nid) for nid in node_ids]

    # DET-04 sort-on-exit with stable composite keys.
    nodes.sort(key=lambda n: n.node_id)
    edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))

    return GraphModel(nodes=nodes, edges=edges)
