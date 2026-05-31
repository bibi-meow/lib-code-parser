"""FR-05: TraceTag extraction from Traces: lines in docstrings (Phase 2 v0.2.0).

Consumes the typed ParserConfig + dispatch-driven executor through the public
v0.2.0 surface. TraceTag parity with v0.1.0 is byte-identical (same verbatim
regex in the functions extractor).
"""

from __future__ import annotations

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig
from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE


def _nodes(source: str, path: str) -> dict:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return {fn.node_id: fn for fn in result.content.functions}


@pytest.fixture
def example_nodes() -> dict:
    return _nodes(EXAMPLE_SOURCE, EXAMPLE_PATH)


class TestClassTraceTags:
    def test_order_service_has_trace_tags(self, example_nodes: dict) -> None:
        tags = example_nodes["order_service.OrderService"].trace_tags
        assert len(tags) > 0

    def test_order_service_trace_refs(self, example_nodes: dict) -> None:
        tags = example_nodes["order_service.OrderService"].trace_tags
        all_refs = [ref for t in tags for ref in t.refs]
        assert "US-01" in all_refs
        assert "FR-02" in all_refs


class TestMethodTraceTags:
    def test_create_order_trace_fr01(self, example_nodes: dict) -> None:
        tags = example_nodes["order_service.OrderService.create_order"].trace_tags
        all_refs = [ref for t in tags for ref in t.refs]
        assert "FR-01" in all_refs

    def test_cancel_order_no_trace(self, example_nodes: dict) -> None:
        tags = example_nodes["order_service.OrderService.cancel_order"].trace_tags
        # cancel_order has no Traces: in its docstring
        assert tags == []


class TestFunctionTraceTags:
    def test_process_payment_traces(self, example_nodes: dict) -> None:
        tags = example_nodes["order_service.process_payment"].trace_tags
        all_refs = [ref for t in tags for ref in t.refs]
        assert "FR-03" in all_refs
        assert "US-22" in all_refs

    def test_trace_tag_name(self, example_nodes: dict) -> None:
        tags = example_nodes["order_service.process_payment"].trace_tags
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
        nodes = _nodes(source, "mod.py")
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
        nodes = _nodes(source, "mod.py")
        tags = nodes["mod.bar"].trace_tags
        assert tags == []
