"""Unit tests for the DIA-02 sequence_diagram extractor.

Sequence diagram = call-graph-derived linear interaction sequence (must-have,
D-07) plus SP-2 branch-fidelity frames (alt/loop/par) encoded on the edge label
(SP-2 verdict = SHIP). Pulls the Phase 2 ``callgraph`` primitive for the
authoritative ``calls`` edges and re-walks ``cav.payload`` for frame labels.

Traces: DIA-02, DIA-07, DET-04.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations.sequence_diagram import extract
from lib_code_parser.models.evaluations.graph_base import GraphModel
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from tests.unit.extractors.fixtures.seq_callgraph import (
    BRANCH_PATH,
    BRANCH_SOURCE,
    LINEAR_PATH,
    LINEAR_SOURCE,
    NO_CALLS_PATH,
    NO_CALLS_SOURCE,
)

_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _build_cav(source: str, path: str) -> CAV:
    return CAV(language="python", path=path, payload=ast.parse(source))


def _extract(source: str, path: str) -> GraphModel:
    return extract(_build_cav(source, path), _CONFIG)


class TestSequenceLinearEdges:
    """D-07 must-have: linear calls edges from the call graph."""

    def test_call_becomes_calls_edge(self) -> None:
        model = _extract(LINEAR_SOURCE, LINEAR_PATH)
        pairs = {(e.source, e.target) for e in model.edges}
        assert ("order_service.OrderService.create_order", "_calculate_total") in pairs
        assert ("order_service.process_payment", "validate") in pairs

    def test_all_edges_are_calls_kind(self) -> None:
        model = _extract(LINEAR_SOURCE, LINEAR_PATH)
        assert all(e.edge_type == "calls" for e in model.edges)

    def test_no_calls_yields_no_edges(self) -> None:
        model = _extract(NO_CALLS_SOURCE, NO_CALLS_PATH)
        assert model.edges == []


class TestSequenceParticipants:
    """Participant nodes: distinct callers + callees, deterministically ordered."""

    def test_callers_are_participants(self) -> None:
        model = _extract(LINEAR_SOURCE, LINEAR_PATH)
        node_ids = {n.node_id for n in model.nodes}
        assert "order_service.OrderService.create_order" in node_ids
        assert "order_service.process_payment" in node_ids

    def test_callees_are_participants(self) -> None:
        model = _extract(LINEAR_SOURCE, LINEAR_PATH)
        node_ids = {n.node_id for n in model.nodes}
        assert "_calculate_total" in node_ids
        assert "validate" in node_ids

    def test_participant_node_type(self) -> None:
        model = _extract(LINEAR_SOURCE, LINEAR_PATH)
        assert all(n.node_type == "participant" for n in model.nodes)

    def test_no_calls_still_lists_defined_callables(self) -> None:
        # lonely() defines a function with no calls → it is still a participant
        # node (it appears as a callgraph node), but there are no edges.
        model = _extract(NO_CALLS_SOURCE, NO_CALLS_PATH)
        node_ids = {n.node_id for n in model.nodes}
        assert "lonely.lonely" in node_ids


class TestSequenceBranchFrames:
    """SP-2 SHIP: alt/loop/par frame labels from control flow."""

    def test_if_call_labelled_alt(self) -> None:
        model = _extract(BRANCH_SOURCE, BRANCH_PATH)
        labels = {(e.target, e.label) for e in model.edges}
        assert ("notify", "alt") in labels

    def test_for_and_while_calls_labelled_loop(self) -> None:
        model = _extract(BRANCH_SOURCE, BRANCH_PATH)
        labels = {(e.target, e.label) for e in model.edges}
        assert ("process", "loop") in labels  # for-body
        assert ("retry", "loop") in labels  # while-body

    def test_await_call_labelled_par(self) -> None:
        model = _extract(BRANCH_SOURCE, BRANCH_PATH)
        labels = {(e.target, e.label) for e in model.edges}
        assert ("fetch", "par") in labels

    def test_linear_call_has_empty_label(self) -> None:
        model = _extract(BRANCH_SOURCE, BRANCH_PATH)
        labels = {(e.target, e.label) for e in model.edges}
        assert ("setup", "") in labels  # top-level, no enclosing frame


class TestSequenceFrameAlignment:
    """CR-01: frame labels must align 1:1 with callgraph edges occurrence-for-
    occurrence, even when calls within ONE statement live at different AST
    depths. The callgraph primitive collects callees via ``ast.walk`` (BFS),
    so the frame walk must consume callees in the SAME order, else an awaited
    call's ``par`` frame is popped for the wrong edge."""

    def test_same_callee_mixed_frames_align_with_callgraph(self) -> None:
        # `await go() + go()`: the SAME bare callee `go` appears twice within
        # one statement at DIFFERENT AST depths — the right `go()` is a direct
        # child of the BinOp (depth 1, linear), the left `go()` is wrapped in
        # Await (depth 2, par). callgraph collects callees via ast.walk (BFS),
        # so it emits the shallow (linear) `go` FIRST. The frame walk must
        # consume callees in the SAME BFS order so the `par`/`` frames land on
        # the correct edge occurrences. The frame multiset for (driver, go)
        # must be exactly {"par", ""} in callgraph (BFS) order.
        src = "async def driver():\n    x = await go() + go()\n"
        model = _extract(src, "m.py")
        go_labels = sorted(e.label for e in model.edges if e.target == "go")
        assert go_labels == ["", "par"]
        # The genuine alignment assertion: the FIRST callgraph edge (shallow go)
        # is linear, the SECOND (awaited go) is par. After the DET-04 sort both
        # share key (m.driver, go), so we re-derive expected order from the
        # callgraph BFS to assert occurrence-correct assignment.
        from lib_code_parser.extractors.evaluations.sequence_diagram import _frames_for_body

        frames = _frames_for_body(ast.parse(src).body[0].body)
        # BFS order (matching callgraph): shallow linear `go` then awaited par.
        assert frames == [("go", ""), ("go", "par")]


class TestSequenceDeterminism:
    """DET-04: sorted on exit, byte-identical across runs / PYTHONHASHSEED."""

    def test_nodes_sorted_by_node_id(self) -> None:
        model = _extract(LINEAR_SOURCE, LINEAR_PATH)
        ids = [n.node_id for n in model.nodes]
        assert ids == sorted(ids)

    def test_edges_sorted_by_composite_key(self) -> None:
        model = _extract(BRANCH_SOURCE, BRANCH_PATH)
        keys = [(e.source, e.target, e.edge_type, e.label) for e in model.edges]
        assert keys == sorted(keys)

    def test_byte_identical_repeated_extraction(self) -> None:
        a = _extract(BRANCH_SOURCE, BRANCH_PATH)
        b = _extract(BRANCH_SOURCE, BRANCH_PATH)
        assert a.model_dump_json() == b.model_dump_json()


class TestSequenceReturnType:
    def test_returns_graphmodel(self) -> None:
        assert isinstance(_extract(LINEAR_SOURCE, LINEAR_PATH), GraphModel)
