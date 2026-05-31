---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 06
subsystem: code-parser-pipeline
tags: [type-deps, executor, dispatch, pyright, wave2-closer]
requires: [02-01, 02-02, 02-03, 02-04, 02-05]
provides:
  - "type_deps extractor (RESEARCH §2.3 hybrid ast walk + pyright resolved oracle)"
  - "TypeDep model additive resolved + source_line fields"
  - "populated _dispatch.FRONTENDS (1) + PRIMITIVES (4)"
  - "dispatch-dict-driven CodeParserExecutor (D-03) on typed ParserConfig"
affects:
  - "Plan 02-07 (Wave 3 closer): inherits intentional-break acceptance/parity suite + barrel ParserConfig graduation + legacy file deletion"
tech-stack:
  added: []
  patterns: ["dispatch-dict walk (D-03)", "append-only registration (D-12)", "diagnostic-driven resolved annotation (D-07-revised)"]
key-files:
  created:
    - lib_code_parser/extractors/primitives/type_deps.py
    - tests/unit/models/test_type_deps_model.py
    - tests/unit/extractors/test_type_deps_extractor.py
    - tests/unit/test_executor_dispatch.py
  modified:
    - lib_code_parser/models/primitives/type_deps.py
    - lib_code_parser/_dispatch.py
    - lib_code_parser/executor.py
    - tests/unit/test_dispatch.py
decisions:
  - "type_deps extractor normalizes pyright 0-based diagnostic lines to ast 1-based for resolved mapping"
  - "executor uses typed ParserConfig internally; barrel graduation deferred to 02-07 per plan scope"
  - "Phase-1 'dispatch dicts empty' test invariant retired (Rule 1) — invalidated by this plan's registration deliverable"
metrics:
  duration: ~25 min
  completed: 2026-05-31
  tasks: 3
  files: 8
---

# Phase 2 Plan 06: Type-Deps Extractor & Dispatch-Driven Executor Summary

One-liner: Wave 2 closer wiring the 4 Wave-1 extractors + Frontend + PyrightAdapter into an end-to-end Python parser pipeline — adds the pyright-oracle `type_deps` extractor and rewrites the executor as a dispatch-dict walk over typed `ParserConfig`.

## What Was Built

1. **TypeDep model extension** (`models/primitives/type_deps.py`) — additive `resolved: bool = True` + `source_line: int = 0`; Phase 1 forward-ref usage and `extra="forbid"` unchanged.
2. **type_deps extractor** (`extractors/primitives/type_deps.py`) — RESEARCH §2.3 hybrid: stdlib ast walk (v0.1.0 import/annotation parity + `source_line` tracking) + `PyrightAdapter.analyze(cav.raw_content, cav.path)` reportMissingImports oracle → `resolved` flag; pyright 0-based lines normalized to ast 1-based; DET-04 sort by `(source, target, kind, source_line)`; D-06 fail-loudly RuntimeError propagation.
3. **_dispatch.py registration** — append-only (D-12): `FRONTENDS["python"]=build_cav` + `PRIMITIVES` 4 entries in insertion order `functions, call_graph, type_deps, contracts`.
4. **executor.py rewrite** (D-03) — v0.1.0 if/elif body + legacy extractor imports removed; now walks `FRONTENDS[language]` → CAV then `PRIMITIVES.items()`; typed `ParserConfig` (`config.language/enabled/extract_contracts`); ContractInfo→FunctionNode.contracts merger (v0.1.0 parity); disabled / C++-extension early returns preserved.

## Verification Evidence

### pytest (Plan 02-06 contribution)
- `tests/unit/models/test_type_deps_model.py` — 4 pass
- `tests/unit/extractors/test_type_deps_extractor.py` — 9 pass (mocked PyrightAdapter)
- `tests/unit/test_executor_dispatch.py` — 6 pass
- `tests/unit/test_dispatch.py` — 8 pass (Rule 1 updated)
- Plan 02-06 new units total: **19 pass**

Full suite: `tests/unit/ tests/parity/` → **208 passed, 16 failed** (all 16 are the plan-sanctioned intentional breaks below). AST-05 parity gate (`tests/parity/test_ast_05_one_parse.py`) passes; `ruff check lib_code_parser/ tests/unit/ tests/parity/` → All checks passed.

### Dispatch dump
```
FRONTENDS: ['python']
PRIMITIVES: ['functions', 'call_graph', 'type_deps', 'contracts']
```

### executor.py rewrite highlights
- Removed: `from lib_code_parser.{ast_extractor,callgraph_builder,contract_extractor,type_dep_builder} import ...`; `config.params` access (grep count now 0).
- Added: `from lib_code_parser._dispatch import FRONTENDS, PRIMITIVES`; `from lib_code_parser.models.infrastructure.config import ParserConfig`; `for name, primitive_fn in PRIMITIVES.items(): ...` walk.

### Grep traceability (AST-05 / DET-04 / DET-03 / D-03 / D-12)
- `Implements: AST-03, AST-05, DET-03` in type_deps extractor: 1
- `annotated.sort` (DET-04): 1
- `reportMissingImports` (DET-03 oracle): 3
- executor `FRONTENDS[` (D-03): 3
- executor `PRIMITIVES.items` (D-12): 1
- TRC-02: all 4 extractors carry `Implements:` docstrings.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Task 1 verify referenced non-existent test file**
- **Found during:** Task 1
- **Issue:** Plan's `<verify>` and acceptance referenced `tests/unit/models/test_type_deps.py` (Phase 1 TypeDep unit), which does not exist. The actual Phase 1 TypeDep unit lives in `tests/unit/models/test_primitives_extra_forbid.py`.
- **Fix:** Ran the new `test_type_deps_model.py` alongside the real Phase 1 unit `test_primitives_extra_forbid.py`; both pass together (backward-compat confirmed).
- **Files modified:** none (verify-command substitution only)
- **Commit:** dd7eec7

**2. [Rule 3 - Blocking] ruff E402 vs intentional bottom-of-module registration imports**
- **Found during:** Task 3
- **Issue:** The plan prescribes placing the 5 registration imports at the module bottom (append-only Open-Closed invariant #4), which triggers ruff `E402` (+`I001` after autofix).
- **Fix:** Added a file-level `# ruff: noqa: E402` directive (with rationale comment) to `_dispatch.py`, preserving the plan's intentional bottom placement. `ruff check` now clean.
- **Files modified:** `lib_code_parser/_dispatch.py`
- **Commit:** 8fe60e1

**3. [Rule 1 - Bug] Phase-1 "dispatch dicts empty" test invariant invalidated by this plan**
- **Found during:** Task 3 (full-suite verification)
- **Issue:** `tests/unit/test_dispatch.py::TestDispatchDictsEmpty` asserted `len(FRONTENDS)==0` and `len(PRIMITIVES)==0` — a Phase-1-only invariant directly overturned by this plan's core registration deliverable. Not in plan `files_modified`, but the test encodes an obsolete invariant for the exact module the plan modifies.
- **Fix:** Renamed class to `TestDispatchDictsPopulated`; updated assertions to `"python" in FRONTENDS` and `list(PRIMITIVES.keys()) == ['functions','call_graph','type_deps','contracts']` (append-only order). `EVALUATIONS` empty assertion retained (Phase 3).
- **Files modified:** `tests/unit/test_dispatch.py`
- **Commit:** 8fe60e1

## Intentional Breaks (Plan-Sanctioned — Handoff to Plan 02-07)

16 failing tests, all dependent on the v0.1.0 barrel `lib_code_parser.ParserConfig` stub (`params: dict`) or the v0.1.0 dead-code extractor. The plan scopes barrel ParserConfig graduation + legacy file deletion + acceptance/parity rewrites to Plan 02-07.

| File | Count | Root cause | Owner |
|------|-------|------------|-------|
| `tests/unit/test_executor.py` | 9 | v0.1.0 executor unit constructs barrel stub `ParserConfig(..., params={...})` and exercises the now-removed if/elif body; typed executor reads `config.language` | 02-07 |
| `tests/unit/test_contract_extractor.py` | 6 | Pre-existing (deferred-items.md from 02-04): v0.1.0 `contract_extractor.py:69` constructs removed `ContractInfo(preconditions=...)` kwargs | 02-07 |
| `tests/parity/test_v01_v02_compat.py::test_executor_runs_on_example_source` | 1 | Feeds barrel stub `ParserConfig` to typed executor (`config.language` AttributeError) | 02-07 |

**Note on plan internal contradiction:** the plan's `<verification>` line listed full `test_v01_v02_compat.py` exit 0, but Task 3's `<acceptance_criteria>` precisely scopes the required-pass set to `test_v01_v02_compat.py test_ast_05_one_parse.py` "だけを必須" while explicitly forbidding barrel graduation (02-07's job). The single end-to-end parity test cannot pass without either graduating the barrel (out of scope) or keeping the executor on the stub (violates the `truths` must_have "executor uses TYPED ParserConfig"). It therefore joins the intentional-break set. The 14 surface/D-06/ARC-05/SCH-03 parity tests pass.

### Acceptance tests for Plan 02-07 to rewrite (typed ParserConfig + CAV signature)
- `tests/acceptance/test_fr01_function_extraction.py`
- `tests/acceptance/test_fr02_*` / `test_fr03_*` / `test_fr05_*` / `test_fr06_*` (broken on legacy-import deletion in 02-07)
- `tests/acceptance/test_fr04_contracts.py` (already broken by 02-04)
- `tests/unit/test_executor.py` (rewrite to typed ParserConfig + dispatch flow)
- `tests/unit/test_contract_extractor.py` (remove — v0.1.0 dead extractor)
- `tests/parity/test_v01_v02_compat.py::test_executor_runs_on_example_source` (graduate barrel ParserConfig → typed)

## Requirements Satisfied
AST-03, AST-05, DET-03, DET-04, ARC-03, TRC-02, TRC-03

## Self-Check: PASSED
- Created files exist: type_deps.py extractor + 3 test files — confirmed.
- Commits exist: dd7eec7 (Task 1), 4d69368 (Task 2), 8fe60e1 (Task 3) — confirmed in git log.
