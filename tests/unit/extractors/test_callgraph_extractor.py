"""Unit tests for the CAV-consumer call graph extractor (Plan 02-03).

Locks v0.1.0 resolution rules (RESEARCH §4.1 CG1-CG7 truth table) plus the
DET-04 edge sort invariant. CAVs are built via build_cav (the single AST-05
parse site); tests never call ast.parse directly.

Traces: AST-02, AST-05, DET-04, US-01, US-22, US-25
"""

from __future__ import annotations

import pytest

from lib_code_parser.extractors.primitives.callgraph import extract
from lib_code_parser.frontends.python import build_cav
from lib_code_parser.models.infrastructure.config import ParserConfig
from tests.conftest import EXAMPLE_SOURCE


def _build_cav(source: str, path: str = "m.py"):
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    return build_cav(source.encode("utf-8"), path, config)


@pytest.fixture
def config():
    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _edge_pairs(cav, config):
    cg = extract(cav, config)
    return [(e.caller, e.callee) for e in cg.edges]


def test_self_dot_foo_resolves_to_bare_name(config):
    """CG1: self.baz() in a method resolves to bare ``baz`` (not Class.baz)."""
    src = "class Foo:\n    def bar(self):\n        self.baz()\n"
    pairs = _edge_pairs(_build_cav(src), config)
    assert ("m.Foo.bar", "baz") in pairs


def test_chain_call_emits_two_edges(config):
    """CG2 + RESEARCH Pitfall 4: chain a.b().c() yields 2 edges (c and b).

    After DET-04 sort the order is (m.outer, b) then (m.outer, c).
    """
    src = "def outer():\n    a.b().c()\n"
    pairs = _edge_pairs(_build_cav(src), config)
    assert ("m.outer", "c") in pairs
    assert ("m.outer", "b") in pairs
    outer_pairs = [p for p in pairs if p[0] == "m.outer"]
    assert outer_pairs == [("m.outer", "b"), ("m.outer", "c")]


def test_duplicate_callee_not_deduped(config):
    """CG3: helper() + other.helper() emits 2 (outer, helper) edges, no dedup."""
    src = "from other import helper\ndef outer():\n    helper()\n    other.helper()\n"
    pairs = _edge_pairs(_build_cav(src), config)
    assert pairs.count(("m.outer", "helper")) == 2


def test_nested_function_flattened_to_outer(config):
    """CG4: nested inner()'s leaf() flattens to outer; inner is not a node."""
    src = "def outer():\n    def inner():\n        leaf()\n    inner()\n"
    cav = _build_cav(src)
    cg = extract(cav, config)
    pairs = [(e.caller, e.callee) for e in cg.edges]
    assert ("m.outer", "leaf") in pairs
    assert ("m.outer", "inner") in pairs
    assert "m.inner" not in cg.nodes
    assert "m.outer.inner" not in cg.nodes


def test_staticmethod_classmethod_treated_as_method(config):
    """CG5: @staticmethod / @classmethod decorators are ignored (normal methods)."""
    src = (
        "class Foo:\n"
        "    @staticmethod\n"
        "    def smethod():\n"
        "        ...\n"
        "    @classmethod\n"
        "    def cmethod(cls):\n"
        "        ...\n"
    )
    cg = extract(_build_cav(src), config)
    assert "m.Foo.smethod" in cg.nodes
    assert "m.Foo.cmethod" in cg.nodes


def test_deep_attribute_innermost_only(config):
    """CG7: deep a.b.c.d() emits only the innermost Call edge (outer, d)."""
    src = "def outer():\n    a.b.c.d()\n"
    pairs = _edge_pairs(_build_cav(src), config)
    outer_pairs = [p for p in pairs if p[0] == "m.outer"]
    assert outer_pairs == [("m.outer", "d")]


def test_edges_lex_sorted_by_caller_callee(config):
    """DET-04 + ROADMAP SC-2: edges are lex-sorted by (caller, callee)."""
    src = "def b():\n    z()\n    a()\n    m()\n"
    pairs = _edge_pairs(_build_cav(src), config)
    assert pairs == [("m.b", "a"), ("m.b", "m"), ("m.b", "z")]


def test_nodes_insertion_order_with_dedup(config):
    """Nodes use dict.fromkeys: insertion order preserved, duplicates removed."""
    src = "class Foo:\n    def bar(self):\n        pass\ndef top():\n    pass\n"
    cg = extract(_build_cav(src), config)
    assert cg.nodes == ["m.Foo", "m.Foo.bar", "m.top"]
    assert len(cg.nodes) == len(set(cg.nodes))


def test_isolated_import_no_executor(config):
    """ROADMAP SC-4: extract is callable without importing CodeParserExecutor."""
    src = "def foo():\n    bar()\n"
    cg = extract(_build_cav(src), config)
    callees = {e.callee for e in cg.edges}
    assert "bar" in callees
    assert "m.foo" in cg.nodes


def test_extract_on_example_source(config):
    """v0.1.0 acceptance parity: create_order calls _calculate_total."""
    cav = build_cav(EXAMPLE_SOURCE.encode("utf-8"), "src/order_service.py", config)
    cg = extract(cav, config)
    pairs = {(e.caller, e.callee) for e in cg.edges}
    assert ("order_service.OrderService.create_order", "_calculate_total") in pairs
    assert "order_service.OrderService" in cg.nodes
    assert "order_service.process_payment" in cg.nodes
