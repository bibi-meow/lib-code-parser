---
spike_id: SP-2
phase: 3
target: "sequence-diagram branch fidelity (alt/loop/par frames) — deterministic-rule constructibility"
policy: "D-08 — ship-vs-defer judged SOLELY by 'is a deterministic rule constructible as a pure function' (no LLM/heuristic)"
status: verdict-recorded-ship
---

# SP-2: Sequence-Diagram Branch Fidelity (alt / loop / par frames)

**Spike ID:** SP-2
**Run date:** 2026-06-02 (Plan 03-03 Task 1, first deliverable)
**Plan 03-03 gate:** spike run FIRST, verdict recorded here, BEFORE DIA-02 implementation.

## Purpose

Decide whether the v0.2.0 `sequence_diagram` extractor (DIA-02) ships branch
fidelity — wrapping calls in Mermaid-style `alt` / `loop` / `par` frames derived
from Python control-flow constructs — NOW, or defers it to v0.3.0 as
**DIA-02-FULL**.

Per **D-07** the *linear* sequence (call-graph-derived `calls` edges) is a
v0.2.0 must-have **independent of this spike's outcome**. SP-2 only governs the
*branch-fidelity* layer on top of it.

Per **D-08** the SOLE ship criterion is: **"is a deterministic rule
constructible as a pure function of `(raw_content, path, config)`?"** — i.e. can
the mapping be applied as a byte-identical pure AST walk with no LLM, no
heuristic disambiguation, and no order-dependent (set/dict-iteration) state?
This preserves the Layer M bisimulation determinism precondition.

## Candidate rule under test

A pure structural map from Python AST control-flow node type → sequence frame
kind:

| AST construct | Frame kind | Rationale |
|---------------|-----------|-----------|
| `ast.If` | `alt` | conditional branch = alternative interaction |
| `ast.For` / `ast.AsyncFor` / `ast.While` | `loop` | iteration = repeated interaction |
| `ast.AsyncWith` + awaited call (`ast.Await` wrapping `ast.Call`) | `par` | concurrent / asynchronous interaction |
| (none of the above) | `""` (linear) | top-level / unframed call |

Frame assignment for a call is decided by the **nearest enclosing** control-flow
statement (deepest-frame-wins), recomputed by recursive descent over each node's
own `body` / `orelse` / `finalbody` / handler bodies in **source order**. An
awaited call is always `par` regardless of enclosing frame.

## Determinism verification (the D-08 evidence)

Probe: `tests/spikes/test_sp2_branch_fidelity.py` (does NOT import the
production extractor — a self-contained proof of the rule).

| Probe | What it proves | Result |
|-------|----------------|--------|
| `test_if_maps_to_alt` | `ast.If` → `alt` for both branches | ✓ PASS |
| `test_for_maps_to_loop` | `ast.For` → `loop` | ✓ PASS |
| `test_while_maps_to_loop` | `ast.While` → `loop` | ✓ PASS |
| `test_async_await_maps_to_par` | `async with` + `await call()` → `par` | ✓ PASS |
| `test_repeated_extraction_byte_identical` | same fixture parsed twice → identical `repr` (5 fixtures) | ✓ PASS |
| `test_mixed_nesting_is_stable` | nested `if > for > while` → deepest frame wins, byte-stable | ✓ PASS |
| `test_no_set_or_dict_in_output_path` | output is an ordered `list[tuple]` (hashseed-stable) | ✓ PASS |

- `python -m pytest tests/spikes/test_sp2_branch_fidelity.py -q` → **7 passed**.
- `PYTHONHASHSEED=random python -m pytest tests/spikes/test_sp2_branch_fidelity.py -q` → **7 passed** (no set/dict iteration in the output path → byte-identical regardless of hash seed).

### Fixtures that proved determinism

- **`_IF_FIXTURE`** (`if/else`) — proved `ast.If → alt` for both arms.
- **`_FOR_FIXTURE`** / **`_WHILE_FIXTURE`** — proved `ast.For` / `ast.While → loop`.
- **`_ASYNC_FIXTURE`** (`async with` + two `await call()`) — proved awaited calls → `par`.
- **`_MIXED_FIXTURE`** (`if > for > while > process()`) — proved nesting precedence
  (deepest enclosing frame wins) is computable by recursive descent and is byte-stable.

### Fixtures / cases that would have DISPROVEN determinism (none triggered)

The rule was specifically designed to avoid the non-deterministic traps the
research (§Open Questions #3) flagged:
- No symbol-table / type-resolution lookup is required to choose a frame
  (frame depends only on Python AST node type).
- No heuristic disambiguation between "this `if` is a guard" vs "this `if` is an
  alt frame" — every `ast.If` maps to `alt` unconditionally.
- No set/dict iteration feeds the output ordering — the descent walks ordered
  `list` bodies, so PYTHONHASHSEED has no effect.

An early probe revision that flattened nested bodies via a single `ast.walk`
pass was *byte-identical* but assigned the wrong (outermost) frame to deeply
nested calls; this was a precision bug, NOT a determinism failure — fixing it to
recursive descent kept the output a pure deterministic function. The
determinism criterion (D-08) was never in doubt.

## Verdict legend (D-08)

- Deterministic pure-function rule constructible (byte-identical, no LLM/heuristic) → **SHIP** (branch fidelity in v0.2.0).
- Rule requires LLM / heuristic / non-pure state → **DEFER** to v0.3.0 as DIA-02-FULL.

## Verdict

**VERDICT: SHIP.** Branch fidelity (`alt` / `loop` / `par` frames) IS a
deterministic, byte-identical pure-function rule of the source AST. It ships in
the v0.2.0 `sequence_diagram` extractor (Plan 03-03 Task 2).

**Documented frame-marker scheme for Task 2:** branch frames are encoded on the
`calls` `GraphEdge` via the edge `label` field, set to the nearest-enclosing
frame kind (`"alt"` / `"loop"` / `"par"`), empty string for linear/top-level
calls. This requires NO schema change (`GraphEdge.label` already exists and is
part of the DET-04 composite sort key `(source, target, edge_type, label)`), and
keeps the edge `edge_type` as the existing `calls` EdgeKind value (no new
EdgeKind). The deepest-enclosing-frame-wins rule from the probe is the
implemented semantic.

**Rationale (D-08 criterion):** the mapping is a pure function of the parsed AST
— every frame decision is made solely from the Python AST node *type* and source
*order*, with no external lookup, no heuristic, and no hash-seed-dependent
iteration. All 7 probes pass, including byte-identical re-extraction under
`PYTHONHASHSEED=random`. This satisfies the Layer M bisimulation determinism
precondition, so there is no reason to defer.

**Independent of this verdict (D-07):** the linear `calls`-edge sequence is a
v0.2.0 must-have and ships regardless. DIA-02-FULL is NOT created — branch
fidelity is delivered in v0.2.0, not deferred.

---

Last updated by Plan 03-03 Task 1 on 2026-06-02.
