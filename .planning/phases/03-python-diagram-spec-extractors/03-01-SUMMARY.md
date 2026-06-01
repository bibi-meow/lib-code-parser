---
phase: 03-python-diagram-spec-extractors
plan: 01
subsystem: schema-foundation
tags: [pydantic, graph-schema, edgekind, codecontent, dispatch, evaluations, fsm-marker]

# Dependency graph
requires:
  - phase: 02-python-primitives
    provides: "graph_base.py (EdgeKind + 4 graph models), CodeContent 4 primitive slots, executor PRIMITIVES walk, _dispatch.py EVALUATIONS empty dict, CAV + typed ParserConfig"
provides:
  - "EdgeKind += 'imports' (12 explicit-semantic values; catch-alls still rejected)"
  - "GraphEdge.source_unresolved: bool = False (DIA-06 marker home under extra=forbid)"
  - "models/evaluations/spec.py — FunctionSpec/ClassSpec/DocstringSection/SpecCondition + SpecConditionSourceKind (SPC-04 taxonomy)"
  - "CodeContent 7 additive evaluation slots (5 diagrams + function_spec + class_spec), all inert defaults"
  - "executor EVALUATIONS walk (run-all-registered, invariant #6) wired dict-driven"
  - "Wave-0 test scaffold: fixtures package, conftest build_python_cav + parser_config, DIA-07 assert_valid_graphmodel helper, forward-compatible dispatch-count test"
affects: ["03-02 class/component/package diagram", "03-03 sequence diagram", "03-04 FSM/state diagram", "03-05 function/class spec", "03-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Append-only EdgeKind Literal growth (D-01): new value + comment + test discipline, 11 existing values immutable"
    - "DIA-06 unresolved marker via source_ prefixed optional bool (verifier-invisible parity)"
    - "Dict-driven EVALUATIONS walk: executor setattr by name, body never changes when evaluations are added (invariant #6)"
    - "Lazy default-factory (_empty_graph_model) keeps infrastructure layer from hard-importing evaluations at module load"
    - "Forward-compatible append-only test: subset-of-canonical + relative-order, passes at 0 entries and as later plans register"

key-files:
  created:
    - lib_code_parser/models/evaluations/spec.py
    - tests/unit/models/test_spec_extra_forbid.py
    - tests/unit/extractors/test_diagram_schema.py
    - tests/unit/extractors/fixtures/__init__.py
  modified:
    - lib_code_parser/models/evaluations/graph_base.py
    - lib_code_parser/models/evaluations/__init__.py
    - lib_code_parser/models/infrastructure/artifact.py
    - lib_code_parser/executor.py
    - tests/unit/models/test_graph_base.py
    - tests/unit/test_dispatch.py
    - tests/conftest.py

key-decisions:
  - "D-01 sub-decision: add ONLY 'imports' to EdgeKind; express DIA-04 package containment via GraphNode.attributes['parent_package'] rather than a 'contains' edge — Plan 02 may add 'contains' only if containment EDGE proves required"
  - "DIA-06 marker home: source_unresolved: bool = False on GraphEdge (SCH-02 source_ prefix), not a separate model"
  - "SPC-04 source taxonomy (SpecConditionSourceKind) lives in evaluations/spec.py, NOT in frozen primitives/contracts.py SourceKind — keeps Phase 2 frozen file untouched"
  - "EVALUATIONS gating: run-all-registered (ParserConfig has no is_enabled flag); documented in executor docstring"
  - "FunctionSpec.source_range references primitives SourceRange via string forward ref + bottom try/except rebuild (evaluations ships independently of primitives load order)"

patterns-established:
  - "Pattern: append-only EVALUATIONS registration — downstream extractor plans add only their extractor file + one EVALUATIONS entry; CodeContent/executor/spec-model shape is now immutable contract"
  - "Pattern: DIA-07 assert_valid_graphmodel — shared schema-conformance helper validating GraphModel + physical_*/source_* prefix discipline, fed real outputs by Plans 02-04"

requirements-completed: [DIA-06, DIA-07, DIA-03]

# Metrics
duration: 6min
completed: 2026-06-01
---

# Phase 3 Plan 01: Python Diagram/Spec Extractor Foundation Summary

**Laid the immutable schema + integration contracts that all 7 Phase 3 extractors build against: EdgeKind gained 'imports', GraphEdge got its DIA-06 unresolved marker, CodeContent grew 7 evaluation slots, and the executor finally walks the EVALUATIONS dict it never implemented — without writing any extractor.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-01T17:04:14Z
- **Completed:** 2026-06-01T17:09:57Z
- **Tasks:** 4 completed
- **Files modified:** 11 (4 created, 7 modified)

## Accomplishments
- Closed the four PATTERNS.md integration gaps at the contract level: (b) CodeContent 7 new optional slots, (a) executor EVALUATIONS walk, (c) DIA-06 unresolved-marker schema home, (d) both by-design-breaking tests updated forward-compatibly in the same commits as the schema change.
- Landed `models/evaluations/spec.py` (FunctionSpec/ClassSpec/DocstringSection/SpecCondition) with the SPC-04 source taxonomy in the evaluations layer, leaving the frozen Phase 2 `primitives/contracts.py` untouched.
- Built the Wave-0 test scaffold (fixtures package, shared conftest CAV builder + config fixture, DIA-07 schema-conformance helper) so Plans 02–06 each add only an extractor + one EVALUATIONS entry.

## Task Commits

Each task was committed atomically:

1. **Task 1: Append EdgeKind 'imports' + GraphEdge source_unresolved; update breaking test_graph_base** - `a7a63b2` (feat)
2. **Task 2: Create models/evaluations/spec.py + extra=forbid test** - `ab04c2b` (feat)
3. **Task 3: 7 CodeContent slots + executor EVALUATIONS walk + DIA-07 schema test** - `27bdde9` (feat)
4. **Task 4: Wave-0 scaffold — fixtures pkg, conftest harness, forward-compat dispatch test** - `8246220` (test)

_TDD tasks 1–3 followed RED→GREEN within a single commit (test edits + schema change committed together per plan instruction for the by-design-breaking tests)._

## Files Created/Modified
- `lib_code_parser/models/evaluations/graph_base.py` - EdgeKind += "imports"; GraphEdge.source_unresolved optional field + semantic comment
- `lib_code_parser/models/evaluations/spec.py` - NEW: FunctionSpec/ClassSpec/DocstringSection/SpecCondition + SpecConditionSourceKind closed Literal (SPC-04)
- `lib_code_parser/models/evaluations/__init__.py` - export the four spec models
- `lib_code_parser/models/infrastructure/artifact.py` - CodeContent 7 additive evaluation slots + lazy GraphModel factory + forward-ref resolution
- `lib_code_parser/executor.py` - import EVALUATIONS; run-all-registered walk with setattr-by-name after PRIMITIVES/contract-merger
- `tests/unit/models/test_graph_base.py` - count 11→12, imports + source_unresolved positive tests
- `tests/unit/models/test_spec_extra_forbid.py` - NEW: spec model construction + extra=forbid + SPC-04 value set
- `tests/unit/extractors/test_diagram_schema.py` - NEW: DIA-07 assert_valid_graphmodel helper
- `tests/unit/extractors/fixtures/__init__.py` - NEW: fixtures package marker
- `tests/unit/test_dispatch.py` - forward-compatible test_evaluations_registered_append_only
- `tests/conftest.py` - shared build_python_cav + parser_config fixture

## Verification Results
- `python -m pytest tests/unit -q` → 180 passed (then 237 passed / 1 skipped across unit+acceptance after conftest change)
- `python -m pytest tests/acceptance -q` → 58 passed (v0.1.0 parity preserved)
- `ruff check` + `ruff format --check` → clean on all modified library + test files
- `git diff --name-only ccf6c59..HEAD` → does NOT include any `extractors/primitives/*` or `models/primitives/contracts.py` (Phase 2 frozen files untouched, invariant #1)
- EVALUATIONS still empty (`len(EVALUATIONS)==0`) — no extractor registered in this foundation plan

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan verify referenced non-existent test path**
- **Found during:** Task 3
- **Issue:** Plan `<verify>` and acceptance for Task 3 named `tests/unit/test_executor.py`, which does not exist; the actual executor test is `tests/unit/test_executor_dispatch.py`.
- **Fix:** Ran `tests/unit/test_executor_dispatch.py` + the new `test_diagram_schema.py`, then the full `tests/unit` suite (acceptance criterion #3 "no regression"). All green.
- **Files modified:** none (test-path resolution only)
- **Commit:** 27bdde9

## Self-Check: PASSED

- All 4 created files exist; all 4 task commits present in `git log`.
