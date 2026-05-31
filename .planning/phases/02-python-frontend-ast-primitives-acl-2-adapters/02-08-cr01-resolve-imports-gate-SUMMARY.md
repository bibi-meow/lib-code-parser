---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 08
subsystem: api
tags: [pyright, determinism, type-deps, pydantic, ast, gap-closure]

# Dependency graph
requires:
  - phase: 02-python-frontend-ast-primitives-acl-2-adapters
    provides: "type_deps extractor (plan 02-06) + PyrightAdapter (plan 02-05) + typed ParserConfig (ARC-05)"
provides:
  - "ParserConfig.resolve_imports gate (default False) — execute() restored to a pure function of (raw_content, path, config)"
  - "type_deps pure default path (AST-only, resolved=True, no subprocess) + opt-in pyright-hybrid path"
affects: [architecture_verifier, spec_code_verifier, layer-m-bisimulation, phase-03-evaluations]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Opt-in environment-dependent behavior behind an additive default-safe config flag"
    - "Pure default path / explicit opt-in side-effecting path split inside a single extractor"

key-files:
  created:
    - .planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-08-cr01-resolve-imports-gate-SUMMARY.md
  modified:
    - lib_code_parser/models/infrastructure/config.py
    - lib_code_parser/extractors/primitives/type_deps.py
    - tests/unit/models/test_config.py
    - tests/unit/extractors/test_type_deps_extractor.py
    - tests/acceptance/test_fr03_type_deps.py
    - .planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-HUMAN-UAT.md
    - .planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-VERIFICATION.md

key-decisions:
  - "CR-01 resolved via Option B (user-approved): pyright import-resolution is opt-in, not the default."
  - "Default path sets resolved=True optimistically (TypeDep model default) — no pyright, no subprocess, never raises on missing pyright."
  - "resolve_imports=True keeps the unchanged RESEARCH §2.3 pyright-hybrid path (D-06 fail-loudly, 0→1-based normalize, DET-04 sort)."

patterns-established:
  - "Determinism-sensitive external-tool calls are gated behind an additive default-False config flag so the default contract stays pure."

requirements-completed: []

# Metrics
duration: 6min
completed: 2026-05-31
---

# Phase 2 Plan 08: CR-01 resolve_imports Gate Summary

**pyright import-resolution made opt-in via `ParserConfig.resolve_imports=False`, restoring `execute()` as a pure deterministic function of `(raw_content, path, config)` (Layer M bisimulation prerequisite).**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-05-31T13:13:43Z
- **Completed:** 2026-05-31T13:19:58Z
- **Tasks:** 3 (test → feat → docs)
- **Files modified:** 7 (5 code/test + 2 planning docs) + 1 created (this SUMMARY)

## Accomplishments
- Added additive `ParserConfig.resolve_imports: bool = False` (backward-compatible; mirrors the additive `resolved: bool = True` TypeDep default from plan 02-06).
- Gated `type_deps.extract()`: the DEFAULT path no longer constructs/invokes `PyrightAdapter` at all — pure AST-only walk, every TypeDep `resolved=True`, DET-04 sort, no subprocess, no network, no environment dependence, never raises when pyright is absent.
- The `resolve_imports=True` opt-in path is byte-for-byte the prior RESEARCH §2.3 pyright-hybrid behavior (reportMissingImports oracle, D-06 fail-loudly, 0-based→1-based line normalization, DET-04 sort).
- Confirmed `config` already flows to the extractor via the executor dispatch (`primitive_fn(cav, config)`); no dispatch wiring change needed.
- Full suite: 241 passed / 0 failed / 0 skipped (was 235 passed with FR-03 conditionally pyright-skipped); ruff clean. Suite runtime dropped from ~75s to ~5s because the default acceptance path no longer spawns pyright.

## Task Commits

1. **Task 1 (RED): failing tests for resolve_imports gate** — `5bb7b52` (test)
2. **Task 2 (GREEN): resolve_imports gate implementation** — `9ed82e1` (feat)
3. **Task 3 (docs): SUMMARY + UAT + VERIFICATION traceability** — committed with plan metadata (this commit)

## Files Created/Modified
- `lib_code_parser/models/infrastructure/config.py` — added `resolve_imports: bool = False` with CR-01 rationale docstring.
- `lib_code_parser/extractors/primitives/type_deps.py` — branch on `config.resolve_imports`; default returns sorted AST-only deps before any pyright construction; opt-in keeps the hybrid path; expanded docstring documenting both paths.
- `tests/unit/models/test_config.py` — added default-False and opt-in field tests.
- `tests/unit/extractors/test_type_deps_extractor.py` — gated the three pyright-resolution tests behind `_CONFIG_RESOLVE`; added 4 new tests: default path never constructs PyrightAdapter, never raises when pyright would fail, keeps DET-04 sort, and opt-in path does construct/invoke the adapter.
- `tests/acceptance/test_fr03_type_deps.py` — removed the module-level pyright skip (default path is now pyright-free); clarified the resolved-flag docstring.
- `02-HUMAN-UAT.md` — test #1 result → "resolved (Option B applied)"; frontmatter status: resolved, passed: 1, pending: 0.
- `02-VERIFICATION.md` — status human_needed → passed; added a resolution note + human_verification `resolution` field.

## Decisions Made
- Default path uses the optimistic `resolved=True` (the TypeDep model default) rather than a tri-state "unknown", per CR-01's suggested fix and v0.1.0 parity — callers ignoring resolution semantics see an unchanged shape.
- Kept the opt-in path's D-06 hard-fail-when-pyright-absent: acceptable only on the explicit `resolve_imports=True` request, since that caller has chosen environment-dependent resolution.

## Deviations from Plan
None - plan executed exactly as written. (Confirmed `config` already reaches the extractor through the dispatch, so the optional dispatch-wiring step in `the_fix` step 3 was not needed.)

## Issues Encountered
- Transient: removing the now-unused `pytest` import from FR-03 broke the surviving `@pytest.fixture`; restored the import (caught immediately by the post-edit pytest+ruff run).

## User Setup Required
None - no external service configuration required. (The change reduces external dependence: the default path no longer needs pyright installed.)

## Next Phase Readiness
- Phase 2 CR-01 (the sole human-needed verification item) is closed; 02-VERIFICATION.md is now `passed`.
- ROADMAP/STATE phase-complete markers intentionally NOT touched — the orchestrator marks the phase complete after re-verifying.
- Phase 3 evaluations that need import-resolution must opt in with `ParserConfig(resolve_imports=True)`.

## Self-Check: PASSED

- FOUND: 02-08-cr01-resolve-imports-gate-SUMMARY.md
- FOUND: lib_code_parser/models/infrastructure/config.py (resolve_imports field)
- FOUND: lib_code_parser/extractors/primitives/type_deps.py (gate)
- FOUND commit 5bb7b52 (test RED)
- FOUND commit 9ed82e1 (feat GREEN)

---
*Phase: 02-python-frontend-ast-primitives-acl-2-adapters*
*Completed: 2026-05-31*
