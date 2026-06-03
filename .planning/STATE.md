---
gsd_state_version: 1.0
milestone: v0.1.0
milestone_name: milestone
status: executing
stopped_at: Completed 04-02-PLAN.md
last_updated: "2026-06-03T16:56:46.308Z"
last_activity: 2026-06-03
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 30
  completed_plans: 27
  percent: 60
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-02)

**Core value:** コードから抽出する全アーキ表現が、`lib-diagram-parser` が spec から抽出するものと同形式・最大忠実度・決定論的に比較可能であること (Layer M bisimulation の物理側基盤)
**Current focus:** Phase 04 — C++ Frontend + C++ Extractors

## Current Position

Phase: 04 (C++ Frontend + C++ Extractors) — EXECUTING
Plan: 4 of 7
Status: Ready to execute
Last activity: 2026-06-03

Progress: [█████████░] 90%

## Performance Metrics

**Velocity:**

- Total plans completed: 24
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 10 | - | - |
| 02 | 8 | - | - |
| 03 | 6 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: — (no data yet)

*Updated after each plan completion*
| Phase 02 P06 | 25 | 3 tasks | 8 files |
| Phase 02 P07 | 25 | 3 tasks | 20 files |
| Phase 03 P01 | 6 | 4 tasks | 11 files |
| Phase 03 P02 | 14 | 2 tasks | 15 files |
| Phase 03 P03 | 12 | 2 tasks | 10 files |
| Phase 03 P04 | 18 | 3 tasks | 12 files |
| Phase 03 P05 | 6min | 2 tasks | 8 files |
| Phase 03 P06 | 6min | 2 tasks | 10 files |
| Phase 04 P01 | 6 | 3 tasks | 5 files |
| Phase 04 P02 | 9min | 2 tasks | 8 files |
| Phase 04 P03 | 3min | 3 tasks | 4 files |

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
- [Phase ?]: Phase 2 Plan 06: executor rewritten as dispatch-dict walk (D-03) on typed ParserConfig; barrel ParserConfig graduation deferred to Plan 02-07
- [Phase ?]: Phase 3 Plan 01: D-01 sub-decision — add ONLY 'imports' to EdgeKind; DIA-04 package containment via GraphNode.attributes['parent_package'], not a 'contains' edge
- [Phase ?]: Phase 3 Plan 01: DIA-06 marker = GraphEdge.source_unresolved (source_ prefix); SPC-04 taxonomy in evaluations/spec.py (frozen contracts.py untouched); EVALUATIONS gating = run-all-registered
- Phase 3 Plan 02: DIA-04 package containment via GraphNode.attributes['parent_package'] confirmed sufficient — NO 'contains' EdgeKind added, graph_base.py untouched this plan; DIA-04 completed entirely in-lib (no sibling-lib PR dependency)
- Phase 3 Plan 02: DIA-01 known-class resolution is structural (module ClassDefs + imported class-like names); unknown annotation names → associates fallback, never a 'uses'/fabricated edge (T-03-03); Optional/X|None/container of known class → aggregates, direct known class → composes, builtins skipped
- Phase 3 Plan 02: D-03 edges keep this lib's own vocabulary (inherits/composes/aggregates/associates/imports), NOT renamed to sibling lib-diagram-parser spelling — verifier resolves the physical↔logical gap
- [Phase ?]: Phase 3 Plan 03: SP-2 verdict = SHIP (D-08) — sequence branch fidelity (alt/loop/par) is a deterministic pure-AST rule; ships in v0.2.0, DIA-02-FULL NOT created
- [Phase ?]: Phase 3 Plan 03: DIA-02 branch frames encoded on GraphEdge.label (alt/loop/par) — no new EdgeKind, edge_type stays 'calls'; label is part of the DET-04 sort key; deepest-frame-wins, awaited call always 'par'
- [Phase ?]: Phase 3 Plan 03: DIA-02 participants inherit Phase 2 callgraph representation verbatim; Phase 2 deferred CallGraph resolution expansion re-evaluated and NOT needed for linear correctness
- [Phase ?]: Phase 3 Plan 04: SP-1 verdict = DEFER (D-08) — general control-flow→state is NOT deterministic (state identity ambiguous without explicit state var; two valid rules disagree on same source); DIA-05-FULL deferred to v0.3.0, explicit FSM families ship regardless (D-07)
- [Phase ?]: Phase 3 Plan 04: DIA-06 unresolved marker = GraphEdge.source_unresolved; unresolvable mutation (external call / cycle dead-end / non-literal) emits exactly ONE placeholder edge
- [Phase ?]: Phase 3 Plan 04: FSM detection via import-provenance parameterized per target pkg — user's own Machine/State without import NOT detected (T-03-08); target libs detected by AST never imported (D-10)
- [Phase ?]: D-09 honored: SPC-01 docstring parsing is a stdlib-only internal state machine (Google/NumPy/Sphinx); zero external library, grep gate=0
- [Phase ?]: Three-dialect equivalence is the SPC-01 determinism contract: same function documented 3 ways -> byte-identical normalized output (golden fixture)
- [Phase ?]: function_spec registered append-only at canonical EVALUATIONS #6; parity snapshot regenerated (function_spec slot only)
- [Phase ?]: Phase 3 Plan 06: SPC-04 markers detection-only (D-10) via parameterized import-provenance over (icontract,deal); decoy require() not flagged (T-03-13); lambdas ast.unparse'd never executed (T-03-14)
- [Phase ?]: Phase 3 Plan 06: class_spec registered final EVALUATIONS #7; all 7 in canonical order; ClassSpec.invariants holds SPC-04 markers only (Phase-2 contracts stay in CodeContent.contracts; frozen contracts.py + shipped spec.py untouched)
- [Phase ?]: Phase 3 Plan 06: v01 parity snapshot regenerated (class_spec slot [] -> 2 ClassSpec for EXAMPLE_SOURCE); all other slots byte-identical
- [Phase ?]: Phase 4 Plan 01: D-01 — PRIMITIVES/EVALUATIONS nested dict[language, dict[name, fn]] = {python:{...}, cpp:{}}; Python values byte-unchanged under [python]; FRONTENDS stays flat (D-02, Pitfall 1)
- [Phase ?]: Phase 4 Plan 01: D-03 — executor indexes PRIMITIVES[cav.language]/EVALUATIONS[cav.language] (uses cav.language not local language); ONE-TIME exception to invariant #6, later cpp aspects are 0-line executor diff
- [Phase ?]: Phase 4 Plan 02: build_cpp_cav test-side libclang CAV builder (mirror of build_python_cav) added to conftest; parses -x c++ -std=c++17, unsaved_files, PARSE_INCOMPLETE, raw_content carried, no PARSE_DETAILED_PROCESSING_RECORD
- [Phase ?]: Phase 4 Plan 02: tests/fixtures/cpp/ corpus (7 fixtures, pure-ASCII, <30 lines, -std=c++17) covers D-04/D-05/D-08/D-09; missing_include.cpp mechanically demonstrates LNG-05 warn-not-error (diagnostic emitted, Ok cursor still built)
- [Phase ?]: Phase 4 Plan 03: frontends/cpp.py single libclang parse site; D-07 lazy _READY guard (DET-02 ABI pin via importlib.metadata.version no FFI, LNG-03 reject set_library_file + assert bundled clang/native, Index.create smoke test); build_cav -x c++ + compile_args + PARSE_INCOMPLETE (LNG-05 warn-not-error), in-process no adapters; FRONTENDS[cpp] registered flat

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

Last session: 2026-06-03T16:56:46.297Z
Stopped at: Completed 04-02-PLAN.md
Resume file: None
