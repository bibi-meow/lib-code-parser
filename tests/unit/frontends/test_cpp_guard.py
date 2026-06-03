"""Unit tests for the libclang runtime guard (_ensure_libclang_ready).

Behavior under test (Phase 4 plan 04-03), requirements LNG-03 / DET-02:
  - test_abi_pin: a wrong importlib.metadata.version("libclang") raises RuntimeError,
  - test_rejects_set_library_file_override: a non-None Config.library_file raises
    RuntimeError,
  - happy path: in the real (pinned 18.1.1, bundled wheel) environment the guard
    succeeds and sets the module-level _READY flag True.

Each guard-failure assertion explicitly resets the module-level _READY flag to
False first so the idempotency short-circuit does not mask the failure path.

Traces: LNG-03, DET-02.
"""

from __future__ import annotations

import importlib.metadata

import clang.cindex
import pytest

from lib_code_parser.frontends import cpp


def _reset_ready() -> None:
    cpp._READY = False


def test_abi_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    """DET-02: a libclang version other than 18.1.1 raises RuntimeError."""

    def fake_version(name: str) -> str:
        if name == "libclang":
            return "99.0.0"
        return importlib.metadata.version(name)

    monkeypatch.setattr(importlib.metadata, "version", fake_version)
    _reset_ready()
    with pytest.raises(RuntimeError, match="ABI pin"):
        cpp._ensure_libclang_ready()


def test_rejects_set_library_file_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """LNG-03: a caller Config.set_library_file override is rejected."""
    monkeypatch.setattr(clang.cindex.Config, "library_file", "/some/override/libclang.so")
    _reset_ready()
    with pytest.raises(RuntimeError, match="override is rejected"):
        cpp._ensure_libclang_ready()


def test_happy_path_sets_ready() -> None:
    """In the real pinned/bundled environment the guard succeeds and sets _READY."""
    _reset_ready()
    cpp._ensure_libclang_ready()  # must not raise
    assert cpp._READY is True
