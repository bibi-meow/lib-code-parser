"""DIA-06 acceptance: return-value substitution via the public execute() surface.

Verifies the N-level resolution, cycle-safety, and the single
``source_unresolved=True`` placeholder for unresolvable cases through the full
CodeParserExecutor path.

Traces: DIA-06, DIA-07.
"""

from __future__ import annotations

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.graph_base import GraphModel
from tests.unit.extractors.fixtures.fsm_samples import (
    SUBST_CYCLIC,
    SUBST_EXTERNAL,
    SUBST_NLEVEL,
    SUBST_RESOLVED,
)


def _state_diagram(source: str, path: str = "pkg/app.py") -> GraphModel:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.state_diagram


class TestReturnSubstitutionAcceptance:
    def test_resolved_concrete_edges(self) -> None:
        model = _state_diagram(SUBST_RESOLVED)
        targets = {e.target for e in model.edges if e.edge_type == "transitions_to"}
        assert {"A", "B"} <= targets
        assert [e for e in model.edges if e.source_unresolved] == []

    def test_nlevel_resolves(self) -> None:
        model = _state_diagram(SUBST_NLEVEL)
        targets = {e.target for e in model.edges if e.edge_type == "transitions_to"}
        assert "B" in targets

    def test_cycle_terminates(self) -> None:
        # Completes without hang/recursion error.
        model = _state_diagram(SUBST_CYCLIC)
        assert isinstance(model, GraphModel)
        assert len([e for e in model.edges if e.source_unresolved]) == 1

    def test_external_one_placeholder(self) -> None:
        model = _state_diagram(SUBST_EXTERNAL)
        unresolved = [e for e in model.edges if e.source_unresolved]
        assert len(unresolved) == 1
        assert unresolved[0].source_unresolved is True
