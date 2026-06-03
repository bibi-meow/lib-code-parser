---
phase: 04-c-frontend-c-extractors
plan: 01
subsystem: infra
tags: [dispatch, open-closed, language-dimension, cpp, executor, pydantic]

# Dependency graph
requires:
  - phase: 02-...
    provides: dispatch-dict-driven executor (D-03) walking flat FRONTENDS/PRIMITIVES
  - phase: 03-...
    provides: 7 EVALUATIONS entries (5 diagrams + 2 specs) registered append-only
provides:
  - Nested language-dimension dispatch — PRIMITIVES/EVALUATIONS are dict[language, dict[name, fn]]
  - Reserved empty ["cpp"] sub-dicts every later Phase 4 cpp extractor registers into
  - Executor walks indexed by cav.language (PRIMITIVES[cav.language] / EVALUATIONS[cav.language])
  - Per-language import-time slot guard (fail-loud, T-04-01)
  - docs/09 language-axis extension procedure + append-only language-key invariant + invariant #6 one-time revision
affects: [04-cpp-frontend, 04-cpp-extractors, doxygen-contract, libclang, all-phase-4-plans]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Language-dimension dispatch nesting (D-01): per-language extractor sets keyed by cav.language"
    - "Append-only language keys: existing language keys never removed/renamed (extends invariant #4 to the language axis)"

key-files:
  created: []
  modified:
    - lib_code_parser/_dispatch.py
    - lib_code_parser/executor.py
    - docs/09-extending.md
    - tests/unit/test_dispatch.py
    - tests/unit/test_executor_dispatch.py

key-decisions:
  - "D-01: PRIMITIVES/EVALUATIONS nested dict[language, dict[name, fn]] = {python:{...}, cpp:{}}; Python values byte-unchanged under [python]"
  - "D-02: FRONTENDS stays flat dict[language, fn] — one frontend per language, NOT double-nested (Phase 4 Pitfall 1); no FRONTENDS[cpp] yet (lands in the frontend plan)"
  - "D-03: executor changes exactly the two walk lines to index cav.language; all other lines (frontend selection, cpp suffix override, contracts gate, ContractInfo merger, CodeContent assembly) unchanged"
  - "cav.language (the CAV the frontend produced) is used to index, NOT the local 'language' variable — dispatch set matches the actual payload type"

patterns-established:
  - "Language axis is the ONE-TIME structural exception to invariant #6 (executor body does not grow per-extractor); adding cpp aspects later is again 0-line executor diff"
  - "Per-language slot guard iterates every language dim so a mis-named cpp evaluation key fails fast at import time"

requirements-completed: [LNG-04]

# Metrics
duration: 6min
completed: 2026-06-03
---

# Phase 4 Plan 01: Language-Dimension Dispatch Nesting Summary

**Introduced the language axis into dispatch once (D-01): PRIMITIVES/EVALUATIONS became dict[language, dict[name, fn]] with Python entries byte-unchanged under ["python"] and reserved empty ["cpp"] sub-dicts; the executor now walks PRIMITIVES[cav.language]/EVALUATIONS[cav.language], FRONTENDS stays flat.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-03T16:39:28Z
- **Completed:** 2026-06-03T16:46:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Nested `PRIMITIVES`/`EVALUATIONS` into per-language dicts with Python registrations migrated under `["python"]` with identical callables and identical key spelling (`call_graph` underscore preserved); `cpp` reserved as empty sub-dicts.
- Kept `FRONTENDS` flat `dict[language, FrontendFn]` (Pitfall 1 — never double-nested); `FRONTENDS["python"] = _build_cav_python` unchanged, no `cpp` frontend yet.
- Changed the executor's two walk headers to index `cav.language`; every other executor line untouched (verified by grep that each indexed walk appears exactly once).
- Generalized the WR-01 registration-time slot guard to iterate both language dims (fail-loud on a bad cpp key — T-04-01).
- Documented the language-dimension extension procedure, the append-only language-key invariant, and the one-time invariant-#6 revision in `docs/09-extending.md`.
- Full unit suite green: **325 passed, 1 skipped**; ruff clean on all touched files.

## Task Commits

Each task was committed atomically:

1. **Task 1: Nest PRIMITIVES/EVALUATIONS into language-keyed dicts; keep FRONTENDS flat** - `0978181` (refactor)
2. **Task 2: Index executor primitive + evaluation walks by cav.language (D-03)** - `bbdcd86` (feat)
3. **Task 3: Update test_dispatch nested assertions + document language dimension in docs/09** - `f53fd7c` (test)

_Note: Tasks 1 & 2 were declared `tdd="true"`; the structural change made the existing flat-shape assertions in `test_dispatch.py` (Task 3-owned) the RED signal, and the inline verify one-liners gated each GREEN step._

## Files Created/Modified
- `lib_code_parser/_dispatch.py` - `PRIMITIVES`/`EVALUATIONS` typed `dict[str, dict[str, …Fn]]` initialized `{"python": {}, "cpp": {}}`; Python entries migrated under `["python"]`; FRONTENDS left flat; per-language slot guard.
- `lib_code_parser/executor.py` - primitive walk → `PRIMITIVES[cav.language].items()`, evaluation walk → `EVALUATIONS[cav.language].items()`; all other lines unchanged.
- `docs/09-extending.md` - "新言語の extractor セット追加手順" subsection + append-only language-key invariant + invariant-#6 one-time D-01 revision note (appended, no deletions).
- `tests/unit/test_dispatch.py` - nested-shape assertions under `["python"]`, `cpp` presence checks, per-language guard iteration, new fail-loud guard test + live-dispatch guard test, updated class docstring.
- `tests/unit/test_executor_dispatch.py` - stub frontends now return `CAV(language="python", …)`; monkeypatch targets the nested `PRIMITIVES["python"]` sub-dict; `EVALUATIONS` override is `{"python": {}}`.

## Decisions Made
- Used `cav.language` (not the local `language` variable) to index both walks, so the dispatch set always matches the actual CAV payload type — matches the plan's D-03 instruction and the threat-register T-04-02 disposition (CAV.language is a closed `Literal["python","cpp"]` validated upstream).
- The empty `["cpp"]` sub-dicts are the sole cpp presence in this plan; no cpp callable imports/registrations added (per plan — those land in later Phase 4 plans).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated tests/unit/test_executor_dispatch.py for the nested shape + cav.language**
- **Found during:** Task 2 (executor walk re-indexing)
- **Issue:** The structural nesting broke 4 executor-dispatch unit tests not listed in the plan's `files_modified`. Their frontend stubs returned a bare `object()` (no `.language` attribute → `AttributeError` on `PRIMITIVES[cav.language]`), and their `monkeypatch.setitem(_dispatch.PRIMITIVES, "functions", …)` calls set a top-level *language* key instead of `PRIMITIVES["python"]["functions"]`. Their `EVALUATIONS = {}` override would also `KeyError` on `["python"]`.
- **Fix:** Stub frontends now return `CAV(language="python", path=path, payload=object())`; monkeypatches target `_dispatch.PRIMITIVES["python"]`; `EVALUATIONS` override is `{"python": {}}`.
- **Files modified:** tests/unit/test_executor_dispatch.py
- **Verification:** `pytest tests/unit/test_executor_dispatch.py -q` → 6 passed.
- **Committed in:** bbdcd86 (Task 2 commit; ruff-format follow-up landed in f53fd7c)

**2. [Rule 3 - Blocking] Ran ruff format on test_executor_dispatch.py to satisfy the lint gate**
- **Found during:** Task 3 (lint check before completion)
- **Issue:** Two `monkeypatch.setitem(...PRIMITIVES["python"]...call_graph...)` lines exceeded the 100-col `ruff` limit (E501) after nesting, violating the project CI lint gate.
- **Fix:** `ruff format tests/unit/test_executor_dispatch.py` wrapped the two long calls; behavior unchanged.
- **Files modified:** tests/unit/test_executor_dispatch.py
- **Verification:** `ruff check` on all four touched code/test files → "All checks passed!"; tests still pass.
- **Committed in:** f53fd7c (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both auto-fixes were directly caused by this plan's structural change and are required for the unit suite + lint gate to pass (Open-Closed invariants #1/#2 require the existing Python suite to stay green). No scope creep — no cpp behavior added, no extractor logic changed.

## Issues Encountered
- A verify one-liner using `pathlib.Path.read_text()` hit a Windows `cp932` UnicodeDecodeError on the non-ASCII executor docstring; re-ran with `encoding="utf-8"`. This was a transient harness/encoding artifact in the check command, not a code defect (the file is valid UTF-8).

## User Setup Required
None - pure internal refactor of in-process dispatch dicts; no external service configuration required.

## Next Phase Readiness
- The language axis is live: later Phase 4 plans register the cpp frontend (`FRONTENDS["cpp"]`) and cpp extractors into the reserved `PRIMITIVES["cpp"]` / `EVALUATIONS["cpp"]` sub-dicts with **0-line executor diff**.
- This was the only Phase 4 plan modifying the existing executor/_dispatch; the load-bearing D-01 structural change is complete and Open-Closed invariants #1/#2 are preserved (existing Python values byte-unchanged).

## Self-Check: PASSED

All 5 modified files exist on disk; all 3 task commits (`0978181`, `bbdcd86`, `f53fd7c`) are present in git history.

---
*Phase: 04-c-frontend-c-extractors*
*Completed: 2026-06-03*
