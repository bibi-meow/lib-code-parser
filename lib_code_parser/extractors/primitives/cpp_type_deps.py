r"""C++ libclang -> TypeDep extractor (#include + member types, pure CAV consumer).

The C++ analog of the DEFAULT (pure) path of ``extractors/primitives/type_deps.py``
(LNG-04 parity). It emits two flavors of ``TypeDep``:

- ``kind="imports"`` from ``#include`` directives, parsed by a deterministic
  regex over ``cav.raw_content`` (RESEARCH Open Question 3 recommendation —
  avoids the macro-polluting ``PARSE_DETAILED_PROCESSING_RECORD`` flag, Pitfall
  3). An unresolved / missing header still yields an import edge (LNG-05
  warn-not-error) — the regex only reads the header NAME and never opens the file
  (threat T-04-09 accept).
- ``kind="uses"`` member-type deps from main-file ``FIELD_DECL`` cursors whose
  type resolves to a class/struct (value, pointer, or reference). Builtin
  primitive members produce no edge. Unresolved / template-dependent members do
  not crash.

There is NO subprocess resolution-oracle path: C++ has no in-process equivalent
of the Python import resolver and libclang runs in-process (D-06; the
subprocess-only layer is never imported here). DET-04: the returned list is
sorted by ``(source, target, kind, source_line)`` on exit, verbatim from the
Python sibling. The existing ``TypeDep`` model is reused unchanged;
``TypeDep.kind`` is a free-form str at the primitives layer.

Implements: LNG-04, LNG-05
Traces: LNG-04, LNG-05, US-01, US-22
"""

from __future__ import annotations

import re

import clang.cindex
from clang.cindex import CursorKind

from lib_code_parser import _cpp_cursor
from lib_code_parser._paths import get_module_name
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.type_deps import TypeDep

__all__ = ["extract"]

_CLASS_KINDS = (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL)

# #include <header> / #include "header" — capture the header NAME only. The
# regex never opens the referenced file (threat T-04-09 accept).
_INCLUDE_RE = re.compile(r"""^\s*#\s*include\s*[<"]([^>"]+)[>"]""", re.MULTILINE)


def _collect_known_classes(tu_cursor, path: str) -> set[str]:
    """Main-file class/struct spellings (the resolvable-as-member-type set)."""
    known: set[str] = set()
    for cursor in tu_cursor.walk_preorder():
        if cursor.kind in _CLASS_KINDS and _cpp_cursor._in_main_file(cursor, path):
            if cursor.spelling:
                known.add(cursor.spelling)
    return known


def extract(cav: CAV, config: ParserConfig) -> list[TypeDep]:
    """LNG-04 / LNG-05 / DET-04: emit C++ type_deps from cav (pure, no subprocess).

    config is accepted for PrimitiveFn signature alignment but is not consumed;
    the C++ path has no resolve-imports opt-in (no in-process resolver oracle).
    """
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit), (
        "cpp_type_deps extractor requires C++ CAV (TranslationUnit payload), "
        f"got {type(tu).__name__}"
    )
    module_name = get_module_name(cav.path)
    raw_deps: list[TypeDep] = []

    # 1) #include import deps — regex over the carried raw bytes (deterministic,
    #    no detailed-processing-record macro pollution). Missing headers still
    #    emit an import edge (LNG-05); the regex never opens the file.
    source_text = cav.raw_content.decode("utf-8", errors="replace")
    for m in _INCLUDE_RE.finditer(source_text):
        line = source_text.count("\n", 0, m.start()) + 1
        raw_deps.append(
            TypeDep(
                source=module_name,
                target=m.group(1),
                kind="imports",
                source_line=line,
            )
        )

    # 2) member-type deps from main-file FIELD_DECL cursors. The enclosing class
    #    node_id is the source; the resolved member type base is the target.
    known = _collect_known_classes(tu.cursor, cav.path)
    for cursor in tu.cursor.walk_preorder():
        if cursor.kind != CursorKind.FIELD_DECL:
            continue
        if not _cpp_cursor._in_main_file(cursor, cav.path):
            continue
        relation = _cpp_cursor.field_relation(cursor, known)
        if relation is None:
            continue  # builtin primitive member — no edge
        _, target = relation
        parent = cursor.semantic_parent
        source = _cpp_cursor.qualified_node_id(parent) if parent is not None else module_name
        raw_deps.append(
            TypeDep(
                source=source,
                target=target,
                kind="uses",
                source_line=cursor.location.line,
            )
        )

    # DET-04: sort by the verbatim composite key.
    raw_deps.sort(key=lambda d: (d.source, d.target, d.kind, d.source_line))
    return raw_deps
