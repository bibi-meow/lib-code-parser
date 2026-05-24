"""Wave 0 tests for lib_code_parser/models/evaluations/graph_base.py.

Locks the closed EdgeKind Literal (SCH-03 / Pitfall 7) plus the four
verifier-facing graph models (SCH-02 extra="forbid") before any diagram
extractor is written. Direct submodule import path is used so the test
suite remains valid once Wave 2 Plan 01-09 rewrites the package barrel.
"""

from __future__ import annotations

from typing import get_args

import pytest
from pydantic import ValidationError

from lib_code_parser.models.evaluations.graph_base import (
    EdgeKind,
    GraphEdge,
    GraphModel,
    GraphNode,
    GuardExpr,
)

CANONICAL_EDGE_KINDS = {
    "inherits",
    "implements",
    "composes",
    "aggregates",
    "associates",
    "field_of",
    "param_of",
    "returns",
    "instantiates",
    "calls",
    "transitions_to",
}


class TestEdgeKindLiteral:
    def test_edge_kind_has_eleven_values(self) -> None:
        values = get_args(EdgeKind)
        assert len(values) == 11, f"expected 11 values, got {len(values)}: {values}"

    def test_edge_kind_value_set(self) -> None:
        values = set(get_args(EdgeKind))
        extra = values - CANONICAL_EDGE_KINDS
        missing = CANONICAL_EDGE_KINDS - values
        assert not extra, f"unexpected extra EdgeKind values: {sorted(extra)}"
        assert not missing, f"missing canonical EdgeKind values: {sorted(missing)}"

    def test_edge_kind_rejects_uses(self) -> None:
        # Pitfall 7: "uses" is the canonical example of a forbidden catch-all
        with pytest.raises(ValidationError):
            GraphEdge(source="A", target="B", edge_type="uses")  # type: ignore[arg-type]

    def test_edge_kind_rejects_other(self) -> None:
        with pytest.raises(ValidationError):
            GraphEdge(source="A", target="B", edge_type="other")  # type: ignore[arg-type]

    def test_edge_kind_rejects_misc(self) -> None:
        with pytest.raises(ValidationError):
            GraphEdge(source="A", target="B", edge_type="misc")  # type: ignore[arg-type]

    def test_edge_kind_accepts_all_eleven(self) -> None:
        for kind in get_args(EdgeKind):
            edge = GraphEdge(source="A", target="B", edge_type=kind)
            assert edge.edge_type == kind


class TestGraphNode:
    def test_graph_node_constructible(self) -> None:
        node = GraphNode(node_id="A", node_type="class", label="A")
        assert node.node_id == "A"
        assert node.node_type == "class"
        assert node.label == "A"
        assert node.attributes == {}

    def test_graph_node_node_type_str_allows_package(self) -> None:
        # node_type is plain str (NOT Literal) so the DIA-04 "package" extension
        # path stays open per D-15 / D-17. This is a deliberate design choice.
        node = GraphNode(node_id="P", node_type="package", label="P")
        assert node.node_type == "package"


class TestGraphEdgePhysicalModule:
    def test_graph_edge_physical_module_default_none(self) -> None:
        edge = GraphEdge(source="A", target="B", edge_type="calls")
        assert edge.physical_module is None

    def test_graph_edge_physical_module_settable(self) -> None:
        edge = GraphEdge(
            source="A",
            target="B",
            edge_type="calls",
            physical_module="order_service.OrderService",
        )
        assert edge.physical_module == "order_service.OrderService"


class TestExtraForbid:
    def test_all_evaluation_models_forbid_extra(self) -> None:
        # SCH-02: every verifier-facing model rejects unknown fields.
        with pytest.raises(ValidationError):
            GraphNode(node_id="A", node_type="class", label="A", unknown=1)  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            GraphEdge(source="A", target="B", edge_type="inherits", unknown=1)  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            GraphModel(unknown=1)  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            GuardExpr(from_state="X", to_state="Y", condition="c", unknown=1)  # type: ignore[call-arg]


class TestGraphModelDefaults:
    def test_graph_model_default_empty(self) -> None:
        model = GraphModel()
        assert model.nodes == []
        assert model.edges == []
        assert model.guards == []


class TestGuardExpr:
    def test_guard_expr_default_action_empty(self) -> None:
        guard = GuardExpr(from_state="X", to_state="Y", condition="c")
        assert guard.action == ""
