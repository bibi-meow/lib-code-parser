"""Unit tests for lib_code_parser.extractors.primitives.cpp_functions.extract.

Covers kind discrimination (class/method/function), namespace-qualified
node_id, params/return_type/source_range, TRC-03 trace-tag extraction from
cursor.raw_comment, and DET-04 sort-on-exit by node_id.
"""

from __future__ import annotations

import clang.cindex
import pytest

from lib_code_parser.extractors.primitives.cpp_functions import extract
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.functions import FunctionNode
from tests.conftest import build_cpp_cav


@pytest.fixture
def config() -> ParserConfig:
    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _by_id(nodes: list[FunctionNode], node_id: str) -> FunctionNode:
    matches = [n for n in nodes if n.node_id == node_id]
    assert matches, f"expected node_id {node_id!r}; got {[n.node_id for n in nodes]}"
    return matches[0]


def test_payload_assert_rejects_non_tu(config) -> None:
    from lib_code_parser.models.infrastructure.cav import CAV

    bad = CAV(language="cpp", path="x.cpp", payload=object())
    with pytest.raises(AssertionError):
        extract(bad, config)


def test_class_method_function_kinds(config) -> None:
    src = (
        "namespace a {\n"
        "struct Calc {\n"
        "  int add(int lhs, int rhs);\n"
        "};\n"
        "int free_fn(double v) { return 1; }\n"
        "}\n"
    )
    cav = build_cpp_cav(src, "k.cpp")
    nodes = extract(cav, config)
    assert _by_id(nodes, "a.Calc").kind == "class"
    method = _by_id(nodes, "a.Calc.add")
    assert method.kind == "method"
    assert [p.name for p in method.params] == ["lhs", "rhs"]
    assert method.return_type == "int"
    fn = _by_id(nodes, "a.free_fn")
    assert fn.kind == "function"


def test_trace_tags_from_raw_comment(config) -> None:
    src = "/// Adds.\n/// Traces: REQ-1, US-2\nint add(int x);\n"
    cav = build_cpp_cav(src, "t.cpp")
    nodes = extract(cav, config)
    fn = _by_id(nodes, "add")
    assert fn.trace_tags and fn.trace_tags[0].refs == ["REQ-1", "US-2"]


def test_source_range_populated(config) -> None:
    src = "struct S {\n  int f();\n};\n"
    cav = build_cpp_cav(src, "sr.cpp")
    nodes = extract(cav, config)
    s = _by_id(nodes, "S")
    assert s.source_range.start_line == 1
    assert s.source_range.end_line >= s.source_range.start_line


def test_sorted_by_node_id(config) -> None:
    src = "int zeta();\nint alpha();\nstruct Mid { int beta(); };\n"
    cav = build_cpp_cav(src, "srt.cpp")
    nodes = extract(cav, config)
    ids = [n.node_id for n in nodes]
    assert ids == sorted(ids)


def test_no_duplicate_node_ids_for_out_of_line_def(config) -> None:
    src = "struct S { int f(); };\nint S::f() { return 1; }\n"
    cav = build_cpp_cav(src, "dup.cpp")
    nodes = extract(cav, config)
    ids = [n.node_id for n in nodes]
    assert ids.count("S.f") == 1


def test_header_decls_excluded(config) -> None:
    # vector pulls in std:: decls from a header; only main-file decls emit.
    src = "#include <vector>\nstruct Local { int v; };\n"
    cav = build_cpp_cav(src, "hdr.cpp")
    nodes = extract(cav, config)
    assert all(n.node_id == "Local" or n.node_id.startswith("Local") for n in nodes), (
        f"header decls leaked: {[n.node_id for n in nodes]}"
    )


def test_never_branches_on_language(config) -> None:
    # Smoke: a python-language CAV carrying a TU still works (assert is on payload type).
    src = "int f();\n"
    tu = build_cpp_cav(src, "lang.cpp").payload
    from lib_code_parser.models.infrastructure.cav import CAV

    mislabeled = CAV(language="python", path="lang.cpp", payload=tu)
    assert isinstance(tu, clang.cindex.TranslationUnit)
    nodes = extract(mislabeled, config)
    assert _by_id(nodes, "f").kind == "function"
