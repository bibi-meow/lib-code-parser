r"""D-04 C++ component diagram extractor (module boundaries + #include edges).

The C++ analog of ``evaluations/component_diagram.py`` (LNG-04 parity). Pulls the
cpp ``cpp_type_deps`` primitive directly (pull-a-primitive, invariant #5 — its
OWN primitive, NOT the Python ``type_deps``) and keeps only the
``kind=="imports"`` facts (one per ``#include`` directive). Each becomes one
``imports`` edge from the importing module to the included header name; every
distinct module/header becomes a ``GraphNode(node_type="component")``.

D-03: edges keep this lib's own ``imports`` vocabulary — never renamed to the
sibling spelling, never a catch-all ``"uses"``/``"depends"``/``"other"``.

DET-04: nodes sorted by ``node_id``; edges sorted by
``(source, target, edge_type, label)`` on exit. ``dict.fromkeys`` gives ordered
dedup before sorting.

Implements: LNG-04
Traces: LNG-04, US-25, US-32
"""

from __future__ import annotations

import clang.cindex

from lib_code_parser._paths import get_module_name
from lib_code_parser.extractors.primitives import cpp_type_deps
from lib_code_parser.models.evaluations.graph_base import GraphEdge, GraphModel, GraphNode
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """LNG-04 / DET-04: emit a component GraphModel (module nodes + import edges).

    Pull the cpp ``cpp_type_deps`` primitive and keep only ``kind=="imports"``
    facts (the ``#include`` directives). Asserts a TranslationUnit payload and
    NEVER branches on ``cav.language`` (invariant #2).
    """
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit), (
        "cpp_component_diagram extractor requires C++ CAV (TranslationUnit payload), "
        f"got {type(tu).__name__}"
    )
    module_name = get_module_name(cav.path)

    tds = cpp_type_deps.extract(cav, config)
    import_deps = [td for td in tds if td.kind == "imports"]

    node_ids: list[str] = [module_name]
    for td in import_deps:
        node_ids.append(td.target)
    node_ids = list(dict.fromkeys(node_ids))

    nodes = [GraphNode(node_id=nid, node_type="component", label=nid) for nid in node_ids]
    edges = [
        GraphEdge(source=td.source, target=td.target, edge_type="imports") for td in import_deps
    ]

    # DET-04 sort-on-exit with stable composite keys.
    nodes.sort(key=lambda n: n.node_id)
    edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))

    return GraphModel(nodes=nodes, edges=edges)
