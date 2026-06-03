"""Unit tests for lib_code_parser.extractors.primitives.cpp_contracts.extract.

Covers SPC-03 Doxygen contract extraction off the EXACT decl cursor's
raw_comment: \\pre/@pre -> precondition, \\post/@post -> postcondition,
\\invariant/@invariant -> invariant, all source_kind="doxygen" (D-08/D-09);
the dict[node_id, ContractInfo] output shape (Python contracts parity); and
Pitfall 4 (no inference from an enclosing namespace's leading comment).
"""

from __future__ import annotations

import pytest

from lib_code_parser.extractors.primitives.cpp_contracts import extract
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.contracts import ContractInfo
from tests.conftest import build_cpp_cav


@pytest.fixture
def config() -> ParserConfig:
    return ParserConfig(
        artifact_type="code",
        executor_lib="lib_code_parser",
        language="cpp",
        extract_contracts=True,
    )


def test_payload_assert_rejects_non_tu(config) -> None:
    from lib_code_parser.models.infrastructure.cav import CAV

    bad = CAV(language="cpp", path="x.cpp", payload=object())
    with pytest.raises(AssertionError):
        extract(bad, config)


def test_pre_post_invariant_both_forms(config) -> None:
    src = (
        "/**\n"
        " * @pre x > 0\n"
        " * \\post r >= 0\n"
        " * \\invariant ok\n"
        " */\n"
        "int compute(int x) { return x; }\n"
    )
    cav = build_cpp_cav(src, "c.cpp")
    res = extract(cav, config)
    assert isinstance(res, dict)
    ci = res["compute"]
    assert isinstance(ci, ContractInfo)
    kinds = {(e.kind, e.source_kind) for e in ci.entries}
    assert ("precondition", "doxygen") in kinds
    assert ("postcondition", "doxygen") in kinds
    assert ("invariant", "doxygen") in kinds
    # name is the decl spelling, line_no the decl line.
    assert all(e.name == "compute" for e in ci.entries)
    assert all(e.line_no > 0 for e in ci.entries)


def test_case_insensitive(config) -> None:
    src = "/** @PRE positive */\nvoid f() {}\n"
    cav = build_cpp_cav(src, "ci.cpp")
    res = extract(cav, config)
    assert res["f"].entries[0].kind == "precondition"
    assert res["f"].entries[0].source_kind == "doxygen"


def test_no_doxygen_no_entry(config) -> None:
    src = "// just a line comment\nvoid g() {}\n"
    cav = build_cpp_cav(src, "g.cpp")
    res = extract(cav, config)
    assert "g" not in res


def test_pitfall4_namespace_comment_not_inferred(config) -> None:
    """A namespace's leading Doxygen comment must NOT attach to an inner decl."""
    src = "/** \\pre namespace-level comment */\nnamespace ns {\nvoid inner() {}\n}\n"
    cav = build_cpp_cav(src, "ns.cpp")
    res = extract(cav, config)
    # inner() has no own raw_comment -> no contract entry attributed to it.
    assert "ns.inner" not in res


def test_method_contract_qualified_id(config) -> None:
    src = "class Calc {\npublic:\n  /** @pre a >= 0 */\n  int add(int a);\n};\n"
    cav = build_cpp_cav(src, "calc.cpp")
    res = extract(cav, config)
    assert "Calc.add" in res
    assert res["Calc.add"].entries[0].kind == "precondition"


def test_registered_in_dispatch() -> None:
    from lib_code_parser._dispatch import PRIMITIVES

    assert "contracts" in PRIMITIVES["cpp"]
