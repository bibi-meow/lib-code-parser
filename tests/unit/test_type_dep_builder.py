"""Unit tests for type_dep_builder module."""

from __future__ import annotations

from lib_code_parser.type_dep_builder import build_type_deps


class TestImportDeps:
    def test_simple_import(self) -> None:
        deps = build_type_deps("import os\n", "mod.py")
        targets = {d.target for d in deps}
        assert "os" in targets

    def test_import_kind(self) -> None:
        deps = build_type_deps("import os\n", "mod.py")
        assert any(d.kind == "imports" for d in deps)

    def test_from_import(self) -> None:
        deps = build_type_deps("from pathlib import Path\n", "mod.py")
        targets = {d.target for d in deps}
        assert "pathlib.Path" in targets

    def test_from_import_no_module(self) -> None:
        # edge case: "from . import something" → module=""
        deps = build_type_deps("from . import util\n", "mod.py")
        targets = {d.target for d in deps}
        assert "util" in targets

    def test_import_alias(self) -> None:
        deps = build_type_deps("import numpy as np\n", "mod.py")
        targets = {d.target for d in deps}
        assert "np" in targets

    def test_multiple_imports(self) -> None:
        source = "import os\nimport sys\n"
        deps = build_type_deps(source, "mod.py")
        targets = {d.target for d in deps}
        assert "os" in targets
        assert "sys" in targets


class TestAnnotationDeps:
    def test_function_param_annotation(self) -> None:
        source = "def foo(x: MyClass): pass\n"
        deps = build_type_deps(source, "mod.py")
        targets = {d.target for d in deps}
        assert "MyClass" in targets

    def test_function_return_annotation(self) -> None:
        source = "def foo() -> MyResult: pass\n"
        deps = build_type_deps(source, "mod.py")
        targets = {d.target for d in deps}
        assert "MyResult" in targets

    def test_source_is_module(self) -> None:
        source = "import os\n"
        deps = build_type_deps(source, "my_module.py")
        for d in deps:
            assert d.source == "my_module"

    def test_empty_source(self) -> None:
        deps = build_type_deps("", "mod.py")
        assert deps == []
