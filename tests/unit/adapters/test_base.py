"""Wave 0 subprocess hardening tests for lib_code_parser.adapters.base.

These tests run live `sys.executable` subprocesses (no mocks) to assert the
six hardening invariants of `run_subprocess()` and the ABC contract of
`SubprocessAdapter`.

Traces: ARC-03, DET-05.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
from pydantic import BaseModel

from lib_code_parser.adapters.base import SubprocessAdapter, run_subprocess

# ---------------------------------------------------------------------------
# Deterministic env injection — assert each of the 4 _DETERMINISTIC_ENV keys
# ---------------------------------------------------------------------------


def test_run_subprocess_sets_lc_all_c() -> None:
    result = run_subprocess(
        [sys.executable, "-c", "import os; print(os.environ.get('LC_ALL', ''))"],
        cwd=os.getcwd(),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "C" in result.stdout


def test_run_subprocess_sets_pythonhashseed_zero() -> None:
    result = run_subprocess(
        [sys.executable, "-c", "import os; print(os.environ.get('PYTHONHASHSEED', ''))"],
        cwd=os.getcwd(),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "0" in result.stdout


def test_run_subprocess_sets_lang_c() -> None:
    result = run_subprocess(
        [sys.executable, "-c", "import os; print(os.environ.get('LANG', ''))"],
        cwd=os.getcwd(),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "C" in result.stdout


def test_run_subprocess_sets_pythonioencoding_utf8() -> None:
    result = run_subprocess(
        [sys.executable, "-c", "import os; print(os.environ.get('PYTHONIOENCODING', ''))"],
        cwd=os.getcwd(),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "utf-8" in result.stdout


# ---------------------------------------------------------------------------
# extra_env overlay
# ---------------------------------------------------------------------------


def test_run_subprocess_extra_env_overlays() -> None:
    result = run_subprocess(
        [sys.executable, "-c", "import os; print(os.environ.get('FOO', ''))"],
        cwd=os.getcwd(),
        timeout=30,
        extra_env={"FOO": "bar"},
    )
    assert result.returncode == 0, result.stderr
    assert "bar" in result.stdout


# ---------------------------------------------------------------------------
# Timeout — must propagate subprocess.TimeoutExpired
# ---------------------------------------------------------------------------


def test_run_subprocess_raises_on_timeout() -> None:
    with pytest.raises(subprocess.TimeoutExpired):
        run_subprocess(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            cwd=os.getcwd(),
            timeout=1,
        )


# ---------------------------------------------------------------------------
# shell=False — `$PATH` must appear literally (not expanded by a shell)
# ---------------------------------------------------------------------------


def test_run_subprocess_does_not_use_shell() -> None:
    result = run_subprocess(
        [sys.executable, "-c", "print('$PATH')"],
        cwd=os.getcwd(),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    # Literal — never expanded by any shell because shell=False.
    assert "$PATH" in result.stdout


# ---------------------------------------------------------------------------
# Return type — CompletedProcess[str] with stdout/stderr/returncode
# ---------------------------------------------------------------------------


def test_run_subprocess_returns_completed_process() -> None:
    result = run_subprocess(
        [sys.executable, "-c", "print('hello'); import sys; print('err', file=sys.stderr)"],
        cwd=os.getcwd(),
        timeout=30,
    )
    assert hasattr(result, "stdout")
    assert hasattr(result, "stderr")
    assert hasattr(result, "returncode")
    assert isinstance(result.stdout, str)
    assert isinstance(result.stderr, str)
    assert isinstance(result.returncode, int)


# ---------------------------------------------------------------------------
# UTF-8 decoding — result.stdout is str (decoded), not bytes
# ---------------------------------------------------------------------------


def test_run_subprocess_decodes_utf8() -> None:
    # Plain ASCII echo — assert the result is a decoded str regardless of platform.
    # On Windows, decoding via cp1252 (the default for text=True without explicit
    # encoding) would corrupt non-ASCII bytes; we force UTF-8 + errors=replace.
    result = run_subprocess(
        [sys.executable, "-c", "print('plain ascii line')"],
        cwd=os.getcwd(),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert isinstance(result.stdout, str)
    assert not isinstance(result.stdout, bytes)
    assert "plain ascii line" in result.stdout


# ---------------------------------------------------------------------------
# cwd is keyword-only required
# ---------------------------------------------------------------------------


def test_run_subprocess_requires_cwd() -> None:
    with pytest.raises(TypeError):
        # Intentionally calling without the required keyword-only `cwd`.
        run_subprocess([sys.executable, "-c", "print('x')"])  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# SubprocessAdapter ABC contract
# ---------------------------------------------------------------------------


def test_subprocess_adapter_is_abstract() -> None:
    with pytest.raises(TypeError):
        SubprocessAdapter()  # type: ignore[abstract]


class _FakeOutput(BaseModel):
    stdout: str
    stderr: str
    returncode: int


class _FakeAdapter(SubprocessAdapter):
    """In-test concrete subclass to validate the ABC template-method wiring."""

    def tool_argv(self, target_path: str) -> list[str]:
        # Echo the target_path back through stdout so we can assert it flowed through.
        return [sys.executable, "-c", f"print({target_path!r})"]

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> _FakeOutput:
        return _FakeOutput(stdout=stdout, stderr=stderr, returncode=returncode)


def test_subprocess_adapter_subclass_works() -> None:
    adapter = _FakeAdapter()
    result = adapter.execute("hello-token", cwd=os.getcwd())
    assert isinstance(result, _FakeOutput)
    assert "hello-token" in result.stdout
    assert result.returncode == 0
