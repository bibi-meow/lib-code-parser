---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 03
subsystem: extractors/primitives
tags: [callgraph, AST-02, AST-05, DET-04, TRC-02, TRC-03]
dependency_graph:
  requires:
    - "lib_code_parser.models.primitives.callgraph.CallEdge/CallGraph (Phase 1 locked)"
    - "lib_code_parser.models.infrastructure.cav.CAV (Phase 1)"
    - "lib_code_parser.models.infrastructure.config.ParserConfig (Phase 1)"
    - "lib_code_parser._paths.get_module_name (Phase 1, ARC-04 single source)"
    - "lib_code_parser.frontends.python.build_cav (Plan 02-01, merged by orchestrator post-wave)"
  provides:
    - "lib_code_parser.extractors.primitives.callgraph.extract(cav, config) -> CallGraph"
  affects:
    - "Plan 02-06 will register _dispatch.PRIMITIVES['call_graph'] = extract (exclusive owner)"
    - "Plan 02-07 will rewrite tests/acceptance/test_fr02_callgraph.py to consume extract"
tech_stack:
  added: []
  patterns:
    - "Pure CAV consumer: no ast.parse, walks cav.payload once (AST-05)"
    - "Emit-time DET-04 sort: edges.sort(key=lambda e: (e.caller, e.callee))"
    - "v0.1.0 resolution parity inherited verbatim from callgraph_builder.py"
key_files:
  created:
    - "lib_code_parser/extractors/primitives/callgraph.py"
    - "tests/unit/extractors/test_callgraph_extractor.py"
    - "tests/unit/test_callgraph_sort.py"
    - "tests/unit/extractors/__init__.py (shared with Plan 02-02, identical content)"
  modified: []
decisions:
  - "Edges sorted at emit time per DET-04 / ROADMAP SC-2; nodes NOT sorted (SC-2 規定なし, v0.1.0 parity)"
  - "Duplicate edges NOT deduped (v0.1.0 parity); nodes deduped via dict.fromkeys"
  - "build_cav dependency (Plan 02-01) absent in isolated worktree → temporary local shim used ONLY to run tests green, removed before commit (never committed)"
metrics:
  duration: "~20 min"
  completed: "2026-05-31"
  tasks: 3
  files: 4
---

# Phase 2 Plan 03: Callgraph Extractor Summary

CAV-consumer internal call graph extractor (`extract(cav, config) -> CallGraph`) that walks the CAV's `ast.Module` payload once, inherits v0.1.0 resolution rules verbatim, and applies a DET-04 lexicographic `(caller, callee)` edge sort at emit time — satisfying ROADMAP Phase 2 SC-2 (in-house CallGraph + sort) and SC-4 (isolated extractor call).

## What Was Built

- **`lib_code_parser/extractors/primitives/callgraph.py`** — `extract(cav, config)` + `_get_call_name` / `_collect_calls` helpers (verbatim from v0.1.0 `callgraph_builder.py`). Reads `cav.payload` directly (no re-parse), asserts `isinstance(tree, ast.Module)` for isolated-call safety, derives module name via `_paths.get_module_name` (ARC-04), emits classes+methods (1st pass) then top-level functions (2nd pass), and sorts edges `(caller, callee)` before returning. TRC-02 `Implements: AST-02, AST-05, DET-04` + TRC-03 `Traces: AST-02, AST-05, DET-04, US-01, US-22, US-25`.
- **`tests/unit/extractors/test_callgraph_extractor.py`** — 10 unit tests locking the RESEARCH §4.1 CG1-CG7 truth table + sort + node dedup + isolated import + EXAMPLE_SOURCE parity.
- **`tests/unit/test_callgraph_sort.py`** — 4 unit tests for the DET-04 sort invariant (incl. byte-identical stability across 3 runs).

## pytest Output (Plan 02-03 contribution)

```
tests/unit/extractors/test_callgraph_extractor.py  10 passed
tests/unit/test_callgraph_sort.py                   4 passed
Plan 02-03 total: 14 passed
Full suite (worktree): 201 passed in 2.37s
```

## Grep Gate Evidence

| Gate | Command | Expected | Actual |
|------|---------|----------|--------|
| AST-05 (extractors dir) | `grep -rn -E "ast\.parse\(\|from ast import parse" lib_code_parser/extractors/` | 0 | 0 ✓ |
| AST-05 (callgraph.py) | `grep -c "ast\.parse" .../callgraph.py` | 0 | 0 ✓ |
| ARC-04 no-duplication | `grep -rln "^def get_module_name" lib_code_parser/` | 1 (`_paths.py`) | 1 ✓ |
| ARC-04 (local def absent) | `grep -c "^def _get_module_name\|^def get_module_name" .../callgraph.py` | 0 | 0 ✓ |
| ARC-04 (import present) | `grep -c "from lib_code_parser\._paths import get_module_name" .../callgraph.py` | 1 | 1 ✓ |
| DET-04 sort | `grep -c "edges.sort" .../callgraph.py` | >=1 | 1 ✓ |
| DET-04 sort key | `grep -c "(e.caller, e.callee)" .../callgraph.py` | >=1 | 1 ✓ |
| TRC-02 | `grep -c "Implements: AST-02" .../callgraph.py` | 1 | 1 ✓ |
| TRC-03 | `grep -c "Traces: AST-02" .../callgraph.py` | >=1 | 1 ✓ |
| AST-05 (extractor test) | `grep -E -c "ast\.parse\(" .../test_callgraph_extractor.py` | 0 | 0 ✓ |
| build_cav usage (test) | `grep -c "from lib_code_parser.frontends.python import build_cav" .../test_callgraph_extractor.py` | 1 | 1 ✓ |
| AST-05 (sort test) | `grep -E -c "ast\.parse\(" .../test_callgraph_sort.py` | 0 | 0 ✓ |
| stability (sort test) | `grep -c "model_dump_json" .../test_callgraph_sort.py` | >=1 | 1 ✓ |
| ruff | `ruff check` on all 3 files | exit 0 | All checks passed ✓ |

## RESEARCH §4.1 7-Fixture Truth Table Coverage

| Fixture | Rule | Test |
|---------|------|------|
| CG1 | `self.foo()` → bare `foo` | `test_self_dot_foo_resolves_to_bare_name` |
| CG2 | chain `a.b().c()` → 2 edges (c, b) | `test_chain_call_emits_two_edges` |
| CG3 | duplicate callee, no dedup | `test_duplicate_callee_not_deduped`, `test_edges_sort_with_duplicates_preserves_count` |
| CG4 | nested function flatten to outer | `test_nested_function_flattened_to_outer` |
| CG5 | `@staticmethod`/`@classmethod` as normal method | `test_staticmethod_classmethod_treated_as_method` |
| CG6 | pre-sort AST order → post-sort lex | `test_edges_lex_sorted_by_caller_callee`, `test_edges_are_lex_sorted_for_simple_fixture` |
| CG7 | deep `a.b.c.d()` → innermost 1 edge | `test_deep_attribute_innermost_only` |
| DET-04 | byte-identical stability | `test_edges_sort_is_stable_across_runs` |
| SC-4 | isolated extract() call | `test_isolated_import_no_executor` |
| nodes dedup | `dict.fromkeys` insertion order | `test_nodes_insertion_order_with_dedup` |

## v0.1.0 Baseline Parity Evidence

- `tests/acceptance/` 58 passed (unchanged v0.1.0 acceptance suite).
- Full worktree suite 201 passed — no regressions in existing `test_callgraph_builder.py` or other extractor tests.
- `_get_call_name` / `_collect_calls` copied verbatim from `callgraph_builder.py` L14-32; main loop mirrors `build_callgraph` L35-66 with only the CAV-payload swap and the appended `edges.sort` line.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing cross-plan `build_cav` dependency in isolated worktree**
- **Found during:** Task 2 (tests import `from lib_code_parser.frontends.python import build_cav`)
- **Issue:** `build_cav` / `frontends/python.py` is owned by sibling Wave 1 Plan 02-01 and is not present in this isolated worktree (base `ef2ab01`). Tests could not run green in isolation.
- **Fix:** Created a temporary local `frontends/python.py` shim (matching 02-01's `build_cav(raw_content, path, config)` signature, adapted to the current Phase 1 CAV model which has no `raw_content` field) solely to exercise the tests, ran the suite green (14/201 pass), then **removed the shim before any commit**. The shim was never staged or committed — it belongs to 02-01 and will be supplied at orchestrator merge.
- **Files modified:** none committed (shim transient only)
- **Note:** This is NOT a package-install deviation (no new dependency). It is a known parallel-wave artifact gap resolved without touching sibling-owned committed files.

### Process Note (not a plan deviation)

The executor's first file writes were accidentally placed in the **main repo** working tree instead of the worktree (an explicit `cd` to the main-repo absolute path overrode the harness default cwd). Detected via the per-commit HEAD assertion (branch reported `master`, `.git` a directory). Recovered by copying the 3 deliverables into the worktree, removing the untracked pollution from the main repo individually (no `git clean`, no tracked-file changes), and committing only inside the worktree on `worktree-agent-a81359d2991d0d491`. No data lost; main repo left with only its pre-existing modifications.

## Commits

- `586cb26` feat(02-03): implement CAV-consumer callgraph extractor with DET-04 sort
- `95e1a1e` test(02-03): unit tests for callgraph extractor (v0.1.0 resolution + isolated import)
- `8303aee` test(02-03): DET-04 sort invariant gate (tests/unit/test_callgraph_sort.py)

## Known Stubs

None. The extractor is fully wired to `cav.payload`; dispatch registration is intentionally deferred to Plan 02-06 (exclusive owner of `_dispatch.PRIMITIVES`).

## Self-Check: PASSED

- Created files all FOUND: `callgraph.py`, `test_callgraph_extractor.py`, `test_callgraph_sort.py`, `extractors/__init__.py`, `02-03-callgraph-extractor-SUMMARY.md`
- Commits all FOUND: `586cb26`, `95e1a1e`, `8303aee`, `e1fd026`
- No STATE.md / ROADMAP.md modifications committed (orchestrator-owned, untouched)
