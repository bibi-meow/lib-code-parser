"""Unit tests for lib_code_parser._cpp_cursor shared helpers.

Covers the TRC-03 byte-identical regex parity, the main-file cursor filter,
the namespace-qualified node_id helper (with get_usr() fallback), and the
composes/aggregates/associates/none field-relation classifier (D-04).
"""

from __future__ import annotations

import os
import pathlib
import re

import pytest
from clang.cindex import CursorKind

from lib_code_parser import _cpp_cursor as h
from tests.conftest import build_cpp_cav


def test_trace_regex_byte_identical_to_python() -> None:
    """The TRC-03 regex literal in _cpp_cursor must match functions.py exactly."""
    fn = pathlib.Path("lib_code_parser/extractors/primitives/functions.py").read_text(
        encoding="utf-8"
    )
    m = re.search(r"_TRACE_TAGS_RE = re\.compile\((.*?)\)", fn)
    assert m, "could not locate _TRACE_TAGS_RE in functions.py"
    helper = pathlib.Path("lib_code_parser/_cpp_cursor.py").read_text(encoding="utf-8")
    assert m.group(1) in helper, "TRC-03 regex must be byte-identical to functions.py"


def test_extract_trace_tags_parses_refs() -> None:
    tags = h.extract_trace_tags("Traces: REQ-9, US-3")
    assert tags and tags[0].tag == "Traces"
    assert tags[0].refs == ["REQ-9", "US-3"]


def test_extract_trace_tags_empty() -> None:
    assert h.extract_trace_tags("") == []
    assert h.extract_trace_tags("no tags here") == []


def _find(tu, kind, spelling, path):
    for c in tu.cursor.walk_preorder():
        f = c.location.file
        if f is not None and f.name == path and c.kind == kind and c.spelling == spelling:
            return c
    raise AssertionError(f"no {kind} {spelling!r} found")


def test_in_main_file_filters_headers() -> None:
    cav = build_cpp_cav("struct Ok { int v; };", "main.cpp")
    tu = cav.payload
    ok = _find(tu, CursorKind.STRUCT_DECL, "Ok", "main.cpp")
    assert h._in_main_file(ok, "main.cpp") is True
    # The translation-unit root cursor has no location.file -> filtered out.
    assert h._in_main_file(tu.cursor, "main.cpp") is False


def test_in_main_file_normalizes_dotslash_path() -> None:
    """CR-02: a './'-prefixed parse path still matches its cursors (not silent-empty).

    libclang collapses the ``./`` prefix in ``location.file.name`` so a
    byte-exact compare would drop every cursor; the normalized compare must
    still match.
    """
    cav = build_cpp_cav("struct Ok { int v; };", "./relations.cpp")
    tu = cav.payload
    matched = [
        c
        for c in tu.cursor.walk_preorder()
        if c.kind == CursorKind.STRUCT_DECL
        and c.spelling == "Ok"
        and h._in_main_file(c, "./relations.cpp")
    ]
    assert matched, "normalized path compare must match the './relations.cpp' main file"


def test_in_main_file_normalizes_redundant_segments() -> None:
    """CR-02: a redundant './' segment in the caller path still matches."""
    cav = build_cpp_cav("struct Ok { int v; };", "src/sub/main.cpp")
    tu = cav.payload
    ok = _find(tu, CursorKind.STRUCT_DECL, "Ok", "src/sub/main.cpp")
    assert h._in_main_file(ok, "src/./sub/main.cpp") is True


@pytest.mark.skipif(os.sep != "\\", reason="backslash normalization is Windows-only")
def test_in_main_file_normalizes_backslash_path() -> None:
    """CR-02: on Windows a backslash-separated caller path still matches."""
    cav = build_cpp_cav("struct Ok { int v; };", "src/sub/main.cpp")
    tu = cav.payload
    ok = _find(tu, CursorKind.STRUCT_DECL, "Ok", "src/sub/main.cpp")
    assert h._in_main_file(ok, "src\\sub\\main.cpp") is True


def test_qualified_node_id_namespace_qualified() -> None:
    src = "namespace a { namespace b { struct Calc { int add(int x); }; } }"
    cav = build_cpp_cav(src, "q.cpp")
    tu = cav.payload
    add = _find(tu, CursorKind.CXX_METHOD, "add", "q.cpp")
    assert h.qualified_node_id(add) == "a.b.Calc.add"
    calc = _find(tu, CursorKind.STRUCT_DECL, "Calc", "q.cpp")
    assert h.qualified_node_id(calc) == "a.b.Calc"


def test_qualified_node_id_stable_across_runs() -> None:
    src = "struct S { int f(); };"
    a = build_cpp_cav(src, "s.cpp").payload
    b = build_cpp_cav(src, "s.cpp").payload
    fa = _find(a, CursorKind.CXX_METHOD, "f", "s.cpp")
    fb = _find(b, CursorKind.CXX_METHOD, "f", "s.cpp")
    assert h.qualified_node_id(fa) == h.qualified_node_id(fb) == "S.f"


def test_qualified_node_id_anonymous_stays_in_dotted_namespace() -> None:
    """CR-01: an empty-spelling decl gets a synthetic segment, never a bare USR.

    An anonymous namespace (``namespace { ... }``) is the deterministic
    empty-``spelling`` case in this libclang build. Its id must stay in the
    dotted namespace (carry a ``<anonymous@`` segment) rather than collapsing
    to a raw ``c:@...`` USR that would break node_id-keyed merge/dedup, and it
    must be stable across runs for identical input.
    """
    src = "namespace { int g; }"
    anon_a = None
    for c in build_cpp_cav(src, "anon.cpp").payload.cursor.walk_preorder():
        f = c.location.file
        if f is not None and f.name == "anon.cpp" and c.kind == CursorKind.NAMESPACE:
            assert not c.spelling, "fixture must produce an empty-spelling namespace"
            anon_a = c
            break
    assert anon_a is not None, "expected an anonymous namespace (empty spelling)"

    ns_id = h.qualified_node_id(anon_a)
    assert not ns_id.startswith("c:"), "must not return a bare USR"
    assert "<anonymous@" in ns_id, "empty-spelling decl must carry the synthetic segment"

    # Deterministic across runs for identical bytes.
    anon_b = None
    for c in build_cpp_cav(src, "anon.cpp").payload.cursor.walk_preorder():
        f = c.location.file
        if f is not None and f.name == "anon.cpp" and c.kind == CursorKind.NAMESPACE:
            anon_b = c
            break
    assert anon_b is not None
    assert h.qualified_node_id(anon_b) == ns_id


def test_field_relation_spectrum() -> None:
    # Widget is forward-declared (incomplete) -> known as a reference but
    # undecidable as ownership: the honest "associates" case. (A pointer to a
    # name with no declaration at all is recovered by libclang to int* under
    # PARSE_INCOMPLETE, so a forward declaration is the deterministic associates
    # fixture; the never-declared form is exercised in the relations.cpp
    # acceptance path as a no-crash/no-edge case.)
    src = (
        "class Widget;\n"
        "struct Point { int x; };\n"
        "class Diagram {\n"
        "  Point center;\n"  # value of known -> composes
        "  Point* parent;\n"  # pointer of known -> aggregates
        "  Point& ref;\n"  # reference of known -> aggregates
        "  int count;\n"  # builtin -> None
        "  Widget* widget;\n"  # pointer of forward-declared -> associates
        "};\n"
    )
    cav = build_cpp_cav(src, "rel.cpp")
    tu = cav.payload
    known = {"Point", "Diagram"}

    def rel(name: str):
        fc = _find(tu, CursorKind.FIELD_DECL, name, "rel.cpp")
        return h.field_relation(fc, known)

    assert rel("center") == ("composes", "Point")
    assert rel("parent") == ("aggregates", "Point")
    assert rel("ref") == ("aggregates", "Point")
    assert rel("count") is None
    assert rel("widget") == ("associates", "Widget")


def test_field_relation_const_ref_strips_cv_qualifier() -> None:
    """WR-03: a ``const Point&`` member resolves to ``Point`` (aggregates), not associates.

    Without stripping the leading ``const `` cv-qualifier the base would be
    ``const Point`` which never matches known_classes, silently degrading the
    classification to ``associates``.
    """
    src = (
        "struct Point { int x; };\n"
        "class Diagram {\n"
        "  const Point& cref;\n"  # const reference of known -> aggregates
        "  const Point* cptr;\n"  # const pointer of known -> aggregates
        "};\n"
    )
    cav = build_cpp_cav(src, "cv.cpp")
    tu = cav.payload
    known = {"Point", "Diagram"}

    def rel(name: str):
        fc = _find(tu, CursorKind.FIELD_DECL, name, "cv.cpp")
        return h.field_relation(fc, known)

    assert rel("cref") == ("aggregates", "Point")
    assert rel("cptr") == ("aggregates", "Point")
