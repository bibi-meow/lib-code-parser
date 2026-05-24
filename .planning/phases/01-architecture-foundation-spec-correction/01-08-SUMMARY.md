---
phase: 01-architecture-foundation-spec-correction
plan: 08
subsystem: docs
tags: [cav, normalized-artifact, pydantic-generic, edgekind, open-closed, dispatch-dict, sdd-chain]

# Dependency graph
requires:
  - phase: 01-architecture-foundation-spec-correction
    provides: D-04..D-09 (CAV polymorphism), D-13 (6 Open-Closed invariants), D-14 (layer purity), Pitfall 7 (EdgeKind ad-hoc growth ban), pre-resolved Open Question #4 (append-only enforced via code review)
provides:
  - docs/08-common-view-pattern.md (CAV envelope + NormalizedArtifact[TContent] Generic + caller-agnostic I/O + sibling-lib adoption recipe)
  - docs/09-extending.md (6 Open-Closed invariants verbatim + EdgeKind MAJOR-version policy + dispatch entry-addition recipe + DDD reverse extension scenario)
affects:
  - 01-02-spec-doc-rewrite (forward-references docs/08 from lib-code-parser.md §採用アルゴリズム)
  - 01-03-models-infrastructure (CAV / NormalizedArtifact code substrate that docs/08 documents)
  - 01-06-paths-and-dispatch (_dispatch.py module docstring back-links to docs/09)
  - Phase 2-4 contributors (consult docs/09 when adding new extractors)
  - future v0.3.0+ DDD-reverse milestone (docs/09 §拡張シナリオ例 forward-references this)

# Tech tracking
tech-stack:
  added: []  # docs-only plan, no code dependencies added
  patterns:
    - Common AST View (CAV) single-parse envelope pattern
    - Pydantic v2 Generic envelope (NormalizedArtifact[TContent]) with byte-identical JSON parity
    - 6 Open-Closed invariants for dispatch-dict-driven extractor composition
    - EdgeKind closed Literal with MAJOR-version-bump policy (Pitfall 7 prevention)
    - Code-review-only enforcement of append-only invariant (no hook/lint automation in Phase 1)

key-files:
  created:
    - docs/08-common-view-pattern.md
    - docs/09-extending.md
  modified: []

key-decisions:
  - "docs/08-common-view-pattern.md ships on SDD-chain numbering 08-, closed to lib-code-parser; workspace-common doc is Deferred until 2+ sibling libs adopt the pattern (per D-07)"
  - "docs/09-extending.md enumerates the 6 Open-Closed invariants verbatim from D-13 (existing primitive/evaluation immutability, CodeContent optional fields, dispatch dict append-only, pull-based primitive supply, executor scan-only)"
  - "Layer purity rule (D-14): only models/evaluations/ is verifier-facing; EdgeKind strict Literal applies only there; primitives/infrastructure remain free-form to preserve representation breadth"
  - "EdgeKind addition policy: ad-hoc catch-all (uses/other/misc) prohibited; new EdgeKind value requires (a) issue justifying why none of 11 fit, (b) MAJOR version bump, (c) sibling-lib coordination. Undecidable composition vs aggregation falls back to explicit 'associates' enum value"
  - "Append-only invariant on dispatch dicts is enforced via code review (per pre-resolved Open Question #4); hook/lint automation is explicitly NOT shipped in Phase 1"

patterns-established:
  - "Common AST View (CAV) pattern: Pydantic BaseModel with Literal language discriminator + opaque payload + frozen=True + arbitrary_types_allowed=True + extra=forbid"
  - "Generic envelope pattern: NormalizedArtifact[TContent] with TypeVar bound=BaseModel, preserving byte-identical JSON between unparameterized (v0.1.0 caller) and parameterized (v0.2.0 typed caller) construction"
  - "Open-Closed extension pattern: new file + 1 line in _dispatch.py + optional field on CodeContent; zero touch on existing files (executor, existing primitives, existing evaluations)"
  - "Code-review-only enforcement pattern for invariants that lint/hook cannot statically verify (Phase 1 baseline)"

requirements-completed: [ARC-04, DET-04]

# Metrics
duration: 25min
completed: 2026-05-24
---

# Phase 01 Plan 08: docs/08-common-view-pattern.md + docs/09-extending.md Summary

**Authoritative SDD-chain docs codifying the CAV/NormalizedArtifact Generic envelope pattern and the 6 Open-Closed invariants (with EdgeKind MAJOR-version policy and code-review-only append-only enforcement) for Phase 2-4 contributors.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-24T22:53:50Z (approx, from worktree spawn)
- **Completed:** 2026-05-24T23:18:50Z
- **Tasks:** 2
- **Files modified:** 2 (created)

## Accomplishments

- `docs/08-common-view-pattern.md` (219 lines, 10.6 KB) — Documents the Common View pattern with 6 H2 sections (目的, CAV, NormalizedArtifact[TContent] Generic 化, I/O variability caller-agnostic, 兄弟 lib 採用ガイド, Traceability) including ConfigDict flag rationale, byte-identical JSON parity example, and a 4-step sibling-lib adoption recipe marked as Phase 1 NOT-shipped.
- `docs/09-extending.md` (377 lines, 19.6 KB) — Documents the extension contract with 7 H2 sections including the 6 Open-Closed invariants verbatim from D-13, layer purity rule (D-14), EdgeKind MAJOR-version policy (Pitfall 7 prevention with `"associates"` as the explicit undecidable fallback), dispatch entry-addition recipe (Frontend / Primitive / Evaluation), and DDD-reverse extension scenario showing all 6 invariants hold.
- Both docs use the existing SDD-chain numbering and Japanese prose style of `docs/06-architecture.md`.
- Forward-references from docs/09 → `_dispatch.py` docstring (to be wired in Plan 06) and from docs/08 → `lib-code-parser.md` §採用アルゴリズム (to be written in Plan 02) are documented in the Traceability sections.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write docs/08-common-view-pattern.md** — `70b8544` (docs)
2. **Task 2: Write docs/09-extending.md with 6 Open-Closed invariants** — `ddc83a5` (docs)

## Files Created/Modified

- `docs/08-common-view-pattern.md` — Created. CAV + NormalizedArtifact Generic + caller-agnostic I/O + sibling-lib adoption recipe. 6 H2 sections + Traceability tags (Traces: ARC-02, ARC-04, ARC-05).
- `docs/09-extending.md` — Created. 6 Open-Closed invariants verbatim from D-13 + D-14 layer purity rule + EdgeKind MAJOR-version policy + dispatch entry-addition recipe + DDD-reverse extension scenario + code-review-only enforcement model. 7 H2 sections + Traceability tags (Traces: ARC-01..05, SCH-01..03, DET-04).

## Decisions Made

None beyond the plan — all key decisions were pre-resolved in CONTEXT.md and 01-DISCUSSION-LOG.md. Doc structure, section ordering, and invariant content were locked by D-13 / D-14 / D-07; Claude exercised discretion only on prose style (sentence length, code-fence placement, anti-pattern examples) per `CONTEXT.md ## Claude's Discretion`.

## Deviations from Plan

None - plan executed exactly as written.

All acceptance criteria gates passed on first verification:

- docs/08-common-view-pattern.md: 6 H2 sections present (目的, CAV, NormalizedArtifact, I/O variability, 兄弟 lib, Traceability), `extra="forbid"` x6, `frozen=True` x3, `Generic[TContent]` x2, 219 lines, 10587 bytes, 1 `Traces:` tag.
- docs/09-extending.md: 7 H2 sections present, `append-only` x6, `EdgeKind` x15, `MAJOR` x6, `associates` x7, `code review` x4, `evaluations` x7, 377 lines, 19555 bytes, 1 `Traces:` tag. All `hook|lint` mentions (5 total) explicitly state that automation is NOT shipped in Phase 1 (manual review verified per acceptance gate).

## Issues Encountered

None.

## Self-Check: PASSED

- File existence: docs/08-common-view-pattern.md FOUND, docs/09-extending.md FOUND.
- Commit existence: 70b8544 FOUND, ddc83a5 FOUND on branch `worktree-agent-ace1a9eae58510fb6`.
- Threat model mitigations (T-08-01, T-08-02, T-08-03) all addressed: EdgeKind ad-hoc growth banned in docs/09 §"EdgeKind 追加は MAJOR version 案件" with `"associates"` documented as sanctioned fallback; dispatch dict overwrite addressed in docs/09 §"6 つの Open-Closed 不変条件" invariant #4 + §"dispatch dict への entry 追加手順" + (forward-link) `_dispatch.py` module docstring (Plan 06); verifier layer-boundary misinterpretation addressed in docs/09 §"論理アーキ比較対象は models/evaluations/ のみ (D-14)".

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02 (lib-code-parser.md spec doc rewrite) can now forward-reference `docs/08-common-view-pattern.md` from its §採用アルゴリズム as planned.
- Plan 06 (`_paths.py` + `_dispatch.py`) can now back-link from `_dispatch.py` module docstring to `docs/09-extending.md` §"dispatch dict への entry 追加手順" as planned in its acceptance criteria.
- Phase 2-4 contributors have an authoritative reference doc instead of needing to re-derive Open-Closed rules from CONTEXT.md.
- No blockers introduced. Both new docs are pure prose with no runtime dependencies.

---
*Phase: 01-architecture-foundation-spec-correction*
*Completed: 2026-05-24*
