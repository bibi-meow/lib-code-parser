---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 02
subsystem: extractors/primitives
tags: [ast, functions, cav, trace-tags, parity]
requires:
  - "CAV model (lib_code_parser.models.infrastructure.cav.CAV) — Phase 1"
  - "ParserConfig model (lib_code_parser.models.infrastructure.config) — Phase 1"
  - "FunctionNode/ParamInfo/SourceRange/TraceTag models — Phase 1"
  - "get_module_name single source (lib_code_parser._paths) — Phase 1"
provides:
  - "lib_code_parser.extractors.primitives.functions.extract — pure-CAV FunctionNode extractor (AST-01)"
  - "lib_code_parser.frontends.python.build_cav — 1-parse Python Frontend (AST-05); ALSO produced by Plan 02-01 (same wave) — identical content"
affects:
  - "Plan 02-06 (_dispatch registration of PRIMITIVES['functions'] + executor rewrite)"
  - "Plan 02-07 (acceptance test signature rewrite)"
tech-stack:
  added: []
  patterns:
    - "CAV consumer signature extract(cav, config) -> list[FunctionNode]"
    - "isinstance(tree, ast.Module) fail-loud assert at extractor entry (T-02-08)"
    - "TRC-03 trace-tag regex preserved byte-identical from v0.1.0"
key-files:
  created:
    - "lib_code_parser/extractors/primitives/functions.py"
    - "lib_code_parser/frontends/python.py"
    - "tests/unit/extractors/__init__.py"
    - "tests/unit/extractors/test_functions_extractor.py"
  modified: []
decisions:
  - "build_cav (frontends/python.py) created in this worktree to unblock CAV-based unit tests under parallel-wave isolation; content byte-identical to RESEARCH §6.3 template / Plan 02-01 deliverable"
  - "Module docstring uses a raw string (r\"\"\") so the embedded TRC-03 regex stays byte-identical and avoids an invalid-escape DeprecationWarning"
metrics:
  duration: ~12m
  completed: 2026-05-31
  tasks: 2
  files: 4
---

# Phase 2 Plan 02: Functions Extractor Summary

CAV-consuming `extract(cav, config) -> list[FunctionNode]` extractor that ports v0.1.0 `ast_extractor.extract_functions` logic (FunctionNode + ParamInfo + SourceRange + TraceTag) to the new single-parse CAV signature with byte-identical TRC-03 trace-tag regex and v0.1.0 emit-order parity.

## What Was Built

- **`lib_code_parser/extractors/primitives/functions.py`** — `extract(cav, config)` pulls `cav.payload` (an already-parsed `ast.Module`), asserts it `isinstance(ast.Module)` (T-02-08 fail-loud), and walks it once: first pass emits each `ClassDef` (kind="class") + its methods (kind="method", `skip_self_cls=True`), second pass emits top-level functions (kind="function", `skip_self_cls=False`). Module name comes from `lib_code_parser._paths.get_module_name` (ARC-04 single source — no local definition). The 4 v0.1.0 helpers (`_extract_annotation`, `_extract_trace_tags`, `_make_source_range`, `_extract_params`) are ported verbatim; the trace-tag regex `r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)"` is byte-identical to v0.1.0 ast_extractor.py L28. `ast.parse` is never imported or called (AST-05).
- **`lib_code_parser/frontends/python.py`** — `build_cav(raw_content, path, config)` 1-parse Frontend. See Deviations (Rule 3).
- **`tests/unit/extractors/test_functions_extractor.py`** — 11 unit tests; CAV assembled via `build_cav` (no test-level parse, per RESEARCH §Pitfall 7).

## Verification Evidence

1. **pytest (full suite):** `198 passed` (Phase 1 baseline 187 + 11 new functions-extractor unit tests). Plan 02-02 contribution = 11 tests, all green.
2. **AST-05 grep gate:** `grep -rn -E "ast\.parse\(|from ast import parse" lib_code_parser/extractors/` → **0 matches**. (The single parse site `frontends/python.py` is outside `extractors/`.)
3. **ARC-04 no-duplication grep gate:** `grep -rn -E "^def _get_module_name|^def get_module_name" lib_code_parser/` → **1 match** (`_paths.py:18`). `functions.py` defines 0 local module-name helpers; imports `get_module_name` from `_paths` (1 match).
4. **TRC-02 / TRC-03 evidence on functions.py:** `Implements: AST-01` → 1; `Traces: AST-01` → 1; `Traces:` total → 5; verbatim regex literal `Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)` present (docstring + code).
5. **v0.1.0 baseline parity:** Phase 1 acceptance + parity suites (`tests/acceptance/`, `tests/parity/`) remain green inside the full 198-test run.
6. **ruff:** `All checks passed!` on `functions.py`, `frontends/python.py`, and `tests/unit/extractors/`.

## TDD Gate Compliance

- RED gate commit present: `68770af test(02-02): add failing unit tests for functions extractor` (RED confirmed: `ModuleNotFoundError: No module named 'lib_code_parser.extractors.primitives.functions'`).
- GREEN gate commit present: `dd981ff feat(02-02): implement functions extractor (CAV consumer + v0.1.0 parity)` (all 11 tests pass after).
- REFACTOR gate: not needed (clean implementation, ruff green). One in-GREEN fix applied (raw-string docstring) — see Deviations Rule 1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Module docstring DeprecationWarning (invalid escape sequence)**
- **Found during:** Task 1 GREEN run.
- **Issue:** The plan's docstring template embeds the regex `\s*(...)` inside a non-raw `"""..."""` docstring, producing `DeprecationWarning: invalid escape sequence '\s'` at import.
- **Fix:** Changed the module docstring to a raw string (`r"""..."""`). This keeps the embedded TRC-03 regex byte-identical to the actual `re.compile` pattern and removes the warning.
- **Files modified:** `lib_code_parser/extractors/primitives/functions.py`
- **Commit:** dd981ff

**2. [Rule 3 - Blocking dependency] build_cav absent in isolated parallel-wave worktree**
- **Found during:** Task 2 (test infrastructure).
- **Issue:** Plan 02-02's unit tests import `from lib_code_parser.frontends.python import build_cav`, but `build_cav` is Plan 02-01's deliverable. 02-01 runs in a sibling Wave 1 worktree and is NOT merged into this worktree (base = ef2ab01, `frontends/python.py` does not exist here). The tests could not be collected, blocking the TDD GREEN gate.
- **Fix:** Created `lib_code_parser/frontends/python.py` with `build_cav(raw_content, path, config)` byte-identical to the RESEARCH §6.3 / §例 1 (line 1054) template — the exact contract 02-01 will produce. This unblocks CAV-based test verification in isolation; at orchestrator merge time both worktrees create identical file content (clean / trivially-identical merge).
- **Files modified:** `lib_code_parser/frontends/python.py` (new)
- **Commit:** dd981ff
- **Note for merge:** If 02-01 and 02-02 both add `frontends/python.py`, the contents are identical; resolve by keeping either copy.

## Threat Mitigations Applied

| Threat ID | Mitigation |
|-----------|-----------|
| T-02-06 (ast.parse in extractors) | `grep -c "ast\.parse" functions.py` == 0; verified in Verification Evidence #2 |
| T-02-07 (local _get_module_name) | 0 local definitions; imports from `_paths` (Evidence #3) |
| T-02-08 (non-Python CAV payload) | `assert isinstance(tree, ast.Module)` with type-name diagnostic at extract() entry |

## Known Stubs

None — `extract` is fully wired to `cav.payload` and emits populated FunctionNode entries. `config` is accepted-but-unconsumed by design (documented in the function docstring; PrimitiveFn signature alignment, Phase 3+ may use `config.python_version`).

## Self-Check: PASSED

- FOUND: lib_code_parser/extractors/primitives/functions.py
- FOUND: lib_code_parser/frontends/python.py
- FOUND: tests/unit/extractors/__init__.py
- FOUND: tests/unit/extractors/test_functions_extractor.py
- FOUND commit: 68770af (test/RED gate)
- FOUND commit: dd981ff (feat/GREEN gate)
