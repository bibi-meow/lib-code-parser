"""SPC-02 acceptance: class_spec via the public execute() surface.

Exercises the full CodeParserExecutor path (frontend → primitives → EVALUATIONS
walk) and reads ``result.content.class_spec``. Verifies one ClassSpec per class
with definition + members, and that the full 7-extractor pipeline populates all
seven CodeContent evaluation slots.

Traces: SPC-02, US-01, US-22.
"""

from __future__ import annotations

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.spec import ClassSpec
from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE


def _execute(source: str, path: str):
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    return exe.execute(config, source.encode("utf-8"), path)


def _class_spec(source: str, path: str) -> list[ClassSpec]:
    return _execute(source, path).content.class_spec


class TestClassSpecAcceptance:
    def test_example_source_has_two_classspecs(self) -> None:
        specs = _class_spec(EXAMPLE_SOURCE, EXAMPLE_PATH)
        names = {s.node_id.rsplit(".", 1)[-1] for s in specs}
        assert {"OrderService", "OrderModel"} <= names

    def test_orderservice_members(self) -> None:
        specs = _class_spec(EXAMPLE_SOURCE, EXAMPLE_PATH)
        by_name = {s.node_id.rsplit(".", 1)[-1]: s for s in specs}
        members = by_name["OrderService"].members
        assert set(members) >= {"create_order", "_calculate_total", "cancel_order"}
        assert members == sorted(members)

    def test_definition_present(self) -> None:
        specs = _class_spec(EXAMPLE_SOURCE, EXAMPLE_PATH)
        for spec in specs:
            assert spec.definition

    def test_det04_sorted_through_pipeline(self) -> None:
        specs = _class_spec(EXAMPLE_SOURCE, EXAMPLE_PATH)
        node_ids = [s.node_id for s in specs]
        assert node_ids == sorted(node_ids)


class TestAllSevenSlotsPopulated:
    def test_all_seven_evaluation_slots_present(self) -> None:
        content = _execute(EXAMPLE_SOURCE, EXAMPLE_PATH).content
        # All 7 EVALUATIONS slots exist on CodeContent (5 diagrams + 2 specs).
        assert content.class_diagram is not None
        assert content.sequence_diagram is not None
        assert content.component_diagram is not None
        assert content.package_diagram is not None
        assert content.state_diagram is not None
        assert content.function_spec is not None
        assert content.class_spec is not None
        # The 2 documented classes populate class_spec (non-empty).
        assert len(content.class_spec) >= 2
