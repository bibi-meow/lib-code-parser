"""FR-03: Type dependency extraction acceptance tests (Phase 2 v0.2.0 form).

Consumes the typed ParserConfig + dispatch-driven executor through the public
v0.2.0 surface. CR-01 (Option B): the DEFAULT execute() path is pure & pyright-
free (``resolve_imports=False``), so these acceptance tests run WITHOUT any
pyright dependence — all deps carry the optimistic default ``resolved=True``.
The pyright-hybrid resolution oracle is exercised separately via the opt-in
``resolve_imports=True`` config (and unit tests with a mocked adapter).
"""

from __future__ import annotations

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig
from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE


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
        """Default path (resolve_imports=False): every dep is optimistically
        resolved=True (no pyright invoked)."""
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
