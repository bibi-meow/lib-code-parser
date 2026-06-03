r"""D-04 C++ package diagram extractor (namespace nesting -> packages).

The C++ analog of ``evaluations/package_diagram.py`` (LNG-04 parity). C++ packages
are derived primarily from NAMESPACE nesting (RESEARCH §package mapping): each
``namespace`` cursor in the main file becomes one ``GraphNode(node_type="package")``
whose ``node_id`` is the dotted qualified namespace path (``a``, ``a.b``) produced
by the shared ``_cpp_cursor.qualified_node_id``.

Containment is expressed via ``GraphNode.attributes={"parent_package": parent}``
(the D-01 sub-decision: NO ``contains`` edge — identical to the Python sibling).
``parent`` is the dotted prefix up to the last segment, absent for a top-level
namespace.

DET-04: nodes sorted by ``node_id`` on exit. ``dict.fromkeys`` gives ordered
dedup before sorting.

Implements: LNG-04
Traces: LNG-04, US-25, US-32
"""

from __future__ import annotations

import clang.cindex
from clang.cindex import CursorKind

from lib_code_parser import _cpp_cursor
from lib_code_parser.models.evaluations.graph_base import GraphModel, GraphNode
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """LNG-04 / DET-04: emit a package GraphModel (namespace packages + containment).

    Each main-file NAMESPACE cursor becomes one ``package`` node; containment is
    carried on each node's ``attributes["parent_package"]`` (no ``contains``
    edge). Asserts a TranslationUnit payload and NEVER branches on
    ``cav.language`` (invariant #2).
    """
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit), (
        "cpp_package_diagram extractor requires C++ CAV (TranslationUnit payload), "
        f"got {type(tu).__name__}"
    )
    path = cav.path

    pkg_ids: list[str] = []
    for cursor in tu.cursor.walk_preorder():
        if cursor.kind != CursorKind.NAMESPACE:
            continue
        if not _cpp_cursor._in_main_file(cursor, path):
            continue
        if not cursor.spelling:
            continue  # anonymous namespace -> no package id
        pkg_ids.append(_cpp_cursor.qualified_node_id(cursor))

    pkg_ids = list(dict.fromkeys(pkg_ids))

    nodes: list[GraphNode] = []
    for pkg_id in pkg_ids:
        parent = pkg_id.rsplit(".", 1)[0] if "." in pkg_id else ""
        attributes = {"parent_package": parent} if parent else {}
        nodes.append(
            GraphNode(
                node_id=pkg_id,
                node_type="package",
                label=pkg_id.rsplit(".", 1)[-1],
                attributes=attributes,
            )
        )

    # DET-04 sort-on-exit.
    nodes.sort(key=lambda n: n.node_id)

    return GraphModel(nodes=nodes)
