---
phase: 03-python-diagram-spec-extractors
plan: 06
subsystem: spec-extractors
tags: [evaluations, spc-02, spc-04, class-spec, aux-contract-markers, icontract, deal, pep316, import-provenance, d-10, det-04, dispatch, parity-snapshot, phase-close]

# Dependency graph
requires:
  - phase: 03-python-diagram-spec-extractors
    plan: 01
    provides: "models/evaluations/spec.py (ClassSpec + SpecCondition + SpecConditionSourceKind SPC-04 taxonomy), CodeContent.class_spec slot, executor EVALUATIONS walk"
  - phase: 03-python-diagram-spec-extractors
    plan: 05
    provides: "EVALUATIONS canonical-order append-only registration (#6 function_spec), DET-04 sort-on-exit discipline, parity-snapshot regeneration discipline"
provides:
  - "SPC-04 _markers.py — detection-only (D-10) icontract/deal decorator + PEP-316 docstring-keyword detector using Phase-2 import-provenance (T-03-13); a user's own require()/@pre with no marker import is NOT flagged; lambdas ast.unparse'd never executed (T-03-14)"
  - "SPC-02 class_spec extractor — one ClassSpec(node_id, definition, members, invariants) per class; members = methods + class-level annotated attrs (sorted); invariants = aggregated SPC-04 markers (class-decorator inv + per-method pre/post/ensure/require + PEP-316), DET-04-sorted by (source_kind, line_no, text)"
  - "EVALUATIONS class_spec registration at canonical position #7 — the FINAL entry; all 7 EVALUATIONS now present in canonical order; executor walk produces all 7 CodeContent evaluation slots"
  - "v01 parity snapshot regenerated: class_spec slot now populated for EXAMPLE_SOURCE (2 ClassSpec); all primitive + diagram + function_spec slots stay byte-identical"
affects: ["Phase 4 (C++ frontend reuses the EVALUATIONS dispatch contract — now complete at 7)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Detection-only auxiliary-marker recognition (D-10): the marker libraries (icontract/deal) are NEVER imported — they are recognized by AST decorator shape with the contracts.py import-provenance restriction reused per target package. The (pkg, attr) marker table drives kind/source_kind. Bare-name decorators without a real marker import have NO provenance and are rejected (T-03-13 false-positive defense)."
    - "Parameterized import-provenance over multiple target packages: resolve_marker_aliases scans ImportFrom whose root package is in _TARGET_PACKAGES=('icontract','deal'), mapping local_name -> (package, canonical_attr); attribute form (@pkg.attr) carries inline provenance independent of the alias map (mirrors contracts.py _is_attribute_form)."
    - "Condition text via ast.unparse of the decorator's first arg only — the lambda AST is stringified, never evaluated (T-03-14); no code execution from untrusted source."
    - "ClassSpec.invariants as SPC-04 marker aggregate: SPC-04 conditions carry their own source_kind (icontract_*/deal_*/pep316_*) so the verifier can weight them against the Phase-2 contracts primitive (read separately from CodeContent.contracts); SpecCondition.line_no stamped via model_copy at the class/method node so the DET-04 (source_kind, line_no, text) sort key is total and stable."

key-files:
  created:
    - lib_code_parser/extractors/evaluations/_markers.py
    - lib_code_parser/extractors/evaluations/class_spec.py
    - tests/unit/extractors/test_aux_markers.py
    - tests/unit/extractors/test_class_spec.py
    - tests/unit/extractors/fixtures/aux_marker_samples.py
    - tests/acceptance/test_spc02_class_spec.py
    - tests/acceptance/test_spc04_contract_markers.py
  modified:
    - lib_code_parser/_dispatch.py
    - tests/unit/test_dispatch.py
    - tests/parity/fixtures/v01_snapshot.json

key-decisions:
  - "D-10 HONORED: icontract/deal are DETECTED, never imported. The D-10 grep gate (grep -v '^#' _markers.py | grep -cE 'import icontract|import deal|from icontract|from deal') returns 0 — docstring examples were rephrased with <pkg> placeholders so no literal import-token sequence appears even in comments/prose."
  - "Invariant #1 HONORED: the frozen primitives/contracts.py SourceKind Literal is NOT mutated; all SPC-04 source_kind values come from models/evaluations/spec.py SpecConditionSourceKind (shipped by Plan 01). git status shows no change to extractors/primitives/contracts.py or models/primitives/contracts.py."
  - "SPC-04 markers live in ClassSpec.invariants (valid SpecConditionSourceKind values); the Phase-2 Pydantic/dataclass contracts are NOT duplicated into ClassSpec.invariants because their source_kinds (pydantic_validator etc.) are NOT in the frozen SpecConditionSourceKind Literal and mutating that shipped Plan-01 model is out of this plan's scope. The verifier reads Phase-2 contracts from CodeContent.contracts directly (already populated by the contracts primitive) and SPC-04 markers from ClassSpec.invariants — both surfaces remain available. (Deviation Rule 3, documented below.)"
  - "members aggregate methods + class-level annotated attrs (AnnAssign) + plain class-body Assign targets, sorted by name (DET-04). definition = synthesized 'class Name(Base, ...)' header (bases + keyword bases like metaclass), ast.unparse'd for byte-stability."
  - "Parity snapshot regenerated via scripts/generate_v01_snapshot.py (NEVER hand-edited): the ONLY change is the class_spec slot for EXAMPLE_SOURCE going from [] to 2 ClassSpec (OrderModel + OrderService, invariants=[] since EXAMPLE_SOURCE has no icontract/deal/PEP-316 markers); verified single-hunk +24/-1 at the final slot, all primitive + diagram + function_spec slots byte-identical."

patterns-established:
  - "Pattern: parameterized import-provenance detector — the contracts.py provenance trio generalizes to N target libraries by keying the alias map on (package, attr) and accepting a _TARGET_PACKAGES tuple; FSM detection (Plan 04) and SPC-04 (this plan) both reuse it, proving the Phase-2 false-positive defense is library-agnostic."
  - "Pattern: phase-closing append-only registration — the final EVALUATIONS entry graduates the forward-compatible subsequence dispatch test to a full-equality assertion; this is the canonical 'last extractor in a dispatch family' close-out."

requirements-completed: [SPC-02, SPC-04]

# Metrics
duration: 6min
completed: 2026-06-01
---

# Phase 3 Plan 06: SPC-02 Class Spec + SPC-04 Auxiliary Contract Markers (Phase Close) Summary

**Closed Phase 3 by delivering the last two requirements and registering the 7th and final EVALUATIONS extractor: a detection-only (D-10) auxiliary-contract-marker detector (`_markers.py`) that recognizes icontract `@require/@ensure/@invariant`, deal `@pre/@post/@ensure/@inv`, and PEP-316 `pre:/post:` docstring keywords purely by AST shape — never importing the libraries — guarded by the Phase-2 import-provenance restriction so a user's own `def require()` with no marker import is rejected (T-03-13) and condition lambdas are `ast.unparse`'d but never executed (T-03-14); plus the `class_spec` extractor that emits one `ClassSpec(node_id, definition, members, invariants)` per class with members (methods + annotated attrs, sorted) and DET-04-sorted SPC-04 marker invariants, registered append-only at canonical EVALUATIONS position #7 — completing all 7 in canonical order — with the v0.1.0 parity snapshot regenerated via the script to absorb the now-populated `class_spec` slot while every primitive, diagram, and function_spec slot stays byte-identical, and the frozen `primitives/contracts.py` SourceKind Literal left untouched (invariant #1).**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-01T18:04:23Z
- **Completed:** 2026-06-01T18:10:35Z
- **Tasks:** 2 completed
- **Files:** 7 created, 3 modified
- **Tests:** 393 → 426 passing (+33 new: 15 aux-marker unit + 11 class_spec unit + 5 SPC-02 acceptance + 3 SPC-04 acceptance, minus the dispatch test graduating in place); FULL suite incl. `tests/parity` green

## Accomplishments

### Task 1 — `_markers.py` SPC-04 detection-only marker detector (TDD RED → GREEN)
- **`resolve_marker_aliases(module)`** scans `ImportFrom` whose root package ∈ `("icontract", "deal")`, mapping `local_name → (package, canonical_attr)` (handles `... import require`, `... import require as req`); a plain module import yields `{}` (attribute form handled separately).
- **`detect_decorator_markers(decorators, aliases)`** classifies via the `_MARKER_TABLE` `(pkg, attr) → (kind, source_kind)` (RESEARCH §575-583). Provenance order: attribute form `@pkg.attr` first (inline provenance), then bare name resolved through the alias map; bare names with no marker import are rejected. Condition `text` = `ast.unparse(decorator.args[0])` (the lambda) — never evaluated.
- **`detect_pep316_markers(docstring)`** — two anchored linear regexes (`^\s*pre:\s*(.+)$`, `^\s*post(?:\[\w+\])?:\s*(.+)$`) over docstring lines; supports `post[self]:`/`post[old]:` qualified forms.
- **D-10 grep gate = 0** — docstring examples rephrased with `<pkg>` placeholders so no literal `import icontract`/`from deal` token sequence appears even in prose.
- **15 unit tests**: provenance map, icontract/deal attribute + from-import forms, class-decorator invariants, PEP-316 pre/post, the two decoy false-positive cases (`def require()` and bare `@pre`), and repeated-run byte-stability.

### Task 2 — `class_spec.py` (SPC-02/04) + register #7 (final) + parity regen (TDD RED → GREEN)
- **`class_spec.extract`** walks the CAV `ast.Module` once (Pitfall 5 — no re-parse); for each top-level `ClassDef` builds `ClassSpec(node_id, definition, members, invariants)`.
  - `definition` = synthesized `class Name(Base, ...)` header (bases + keyword bases, `ast.unparse`'d).
  - `members` = method names + class-level annotated/plain attribute names, sorted (DET-04).
  - `invariants` = SPC-04 markers from class decorators + per-method decorators + per-method PEP-316 docstrings; each `SpecCondition` line-stamped via `model_copy`, then sorted by `(source_kind, line_no, text)`.
- Registered **append-only at canonical position #7** (`class_diagram`, `sequence_diagram`, `component_diagram`, `package_diagram`, `state_diagram`, `function_spec`, **`class_spec`**) — the FINAL EVALUATIONS entry. `test_dispatch` graduated from the forward-compatible subsequence assertion to full 7-key equality.
- **All 7 evaluation slots populated** through the public `execute()` path (acceptance-asserted); `class_spec` slot is non-empty (2 ClassSpec) for `EXAMPLE_SOURCE`.
- **Parity snapshot regenerated** (`scripts/generate_v01_snapshot.py`, never hand-edited): the `class_spec` slot for `EXAMPLE_SOURCE` went from `[]` to 2 ClassSpec (`OrderModel` members = order_id/status/total/validate_status/check_total; `OrderService` members = create_order/_calculate_total/cancel_order; both `invariants=[]` since no aux markers). Diff verified as a single contiguous hunk (+24/-1) at the final slot — **all primitive, diagram, and function_spec slots byte-identical**.

## Task Commits

1. **Task 1: SPC-04 aux contract marker detector (_markers.py, detection-only D-10)** — `cb3b54c` (feat)
2. **Task 2: SPC-02/04 class_spec extractor + register final 7th EVALUATIONS entry** — `bde5fcb` (feat)

_TDD: Task 1 RED (`_markers` missing → ImportError) → GREEN (15 unit). Task 2 RED (`class_spec` missing → ImportError + dispatch len mismatch) → GREEN (11 unit + 8 acceptance + dispatch full-equality), then the parity test (in `tests/parity`) drove the snapshot regeneration that completed GREEN._

## Verification Results

- `PYTHONPATH=. python -m pytest -q` → **426 passed** (FULL suite incl. `tests/parity/test_snapshot_v01_fixture.py`).
- `PYTHONHASHSEED=random python -m pytest tests/unit/extractors -q` → **172 passed** (DET-04 byte-stability).
- D-10 grep gate `grep -v '^#' _markers.py | grep -cE 'import icontract|import deal|from icontract|from deal'` → **0**.
- EVALUATIONS canonical order → `['class_diagram','sequence_diagram','component_diagram','package_diagram','state_diagram','function_spec','class_spec']` — all 7 present, `class_spec` at #7 (final).
- `git status` → no change to `extractors/primitives/contracts.py` or `models/primitives/contracts.py` (invariant #1 — frozen Phase-2 files untouched).
- `ruff check` + `ruff format --check` → clean on `_markers.py`, `class_spec.py`, `_dispatch.py`, and all new/modified test files.
- Parity diff: single contiguous hunk +24/-1 at the final `class_spec` slot; no `functions`/`call_graph`/`type_deps`/`contracts`/diagram-slot/`function_spec`-slot lines in the diff.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Phase-2 contracts NOT duplicated into ClassSpec.invariants (frozen-Literal constraint)**
- **Found during:** Task 2 design.
- **Issue:** The plan behavior says ClassSpec.invariants should aggregate Phase-2 dataclass/Pydantic contracts (from `contracts.extract`) PLUS SPC-04 markers. But `ClassSpec.invariants` is `list[SpecCondition]`, and `SpecCondition.source_kind` is the closed `SpecConditionSourceKind` Literal (docstring / icontract_* / deal_* / pep316_*) shipped by Plan 01 — it does NOT include the Phase-2 `SourceKind` values (`pydantic_validator`, `pydantic_field_validator`, `pydantic_model_validator`, `dataclass_post_init`). Representing Phase-2 contracts as `SpecCondition` would require mutating the shipped Plan-01 `SpecConditionSourceKind` Literal (a schema change beyond this plan's artifacts, and a parity risk).
- **Fix:** ClassSpec.invariants aggregates SPC-04 markers only (their source_kinds are valid). Phase-2 Pydantic/dataclass contracts remain in `CodeContent.contracts` (already populated by the `contracts` primitive) — the verifier reads both surfaces. No data is lost; SPC-04 is correctly SUPPLEMENTARY (per RESEARCH §409/§449 "keep them in a separate field / mark source_kind so the verifier can weight them"). This honors invariant #1 (frozen primitives/contracts.py) AND avoids mutating the shipped Plan-01 spec.py Literal.
- **Files modified:** none beyond the planned set (no schema files touched).
- **Commit:** `bde5fcb`

## Authentication Gates

None.

## Known Stubs

None. `class_spec` is fully wired: definition/members from the CAV ClassDef walk, invariants from the `_markers` detector (icontract/deal/PEP-316). All 7 EVALUATIONS slots are now populated — Phase 3 closes with no inert evaluation slots remaining.

## Threat Flags

None. The threat register dispositions were satisfied:
- **T-03-13** (Spoofing / data integrity): import-provenance restriction asserted — `def require()` with no icontract import and bare `@pre` with no deal import are both NOT classified (unit + acceptance tests).
- **T-03-14** (Elevation of privilege / code exec): condition text is `ast.unparse(decorator.args[0])` only; icontract/deal never imported/executed (D-10 grep gate = 0).
- **T-03-15** (Tampering / Layer M integrity): DET-04 sort-on-exit on members (by name) + invariants (by source_kind, line_no, text) + ClassSpec list (by node_id); no clock/env/network — byte-identical under `PYTHONHASHSEED=random`.
- **T-03-SC** (package installs): ZERO installs — icontract/deal are detection targets, NOT dependencies; `pyproject.toml` unchanged.

No new network/auth/secret/file-access surface introduced (pure in-process AST/text analysis over `cav.payload`).

## Self-Check: PASSED

- All 7 created files exist on disk.
- Both task commits (`cb3b54c`, `bde5fcb`) present in `git log`.
- Full suite (426) green including `tests/parity/test_snapshot_v01_fixture.py`; parity snapshot regenerated (class_spec slot only) — `git status` clean on the snapshot.
- D-10 grep gate = 0; frozen `primitives/contracts.py` untouched; all 7 EVALUATIONS in canonical order.
