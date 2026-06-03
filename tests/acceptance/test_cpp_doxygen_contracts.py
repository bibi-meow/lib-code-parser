"""SPC-03 acceptance: C++ Doxygen contracts via the public execute() surface.

Exercises the full CodeParserExecutor path on a ``.cpp`` artifact (the suffix
override selects the cpp track) and reads ``result.content.contracts``. Proves:
- the three Doxygen kinds (precondition / postcondition / invariant) are emitted,
- every entry carries ``source_kind == "doxygen"`` (D-08),
- the emitted schema (ContractInfo / ContractEntry field set) is IDENTICAL to
  what the Python contracts path produces (D-09 parity).

Traces: SPC-03, LNG-04.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.primitives.contracts import ContractEntry, ContractInfo

_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "cpp" / "doxygen_contracts.cpp"


def _contracts(path: str) -> dict:
    config = ParserConfig(
        artifact_type="code",
        executor_lib="lib_code_parser",
        extract_contracts=True,
    )
    exe = CodeParserExecutor()
    raw = _FIXTURE.read_bytes()
    result = exe.execute(config, raw, path)
    return result.content.contracts


@pytest.fixture
def contracts() -> dict:
    return _contracts("doxygen_contracts.cpp")


class TestDoxygenContractAcceptance:
    def test_three_kinds_emitted(self, contracts: dict) -> None:
        kinds = {e.kind for ci in contracts.values() for e in ci.entries}
        assert {"precondition", "postcondition", "invariant"} <= kinds

    def test_all_source_kind_doxygen(self, contracts: dict) -> None:
        source_kinds = {e.source_kind for ci in contracts.values() for e in ci.entries}
        assert source_kinds == {"doxygen"}

    def test_attached_to_compute_score(self, contracts: dict) -> None:
        # compute_score is a free function -> its node_id is the decl spelling.
        assert "compute_score" in contracts
        ci = contracts["compute_score"]
        assert isinstance(ci, ContractInfo)
        assert {e.kind for e in ci.entries} == {
            "precondition",
            "postcondition",
            "invariant",
        }

    def test_schema_identical_to_python(self, contracts: dict) -> None:
        """D-09 parity: the C++ path emits the SAME ContractInfo/ContractEntry schema."""
        ci = next(iter(contracts.values()))
        assert isinstance(ci, ContractInfo)
        assert set(ContractInfo.model_fields) == set(type(ci).model_fields)
        entry = ci.entries[0]
        assert isinstance(entry, ContractEntry)
        assert set(ContractEntry.model_fields) == set(type(entry).model_fields)
