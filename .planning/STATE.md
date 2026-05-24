# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-24)

**Core value:** コードから抽出する全アーキ表現が、`lib-diagram-parser` が spec から抽出するものと同形式・最大忠実度・決定論的に比較可能であること (Layer M bisimulation の物理側基盤)
**Current focus:** Phase 1 — Architecture Foundation + Spec Correction

## Current Position

Phase: 1 of 5 (Architecture Foundation + Spec Correction)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-05-24 — Roadmap created, 42/42 v1 requirements mapped, no orphans

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
- Trend: — (no data yet)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table (16 decisions as of 2026-05-24).

Recent decisions affecting current work:

- Phase 1: spec doc (`lib-code-parser.md`) must remove `callgraph.py` + "ACL-2" misreferences before any extractor code — internal call graph extractor + `pyright` are the real tools
- Phase 1: CAV (Common AST View) is the keystone — single parse per file, immutable Pydantic envelope, shared to all extractors; replaces v0.1.0 4× re-parse anti-pattern
- Phase 1: `EdgeKind` is a closed `Literal` enum locked in models layer — no "uses" / "other" catch-all; ad-hoc growth forbidden after Phase 1 close
- Phase 1: subprocess lives only in `adapters/` layer (no extractor may call `subprocess` directly); subprocess hardening (`LC_ALL=C`, `PYTHONHASHSEED=0`, `encoding="utf-8"`, explicit `timeout`/`cwd`) is enforced by `adapters/base.py`
- Phase 1: Apache-2.0 license declared with `LICENSE` file shipped; no GPL bundled (call graph internal, pyright MIT, libclang Apache-2.0+LLVM exception)
- Phase 3: `lib-diagram-parser` PR adding `node_type="package"` enum value is a sibling-lib coordination dependency (DIA-04 / SCH-01 require it)

### Pending Todos

None yet.

### Blockers/Concerns

- SP-3 spike (libclang `==18.1.1` on macOS arm64 + Python 3.13/3.14) result will determine whether macOS arm64 ships as best-effort or is deferred to v0.3.0 (impacts LNG-02 success in Phase 4)
- `lib-diagram-parser` sibling-lib PR for `node_type="package"` enum addition must be merged before Phase 3 closes (DIA-04 acceptance depends on it)

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none — first milestone)* | | | |

## Session Continuity

Last session: 2026-05-24
Stopped at: ROADMAP.md + STATE.md + REQUIREMENTS.md traceability written; ready for `/gsd:plan-phase 1`
Resume file: None
