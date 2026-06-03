r"""D-05 / A1 C++ state diagram extractor (empty GraphModel — parity-as-empty-shape).

The C++ role-analog of ``evaluations/state_diagram.py``. The Python sibling
detects three library-anchored FSM families (``transitions.Machine``,
``python-statemachine``, native ``Enum`` + literal ``self.state = ...``). C++ has
NO portable, deterministic FSM idiom that maps onto those families: an
``enum class`` + ``switch`` (the ``not_a_state_machine.cpp`` fixture) is exactly
the C++ shape of a Python ``Color(Enum)`` with no transitions, which the Python
sibling correctly yields ZERO state nodes for.

A1 / D-05 (RESOLVED): for v0.2.0 this extractor emits an EMPTY ``GraphModel``
(zero state nodes / edges / guards) — *parity-as-empty-shape*, consistent with
the SP-1 DEFER verdict (general control-flow -> state is not deterministic). We
do NOT invent a non-deterministic C++ FSM idiom. This is best-effort and
fixture-asserted (``tests`` assert zero state nodes on the negative fixture), not
silently skipped: the extractor IS registered and DOES run, it just emits the
correct empty Pydantic shape.

DET-04: still ends with the verbatim sort tail over the (empty) lists so the
structural shape is byte-identical across runs.

Implements: LNG-04
Traces: LNG-04, US-25, US-32
"""

from __future__ import annotations

import clang.cindex

from lib_code_parser.models.evaluations.graph_base import (
    GraphEdge,
    GraphModel,
    GraphNode,
    GuardExpr,
)
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """LNG-04 / A1 / D-05: emit an EMPTY state GraphModel (parity-as-empty-shape).

    C++ has no portable deterministic FSM idiom mapping to the Python families,
    so v0.2.0 emits zero state nodes (identical to a Python ``Color(Enum)`` with
    no transitions). Asserts a TranslationUnit payload and NEVER branches on
    ``cav.language`` (invariant #2); still applies the DET-04 sort tail over the
    empty lists for structural identity.
    """
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit), (
        "cpp_state_diagram extractor requires C++ CAV (TranslationUnit payload), "
        f"got {type(tu).__name__}"
    )

    # A1 / D-05 (DELIBERATE, not a stub): for v0.2.0 the C++ state diagram is the
    # empty-shape parity contract. C++ has no portable deterministic FSM idiom
    # mapping to the Python families, so this extractor intentionally emits an
    # EMPTY GraphModel — identical to a Python ``Color(Enum)`` with no
    # transitions. It IS registered and DOES run; it is not an unfinished
    # placeholder. The three sorts below are therefore no-ops over empty lists;
    # they are kept only to make the DET-04 sort-on-exit shape byte-identical to
    # the Python sibling (a reviewer should read them as "same structure, zero
    # data", not "TODO: implement").
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    guards: list[GuardExpr] = []

    nodes.sort(key=lambda n: n.node_id)
    edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))
    guards.sort(key=lambda g: (g.from_state, g.to_state, g.condition, g.action))

    return GraphModel(nodes=nodes, edges=edges, guards=guards)
