"""DIA-03 component diagram extractor (module boundaries + import edges).

The closest exact analog in the codebase: this consumes the ``kind=="imports"``
TypeDeps that ``extractors/primitives/type_deps.extract`` already emits (one per
``import X`` / ``from M import N``) and maps each to a
``GraphEdge(edge_type="imports", source=module, target="X"|"M.N")``. Modules
become ``GraphNode(node_type="component")``.

D-03: edges keep this lib's own ``imports`` vocabulary — they are NOT renamed to
the sibling lib-diagram-parser spelling (``dependency``). The physical↔logical
vocabulary gap is resolved by the verifier, not by this extractor. Pitfall 2:
no catch-all ``uses`` / ``depends`` / ``other`` edge is ever emitted.

DET-04: nodes sorted by ``node_id``; edges sorted by
``(source, target, edge_type, label)`` on exit → byte-identical across
PYTHONHASHSEED. ``dict.fromkeys`` gives ordered dedup before sorting.

Implements: DIA-03, DIA-07
Traces: DIA-03, DIA-07, US-25, US-32
"""

from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name
from lib_code_parser.extractors.primitives import type_deps
from lib_code_parser.models.evaluations.graph_base import GraphEdge, GraphModel, GraphNode
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """DIA-03: emit a component GraphModel (module nodes + import edges) from cav.

    Pull the Phase 2 ``type_deps`` primitive and keep only the ``kind=="imports"``
    facts (DIA-03 is module-boundary import dependency, not annotation-derived
    type use). Each import fact becomes one ``imports`` edge from the importing
    module to the imported target; every distinct module referenced (the
    importer + each importable target) becomes a ``component`` node.
    """
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"component_diagram extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )
    module_name = get_module_name(cav.path)

    tds = type_deps.extract(cav, config)
    import_deps = [td for td in tds if td.kind == "imports"]

    # Component nodes: the importing module is always present; targets are the
    # imported module/symbol names. Ordered dedup via dict.fromkeys.
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
