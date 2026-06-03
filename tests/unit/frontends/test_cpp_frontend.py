"""Unit tests for the C++ Frontend (cpp.build_cav).

Behavior under test (Phase 4 plan 04-03):
  - returns a CAV with language="cpp",
  - payload is a clang.cindex.TranslationUnit,
  - raw_content is carried verbatim,
  - UTF-8 decode uses errors="replace" (no crash on invalid bytes),
  - path metadata is carried to the CAV,
  - LNG-05: an unresolved #include surfaces as a diagnostics warning, never an
    exception, and the rest of the cursor tree is still built.

Traces: AST-05, ARC-02, LNG-05.
"""

from __future__ import annotations

from pathlib import Path

import clang.cindex

from lib_code_parser.frontends.cpp import build_cav
from lib_code_parser.models.infrastructure.config import ParserConfig

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "cpp"


def _config() -> ParserConfig:
    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser", language="cpp")


def test_build_cav_returns_cav_with_language_cpp() -> None:
    """build_cav returns a CAV with the cpp discriminator."""
    cav = build_cav(b"struct A {};", "a.cpp", _config())
    assert cav.language == "cpp"


def test_build_cav_payload_is_translation_unit() -> None:
    """The CAV payload is the parsed clang.cindex.TranslationUnit."""
    cav = build_cav(b"struct A {};", "a.cpp", _config())
    assert isinstance(cav.payload, clang.cindex.TranslationUnit)


def test_build_cav_carries_raw_content_verbatim() -> None:
    """Input bytes are carried byte-for-byte onto cav.raw_content."""
    raw = b"struct A {};"
    cav = build_cav(raw, "a.cpp", _config())
    assert cav.raw_content == raw


def test_build_cav_decodes_utf8_with_replace() -> None:
    """Invalid UTF-8 bytes do not crash decode; replace substitutes them.

    The invalid bytes sit inside a // comment so the replaced source is still
    syntactically valid C++ and parses cleanly.
    """
    raw = b"// \xff\xfe bad bytes \x80\nstruct A {};\n"
    cav = build_cav(raw, "bad.cpp", _config())
    assert isinstance(cav.payload, clang.cindex.TranslationUnit)
    assert cav.raw_content == raw


def test_build_cav_path_carried_to_cav() -> None:
    """The caller-supplied path is carried onto the CAV."""
    cav = build_cav(b"int x = 1;", "some/file.cpp", _config())
    assert cav.path == "some/file.cpp"


def test_missing_include_warns() -> None:
    """LNG-05: an unresolved #include warns rather than raising.

    build_cav must NOT raise; tu.diagnostics must contain an entry mentioning the
    missing header; the valid `struct Ok` cursor must still be present in the tree.
    """
    raw = (_FIXTURES / "missing_include.cpp").read_bytes()
    cav = build_cav(raw, "missing_include.cpp", _config())  # must not raise
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit)

    diag_messages = [d.spelling for d in tu.diagnostics]
    assert any("missing_header" in msg for msg in diag_messages), diag_messages

    struct_names = {
        c.spelling
        for c in tu.cursor.walk_preorder()
        if c.kind == clang.cindex.CursorKind.STRUCT_DECL
    }
    assert "Ok" in struct_names, struct_names
