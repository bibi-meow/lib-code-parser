"""DIA-03 acceptance: component diagram via the public execute() surface.

Exercises the full CodeParserExecutor path (frontend → primitives → EVALUATIONS
walk) and reads ``result.content.component_diagram``.

Traces: DIA-03, DIA-07.
"""

from __future__ import annotations

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.graph_base import GraphModel


def _component_diagram(source: str, path: str) -> GraphModel:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.component_diagram


class TestComponentDiagramAcceptance:
    def test_imports_become_imports_edges(self) -> None:
        model = _component_diagram("import os\nfrom m import N\n", "pkg/app.py")
        assert isinstance(model, GraphModel)
        targets = {e.target for e in model.edges}
        assert {"os", "m.N"} <= targets
        assert all(e.edge_type == "imports" for e in model.edges)

    def test_component_nodes_present(self) -> None:
        model = _component_diagram("import os\n", "pkg/app.py")
        node_ids = {n.node_id for n in model.nodes}
        assert "app" in node_ids
        assert all(n.node_type == "component" for n in model.nodes)

    def test_no_imports_yields_self_node_only(self) -> None:
        model = _component_diagram("x = 1\n", "pkg/app.py")
        assert {n.node_id for n in model.nodes} == {"app"}
        assert model.edges == []
