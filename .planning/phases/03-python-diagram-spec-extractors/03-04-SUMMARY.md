---
phase: 03-python-diagram-spec-extractors
plan: 04
subsystem: diagram-extractors
tags: [evaluations, state-diagram, dia-05, dia-06, sp-1-spike, fsm-detection, import-provenance, return-value-substitution, det-04, dispatch, parity-snapshot]

# Dependency graph
requires:
  - phase: 03-python-diagram-spec-extractors
    plan: 01
    provides: "graph_base.py (GraphNode/GraphEdge with source_unresolved + transitions_to EdgeKind + GuardExpr), CodeContent state_diagram slot, executor EVALUATIONS walk, DIA-07 assert_valid_graphmodel"
  - phase: 03-python-diagram-spec-extractors
    plan: 03
    provides: "EVALUATIONS canonical-order registration pattern, DET-04 sort-on-exit + dict.fromkeys dedup, parity-snapshot regeneration discipline, first-deliverable-spike pattern, must-have-independent-of-spike (D-07)"
provides:
  - "SP-1 verdict = DEFER: general control-flow→state (beyond explicit FSM) is NOT a deterministic pure-function rule (state identity ambiguous without an explicit state variable); recorded in .planning/spikes/SP-1-general-control-flow-state.md with the D-08 determinism rationale. DIA-05-FULL deferred to v0.3.0"
  - "DIA-05 state_diagram extractor — 3 explicit FSM families (transitions.Machine / python-statemachine / native Enum) via import-provenance + fixture-asserted Color(Enum)→0-FSM negative + false-positive defense"
  - "DIA-06 return-value substitution — intra-class, N-level recursive, cycle-safe; fully-resolved→concrete transitions_to edges, unresolvable→one source_unresolved=True placeholder"
  - "EVALUATIONS state_diagram registration at canonical position #5 (append-only)"
  - "DIA-07 schema-conformance case feeding state output through assert_valid_graphmodel"
  - "v01 parity snapshot byte-identical: state_diagram slot stays empty (EXAMPLE_SOURCE has no explicit FSM) — no regeneration needed"
affects: ["03-05 function/class spec", "03-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import-provenance-gated FSM detection: copy the contracts.py provenance trio (resolve_aliases over target_pkgs + plain-import binding map + provenance-gated classify) parameterized for ('transitions',) and ('statemachine','python_statemachine') — a same-name user Machine/State without a real import is never misdetected (T-03-08)"
    - "Detection-only target libraries (D-10): transitions / python-statemachine are matched by AST shape and NEVER imported; the grep gate (no `import transitions`/`from statemachine`) asserts zero target-lib imports in source"
    - "Bounded intra-class return-value propagation: resolve self.state=self._next() by walking the callee's ast.Return nodes intra-class with a visited:set[str] of method names — N-level recursive, cycle-safe (re-entry stops the branch), termination guaranteed by finite method count (T-03-07 DoS bound)"
    - "source_unresolved marker on GraphEdge (NOT attributes — GraphEdge has none): exactly ONE placeholder transitions_to edge with source_unresolved=True per unresolvable mutation (external call / cycle dead-end / non-literal path)"
    - "Spike-as-determinism-probe (inverse outcome): the SP-1 probe proves NON-determinism by showing two equally-defensible candidate rules (first-assigned-attr vs most-assigned-attr) disagree on state identity for the SAME source — no canonical pure-function choice → DEFER"

key-files:
  created:
    - tests/spikes/test_sp1_control_flow_state.py
    - .planning/spikes/SP-1-general-control-flow-state.md
    - lib_code_parser/extractors/evaluations/_fsm_detect.py
    - lib_code_parser/extractors/evaluations/state_diagram.py
    - lib_code_parser/extractors/evaluations/_substitution.py
    - tests/unit/extractors/fixtures/fsm_samples.py
    - tests/unit/extractors/test_state_diagram.py
    - tests/unit/extractors/test_state_substitution.py
    - tests/acceptance/test_dia05_state_fsm.py
    - tests/acceptance/test_dia06_return_substitution.py
  modified:
    - lib_code_parser/_dispatch.py
    - tests/unit/extractors/test_diagram_schema.py

key-decisions:
  - "SP-1 VERDICT = DEFER (D-08): general control-flow→state extraction is NOT a deterministic pure-function rule. The probe proves the failure mode is NOT per-rule instability (every candidate rule is itself byte-stable) but the absence of a canonical CHOICE among equally-valid rules — without an explicit state variable, 'which attribute is the state' is a modeling judgment, not a source fact. Two defensible rules (first-assigned→count, most-assigned→flag) disagree on the same source. DIA-05-FULL deferred to v0.3.0; the explicit families ship regardless (D-07)."
  - "DIA-06 marker placement RESOLVED to GraphEdge.source_unresolved (the Plan 01 marker home, RESEARCH Pitfall 1 / Open Question #1): GraphEdge has NO attributes field and is extra='forbid', so the unresolved=true attribute wording from DIA-06 is reconciled to the source_unresolved:bool field. The unresolvable case emits exactly ONE placeholder edge (not N)."
  - "Family C (native Enum) split between two passes: literal `self.state = Enum.MEMBER` is handled by detect_native_enum (Task 2); non-literal `self.state = self._next()` is handled by the DIA-06 substitution pass (Task 3). Family C REQUIRES BOTH an Enum class AND >=1 transition assignment — a bare Color(Enum) yields ZERO state machines (SC3 negative)."
  - "Substitution's 'unresolvable' covers three deterministic cases, all → one placeholder: (a) external/non-self call (helper.compute()), (b) cycle dead-end (_a→_b→_a, visited-set stops with no literal), (c) a return path that can't reduce to a literal (conditional/variable). Each candidate rule is a pure function; the placeholder target label is the deterministic callee name."

patterns-established:
  - "Pattern: import-provenance FSM detection — reuse the Phase-2 contracts.py same-name false-positive defense (T-02-19) for FSM library anchoring (T-03-08), parameterized per target package set"
  - "Pattern: deterministic-spike DEFER outcome — a spike can prove NON-determinism by exhibiting two equally-valid candidate rules that disagree on the same source; the absence of a canonical choice (not per-rule instability) is the D-08 defer evidence"

requirements-completed: [DIA-05, DIA-06, DIA-07]

# Metrics
duration: 18min
completed: 2026-06-02
---

# Phase 3 Plan 04: SP-1 Spike + DIA-05 FSM State Diagram + DIA-06 Substitution Summary

**Ran the SP-1 spike first and proved that general control-flow→state extraction beyond the three explicit FSM families is NOT a deterministic pure-function rule (verdict = DEFER to v0.3.0 DIA-05-FULL: state identity is ambiguous without an explicit state variable, so two equally-valid candidate rules disagree on the same source), then shipped the D-07 must-haves regardless — the DIA-05 state_diagram extractor detecting all three explicit FSM families (transitions.Machine, python-statemachine, native Enum + transition method) via import-provenance with the Color(Enum)→0-FSM fixture-asserted negative case and false-positive defense, plus the DIA-06 N-level cycle-safe intra-class return-value substitution that emits concrete transitions_to edges when fully resolved and exactly one source_unresolved=True placeholder otherwise — registered append-only at canonical EVALUATIONS position #5, validating against the DIA-07 schema with DET-04-sorted output that is byte-identical under PYTHONHASHSEED=random.**

## Performance

- **Duration:** ~18 min
- **Tasks:** 3 completed
- **Files:** 10 created, 2 modified
- **Tests:** 335 → 365 passing (+30 new: 4 SP-1 spike probes + 11 state unit + 11 substitution unit + 4 DIA-05 acceptance + 4 DIA-06 acceptance + 1 DIA-07 schema case − overlaps), full suite incl. tests/parity green

## Accomplishments

### Task 1 — SP-1 spike (gating deliverable, run FIRST)
- Built `tests/spikes/test_sp1_control_flow_state.py`: 4 pure-function probes. The explicit-state form (`self.state = '...'`) IS canonically reducible (byte-stable); the general control-flow form (no explicit state var) is NOT — two equally-defensible candidate selection rules (`first-assigned-attr`→`count`, `most-assigned-attr`→`flag`) pick different "state" attributes from the SAME source.
- Recorded **VERDICT = DEFER** in `.planning/spikes/SP-1-general-control-flow-state.md` (SP-2 doc format) with the D-08 deterministic-rule rationale: the failure is NOT per-rule instability (each rule is byte-stable) but the absence of a canonical CHOICE among equally-valid rules — picking one would inject a modeling heuristic (forbidden by D-08). Confirms the RESEARCH §Open Questions #3 prediction. The explicit-FSM must-haves ship in Task 2/3 regardless (D-07).

### Task 2 — DIA-05 FSM detection (TDD: RED → GREEN)
- **`_fsm_detect.py`** (shared helper, stdlib-only): copies the contracts.py provenance trio parameterized per target package. Three matchers: `detect_transitions_machine` (Family A — list-of-dicts AND list-of-lists kwargs, bare + attribute call forms), `detect_python_statemachine` (Family B — State() attrs + `src.to(dst)` events + `|`-combine + `from_` reverse), `detect_native_enum` (Family C — Enum class + literal `self.state = Enum.MEMBER`, requires BOTH).
- **Negative case (SC3):** `class Color(Enum)` with no transition method → ZERO state nodes (fixture-asserted).
- **False-positive defense (T-03-08):** a user's own `Machine`/`State` with NO import of transitions/statemachine → NOT detected (mirrors contracts.py:180-222 shapes).
- **`state_diagram.py`:** unions the three matchers → `GraphModel` (state nodes + transitions_to edges + GuardExpr per event), DET-04-sorted on exit.
- Registered append-only at **canonical position #5** (`class_diagram`, `sequence_diagram`, `component_diagram`, `package_diagram`, **`state_diagram`**).
- Added a DIA-07 schema-conformance case; **D-10 grep gate = 0** (target libs never imported).
- **Parity snapshot byte-identical:** EXAMPLE_SOURCE has no explicit FSM, so the `state_diagram` slot stayed `{nodes:[],edges:[],guards:[]}` — no regeneration needed (verified slot + `git status` clean).

### Task 3 — DIA-06 return-value substitution (TDD: RED → GREEN)
- **`_substitution.py`:** resolves non-literal `self.<attr> = self._next()` by walking `_next`'s `ast.Return` nodes intra-class. N-level recursion through `self._other()`; `visited: set[str]` cycle detection (re-entry stops the branch); termination bounded by finite method count (T-03-07 DoS mitigation).
- Fully resolved (all paths → literals) → one concrete `transitions_to` edge per distinct resolved target. Unresolvable (external call / cycle dead-end / non-literal path) → exactly ONE placeholder edge with `source_unresolved=True`.
- Verified the cyclic fixture (`_a→_b→_a`) completes with no hang/RecursionError.

## Task Commits

1. **Task 1: SP-1 spike — verdict=DEFER** — `b166123` (test)
2. **Task 2: DIA-05 FSM detection + register #5 + parity check** — `1f6b32d` (feat)
3. **Task 3: DIA-06 return-value substitution** — `a6f902d` (feat)

_TDD: Task 2 RED (state_diagram module missing) → GREEN (state unit + acceptance + schema pass). Task 3 RED (substitution placeholder returned empty) → GREEN (substitution unit + acceptance pass). Task 2's `_substitution.py` was a deliberate no-op placeholder so DIA-05 shipped first; Task 3 replaced its body with the full algorithm._

## Verification Results

- `PYTHONPATH=. python -m pytest -q` → **365 passed** (full suite incl. `tests/parity/test_snapshot_v01_fixture.py`).
- `PYTHONPATH=. python -m pytest tests/unit tests/acceptance tests/spikes -q` → **343 passed, 1 skipped** (the skip is a pre-existing unrelated skip; parity test is in tests/parity, exercised by the full-suite run above).
- `PYTHONHASHSEED=random python -m pytest tests/unit/extractors tests/spikes -q` → **134 passed** (DET-04 determinism + SP-1 byte-identical probes).
- SP-1 grep gate `grep -v '^#' SP-1-general-control-flow-state.md | grep -ciE 'verdict|ship|defer'` → **16** (≥1).
- D-10 import gate (no `import transitions`/`from statemachine` in source) → **0**.
- Canonical-order dispatch check → `['class_diagram','sequence_diagram','component_diagram','package_diagram','state_diagram']` — prefix-preserving subsequence of the 7-canonical order, contains `state_diagram` at #5.
- `ruff check` + `ruff format --check` → clean on `_fsm_detect.py`, `state_diagram.py`, `_substitution.py`, `_dispatch.py`.
- Color(Enum) negative-case assertion `len([n for n in result.state_diagram.nodes if n.node_type=='state'])==0` passes.
- Cyclic substitution fixture completes within suite timeout (no hang/recursion error).

## Deviations from Plan

None affecting behavior — plan executed as written. One structural decision within Claude's discretion: the DIA-06 substitution algorithm was placed in a dedicated `_substitution.py` module (wired into `state_diagram.py`) rather than inlined into `state_diagram.py`. This keeps the FSM-matching (Task 2) and return-value-propagation (Task 3) concerns in separate stdlib-only helpers and let Task 2 ship DIA-05 with a no-op placeholder before Task 3 filled in the algorithm — consistent with the plan's "extend state_diagram.py, do not create a new extractor" intent (the extractor entry point remains the single `state_diagram.extract`; `_substitution.py` is an internal helper of that extractor, not a second registered EVALUATIONS entry). The SP-1 verdict resolved to DEFER (as RESEARCH §Open Questions #3 anticipated); the explicit-FSM must-haves shipped regardless per D-07.

## Known Stubs

None. `state_diagram` is fully wired: the three explicit FSM families are detected via import-provenance and the DIA-06 substitution resolves non-literal mutations. The remaining empty CodeContent slots (`function_spec`, `class_spec`) are owned by Plan 03-05 and intentionally remain inert defaults until that plan registers its EVALUATIONS entries.

## Threat Flags

None. The threat register dispositions were satisfied:
- **T-03-07** (DoS / recursion exhaustion): the DIA-06 walker is bounded by a `visited:set[str]` + finite intra-class method count; the cyclic `_a→_b→_a` fixture asserts no infinite loop.
- **T-03-08** (spoofing / data integrity): import-provenance restriction — a user's own Machine/State/require without a real import is NOT classified; false-positive defense tests asserted (decoy Machine + decoy StateMachine → 0 states).
- **T-03-09** (code exec): only `ast.Constant` literals are read; FSM libs never imported/executed (D-10, grep gate=0).
- **T-03-10** (Layer M integrity): DET-04 sort-on-exit; no clock/env/network; SP-1 general-control-flow did NOT ship (deferred — would have required a non-deterministic modeling choice).
- **T-03-SC** (package installs): zero installs — transitions/python-statemachine are detection targets only.

No new network/auth/secret/file-access surface introduced (pure in-process AST detection over `cav.payload`).

## Self-Check: PASSED

- All 10 created files exist on disk.
- All 3 task commits (`b166123`, `1f6b32d`, `a6f902d`) present in `git log`.
- Full suite (365) green including `tests/parity/test_snapshot_v01_fixture.py`; parity snapshot byte-identical (state_diagram slot empty, `git status` clean on the snapshot).
- SP-1 verdict doc lists the file via `git ls-files`; grep gate returns 16 (≥1).
