"""DET-04 sort invariant gate for the call graph extractor (Plan 02-03).

ROADMAP Phase 2 SC-2 invariant: CallGraph.edges are lexicographically sorted by
(caller, callee) at emit time. These tests re-confirm the invariant on the
extractor's output, including byte-identical stability (DET-01 precondition) and
preservation of intentional duplicate edges (v0.1.0 parity, no dedup).

Traces: DET-04, DET-01, AST-02
"""

from __future__ import annotations

from lib_code_parser.extractors.primitives.callgraph import extract
from lib_code_parser.frontends.python import build_cav
from lib_code_parser.models.infrastructure.config import ParserConfig


def _cg(source: str):
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    cav = build_cav(source.encode("utf-8"), "m.py", config)
    return extract(cav, config)


def test_edges_are_lex_sorted_for_simple_fixture():
    """Edges sort by (caller, callee): m.a before m.b; m.b callees a < m < z."""
    src = "def b():\n    z()\n    a()\n    m()\ndef a():\n    pass\n"
    cg = _cg(src)
    pairs = [(e.caller, e.callee) for e in cg.edges]
    assert pairs == sorted(pairs)
    b_callees = [e.callee for e in cg.edges if e.caller == "m.b"]
    assert b_callees == ["a", "m", "z"]


def test_edges_sort_is_stable_across_runs():
    """DET-01 precondition: 3 extract runs produce byte-identical JSON."""
    src = "def b():\n    z()\n    a()\n    m()\n"
    dumps = [_cg(src).model_dump_json() for _ in range(3)]
    assert dumps[0] == dumps[1] == dumps[2]


def test_edges_sort_handles_empty_callgraph():
    """Empty body → no edges; sort of empty list is a no-op."""
    src = "class Empty:\n    pass\n"
    cg = _cg(src)
    assert cg.edges == []


def test_edges_sort_with_duplicates_preserves_count():
    """Duplicate edges (CG3) survive sort: count is unchanged, no dedup."""
    src = "from other import helper\ndef outer():\n    helper()\n    other.helper()\n"
    cg = _cg(src)
    pairs = [(e.caller, e.callee) for e in cg.edges]
    assert pairs == sorted(pairs)
    assert pairs.count(("m.outer", "helper")) == 2
