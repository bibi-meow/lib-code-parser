"""FR-02: Call graph extraction acceptance tests."""

from __future__ import annotations

import pytest

from lib_code_parser.callgraph_builder import build_callgraph


@pytest.fixture
def example_source() -> str:
    from tests.conftest import EXAMPLE_SOURCE

    return EXAMPLE_SOURCE


@pytest.fixture
def example_path() -> str:
    return "src/order_service.py"


class TestCallGraphNodes:
    def test_class_in_nodes(self, example_source: str, example_path: str) -> None:
        cg = build_callgraph(example_source, example_path)
        assert "order_service.OrderService" in cg.nodes

    def test_methods_in_nodes(self, example_source: str, example_path: str) -> None:
        cg = build_callgraph(example_source, example_path)
        assert "order_service.OrderService.create_order" in cg.nodes
        assert "order_service.OrderService._calculate_total" in cg.nodes

    def test_top_level_fn_in_nodes(self, example_source: str, example_path: str) -> None:
        cg = build_callgraph(example_source, example_path)
        assert "order_service.process_payment" in cg.nodes

    def test_no_duplicate_nodes(self, example_source: str, example_path: str) -> None:
        cg = build_callgraph(example_source, example_path)
        assert len(cg.nodes) == len(set(cg.nodes))


class TestCallGraphEdges:
    def test_create_order_calls_calculate_total(
        self, example_source: str, example_path: str
    ) -> None:
        cg = build_callgraph(example_source, example_path)
        edge_pairs = {(e.caller, e.callee) for e in cg.edges}
        assert (
            "order_service.OrderService.create_order",
            "_calculate_total",
        ) in edge_pairs

    def test_edges_have_caller_callee(self, example_source: str, example_path: str) -> None:
        cg = build_callgraph(example_source, example_path)
        for edge in cg.edges:
            assert edge.caller
            assert edge.callee


class TestCallGraphMinimal:
    def test_empty_source(self) -> None:
        cg = build_callgraph("", "empty.py")
        assert cg.nodes == []
        assert cg.edges == []

    def test_simple_function_with_call(self) -> None:
        source = "def foo():\n    bar()\n"
        cg = build_callgraph(source, "simple.py")
        assert "simple.foo" in cg.nodes
        callee_names = {e.callee for e in cg.edges}
        assert "bar" in callee_names
