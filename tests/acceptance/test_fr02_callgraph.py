"""FR-02: Call graph extraction acceptance tests (Phase 2 v0.2.0 form).

Consumes the typed ParserConfig + dispatch-driven executor through the public
v0.2.0 surface. Edge assertions use set-membership over DET-04-sorted
`(caller, callee)` pairs (no positional `edges[0]` assumptions).
"""

from __future__ import annotations

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig
from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE


def _call_graph(source: str, path: str):
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.call_graph


@pytest.fixture
def example_call_graph():
    return _call_graph(EXAMPLE_SOURCE, EXAMPLE_PATH)


class TestCallGraphNodes:
    def test_class_in_nodes(self, example_call_graph) -> None:
        assert "order_service.OrderService" in example_call_graph.nodes

    def test_methods_in_nodes(self, example_call_graph) -> None:
        assert "order_service.OrderService.create_order" in example_call_graph.nodes
        assert "order_service.OrderService._calculate_total" in example_call_graph.nodes

    def test_top_level_fn_in_nodes(self, example_call_graph) -> None:
        assert "order_service.process_payment" in example_call_graph.nodes

    def test_no_duplicate_nodes(self, example_call_graph) -> None:
        assert len(example_call_graph.nodes) == len(set(example_call_graph.nodes))


class TestCallGraphEdges:
    def test_create_order_calls_calculate_total(self, example_call_graph) -> None:
        edge_pairs = {(e.caller, e.callee) for e in example_call_graph.edges}
        assert (
            "order_service.OrderService.create_order",
            "_calculate_total",
        ) in edge_pairs

    def test_edges_have_caller_callee(self, example_call_graph) -> None:
        for edge in example_call_graph.edges:
            assert edge.caller
            assert edge.callee

    def test_edges_det04_sorted(self, example_call_graph) -> None:
        """DET-04: edges are lexicographically sorted by (caller, callee)."""
        pairs = [(e.caller, e.callee) for e in example_call_graph.edges]
        assert pairs == sorted(pairs)


class TestCallGraphMinimal:
    def test_empty_source(self) -> None:
        cg = _call_graph("", "empty.py")
        assert cg.nodes == []
        assert cg.edges == []

    def test_simple_function_with_call(self) -> None:
        cg = _call_graph("def foo():\n    bar()\n", "simple.py")
        assert "simple.foo" in cg.nodes
        callee_names = {e.callee for e in cg.edges}
        assert "bar" in callee_names
