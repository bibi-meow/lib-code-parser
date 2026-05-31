---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 07
subsystem: parser-core
tags: [clean-break, parity, barrel, snapshot, traceability]
requires: [02-01, 02-02, 02-03, 02-04, 02-05, 02-06]
provides:
  - typed-barrel-parserconfig
  - pyright-adapter-public-surface
  - v01-fixture-snapshot-baseline
  - trc-02-docstring-gate
affects:
  - lib_code_parser/__init__.py
  - lib_code_parser/models/__init__.py
  - lib_code_parser/adapters/__init__.py
  - tests/acceptance
  - tests/parity
tech-stack:
  added: []
  patterns: [dispatch-driven-executor, byte-identical-snapshot, grep-gate]
key-files:
  created:
    - tests/parity/test_trc_02_docstring.py
    - tests/parity/test_snapshot_v01_fixture.py
    - tests/parity/fixtures/v01_snapshot.json
    - scripts/generate_v01_snapshot.py
  modified:
    - lib_code_parser/__init__.py
    - lib_code_parser/models/__init__.py
    - lib_code_parser/adapters/__init__.py
    - tests/acceptance/test_fr01_function_extraction.py
    - tests/acceptance/test_fr02_callgraph.py
    - tests/acceptance/test_fr03_type_deps.py
    - tests/acceptance/test_fr04_contracts.py
    - tests/acceptance/test_fr05_trace_tags.py
    - tests/acceptance/test_fr06_disabled.py
    - tests/parity/test_v01_v02_compat.py
  deleted:
    - lib_code_parser/ast_extractor.py
    - lib_code_parser/callgraph_builder.py
    - lib_code_parser/contract_extractor.py
    - lib_code_parser/type_dep_builder.py
    - tests/unit/test_ast_extractor.py
    - tests/unit/test_callgraph_builder.py
    - tests/unit/test_type_dep_builder.py
    - tests/unit/test_contract_extractor.py
    - tests/unit/test_executor.py
decisions:
  - "D-01 clean break: legacy v0.1.0 4 source modules + 5 legacy unit tests deleted (not shimmed)"
  - "D-02 explicit break: barrel ParserConfig graduated to typed variant; dict-style params={} now raises ValidationError"
  - "D-04 parity redesign: stub-JSON byte-identical parity dropped, replaced by shipped EXAMPLE_SOURCE snapshot"
metrics:
  duration: ~25 min
  completed: 2026-05-31
---

# Phase 2 Plan 07: Legacy Deletion + Parity Redesign Summary

D-01 clean break completed — legacy v0.1.0 extractor modules deleted, barrel `ParserConfig` graduated to the typed v0.2.0 variant, PyrightAdapter family exposed on the lib surface, and the full Phase 2 test suite is green (235 passed, 0 failures, 0 skips) with the AST-05 one-parse gate, TRC-02/03 docstring gates, and the new D-04 snapshot all passing.

## What Was Built

This is the Wave 3 sequential closer for Phase 2. Three atomic commits:

| Task | Commit | What |
|------|--------|------|
| 1 | `4f005c8` | Delete 4 legacy source + 5 legacy unit tests; graduate typed barrel ParserConfig; expose PyrightAdapter family; rewrite 6 acceptance tests |
| 2 | `923166f` | D-04 parity test redesign (`test_v01_v02_compat.py`) |
| 3 | `d6aa2e8` | New TRC-02 docstring gate + D-04 v0.1.0 fixture snapshot + fixture + generator script |

## pytest Result (Phase 2 final full suite)

```
python -m pytest -q
235 passed in 68.45s
```

- 0 failures (down from 24 legacy v0.1.0 failures at plan start).
- 0 skips. Note: pyright `1.1.409` is installed in this environment, so the
  `_has_pyright()`-guarded acceptance (`test_fr03`) and snapshot tests RAN
  (not skipped). In a pyright-absent environment those modules skip cleanly via
  `pytestmark = pytest.mark.skipif(...)` — acceptable per the plan's
  cold-start/real-pyright skip allowance.

## Deleted Legacy Files (8 source/test files)

**4 legacy source modules** (replaced by `lib_code_parser/extractors/primitives/*`):
- `lib_code_parser/ast_extractor.py`
- `lib_code_parser/callgraph_builder.py`
- `lib_code_parser/contract_extractor.py`
- `lib_code_parser/type_dep_builder.py`

**5 legacy v0.1.0 unit tests** (imported the deleted modules or the dict-style ParserConfig):
- `tests/unit/test_ast_extractor.py` → covered by `tests/unit/extractors/test_functions_extractor.py`
- `tests/unit/test_callgraph_builder.py` → covered by `tests/unit/extractors/test_callgraph_extractor.py`
- `tests/unit/test_type_dep_builder.py` → covered by `tests/unit/extractors/test_type_deps_extractor.py`
- `tests/unit/test_contract_extractor.py` → covered by `tests/unit/extractors/test_contracts_extractor.py`
- `tests/unit/test_executor.py` → covered by `tests/unit/test_executor_dispatch.py`

Verification: `python -c "...any(Path('lib_code_parser/{n}.py').exists()...)"` exit 0 (all absent);
`grep -rn --include="*.py" "from lib_code_parser.(ast_extractor|callgraph_builder|contract_extractor|type_dep_builder)" tests/ lib_code_parser/` → 0 matches.

## Barrel ParserConfig Graduation (D-01 / D-02)

- The v0.1.0 parity stub class (`class ParserConfig(BaseModel): params: dict[str, object]`)
  in `lib_code_parser/models/__init__.py` is **deleted**.
- The barrel now re-exports the typed `lib_code_parser.models.infrastructure.config.ParserConfig`
  (`extra="forbid"` + typed `language` / `extract_contracts` / `python_version` / `compile_args`).
- **Identity** verified: `lib_code_parser.ParserConfig is lib_code_parser.models.infrastructure.config.ParserConfig` (T-02-36 mitigation).
- **Explicit break** verified: `ParserConfig(artifact_type="code", executor_lib="lib_code_parser", params={"language":"python"})` raises `ValidationError` (D-02).
- `lib_code_parser.__all__` is now **22 names** (13 v0.1.0 + 6 Phase 1 v0.2.0 + 3 Phase 2 v0.2.0).
- `PyrightAdapter` / `PyrightOutput` / `PyrightDiagnostic` importable from both the
  top-level barrel and `lib_code_parser.adapters`.

## D-04 Parity Test Redesign (`test_v01_v02_compat.py`, 12 tests pass)

**Dropped (3):**
- `test_normalized_artifact_json_byte_identical` — superseded by the shipped EXAMPLE_SOURCE snapshot.
- `test_executor_runs_on_example_source` — the legacy `b"def foo(): pass"` smoke is now covered end-to-end by the snapshot.
- `test_parser_config_unknown_field_raises` — the typed contract is now asserted at the barrel (below), not only at the infrastructure path.

**Added (4):**
- `test_v02_phase2_surface_present` — PyrightAdapter / PyrightOutput / PyrightDiagnostic importability.
- `test_parser_config_typed_at_barrel_rejects_unknown` — barrel ParserConfig rejects unknown fields.
- `test_parser_config_barrel_is_typed_identity` — barrel is the typed object (T-02-36).
- `test_v01_params_dict_explicit_break` — D-02 dict-style API raises.

(Net +1 vs the plan's "11" target because the identity test was split out to explicitly cover T-02-36; the remaining preserved tests — surface intact, Phase 1 surface, version bump, no-duplication gate, D-06 generic parity ×2, EdgeKind closed Literal, package-not-module — are unchanged.)

## Snapshot Fixture (`tests/parity/fixtures/v01_snapshot.json`)

- Generated by `scripts/generate_v01_snapshot.py` running the typed ParserConfig +
  dispatch executor over `conftest.EXAMPLE_SOURCE` with real pyright.
- Size: **10673 bytes** on disk (10251 chars of JSON content).
- Contains the full `NormalizedArtifact[CodeContent]` dump: `artifact_id`, `content.functions`
  (FunctionNode with node_id/kind/params/return_type/docstring/trace_tags/source_range/contracts),
  `content.call_graph` (DET-04-sorted edges), `content.type_deps` (with pyright-resolved `resolved` flags),
  `content.contracts` (ContractEntry per-entry source_kind + computed-field preconditions/invariants).
- `test_snapshot_v01_fixture.py`: byte-identical comparison + 3-run determinism gate.

## ROADMAP Phase 2 Success Criteria

- [x] **SC-1** — `CodeParserExecutor().execute(config, raw, path)` yields `FunctionNode` entries with kind/params/return_type/docstring/trace_tags/source_range; single `ast.parse()` per file (AST-05 gate green). Verified via `test_fr01` + `test_ast_05_one_parse.py`.
- [x] **SC-2** — `call_graph` populated by the internal extractor with DET-04 lex-sorted `(caller, callee)` edges; `type_deps` populated via the pyright adapter pinned to `1.1.409`. Verified via `test_fr02` (incl. `test_edges_det04_sorted`) + `test_fr03` (resolved flags) + DET-03 grep gate.
- [x] **SC-3** — per-entry `source_kind ∈ {pydantic_validator, pydantic_model_validator, pydantic_field_validator, dataclass_post_init}`; `__post_init__` no longer unconditionally Pydantic. Verified via `test_fr04` per-entry assertions.
- [x] **SC-4** — each extractor importable/callable in isolation; each module declares its REQ-IDs; `Traces:` regex parity. Verified via `test_trc_02_docstring.py` (TRC-02 Implements + TRC-03 Traces) + `test_fr05` + the isolated `tests/unit/extractors/test_*_extractor.py` suite.

## Phase 2 Requirements Coverage (8)

| REQ | Description | Covered by |
|-----|-------------|-----------|
| AST-01 | FunctionNode extraction | `test_fr01`, functions extractor unit |
| AST-02 | Internal call graph | `test_fr02`, callgraph extractor unit |
| AST-03 | TypeDep (import + annotation) | `test_fr03`, type_deps extractor unit |
| AST-04 | Pydantic / dataclass contract discrimination | `test_fr04`, contracts extractor unit |
| AST-05 | One parse per file (CAV) | `test_ast_05_one_parse.py` |
| DET-03 | pyright pinned 1.1.409 / forward-slash canonicalization | DET-03 grep gate, pyright adapter unit |
| TRC-02 | Each extractor declares `Implements: REQ-ID` | `test_trc_02_docstring.py::test_all_extractor_modules_declare_implements_req_id` |
| TRC-03 | `Traces: REQ-ID` verbatim parity | `test_trc_02_docstring.py::test_all_extractor_modules_have_traces_line`, `test_fr05` |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Plan assumption] Deleted `tests/unit/test_executor.py` (legacy v0.1.0 executor unit) in Task 1**
- **Found during:** Task 1 (it was flagged in wave_context, not in the plan's explicit action list, which named only the 4 contract/extractor unit files).
- **Issue:** `test_executor.py` uses the v0.1.0 dict-style `ParserConfig(params={...})` and the v0.1.0 executor body. After the typed-barrel graduation it raised on every test (9 failures). The new dispatch executor is already covered by `tests/unit/test_executor_dispatch.py`.
- **Fix:** `git rm tests/unit/test_executor.py` together with the other 4 legacy unit files in the Task 1 commit. No remaining test imports a deleted module.
- **Commit:** `4f005c8`

**2. [Rule 3 - Sequencing] Folded the barrel-graduation source change (3 files) into the Task 1 commit**
- **Found during:** Task 1 verification — the rewritten acceptance tests (typed ParserConfig) cannot pass until the barrel `ParserConfig` is the typed variant, which the plan placed in Task 2's behavior. To keep every commit's tree coherent (no committed-broken state), the 3 source edits (`models/__init__.py`, `__init__.py`, `adapters/__init__.py`) ship in Task 1. Task 2 then carries only the parity-test redesign.
- **Fix:** Source graduation in `4f005c8`; parity tests in `923166f`. End result is identical to the plan's intent; only the commit boundary shifted.
- **Commit:** `4f005c8`

**3. [Rule 1 - Bug] TRC-02/03 grep gate used PCRE `\d` which GNU grep ERE does not support**
- **Found during:** Task 3 (RED — `test_all_extractor_modules_have_traces_line` failed with empty matches despite the lines existing).
- **Issue:** GNU grep `3.0` ERE (`-E`) does not interpret `\d`; the pattern matched nothing.
- **Fix:** Replaced `\d` with POSIX `[0-9]` and `\s` with `[[:space:]]` in `test_trc_02_docstring.py`.
- **Commit:** `d6aa2e8`

**4. [Rule 1 - Bug] Acceptance-test docstring text tripped the legacy-import grep gate**
- **Found during:** Task 1 verification — `grep ... "from lib_code_parser.ast_extractor"` matched a prose example inside the `test_fr01` module docstring.
- **Fix:** Rephrased the docstring to "No legacy direct-extractor imports remain." `.py`-scoped grep now returns 0 matches. (The `.pyc` match was a stale build artifact, irrelevant to source.)
- **Commit:** `4f005c8`

## SCH-02 `extra="forbid"` Compatibility Rationale

- `ContractEntry` and `TypeDep` both declare `model_config = ConfigDict(extra="forbid")`. The Phase 2 additive fields (`ContractEntry.source_kind/kind/decorator_name/line_no`; `TypeDep.resolved/source_line`) are declared as explicit typed fields, so they do **not** trip `extra="forbid"` — additive typed fields are part of the schema, not "extra" input.
- `ContractInfo.preconditions/invariants/postconditions` are Pydantic v2 `@computed_field` read-only properties. They are included in `model_dump_json()` in **declaration order** (not alphabetical), which is stable as long as the declaration order in `contracts.py` is unchanged. The shipped `v01_snapshot.json` locks this order; any PR reordering computed fields will fail the snapshot test and must update the fixture with a documented rationale (T-02-40 accept disposition).

## Threat Surface Scan

No new security-relevant surface introduced beyond the plan's `<threat_model>`. The
deletion of legacy modules narrows the import surface (T-02-38 accept). The fixture
generator (`scripts/generate_v01_snapshot.py`) uses only Phase 2 deliverables + stdlib
(T-02-41 accept). No new network endpoints, auth paths, or trust-boundary schema changes.

## Known Stubs

None. All acceptance/parity tests are wired to the live typed-ParserConfig dispatch executor and the real pyright adapter; no placeholder data sources remain.

## Phase 3 Entry Condition

Plan 02-07 complete = **Phase 2 closed**. The v0.2.0 baseline is fixed: no legacy modules,
typed barrel, snapshot test established, full suite green. `/gsd:plan-phase` for Phase 3
(Python Diagram + Spec Extractors) may proceed.

## Self-Check: PASSED

- Created files exist: `tests/parity/test_trc_02_docstring.py`, `tests/parity/test_snapshot_v01_fixture.py`, `tests/parity/fixtures/v01_snapshot.json`, `scripts/generate_v01_snapshot.py` — all FOUND.
- Commits exist: `4f005c8`, `923166f`, `d6aa2e8` — all in `git log`.
- Legacy modules absent; legacy import grep returns 0; full `pytest -q` = 235 passed / 0 failed.
