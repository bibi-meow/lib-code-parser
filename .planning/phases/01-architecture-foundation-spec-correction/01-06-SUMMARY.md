---
phase: 01-architecture-foundation-spec-correction
plan: 06
subsystem: infra
tags: [pydantic, ast, dispatch-table, callable, type-checking, open-closed]

# Dependency graph
requires:
  - phase: 01-architecture-foundation-spec-correction
    provides: "D-10/D-11/D-12/D-13 nested layout + dispatch dict design decisions (CONTEXT.md / RESEARCH.md)"
provides:
  - "lib_code_parser/_paths.py with get_module_name() as single source of truth (ARC-04, DET-04 substrate)"
  - "lib_code_parser/_dispatch.py with 3 typed empty dispatch dicts FRONTENDS / PRIMITIVES / EVALUATIONS (D-12)"
  - "Callable type aliases FrontendFn / PrimitiveFn / EvaluationFn for dispatch signatures"
  - "Append-only invariant documented in module docstring (D-13 #4, code review gate)"
  - "TYPE_CHECKING forward refs to CAV / ParserConfig avoid import cycle (T-06-04)"
  - "Wave 0 unit tests (14 passed) anchoring path / dispatch invariants"
affects:
  - "01-09-eliminate-anti-patterns (will shim the 4 v0.1.0 _get_module_name to _paths.get_module_name)"
  - "01-08-design-docs-and-extending (docs/09-extending.md formalizes the Open-Closed 6-invariant contract referenced here)"
  - "02-* (Phase 2 will add 'python' to FRONTENDS and 4 entries to PRIMITIVES)"
  - "03-* (Phase 3 will add 5 diagrams + 2 specs to EVALUATIONS)"
  - "04-* (Phase 4 will add 'cpp' to FRONTENDS)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Static dispatch tables (module-level dicts keyed by str → typed Callable) — closed registry, no plugin/entry-points mechanism"
    - "TYPE_CHECKING + string forward refs for breaking import cycles between dispatch layer and models layer"
    - "Single-source helper pattern: one canonical implementation + thin re-export shims (shimming deferred to Plan 09)"

key-files:
  created:
    - "lib_code_parser/_paths.py"
    - "lib_code_parser/_dispatch.py"
    - "tests/unit/test_paths.py"
    - "tests/unit/test_dispatch.py"
  modified: []

key-decisions:
  - "Dispatch dicts use Callable type aliases (not Protocol) — module-level pure functions are the registry entries; Protocol would attract method-shaped expectations conflicting with this design (RESEARCH §Dispatch Dict Pattern)"
  - "MappingProxyType deliberately not used — would block legitimate Phase 2-4 dict additions; append-only invariant is enforced by code review per pre-resolved Open Question #4"
  - "TYPE_CHECKING gating used for CAV / ParserConfig forward refs — these models live under lib_code_parser/models/infrastructure/ (per D-10 nested layout, to be created in Plan 07); load-time importing them from _dispatch would cycle when executor imports _dispatch"
  - "Phase 1 RELAXED gate for no-duplication: this plan only asserts get_module_name is defined exactly once in _paths.py; the hard 'no _get_module_name anywhere outside _paths.py' gate is owned by Plan 09 (which patches the 4 v0.1.0 extractors)"

patterns-established:
  - "Single source of truth helper at top of nested layout (`lib_code_parser/_paths.py`) — future cross-cutting helpers follow same convention"
  - "Open-Closed dispatch registry: executor walks the 3 dicts; never grows logic; new extractors append one entry"
  - "Module docstring carries trace IDs and forward-references companion docs (e.g., docs/09-extending.md)"

requirements-completed: [ARC-04, DET-04]

# Metrics
duration: 4min
completed: 2026-05-24
---

# Phase 01 Plan 06: Paths and Dispatch Substrate Summary

**`_paths.py` ships `get_module_name()` as the single source of truth (ARC-04 substrate) and `_dispatch.py` ships 3 typed empty Callable-keyed dispatch tables (FRONTENDS / PRIMITIVES / EVALUATIONS) with the append-only Open-Closed invariant documented (DET-04 substrate).**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-24T23:11:41Z
- **Completed:** 2026-05-24T23:15:41Z
- **Tasks:** 2 (both TDD: RED → GREEN)
- **Files created:** 4 (2 source + 2 test)
- **Files modified:** 0 (v0.1.0 extractors untouched per plan scope — Plan 09 owns wiring)

## Accomplishments

- Locked the centralization point for module-name derivation BEFORE the 4 v0.1.0 extractors get patched (Plan 09 will shim them).
- Locked the dispatch surface BEFORE any extractor is registered (Phase 2-4 will only append, never modify).
- Established the TYPE_CHECKING + string forward-ref pattern for inter-layer references that would otherwise cycle.
- 14 Wave 0 unit tests pass (6 in test_paths.py + 8 in test_dispatch.py); full suite 125 passed (no regression on v0.1.0).

## Task Commits

Each task was committed atomically with full RED → GREEN TDD gate sequence:

1. **Task 1 RED: failing tests for get_module_name** — `85aff1b` (test)
2. **Task 1 GREEN: _paths.get_module_name single-source helper** — `8ad7fe0` (feat)
3. **Task 2 RED: failing tests for _dispatch typed empty dicts** — `cba2cac` (test)
4. **Task 2 GREEN: _dispatch with 3 typed empty dispatch dicts** — `59ed0d9` (feat)

_TDD gate compliance: both tasks have `test(...)` commit before `feat(...)` commit. No REFACTOR commits were needed — both implementations were minimal-by-design and ruff/pyright-clean on first compose (after one isort auto-fix on _dispatch.py, see Deviations)._

## Files Created/Modified

- `lib_code_parser/_paths.py` — Single source of truth for `path → module-name`; exports `get_module_name(path: str) -> str` returning `Path(path).stem` (byte-equivalent v0.1.0 semantics). Module docstring traces ARC-04 / DET-04. `__all__ = ["get_module_name"]`.
- `lib_code_parser/_dispatch.py` — 3 typed empty dispatch dicts (FRONTENDS / PRIMITIVES / EVALUATIONS) + 3 Callable type aliases (FrontendFn / PrimitiveFn / EvaluationFn). TYPE_CHECKING-gated forward imports of `CAV` / `ParserConfig` (string refs in Callable signatures). Module docstring documents the Open-Closed append-only invariant (#4) and forward-references docs/09-extending.md. Per-dict comments preview which Phase will populate each.
- `tests/unit/test_paths.py` — 6 tests: 5 happy-path (basic / directory / dots / no-extension / empty) + 1 single-source assertion (Phase 1 RELAXED gate).
- `tests/unit/test_dispatch.py` — 8 tests: 3 emptiness + 2 docstring (append-only + extending forward-ref) + 1 callable-aliases importability + 2 source-file invariants (no MappingProxyType, no Protocol).

## Decisions Made

- **No Protocol, only Callable** — Pre-resolved by RESEARCH §Dispatch Dict Pattern; Protocol would attract method-shaped expectations conflicting with module-level pure-function entries.
- **No MappingProxyType** — Pre-resolved; runtime immutability would block legitimate Phase 2-4 dict additions. Append-only is a code-review gate (Open Question #4), not a runtime gate.
- **No entry_points / pluggy plugin mechanism** — Pre-resolved by RESEARCH; closed registry only. `pyproject.toml` declares no `[project.entry-points]` section that could populate dispatch dicts externally (T-06-03 mitigation).
- **Phase 1 single-source gate is RELAXED** — Plan 09 owns the hard "no `_get_module_name` outside `_paths.py`" gate after it patches the 4 v0.1.0 extractors to thin shims. This plan only asserts that `_paths.py` contains `def get_module_name(` exactly once.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ruff isort reordered `from typing import Callable, TYPE_CHECKING` to `from typing import TYPE_CHECKING, Callable`**

- **Found during:** Task 2 GREEN (after `_dispatch.py` write)
- **Issue:** Plan acceptance criterion #10 literally requires `grep -c 'from typing import Callable, TYPE_CHECKING' lib_code_parser/_dispatch.py >= 1`, but project's enforced lint (`ruff check`, rule group `I` per CONVENTIONS.md / pyproject.toml) sorts imports alphabetically, producing `from typing import TYPE_CHECKING, Callable`. The two requirements are in direct conflict.
- **Fix:** Accepted ruff's isort ordering. The AC's semantic intent — "TYPE_CHECKING is imported from typing (for forward-ref cycle avoidance)" — is preserved and verifiable: `grep -cE 'from typing import.*TYPE_CHECKING' lib_code_parser/_dispatch.py` returns 1.
- **Files modified:** lib_code_parser/_dispatch.py (via `ruff check --fix`)
- **Verification:** `ruff check lib_code_parser/_dispatch.py` exits 0; `ruff format --check` clean; all 8 _dispatch tests still pass; full suite 125 passed.
- **Committed in:** 59ed0d9 (Task 2 GREEN commit; deviation noted in commit message body)

**2. [Bonus tests, not a deviation per Rule 1-3] _dispatch.py source-file invariants added to test_dispatch.py**

- **Found during:** Task 2 RED design
- **Issue:** Plan `<behavior>` listed 6 tests; AC #11/#12 require `grep` checks for "no MappingProxyType" and "no Protocol" but did not specify Python-level assertions for them.
- **Decision:** Added 2 source-file-read tests (`TestDispatchSourceFile.test_no_mappingproxytype`, `test_no_protocol`) so the invariants are enforced by the pytest suite, not only by manual `grep`. This **strengthens** the design without violating plan scope.
- **Resulting test count:** 8 instead of the planned 6. AC #1 (the only AC that pins a test count) requires "all tests passing" — semantic intent preserved.

---

**Total deviations:** 1 auto-fixed (Rule 3 blocking — lint/AC conflict), 1 documented design strengthening.
**Impact on plan:** No scope creep. Both adjustments preserve the plan's design intent and improve enforceability of pre-resolved decisions.

## Issues Encountered

None. Both tasks executed in straight RED → GREEN sequence with no implementation iteration.

## Threat Surface Scan

All new surface is covered by the plan's existing `<threat_model>`:

| Threat ID | Mitigation Status |
|-----------|-------------------|
| T-06-01 (semantics drift) | Mitigated — `Path(path).stem` byte-equivalent to v0.1.0; 5 happy-path tests assert behavior |
| T-06-02 (dispatch entry overwrite) | Accepted — code review gate documented in `_dispatch.py` docstring |
| T-06-03 (entry_points abuse) | Mitigated — no `[project.entry-points]` section in pyproject.toml; module-level dict is a closed registry |
| T-06-04 (import cycle) | Mitigated — TYPE_CHECKING + string forward refs `"CAV"` / `"ParserConfig"`; verified by clean import at test-collection time |

**No new threat surface introduced beyond the registered set.**

## Known Stubs

The 3 dispatch dicts ship intentionally **empty** in Phase 1 — this is the documented design (D-12 + per-dict source comments). They are NOT bugs:

- `FRONTENDS = {}` — Phase 2 adds `'python'`; Phase 4 adds `'cpp'`.
- `PRIMITIVES = {}` — Phase 2 adds 4 entries (functions, call_graph, type_deps, contracts).
- `EVALUATIONS = {}` — Phase 3 adds 5 diagrams + 2 specs.

Each dict carries an inline comment stating which Phase populates it. Module docstring states the executor walks these dicts.

## User Setup Required

None — pure-Python additions, no external services.

## Next Phase Readiness

- **For Plan 07 (nested layout scaffolding, D-10):** `_paths.py` and `_dispatch.py` are ready at the top of the nested layout. Plan 07 creates `lib_code_parser/models/{infrastructure,primitives,evaluations}/`, `frontends/`, `extractors/`, `adapters/` directories — `_dispatch.py`'s TYPE_CHECKING import targets (`lib_code_parser.models.infrastructure.cav.CAV`, `lib_code_parser.models.infrastructure.config.ParserConfig`) anticipate Plan 07's layout.
- **For Plan 08 (design docs):** `_dispatch.py` module docstring forward-references `docs/09-extending.md`. Plan 08 will create that file with the full 6-invariant Open-Closed contract (the append-only invariant #4 is already cited).
- **For Plan 09 (eliminate anti-patterns):** `_paths.get_module_name` is ready to be shimmed by the 4 v0.1.0 extractor `_get_module_name` definitions. Phase 1 RELAXED gate (`get_module_name` defined once in `_paths.py`) holds; Plan 09 will finalize the hard "no duplication outside _paths.py" gate.

**No blockers introduced.**

## Self-Check: PASSED

Verified via the project's actual state:

- `lib_code_parser/_paths.py` exists — confirmed via `ls`.
- `lib_code_parser/_dispatch.py` exists — confirmed via `ls`.
- `tests/unit/test_paths.py` exists with 6 passing tests — confirmed via `pytest -q`.
- `tests/unit/test_dispatch.py` exists with 8 passing tests — confirmed via `pytest -q`.
- Commits `85aff1b`, `8ad7fe0`, `cba2cac`, `59ed0d9` exist in branch `worktree-agent-a14cf47d9db6a4ae3` — confirmed via `git log --oneline`.
- Full test suite: 125 passed — confirmed via `pytest tests/ -q`.
- `ruff check` clean on both new source files — confirmed.
- `ruff format --check` clean on all 4 new files — confirmed.

---
*Phase: 01-architecture-foundation-spec-correction*
*Plan: 06 (paths and dispatch substrate)*
*Completed: 2026-05-24*
