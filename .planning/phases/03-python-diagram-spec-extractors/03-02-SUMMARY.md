---
phase: 03-python-diagram-spec-extractors
plan: 02
subsystem: diagram-extractors
tags: [evaluations, class-diagram, component-diagram, package-diagram, edgekind, det-04, dispatch, parity-snapshot]

# Dependency graph
requires:
  - phase: 03-python-diagram-spec-extractors
    plan: 01
    provides: "EdgeKind+='imports', GraphEdge.source_unresolved, CodeContent 7 evaluation slots, executor EVALUATIONS walk, evaluations/spec.py, Wave-0 test scaffold (conftest build_python_cav, DIA-07 assert_valid_graphmodel)"
provides:
  - "DIA-01 class_diagram extractor — inherits/composes/aggregates/associates from type annotations; association fallback; builtins skipped; never a 'uses' edge"
  - "DIA-03 component_diagram extractor — module nodes + edge_type='imports' from type_deps kind=='imports' facts"
  - "DIA-04 package_diagram extractor — node_type='package' (plain str, no schema change) + containment via GraphNode.attributes['parent_package']"
  - "3 EVALUATIONS registrations (class/component/package) append-only in canonical order"
  - "DIA-07 schema-conformance cases feeding all 3 real diagram outputs through assert_valid_graphmodel"
  - "regenerated v01 parity snapshot: class/component/package slots now populated for EXAMPLE_SOURCE; 4 primitive slots byte-identical"
affects: ["03-03 sequence diagram", "03-04 FSM/state diagram", "03-05 function/class spec", "03-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure-CAV evaluation extractor: def extract(cav, config) -> GraphModel; assert ast.Module; pull primitives, never re-parse (Pitfall 5)"
    - "DET-04 sort-on-exit: nodes by node_id, edges by (source,target,edge_type,label); dict.fromkeys ordered dedup → byte-identical under PYTHONHASHSEED"
    - "Annotation-only relationship rule (py2puml-style): structural unwrap of Optional/X|None/list/set/dict; known-class resolution over ClassDefs + imported class-like names; association fallback for undecidable"
    - "Containment-via-attributes (D-06): package hierarchy on GraphNode.attributes['parent_package'], no 'contains' EdgeKind, no GraphNode schema change, no sibling-lib PR dependency"
    - "Parity-snapshot discipline: first real EVALUATIONS registrations change the EXAMPLE_SOURCE diagram slots → regenerate via scripts/generate_v01_snapshot.py, verify only intended slots changed (primitive slots byte-identical)"

key-files:
  created:
    - lib_code_parser/extractors/evaluations/__init__.py
    - lib_code_parser/extractors/evaluations/component_diagram.py
    - lib_code_parser/extractors/evaluations/package_diagram.py
    - lib_code_parser/extractors/evaluations/class_diagram.py
    - tests/unit/extractors/test_component_diagram.py
    - tests/unit/extractors/test_package_diagram.py
    - tests/unit/extractors/test_class_diagram.py
    - tests/unit/extractors/fixtures/dia_structural.py
    - tests/acceptance/test_dia01_class_diagram.py
    - tests/acceptance/test_dia03_component_diagram.py
    - tests/acceptance/test_dia04_package_diagram.py
  modified:
    - lib_code_parser/_dispatch.py
    - tests/unit/extractors/test_diagram_schema.py
    - tests/unit/test_executor_dispatch.py
    - tests/parity/fixtures/v01_snapshot.json

key-decisions:
  - "D-04/D-05/D-06: package containment via GraphNode.attributes['parent_package']; NO 'contains' EdgeKind added; graph_base.py untouched this plan (containment as attribute proven sufficient — no containment EDGE needed for verifier comparison)"
  - "D-03: class/component edges keep this lib's own vocabulary (inherits/composes/aggregates/associates/imports), NOT renamed to sibling lib-diagram-parser spelling — verifier resolves the physical↔logical gap"
  - "DIA-01 known-class resolution is structural: module ClassDefs + imported class-like names (uppercase-first heuristic, v0.1.0 type_deps parity); unknown names → associates (explicit), never fabricated, never silently dropped (T-03-03 mitigation)"
  - "Union (X | None) and Optional[X]/container[X] of a known class → aggregates; direct known class → composes; builtin/primitive → skipped (plain field)"

patterns-established:
  - "Pattern: pull-and-map diagram extractor — consume a Phase 2 primitive (type_deps) or re-walk cav.payload for new structural facts (class annotations), map to GraphModel, DET-04 sort, register one append-only EVALUATIONS entry"
  - "Pattern: EVALUATIONS canonical-order registration — class_diagram is #1; later plans (sequence #2, state #5, specs #6/7) insert per canonical order; dispatch test asserts subset-in-canonical-order (not contiguity)"

requirements-completed: [DIA-01, DIA-03, DIA-04, DIA-07]

# Metrics
duration: 14min
completed: 2026-06-01
---

# Phase 3 Plan 02: Structurally-Simple Diagram Extractors (DIA-01/03/04) Summary

**Shipped the three lowest-risk "pull-and-map" diagram extractors — class (inherits/composes/aggregates/associates from type annotations), component (import edges), and package (directory hierarchy with attribute-based containment) — exercising the Wave-0 foundation end-to-end, all registered append-only in canonical EVALUATIONS order and all emitting DET-04-sorted GraphModels that validate against the shared DIA-07 schema.**

## Performance

- **Duration:** ~14 min
- **Tasks:** 2 completed
- **Files:** 11 created, 4 modified
- **Tests:** 259 → 308 passing (+49 new), full suite incl. tests/parity green

## Accomplishments
- **DIA-03 component_diagram** (the exact analog): pulls `type_deps.extract`, keeps `kind=="imports"` facts, maps each to `GraphEdge(edge_type="imports")` + `GraphNode(node_type="component")`. No catch-all `uses`/`depends` edge (Pitfall 2 / D-03 own vocabulary).
- **DIA-04 package_diagram**: derives the dotted package chain from the file path (OS-independent), emits `GraphNode(node_type="package")` (plain str — D-05 no schema change), and expresses containment via `attributes["parent_package"]` (D-06 — no `contains` edge, no sibling-lib PR dependency, DIA-04 completed entirely in-lib).
- **DIA-01 class_diagram**: inheritance from `ClassDef.bases`; the composition/aggregation/association rule over declared instance-attribute annotations (class-body `AnnAssign` + `__init__` `self.x: T`), with structural known-class resolution and the `associates` undecidable fallback — never a fabricated edge, never `uses`.
- **DIA-07**: added real-output schema cases feeding all three diagrams through `assert_valid_graphmodel` + an edge-kind closure assertion.
- Regenerated the v0.1.0 parity snapshot twice (once per task) and **verified each time that only the intended diagram slot(s) changed** while the four primitive slots stayed byte-identical.

## Task Commits

1. **Task 1: DIA-03 component + DIA-04 package extractors + register** — `cdf2d03` (feat)
2. **Task 2: DIA-01 class diagram + DIA-07 schema cases + register #1** — `be83178` (feat)

_TDD tasks: behavior tests + implementation committed together per the by-design-breaking-test convention established in Plan 01 (the parity snapshot is a by-design-breaking artifact regenerated in the same commit as the extractor that changes it)._

## Files Created/Modified
- `lib_code_parser/extractors/evaluations/__init__.py` — NEW evaluations extractor package marker
- `lib_code_parser/extractors/evaluations/component_diagram.py` — NEW DIA-03 (imports edges + component nodes)
- `lib_code_parser/extractors/evaluations/package_diagram.py` — NEW DIA-04 (package nodes + parent_package attribute)
- `lib_code_parser/extractors/evaluations/class_diagram.py` — NEW DIA-01 (inherits/composes/aggregates/associates rule)
- `lib_code_parser/_dispatch.py` — register class_diagram (#1), component_diagram, package_diagram append-only in EVALUATIONS
- `tests/unit/extractors/test_{component,package,class}_diagram.py` — NEW unit tests (edges/nodes/determinism/return-type)
- `tests/unit/extractors/fixtures/dia_structural.py` — NEW class-hierarchy + __init__-attr fixtures (RESEARCH §Required Test Fixtures)
- `tests/unit/extractors/test_diagram_schema.py` — added DIA-07 real-output cases for all 3 diagrams
- `tests/acceptance/test_dia0{1,3,4}_*.py` — NEW acceptance tests via public execute()
- `tests/unit/test_executor_dispatch.py` — isolate sentinel-CAV dispatch units from real EVALUATIONS (deviation Rule 1, below)
- `tests/parity/fixtures/v01_snapshot.json` — regenerated; class/component/package slots now populated for EXAMPLE_SOURCE

## Verification Results
- `PYTHONPATH=. python -m pytest -q` → **308 passed** (full suite incl. tests/parity + tests/acceptance + tests/unit)
- `PYTHONHASHSEED=random python -m pytest tests/unit/extractors -q` → 89 passed (DET-04 determinism)
- Grep gate `grep -v '^#' class_diagram.py | grep -cE '"uses"|"depends"|"other"'` → **0**
- Canonical-order dispatch check → `['class_diagram','component_diagram','package_diagram']` is a prefix-preserving subsequence of the 7-canonical order
- `ruff check` + `ruff format --check` → clean on all evaluations extractors + `_dispatch.py`
- `git diff lib_code_parser/models/evaluations/graph_base.py` (this plan) → **EMPTY** — no `contains` EdgeKind, no GraphNode schema change
- Parity snapshot: 4 primitive slots (functions/call_graph/type_deps/contracts) **byte-identical** after both regenerations; only the diagram slots changed as intended (component+package after Task 1, class after Task 2)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Sentinel-CAV dispatch units crashed once a real EVALUATIONS entry existed**
- **Found during:** Task 1 (first full-suite run after registering component/package)
- **Issue:** `tests/unit/test_executor_dispatch.py` had 4 dispatch-walk-isolation units that stub `FRONTENDS["python"]` to return a sentinel `object()` as the CAV, but never stubbed `EVALUATIONS`. While EVALUATIONS was empty (Plan 01) the executor's EVALUATIONS walk was a no-op; the first real registration made the executor feed that sentinel `object()` to the real diagram extractors, which crashed on `cav.payload` (AttributeError). This is a pre-existing test-isolation gap exposed (not introduced) by the first real EVALUATIONS entry.
- **Fix:** Added `monkeypatch.setattr(_executor_module, "EVALUATIONS", {})` to the 4 sentinel-CAV units so they isolate the PRIMITIVES/frontend walk (their documented intent) without invoking real evaluations. The two non-sentinel units (disabled / C++ early-return) were untouched.
- **Files modified:** `tests/unit/test_executor_dispatch.py`
- **Commit:** `cdf2d03`

### Plan-driven adjustment

- The plan's Task-1 ordering note instructs registering component+package in Task 1 and inserting class_diagram as canonical #1 in Task 2. The dispatch append-only test asserts a *subset-in-canonical-order* (not contiguity), so each task's intermediate registration set is valid: Task 1 leaves `[component, package]` (valid subsequence), Task 2 prepends `class_diagram` → `[class, component, package]` (valid subsequence). Confirmed by the canonical-order acceptance check.

## Known Stubs

None. All three extractors are fully wired: component/package are pure structural transforms; class_diagram resolves known classes structurally with an explicit association fallback. The remaining empty CodeContent slots (`sequence_diagram`, `state_diagram`, `function_spec`, `class_spec`) are owned by Plans 03-03/03-04/03-05 and intentionally remain inert defaults until those plans register their EVALUATIONS entries.

## Threat Flags

None. The threat register dispositions were satisfied: T-03-03 (DIA-01 known-class resolution) is structural over ClassDefs + import map with explicit `associates` fallback (no name guessing); T-03-04 (Layer M integrity) is DET-04 sort + dict.fromkeys dedup, verified byte-identical under PYTHONHASHSEED=random; T-03-SC (no package installs) — zero installs, stdlib + Pydantic only. No new network/auth/secret/file-access surface introduced.

## Self-Check: PASSED

- All 11 created files exist on disk.
- Both task commits (`cdf2d03`, `be83178`) present in `git log`.
- Full suite (308) green including the easy-to-miss `tests/parity/test_snapshot_v01_fixture.py`.
