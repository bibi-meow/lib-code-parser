"""Wave 0 unit tests for the Python Frontend (build_cav).

Behavior under test (Phase 2 plan 02-01):
  - returns a CAV with language="python",
  - payload is an ast.Module,
  - raw_content is carried verbatim,
  - UTF-8 decode uses errors="replace" (no crash on invalid bytes),
  - SyntaxError propagates to the caller (fail-loudly, D-06),
  - ast.parse is called exactly once per build_cav (AST-05 dynamic gate, unit),
  - path metadata is carried to the CAV.

Traces: AST-05, ARC-02.
"""

from __future__ import annotations

import ast

import pytest

from lib_code_parser.frontends.python import build_cav
from lib_code_parser.models.infrastructure.config import ParserConfig


def _config() -> ParserConfig:
    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def test_build_cav_returns_cav_with_language_python() -> None:
    """build_cav returns a CAV with the python discriminator."""
    cav = build_cav(b"def foo(): pass", "foo.py", _config())
    assert cav.language == "python"


def test_build_cav_payload_is_ast_module() -> None:
    """The CAV payload is the parsed ast.Module."""
    cav = build_cav(b"def foo(): pass", "foo.py", _config())
    assert isinstance(cav.payload, ast.Module)


def test_build_cav_carries_raw_content_verbatim() -> None:
    """Input bytes are carried byte-for-byte onto cav.raw_content."""
    raw = b"def foo(): pass"
    cav = build_cav(raw, "foo.py", _config())
    assert cav.raw_content == raw


def test_build_cav_decodes_utf8_with_replace() -> None:
    """Invalid UTF-8 bytes do not crash decode; replace substitutes them.

    errors="replace" is the T-02-03 DoS mitigation: malformed bytes are
    substituted with the U+FFFD replacement char instead of raising
    UnicodeDecodeError. Here the invalid bytes sit inside a comment so the
    replaced source is still syntactically valid Python and parses cleanly.
    """
    raw = b"# \xff\xfe bad bytes \x80\ndef f(): pass\n"
    cav = build_cav(raw, "bad.py", _config())
    assert isinstance(cav.payload, ast.Module)
    assert cav.raw_content == raw


def test_build_cav_propagates_syntax_error() -> None:
    """Malformed source raises SyntaxError (fail-loudly, D-06)."""
    with pytest.raises(SyntaxError):
        build_cav(b"def f(", "syntax_error.py", _config())


def test_build_cav_parses_exactly_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """AST-05 dynamic gate (unit): build_cav calls ast.parse exactly once."""
    real_parse = ast.parse
    call_count = 0

    def spy(*args: object, **kwargs: object) -> ast.Module:
        nonlocal call_count
        call_count += 1
        return real_parse(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(ast, "parse", spy)
    build_cav(b"def foo(): pass", "foo.py", _config())
    assert call_count == 1


def test_build_cav_path_carried_to_cav() -> None:
    """The caller-supplied path is carried onto the CAV."""
    cav = build_cav(b"x = 1", "some/file.py", _config())
    assert cav.path == "some/file.py"
