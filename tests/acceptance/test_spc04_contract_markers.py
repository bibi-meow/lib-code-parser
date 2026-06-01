"""SPC-04 acceptance: auxiliary contract markers via execute().

Exercises the full CodeParserExecutor path and reads
``result.content.class_spec[*].invariants`` for the SPC-04 marker families.
Detection-only (D-10): the library never imports icontract/deal; markers are
recognized by AST shape with import-provenance (T-03-13). The decoy
``def require()`` with no marker import is NOT flagged.

Traces: SPC-04, D-10, US-01, US-22.
"""

from __future__ import annotations

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.spec import ClassSpec
from tests.unit.extractors.fixtures.aux_marker_samples import (
    DEAL_ATTR_SOURCE,
    DECOY_REQUIRE_SOURCE,
    ICONTRACT_ATTR_SOURCE,
)


def _class_spec(source: str, path: str) -> list[ClassSpec]:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    return exe.execute(config, source.encode("utf-8"), path).content.class_spec


def _by_name(specs: list[ClassSpec]) -> dict[str, ClassSpec]:
    return {s.node_id.rsplit(".", 1)[-1]: s for s in specs}


class TestIcontractThroughPipeline:
    def test_account_invariants(self) -> None:
        specs = _class_spec(ICONTRACT_ATTR_SOURCE, "a.py")
        account = _by_name(specs)["Account"]
        sks = {c.source_kind for c in account.invariants}
        assert {"icontract_invariant", "icontract_require", "icontract_ensure"} <= sks


class TestDealThroughPipeline:
    def test_buffer_invariants(self) -> None:
        specs = _class_spec(DEAL_ATTR_SOURCE, "b.py")
        buffer = _by_name(specs)["Buffer"]
        sks = {c.source_kind for c in buffer.invariants}
        assert {"deal_inv", "deal_pre", "deal_post", "deal_ensure"} <= sks


class TestFalsePositiveDefenseThroughPipeline:
    def test_decoy_not_flagged(self) -> None:
        specs = _class_spec(DECOY_REQUIRE_SOURCE, "d.py")
        service = _by_name(specs)["Service"]
        assert service.invariants == []
