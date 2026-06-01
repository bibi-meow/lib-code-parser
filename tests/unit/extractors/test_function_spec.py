"""Unit tests for the SPC-01 function_spec extractor.

The 3-dialect golden: the SAME function documented Google/NumPy/Sphinx in the
SAME module → identical FunctionSpec.docstring_sections (modulo node_id). Also
asserts inert (empty-section) FunctionSpec for undocumented functions and the
DET-04 byte-stable sort under PYTHONHASHSEED.

Traces: SPC-01.
"""

from __future__ import annotations

from lib_code_parser.extractors.evaluations.function_spec import extract
from tests.conftest import build_python_cav
from tests.unit.extractors.fixtures.docstring_dialects import (
    THREE_DIALECT_PATH,
    THREE_DIALECT_SOURCE,
)


def _specs(parser_config):  # type: ignore[no-untyped-def]
    cav = build_python_cav(THREE_DIALECT_SOURCE, THREE_DIALECT_PATH)
    return {fs.node_id.rsplit(".", 1)[-1]: fs for fs in extract(cav, parser_config)}


class TestFunctionSpecExtraction:
    def test_one_spec_per_function(self, parser_config) -> None:  # type: ignore[no-untyped-def]
        specs = _specs(parser_config)
        assert set(specs) == {"pay_google", "pay_numpy", "pay_sphinx", "undocumented"}

    def test_three_dialects_yield_identical_sections(self, parser_config) -> None:  # type: ignore[no-untyped-def]
        specs = _specs(parser_config)
        g = [s.model_dump() for s in specs["pay_google"].docstring_sections]
        n = [s.model_dump() for s in specs["pay_numpy"].docstring_sections]
        s = [s.model_dump() for s in specs["pay_sphinx"].docstring_sections]
        assert g == n == s

    def test_three_dialects_yield_identical_pre_post(self, parser_config) -> None:  # type: ignore[no-untyped-def]
        specs = _specs(parser_config)
        gp = [c.model_dump() for c in specs["pay_google"].preconditions]
        np_ = [c.model_dump() for c in specs["pay_numpy"].preconditions]
        sp = [c.model_dump() for c in specs["pay_sphinx"].preconditions]
        assert gp == np_ == sp
        gpo = [c.model_dump() for c in specs["pay_google"].postconditions]
        npo = [c.model_dump() for c in specs["pay_numpy"].postconditions]
        spo = [c.model_dump() for c in specs["pay_sphinx"].postconditions]
        assert gpo == npo == spo

    def test_undocumented_function_is_inert(self, parser_config) -> None:  # type: ignore[no-untyped-def]
        specs = _specs(parser_config)
        und = specs["undocumented"]
        assert und.docstring_sections == []
        assert und.preconditions == []
        assert und.postconditions == []
        # still carries the signature so the caller sees it
        assert "undocumented" in und.node_id

    def test_signature_present(self, parser_config) -> None:  # type: ignore[no-untyped-def]
        specs = _specs(parser_config)
        assert "amount" in specs["pay_google"].signature

    def test_node_id_namespaced_by_module(self, parser_config) -> None:  # type: ignore[no-untyped-def]
        specs = _specs(parser_config)
        assert specs["pay_google"].node_id == "payments.pay_google"


class TestDeterminism:
    def test_sorted_by_node_id(self, parser_config) -> None:  # type: ignore[no-untyped-def]
        cav = build_python_cav(THREE_DIALECT_SOURCE, THREE_DIALECT_PATH)
        out = extract(cav, parser_config)
        node_ids = [fs.node_id for fs in out]
        assert node_ids == sorted(node_ids)

    def test_byte_stable_repeated_runs(self, parser_config) -> None:  # type: ignore[no-untyped-def]
        cav = build_python_cav(THREE_DIALECT_SOURCE, THREE_DIALECT_PATH)
        first = [fs.model_dump() for fs in extract(cav, parser_config)]
        for _ in range(3):
            cav2 = build_python_cav(THREE_DIALECT_SOURCE, THREE_DIALECT_PATH)
            assert [fs.model_dump() for fs in extract(cav2, parser_config)] == first
