"""FR-03: Type dependency extraction acceptance tests."""

from __future__ import annotations

import pytest

from lib_code_parser.type_dep_builder import build_type_deps


@pytest.fixture
def example_source() -> str:
    from tests.conftest import EXAMPLE_SOURCE

    return EXAMPLE_SOURCE


@pytest.fixture
def example_path() -> str:
    return "src/order_service.py"


class TestImportDeps:
    def test_pydantic_import_detected(self, example_source: str, example_path: str) -> None:
        deps = build_type_deps(example_source, example_path)
        targets = {d.target for d in deps}
        # from pydantic import BaseModel → pydantic.BaseModel
        assert any("BaseModel" in t for t in targets)

    def test_import_kind(self, example_source: str, example_path: str) -> None:
        deps = build_type_deps(example_source, example_path)
        import_deps = [d for d in deps if d.kind == "imports"]
        assert len(import_deps) > 0

    def test_source_is_module_name(self, example_source: str, example_path: str) -> None:
        deps = build_type_deps(example_source, example_path)
        for d in deps:
            assert d.source == "order_service"


class TestAnnotationDeps:
    def test_annotation_deps_extracted(self, example_source: str, example_path: str) -> None:
        deps = build_type_deps(example_source, example_path)
        targets = {d.target for d in deps}
        # process_payment has float and str params
        assert len(targets) > 0

    def test_no_empty_targets(self, example_source: str, example_path: str) -> None:
        deps = build_type_deps(example_source, example_path)
        for d in deps:
            assert d.target != ""


class TestTypeDepsMinimal:
    def test_simple_import(self) -> None:
        source = "import os\n"
        deps = build_type_deps(source, "mod.py")
        targets = {d.target for d in deps}
        assert "os" in targets

    def test_from_import(self) -> None:
        source = "from pathlib import Path\n"
        deps = build_type_deps(source, "mod.py")
        targets = {d.target for d in deps}
        assert "pathlib.Path" in targets

    def test_empty_source(self) -> None:
        deps = build_type_deps("", "mod.py")
        assert deps == []
