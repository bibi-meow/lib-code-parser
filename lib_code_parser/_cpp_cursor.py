r"""Shared libclang cursor-walk helpers for the C++ extractor set.

Single source of the cross-cutting cpp helpers (mirrors the ``_paths.py``
single-source idiom) so the three cpp primitive extractors — and the later
cpp evaluation extractors — share ONE implementation of:

- ``_in_main_file``    — drops builtin / header decls (Pitfall 3 main-file filter)
- ``_TRACE_TAGS_RE`` / ``extract_trace_tags`` — the TRC-03 trace-tag regex copied
  BYTE-IDENTICAL from ``extractors/primitives/functions.py`` so the same
  ``Traces:`` lines extract the same for Python docstrings and C++ Doxygen
  comments (D-09 parity).
- ``qualified_node_id`` — a stable namespace-qualified dotted id
  (``a.b.Class.method``); anonymous decls get a synthetic ``<anonymous@l:c>``
  chain segment so the id never escapes the dotted namespace (CR-01).
- ``field_relation``   — the composes / aggregates / associates / none classifier
  (D-04), the C++ analog of class_diagram.py's ``_classify_annotation``.

This module imports libclang at top level; it is only ever imported on the cpp
path (the pure-Python extractors never touch it), so the no-I/O-at-import
guarantee for the Python path is preserved — same rationale as ``frontends/cpp.py``.

Traces: LNG-04, TRC-03
"""

from __future__ import annotations

import os
import re

from clang.cindex import Cursor, CursorKind, TypeKind

from lib_code_parser.models.primitives.functions import TraceTag

__all__ = [
    "_in_main_file",
    "_TRACE_TAGS_RE",
    "extract_trace_tags",
    "qualified_node_id",
    "field_relation",
]

# TRC-03: copied VERBATIM from extractors/primitives/functions.py line 32 — the
# regex literal MUST stay byte-identical so trace-tag extraction behaves the
# same for Python docstrings and C++ raw_comment Doxygen blocks (D-09).
_TRACE_TAGS_RE = re.compile(r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)", re.MULTILINE)


def _in_main_file(cursor: Cursor, path: str) -> bool:
    """True only when the cursor's location is the parsed main file (Pitfall 3).

    Drops builtin declarations (no location.file) and decls pulled in from
    headers (different file) so cpp extractors emit ONLY the artifact's own
    declarations.

    The comparison is normalized (CR-02): libclang's ``location.file.name``
    echoes the spelling it was given but may normalize separators, collapse
    ``./`` prefixes, or differ in absolute-vs-relative form from ``path``. A
    byte-exact compare silently dropped EVERY cursor (a well-formed empty
    extraction) when a caller passed ``./foo.cpp`` or an absolute/backslash
    path. ``os.path.normcase(os.path.normpath(...))`` collapses these so the
    main-file filter still matches.
    """
    f = cursor.location.file
    if f is None:
        return False
    return os.path.normcase(os.path.normpath(f.name)) == os.path.normcase(os.path.normpath(path))


def extract_trace_tags(text: str) -> list[TraceTag]:
    """Extract ``Traces:`` tags from a comment / docstring (TRC-03 verbatim).

    Byte-identical behavior to ``functions._extract_trace_tags``; fed by
    ``cursor.raw_comment`` on the cpp path instead of an ast docstring.
    """
    tags: list[TraceTag] = []
    for m in _TRACE_TAGS_RE.finditer(text):
        refs = [r.strip() for r in m.group(1).split(",")]
        tags.append(TraceTag(tag="Traces", refs=refs))
    return tags


def qualified_node_id(cursor: Cursor) -> str:
    """Stable namespace-qualified dotted id (``a.b.Class.method``).

    Walks the ``semantic_parent`` chain collecting the spellings of enclosing
    NAMESPACE / CLASS / STRUCT (any named scope) cursors, then appends the
    cursor's own spelling. The chain is the same for an in-class declaration
    and its out-of-line definition, so both resolve to the identical id.

    For anonymous decls (empty spelling) a stable synthetic segment
    ``<anonymous@line:col>`` is appended to the enclosing chain instead of
    collapsing to a bare ``cursor.get_usr()``. This keeps the id inside the
    dotted ``a.b.Class`` namespace every other code path merges against
    (CR-01): a raw USR (``c:@S@...``) is a different id namespace and would
    silently fail node_id-keyed dedup/merge. The synthetic segment is
    deterministic across runs for identical input (libclang reports a stable
    line:col for the same source bytes).
    """
    parts: list[str] = []
    parent = cursor.semantic_parent
    while parent is not None and parent.kind != CursorKind.TRANSLATION_UNIT:
        if parent.spelling:
            parts.append(parent.spelling)
        parent = parent.semantic_parent
    parts.reverse()
    own = cursor.spelling
    if not own:
        # Keep the dotted-id namespace for anonymous decls; never escape to a
        # bare USR (CR-01).
        loc = cursor.location
        own = f"<anonymous@{loc.line}:{loc.column}>"
    parts.append(own)
    return ".".join(parts)


def field_relation(field_cursor: Cursor, known_classes: set[str]) -> tuple[str, str] | None:
    """Classify a FIELD_DECL into a (relation, target) edge or None (D-04).

    Verified rule (RESEARCH §Deterministic main-file cursor walk):
      • POINTER / LVALUEREFERENCE of a known class -> ("aggregates", base)
      • POINTER / LVALUEREFERENCE of an unknown type -> ("associates", base)
      • ELABORATED / RECORD value of a known class -> ("composes", base)
      • ELABORATED / RECORD value of an unknown type -> ("associates", base)
      • builtin primitive (int / double / ...) -> None (a plain field, no edge)

    "associates" is the undecidable fallback (never a catch-all "uses"/"other").
    """
    t = field_cursor.type
    is_ptr_ref = t.kind in (TypeKind.POINTER, TypeKind.LVALUEREFERENCE)
    target = t.get_pointee().spelling if is_ptr_ref else t.spelling
    base = target.replace("class ", "").replace("struct ", "").split("::")[-1].strip(" *&")
    if is_ptr_ref:
        return ("aggregates", base) if base in known_classes else ("associates", base)
    if t.kind in (TypeKind.ELABORATED, TypeKind.RECORD):
        return ("composes", base) if base in known_classes else ("associates", base)
    return None
