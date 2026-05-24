"""Wave 0 unit tests for lib_code_parser._paths.get_module_name (ARC-04, DET-04).

Traces: ARC-04, DET-04
"""

from pathlib import Path

from lib_code_parser._paths import get_module_name


class TestGetModuleNameBasic:
    """Happy path: file stem extraction parity with v0.1.0 _get_module_name."""

    def test_get_module_name_basic(self) -> None:
        assert get_module_name("foo.py") == "foo"

    def test_get_module_name_with_directory(self) -> None:
        # Forward-slash path: cross-OS deterministic via pathlib
        assert get_module_name("src/order_service.py") == "order_service"

    def test_get_module_name_with_dots(self) -> None:
        # Path.stem strips only the LAST extension — preserves v0.1.0 behavior
        assert get_module_name("path/to/my.module.py") == "my.module"

    def test_get_module_name_no_extension(self) -> None:
        assert get_module_name("Makefile") == "Makefile"

    def test_get_module_name_empty(self) -> None:
        assert get_module_name("") == ""


class TestGetModuleNameSingleSource:
    """Phase 1 RELAXED gate: get_module_name is defined exactly once in _paths.py.

    The hard "no _get_module_name duplication outside _paths.py" gate is asserted
    by Plan 09's parity test (after Plan 09 patches the 4 v0.1.0 extractors to
    shim through _paths.get_module_name).
    """

    def test_no_duplicate_module_name_helper(self) -> None:
        # _paths.py is the single source of truth — must define get_module_name once
        paths_py = (
            Path(__file__).resolve().parents[2] / "lib_code_parser" / "_paths.py"
        )
        content = paths_py.read_text(encoding="utf-8")
        assert content.count("def get_module_name(") == 1
