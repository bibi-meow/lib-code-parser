---
spike_id: SP-1
phase: 3
target: "general control-flow -> state extraction (beyond the 3 explicit FSM families) — deterministic-rule constructibility"
policy: "D-08 — ship-vs-defer judged SOLELY by 'is a deterministic rule constructible as a pure function' (no LLM/heuristic)"
status: verdict-recorded-defer
---

# SP-1: General Control-Flow -> State Extraction

**Spike ID:** SP-1
**Run date:** 2026-06-02 (Plan 03-04 Task 1, first deliverable)
**Plan 03-04 gate:** spike run FIRST, verdict recorded here, BEFORE the state_diagram extractor (Task 2/3) is implemented.

## Purpose

Decide whether the v0.2.0 `state_diagram` extractor (DIA-05) ships **general
control-flow -> state** extraction — reducing an arbitrary method that mutates
`self.<attr>` through nested conditionals, *without* an explicit Enum / State
variable, to a state graph — NOW, or defers it to v0.3.0 as **DIA-05-FULL**.

Per **D-07** the three explicit FSM families (`transitions.Machine(...)`,
`python-statemachine` `StateMachine` subclass, native `Enum` + transition
method) **plus** the DIA-06 return-value-substitution analysis are v0.2.0
must-haves **independent of this spike's outcome**. SP-1 only governs the
*general control-flow -> state* layer beyond those explicit families.

Per **D-08** the SOLE ship criterion is: **"is a deterministic rule constructible
as a pure function of `(raw_content, path, config)`?"** — i.e. can the mapping
be applied as a byte-identical pure AST walk with no LLM, no heuristic
disambiguation, and no order-dependent (set/dict-iteration) state? This
preserves the Layer M bisimulation determinism precondition.

## Candidate rule under test

A general rule would have to, for an arbitrary method, (1) identify *which*
instance attribute is "the state" and (2) enumerate *which* of its values are
canonical "states", from control flow alone — with no explicit state-variable
anchor (no `transitions.Machine`, no `State()`, no `Enum`-typed state attr +
literal `self.state = EnumClass.MEMBER`).

## Determinism verification (the D-08 evidence)

Probe: `tests/spikes/test_sp1_control_flow_state.py` (does NOT import the
production extractor — a self-contained proof about the rule's
constructibility).

| Probe | What it proves | Result |
|-------|----------------|--------|
| `test_explicit_state_values_are_canonical` | the EXPLICIT-state form (`self.state = '...'`) yields a uniquely-determined, byte-stable state list `["open","closed"]` — this is the SHIP-able form Task 2/3 implement | ✓ PASS |
| `test_two_reasonable_rules_disagree_on_state_identity` | for general control flow with NO explicit state var, two equally-defensible candidate selection rules (`first-assigned-attr` vs `most-assigned-attr`) pick DIFFERENT state attributes (`count` vs `flag`) from the SAME source | ✓ PASS |
| `test_no_explicit_state_literal_to_anchor_on` | the general method assigns no literal state value to any attr, so the explicit-FSM literal rule (which IS deterministic) finds nothing to anchor on — a NEW general rule would be required | ✓ PASS |
| `test_each_rule_is_individually_deterministic` | each candidate rule is itself a pure byte-stable function — determinism does not fail per-rule; it fails because there is no canonical CHOICE among equally-valid rules | ✓ PASS |

- `python -m pytest tests/spikes/test_sp1_control_flow_state.py -q` -> **4 passed**.
- `PYTHONHASHSEED=random python -m pytest tests/spikes/test_sp1_control_flow_state.py -q` -> **4 passed** (no set/dict iteration in any rule's output path).

### Why this is a DEFER (the determinism failure mode)

The failure is NOT that a single rule is unstable — every candidate rule is a
pure, byte-stable function (proved by `test_each_rule_is_individually_deterministic`).

The failure is that **there is no canonical CHOICE of rule** for the unanchored
general case. Without an explicit state variable in the source, "which attribute
is the state" and "which values are states" are *modeling decisions*, not facts
in the source. Two equally-reasonable rules
(`first-assigned-attr` -> `count`, `most-assigned-attr` -> `flag`) disagree on
the SAME source. A library whose Core Value is *deterministic fact extraction*
(physical facts only; the verifier owns interpretation) cannot pick one rule
over the other without injecting a heuristic / modeling judgment — exactly what
D-08 forbids. So no single pure function yields a canonical byte-identical state
graph for general control flow.

By contrast the explicit families ARE deterministic because the source itself
names the state variable and its literal values
(`test_explicit_state_values_are_canonical`) — the fact is in the source, not in
a modeling choice. That is why DIA-05 (explicit families) + DIA-06
(return-value substitution over those literal assignments) ship, while general
control-flow -> state does not.

## Verdict legend (D-08)

- Deterministic pure-function rule constructible (byte-identical, no LLM/heuristic) -> **SHIP** (general control-flow -> state in v0.2.0).
- Rule requires LLM / heuristic / modeling-judgment / non-pure choice -> **DEFER** to v0.3.0 as DIA-05-FULL.

## Verdict

**VERDICT: DEFER.** General control-flow -> state extraction (beyond the three
explicit FSM families) is **NOT** a deterministic pure-function rule: state
identity is ambiguous without an explicit state variable, so equally-valid
candidate rules disagree on the same source and no canonical reduction exists
without a heuristic / modeling judgment (forbidden by D-08). It is deferred to
**v0.3.0 as DIA-05-FULL** and is NOT implemented in v0.2.0.

This confirms the RESEARCH §Open Questions #3 prediction ("SP-1 likely defers:
state identity is ambiguous without an explicit state variable").

**Independent of this verdict (D-07):** the three explicit FSM families
(`transitions.Machine` / `python-statemachine` / native `Enum` + transition
method) and the DIA-06 return-value-substitution analysis ARE deterministic
(the state variable + its literal values are facts in the source) and **ship in
v0.2.0** — implemented in Task 2 (DIA-05 detection) and Task 3 (DIA-06
substitution) of this plan, regardless of this DEFER verdict.

---

Last updated by Plan 03-04 Task 1 on 2026-06-02.
