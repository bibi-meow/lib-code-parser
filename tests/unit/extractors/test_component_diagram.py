"""Unit tests for the DIA-03 component_diagram extractor.

Component diagram = module-boundary import dependency graph. Pulls the Phase 2
``type_deps`` primitive, keeps ``kind=="imports"`` facts, maps them to
``GraphEdge(edge_type="imports")`` + ``GraphNode(node_type="component")``.

Traces: DIA-03, DIA-07, DET-04.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations.component_diagram import extract
from lib_code_parser.models.evaluations.graph_base import GraphModel
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _build_cav(source: str, path: str = "m.py") -> CAV:
    """Build a Python CAV from source (test-side parse only)."""
    return CAV(
        language="python",
        path=path,
        payload=ast.parse(source),
        raw_content=source.encode("utf-8"),
    )


class TestComponentEdges:
    def test_import_emits_imports_edge(self) -> None:
        """`import os` → GraphEdge(edge_type='imports', target='os')."""
        cav = _build_cav("import os\n", "m.py")
        model = extract(cav, _CONFIG)
        targets = {e.target for e in model.edges}
        assert "os" in targets
        assert all(e.edge_type == "imports" for e in model.edges)

    def test_from_import_emits_qualified_target(self) -> None:
        """`from m import N` → GraphEdge(target='m.N')."""
        cav = _build_cav("from m import N\n", "src.py")
        model = extract(cav, _CONFIG)
        targets = {e.target for e in model.edges}
        assert "m.N" in targets

    def test_source_is_importing_module(self) -> None:
        cav = _build_cav("import os\n", "pkg/order.py")
        model = extract(cav, _CONFIG)
        assert all(e.source == "order" for e in model.edges)

    def test_no_catch_all_edge_kind(self) -> None:
        """Pitfall 2: never emit 'uses'/'depends'/'other' edges."""
        cav = _build_cav("import os\nfrom m import N\n", "m.py")
        model = extract(cav, _CONFIG)
        kinds = {e.edge_type for e in model.edges}
        assert kinds == {"imports"}


class TestComponentNodes:
    def test_module_node_present(self) -> None:
        cav = _build_cav("import os\n", "order.py")
        model = extract(cav, _CONFIG)
        node_ids = {n.node_id for n in model.nodes}
        assert "order" in node_ids
        assert all(n.node_type == "component" for n in model.nodes)

    def test_imported_target_is_a_node(self) -> None:
        cav = _build_cav("import os\n", "order.py")
        model = extract(cav, _CONFIG)
        node_ids = {n.node_id for n in model.nodes}
        assert "os" in node_ids

    def test_no_import_only_self_node(self) -> None:
        cav = _build_cav("x = 1\n", "lonely.py")
        model = extract(cav, _CONFIG)
        assert {n.node_id for n in model.nodes} == {"lonely"}
        assert model.edges == []


class TestComponentDeterminism:
    def test_nodes_sorted_by_node_id(self) -> None:
        cav = _build_cav("import zlib\nimport abc\n", "m.py")
        model = extract(cav, _CONFIG)
        ids = [n.node_id for n in model.nodes]
        assert ids == sorted(ids)

    def test_edges_sorted_by_composite_key(self) -> None:
        cav = _build_cav("import zlib\nimport abc\n", "m.py")
        model = extract(cav, _CONFIG)
        keys = [(e.source, e.target, e.edge_type, e.label) for e in model.edges]
        assert keys == sorted(keys)

    def test_byte_identical_repeated_extraction(self) -> None:
        """DET-04: byte-stable output (test runs under PYTHONHASHSEED=random in CI)."""
        src = "import zlib\nimport abc\nfrom m import N, P\n"
        a = extract(_build_cav(src, "m.py"), _CONFIG)
        b = extract(_build_cav(src, "m.py"), _CONFIG)
        assert a.model_dump_json() == b.model_dump_json()


class TestComponentReturnType:
    def test_returns_graphmodel(self) -> None:
        model = extract(_build_cav("import os\n", "m.py"), _CONFIG)
        assert isinstance(model, GraphModel)
