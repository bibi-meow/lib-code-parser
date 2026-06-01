"""DIA-01 acceptance: class diagram via the public execute() surface.

Exercises the full CodeParserExecutor path and reads
``result.content.class_diagram``. Verifies inheritance + composition/
aggregation/association edges and that no catch-all 'uses' edge appears.

Traces: DIA-01, DIA-07.
"""

from __future__ import annotations

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.graph_base import GraphModel

_SOURCE = (
    "from typing import Optional\n"
    "class A:\n    pass\n"
    "class Engine:\n    pass\n"
    "class B(A):\n"
    "    x: Engine\n"
    "    y: Optional[Engine]\n"
    "    w: SomeUnknown\n"
    "    n: int\n"
)


def _class_diagram(source: str, path: str) -> GraphModel:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.class_diagram


class TestClassDiagramAcceptance:
    def test_relationship_spectrum(self) -> None:
        model = _class_diagram(_SOURCE, "src/shapes.py")
        assert isinstance(model, GraphModel)
        edges = {(e.source, e.target, e.edge_type) for e in model.edges}
        assert ("B", "A", "inherits") in edges
        assert ("B", "Engine", "composes") in edges
        assert ("B", "Engine", "aggregates") in edges
        assert ("B", "SomeUnknown", "associates") in edges

    def test_no_uses_edge_and_builtin_skipped(self) -> None:
        model = _class_diagram(_SOURCE, "src/shapes.py")
        kinds = {e.edge_type for e in model.edges}
        assert "uses" not in kinds
        targets = {e.target for e in model.edges}
        assert "int" not in targets

    def test_class_nodes(self) -> None:
        model = _class_diagram(_SOURCE, "src/shapes.py")
        node_ids = {n.node_id for n in model.nodes}
        assert node_ids == {"A", "Engine", "B"}
        assert all(n.node_type == "class" for n in model.nodes)
