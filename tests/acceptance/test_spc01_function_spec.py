"""SPC-01 acceptance: function_spec via the public execute() surface.

Exercises the full CodeParserExecutor path (frontend → primitives → EVALUATIONS
walk) and reads ``result.content.function_spec``. Verifies the 3-dialect golden
through the real pipeline and the inert-spec-for-undocumented case.

Traces: SPC-01, US-01, US-22.
"""

from __future__ import annotations

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.spec import FunctionSpec
from tests.unit.extractors.fixtures.docstring_dialects import (
    THREE_DIALECT_PATH,
    THREE_DIALECT_SOURCE,
)


def _function_spec(source: str, path: str) -> list[FunctionSpec]:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.function_spec


class TestFunctionSpecAcceptance:
    def test_function_spec_populated(self) -> None:
        specs = _function_spec(THREE_DIALECT_SOURCE, THREE_DIALECT_PATH)
        by_name = {fs.node_id.rsplit(".", 1)[-1]: fs for fs in specs}
        assert {"pay_google", "pay_numpy", "pay_sphinx", "undocumented"} <= set(by_name)

    def test_three_dialects_identical_through_pipeline(self) -> None:
        specs = _function_spec(THREE_DIALECT_SOURCE, THREE_DIALECT_PATH)
        by_name = {fs.node_id.rsplit(".", 1)[-1]: fs for fs in specs}
        g = [s.model_dump() for s in by_name["pay_google"].docstring_sections]
        n = [s.model_dump() for s in by_name["pay_numpy"].docstring_sections]
        s = [s.model_dump() for s in by_name["pay_sphinx"].docstring_sections]
        assert g == n == s

    def test_undocumented_is_inert_through_pipeline(self) -> None:
        specs = _function_spec(THREE_DIALECT_SOURCE, THREE_DIALECT_PATH)
        by_name = {fs.node_id.rsplit(".", 1)[-1]: fs for fs in specs}
        assert by_name["undocumented"].docstring_sections == []

    def test_det04_sorted_through_pipeline(self) -> None:
        specs = _function_spec(THREE_DIALECT_SOURCE, THREE_DIALECT_PATH)
        node_ids = [fs.node_id for fs in specs]
        assert node_ids == sorted(node_ids)
