---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 05
subsystem: adapters
tags: [pyright, subprocess, adapter, determinism, fail-loudly]
requires: [ARC-03, DET-05]  # Phase 1 SubprocessAdapter ABC + run_subprocess + _paths.get_module_name
provides: [AST-03, DET-03, DET-05, TRC-02, TRC-03]  # PyrightAdapter + PyrightOutput typed model
affects: [02-06]  # Plan 02-06 type_deps extractor consumes PyrightOutput.diagnostics for `resolved` flag
tech-stack:
  added: []  # pyright[nodejs]==1.1.409 already declared in Phase 1 pyproject.toml
  patterns: [SubprocessAdapter-subclass, caller-agnostic-tmpdir-IO, fail-loudly-RuntimeError, Pydantic-v2-extra-forbid]
key-files:
  created:
    - lib_code_parser/adapters/pyright.py
    - tests/unit/test_pyright_adapter.py
  modified: []
decisions:
  - "PyrightAdapter.analyze(raw_content, path) is an adapter-specific public entry point distinct from SubprocessAdapter.execute() — execute()'s signature carries no raw bytes, so analyze() owns the tmpdir lifecycle (D-05 caller-agnostic I/O)"
  - "parse_output widens the ABC signature with keyword-only tmpdir/caller_path for D-07 canonicalization; execute() never passes them (analyze() calls parse_output directly)"
  - "Only generalDiagnostics[].{file, severity, message, rule, range.start.line, range.end.line} retained; version/time/summary discarded per RESEARCH §2.1 empirical finding (pyright --outputjson carries no resolved-type info)"
metrics:
  duration: ~25m (including cwd-drift recovery)
  completed: 2026-05-31
---

# Phase 02 Plan 05: Pyright Adapter Summary

PyrightAdapter (SubprocessAdapter subclass) runs `pyright --outputjson` on caller bytes via an internal tempfile.TemporaryDirectory, locks DET-03 env vars (PYRIGHT_PYTHON_FORCE_VERSION=1.1.409 + PYRIGHT_PYTHON_IGNORE_WARNINGS=1), isolates the caller's pyproject.toml with a tmpdir pyrightconfig.json + `-p`, and parses only generalDiagnostics into a typed Pydantic v2 PyrightOutput model with fail-loudly RuntimeError on every error path.

## What Was Built

- **`lib_code_parser/adapters/pyright.py`** — 3 classes (`PyrightAdapter`, `PyrightOutput`, `PyrightDiagnostic`) + 3 module constants:
  - `PyrightAdapter.__init__(python_version="3.12")`
  - `tool_argv(target_path)` → `["pyright", "--outputjson", "--pythonversion", <ver>, "-p", "<tmpdir>/pyrightconfig.json", target_path]` (D-08 verbatim, no other flags)
  - `parse_output(stdout, stderr, returncode, *, tmpdir="", caller_path="")` → D-06 fail-loudly (returncode not in {0,1} → RuntimeError; JSONDecodeError → RuntimeError raise-from) + D-07 forward-slash normalize + tmpdir-prefix strip to caller_path
  - `analyze(raw_content, path)` → internal tmpdir lifecycle (D-05), bytes write, config write, run_subprocess with `_PYRIGHT_DET_ENV`, TimeoutExpired/FileNotFoundError → RuntimeError raise-from
  - `_PYRIGHT_DET_ENV`, `_PYRIGHT_CONFIG_JSON` (`{"include": ["."], "reportMissingImports": "error"}`), `_OK_RETURNCODES = frozenset({0, 1})`
  - `PyrightDiagnostic` / `PyrightOutput` — Pydantic v2 `ConfigDict(extra="forbid")`
- **`tests/unit/test_pyright_adapter.py`** — 13 mock/unit tests + 1 env-dependent smoke test (14 total).

`lib_code_parser/adapters/__init__.py` barrel re-export of PyrightAdapter is intentionally deferred to Plan 02-07 (Wave 3 closer owns barrel + executor edits), per the plan's action note. `tests/unit/adapters/__init__.py` already existed from Phase 1 (no change needed).

## Test Results (pytest)

`pytest tests/unit/test_pyright_adapter.py` — **14 passed** (warm-pyright run; smoke test executed). On a cold run the smoke test (`test_real_pyright_analyzes_clean_python`) is `skipif`-skipped when `pyright --version` exceeds the 10s warm-up timeout, so the CI-deterministic floor is 13 passed + 1 skipped — neither outcome fails the suite.

| Test | Purpose | Status |
|------|---------|--------|
| test_tool_argv_includes_outputjson_pythonversion_p_target | D-08 argv verbatim | PASS |
| test_det_03_env_var_set (VALIDATION.md required) | DET-03 both env keys via run_subprocess extra_env | PASS |
| test_pyrightconfig_json_written_to_tmpdir | Pitfall 3 config isolation | PASS |
| test_target_file_written_with_module_name_basename | get_module_name basename in tmpdir | PASS |
| test_parse_output_returncode_2_raises_runtime_error | D-06 returncode path | PASS |
| test_parse_output_returncode_0_or_1_accepted | both clean/error returncodes valid | PASS |
| test_parse_output_invalid_json_raises_runtime_error | D-06 JSONDecodeError + __cause__ chain | PASS |
| test_parse_output_strips_tmpdir_prefix_in_file_path | D-07 tmpdir-strip to caller_path | PASS |
| test_parse_output_forward_slash_normalizes_backslash_paths | D-07 backslash normalize (no prefix match) | PASS |
| test_parse_output_discards_unused_fields | extra="forbid" drops time/summary | PASS |
| test_timeout_raises_runtime_error | D-06 TimeoutExpired path | PASS |
| test_file_not_found_raises_runtime_error | D-06 install-failure path | PASS |
| test_real_pyright_analyzes_clean_python (smoke) | real pyright, clean Python = 0 diagnostics | PASS (warm) / SKIP (cold) |
| test_models_are_pydantic_with_forbid | SCH-02 extra="forbid" sanity | PASS |

## Grep Gate Evidence

`lib_code_parser/adapters/pyright.py`:
- PYRIGHT_PYTHON_FORCE_VERSION = 2 (≥2) — DET-03 constant + extra_env use
- `"1.1.409"` = 1 (≥1) — DET-03 pin
- PYRIGHT_PYTHON_IGNORE_WARNINGS = 2 (≥1) — RESEARCH §2.4 suppression
- TemporaryDirectory = 3 (≥1) — D-05 internal tmpdir
- `raise RuntimeError` = 4 (≥3) — D-06 fail-loudly (returncode / JSON / timeout / FileNotFound)
- `ast.parse` = 0 (==0) — adapter never parses
- `Implements: AST-03` = 1 (TRC-02); `Traces: AST-03` = 1 (TRC-03)
- `"--outputjson"` = 1, `"--pythonversion"` = 1, `"-p"` = 1 (D-08 / Pitfall 3)
- `extra="forbid"` = 2 (≥2) — both models (SCH-02)
- `pyrightconfig.json` = 4 (≥2) — Pitfall 3 mitigation

`tests/unit/test_pyright_adapter.py`: `def test_det_03_env_var_set` = 1, FORCE_VERSION ≥1, IGNORE_WARNINGS ≥1, TimeoutExpired = 3, JSONDecodeError = 3, RuntimeError = 8.

## Model Structure

```
PyrightDiagnostic fields: ['file', 'severity', 'message', 'rule', 'start_line', 'end_line']
PyrightOutput fields:     ['version', 'diagnostics']
```
Example dump (reportMissingImports diagnostic with caller_path canonicalized):
```json
{
  "version": "1.1.409",
  "diagnostics": [
    {"file": "src/foo.py", "severity": "error",
     "message": "Import \"missing_pkg\" could not be resolved",
     "rule": "reportMissingImports", "start_line": 0, "end_line": 0}
  ]
}
```

## Real Pyright Smoke

Installed pyright version: **1.1.408** (CI runner; pin target is 1.1.409 — version mismatch does not affect this plan's grep/behavior gates, which assert the env-pin string, not the runner version). Smoke test analyzed `def foo() -> int: return 1` → `version != ""` and `len(diagnostics) == 0`. Result: PASS on warm invocation; SKIP on cold invocation (first `pyright --version` Node cold-start can exceed the 10s `_has_pyright` timeout).

## Baseline Parity (v0.1.0)

`pytest tests/parity/ tests/acceptance/test_fr01_function_extraction.py test_fr02_callgraph.py test_fr03_type_deps.py test_fr05_trace_tags.py test_fr06_disabled.py` → **61 passed** (test_fr04_contracts.py intentionally excluded — broken by Plan 02-04). No regression.

`ruff check lib_code_parser/adapters/pyright.py tests/unit/test_pyright_adapter.py` → All checks passed.

## Deviations from Plan

### Auto-fixed Issues — None affecting deliverables

The implementation followed the plan's RESEARCH §Code Examples §例 2 template verbatim. No Rule 1/2/3 code deviations were required.

### Execution-environment recovery (worktree cwd-drift, #3099)

- **Found during:** Task 1 GREEN commit attempt.
- **Issue:** The orchestrator-supplied absolute paths in `<files_to_read>` / `<execution_context>` pointed at the **main repo root** (`.../lib-code-parser/`), not the worktree root (`.../lib-code-parser/.claude/worktrees/agent-a61edec7c34d33a7c/`). All file Writes and the first `test(02-05)` commit (`471d27f`) therefore landed in the main repo on `master`, not in the worktree.
- **Fix:** (1) Copied both created files from main repo into the worktree. (2) On `master`, `git reset --soft HEAD~1` to undo my stray `471d27f` commit (kept all concurrent agents' working-tree changes intact — NO hard reset, per #2924/#2075 destructive-git prohibition), then removed my two stray untracked files. (3) Re-ran the full TDD gate sequence inside the worktree: RED commit `4fdc5fa` (test), GREEN commit `5d9a0c4` (impl).
- **Files modified:** none beyond plan deliverables; recovery only relocated work to the correct git tree.
- **Note for future executors:** when a worktree path differs from the supplied absolute paths, derive `WT_ROOT` from `git rev-parse --show-toplevel` *inside the worktree* and use paths relative to it (worktree-path-safety #3099).

## TDD Gate Compliance

- RED gate present: `4fdc5fa test(02-05): add failing tests for PyrightAdapter` (verified failing with ModuleNotFoundError before implementation).
- GREEN gate present: `5d9a0c4 feat(02-05): implement PyrightAdapter ...` after RED.
- No REFACTOR commit needed (implementation passed clean on first GREEN).

## Known Stubs

None. PyrightAdapter is fully wired: `analyze()` runs real pyright, `parse_output()` extracts real diagnostics. The deferred `__init__.py` barrel re-export is an intentional cross-plan boundary (Plan 02-07 owns it), not a stub.

## Self-Check

(appended below)
