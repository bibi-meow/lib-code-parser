---
phase: 04-c-frontend-c-extractors
plan: 02
subsystem: testing
tags: [libclang, clang.cindex, cpp, test-fixtures, conftest, cav]

# Dependency graph
requires:
  - phase: 04-01
    provides: language-nested dispatch (PRIMITIVES/EVALUATIONS dict[lang][name]); cpp dispatch path live
provides:
  - "build_cpp_cav(source, path) conftest helper — the single shared libclang CAV builder for all downstream cpp extractor tests"
  - "tests/fixtures/cpp/ corpus (7 fixtures) covering inheritance/relations/namespaces/includes/doxygen/negative-FSM/missing-include"
affects: [04-03, 04-04, 04-05, 04-06, 04-07, cpp-frontend, cpp-extractor-tests]

# Tech tracking
tech-stack:
  added: []  # libclang already pinned in Phase 1; this plan only uses it in tests
  patterns:
    - "Test-side single-parse CAV builder mirrors build_python_cav: one libclang parse per fixture, TranslationUnit stashed on CAV.payload"
    - "Fixtures are pure-ASCII, self-contained, <30 lines, -std=c++17 parseable"

key-files:
  created:
    - tests/fixtures/cpp/inheritance.cpp
    - tests/fixtures/cpp/relations.cpp
    - tests/fixtures/cpp/namespaces.cpp
    - tests/fixtures/cpp/includes.cpp
    - tests/fixtures/cpp/doxygen_contracts.cpp
    - tests/fixtures/cpp/not_a_state_machine.cpp
    - tests/fixtures/cpp/missing_include.cpp
  modified:
    - tests/conftest.py

key-decisions:
  - "build_cpp_cav parses libclang directly in the test layer (mirroring how build_python_cav uses ast.parse) so cpp tests do not require the cpp frontend plan to ship first"
  - "raw_content is set to source bytes on the cpp CAV (not left as the b'' default) so the component-diagram #include regex has source to scan"
  - "No PARSE_DETAILED_PROCESSING_RECORD (RESEARCH Pitfall 3 — floods cursor tree with builtin macros); default parse + PARSE_INCOMPLETE for missing-include tolerance"
  - "Fixtures kept pure-ASCII (em-dash in includes.cpp comment replaced with hyphen) to avoid locale-encoding read failures"

patterns-established:
  - "Pattern 1: ONE shared libclang CAV builder in conftest; downstream cpp tests import it rather than re-inventing libclang parse (drift prevention)"
  - "Pattern 2: missing-include fixture mechanically demonstrates LNG-05 warn-not-error — diagnostic emitted yet Ok struct cursor still built"

requirements-completed: [LNG-04]

# Metrics
duration: 9min
completed: 2026-06-04
---

# Phase 4 Plan 02: C++ Test Infrastructure (Wave 0) Summary

**Shared `build_cpp_cav` libclang CAV builder in conftest plus a 7-file `tests/fixtures/cpp/` corpus, unblocking all downstream cpp-extractor test authoring with one parse site and a known fixture set.**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-06-04
- **Completed:** 2026-06-04
- **Tasks:** 2
- **Files modified:** 8 (1 modified, 7 created)

## Accomplishments
- `build_cpp_cav(source, path)` added to `tests/conftest.py` as the exact analog of `build_python_cav`: libclang `Index.create().parse(path, args=["-x","c++","-std=c++17"], unsaved_files=[(path,source)], options=PARSE_INCOMPLETE)`, returning `CAV(language="cpp", payload=TranslationUnit, raw_content=<bytes>)`.
- 7 self-contained C++ fixtures authored, covering every D-04/D-05/D-08/D-09 behavior the later test plans assert.
- Mechanically verified: multiple inheritance yields 2 `CXX_BASE_SPECIFIER` children; doxygen comment carries `@pre`/`\post`/`\invariant` + `Traces: REQ-9, US-3`; relations fixture exposes the composes/aggregates/associates/none member spectrum; missing-include fixture emits a `missing_header.h` diagnostic yet still builds the `Ok` struct cursor (LNG-05).
- Full test collection still clean (449 tests collected) after the additive conftest change.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add build_cpp_cav libclang CAV builder to conftest** - `7ac1f7b` (feat)
2. **Task 2: Author the tests/fixtures/cpp/ corpus** - `be695b3` (feat)

## Files Created/Modified
- `tests/conftest.py` - Added `build_cpp_cav` next to `build_python_cav`; lazy libclang import inside the function; `build_python_cav` and all existing fixtures untouched.
- `tests/fixtures/cpp/inheritance.cpp` - Single inheritance (`Square : public Shape`) + multiple inheritance (`Circle : public Shape, public Point`, 2 base specifiers).
- `tests/fixtures/cpp/relations.cpp` - `Diagram` with value (composes), pointer (aggregates), reference (aggregates), builtin (none), unknown-type (associates) members.
- `tests/fixtures/cpp/namespaces.cpp` - Nested `namespace a { namespace b { struct S{}; } }` for namespace→package mapping.
- `tests/fixtures/cpp/includes.cpp` - `#include "local_a.h"` / `"local_b.h"` / `<vector>` for #include-regex edges (locals deliberately unresolved).
- `tests/fixtures/cpp/doxygen_contracts.cpp` - `compute_score` with `@pre` / `\post` / `\invariant` (mixed `@`/`\` forms) + `Traces: REQ-9, US-3`.
- `tests/fixtures/cpp/not_a_state_machine.cpp` - `enum class Color` + plain switch — FSM-looking but maps to no FSM family (negative fixture).
- `tests/fixtures/cpp/missing_include.cpp` - `#include "missing_header.h"` + valid `struct Ok {}` (LNG-05 warn-not-error).

## Decisions Made
- Parse libclang directly in the test layer so cpp test authoring does not block on the cpp frontend plan shipping first (mirrors `build_python_cav`'s direct `ast.parse`).
- Set `raw_content` on the cpp CAV (override the `b""` default) for the downstream component-diagram `#include` regex.
- Omit `PARSE_DETAILED_PROCESSING_RECORD` per RESEARCH Pitfall 3; rely on default parse + `PARSE_INCOMPLETE`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's Task 2 verify command had a wrong expected sort order**
- **Found during:** Task 2 (corpus verification)
- **Issue:** The plan's hardcoded expected list ordered `inheritance.cpp` before `includes.cpp`, but Python `sorted()` correctly orders `includes.cpp` first (`inc` < `inh`). The assertion would always fail despite all 7 fixtures being present and correctly named.
- **Fix:** Verified the substantive checks (all 7 fixtures present, missing-include diagnostic emitted, `Ok` cursor built, every fixture parses) against the correct lexicographic order. The deliverable fixtures are correct; only the plan's assertion list was mis-ordered. No fixture files were renamed.
- **Files modified:** none (verification-command-only discrepancy)
- **Verification:** `sorted(glob('*.cpp'))` == correctly-ordered list; missing-include + `Ok` cursor checks pass.
- **Committed in:** n/a (no source change needed)

**2. [Rule 1 - Bug] Non-ASCII em-dash in includes.cpp comment broke locale-default file reads**
- **Found during:** Task 2 (corpus verification)
- **Issue:** A UTF-8 em-dash (`—`, bytes `e2 80 94`) in the `includes.cpp` comment caused `Path.read_text()` (cp932 locale default on this Windows env) to raise `UnicodeDecodeError`. Source fixtures should be pure ASCII for robustness across readers.
- **Fix:** Replaced the em-dash with an ASCII hyphen; re-confirmed all fixtures are pure ASCII via a non-ASCII byte scan.
- **Files modified:** tests/fixtures/cpp/includes.cpp
- **Verification:** Byte scan shows zero non-ASCII bytes across all 7 fixtures; verify command passes.
- **Committed in:** be695b3 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule-1 bugs).
**Impact on plan:** Both are correctness fixes (one in the plan's verify assertion, one fixture-content hygiene). No scope creep; deliverables match the plan's must-haves exactly.

## Issues Encountered
- None beyond the two auto-fixed items above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Downstream cpp-extractor test plans (04-03..04-07) can now `from conftest import build_cpp_cav` and pull from `tests/fixtures/cpp/`.
- The cpp frontend's `build_cav` (lands in the frontend plan) should produce a CAV equivalent to this test-side builder; the `build_cpp_cav` parse args (`-x c++ -std=c++17`, `PARSE_INCOMPLETE`, `raw_content` carried) are the contract to mirror.
- No blockers.

## Self-Check: PASSED

- All 9 files verified present on disk (1 modified, 7 fixtures, 1 SUMMARY).
- Both task commits verified in git log: `7ac1f7b` (Task 1), `be695b3` (Task 2).

---
*Phase: 04-c-frontend-c-extractors*
*Completed: 2026-06-04*
