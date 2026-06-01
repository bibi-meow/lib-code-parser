"""DIA-05 acceptance: state diagram via the public execute() surface.

Exercises the full CodeParserExecutor path (frontend → primitives → EVALUATIONS
walk) and reads ``result.content.state_diagram``. Verifies the 3 explicit FSM
families are detected and the bare-Enum negative case yields zero state nodes.

Traces: DIA-05, DIA-07.
"""

from __future__ import annotations

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.graph_base import GraphModel
from tests.unit.extractors.fixtures.fsm_samples import (
    FAMILY_A_DICTS,
    FAMILY_B_BASIC,
    FAMILY_C_LITERAL,
    NEGATIVE_BARE_ENUM,
)


def _state_diagram(source: str, path: str = "pkg/app.py") -> GraphModel:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.state_diagram


class TestStateDiagramAcceptance:
    def test_family_a_transitions_machine(self) -> None:
        model = _state_diagram(FAMILY_A_DICTS)
        assert isinstance(model, GraphModel)
        states = {n.node_id for n in model.nodes if n.node_type == "state"}
        assert states == {"idle", "ringing", "connected"}

    def test_family_b_python_statemachine(self) -> None:
        model = _state_diagram(FAMILY_B_BASIC)
        states = {n.node_id for n in model.nodes if n.node_type == "state"}
        assert states == {"pending", "confirmed", "shipped"}

    def test_family_c_native_enum(self) -> None:
        model = _state_diagram(FAMILY_C_LITERAL)
        targets = {e.target for e in model.edges if e.edge_type == "transitions_to"}
        assert {"OPEN", "CLOSED"} <= targets

    def test_negative_bare_enum_zero_states(self) -> None:
        model = _state_diagram(NEGATIVE_BARE_ENUM)
        assert len([n for n in model.nodes if n.node_type == "state"]) == 0
