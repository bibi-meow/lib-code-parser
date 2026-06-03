---
phase: 04-c-frontend-c-extractors
plan: 04
subsystem: cpp-extractors
tags: [libclang, clang.cindex, cpp, primitives, det-04, trc-03, lng-04, lng-05, dispatch]

# Dependency graph
requires:
  - phase: 04-01
    provides: nested PRIMITIVES dict[language, dict[name, fn]] with reserved empty ["cpp"] sub-dict + executor walk indexed by cav.language
  - phase: 04-03
    provides: FRONTENDS["cpp"] = build_cav (the libclang parse site producing the cpp CAV with TranslationUnit payload + raw_content carried)
provides:
  - "_cpp_cursor.py — shared cpp cursor-walk helpers: _in_main_file filter, byte-identical TRC-03 regex + extract_trace_tags, qualified_node_id (semantic_parent chain + get_usr fallback), field_relation composes/aggregates/associates/none classifier (D-04)"
  - "cpp_functions — FunctionNode extraction (class/method/function kinds) from libclang cursors with qualified node_id + TRC-03 trace tags"
  - "cpp_callgraph — CallGraph (CallEdge caller,callee) from CALL_EXPR/MEMBER_REF_EXPR in main-file bodies"
  - "cpp_type_deps — TypeDep from #include regex over raw_content + FIELD_DECL member types (no subprocess oracle)"
  - "PRIMITIVES['cpp'] = {functions, call_graph, type_deps} registered with the Python key spelling (LNG-04 parity)"
affects: [04-05, 04-06, 04-07, cpp-evaluations, cpp-class-diagram, cpp-component-diagram, cpp-acceptance-tests]

# Tech tracking
tech-stack:
  added: []  # libclang already pinned/in-use since 04-03; this plan is the first cpp PRIMITIVES use
  patterns:
    - "Shared cpp cursor helper module (_cpp_cursor.py) mirrors the _paths.py single-source idiom; imports libclang at top level but only ever loaded on the cpp path"
    - "node_id dedup: an in-class method declaration and its out-of-line definition share a qualified node_id (semantic_parent chain), so cpp_functions keeps the first-seen and cpp_callgraph guards calls with a seen_callers set"
    - "#include source for type_deps is a deterministic regex over cav.raw_content (RESEARCH Open Question 3) — never PARSE_DETAILED_PROCESSING_RECORD (Pitfall 3); the regex reads header NAMES only and never opens a file (T-04-09 accept)"

key-files:
  created:
    - lib_code_parser/_cpp_cursor.py
    - lib_code_parser/extractors/primitives/cpp_functions.py
    - lib_code_parser/extractors/primitives/cpp_callgraph.py
    - lib_code_parser/extractors/primitives/cpp_type_deps.py
    - tests/unit/test_cpp_cursor.py
    - tests/unit/extractors/test_cpp_functions.py
    - tests/unit/extractors/test_cpp_callgraph.py
    - tests/unit/extractors/test_cpp_type_deps.py
  modified:
    - lib_code_parser/_dispatch.py
    - tests/acceptance/test_fr06_disabled.py

key-decisions:
  - "TRC-03 (D-09) honored: _cpp_cursor._TRACE_TAGS_RE is byte-identical to functions.py L32 (asserted by a static substring test); cpp_functions feeds cursor.raw_comment into the shared extract_trace_tags"
  - "node_id is namespace-qualified via the semantic_parent chain (a.b.Class.method), get_usr() fallback for anonymous decls; identical id for an in-class decl and its out-of-line definition -> de-duplicated on emit (D-04 stable id)"
  - "field_relation (D-04): POINTER/LVALUEREFERENCE via get_pointee().spelling -> aggregates if base in known else associates; ELABORATED/RECORD value -> composes if known else associates; builtin -> None (no edge). 'associates' is the undecidable fallback, NEVER a 'uses'/'other' catch-all"
  - "DET-04 parity: cpp_functions sorts by node_id; cpp_callgraph edges by (caller,callee) + nodes via dict.fromkeys; cpp_type_deps by (source,target,kind,source_line) — verbatim composite keys from the Python siblings"
  - "D-06 in-process boundary honored: cpp_type_deps has NO subprocess resolution-oracle path (literal 'pyright'/'adapter' substrings absent, asserted by test); libclang is in-process only"
  - "LNG-05 warn-not-error: a missing/unresolved #include still yields an import TypeDep without raising (the regex never opens the file); FIELD_DECL of an unresolved type does not crash"
  - "Each cpp primitive asserts isinstance(cav.payload, clang.cindex.TranslationUnit) and NEVER branches on cav.language (invariant #2); the nested dispatch (04-01) guarantees the precondition"

patterns-established:
  - "_cpp_cursor is the centralization point the cpp class/component diagrams (04-05/04-06) will reuse for the field-relation classifier + main-file filter + node_id, exactly as the Python class_diagram reuses its own helpers"

requirements-completed: [LNG-04, LNG-05, TRC-03]

# Metrics
duration: 9min
completed: 2026-06-04
---

# Phase 4 Plan 04: C++ AST Primitive Extractors Summary

**The three C++ AST primitives are live and registered: `cpp_functions` (FunctionNode class/method/function kinds with namespace-qualified node_ids + byte-identical TRC-03 trace tags), `cpp_callgraph` (CallEdge from CALL_EXPR/MEMBER_REF_EXPR, (caller,callee)-sorted), and `cpp_type_deps` (#include import deps via raw_content regex + FIELD_DECL member-type deps, no subprocess oracle), all sharing the new `_cpp_cursor.py` helper (main-file filter, verbatim TRC-03 regex, qualified node_id, composes/aggregates/associates/none classifier) and emitting the EXISTING Pydantic shapes unchanged (LNG-04) with DET-04 sort-on-exit — registered into `PRIMITIVES["cpp"]`.**

## Performance

- **Duration:** ~9 min
- **Tasks:** 3 (all `tdd="true"`)
- **Files modified:** 10 (8 created, 2 modified)

## Accomplishments
- `_cpp_cursor.py` centralizes the four cross-cutting cpp helpers (mirroring the `_paths.py` single-source idiom): `_in_main_file` (Pitfall 3 header filter), the byte-identical `_TRACE_TAGS_RE` + `extract_trace_tags` (TRC-03/D-09), `qualified_node_id` (semantic_parent walk + `get_usr()` fallback), and `field_relation` (the verified composes/aggregates/associates/none rule using `TypeKind` + `get_pointee()`).
- `cpp_functions` emits the three `FunctionNode` kinds with qualified node_ids, params from PARM_DECL, `return_type=cursor.result_type.spelling`, source_range from `cursor.extent`, and trace tags from `cursor.raw_comment`; de-dups the in-class-decl/out-of-line-def pair; sorts by `node_id`.
- `cpp_callgraph` collects `CallEdge(caller=<enclosing node_id>, callee=<call spelling>)` from CALL_EXPR/MEMBER_REF_EXPR within main-file function/method bodies, dedups nodes via `dict.fromkeys`, sorts edges by `(caller,callee)`.
- `cpp_type_deps` emits `imports` deps from a deterministic `#include` regex over `cav.raw_content` (missing headers still emit, no raise — LNG-05) plus `uses` member-type deps from FIELD_DECL via the shared `field_relation`; NO subprocess oracle path (D-06); sorts by `(source,target,kind,source_line)`.
- `PRIMITIVES["cpp"]["functions"/"call_graph"/"type_deps"]` registered append-only with the Python key spelling — LNG-04 parity is automatic.
- 25 new cpp unit tests green (7 cursor + 8 functions + 5 callgraph + 6 type_deps − 1 adjusted) ; full repo suite **484 passed**, zero regressions; ruff check + format clean on all touched files.

## Task Commits

Each task was committed atomically:

1. **Task 1: Shared _cpp_cursor.py helpers** - `95c0c29` (feat)
2. **Task 2: cpp_functions + cpp_callgraph + PRIMITIVES["cpp"] registration** - `348b95e` (feat)
3. **Task 3: cpp_type_deps (#include + member types) + registration** - `b5c631d` (feat)

Plus a Rule-1 fix:

4. **Fix: update obsolete cpp-returns-empty acceptance test** - `54a1974` (fix)

_All three tasks were `tdd="true"`. RED: each test file was authored first and failed on import (modules absent) or on the field-relation/sort assertions. GREEN: the implementation made the inline plan-verify one-liners + the unit tests pass. The TDD gate sequence holds per task (test authored → fail → implement → pass), committed together per the per-task atomic-commit protocol._

## Files Created/Modified
- `lib_code_parser/_cpp_cursor.py` (created) — shared cpp cursor helpers; top-level `from clang.cindex import Cursor, CursorKind, TypeKind` (only imported on the cpp path).
- `lib_code_parser/extractors/primitives/cpp_functions.py` (created) — FunctionNode extraction; `Implements: LNG-04`, `Traces: LNG-04, TRC-03, US-01, US-22`.
- `lib_code_parser/extractors/primitives/cpp_callgraph.py` (created) — CallGraph extraction; `Traces: LNG-04, DET-04, ...`.
- `lib_code_parser/extractors/primitives/cpp_type_deps.py` (created) — #include + member TypeDep; `Traces: LNG-04, LNG-05, ...`.
- `lib_code_parser/_dispatch.py` (modified) — appended `# noqa: E402` imports + `PRIMITIVES["cpp"]["functions"/"call_graph"/"type_deps"]` into the reserved `["cpp"]` sub-dict; `FRONTENDS["python"]`/`["cpp"]` and all Python registrations untouched.
- `tests/unit/test_cpp_cursor.py` (created) — TRC-03 byte-identity, main-file filter, qualified node_id stability, field-relation spectrum.
- `tests/unit/extractors/test_cpp_functions.py` (created) — kind discrimination, node_id qualification, params/return/source_range, raw_comment trace tags, sort, out-of-line dedup, header exclusion, payload assert.
- `tests/unit/extractors/test_cpp_callgraph.py` (created) — function/method edges, (caller,callee) sort, node dedup, payload assert.
- `tests/unit/extractors/test_cpp_type_deps.py` (created) — include deps, missing-header no-raise, member deps, DET-04 sort, no-pyright/adapter static guard, payload assert.
- `tests/acceptance/test_fr06_disabled.py` (modified) — see Deviations.

## Decisions Made
- **node_id de-duplication strategy:** libclang surfaces a method both as an in-class declaration (inside STRUCT/CLASS_DECL) and, when defined out-of-line, as a sibling definition cursor; both share the same `semantic_parent`-derived qualified id. `cpp_functions` keeps the first-seen entry per id; `cpp_callgraph` walks bodies for both kinds but guards with a `seen_callers` set so calls are counted once. This was verified against a live `Calc::add2` out-of-line definition.
- **`associates` fixture for the unit test:** a pointer to a *never-declared* name (`Unknown*`) is recovered by libclang to `int*` under `PARSE_INCOMPLETE` (implicit-int recovery), so the deterministic `associates` unit fixture uses a *forward-declared* class (`class Widget;` then `Widget* w`) — known-as-reference, undecidable-as-ownership. The never-declared form is exercised as a no-crash/no-edge case via the `relations.cpp` acceptance path.
- **member-dep `source`:** the enclosing class's qualified node_id (via `semantic_parent`) is the TypeDep `source`, so member deps compose cleanly with the cpp class diagram (04-05) which keys on the same id.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reworded `cpp_type_deps.py` docstring to satisfy the no-`pyright`/`adapter` static verify**
- **Found during:** Task 3 (running the inline automated verify + its unit test)
- **Issue:** Task 3's verify and `test_no_pyright_adapter_in_source` assert the literal substrings `pyright` and `adapter` are absent from the source. My explanatory docstring used those words to describe what the cpp path deliberately AVOIDS ("no pyright/adapter path"). The code never imports or references either — but the literal words tripped the substring guard.
- **Fix:** Reworded to "no subprocess resolution-oracle path … no in-process resolver oracle". No behavior change; the property the guard enforces (D-06 in-process boundary, no subprocess layer import) is unchanged. Same class of wording-only fix as 04-03 Task 1.
- **Files modified:** lib_code_parser/extractors/primitives/cpp_type_deps.py
- **Committed in:** `b5c631d` (Task 3 commit)

**2. [Rule 1 - Bug] Updated obsolete `tests/acceptance/test_fr06_disabled.py::TestCppNotSupported`**
- **Found during:** Post-task full-suite run (acceptance + parity, which the per-task unit verifies did not cover)
- **Issue:** `TestCppNotSupported::test_cpp_extension_returns_empty` encoded the pre-Phase-4 stub assumption that a `.cpp` artifact returns empty content ("not in FRONTENDS -> empty"). With `FRONTENDS["cpp"]` live (04-03) and `PRIMITIVES["cpp"]` now live (this plan), `int main() {}` correctly emits a `("main","function")` FunctionNode, so the assertion was wrong. This failure was latent after 04-03 (which ran only the unit suite) and surfaced once the cpp extractors made the cpp path fully functional — exactly the behavior change Phase 4 exists to deliver.
- **Fix:** Renamed the class to `TestCppSupported`; `test_cpp_extension_extracts_functions` asserts the `main` function is emitted; `test_cpp_empty_source_returns_empty` keeps the empty-source → empty-content invariant.
- **Files modified:** tests/acceptance/test_fr06_disabled.py
- **Verification:** `pytest tests/acceptance/test_fr06_disabled.py` → 7 passed; full suite → 484 passed.
- **Committed in:** `54a1974`

---

**Total deviations:** 2 auto-fixed (1 blocking wording, 1 bug — a stale test).
**Impact on plan:** Deviation 1 is wording-only (matches the 04-03 precedent). Deviation 2 corrects a test that asserted the now-obsolete cpp-is-a-stub behavior; it is a direct consequence of this plan's intended functionality and required for the acceptance suite to pass. No scope creep — no extractor logic changed beyond the plan's three primitives + the shared helper.

## Issues Encountered
- A `RequestsDependencyWarning` (urllib3/chardet version mismatch) prints during pytest collection — pre-existing environment noise unrelated to this plan; tests pass cleanly.
- `git` warns `LF will be replaced by CRLF` on each cpp file commit (Windows autocrlf) — cosmetic, no content impact.
- Pre-existing untracked harness/planning artifacts (`.claude/gsd-*.json`, `.claude/scheduled_tasks.lock`) are out of scope and were left untouched.

## User Setup Required
None — libclang 18.1.1 is already pinned/installed and was exercised live by the cpp CAV builder in every cpp test. No external service configuration required.

## Next Phase Readiness
- `PRIMITIVES["cpp"]` now holds `functions`/`call_graph`/`type_deps` with the Python key spelling; the executor runs them on any cpp CAV with a 0-line executor diff (D-01/D-03 from 04-01).
- `_cpp_cursor.py` is the reuse point for the cpp evaluation extractors (04-05 class diagram pulls `field_relation` + the main-file filter + qualified node_id; 04-06 component diagram pulls `cpp_type_deps` for `#include` edges).
- DET-04 sort-on-exit, TRC-03 byte-identity, and the in-process (no-subprocess) boundary are established for the cpp primitive layer; no blockers.

## Self-Check: PASSED

- All 8 created files + 2 modified files verified present on disk.
- All 4 commits verified in git history: `95c0c29` (Task 1), `348b95e` (Task 2), `b5c631d` (Task 3), `54a1974` (Rule-1 fix).
- Full repository test suite: 484 passed, 0 failed.

---
*Phase: 04-c-frontend-c-extractors*
*Completed: 2026-06-04*
