# Deferred Items — Phase 02

Out-of-scope discoveries logged during execution (not fixed by the discovering plan).

## From Plan 02-04 (contracts extractor / ContractInfo restructure)

The D-12 (β) ContractInfo restructure (Plan 02-04 Task 1) removed the v0.1.0
constructor kwargs `preconditions` / `invariants` / `postconditions` (now
read-only `@computed_field` helpers). The v0.1.0 `lib_code_parser/contract_extractor.py`
(line 69) still constructs `ContractInfo(preconditions=..., invariants=...)`,
which now raises `ValidationError` (extra_forbidden).

This breaks 13 v0.1.0-dependent tests that exercise the OLD extractor / executor
path. These files are NOT in Plan 02-04's `files_modified` and are owned by:
- **Plan 02-06** (executor rewrite as dispatch-driven, consuming the new
  `entries` structure) — fixes `executor.py` + `test_executor.py`
- **Plan 02-07** (Wave 3 closer, D-04) — rewrites `test_fr04_contracts.py`

Failing tests (expected, deferred — do NOT fix in Plan 02-04):
- tests/acceptance/test_fr04_contracts.py (6 tests) — plan-sanctioned intentional break
- tests/unit/test_contract_extractor.py (6 tests) — v0.1.0 extractor unit, old module
- tests/unit/test_executor.py::TestExecutorContracts::test_contracts_applied_when_enabled (1 test)

Root cause is a single construction site (`contract_extractor.py:69`). When
Plan 02-06 rewires the executor to call `extractors/primitives/contracts.extract`
(the new pure-CAV extractor) the v0.1.0 `contract_extractor.py` becomes dead
code and these tests are rewritten/removed.
