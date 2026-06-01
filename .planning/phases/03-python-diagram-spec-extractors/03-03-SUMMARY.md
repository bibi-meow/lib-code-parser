---
phase: 03-python-diagram-spec-extractors
plan: 03
subsystem: diagram-extractors
tags: [evaluations, sequence-diagram, dia-02, sp-2-spike, branch-fidelity, det-04, dispatch, parity-snapshot]

# Dependency graph
requires:
  - phase: 03-python-diagram-spec-extractors
    plan: 01
    provides: "graph_base.py (GraphNode/GraphEdge/GraphModel + closed EdgeKind incl. 'calls'), CodeContent sequence_diagram slot, executor EVALUATIONS walk, DIA-07 assert_valid_graphmodel"
  - phase: 03-python-diagram-spec-extractors
    plan: 02
    provides: "EVALUATIONS canonical-order registration pattern (class_diagram #1), DET-04 sort-on-exit + dict.fromkeys dedup pattern, parity-snapshot regeneration discipline"
provides:
  - "SP-2 verdict = SHIP: sequence branch fidelity (alt/loop/par) IS a deterministic pure-AST rule; recorded in .planning/spikes/SP-2-sequence-branch-fidelity.md with the D-08 determinism rationale"
  - "DIA-02 sequence_diagram extractor — linear `calls` edges from callgraph (D-07 must-have) + SP-2 branch-frame labels (alt/loop/par) on GraphEdge.label (no schema change, no new EdgeKind)"
  - "EVALUATIONS sequence_diagram registration at canonical position #2 (after class_diagram, before component_diagram)"
  - "DIA-07 schema-conformance case feeding sequence output through assert_valid_graphmodel"
  - "regenerated v01 parity snapshot: sequence_diagram slot now populated for EXAMPLE_SOURCE (11 participants + 4 calls edges); all other slots byte-identical"
affects: ["03-04 FSM/state diagram", "03-05 function/class spec", "03-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Spike-as-determinism-probe: a self-contained pure-function test (no production import) proves byte-identical output across repeated runs + PYTHONHASHSEED; the SOLE D-08 ship-vs-defer criterion"
    - "Branch-frame encoding on GraphEdge.label: alt/loop/par Mermaid frames carried in the existing label field — zero schema change, label is already part of the DET-04 composite sort key"
    - "Frame-walk mirrors the callgraph primitive's two-pass caller-id construction + per-body ast.walk order, so frames align 1:1 with callgraph edges via a per-(caller,callee) FIFO queue consumed in source order"
    - "Pull-and-annotate: pull the authoritative primitive (callgraph) for the must-have edges, attach a deterministically-computed annotation (frame label) from a parallel pure-AST walk"

key-files:
  created:
    - tests/spikes/__init__.py
    - tests/spikes/test_sp2_branch_fidelity.py
    - .planning/spikes/SP-2-sequence-branch-fidelity.md
    - lib_code_parser/extractors/evaluations/sequence_diagram.py
    - tests/unit/extractors/test_sequence_diagram.py
    - tests/unit/extractors/fixtures/seq_callgraph.py
    - tests/acceptance/test_dia02_sequence_diagram.py
  modified:
    - lib_code_parser/_dispatch.py
    - tests/unit/extractors/test_diagram_schema.py
    - tests/parity/fixtures/v01_snapshot.json

key-decisions:
  - "SP-2 VERDICT = SHIP (D-08): the alt/loop/par mapping (ast.If→alt, ast.For/AsyncFor/While→loop, ast.AsyncWith/await→par) is a pure byte-identical AST function — no LLM, no heuristic, no set/dict-iteration ordering. 7 probes pass incl. PYTHONHASHSEED=random. Branch fidelity ships in v0.2.0; DIA-02-FULL is NOT created."
  - "Branch frames encoded on GraphEdge.label (NOT a new EdgeKind, NOT GraphNode attributes): label already exists, is part of the (source,target,edge_type,label) DET-04 sort key, and edge_type stays the existing `calls` value. Deepest-enclosing-frame-wins; awaited call is always `par`."
  - "Participant resolution (Claude's discretion per CONTEXT §Discretion): inherit Phase 2 callgraph representation verbatim — caller = module-qualified node id, callee = bare name (self-call → bare method name, chain a.b() → multiple edges). Phase 2 deferred 'CallGraph resolution expansion' re-evaluated: NOT needed for linear correctness, so left as-is (minimum for correctness)."
  - "Frame-edge alignment via per-(caller,callee) FIFO queue: the frame walk reproduces callgraph's exact traversal order, so popping one frame per callgraph edge (consumed in callgraph's (caller,callee)-sorted, source-order-stable sequence) attaches the correct frame to each occurrence even when a callee is called multiple times in different frames."

patterns-established:
  - "Pattern: first-deliverable spike — run the determinism probe FIRST, record the ship/defer verdict in .planning/spikes/, THEN implement the must-have + (if SHIP) the spike-gated feature in the same plan"
  - "Pattern: must-have-independent-of-spike (D-07) — the linear sequence ships regardless of the spike outcome; the spike only gates the branch-fidelity layer on top"

requirements-completed: [DIA-02, DIA-07]

# Metrics
duration: 12min
completed: 2026-06-02
---

# Phase 3 Plan 03: SP-2 Spike + DIA-02 Sequence Diagram Summary

**Ran the SP-2 spike first and proved branch fidelity (alt/loop/par frames) is a deterministic pure-AST rule (verdict = SHIP), then shipped the DIA-02 sequence_diagram extractor — linear `calls` edges pulled from the callgraph primitive (D-07 must-have) with SP-2 branch-frame labels carried on `GraphEdge.label` (zero schema change) — registered at canonical EVALUATIONS position #2, validating against the DIA-07 schema and emitting DET-04-sorted output that is byte-identical under PYTHONHASHSEED=random.**

## Performance

- **Duration:** ~12 min
- **Tasks:** 2 completed
- **Files:** 7 created, 3 modified
- **Tests:** 308 → 335 passing (+27 new: 7 spike + 15 sequence unit + 4 acceptance + 1 schema case), full suite incl. tests/parity green

## Accomplishments

### Task 1 — SP-2 spike (gating deliverable, run FIRST)
- Built `tests/spikes/test_sp2_branch_fidelity.py`: 7 probes proving the candidate mapping (`ast.If→alt`, `ast.For/AsyncFor/While→loop`, `ast.AsyncWith`/awaited-call→`par`) is a **pure source-only AST function** — byte-identical across repeated parses AND across `PYTHONHASHSEED=random` (the output path uses only ordered lists, never set/dict iteration).
- Recorded the **VERDICT = SHIP** in `.planning/spikes/SP-2-sequence-branch-fidelity.md` (SP-3 doc format) with the D-08 deterministic-rule rationale, the documented frame-marker scheme for Task 2 (`GraphEdge.label`), and the fixtures that proved determinism (if/for/while/async/mixed-nesting). Noted the early single-pass `ast.walk` revision was a *precision* bug (wrong frame for deep nesting), never a determinism failure — fixed to recursive descent.

### Task 2 — DIA-02 sequence_diagram (TDD: RED → GREEN)
- **Linear must-have (D-07):** pulls `callgraph.extract` → maps each `CallEdge(caller, callee)` to `GraphEdge(edge_type="calls", source=caller, target=callee)`; every distinct caller + callee becomes a `GraphNode(node_type="participant")`.
- **Branch frames (SP-2 SHIP):** a parallel pure-AST walk mirroring callgraph's two-pass caller-id construction + per-body `ast.walk` order computes each call's nearest-enclosing frame (deepest-wins; awaited→`par`) and attaches it to `GraphEdge.label` via a per-`(caller, callee)` FIFO queue consumed in source order. No schema change, no new EdgeKind.
- Registered append-only at **canonical position #2** (`class_diagram`, **`sequence_diagram`**, `component_diagram`, `package_diagram`).
- Added a DIA-07 schema-conformance case (sequence output through `assert_valid_graphmodel`) and a full acceptance test via public `execute()`.
- Regenerated the v0.1.0 parity snapshot via `scripts/generate_v01_snapshot.py` and **verified only the `sequence_diagram` slot changed** (empty → 11 participants + 4 calls edges with correct `alt`/`""` labels) while all other slots stayed byte-identical.

## Task Commits

1. **Task 1: SP-2 spike — verdict=SHIP** — `e8bf002` (test)
2. **Task 2: DIA-02 sequence_diagram + register #2 + parity regen** — `fa82d28` (feat)

_TDD: Task 2 RED (sequence unit tests failed on missing module) → GREEN (15 unit + 4 acceptance + 1 schema pass). Behavior tests + implementation + by-design parity-snapshot regeneration are committed together per the by-design-breaking-artifact convention established in Plans 01/02 (the parity snapshot is regenerated in the same commit as the extractor that changes it)._

## Verification Results

- `PYTHONPATH=. python -m pytest -q` → **335 passed** (full suite incl. `tests/parity/test_snapshot_v01_fixture.py`, which runs because pyright 1.1.409 is installed locally).
- `PYTHONHASHSEED=random python -m pytest tests/unit/extractors tests/spikes -q` → **112 passed** (DET-04 determinism + SP-2 byte-identical probes).
- SP-2 grep gate `grep -v '^#' SP-2-sequence-branch-fidelity.md | grep -ciE 'verdict|ship|defer'` → **14**.
- Canonical-order dispatch check → `['class_diagram','sequence_diagram','component_diagram','package_diagram']` is a prefix-preserving subsequence of the 7-canonical order and contains `sequence_diagram`.
- `ruff check` + `ruff format --check` → clean on `sequence_diagram.py` + `_dispatch.py`.
- Parity diff confirmed (scripted): only `sequence_diagram` slot changed; the 4 primitive slots + class/component/package diagram slots are byte-identical.

## Deviations from Plan

None — plan executed exactly as written. The SP-2 verdict resolved to SHIP (as the RESEARCH §Open Questions #3 recommendation anticipated), so Task 2 implemented branch frames as planned; the must-have linear sequence shipped regardless per D-07.

## Known Stubs

None. `sequence_diagram` is fully wired: linear `calls` edges come from the authoritative callgraph primitive and branch frames are computed from the AST. The remaining empty CodeContent slots (`state_diagram`, `function_spec`, `class_spec`) are owned by Plans 03-04/03-05 and intentionally remain inert defaults until those plans register their EVALUATIONS entries.

## Threat Flags

None. The threat register dispositions were satisfied:
- **T-03-05** (Layer M integrity / branch-frame walk): branch fidelity shipped ONLY after SP-2 proved a deterministic byte-identical rule — determinism is the explicit ship gate (D-08), satisfied by 7 probes incl. PYTHONHASHSEED=random.
- **T-03-06** (output ordering): DET-04 sort-on-exit `(source,target,edge_type,label)` + `dict.fromkeys` dedup; no clock/env/network; verified byte-identical.
- **T-03-SC** (package installs): zero installs — stdlib `ast` + existing pins only.

No new network/auth/secret/file-access surface introduced (pure in-process AST mapping).

## Self-Check: PASSED

- All 7 created files exist on disk.
- Both task commits (`e8bf002`, `fa82d28`) present in `git log`.
- Full suite (335) green including the easy-to-miss `tests/parity/test_snapshot_v01_fixture.py` (runs because pyright is installed).
