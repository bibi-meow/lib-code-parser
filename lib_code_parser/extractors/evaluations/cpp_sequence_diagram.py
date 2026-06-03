r"""D-04 / D-05 C++ sequence diagram extractor (linear call flow).

The C++ analog of ``evaluations/sequence_diagram.py`` (LNG-04 parity), restricted
to the linear must-have (D-05): pull the cpp ``cpp_callgraph`` primitive — the
authoritative source of ``(caller, callee)`` interactions — and map each
``CallEdge`` to ``GraphEdge(edge_type="calls", source=caller, target=callee)``.
Every distinct caller / callee becomes a ``GraphNode(node_type="participant")``.

Branch-frame fidelity (the SP-2 Mermaid frame labels the Python sibling carries)
is best-effort for C++ and out of v0.2.0 scope (D-05); the linear ``calls`` edges
are the must-have. Labels stay empty so the output is a deterministic linear
sequence with NO non-portable C++ control-flow-frame idiom invented.

D-03: ``calls`` is this lib's own vocabulary; never a catch-all. DET-04: nodes
sorted by ``node_id``; edges sorted by ``(source, target, edge_type, label)`` on
exit. ``dict.fromkeys`` gives ordered dedup before sorting.

Implements: LNG-04
Traces: LNG-04, US-25, US-32
"""

from __future__ import annotations

import clang.cindex

from lib_code_parser.extractors.primitives import cpp_callgraph
from lib_code_parser.models.evaluations.graph_base import GraphEdge, GraphModel, GraphNode
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """LNG-04 / DET-04: emit a sequence GraphModel (participants + calls edges).

    The linear ``calls`` edges come from the authoritative ``cpp_callgraph``
    primitive (D-05 must-have). Asserts a TranslationUnit payload and NEVER
    branches on ``cav.language`` (invariant #2).
    """
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit), (
        "cpp_sequence_diagram extractor requires C++ CAV (TranslationUnit payload), "
        f"got {type(tu).__name__}"
    )

    cg = cpp_callgraph.extract(cav, config)

    node_ids: list[str] = list(cg.nodes)
    edges: list[GraphEdge] = []
    for edge in cg.edges:
        edges.append(GraphEdge(source=edge.caller, target=edge.callee, edge_type="calls"))
        node_ids.append(edge.caller)
        node_ids.append(edge.callee)

    node_ids = list(dict.fromkeys(node_ids))
    nodes = [GraphNode(node_id=nid, node_type="participant", label=nid) for nid in node_ids]

    # DET-04 sort-on-exit with stable composite keys.
    nodes.sort(key=lambda n: n.node_id)
    edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))

    return GraphModel(nodes=nodes, edges=edges)
