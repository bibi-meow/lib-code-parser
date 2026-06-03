"""Unit tests for lib_code_parser.extractors.primitives.cpp_callgraph.extract.

Covers CallEdge(caller, callee) emission from CALL_EXPR/MEMBER_REF_EXPR within
main-file function/method bodies, node dedup, and DET-04 (caller, callee) sort.
"""

from __future__ import annotations

import pytest

from lib_code_parser.extractors.primitives.cpp_callgraph import extract
from lib_code_parser.models.infrastructure.config import ParserConfig
from tests.conftest import build_cpp_cav


@pytest.fixture
def config() -> ParserConfig:
    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def test_payload_assert_rejects_non_tu(config) -> None:
    from lib_code_parser.models.infrastructure.cav import CAV

    bad = CAV(language="cpp", path="x.cpp", payload=object())
    with pytest.raises(AssertionError):
        extract(bad, config)


def test_edges_from_function_body(config) -> None:
    src = "int helper();\nint caller() { return helper(); }\n"
    cav = build_cpp_cav(src, "cg.cpp")
    cg = extract(cav, config)
    pairs = {(e.caller, e.callee) for e in cg.edges}
    assert ("caller", "helper") in pairs


def test_method_call_edges(config) -> None:
    src = "struct Calc {\n  int helper();\n  int add() { return helper(); }\n};\n"
    cav = build_cpp_cav(src, "m.cpp")
    cg = extract(cav, config)
    pairs = {(e.caller, e.callee) for e in cg.edges}
    assert ("Calc.add", "helper") in pairs


def test_edges_sorted_by_caller_callee(config) -> None:
    src = "int a(); int b(); int c();\nint z() { return c() + a() + b(); }\n"
    cav = build_cpp_cav(src, "s.cpp")
    cg = extract(cav, config)
    keys = [(e.caller, e.callee) for e in cg.edges]
    assert keys == sorted(keys)


def test_nodes_deduped(config) -> None:
    src = "int f() { return 1; }\nint f2() { return f(); }\n"
    cav = build_cpp_cav(src, "d.cpp")
    cg = extract(cav, config)
    assert len(cg.nodes) == len(set(cg.nodes))


def test_call_inside_lambda_not_attributed_to_enclosing(config) -> None:
    """WR-04: a call inside a nested lambda body is NOT attributed to the encloser.

    The enclosing function ``outer`` only directly invokes the lambda; the
    ``helper()`` call lives inside the lambda body and must not be flattened up
    into ``outer`` (which would double-count it against the nested callable).
    """
    src = "int helper();\nvoid outer() {\n  auto fn = []() { return helper(); };\n  fn();\n}\n"
    cav = build_cpp_cav(src, "lam.cpp")
    cg = extract(cav, config)
    outer_callees = {e.callee for e in cg.edges if e.caller == "outer"}
    # 'helper' is called only inside the lambda body, never directly by outer.
    assert "helper" not in outer_callees
