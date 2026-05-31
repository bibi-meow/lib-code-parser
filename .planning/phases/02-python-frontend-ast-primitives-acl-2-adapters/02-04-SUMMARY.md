---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 04
subsystem: contracts-extractor
tags: [pydantic, ast, contracts, source-kind, alias-resolution, D-12]
requires:
  - "models/infrastructure/cav.py::CAV (Phase 1)"
  - "models/infrastructure/config.py::ParserConfig (Phase 1)"
  - "_paths.py::get_module_name (Phase 1 ARC-04)"
provides:
  - "models/primitives/contracts.py::ContractEntry (per-entry source_kind discriminator)"
  - "models/primitives/contracts.py::ContractInfo (entries list + computed_field helpers)"
  - "extractors/primitives/contracts.py::extract(cav, config) -> dict[str, ContractInfo]"
affects:
  - "Plan 02-06 (executor dispatch — consumes new entries structure)"
  - "Plan 02-07 (Wave 3 closer — rewrites test_fr04_contracts.py)"
tech-stack:
  added: []
  patterns: ["pydantic v2 @computed_field backward-compat helpers", "pydantic-scoped alias resolution", "per-entry discriminator (D-12 β)"]
key-files:
  created:
    - "lib_code_parser/extractors/primitives/contracts.py"
    - "tests/unit/extractors/__init__.py"
    - "tests/unit/extractors/test_contracts_extractor.py"
    - "tests/unit/models/test_contracts_model.py"
  modified:
    - "lib_code_parser/models/primitives/contracts.py"
    - "lib_code_parser/models/primitives/__init__.py"
    - "tests/unit/models/test_primitives_extra_forbid.py"
decisions:
  - "Provenance restriction stricter than plan skeleton: classify only when local name resolves via pydantic-scoped alias map OR pydantic.X attribute form (satisfies T-02-19 for bare non-pydantic imports, which the plan's literal aliases.get(raw, raw) fallback would have false-positived)"
  - "No tests/unit/models/test_contracts.py existed to git rm; ContractInfo shape assertions lived in test_primitives_extra_forbid.py — updated that file's source_kind-literal test to target ContractEntry instead"
metrics:
  duration: "~25 min"
  completed: 2026-05-31
  tasks: 2
  files: 7
---

# Phase 2 Plan 04: Contracts Extractor Summary

D-12 (β) restructure of ContractInfo to a per-entry ContractEntry list, plus a new pure-CAV contracts extractor that fixes v0.1.0 bugs C3 (alias imports) and C4 (@root_validator) and splits __post_init__ into source_kind=dataclass_post_init.

## What Was Built

### Task 1 — ContractInfo restructure (commit 0c1c06e)
- `ContractEntry` sub-model: `(name, source_kind, kind, decorator_name, line_no)` with closed `SourceKind` Literal (4 values) + `ContractKind` Literal (precondition/invariant/postcondition) + `extra="forbid"` (SCH-02).
- `ContractInfo.entries: list[ContractEntry]` is canonical storage. v0.1.0 `preconditions`/`invariants`/`postconditions` are now read-only `@computed_field` helpers deriving `list[str]` from `entries` by `kind` (backward-compat).
- Exported `ContractEntry`/`ContractKind`/`SourceKind` from `models/primitives/__init__.py`.
- `FunctionNode.contracts` default factory (`ContractInfo()` no-args) preserved (T-02-16).

### Task 2 — Pure-CAV extractor (commit a4181d8)
- `extractors/primitives/contracts.py::extract(cav, config) -> dict[str, ContractInfo]`.
- `_DECORATOR_TO_SOURCE_KIND` 4-value mapping (D-11): validator/field_validator → precondition; model_validator/root_validator → invariant/pydantic_model_validator.
- `_resolve_decorator_aliases` walks pydantic-scoped `ImportFrom` to build a `{local: canonical}` map (C3 fix).
- `__post_init__` detected by method-name only → `dataclass_post_init` (ROADMAP SC-3).
- D-13 mixed case auto-supported via per-entry granularity.

## 1. pytest Output (Plan 02-04 contribution)

```
tests/unit/models/test_contracts_model.py ............ (12 model tests)
tests/unit/extractors/test_contracts_extractor.py ..... (12 extractor tests)
22 passed (combined plan-deliverable verify)
```

Phase 1 baseline (excluding intentional break): `tests/acceptance/test_fr01/02/03/05/06 + tests/parity/` = **61 passed**.

**Intentionally failing (deferred — see deferred-items.md):** 13 tests rooted in v0.1.0 `contract_extractor.py:69` constructing `ContractInfo(preconditions=..., invariants=...)` (now removed kwargs → ValidationError):
- `tests/acceptance/test_fr04_contracts.py` (6) — plan-sanctioned, Plan 02-07 rewrites
- `tests/unit/test_contract_extractor.py` (6) — v0.1.0 extractor unit (old module)
- `tests/unit/test_executor.py::TestExecutorContracts::test_contracts_applied_when_enabled` (1) — Plan 02-06 rewires executor

## 2. ContractInfo Restructure Diff (Case A)

Before (v0.1.0 α): single class-level `source_kind` + 3× `list[str] = Field(default_factory=list)`.
After (D-12 β): `entries: list[ContractEntry]` + 3× `@computed_field` helpers. `grep -c "preconditions: list[str] = Field"` → **0**; `grep -c "class ContractEntry"` → **1**; `grep -c "entries: list[ContractEntry]"` → **1**; `grep -c "@computed_field"` → **5** (includes property decorators).

## 3. v0.1.0 C3 / C4 Bug-Fix Evidence

- **C3 (alias)** — `test_c3_alias_resolution_fixes_v01_bug`: `from pydantic import field_validator as fv; @fv("x")` → `source_kind=pydantic_field_validator`, `decorator_name=field_validator`. PASS.
- **C4 (@root_validator)** — `test_c4_root_validator_recognized`: `@root_validator` → `source_kind=pydantic_model_validator`, `kind=invariant`, `decorator_name=root_validator`. PASS.
- **C7 (__post_init__ split)** — `test_c7_post_init_in_plain_class_gets_dataclass_post_init`: asserts `source_kind == "dataclass_post_init"` and `!= "pydantic_validator"`. PASS (ROADMAP SC-3 invariant locked).

## 4. Grep Gate Results

| Gate | File | Expected | Actual |
|------|------|----------|--------|
| AST-05 (no ast.parse) | extractors/primitives/contracts.py | 0 | 0 |
| ARC-04 (no local module_name def) | extractors/primitives/contracts.py | 0 | 0 |
| ARC-04 (_paths import) | extractors/primitives/contracts.py | 1 | 1 |
| C4 (root_validator) | extractors/primitives/contracts.py | >=1 | 5 |
| C3 (_resolve_decorator_aliases) | extractors/primitives/contracts.py | >=2 | 3 |
| C7 (dataclass_post_init) | extractors/primitives/contracts.py | >=1 | 2 |
| TRC-02 (Implements: AST-04) | extractors/primitives/contracts.py | 1 | 1 |
| TRC-03 (Traces: AST-04) | extractors/primitives/contracts.py | >=1 | 1 |
| ruff check (all 4 plan files) | — | exit 0 | All checks passed |

## 5. FunctionNode.contracts Default Factory Compatibility (T-02-16)

`FunctionNode(node_id="x", kind="function", source_range=SourceRange(0,0)).contracts` constructs an empty `ContractInfo()` (no-args) with `entries == []` and `preconditions == []`. Verified by `test_function_node_default_contracts_is_empty_contract_info` (passes) and acceptance one-liner (exit 0).

## Deviations from Plan

### [Rule 1 - Plan correctness] Stricter provenance restriction than plan skeleton
- **Found during:** Task 2.
- **Issue:** The plan's `_classify_decorator` skeleton (`canonical = aliases.get(raw, raw)`) would classify a bare `from other_lib import field_validator; @field_validator` as pydantic (false positive), contradicting plan test #9 `test_non_pydantic_alias_not_classified` AND threat T-02-19.
- **Fix:** Classify only when the local name is in the pydantic-scoped alias map OR the decorator is a `pydantic.X` attribute form. Bare non-pydantic names are skipped. This satisfies both the test intent and T-02-19.
- **Files:** lib_code_parser/extractors/primitives/contracts.py (`_classify_decorator`, `_is_attribute_form`).
- **Commit:** a4181d8.

### [Rule 3 - Plan assumption correction] No test_contracts.py to delete
- **Found during:** Task 1.
- **Issue:** Plan instructed `git rm tests/unit/models/test_contracts.py`, but that file never existed. ContractInfo shape assertions lived in `tests/unit/models/test_primitives_extra_forbid.py::test_contract_info_source_kind_literal`.
- **Fix:** Updated that test in place to assert the closed Literal on `ContractEntry` (where `source_kind` now lives) instead of the removed `ContractInfo.source_kind`.
- **Files:** tests/unit/models/test_primitives_extra_forbid.py.
- **Commit:** 0c1c06e.

### Worktree path-safety recovery (#3099)
- Initial Edit/Write calls landed in the MAIN repo (absolute paths) instead of the worktree (separate checkout). Recovered by copying edited files into the worktree, then `git checkout` to restore the 3 tracked files in the main repo and removing the stray untracked test there. Other parallel agents' untracked files were left untouched. All subsequent work performed inside the worktree.

## Deferred Issues

13 v0.1.0-dependent test failures (rooted in `contract_extractor.py:69`) logged in `deferred-items.md`. Owned by Plan 02-06 (executor) + Plan 02-07 (test_fr04 rewrite). Not fixed here per scope boundary (files outside Plan 02-04's `files_modified`).

## Success Criteria Status

- [x] ROADMAP Phase 2 SC-3 (source_kind 4 values per validator entry)
- [x] ROADMAP Phase 2 SC-4 (contracts extractor isolated)
- [x] v0.1.0 C3 / C4 bugs locked-fixed in unit tests
- [x] D-13 mixed case auto-supported
- [x] TRC-02 / TRC-03 docstring conventions established

## Self-Check

(appended below after verification)
