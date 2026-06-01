"""DIA-04 acceptance: package diagram via the public execute() surface.

Exercises the full CodeParserExecutor path and reads
``result.content.package_diagram``. Verifies node_type='package' and
attribute-based containment (D-05/D-06: no schema change, no 'contains' edge).

Traces: DIA-04, DIA-07.
"""

from __future__ import annotations

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.graph_base import GraphModel


def _package_diagram(source: str, path: str) -> GraphModel:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.package_diagram


class TestPackageDiagramAcceptance:
    def test_package_nodes_emitted(self) -> None:
        model = _package_diagram("x = 1\n", "src/foo/bar/baz.py")
        assert isinstance(model, GraphModel)
        node_ids = {n.node_id for n in model.nodes}
        assert node_ids == {"src", "src.foo", "src.foo.bar"}
        assert all(n.node_type == "package" for n in model.nodes)

    def test_containment_via_attributes(self) -> None:
        model = _package_diagram("x = 1\n", "src/foo/bar/baz.py")
        by_id = {n.node_id: n for n in model.nodes}
        assert by_id["src.foo"].attributes == {"parent_package": "src"}
        assert by_id["src.foo.bar"].attributes == {"parent_package": "src.foo"}
        # No 'contains' edge — containment is attribute-only.
        assert model.edges == []

    def test_flat_path_yields_no_packages(self) -> None:
        model = _package_diagram("x = 1\n", "baz.py")
        assert model.nodes == []
