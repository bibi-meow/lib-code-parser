---
phase: 01-architecture-foundation-spec-correction
plan: 10
subsystem: infra
tags: [sp3-spike, libclang, macos-arm64, ci-workflow, trace-matrix, trc-01, phase-1-closure, ship-best-effort, d-22]

# Dependency graph
requires:
  - phase: 01-architecture-foundation-spec-correction
    provides: "Plans 01-09 (all prior closure plans) — Wave 1 (models 03/04/05) + Wave 2 (paths 06 / adapters 07 / docs 08) + Wave 2 close (layout 09); Plan 01 LICENSE + pyproject.toml that the CI workflow installs; Plan 02 spec doc whose §License + §Traceability are mirrored into docs/99"
provides:
  - "New sp3-libclang-spike job in .github/workflows/ci.yml — macos-14 runner, Python 3.13/3.14 matrix, continue-on-error: true, D-20 4-step verification (a) install / (b) Index.create() / (c) Config.library_path / (d) minimal C++ parse"
  - "Phase 1 14-REQ traceability matrix in docs/99-trace-matrix.md — every Phase 1 REQ-ID (ARC-01..05, SCH-01..03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01) maps to its US-IDs (US-01/US-22/US-25/US-32) + the Phase 1 closure plan that delivered it"
  - "SP-3 spike record at .planning/spikes/SP-3-libclang-macos-arm64.md with finalized verdict (ship-best-effort) — all (a)(b)(c)(d) PASS on Python 3.13 AND 3.14 on macos-14 (Apple Silicon arm64)"
  - "ROADMAP §Phase 1 Success Criterion 5 satisfied (D-22 緩和条件 fully met AND the strongest D-21 tier reached — workflow setup + first run kicked + verdict recorded as ship-best-effort)"
  - "TRC-01 closed: 14 Phase 1 REQ rows present in docs/99-trace-matrix.md (per-row US-ID + closure-plan reference)"
affects:
  - "Phase 4 (LNG-01 C++ frontend matrix CI + LNG-02 libclang dependency choice) — spike verdict ship-best-effort means Phase 4 can proceed with libclang==18.1.1 on macOS arm64 without fallback investigation; the sp3-libclang-spike job graduates from continue-on-error to a mandatory matrix entry"
  - "Phase 2/3/5 plan-phase — TRC-01 matrix in docs/99 is the canonical Phase 1 traceability anchor; later phases append their own H2 sections without rewriting the Phase 1 table"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Best-effort CI matrix entry: macos-14 runner + 2-version Python matrix + continue-on-error: true at the JOB LEVEL — does not block PR merges but produces a recorded verdict via $GITHUB_STEP_SUMMARY. This is the Phase 1 contract for the SP-3 spike per D-18/D-19/D-22 and remains the template Phase 4 LNG-01 will copy when graduating to mandatory"
    - "Spike record D-23 template: 6-H2-section schema (目的 / Test matrix / Verdict legend (D-21) / CI run URL / Re-evaluation / Provisional verdict) + YAML frontmatter status enum (pending-first-run / verdict-recorded-ship-best-effort / verdict-recorded-with-limitations / verdict-recorded-defer-v0.3.0) — Phase 4 plan-phase re-uses this schema when re-running the spike for LNG-02 graduation"
    - "Trace matrix structure: phase-scoped H2 (`## Phase 1 — Architecture Foundation + Spec Correction (TRC-01)`) holding a Requirement | US support | Phase 1 closure plan table; later phases append parallel H2 sections so the file grows additively without invalidating the Phase 1 anchor"

key-files:
  created:
    - ".planning/spikes/SP-3-libclang-macos-arm64.md"
  modified:
    - ".github/workflows/ci.yml"
    - "docs/99-trace-matrix.md"
    - ".planning/spikes/SP-3-libclang-macos-arm64.md"  # Task 4 fills verdict cells, CI URL, provisional verdict, frontmatter status — same file as the Task 1 scaffold

key-decisions:
  - "D-21 tier applied: ship-best-effort (all (a)(b)(c)(d) PASS on both Python 3.13 AND 3.14 on macos-14). This is the strongest of the 4 D-21 tiers and means Phase 4 LNG-02 inherits no known limitations, no version fallback, and no deferral."
  - "Two consecutive green CI runs across two commits (re-run 26406202099 on hot-fixed 69c952e; confirming run 26406392965 on Wave 3 base 0afdb7d) used as the stability evidence — the verdict is not a single-run fluke."
  - "Phase 1 hot-fix acknowledgment: the first SP-3 run on the original 69c952e commit failed at the pip install step because lib-diagram-parser>=0.1.0 (declared as a hard dep by Plan 01-01) is not yet on PyPI. The orchestrator hot-fixed this out-of-band in commit 53688ca (`fix(01-01): remove lib-diagram-parser from hard deps`) per Plan 01-05 OQ#5 + Plan 01-10 D-22 scope. The recorded verdict reflects the post-fix CI run."

patterns-established:
  - "Spike verdict resolution via re-run after dep hot-fix: when a CI run fails for a reason unrelated to the spike's stated verification target (here: a sibling lib's missing PyPI release blocking pip install before SP-3 (b)(c)(d) could run), the correct response is (a) hot-fix the dep, (b) re-trigger the workflow, (c) record the verdict from the re-run. Spike verdicts must reflect the spike's own assertions, not unrelated infra failures."
  - "Continuation-agent worktree pattern for sequential Wave 3 close: orchestrator merges Tasks 1+2 from a prior executor worktree into master, applies any hot-fixes, then spawns a fresh continuation agent off the post-fix base to complete Tasks 3+4 + SUMMARY. The continuation agent does not re-do completed work; it picks up at the checkpoint with the verdict in hand."

requirements-completed: [TRC-01]

# Metrics
duration: ~15min
completed: 2026-05-25
---

# Phase 01 Plan 10: SP-3 Spike + Trace Matrix Summary

**Phase 1 closure: SP-3 libclang spike verdict recorded as ship-best-effort (all 4 D-21 verification steps PASS on macos-14 with Python 3.13 AND 3.14, stable across 2 consecutive CI runs), and TRC-01 finalized with the Phase 1 14-REQ traceability matrix in docs/99.**

## Performance

- **Duration:** ~15 min (continuation agent — Tasks 1+2 + orchestrator hot-fix happened in prior worktree session)
- **Started (continuation agent):** 2026-05-25 (after orchestrator hot-fix commit 53688ca and re-run 26406202099 produced the verdict)
- **Completed:** 2026-05-25
- **Tasks:** 4 (Tasks 1+2 + Task 3 checkpoint + Task 4)
- **Files modified (this plan, all waves):** 3 (.github/workflows/ci.yml + docs/99-trace-matrix.md + .planning/spikes/SP-3-libclang-macos-arm64.md)
- **Files created (this plan):** 1 (.planning/spikes/SP-3-libclang-macos-arm64.md)

## Accomplishments

- **ROADMAP §Phase 1 Success Criterion 5 satisfied — strongest tier reached:** SP-3 libclang feasibility spike result is recorded under `.planning/spikes/SP-3-libclang-macos-arm64.md` with verdict **ship-best-effort** (D-21 tier 1 of 4: all (a)(b)(c)(d) PASS on both Python versions). D-22 緩和条件 required only "workflow setup complete + first run kicked + provisional verdict recorded" — Phase 1 not only met the relaxation but actually achieved the strongest possible verdict, so Phase 4 LNG-02 can proceed with `libclang==18.1.1` on macOS arm64 without further investigation, fallback, or deferral.
- **TRC-01 closed:** `docs/99-trace-matrix.md` contains a `## Phase 1 — Architecture Foundation + Spec Correction (TRC-01)` H2 section with all 14 Phase 1 REQ rows (ARC-01..05, SCH-01..03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01), each mapped to its US-IDs (US-01/US-22/US-25/US-32 per row) and the Phase 1 closure plan that delivered it.
- **Sp3 spike CI workflow operational and stable across 2 commits:** `.github/workflows/ci.yml` has a new `sp3-libclang-spike` sibling job (macos-14, python 3.13/3.14, continue-on-error: true) running 4 verification steps SP-3 (a)(b)(c)(d) per D-20/D-21. The existing `test` job (ubuntu-latest, python 3.11) is preserved verbatim and continues to gate PR merges. Two consecutive runs (`26406202099` on the hot-fixed re-run, `26406392965` on the Wave 3 base commit `0afdb7d`) both show all 3 jobs green.
- **Phase 1 close gate ALL 5 ROADMAP success criteria satisfied:** SC-1 (Plans 03+05+09), SC-2 (Plan 03), SC-3 (Plans 06+09), SC-4 (Plan 07), SC-5 (Plans 01+02+10 — this plan completes SC-5). Phase 1 is ready to transition to Phase 2.

## Task Commits

Each task was committed atomically per the Wave 3 sequential closer execution model. Tasks 1+2 happened in a prior executor worktree (commits `83f0d0a` and `6cce4a1`); the orchestrator hot-fixed an unrelated Plan 01-01 dep declaration (commit `53688ca`) and re-triggered CI; Task 4 happened in this continuation agent's worktree (commit `ead3456`):

1. **Task 1: Add sp3-libclang-spike job to .github/workflows/ci.yml + create spike doc scaffold** — `83f0d0a` (feat)
   - Appends the new sibling job to ci.yml with the exact YAML pinned in `.planning/phases/01-.../01-RESEARCH.md` §libclang 18.1.1 macOS arm64 (macos-14 runner, `strategy: fail-fast: false; matrix: python-version: ["3.13", "3.14"]`, `continue-on-error: true` at the job level, `actions/setup-python@v5` with `allow-prereleases: true` for 3.14, 4 verification steps SP-3 (a)(b)(c)(d) per D-20/D-21, plus an `if: always()` Record-verdict step writing to `$GITHUB_STEP_SUMMARY`).
   - Preserves the original `test` job (ubuntu-latest + python 3.11 + pytest + ruff) verbatim — merge gating intact.
   - Creates `.planning/spikes/SP-3-libclang-macos-arm64.md` per D-23 template (frontmatter `status: pending-first-run`, 6 H2 sections, verdict legend with all 4 D-21 tiers, placeholder `?` matrix cells, TBD CI URL).
2. **Task 2: Update docs/99-trace-matrix.md with Phase 1 14-REQ traceability matrix** — `6cce4a1` (docs)
   - Adds a `## Phase 1 — Architecture Foundation + Spec Correction (TRC-01)` H2 section with the 14-row table mapping each Phase 1 REQ-ID to its US support and the Phase 1 closure plan.
   - Preserves the existing file structure (no other Phase rows touched).
3. **Task 3: Verify SP-3 spike first CI run (checkpoint:human-verify)** — orchestrator-side gate (no commit needed):
   - First run on commit `69c952e` failed at pip install (NOT at SP-3 (a)(b)(c)(d)) because `lib-diagram-parser>=0.1.0` (Plan 01-01 hard dep) is not on PyPI.
   - Orchestrator hot-fixed via commit `53688ca` (`fix(01-01): remove lib-diagram-parser from hard deps (defer to Phase 3 DIA-04)`) per Plan 01-05 OQ#5 + Plan 01-10 D-22 scope.
   - Re-triggered run `26406202099` completed all 4 SP-3 steps PASS on both Python 3.13 (job `77730010113`, 21s) and 3.14 (job `77730010138`, 17s).
   - Confirming run `26406392965` on commit `0afdb7d` (Wave 3 base = continuation agent's spawn base) also all-green for all 3 jobs.
   - Verdict report passed to the continuation agent: **3.13 ✓✓✓✓ / 3.14 ✓✓✓✓ / URL: https://github.com/bibi-meow/lib-code-parser/actions/runs/26406202099**
4. **Task 4: Record provisional verdict in spike doc (post-checkpoint)** — `ead3456` (docs)
   - Applies Branch A of Plan 10 Task 4 `<action>` (all (a)(b)(c)(d) PASS → ship-best-effort).
   - Updates spike-doc frontmatter `status: pending-first-run` → `status: verdict-recorded-ship-best-effort`.
   - Fills the 2-row × 6-column test matrix with ✓ + verdict cells per row.
   - Adds a "Per-step CI evidence" subsection with the actual log strings (`Index OK <object>`, `library_path` values, `parsed 1 top-level cursors`) and job IDs (77730010113 / 77730010138).
   - Replaces the CI run URL "TBD" with the verdict-source run URL plus a background note explaining the orchestrator's lib-diagram-parser hot-fix and the confirming run on the Wave 3 base.
   - Replaces the Provisional verdict "TBD" section with the ship-best-effort statement, D-21 tier rationale, Phase 4 LNG-02 implication, and stability evidence pointing at two consecutive green runs across two commits.
   - Adds "Last updated by Plan 10 Task 4 on 2026-05-25" stamp at the bottom.

**Plan metadata commit:** to follow this SUMMARY (the orchestrator owns STATE.md and ROADMAP.md writes — this continuation agent only commits the spike-doc update and the SUMMARY itself).

## Files Created/Modified

### Created

- `.planning/spikes/SP-3-libclang-macos-arm64.md` — D-23 template spike record. Initially created in Task 1 with `status: pending-first-run` and placeholder `?` matrix cells; Task 4 (this continuation agent) filled the verdict cells, CI URL, provisional verdict section, and status frontmatter to reflect the actual CI run outcome.

### Modified

- `.github/workflows/ci.yml` — Task 1 appended the `sp3-libclang-spike` job as a sibling to the existing `test` job. The original `test` job (ubuntu-latest, python 3.11, pytest + ruff) is preserved verbatim. The new job: `runs-on: macos-14` + matrix `["3.13", "3.14"]` + `continue-on-error: true` at job level + 4-step verification + `Record verdict` summary step.
- `docs/99-trace-matrix.md` — Task 2 added the `## Phase 1 — Architecture Foundation + Spec Correction (TRC-01)` H2 section with the 14-row REQ table. Pre-existing structure (the design-doc §7 Step 15 traceability skeleton) preserved above the new section.

## Decisions Made

- **Branch A of Plan 10 Task 4 selected (verdict recorded, not deferred):** Because the user's resume-signal returned actual (a)(b)(c)(d) results for both Python versions (all ✓) plus a CI run URL, Task 4 followed Branch A: update matrix cells, fill CI URL, write provisional verdict per the matching D-21 tier, and update frontmatter status. Branch B ("spike not yet kicked") was not applicable.
- **D-21 ship-best-effort tier (not ship-best-effort-with-limitations):** All four steps (a)(b)(c)(d) PASS on BOTH Python versions on macos-14 — including step (d), which is the most demanding (actual C++ parse via `idx.parse(...)` returning a non-empty cursor list). Per D-21, "all (a)(b)(c)(d) ✓ → ship-best-effort" is the strongest tier; no "with known limitations" qualifier is needed because no limitation was observed.
- **Two-commit stability evidence cited in the spike doc:** Rather than rely on a single run, the spike doc explicitly cites two consecutive all-green CI runs (`26406202099` on the hot-fixed re-run of `69c952e`, and `26406392965` on Wave 3 base `0afdb7d`) — this defends the verdict against the "single-run fluke" criticism a Phase 4 reviewer might raise.
- **Phase 1 hot-fix explicitly documented in spike doc and SUMMARY:** The fact that the first run on `69c952e` failed for a Plan 01-01 dep-declaration reason (NOT for any libclang/SP-3-step reason) is recorded in the spike doc's "Background note (Phase 1 hot-fix)" subsection and in this SUMMARY's Decisions and Issues sections. A future reader scanning CI history would otherwise see the failed run and misattribute it to libclang itself.

## Deviations from Plan

### Auto-fixed Issues

**1. [Cross-plan dep hot-fix — orchestrator-applied, not this executor] `lib-diagram-parser>=0.1.0` hard dep declared in Plan 01-01 blocked the first SP-3 CI run before SP-3 steps could execute**

- **Found during:** Task 3 checkpoint (orchestrator observed the first CI run on commit `69c952e` failed at the `pip install -e ".[dev]"` step inside the sp3-libclang-spike job — not at any SP-3 verification step).
- **Issue:** Plan 01-01 (`pyproject.toml`) declared `lib-diagram-parser>=0.1.0` as a hard dependency to satisfy Phase 1 SC-1's `from lib_code_parser.models.evaluations import GraphModel` chain. However, `lib-diagram-parser` is not yet released on PyPI — `pip install` therefore failed with `Could not find a version that satisfies the requirement lib-diagram-parser>=0.1.0`. This blocked the SP-3 spike job from reaching steps (a)(b)(c)(d) on the first run.
- **Why this is a Plan 01-10 deviation entry even though it touched Plan 01-01:** The SP-3 spike verdict was directly blocked by it; recording the verdict (Task 4's responsibility) requires the spike to actually run; therefore the hot-fix is part of the chain Plan 10 depends on. Per Plan 01-05's pre-resolved OQ#5 (Phase 1 graph_base.py is self-contained — `lib-diagram-parser` import is not actually needed in Phase 1) and Plan 01-10's D-22 scope (Phase 1 close on workflow setup + first run kick + provisional verdict — not blocked by transitive dep failures), removing the hard dep is the correct fix.
- **Fix (applied by orchestrator, not this executor):** Commit `53688ca` `fix(01-01): remove lib-diagram-parser from hard deps (defer to Phase 3 DIA-04)` removed `lib-diagram-parser>=0.1.0` from `pyproject.toml` `[project.dependencies]`. Phase 3 (DIA-04) will revisit when the dep is actually needed at runtime.
- **Verification:** Re-triggered CI run `26406202099` and confirming run `26406392965` on the Wave 3 base `0afdb7d` both show all 3 jobs green (test + sp3-libclang-spike Python 3.13 + sp3-libclang-spike Python 3.14). The SP-3 (a) "install" step now succeeds, unblocking (b)(c)(d).
- **Committed in:** `53688ca` (orchestrator out-of-band, prior to spawning this continuation agent). Documented here so Plan 10's SUMMARY accurately reflects what enabled Task 4's verdict.

**2. [Continuation-agent worktree convention] Tasks 1 + 2 were committed in a prior executor worktree (commits `83f0d0a` and `6cce4a1`), then merged to master in commit `69c952e` before this continuation agent spawned**

- **Found during:** Continuation agent startup (HEAD assertion + base-merge check).
- **Issue:** Not actually a deviation — this is the expected continuation-agent convention. The orchestrator merges the prior executor worktree's commits into master before spawning the continuation agent off the post-merge base. Documented here for SUMMARY completeness because the commit hashes in `## Task Commits` above refer to the pre-merge worktree commits (`83f0d0a` / `6cce4a1`), not to the merge commit (`69c952e`).
- **Fix:** None needed. The pre-merge commit hashes ARE the canonical task commits (their full diffs are reachable on master because the merge commit is non-squashing). `git log --oneline 0afdb7d` confirms both Task 1 and Task 2 commits are reachable from the Wave 3 base.

---

**Total deviations:** 1 cross-plan hot-fix (orchestrator-applied, documented for traceability) + 1 procedural note (continuation-agent convention, not a real deviation).
**Impact on plan:** The hot-fix was required to make the SP-3 spike actually run; without it, Task 4 could only record the "spike not yet kicked" Branch B outcome (still satisfies D-22 for Phase 1 close, but loses the chance to record the strongest D-21 tier). The post-fix re-run delivered the strongest possible verdict, so Phase 1 closes with `ship-best-effort` recorded — the best possible Phase 1 outcome for SC-5.

## Issues Encountered

- **First SP-3 CI run on `69c952e` failed at pip install (not at SP-3 steps):** Root cause was Plan 01-01's `lib-diagram-parser>=0.1.0` hard dep blocking the install of `pyproject.toml [project.dependencies]` before the SP-3 verification steps could begin. Resolved by orchestrator hot-fix commit `53688ca`. See Deviation #1 above.

No other issues — Tasks 1 + 2 in the prior executor worktree passed all acceptance criteria verbatim against the plan; Task 4 in this continuation agent's worktree applied Branch A as designed.

## TDD Gate Compliance

Plan 10 marks all 4 tasks as `tdd="false"` (workflow-config + docs + checkpoint + verdict-record — none are behavior-adding source-code tasks). Per the plan-level TDD gate rules in `<tdd_execution>`, this plan is therefore exempt from RED/GREEN/REFACTOR gating. The MVP+TDD runtime gate (`references/execute-mvp-tdd.md`) was not invoked for any task because the behavior-adding predicate `task.is-behavior-adding` returns false on all four (no `<behavior>` blocks; no non-test source files in `<files>`).

## Verification

| Check | Required | Result |
|---|---|---|
| `.github/workflows/ci.yml` contains sp3-libclang-spike job | YES | YES (`grep -c "sp3-libclang-spike:" .github/workflows/ci.yml` → 1) |
| Existing `test` job preserved in ci.yml | YES | YES (`grep "name: test" .github/workflows/ci.yml` → present at line 7) |
| Spike doc exists at `.planning/spikes/SP-3-libclang-macos-arm64.md` | YES | YES |
| Spike doc frontmatter status post-Task-4 | one of 4 verdict-recorded-* values OR pending-first-run | `verdict-recorded-ship-best-effort` ✓ |
| Spike doc Provisional verdict section non-placeholder | YES | YES (ship-best-effort statement + D-21 tier rationale + LNG-02 implication + stability evidence) |
| Spike doc test matrix rows filled (no `?` in 3.13/3.14 rows) | YES (Branch A) | YES (all 8 cells ✓ across the 2 rows) |
| Spike doc CI run URL filled (no "TBD") | YES (Branch A) | YES (`https://github.com/bibi-meow/lib-code-parser/actions/runs/26406202099` + confirming run `26406392965`) |
| Spike doc date stamp "Last updated by Plan 10 Task 4 on 2026-05-25" | present | present (1 occurrence) |
| `docs/99-trace-matrix.md` contains Phase 1 H2 section | YES | YES (`grep -c "^## Phase 1" docs/99-trace-matrix.md` → 1) |
| All 14 Phase 1 REQ-IDs appear as table rows | 0 MISSING_ROW | 0 (`ARC-01..05`, `SCH-01..03`, `DET-04`, `DET-05`, `DOC-01`, `DOC-03`, `DOC-04`, `TRC-01` — all 14 present) |
| CI verdict matches D-21 ship-best-effort tier criteria | all (a)(b)(c)(d) ✓ on both Python versions | YES (3.13 job 77730010113 + 3.14 job 77730010138 — all 4 steps PASS in each) |
| CI verdict reproducibility | >= 2 consecutive green runs | YES (run `26406202099` + run `26406392965`) |
| Task 4 commit landed | YES | YES (`ead3456` `docs(01-10): record SP-3 spike verdict — ship-best-effort on macOS arm64`) |

## Threat Surface Scan

No new threat surface introduced beyond Plan 10's `<threat_model>` enumeration. The five registered threats are mitigated as planned:

| Threat | Disposition | How addressed | Evidence |
|---|---|---|---|
| T-10-01 Invalid YAML breaks `test` job | mitigate | Plan 10 Task 1's `<verify><automated>` ran `grep` structural checks against ci.yml; both subsequent CI runs (`26406202099`, `26406392965`) confirm the `test` job continues to be parseable and runnable | Two green `test` jobs in two consecutive runs |
| T-10-02 sp3-libclang-spike runs unboundedly long | mitigate | Both matrix runs completed in <25s (3.13: 21s, 3.14: 17s); GitHub Actions 6h job timeout + `continue-on-error: true` cap exposure | Job durations in run `26406202099` |
| T-10-03 libclang 18.1.1 wheel poisoned in PyPI | accept | Per Plan 10 plan: SHA256 pinning is a Phase 5 hardening deliverable; current `libclang==18.1.1` pin + PyPI integrity is the working baseline; RESEARCH.md §Package Legitimacy Audit slopcheck [OK] | n/a (accepted risk) |
| T-10-04 User misreports a/b/c/d verdict in Task 3 | mitigate | CI run URL (`26406202099`) recorded in spike doc; per-step CI evidence subsection in spike doc cites actual log strings (`Index OK <object>`, `library_path` value, `parsed N top-level cursors`) and job IDs — re-reading the doc against the run logs lets a future reviewer reconcile | Spike doc "Per-step CI evidence" subsection |
| T-10-SC Supply chain (pip installs in CI) | mitigate | RESEARCH.md §Package Legitimacy Audit slopcheck [OK] on all dev extras (libclang==18.1.1 + pyright[nodejs]==1.1.409 + nodejs-wheel-binaries); pyproject.toml pins exact versions; no `[ASSUMED]` or `[SUS]` packages | RESEARCH.md audit + post-hot-fix CI installs succeed |

No threat flags introduced — the new files (spike doc) and modified files (ci.yml, docs/99) are all internal planning/CI artifacts, not network endpoints, auth paths, or schema changes at trust boundaries.

## Known Stubs

None. The SP-3 spike record's Provisional Verdict section is no longer a stub — it carries a concrete ship-best-effort verdict with D-21 tier rationale, LNG-02 implication, and stability evidence. The test matrix cells are all filled (no `?` remains in the 3.13/3.14 rows). The CI URL is concrete (not "TBD"). The frontmatter status is concrete (`verdict-recorded-ship-best-effort`, not `pending-first-run`).

The `## Re-evaluation` section retains a Phase-4-entry-point instruction ("If verdict was provisional or defer, plan-phase for Phase 4 re-runs the spike") — that's a forward-looking guidance, not a stub. Phase 4 will re-run the spike anyway as part of LNG-01 mandatory matrix graduation, regardless of verdict.

## User Setup Required

None at this stage. Plan 10 originally listed a `user_setup` entry for "Push the Phase 1 commit; observe the first sp3-libclang-spike job run on GitHub Actions" — this was already satisfied during the Task 3 checkpoint (the orchestrator pushed the commit, observed the first run, applied the hot-fix to commit `53688ca`, observed the re-run `26406202099` and confirming run `26406392965`, and passed the verdict to this continuation agent). No further user setup is required for Phase 1 close; Phase 4 LNG-01 will re-enter user_setup territory when graduating the sp3-libclang-spike job to a mandatory matrix.

## Next Phase Readiness

- **ROADMAP §Phase 1 close gate: all 5 success criteria satisfied** (SC-1 by Plans 03+05+09; SC-2 by Plan 03; SC-3 by Plans 06+09; SC-4 by Plan 07; SC-5 by Plans 01+02+10 — this plan completes SC-5). Phase 1 is ready to transition to Phase 2.
- **Phase 2 (extractor rewrite + dispatch-driven executor) entry prerequisites:** All Plan 09 deliverables (nested layout migration + v0.1.0→v0.2.0 parity gate) are in master; the `lib_code_parser/extractors/primitives/` placeholder package is ready for Phase 2's frontend (`python`) and 4 primitive entries (`functions`, `call_graph`, `type_deps`, `contracts`).
- **Phase 4 (C++ frontend) confidence boost from SP-3 ship-best-effort verdict:** Because the verdict is the strongest D-21 tier (not "with known limitations" and not "defer to v0.3.0"), Phase 4 LNG-02 can commit to `libclang==18.1.1` on macOS arm64 + Python 3.13/3.14 without budget reserved for a fallback library or a deferral plan. The sp3-libclang-spike CI job graduates from `continue-on-error: true` to a mandatory matrix entry as part of LNG-01.
- **Cross-phase traceability anchor:** `docs/99-trace-matrix.md` Phase 1 H2 section is the canonical reference Phase 2-5 plan-phase will append parallel H2 sections to; the file structure is now stable and additive.
- **Blockers/concerns:** None for Phase 2 entry. The orchestrator's lib-diagram-parser hot-fix (commit `53688ca`) means Phase 1 pyproject.toml `[project.dependencies]` no longer declares `lib-diagram-parser>=0.1.0`; Phase 3 (DIA-04) will revisit the dep declaration when the import is actually needed at runtime.

## Self-Check: PASSED

Verified before SUMMARY commit:

**Files modified by this plan (existence verified via `[ -f path ]`):**
- `.github/workflows/ci.yml` — FOUND (modified by Task 1, base commit `83f0d0a` → reachable from Wave 3 base `0afdb7d`)
- `docs/99-trace-matrix.md` — FOUND (modified by Task 2, base commit `6cce4a1` → reachable from Wave 3 base `0afdb7d`)
- `.planning/spikes/SP-3-libclang-macos-arm64.md` — FOUND (created by Task 1, finalized by Task 4 commit `ead3456`)

**Commits exist (verified via `git log --oneline`):**
- `83f0d0a` (Task 1: feat) — FOUND on master (reachable from Wave 3 base)
- `6cce4a1` (Task 2: docs) — FOUND on master (reachable from Wave 3 base)
- `ead3456` (Task 4: docs) — FOUND on this continuation agent's worktree branch `worktree-agent-a1ee5abda7c11fed9`

**Spike-doc content verification:**
- `grep "^status:" .planning/spikes/SP-3-libclang-macos-arm64.md` → `status: verdict-recorded-ship-best-effort` ✓
- `grep -c "Provisional verdict: ship-best-effort" .planning/spikes/SP-3-libclang-macos-arm64.md` → 1 ✓
- `grep -c "26406202099" .planning/spikes/SP-3-libclang-macos-arm64.md` → 4 (CI URL section + provisional verdict section + per-step evidence header + stability evidence) ✓
- `grep -c "Last updated by Plan 10 Task 4 on 2026-05-25" .planning/spikes/SP-3-libclang-macos-arm64.md` → 1 ✓
- `grep -E "^\| 3\.(13|14) \|" .planning/spikes/SP-3-libclang-macos-arm64.md` → both rows show `✓ | ✓ | ✓ | ✓ | ship-best-effort` ✓

**CI run verdict reconciliation:**
- Verdict source run `26406202099`: 3 jobs, all green (test + sp3-libclang-spike Python 3.13 + sp3-libclang-spike Python 3.14). 4 SP-3 steps PASS in each spike-job matrix entry. Per-step log strings (`Index OK <object>`, `library_path` paths, `parsed 1 top-level cursors`) preserved in spike doc.
- Confirming run `26406392965`: same 3 jobs, all green on Wave 3 base commit `0afdb7d`.

**Trace matrix verification:**
- `grep -c "^## Phase 1" docs/99-trace-matrix.md` → 1 ✓
- Loop check for all 14 Phase 1 REQ-IDs (`for id in ARC-01 ... TRC-01; do grep -q "| $id |" docs/99-trace-matrix.md || echo MISSING_ROW; done | grep -c MISSING_ROW`) → 0 ✓

**Plan acceptance hard gates:**
- ROADMAP §Phase 1 SC-5 satisfied — SP-3 verdict recorded as ship-best-effort (strongest D-21 tier) ✓
- TRC-01 closed — 14 Phase 1 REQ rows in docs/99 with US-IDs + closure-plan references ✓
- D-22 緩和条件 satisfied AND exceeded (verdict is not "pending-first-run" but ship-best-effort) ✓

---
*Phase: 01-architecture-foundation-spec-correction*
*Plan: 10 — SP-3 spike + Phase 1 14-REQ trace matrix*
*Completed: 2026-05-25*
