r"""C++ libclang cursor -> FunctionNode extractor (pure CAV consumer).

The C++ analog of ``extractors/primitives/functions.py`` (LNG-04 parity): walks
the CAV's ``clang.cindex.TranslationUnit`` payload and emits a ``FunctionNode``
for each main-file class/struct (kind="class"), method (kind="method"), and free
function (kind="function") with params / return_type / source_range / trace_tags
populated.

Trace tags come from ``cursor.raw_comment`` fed into the BYTE-IDENTICAL TRC-03
regex shared from ``_cpp_cursor`` so ``Traces:`` lines extract the same as they
do from Python docstrings (D-09 parity). The EXISTING ``FunctionNode`` /
``ParamInfo`` / ``SourceRange`` / ``TraceTag`` models are reused unchanged
(invariant #1). DET-04: the returned list is sorted by ``node_id`` on exit,
absorbing libclang's nondeterministic cursor-traversal order.

This extractor asserts a ``TranslationUnit`` payload and NEVER branches on
``cav.language`` (invariant #2) — the nested dispatch (D-01) guarantees it only
ever receives a cpp CAV; the assert documents and enforces that precondition.

Implements: LNG-04
Traces: LNG-04, TRC-03, US-01, US-22
"""

from __future__ import annotations

import clang.cindex
from clang.cindex import Cursor, CursorKind

from lib_code_parser import _cpp_cursor
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.functions import (
    FunctionNode,
    ParamInfo,
    SourceRange,
)

__all__ = ["extract"]

_CLASS_KINDS = (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL)


def _params(cursor: Cursor) -> list[ParamInfo]:
    """ParamInfo list from PARM_DECL children (name + type spelling)."""
    params: list[ParamInfo] = []
    for child in cursor.get_children():
        if child.kind == CursorKind.PARM_DECL:
            params.append(ParamInfo(name=child.spelling, type_annotation=child.type.spelling))
    return params


def _source_range(cursor: Cursor) -> SourceRange:
    extent = cursor.extent
    return SourceRange(start_line=extent.start.line, end_line=extent.end.line)


def extract(cav: CAV, config: ParserConfig) -> list[FunctionNode]:
    """LNG-04: emit FunctionNode list from cav.payload (libclang TranslationUnit).

    config is accepted for PrimitiveFn signature alignment but is not consumed
    (FunctionNode extraction does not depend on per-config flags), mirroring the
    Python sibling.
    """
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit), (
        "cpp_functions extractor requires C++ CAV (TranslationUnit payload), "
        f"got {type(tu).__name__}"
    )
    path = cav.path
    by_id: dict[str, FunctionNode] = {}

    for cursor in tu.cursor.walk_preorder():
        if not _cpp_cursor._in_main_file(cursor, path):
            continue
        kind = cursor.kind
        if kind in _CLASS_KINDS:
            node_kind = "class"
        elif kind == CursorKind.CXX_METHOD:
            node_kind = "method"
        elif kind == CursorKind.FUNCTION_DECL:
            node_kind = "function"
        else:
            continue

        node_id = _cpp_cursor.qualified_node_id(cursor)
        # An in-class declaration and its out-of-line definition share node_id;
        # keep the first seen (declaration in preorder) so each id emits once.
        if node_id in by_id:
            continue

        comment = cursor.raw_comment or ""
        trace_tags = _cpp_cursor.extract_trace_tags(comment)
        if node_kind == "class":
            by_id[node_id] = FunctionNode(
                node_id=node_id,
                kind=node_kind,
                docstring=comment,
                trace_tags=trace_tags,
                source_range=_source_range(cursor),
            )
        else:
            by_id[node_id] = FunctionNode(
                node_id=node_id,
                kind=node_kind,
                params=_params(cursor),
                return_type=cursor.result_type.spelling,
                docstring=comment,
                trace_tags=trace_tags,
                source_range=_source_range(cursor),
            )

    functions = list(by_id.values())
    # DET-04: deterministic order independent of libclang traversal.
    functions.sort(key=lambda f: f.node_id)
    return functions
