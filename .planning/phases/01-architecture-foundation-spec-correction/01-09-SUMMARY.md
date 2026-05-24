---
phase: 01-architecture-foundation-spec-correction
plan: 09
subsystem: infra
tags: [layout-migration, parity, nested-modules, single-source-of-truth, v0.2.0, sc-3-hard-gate]

# Dependency graph
requires:
  - phase: 01-architecture-foundation-spec-correction
    provides: "Plan 03 — infrastructure subpackage (CAV / ArtifactId / NormalizedArtifact[TContent] / CodeContent / typed ParserConfig); Plan 04 — primitives subpackage (FunctionNode / ParamInfo / SourceRange / TraceTag / CallEdge / CallGraph / TypeDep / ContractInfo); Plan 05 — evaluations subpackage (EdgeKind closed Literal + GraphNode / GraphEdge / GraphModel / GuardExpr); Plan 06 — _paths.get_module_name single source of truth + _dispatch typed empty registries; Plan 07 — adapters/base.py subprocess hardening"
provides:
  - "Rewritten lib_code_parser/__init__.py: v0.1.0 13-name backward-compat surface (ORDER PRESERVED) + v0.2.0 6-name additions (CAV, EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr); __version__ bumped to 0.2.0"
  - "Rewired lib_code_parser/models/__init__.py: barrel re-exports all 18 model names from Plans 03/04/05; v0.1.0 ParserConfig parity stub (params dict shape) retained for transitional Phase 1 window"
  - "Deleted lib_code_parser/models.py (legacy v0.1.0 module replaced by models/ subpackage)"
  - "Shimmed 4 v0.1.0 extractors (ast_extractor.py / callgraph_builder.py / type_dep_builder.py / contract_extractor.py) to re-export _get_module_name from lib_code_parser._paths.get_module_name; identity verified for all 4"
  - "Created 3 empty Phase 2-4 placeholder packages (lib_code_parser/frontends, extractors, extractors/primitives)"
  - "Wave 0 parity test suite (tests/parity/test_v01_v02_compat.py) with 11 tests locking the v0.1.0->v0.2.0 contract including the ROADMAP §Phase 1 SC-3 hard gate (grep-based no-duplication assertion)"
  - "ROADMAP §Phase 1 SC-1 finalized: from lib_code_parser import {CodeParserExecutor, ..., CAV, EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr} works; from lib_code_parser.models import X also works for both v0.1.0 and v0.2.0 names"
  - "ROADMAP §Phase 1 SC-3 finalized: _paths.get_module_name is the SOLE definition (grep -rn '^def _get_module_name|^def get_module_name' lib_code_parser/ returns exactly 1 line)"
  - "D-06 byte-identical JSON parity asserted live: NormalizedArtifact(...) and NormalizedArtifact[CodeContent](...) produce identical model_dump_json()"
affects: ["02-* (Phase 2 dispatch-driven executor rewrite — typed ParserConfig graduates to barrel)", "03-* (Phase 3 diagram extractors — consume EdgeKind + GraphEdge + GraphModel from barrel)", "04-* (Phase 4 C++ frontend — slots into lib_code_parser/frontends/ placeholder)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single source of truth + thin re-export shim: 4 v0.1.0 extractors retain the private symbol _get_module_name as `from lib_code_parser._paths import get_module_name as _get_module_name` so existing test imports keep working (identity is preserved)"
    - "Transitional parity stub: legacy v0.1.0 ParserConfig (params dict shape) co-exists with the typed v0.2.0 ParserConfig (extra=forbid, typed fields per ARC-05); barrel exposes the legacy stub for v0.1.0 executor + tests, infrastructure path exposes the typed variant for Phase 2"
    - "Subprocess-driven hard gate test: tests/parity/test_v01_v02_compat.py::test_no_duplicate_module_name_helper invokes grep at runtime against the actual file tree (not a static import-time check) so drift introduced after Plan 09 is caught at test time"
    - "Empty Phase 2-4 placeholder packages: stable import paths from day one (frontends/, extractors/, extractors/primitives/) so Phase 2-4 only need to add files, never restructure directories"

key-files:
  created:
    - "tests/parity/__init__.py"
    - "tests/parity/test_v01_v02_compat.py"
    - "lib_code_parser/frontends/__init__.py"
    - "lib_code_parser/extractors/__init__.py"
    - "lib_code_parser/extractors/primitives/__init__.py"
  modified:
    - "lib_code_parser/__init__.py"
    - "lib_code_parser/models/__init__.py"
    - "lib_code_parser/ast_extractor.py"
    - "lib_code_parser/callgraph_builder.py"
    - "lib_code_parser/type_dep_builder.py"
    - "lib_code_parser/contract_extractor.py"
  deleted:
    - "lib_code_parser/models.py"

key-decisions:
  - "Rule 1 deviation: barrel-level lib_code_parser.ParserConfig retains the v0.1.0 stub shape (params: dict[str, object]) for the Phase 1 transitional window; the typed ARC-05 ParserConfig stays at lib_code_parser.models.infrastructure.config.ParserConfig until Phase 2 rewrites the executor as dispatch-driven (D-12). The parity test asserts the ARC-05 contract at the canonical typed location, not at the barrel."
  - "Executor body kept BYTE-IDENTICAL to v0.1.0 per the plan objective; only the import block consumes the new models/ package barrel via the legacy path (`from lib_code_parser.models import ArtifactId, CodeContent, NormalizedArtifact, ParserConfig`), which now resolves to a mix of Plan 03 infrastructure models (ArtifactId, CodeContent, NormalizedArtifact) and the Plan 09 parity stub (ParserConfig with params dict)."
  - "_get_module_name shim uses `as` alias (`from lib_code_parser._paths import get_module_name as _get_module_name`) so the v0.1.0 private symbol `lib_code_parser.ast_extractor._get_module_name` keeps resolving and is the same Python object as the canonical `lib_code_parser._paths.get_module_name` (identity check passes for all 4 extractors)."
  - "Placeholder package docstrings rewritten to fit the 100-char line-length lint (originally >108 chars triggered ruff E501); semantic intent (`Phase 2 adds python.py; Phase 4 adds cpp.py`) preserved."

patterns-established:
  - "v0.1.0 -> v0.2.0 caller parity contract is enforced by a dedicated tests/parity/ directory rather than scattered across acceptance/unit. Future migration plans should add tests to tests/parity/ rather than mutate existing acceptance tests."
  - "Hard-gate grep tests live in tests/parity/ as runtime subprocess calls against the file tree (catches drift after the gating plan ships)."

requirements-completed: [ARC-01, ARC-04, DET-04]

# Metrics
duration: ~30min
completed: 2026-05-25
---

# Phase 01 Plan 09: Layout Migration and Parity Summary

**v0.1.0 -> v0.2.0 nested-layout migration closed: 13-name v0.1.0 barrel surface preserved unchanged, 6 v0.2.0 additions exposed (CAV, EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr), legacy `lib_code_parser/models.py` deleted, 4× duplicated `_get_module_name` eliminated at the source level (single source: `_paths.get_module_name`), and 11-test parity gate locks the contract.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-05-25T08:37Z (worktree spawn)
- **Completed:** 2026-05-25T08:48Z
- **Tasks:** 3 (all `tdd="true"`)
- **Files created:** 5 (2 source placeholders + 1 source placeholder + 2 test files)
- **Files modified:** 6
- **Files deleted:** 1

## Accomplishments

- **ROADMAP §Phase 1 SC-1 closed:** All 19 names (13 v0.1.0 + 6 v0.2.0) importable from `lib_code_parser` AND `lib_code_parser.models` barrels. `lib_code_parser.__version__ == "0.2.0"`.
- **ROADMAP §Phase 1 SC-3 hard gate closed:** `grep -rn '^def _get_module_name|^def get_module_name' lib_code_parser/ --include='*.py'` returns exactly 1 line: `lib_code_parser/_paths.py:18:def get_module_name(path: str) -> str:`. The 4 v0.1.0 extractors retain the v0.1.0 private symbol `_get_module_name` as a re-export alias (identity-preserving shim) so existing test imports (`tests/acceptance/test_fr01_function_extraction.py` 3 sites + `tests/unit/test_ast_extractor.py` 1 site) keep working unchanged.
- **D-06 byte-identical JSON parity asserted live:** `test_normalized_artifact_json_byte_identical` confirms `NormalizedArtifact(...).model_dump_json()` and `NormalizedArtifact[CodeContent](...).model_dump_json()` produce byte-identical output on the project's Pydantic 2.11.10 environment.
- **v0.1.0 caller parity intact end-to-end:** Full test suite 187 passed (176 v0.1.0 baseline + 11 new Plan 09 parity tests). All 6 acceptance tests + 5 unit tests + 17 Plan 03 model tests + 6 Plan 04 primitive tests + 13 Plan 05 evaluation tests + 14 Plan 06 path/dispatch tests + 15 Plan 07 adapter tests pass unchanged.
- **Coverage 96.57%** — well above the 80% gate. Plan 09 itself contributes 100% coverage on the rewritten `__init__.py` files and the new placeholder packages.
- **Legacy `lib_code_parser/models.py` deleted via `git rm`** — the package directory `lib_code_parser/models/` is now the canonical location and no longer competes with a same-named module file for import precedence.

## Task Commits

Each task was committed atomically with the per-task TDD RED -> GREEN cycle inline-verified:

1. **Task 1: Rewrite barrel + delete legacy models.py** — `5d06bde` (feat)
   - Rewrites `lib_code_parser/__init__.py` for the 19-name surface + `__version__ = "0.2.0"`.
   - Rewires `lib_code_parser/models/__init__.py` to re-export from Plans 03/04/05 + keeps the v0.1.0 ParserConfig parity stub.
   - Deletes `lib_code_parser/models.py` (git rm).
   - Executor body untouched.
2. **Task 2: Shim `_get_module_name` + Phase 2-4 placeholders** — `7fb6bb5` (refactor)
   - All 4 v0.1.0 extractors patched: local `def _get_module_name(path)` removed; `from lib_code_parser._paths import get_module_name as _get_module_name` added.
   - 3 empty placeholder packages created: `frontends/`, `extractors/`, `extractors/primitives/`.
3. **Task 3: Wave 0 parity gate** — `d88bd23` (test)
   - 11 parity tests in `tests/parity/test_v01_v02_compat.py` (1 more than the plan's 10 — added `test_lib_code_parser_module_is_a_package_not_a_module` defensive check confirming the legacy file deletion).

**Plan metadata commit:** to follow this SUMMARY.

_All three tasks are `tdd="true"`. RED steps were verified inline as the Task 1 acceptance verify command failing pre-rewrite, the Task 2 identity check returning `False` pre-shim, and the Task 3 test file being absent pre-creation. GREEN steps verified by the acceptance gates documented under each task below._

## Files Created/Modified

### Created

- `lib_code_parser/frontends/__init__.py` — Empty Phase 2-4 placeholder package. Phase 2 adds `python.py`; Phase 4 adds `cpp.py`.
- `lib_code_parser/extractors/__init__.py` — Empty Phase 2-4 placeholder package.
- `lib_code_parser/extractors/primitives/__init__.py` — Empty Phase 2 placeholder package.
- `tests/parity/__init__.py` — Pytest package marker for the parity test suite.
- `tests/parity/test_v01_v02_compat.py` — 11 parity tests (see Task Commits §Task 3).

### Modified

- `lib_code_parser/__init__.py` — Rewritten for v0.2.0 surface; `__version__ = "0.2.0"`; 19-name `__all__` (v0.1.0 13 ORDER PRESERVED + 6 v0.2.0 additions); docstring documents the ParserConfig parity stub rationale.
- `lib_code_parser/models/__init__.py` — Replaces the Wave 1 transitional bridge with the final Plan 09 wiring: re-exports CAV / ArtifactId / NormalizedArtifact / CodeContent from `models.infrastructure`; re-exports the 8 primitives from `models.primitives`; re-exports the 5 evaluation names from `models.evaluations`; retains the v0.1.0 ParserConfig parity stub locally so `from lib_code_parser.models import ParserConfig` keeps returning the v0.1.0-shape model the executor + 6 v0.1.0 tests rely on.
- `lib_code_parser/ast_extractor.py` / `callgraph_builder.py` / `type_dep_builder.py` / `contract_extractor.py` — Each: removed `def _get_module_name(path)` (3-line local function) and `from pathlib import Path` (no longer used in the file); added `from lib_code_parser._paths import get_module_name as _get_module_name`. All other extractor logic byte-identical to v0.1.0.

### Deleted

- `lib_code_parser/models.py` — Replaced by the `lib_code_parser/models/` package directory from Plans 03/04/05. Verified absent via `[ ! -f lib_code_parser/models.py ]`.

## Decisions Made

- **Rule 1 deviation — barrel-level ParserConfig is the v0.1.0 parity stub, not the typed v0.2.0 variant.** See "Deviations from Plan" below for the full rationale and acceptance-test relocation.
- **Executor body kept byte-identical to v0.1.0** per the plan's explicit objective (`Executor logic body (lines 19-86 in v0.1.0) MUST remain unchanged`). The executor reads `config.params.get(...)` — that's the v0.1.0 ParserConfig API — so the barrel-level ParserConfig MUST be the v0.1.0-shape stub for the executor to keep working. Phase 2's dispatch-driven executor rewrite (D-12) is the planned migration point where the typed ParserConfig graduates to the barrel.
- **Shim uses `as _get_module_name` alias** so the v0.1.0 private symbol `lib_code_parser.ast_extractor._get_module_name` resolves and (critically) IS the same Python object as `lib_code_parser._paths.get_module_name`. The parity test `test_no_duplicate_module_name_helper` enforces the source-level invariant; the identity check in the executed Python proves the runtime invariant.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan internal contradiction] Barrel-level `ParserConfig` MUST be the v0.1.0 parity stub, not the typed v0.2.0 variant**

- **Found during:** Task 1 design (cross-checking the plan's `must_haves.truths` against the plan's `<acceptance_criteria>` and Task 3 `<behavior>`).
- **Issue:** Three plan requirements were in direct conflict:
  - `must_haves.truths[1]`: "Existing tests/acceptance/test_fr01..06_*.py (6 files) pass unchanged" — these tests pass `ParserConfig(..., params={...}, enabled=...)`. The legacy v0.1.0 ParserConfig accepts this; the typed Plan 03 ParserConfig (which has `extra="forbid"` and no `params` field) raises `ValidationError`.
  - `must_haves.truths[2]`: "Existing tests/unit/test_*.py (5 files) pass unchanged" — `tests/unit/test_executor.py` constructs `ParserConfig(..., params={'language': 'python', 'extract_contracts': True}, enabled=True)`. Same conflict.
  - Plan 09 Task 3 `<behavior>::test_parser_config_unknown_field_raises`: "`ParserConfig(artifact_type="code", executor_lib="lib_code_parser", surprise=1)` raises ValidationError (ARC-05 hard gate)" — this requires the typed ParserConfig.
  - Plan 09 Task 1 `<action>::Step 3 Recommendation`: "Implement Option B... `from lib_code_parser.models.infrastructure import CAV, ArtifactId, NormalizedArtifact, CodeContent, ParserConfig`" — would expose the typed variant at the barrel.
  - Plan 09 Task 1 `<action>::Step 3 Executor`: "Executor logic body (lines 19-86 in v0.1.0) MUST remain unchanged" — the executor reads `config.params.get(...)`, which only works on the v0.1.0 stub.
- **Why this is a Rule 1 (bug) rather than Rule 4 (architectural decision):** The conflict is internal to the plan; the architectural decision (D-08 typed ParserConfig is the v0.2.0 contract; Plan 09 is the Wave 2 layout migration) is locked in CONTEXT/RESEARCH. The plan's Option-B recommendation in Task 1 Step 3 simply did not account for the executor's continued dependency on `config.params.get(...)`. Fixing it does not introduce a new architectural commitment.
- **Fix:** Retained the v0.1.0 ParserConfig parity stub at both `lib_code_parser.models.ParserConfig` and `lib_code_parser.ParserConfig`. The typed v0.2.0 ParserConfig stays at `lib_code_parser.models.infrastructure.config.ParserConfig` (where Plan 03 placed it). Updated `test_parser_config_unknown_field_raises` to import the typed variant from the canonical infrastructure path so the ARC-05 hard gate is still pinned to the actual typed model, just not at the barrel symbol. Documented the dual-path arrangement at the top of `lib_code_parser/models/__init__.py` and `lib_code_parser/__init__.py` so Phase 2's executor rewrite (D-12) knows where to graduate the typed variant.
- **Files modified:** `lib_code_parser/models/__init__.py` (added v0.1.0 ParserConfig stub class + docstring); `lib_code_parser/__init__.py` (docstring annotates ParserConfig parity-stub status); `tests/parity/test_v01_v02_compat.py` (imports typed ParserConfig from the infrastructure path).
- **Verification:** Full test suite 187 passed. All 6 acceptance tests pass with `params=` API. All 11 parity tests pass including the ARC-05 hard gate at the infrastructure path. Plan 09 Task 1 acceptance criterion #6 (`exe.execute(__import__('lib_code_parser').ParserConfig(artifact_type='code', executor_lib='lib_code_parser'), ...)`) exits 0.
- **Committed in:** `5d06bde` (Task 1) for the implementation; `d88bd23` (Task 3) for the test relocation.

**2. [Rule 3 - Blocking] Ruff isort auto-reordered import blocks in 3 files**

- **Found during:** Task 1 GREEN (`ruff check lib_code_parser/__init__.py lib_code_parser/models/__init__.py`) and Task 3 GREEN (`ruff check tests/parity/`).
- **Issue:** `ruff check` enforces `select=["I"]` (isort) per `pyproject.toml`. The hand-written import blocks in `lib_code_parser/models/__init__.py` and `tests/parity/test_v01_v02_compat.py` did not satisfy alphabetical ordering, so ruff reported errors that would block the plan's "ruff check exits 0" implicit gate.
- **Fix:** Applied `ruff check --fix` to auto-sort the imports. Re-ran the full pytest suite to confirm zero regressions; re-ran ruff to confirm clean.
- **Files modified:** `lib_code_parser/models/__init__.py`, `tests/parity/test_v01_v02_compat.py`.
- **Verification:** `ruff check lib_code_parser/ tests/parity/` exits 0; `pytest tests/` 187 passed.
- **Committed in:** `5d06bde` (Task 1) and `d88bd23` (Task 3) — fixes included in the same commits as the files they affected.

**3. [Rule 3 - Blocking] Ruff E501 line-too-long on placeholder docstrings**

- **Found during:** Task 2 GREEN (`ruff check lib_code_parser/`).
- **Issue:** The plan literally specified `"""Extractors (Phase 2-4 add primitives/ and top-level evaluation modules). Empty placeholder in Phase 1."""` (108 chars) and `"""Primitives extractors (Phase 2 implements functions/callgraph/type_deps/contracts). Empty placeholder in Phase 1."""` (119 chars). Both exceed the project's `line-length = 100` lint.
- **Fix:** Rewrote both docstrings to `"""Extractors — Phase 2-4 add primitives/ and top-level evaluation modules."""` (76 chars) and `"""Primitives extractors — Phase 2 implements functions/callgraph/type_deps/contracts."""` (88 chars). Semantic intent preserved; phase ownership and content still documented.
- **Files modified:** `lib_code_parser/extractors/__init__.py`, `lib_code_parser/extractors/primitives/__init__.py`.
- **Verification:** `ruff check lib_code_parser/` exits 0; placeholder line-count gate still satisfied (`[ $(wc -l < ...) -le 2 ]`).
- **Committed in:** `7fb6bb5` (Task 2 commit — fix included).

**4. [Rule 3 - Bonus] Added 11th parity test (`test_lib_code_parser_module_is_a_package_not_a_module`) beyond the plan's enumerated 10**

- **Found during:** Task 3 design.
- **Issue:** The plan's `must_haves.truths[5]` says `lib_code_parser/models.py` file is removed. The other 10 parity tests verify the import surface but do not directly assert the legacy module file's absence on disk. A drifty future refactor could re-introduce `models.py` and the import surface would still pass (the package would win the precedence race), masking the regression.
- **Decision:** Added one defensive test (`test_lib_code_parser_module_is_a_package_not_a_module`) that (a) asserts `lib_code_parser.models.__file__` ends in `__init__.py` (it's a package, not a module) and (b) asserts `lib_code_parser/models.py` does not exist on disk. This strengthens the parity contract without changing it.
- **Files modified:** `tests/parity/test_v01_v02_compat.py`.
- **Verification:** Test passes. Total parity-suite count is 11 instead of 10.
- **Committed in:** `d88bd23` (Task 3).

---

**Total deviations:** 4 auto-fixed (1 Rule 1 — plan internal contradiction; 2 Rule 3 — lint/blocking conflicts with literal plan text; 1 bonus test strengthening).
**Impact on plan:** All four fixes preserve the plan's stated intent and improve the enforceability of the migration contract. No scope creep. The Rule 1 deviation is the consequential one: it explicitly defers the D-08 typed ParserConfig graduation to Phase 2, which matches CONTEXT.md's `## code_context` note that "the dispatch-dict-driven rewrite is a Phase 2 deliverable; Phase 1 only fixes the import path because models.py is gone".

## Issues Encountered

- None beyond the four deviations documented above. Wave 1 outputs (Plans 03/04/05/06/07) integrate cleanly; the transitional bridges they shipped in their respective `lib_code_parser/models/__init__.py` and `lib_code_parser/__init__.py` (Plan 05's `try/except` guard) are wholesale replaced by this plan's final wiring, exactly as their summaries anticipated.

## TDD Gate Compliance

The plan marks all 3 tasks `tdd="true"`. RED steps were verified inline:

- **Task 1 RED:** `python -c "from lib_code_parser import CAV, ..."` failed pre-rewrite with `ImportError: cannot import name 'CAV' from 'lib_code_parser'`.
- **Task 1 GREEN:** Same command exits 0 post-rewrite; full pytest passes (176/176).
- **Task 2 RED:** `python -c "from lib_code_parser.ast_extractor import _get_module_name; from lib_code_parser._paths import get_module_name; assert _get_module_name is get_module_name"` failed pre-shim with `AssertionError: ast identity broken` (False).
- **Task 2 GREEN:** Same command succeeds post-shim; identity is `True` for all 4 extractors; pytest 176/176.
- **Task 3 RED:** No test file existed pre-Task-3 (`pytest tests/parity/` collected 0 tests).
- **Task 3 GREEN:** 11 parity tests pass; full pytest 187/187; coverage 96.57%.

Per the `<tdd_execution>` guidance, RED steps were verified via the acceptance-criteria `python -c ...` commands rather than separate `test(...)` commits because the test file IS the GREEN deliverable for Task 3 and the implementation IS the GREEN deliverable for Tasks 1/2. Git log shows the three Plan 09 commits in canonical order (Task 1 -> Task 2 -> Task 3); no separate RED commit was warranted because each task's RED state was trivially demonstrable from the pre-existing file tree and the plan's own acceptance commands.

## Verification

| Check | Required | Result |
|---|---|---|
| `pytest tests/` exit code | 0 | 0 |
| Test count | >=176 (baseline) | 187 (176 + 11 parity) |
| ROADMAP SC-3 grep hard gate | exactly 1 `def` line | 1 (`lib_code_parser/_paths.py:18`) |
| `lib_code_parser/models.py` exists | NO | NO (deleted via git rm) |
| `lib_code_parser.__version__` | "0.2.0" | "0.2.0" |
| All 19 names importable from `lib_code_parser` | YES | YES |
| All 18 model names importable from `lib_code_parser.models` | YES | YES |
| All 4 extractor `_get_module_name is _paths.get_module_name` | YES | YES (all 4) |
| `from lib_code_parser.ast_extractor import _get_module_name` works | YES | YES |
| 3 Phase 2-4 placeholder packages exist | YES | YES (frontends/, extractors/, extractors/primitives/) |
| `ruff check lib_code_parser/ tests/parity/` | exit 0 | exit 0 |
| Coverage | >=80% | 96.57% |
| D-06 byte-identical JSON parity | YES | YES (asserted live in test) |

## Threat Surface Scan

No new threat surface introduced beyond the plan's `<threat_model>` enumeration. The four registered threats (T-09-01 through T-09-04) are mitigated as planned:

| Threat | Disposition | How addressed | Test that proves it |
|---|---|---|---|
| T-09-01 v0.1.0 caller breaks | mitigate | 13-name `__all__` in `lib_code_parser/__init__.py` ORDER PRESERVED; both barrel paths work | `test_v01_caller_surface_intact` + 176 v0.1.0 baseline tests unchanged |
| T-09-02 Existing test imports break | mitigate | Identity-preserving shim via `as _get_module_name` alias | `test_no_duplicate_module_name_helper` + 4 acceptance test sites + 1 unit test site pass |
| T-09-03 Duplicate `_get_module_name` def survives undetected | mitigate | Subprocess grep gate scans the actual file tree at test time | `test_no_duplicate_module_name_helper` |
| T-09-04 Generic NormalizedArtifact breaks JSON for v0.1.0 callers | mitigate | Live byte-identical JSON assertion | `test_normalized_artifact_json_byte_identical` |
| T-09-05 Supply chain | accept | No `pip install` in this plan | n/a |

## Known Stubs

The barrel-level `lib_code_parser.ParserConfig` is intentionally the v0.1.0 parity stub (params dict, no `extra="forbid"`) for the Phase 1 transitional window. This is documented in both `lib_code_parser/__init__.py` and `lib_code_parser/models/__init__.py` module docstrings and in this SUMMARY's deviation #1. Phase 2 graduates the typed v0.2.0 ParserConfig (which lives at `lib_code_parser.models.infrastructure.config.ParserConfig` and is already complete per Plan 03) to the barrel when the executor is rewritten as dispatch-driven (D-12). The parity test asserts the ARC-05 typed contract at the infrastructure path, so the gate is locked at the canonical location and Phase 2's task is purely "swap the barrel re-export and update the executor body".

The 3 placeholder packages (`frontends/`, `extractors/`, `extractors/primitives/`) are intentionally empty in Phase 1; their `__init__.py` docstrings describe what Phase 2-4 add. These are not stubs in the "broken UI" sense — they are stable extension points.

## User Setup Required

None — Plan 09 only edits Python source files inside the package. No external services, no environment variables, no dashboard config.

## Next Phase Readiness

- **Phase 2 (extractor rewrite + dispatch-driven executor):** Phase 1 infrastructure is complete. `lib_code_parser/_dispatch.py` (Plan 06) has 3 typed empty registries ready to receive Phase 2's frontend (`python`) and 4 primitive entries (`functions`, `call_graph`, `type_deps`, `contracts`). The empty `lib_code_parser/extractors/primitives/__init__.py` is the canonical destination for the new extractor modules. The typed v0.2.0 ParserConfig is ready to graduate to the barrel as part of the executor rewrite.
- **Phase 3 (diagram extractors):** Phase 1 evaluations layer (Plan 05) is locked and exposed via the barrel. Phase 3 only needs to populate `_dispatch.EVALUATIONS` with 5 diagram + 2 spec entries.
- **Phase 4 (C++ frontend):** `lib_code_parser/frontends/__init__.py` placeholder is ready to receive `cpp.py`. The infrastructure CAV (Plan 03) already accepts `Literal["python", "cpp"]` for `language` discrimination.
- **Blockers/concerns:** None for Phase 2 entry. The SP-3 spike (libclang on macOS arm64 + Python 3.13/3.14) is a Phase 4 concern, not blocking Phase 2.

## Self-Check: PASSED

Verified before SUMMARY commit:

**Files created (existence verified via `[ -f path ]`):**
- `lib_code_parser/frontends/__init__.py` — FOUND
- `lib_code_parser/extractors/__init__.py` — FOUND
- `lib_code_parser/extractors/primitives/__init__.py` — FOUND
- `tests/parity/__init__.py` — FOUND
- `tests/parity/test_v01_v02_compat.py` — FOUND

**Files deleted (absence verified via `[ ! -f path ]`):**
- `lib_code_parser/models.py` — ABSENT (confirmed via `git status` clean post-commit + filesystem check)

**Commits exist (verified via `git log --oneline -5`):**
- `5d06bde` (Task 1: feat) — FOUND
- `7fb6bb5` (Task 2: refactor) — FOUND
- `d88bd23` (Task 3: test) — FOUND

**Test results:**
- `pytest tests/` — 187 passed in ~2.0s
- `pytest tests/parity/test_v01_v02_compat.py -v` — 11 passed
- `pytest tests/ --cov=lib_code_parser --cov-fail-under=80` — 96.57% (gate satisfied)
- `ruff check lib_code_parser/ tests/parity/` — All checks passed!
- `grep -rn '^def _get_module_name|^def get_module_name' lib_code_parser/ --include='*.py' | wc -l` — 1 (ROADMAP SC-3 hard gate satisfied)

**Plan acceptance hard gates:**
- All 19 names importable from `lib_code_parser` ✓
- All 18 model names importable from `lib_code_parser.models` ✓
- `lib_code_parser/models.py` absent ✓
- `__version__ == "0.2.0"` ✓
- Single source of truth for `_get_module_name` ✓
- All 4 extractors `_get_module_name is _paths.get_module_name` ✓
- 3 Phase 2-4 placeholder packages exist + are minimal ✓
- D-06 byte-identical JSON parity live-asserted ✓

---
*Phase: 01-architecture-foundation-spec-correction*
*Plan: 09 — layout migration and parity*
*Completed: 2026-05-25*
