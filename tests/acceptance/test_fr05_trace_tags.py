"""FR-05: TraceTag extraction from Traces: comments in docstrings."""

from __future__ import annotations

import pytest

from lib_code_parser.ast_extractor import extract_functions


@pytest.fixture
def example_source() -> str:
    from tests.conftest import EXAMPLE_SOURCE
    return EXAMPLE_SOURCE


@pytest.fixture
def example_path() -> str:
    return "src/order_service.py"


def _nodes_by_id(source: str, path: str) -> dict:
    fns = extract_functions(source, path)
    return {fn.node_id: fn for fn in fns}


class TestClassTraceTags:
    def test_order_service_has_trace_tags(
        self, example_source: str, example_path: str
    ) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        tags = nodes["order_service.OrderService"].trace_tags
        assert len(tags) > 0

    def test_order_service_trace_refs(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        tags = nodes["order_service.OrderService"].trace_tags
        all_refs = [ref for t in tags for ref in t.refs]
        assert "US-01" in all_refs
        assert "FR-02" in all_refs


class TestMethodTraceTags:
    def test_create_order_trace_fr01(
        self, example_source: str, example_path: str
    ) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        tags = nodes["order_service.OrderService.create_order"].trace_tags
        all_refs = [ref for t in tags for ref in t.refs]
        assert "FR-01" in all_refs

    def test_cancel_order_no_trace(
        self, example_source: str, example_path: str
    ) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        tags = nodes["order_service.OrderService.cancel_order"].trace_tags
        # cancel_order has no Traces: in its docstring
        assert tags == []


class TestFunctionTraceTags:
    def test_process_payment_traces(
        self, example_source: str, example_path: str
    ) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        tags = nodes["order_service.process_payment"].trace_tags
        all_refs = [ref for t in tags for ref in t.refs]
        assert "FR-03" in all_refs
        assert "US-22" in all_refs

    def test_trace_tag_name(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        tags = nodes["order_service.process_payment"].trace_tags
        assert all(t.tag == "Traces" for t in tags)


class TestTraceTagMinimal:
    def test_multiple_traces_on_one_line(self) -> None:
        source = '''
def foo():
    """Does something.

    Traces: US-01, US-02, FR-10
    """
    pass
'''
        nodes = _nodes_by_id(source, "mod.py")
        tags = nodes["mod.foo"].trace_tags
        all_refs = [ref for t in tags for ref in t.refs]
        assert "US-01" in all_refs
        assert "US-02" in all_refs
        assert "FR-10" in all_refs

    def test_no_traces_in_docstring(self) -> None:
        source = '''
def bar():
    """No traces here."""
    pass
'''
        nodes = _nodes_by_id(source, "mod.py")
        tags = nodes["mod.bar"].trace_tags
        assert tags == []
