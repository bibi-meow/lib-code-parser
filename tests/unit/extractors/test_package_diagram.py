"""Unit tests for the DIA-04 package_diagram extractor.

Package diagram = directory/namespace hierarchy. Emits
``GraphNode(node_type="package")`` per directory level; containment via
``GraphNode.attributes["parent_package"]`` (D-05/D-06 — no schema change, no
sibling-lib code change, no 'contains' edge).

Traces: DIA-04, DIA-07, DET-04.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations.package_diagram import extract
from lib_code_parser.models.evaluations.graph_base import GraphModel
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _build_cav(source: str, path: str) -> CAV:
    """Build a Python CAV from source (test-side parse only)."""
    return CAV(
        language="python",
        path=path,
        payload=ast.parse(source),
        raw_content=source.encode("utf-8"),
    )


class TestPackageNodes:
    def test_package_node_type_is_plain_str_package(self) -> None:
        """D-05: node_type='package' is a plain str — no Literal/schema change."""
        cav = _build_cav("x = 1\n", "src/order.py")
        model = extract(cav, _CONFIG)
        assert all(n.node_type == "package" for n in model.nodes)
        assert "src" in {n.node_id for n in model.nodes}

    def test_multiple_packages_represented(self) -> None:
        cav = _build_cav("x = 1\n", "src/foo/bar/baz.py")
        model = extract(cav, _CONFIG)
        node_ids = {n.node_id for n in model.nodes}
        assert node_ids == {"src", "src.foo", "src.foo.bar"}

    def test_flat_path_yields_no_packages(self) -> None:
        cav = _build_cav("x = 1\n", "baz.py")
        model = extract(cav, _CONFIG)
        assert model.nodes == []


class TestPackageContainment:
    def test_containment_via_parent_package_attribute(self) -> None:
        """D-06: containment expressed via attributes, NOT a 'contains' edge."""
        cav = _build_cav("x = 1\n", "src/foo/bar/baz.py")
        model = extract(cav, _CONFIG)
        by_id = {n.node_id: n for n in model.nodes}
        assert by_id["src"].attributes == {}
        assert by_id["src.foo"].attributes == {"parent_package": "src"}
        assert by_id["src.foo.bar"].attributes == {"parent_package": "src.foo"}

    def test_no_contains_edge_emitted(self) -> None:
        cav = _build_cav("x = 1\n", "src/foo/baz.py")
        model = extract(cav, _CONFIG)
        # Containment is attribute-based; no edges at all.
        assert model.edges == []


class TestPackageDeterminism:
    def test_nodes_sorted_by_node_id(self) -> None:
        cav = _build_cav("x = 1\n", "src/foo/bar/baz.py")
        model = extract(cav, _CONFIG)
        ids = [n.node_id for n in model.nodes]
        assert ids == sorted(ids)

    def test_windows_and_posix_paths_equivalent(self) -> None:
        """Backslash paths normalize to the same deterministic chain."""
        posix = extract(_build_cav("x = 1\n", "src/foo/baz.py"), _CONFIG)
        win = extract(_build_cav("x = 1\n", "src\\foo\\baz.py"), _CONFIG)
        assert posix.model_dump_json() == win.model_dump_json()

    def test_byte_identical_repeated_extraction(self) -> None:
        a = extract(_build_cav("x = 1\n", "src/foo/bar/baz.py"), _CONFIG)
        b = extract(_build_cav("x = 1\n", "src/foo/bar/baz.py"), _CONFIG)
        assert a.model_dump_json() == b.model_dump_json()


class TestPackageReturnType:
    def test_returns_graphmodel(self) -> None:
        model = extract(_build_cav("x = 1\n", "src/m.py"), _CONFIG)
        assert isinstance(model, GraphModel)
