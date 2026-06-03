"""Unit tests for the libclang runtime guard (_ensure_libclang_ready).

Behavior under test (Phase 4 plan 04-03), requirements LNG-03 / DET-02:
  - test_abi_pin: a wrong importlib.metadata.version("libclang") raises RuntimeError,
  - test_rejects_set_library_file_override: a non-None Config.library_file raises
    RuntimeError,
  - test_rejects_override_after_first_parse: SC#2 holds per-parse — an override set
    AFTER _READY is True is still rejected (BL-02),
  - happy path: in the real (pinned 18.1.1, bundled wheel) environment the guard
    succeeds and sets the module-level _READY flag True.

Every test mutates module/Config state via ``monkeypatch.setattr`` ONLY, so the
``_READY`` flag and ``Config.library_file`` auto-revert at teardown and no global
state leaks across tests — the tests are ordering-independent (BL-01).

Traces: LNG-03, DET-02.
"""

from __future__ import annotations

import importlib.metadata
import pathlib
import re

import pytest
from clang.cindex import Config

from lib_code_parser.frontends import cpp


def test_abi_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    """DET-02: a libclang version other than 18.1.1 raises RuntimeError."""

    def fake_version(name: str) -> str:
        if name == "libclang":
            return "99.0.0"
        return importlib.metadata.version(name)

    monkeypatch.setattr(importlib.metadata, "version", fake_version)
    monkeypatch.setattr(cpp, "_READY", False)
    with pytest.raises(RuntimeError, match="ABI pin"):
        cpp._ensure_libclang_ready()


def test_rejects_set_library_file_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """LNG-03: a caller Config.set_library_file override is rejected."""
    monkeypatch.setattr(Config, "library_file", "/some/override/libclang.so", raising=False)
    monkeypatch.setattr(cpp, "_READY", False)
    with pytest.raises(RuntimeError, match="override is rejected"):
        cpp._ensure_libclang_ready()


def test_rejects_override_after_first_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    """BL-02: SC#2 holds per-parse — an override set AFTER _READY is rejected.

    The cheap override-rejection check runs on EVERY call (not gated by _READY),
    so a caller that calls set_library_file(...) after the first successful parse
    cannot silently swap the bundled libclang for the rest of the process.
    """
    # Simulate "already parsed once": _READY is True (dylib smoke test done).
    monkeypatch.setattr(cpp, "_READY", True)
    monkeypatch.setattr(Config, "library_file", "/late/override/libclang.so", raising=False)
    with pytest.raises(RuntimeError, match="override is rejected"):
        cpp._ensure_libclang_ready()


def test_happy_path_sets_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    """In the real pinned/bundled environment the guard succeeds and sets _READY."""
    monkeypatch.setattr(cpp, "_READY", False)
    cpp._ensure_libclang_ready()  # must not raise
    assert cpp._READY is True


def test_expected_version_matches_pyproject_pin() -> None:
    """IN-04: _EXPECTED_VERSION must equal the libclang== pin in pyproject.toml.

    A drift between the runtime ABI guard and the installed pin would make the
    guard reject the very wheel the package ships (or vice versa); this test
    fails CI on such a drift so the two stay a single source of truth.
    """
    pyproject = pathlib.Path(__file__).resolve().parents[3] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r"libclang==([0-9]+\.[0-9]+\.[0-9]+)", text)
    assert m, "could not find a 'libclang==X.Y.Z' pin in pyproject.toml"
    assert cpp._EXPECTED_VERSION == m.group(1), (
        f"_EXPECTED_VERSION ({cpp._EXPECTED_VERSION!r}) drifted from the "
        f"pyproject libclang pin ({m.group(1)!r})"
    )
