r"""C++ Doxygen-driven contract extractor (pure CAV consumer).

The C++ analog of ``extractors/primitives/contracts.py`` (D-09 parity): walks
the CAV's ``clang.cindex.TranslationUnit`` payload and emits the SAME
``ContractInfo`` / ``ContractEntry`` schema into the SAME ``CodeContent.contracts``
slot — but the provenance machinery is Doxygen, not Pydantic decorator-alias
resolution (none of that Python machinery carries over).

SPC-03 mapping (both ``\`` and ``@`` command forms, case-insensitive):

    \pre        / @pre        -> ContractEntry(kind="precondition")
    \post       / @post       -> ContractEntry(kind="postcondition")
    \invariant  / @invariant  -> ContractEntry(kind="invariant")

Every entry carries ``source_kind="doxygen"`` (the additive D-08 SourceKind).

Pitfall 4 (comment-to-cursor association): each entry is read from
``cursor.raw_comment`` on the EXACT decl cursor being emitted
(function / method / class) — NEVER inferred from an enclosing namespace's
leading comment. libclang attaches a raw_comment only to the decl it documents,
so a namespace-level Doxygen block does not bleed onto its inner decls.

The TRC-03 ``Traces:`` regex is shared verbatim from ``_cpp_cursor`` so trace-tag
extraction is byte-identical to the Python docstring path (D-09 parity); it is
exposed here for any caller that needs the tags alongside contracts.

DET-04: results are emitted deterministically — main-file decls are visited in
preorder, the node_id dict preserves first-seen order, and per-node entries are
sorted by (kind, line_no, name) so libclang's traversal order never leaks.

Implements: SPC-03
Traces: SPC-03, TRC-03, US-01, US-22
"""

from __future__ import annotations

import re

import clang.cindex
from clang.cindex import Cursor, CursorKind

from lib_code_parser import _cpp_cursor
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.contracts import (
    ContractEntry,
    ContractInfo,
    ContractKind,
)

__all__ = ["extract"]

# Both Doxygen command forms (\pre / @pre); case-insensitive marker word.
_DOXY_RE = re.compile(r"[\\@](pre|post|invariant)\b[ \t]*(.*)", re.IGNORECASE)

# Doxygen marker word -> ContractKind (D-09: \post maps to "postcondition" cleanly).
_MARKER_TO_KIND: dict[str, ContractKind] = {
    "pre": "precondition",
    "post": "postcondition",
    "invariant": "invariant",
}

_DECL_KINDS = (
    CursorKind.FUNCTION_DECL,
    CursorKind.CXX_METHOD,
    CursorKind.CLASS_DECL,
    CursorKind.STRUCT_DECL,
)


def extract(cav: CAV, config: ParserConfig) -> dict[str, ContractInfo]:
    """SPC-03: emit dict[node_id, ContractInfo] from cav.payload (TranslationUnit).

    Mirrors the Python contracts extractor's output shape (dict keyed by the
    decl's qualified node_id). ``config`` is accepted for PrimitiveFn signature
    alignment but not consumed; the executor decides whether to invoke this
    extractor at all via ``config.extract_contracts`` on the shared "contracts"
    slot.
    """
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit), (
        "cpp_contracts extractor requires C++ CAV (TranslationUnit payload), "
        f"got {type(tu).__name__}"
    )
    path = cav.path

    result: dict[str, ContractInfo] = {}
    seen: set[str] = set()

    for cursor in tu.cursor.walk_preorder():
        if not _cpp_cursor._in_main_file(cursor, path):
            continue
        if cursor.kind not in _DECL_KINDS:
            continue

        node_id = _cpp_cursor.qualified_node_id(cursor)
        # An in-class declaration and its out-of-line definition share node_id;
        # keep the first seen so each id is emitted once (cpp_functions parity).
        if node_id in seen:
            continue

        # Pitfall 4: read raw_comment on THIS EXACT decl cursor, never inferring
        # from a textually-adjacent namespace comment.
        comment = cursor.raw_comment or ""
        entries = _entries_for(cursor, comment)
        if not entries:
            continue
        seen.add(node_id)
        result[node_id] = ContractInfo(node_id=node_id, entries=entries)

    return result


def _entries_for(cursor: Cursor, comment: str) -> list[ContractEntry]:
    """Build the (kind, line)-sorted ContractEntry list for one decl cursor."""
    line_no = cursor.extent.start.line
    name = cursor.spelling
    entries: list[ContractEntry] = []
    for marker, _condition in _DOXY_RE.findall(comment):
        kind = _MARKER_TO_KIND[marker.lower()]
        entries.append(
            ContractEntry(
                name=name,
                source_kind="doxygen",
                kind=kind,
                decorator_name="",
                line_no=line_no,
            )
        )
    # DET-04: stable per-node order independent of regex/cursor traversal.
    entries.sort(key=lambda e: (e.kind, e.line_no, e.name))
    return entries
