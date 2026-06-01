"""DIA-02 acceptance: sequence diagram via the public execute() surface.

Exercises the full CodeParserExecutor path (frontend → primitives → EVALUATIONS
walk) and reads ``result.content.sequence_diagram``. Verifies the linear
``calls`` edges (D-07 must-have) and the SP-2 branch-frame labels (SHIP).

Traces: DIA-02, DIA-07.
"""

from __future__ import annotations

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.graph_base import GraphModel


def _sequence_diagram(source: str, path: str) -> GraphModel:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.sequence_diagram


class TestSequenceDiagramAcceptance:
    def test_calls_become_calls_edges(self) -> None:
        model = _sequence_diagram(
            "def a():\n    return b()\ndef b():\n    return 1\n", "pkg/app.py"
        )
        assert isinstance(model, GraphModel)
        pairs = {(e.source, e.target) for e in model.edges}
        assert ("app.a", "b") in pairs
        assert all(e.edge_type == "calls" for e in model.edges)

    def test_participants_present(self) -> None:
        model = _sequence_diagram("def a():\n    return b()\n", "pkg/app.py")
        node_ids = {n.node_id for n in model.nodes}
        assert "app.a" in node_ids
        assert "b" in node_ids
        assert all(n.node_type == "participant" for n in model.nodes)

    def test_branch_frames_labelled(self) -> None:
        source = (
            "def h(items):\n"
            "    setup()\n"
            "    if items:\n"
            "        notify()\n"
            "    for it in items:\n"
            "        handle(it)\n"
        )
        model = _sequence_diagram(source, "pkg/app.py")
        labels = {(e.target, e.label) for e in model.edges}
        assert ("setup", "") in labels
        assert ("notify", "alt") in labels
        assert ("handle", "loop") in labels

    def test_no_calls_yields_no_edges(self) -> None:
        model = _sequence_diagram("def lonely():\n    x = 1\n", "pkg/app.py")
        assert model.edges == []
