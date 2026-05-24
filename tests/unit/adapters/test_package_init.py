"""Package-level import contract for lib_code_parser.adapters.

Asserts that the public symbols `run_subprocess` and `SubprocessAdapter` are
re-exported at the package barrel so callers may write either:

    from lib_code_parser.adapters import run_subprocess, SubprocessAdapter

or the sub-module path:

    from lib_code_parser.adapters.base import run_subprocess, SubprocessAdapter

Both must resolve to the same object.

Traces: ARC-03, DET-05.
"""

from __future__ import annotations

import lib_code_parser.adapters as adapters_pkg
from lib_code_parser.adapters import SubprocessAdapter, run_subprocess
from lib_code_parser.adapters.base import SubprocessAdapter as SubprocessAdapter_base
from lib_code_parser.adapters.base import run_subprocess as run_subprocess_base


def test_package_reexports_run_subprocess_identity() -> None:
    assert run_subprocess is run_subprocess_base


def test_package_reexports_subprocess_adapter_identity() -> None:
    assert SubprocessAdapter is SubprocessAdapter_base


def test_package_all_lists_public_symbols() -> None:
    assert hasattr(adapters_pkg, "__all__")
    assert set(adapters_pkg.__all__) >= {"run_subprocess", "SubprocessAdapter"}
