"""FR-03: Type dependency extraction acceptance tests (Phase 2 v0.2.0 form).

Consumes the typed ParserConfig + dispatch-driven executor through the public
v0.2.0 surface. The type_deps extractor invokes the PyrightAdapter subprocess
to annotate the `resolved` flag (CONTEXT.md D-07-revised), so the whole module
is skipped when pyright is not installed (end-to-end acceptance fidelity).
"""

from __future__ import annotations

import subprocess

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig
from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE


def _has_pyright() -> bool:
    try:
        subprocess.run(
            ["pyright", "--version"],
            capture_output=True,
            timeout=30.0,
            check=False,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


pytestmark = pytest.mark.skipif(
    not _has_pyright(), reason="pyright not installed (type_deps extractor requires it)"
)


def _type_deps(source: str, path: str):
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.type_deps


@pytest.fixture
def example_deps():
    return _type_deps(EXAMPLE_SOURCE, EXAMPLE_PATH)


class TestImportDeps:
    def test_pydantic_import_detected(self, example_deps) -> None:
        targets = {d.target for d in example_deps}
        # from pydantic import BaseModel -> pydantic.BaseModel
        assert any("BaseModel" in t for t in targets)

    def test_import_kind(self, example_deps) -> None:
        import_deps = [d for d in example_deps if d.kind == "imports"]
        assert len(import_deps) > 0

    def test_source_is_module_name(self, example_deps) -> None:
        for d in example_deps:
            assert d.source == "order_service"


class TestAnnotationDeps:
    def test_annotation_deps_extracted(self, example_deps) -> None:
        targets = {d.target for d in example_deps}
        assert len(targets) > 0

    def test_no_empty_targets(self, example_deps) -> None:
        for d in example_deps:
            assert d.target != ""


class TestResolvedFlag:
    def test_resolved_field_present(self, example_deps) -> None:
        """Phase 2 additive field: every TypeDep carries a bool `resolved`."""
        for d in example_deps:
            assert isinstance(d.resolved, bool)

    def test_clean_source_all_resolved(self, example_deps) -> None:
        """Clean source (pydantic / typing installed) resolves all imports."""
        assert all(d.resolved for d in example_deps)


class TestTypeDepsMinimal:
    def test_simple_import(self) -> None:
        deps = _type_deps("import os\n", "mod.py")
        targets = {d.target for d in deps}
        assert "os" in targets

    def test_from_import(self) -> None:
        deps = _type_deps("from pathlib import Path\n", "mod.py")
        targets = {d.target for d in deps}
        assert "pathlib.Path" in targets

    def test_empty_source(self) -> None:
        deps = _type_deps("", "mod.py")
        assert deps == []
