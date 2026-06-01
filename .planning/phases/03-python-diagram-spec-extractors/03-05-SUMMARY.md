---
phase: 03-python-diagram-spec-extractors
plan: 05
subsystem: spec-extractors
tags: [evaluations, spc-01, docstring-parser, google-numpy-sphinx, three-dialect-equivalence, pre-post-heuristic, det-04, dispatch, parity-snapshot, d-09]

# Dependency graph
requires:
  - phase: 03-python-diagram-spec-extractors
    plan: 01
    provides: "models/evaluations/spec.py (FunctionSpec/DocstringSection/SpecCondition + SpecConditionSourceKind 'docstring'), CodeContent.function_spec slot, executor EVALUATIONS walk"
  - phase: 03-python-diagram-spec-extractors
    plan: 04
    provides: "EVALUATIONS canonical-order append-only registration pattern (#5 state_diagram), DET-04 sort-on-exit discipline, parity-snapshot regeneration discipline"
provides:
  - "SPC-01 function_spec extractor — one FunctionSpec per function/method (synthesized signature + dialect-normalized docstring_sections + fixed-keyword pre/post); undocumented members emit an inert FunctionSpec so the signature is always visible"
  - "_docstring.py — stdlib-only Google/NumPy/Sphinx Napoleon dialect parser (D-09); the SAME content in all 3 dialects reduces to byte-identical normalized DocstringSection output (strongest SPC-01 determinism proof) — REUSABLE by Plan 06 class_spec"
  - "byte-stable dialect detection order Sphinx -> NumPy -> Google -> none; fixed-keyword pre/post heuristic (no NLP/scoring), source_kind='docstring'"
  - "EVALUATIONS function_spec registration at canonical position #6 (append-only)"
  - "v01 parity snapshot regenerated: function_spec slot now populated for EXAMPLE_SOURCE; all primitive + diagram slots stay byte-identical (single-line empty-array -> populated array; no other drift)"
affects: ["03-06 class_spec (consumes _docstring.parse for class-member invariants)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Three-dialect normalization equivalence: a single _detect_dialect (byte-stable Sphinx->NumPy->Google order) routes to three dialect-specific parsers that ALL emit the identical normalized DocstringSection shape — the equivalence is asserted on the SAME function body documented three ways (golden fixture), proving SPC-01 determinism without an external library (D-09)"
    - "Reusable evaluation-layer helper (_docstring.parse): a stdlib-only state machine over docstring.splitlines() shared by function_spec (Plan 05) and class_spec (Plan 06) — the parse() entry returns (sections, preconditions, postconditions) so both extractors get the same normalized shape"
    - "Fixed-keyword pre/post heuristic: _PRECONDITION_KEYWORDS tuple ('must be','non-negative','> 0','not None','required') + Raises->precondition + Returns->postcondition; substring match only (no scoring) → same docstring yields same conditions every run (T-03-11)"
    - "Inert-but-present spec: undocumented functions still emit a FunctionSpec with empty sections so the verifier always sees the signature (not skipped)"
    - "Signature synthesized deterministically from FunctionNode.params + return_type (FunctionNode has no signature field) — name(p: T, ...) -> R, byte-stable"

key-files:
  created:
    - lib_code_parser/extractors/evaluations/_docstring.py
    - lib_code_parser/extractors/evaluations/function_spec.py
    - tests/unit/extractors/test_docstring_parser.py
    - tests/unit/extractors/test_function_spec.py
    - tests/unit/extractors/fixtures/docstring_dialects.py
    - tests/acceptance/test_spc01_function_spec.py
  modified:
    - lib_code_parser/_dispatch.py
    - tests/parity/fixtures/v01_snapshot.json

key-decisions:
  - "D-09 HONORED: docstring parsing is a stdlib-only (re) internal state machine — NO docstring_parser or any external library added. Grep gate returns 0; git diff pyproject.toml is empty."
  - "Three-dialect equivalence is the correctness contract: the golden fixture (docstring_dialects.py) holds the SAME function documented Google/NumPy/Sphinx; the test asserts byte-identical DocstringSection AND byte-identical pre/post across all three — the strongest SPC-01 determinism proof per RESEARCH §Required Test Fixtures."
  - "parse() return shape = tuple[list[DocstringSection], list[SpecCondition], list[SpecCondition]] (sections, pre, post) — plan-allowed discretion; chosen over a wrapper dataclass to keep the helper a pure function returning spec.py model instances directly."
  - "function_spec is function/method-scoped (SPC-01); class nodes (kind=='class' from the functions primitive) are SKIPPED here — class-level spec is SPC-02 / Plan 06 (class_spec). Undocumented members are inert (empty sections), not skipped."
  - "Parity snapshot regenerated via scripts/generate_v01_snapshot.py (NEVER hand-edited): the ONLY change is the function_spec slot going from [] to a populated array of 6 FunctionSpec (EXAMPLE_SOURCE's 5 methods + process_payment); verified single-line deletion + 89-line insertion, all primitive (functions/call_graph/type_deps/contracts) + diagram (class/sequence/component/package/state) slots byte-identical."

patterns-established:
  - "Pattern: dialect-normalization equivalence — when extracting from multiple equivalent source notations (docstring dialects), assert the equivalence on a single golden fixture documented N ways; identical normalized output IS the determinism proof"
  - "Pattern: reusable stdlib-only evaluation helper (_docstring) consumed by sibling extractors (function_spec now, class_spec next) — the parse() entry returns spec.py model instances so all consumers share one normalized shape"

requirements-completed: [SPC-01]

# Metrics
duration: 6min
completed: 2026-06-01
---

# Phase 3 Plan 05: SPC-01 Function Spec + Stdlib-Only Docstring Dialect Parser Summary

**Delivered SPC-01 by building its genuinely-new dependency first — a stdlib-only (D-09, zero external library) Google/NumPy/Sphinx Napoleon docstring parser whose three dialect-specific parsers all reduce the SAME documented function to byte-identical normalized `DocstringSection` output (the strongest determinism proof, asserted on a single golden fixture documented three ways) — then the `function_spec` extractor that pairs each function/method's synthesized signature with those normalized sections plus a fixed-keyword (no-NLP) pre/post heuristic marked `source_kind="docstring"`, emitting an inert-but-present FunctionSpec for undocumented members, registered append-only at canonical EVALUATIONS position #6, DET-04-sorted, byte-identical under `PYTHONHASHSEED=random`, with the v0.1.0 parity snapshot regenerated via the script to absorb the now-populated `function_spec` slot while every primitive and diagram slot stays byte-identical.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-01T17:54:54Z
- **Completed:** 2026-06-01T18:00:30Z
- **Tasks:** 2 completed
- **Files:** 6 created, 2 modified
- **Tests:** 365 → 393 passing (+28 new: 16 docstring-parser unit + 8 function_spec unit + 4 SPC-01 acceptance), full suite incl. `tests/parity` green

## Accomplishments

### Task 1 — `_docstring.py` stdlib-only dialect parser (TDD RED → GREEN)
- **`_detect_dialect`** byte-stable order: Sphinx (`:param/:returns/:raises/:type/:rtype`) → NumPy (header + `^-{3,}$` underline) → Google (`Args:/Returns:/Raises:` header line) → none. A docstring with BOTH a Sphinx field and a Google header resolves to Sphinx (first-match-wins, tested).
- **Three dialect parsers** (`_parse_google` / `_parse_numpy` / `_parse_sphinx`) all emit the identical normalized `DocstringSection(kind, name, type_ref, text)` shape: summary = leading prose, params explode one-per-parameter (name + type), returns/raises normalized.
- **Golden fixture** `docstring_dialects.py`: the SAME `Process a payment.` function — same two params (`amount: float`, `method: str`), same return clause, same `ValueError` raise — written Google/NumPy/Sphinx. The test asserts byte-identical `DocstringSection` AND byte-identical pre/post across all three (verified by direct inspection: all three yield identical sections + `PRE=['amount: must be > 0 — ...', 'method: ... required.', 'ValueError: if amount is non-negative.']`, `POST=['bool: True if the charge settled.']`).
- **Fixed-keyword pre/post heuristic** `_derive_conditions`: precondition keywords `('must be','non-negative','> 0','not None','required')` over param text + `Raises:` → documented precondition; `Returns:` → postcondition; all `source_kind="docstring"`. No NLP, no scoring — byte-stable across repeated runs (tested).
- **D-09 grep gate = 0** (no `import docstring_parser`); `git diff pyproject.toml` empty.

### Task 2 — `function_spec.py` (SPC-01) + register #6 + parity regen (TDD RED → GREEN)
- **`function_spec.extract`** pulls the Phase 2 `functions` primitive for FunctionNode shape; for each function/method (class nodes skipped — those are SPC-02/Plan 06) it synthesizes a deterministic `name(params) -> return` signature, feeds the raw docstring (already on FunctionNode) to `_docstring.parse`, and builds `FunctionSpec(node_id, signature, docstring_sections, preconditions, postconditions, source_range)`. Undocumented members emit an inert FunctionSpec (empty sections) so the signature is still visible.
- **3-dialect golden through the real pipeline:** `THREE_DIALECT_SOURCE` (the 3 documented functions + 1 undocumented) run through the full `execute()` path yields identical `docstring_sections` / pre / post for `pay_google` / `pay_numpy` / `pay_sphinx`.
- Registered **append-only at canonical position #6** (`class_diagram`, `sequence_diagram`, `component_diagram`, `package_diagram`, `state_diagram`, **`function_spec`**). Canonical-order dispatch check passes.
- **DET-04** sort-on-exit by `node_id`; byte-identical under `PYTHONHASHSEED=random`.
- **Parity snapshot regenerated** (`scripts/generate_v01_snapshot.py`, never hand-edited): the `function_spec` slot for EXAMPLE_SOURCE went from `[]` to a populated array of 6 FunctionSpec (5 OrderService/OrderModel methods + `process_payment`). Diff verified as a single-line deletion + 89-line insertion entirely within the `function_spec` slot — **all primitive and diagram slots byte-identical**.

## Task Commits

1. **Task 1: SPC-01 stdlib-only docstring dialect parser (_docstring.py)** — `dc5ebb2` (feat)
2. **Task 2: SPC-01 function_spec extractor + register #6 + parity regen** — `5afba25` (feat)

_TDD: Task 1 RED (`_docstring` module missing → ImportError) → GREEN (16 unit tests incl. 3-dialect equivalence). Task 2 RED (`function_spec` module missing → ImportError) → GREEN (12 unit + 4 acceptance), then the parity test (393rd, in `tests/parity`) drove the snapshot regeneration that completed GREEN._

## Verification Results

- `PYTHONPATH=. python -m pytest -q` → **393 passed** (FULL suite incl. `tests/parity/test_snapshot_v01_fixture.py` — the integration-critical parity test).
- `PYTHONHASHSEED=random python -m pytest tests/unit/extractors/test_function_spec.py -q` → **8 passed** (DET-04 byte-stability).
- D-09 grep gate `grep -v '^#' _docstring.py | grep -cE 'import docstring_parser|from docstring_parser'` → **0**; `git diff pyproject.toml` → empty (no dependency added).
- Canonical-order dispatch check → `['class_diagram','sequence_diagram','component_diagram','package_diagram','state_diagram','function_spec']` — prefix-preserving subsequence of the 7-canonical order, `function_spec` at #6.
- `ruff check` + `ruff format --check` → clean on `_docstring.py`, `function_spec.py`, `_dispatch.py`, and all new test files.
- 3-dialect equivalence asserted byte-identical at the parser level AND through the full `execute()` pipeline.
- Parity diff: 1 deletion (`"function_spec": [],`) + 89 insertions, single contiguous hunk at line 638; no `functions`/`call_graph`/`type_deps`/`contracts`/diagram-slot lines in the diff.

## Deviations from Plan

None affecting behavior — plan executed as written. One structural decision within Claude's discretion (plan-allowed): `parse()` returns a 3-tuple `(sections, pre, post)` of `spec.py` model instances rather than a wrapper dataclass — keeps the helper a pure function whose outputs slot directly into `FunctionSpec`. function_spec skips `kind=="class"` FunctionNodes (those belong to SPC-02/Plan 06 class_spec), consistent with the plan's SPC-01 function/method scope.

## Known Stubs

None. `function_spec` is fully wired: signatures come from the `functions` primitive, sections from the stdlib `_docstring` parser, pre/post from the fixed heuristic. The remaining empty CodeContent slot (`class_spec`) is owned by Plan 03-06 and intentionally stays inert until that plan registers its EVALUATIONS entry (which will REUSE `_docstring.parse`).

## Threat Flags

None. The threat register dispositions were satisfied:
- **T-03-11** (Tampering / Layer M integrity): the pre/post heuristic is a FIXED keyword/regex set (no NLP/scoring); DET-04 sort-on-exit; no clock/env/network — same docstring yields same conditions every run (tested via repeated-run byte-stability).
- **T-03-12** (DoS / regex): all detection/parse regexes are anchored and linear (`^\s*:(...)`, `^-{3,}$`, `^(\w+)...`) — no catastrophic-backtracking constructs; docstring size bounded by source file.
- **T-03-SC** (package installs): ZERO installs — D-09 forbids `docstring_parser` or any dep; grep gate = 0; `pyproject.toml` unchanged.

No new network/auth/secret/file-access surface introduced (pure in-process text parsing over `ast.get_docstring` output via `cav.payload`).

## Self-Check: PASSED

- All 6 created files exist on disk.
- Both task commits (`dc5ebb2`, `5afba25`) present in `git log`.
- Full suite (393) green including `tests/parity/test_snapshot_v01_fixture.py`; parity snapshot regenerated (function_spec slot only) — `git status` clean on the snapshot.
- D-09 grep gate = 0; no external dependency added.
