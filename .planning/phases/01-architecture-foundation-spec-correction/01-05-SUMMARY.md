---
phase: 01-architecture-foundation-spec-correction
plan: 05
subsystem: models
tags: [pydantic, literal, edge-kind, graph-schema, lib-diagram-parser-compat]

# Dependency graph
requires:
  - phase: 01-architecture-foundation-spec-correction
    provides: D-10 nested layout decision; D-14 evaluations-layer-is-verifier-facing decision
provides:
  - EdgeKind closed Literal (11 values) at lib_code_parser/models/evaluations/graph_base.py
  - GraphNode / GraphEdge / GraphModel / GuardExpr verifier-facing models with extra="forbid"
  - SCH-02 physical_module substrate on GraphEdge
  - 13-test Wave 0 suite locking the closed Literal + extra=forbid contract
affects:
  - 01-09 (Wave 2 layout migration — replaces __init__.py guard and wires the v0.1.0 backward-compat surface)
  - 03-* (Phase 3 diagram extractors — consume EdgeKind + GraphEdge + GraphModel)
  - 05-* (Phase 5 SCH-04 cross-lib schema compat test — relies on structural parity with lib-diagram-parser)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Closed Literal taxonomy enforced at construction time (Pitfall 7 mitigation)"
    - "Pydantic v2 ConfigDict(extra=\"forbid\") on every verifier-facing model (SCH-02)"
    - "physical_* prefix convention for physical-side metadata that verifier ignores (SCH-02)"
    - "Structurally compatible copies of sibling-lib models (no runtime import dependency in Phase 1 per pre-resolved Open Question #5)"

key-files:
  created:
    - lib_code_parser/models/__init__.py  # Wave 1 parent-package placeholder
    - lib_code_parser/models/evaluations/__init__.py  # Re-exports 5 symbols
    - lib_code_parser/models/evaluations/graph_base.py  # EdgeKind + 4 graph models
    - tests/unit/models/__init__.py  # Empty package marker
    - tests/unit/models/test_graph_base.py  # 13-test Wave 0 suite
  modified:
    - lib_code_parser/__init__.py  # Wave 1 transitional try/except guard around legacy 14-name re-export (Rule 3 blocking-issue fix)

key-decisions:
  - "EdgeKind = Literal[...] with exactly 11 values; \"uses\" / \"other\" / \"misc\" forbidden (Pitfall 7 / SCH-03)"
  - "GraphNode.node_type kept as plain str (not Literal) to leave the DIA-04 \"package\" extension path open per D-15 / D-17"
  - "GraphEdge.physical_module: str | None = None as the SCH-02 physical-side substrate"
  - "No runtime import of lib_diagram_parser in Phase 1 — models are self-contained structural copies (pre-resolved Open Question #5; sibling-lib PR deferred per D-15)"
  - "Wave 1 transitional bridge in lib_code_parser/__init__.py via try/except — recorded as a Rule 3 deviation; Wave 2 Plan 01-09 rewrites this file"

patterns-established:
  - "Closed-Literal taxonomy: forbid catch-all values at construction time so verifier-facing schemas cannot drift via ad-hoc growth"
  - "Optional physical_* fields on verifier-shared models: physical-side metadata is invisible to logical-side comparisons"
  - "extra=\"forbid\" on every verifier-facing model: schema drift is rejected at model construction, not at downstream comparison"

requirements-completed: [SCH-01, SCH-02, SCH-03]

# Metrics
duration: ~25 min
completed: 2026-05-24
---

# Phase 1 Plan 05: models/evaluations — verifier-facing graph schema lock

**EdgeKind closed Literal (11 values) plus GraphNode / GraphEdge / GraphModel / GuardExpr with `extra="forbid"` and a `physical_module` substrate — lib-diagram-parser-compatible schema locked at construction time before any Phase 3 diagram extractor is written.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-24T22:58Z (worktree spawn)
- **Completed:** 2026-05-24T23:23Z
- **Tasks:** 2 (both with `tdd="true"`)
- **Files created:** 5 (3 source + 2 test)
- **Files modified:** 1 (`lib_code_parser/__init__.py`, Rule 3 transitional guard)

## Accomplishments

- **SCH-03 hard gate locked:** `EdgeKind = Literal[...]` with exactly 11 enumerated values. Construction of `GraphEdge(edge_type="uses")` raises Pydantic `ValidationError` at instance-creation time. The Pitfall-7 forbidden values (`"uses"`, `"other"`, `"misc"`) appear nowhere in the source code outside the brief explanatory comment.
- **SCH-02 hard gate locked:** All four verifier-facing models (`GraphNode`, `GraphEdge`, `GraphModel`, `GuardExpr`) declare `ConfigDict(extra="forbid")`. Unknown extra kwargs raise `ValidationError`.
- **SCH-01 satisfied structurally:** Field names and shapes mirror `lib-diagram-parser` v0.1.0 (`node_id`, `node_type`, `label`, `attributes`; `source`, `target`, `edge_type`, `label`; `from_state`, `to_state`, `condition`, `action`; `nodes`, `edges`, `guards`). No runtime import of `lib_diagram_parser` in Phase 1 (pre-resolved Open Question #5).
- **SCH-02 physical substrate present:** `GraphEdge.physical_module: str | None = None` is the optional physical-side extension that the verifier will ignore when diffing against logical-side `GraphEdge` instances.
- **DIA-04 extension path open:** `GraphNode.node_type` is plain `str` (not `Literal`), deliberately leaving the `"package"` value valid so the Phase 3 sibling-lib re-evaluation per D-15 / D-17 can proceed without local schema drift.
- **13-test Wave 0 suite passes:** `pytest tests/unit/models/test_graph_base.py -x -q` → 13 passed in 0.98s.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement evaluations/graph_base.py** — `9949901` (feat) — creates `lib_code_parser/models/{__init__.py, evaluations/__init__.py, evaluations/graph_base.py}` with `EdgeKind` + 4 graph models. Verified via every Task 1 grep gate (EdgeKind Literal == 1, GraphNode/Edge/Model/GuardExpr classes each == 1, `extra="forbid"` >= 4, `edge_type: EdgeKind` == 1, `physical_module:` == 1, `from lib_diagram_parser` == 0, forbidden values in non-comment lines == 0, `Traces:` tag present).
2. **Task 2: __init__.py re-exports + Wave 0 tests** — `e11985e` (test) — creates `tests/unit/models/{__init__.py, test_graph_base.py}` with 13 tests covering EdgeKind closure, the canonical 11-value set, rejection of `"uses"` / `"other"` / `"misc"`, the all-11-values loop, GraphNode constructibility, `node_type="package"` acceptance, `physical_module` default + settable, `extra="forbid"` on all 4 models, `GraphModel()` empty defaults, `GuardExpr.action` empty default. Also includes the Rule 3 bridge edit to `lib_code_parser/__init__.py`.

**Plan metadata commit:** (to follow this summary commit)

## Files Created / Modified

### Created

- `lib_code_parser/models/__init__.py` — Wave 1 parent-package marker. Documented as transitional; Wave 2 Plan 01-09 will fill this with v0.1.0 backward-compat re-exports and delete the legacy `lib_code_parser/models.py`.
- `lib_code_parser/models/evaluations/__init__.py` — Absolute-import re-export of `EdgeKind`, `GraphNode`, `GraphEdge`, `GraphModel`, `GuardExpr` with `__all__`. No relative imports.
- `lib_code_parser/models/evaluations/graph_base.py` — Schema lock. EdgeKind closed Literal with one-line semantic comments above the alias listing all 11 values, plus the 4 Pydantic v2 models. Module docstring carries the `Traces: SCH-01, SCH-02, SCH-03` tag.
- `tests/unit/models/__init__.py` — Empty test-package marker.
- `tests/unit/models/test_graph_base.py` — 13-test Wave 0 suite: 6 `TestEdgeKindLiteral` tests, 2 `TestGraphNode` tests, 2 `TestGraphEdgePhysicalModule` tests, 1 `TestExtraForbid` test asserting forbid on all 4 models, 1 `TestGraphModelDefaults` test, 1 `TestGuardExpr` test. Uses fully-qualified submodule imports.

### Modified

- `lib_code_parser/__init__.py` — Wrapped the legacy v0.1.0 14-name re-export in `try/except ImportError` as a Wave 1 transitional bridge. Added a substantive module docstring explaining the shadow-induced ImportError, the Wave 2 fix path (Plan 01-09 full rewrite), and the warning not to rely on the top-level barrel during Wave 1 worktree-local validation. Recorded as a Rule 3 deviation below.

## Decisions Made

All decisions were inherited from the pre-resolved Open Questions and Phase 1 CONTEXT D-NN anchors. The plan was followed exactly per its `<action>` block; only the Rule 3 deviation below required executor discretion.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Wave 1 ImportError shadow on `lib_code_parser/__init__.py`**

- **Found during:** Task 2 (pytest collection of `tests/unit/models/test_graph_base.py`)
- **Issue:** Creating `lib_code_parser/models/` as a package directory shadows the legacy `lib_code_parser/models.py` file. The pre-existing top-level barrel `lib_code_parser/__init__.py` has `from lib_code_parser.models import FunctionNode, ...`, which raises `ImportError` once the `models/` package exists but does not yet re-export the 14 v0.1.0 names. Because Python eagerly executes `lib_code_parser/__init__.py` whenever any `lib_code_parser.*` submodule is imported, this transitively breaks every Plan 01-05 acceptance criterion that depends on a successful import of `lib_code_parser.models.evaluations.graph_base` — including pytest collection of the test file mandated by Task 2.
- **Fix:** Wrapped the legacy 14-name re-export in `try/except ImportError` and added a multi-paragraph module docstring documenting the Wave 1 transitional state, the Wave 2 fix path (Plan 01-09 full rewrite), and the explicit warning that callers must not rely on the top-level barrel for the v0.1.0 surface during Wave 1 worktree-local validation. The `try` block remains the optimistic path so that *if* a future Wave 1 plan completes the `models/__init__.py` re-export first, the legacy surface keeps working with no further change.
- **Files modified:** `lib_code_parser/__init__.py` (1 file, 19 lines docstring + 1 try/except wrapper)
- **Verification:** `pytest tests/unit/models/test_graph_base.py -x -q` → 13 passed in 0.98s. Manual smoke test of every Task 1 acceptance-criterion `python -c ...` command exits 0.
- **Committed in:** `e11985e` (Task 2 commit, alongside the test files it unblocked)
- **Why Rule 3 (not Rule 4):** This is not an architectural decision — the architectural decision (D-10 nested layout + D-14 evaluations-as-the-only-verifier-facing-layer) is already locked in CONTEXT.md and is what *causes* the shadow. The fix is purely a transitional bridge that the planned Wave 2 work (Plan 01-09) will replace with the proper full rewrite. No new architectural commitment is introduced.

### Scope-boundary note

The fix touches `lib_code_parser/__init__.py`, which is listed in Plan 01-09's `files_modified` (not Plan 01-05's). This is recorded as a deliberate Wave 1 cross-plan touch under Rule 3 (blocking-issue auto-fix). Wave 2 Plan 01-09's full rewrite will overwrite this transitional bridge with the canonical v0.1.0 + v0.2.0 public API. If a merge conflict arises during Wave 2 integration, the resolution is unambiguously "take Wave 2's version" — the bridge has no semantic content that needs to survive.

---

**Total deviations:** 1 auto-fixed (1 Rule 3 blocking-issue).
**Impact on plan:** The deviation was necessary to make Task 2's mandatory `pytest tests/unit/models/test_graph_base.py -x -q` verify step pass. No scope creep — the bridge is self-documenting, self-erasing on Wave 2 integration, and changes no behavior for any caller that was not already going to break under the Wave 1 shadow.

## Issues Encountered

- Initial draft of `graph_base.py` had docstring text containing `edge_type: EdgeKind` (verbatim) and `"uses"` (quoted), tripping the `grep -c 'edge_type: EdgeKind' == 1` and `grep -c '"uses"\|"other"\|"misc"' == 0 (non-comment lines)` grep gates. Rephrased the docstring to use prose ("the edge-type field", "forbidden by Pitfall 7") instead of the literal token forms. Both grep gates now match the plan exactly.

## Threat Surface

No new threat flags. The plan's `<threat_model>` enumerates T-05-01 (EdgeKind ad-hoc growth — mitigated by the closed Literal), T-05-02 (unknown-field drift — mitigated by `extra="forbid"`), T-05-03 (cross-lib schema drift — mitigated by structural parity + deferred to SCH-04 Phase 5 test per D-17), and T-05-04 (DIA-04 `"package"` blocked by Literal — accepted by keeping `node_type` as plain `str` per D-15). All mitigations were implemented as planned.

## Verification

| Check | Result |
|---|---|
| `EdgeKind` `get_args` length | 11 (exact) |
| Canonical EdgeKind set match | ✓ (all 11, no extras) |
| `"uses"` / `"other"` / `"misc"` rejected | ✓ ValidationError at construction |
| All 4 models declare `extra="forbid"` | ✓ (4 occurrences in source) |
| `GraphEdge.edge_type: EdgeKind` | ✓ (1 occurrence) |
| `GraphEdge.physical_module` field | ✓ (1 occurrence) |
| No `from lib_diagram_parser` import | ✓ (0 occurrences) |
| No forbidden values in non-comment source | ✓ (0 occurrences) |
| `tests/unit/models/test_graph_base.py` | ✓ 13 passed in 0.98s |
| `ruff check` on modified files | All checks passed |
| `ruff format --check` on modified files | All formatted |
| Task 1 `Traces:` tag in module docstring | ✓ present |

## Self-Check: PASSED

- `lib_code_parser/models/evaluations/graph_base.py` — exists
- `lib_code_parser/models/evaluations/__init__.py` — exists
- `lib_code_parser/models/__init__.py` — exists
- `tests/unit/models/test_graph_base.py` — exists
- `tests/unit/models/__init__.py` — exists
- `lib_code_parser/__init__.py` — modified (Rule 3 bridge)
- Commit `9949901` (Task 1 feat) — present in git log
- Commit `e11985e` (Task 2 test) — present in git log

## Next Phase Readiness

- **Wave 1 sibling plans (01-03 infrastructure, 01-04 primitives):** Independent — no contract changes against their scopes. They each create their own subpackage under `lib_code_parser/models/`. They may have made the same Rule 3 bridge edit; if so, the diffs converge.
- **Wave 2 Plan 01-09:** Ready to overwrite `lib_code_parser/__init__.py` with the canonical v0.1.0 + v0.2.0 surface. The transitional `try/except` guard here is intentionally orthogonal to that rewrite and has no semantic content to preserve.
- **Phase 3 diagram extractors:** Can begin building against the locked `EdgeKind` taxonomy + `GraphNode/Edge/Model` shapes the moment their wave begins.
- **Phase 5 SCH-04 cross-lib compat test:** Has the contract pin it needs — field names and types on the four models match `lib-diagram-parser` v0.1.0 exactly.

## TDD Gate Compliance

Plan 01-05 marks both tasks `tdd="true"` but the plan's task ordering puts the implementation (Task 1 `feat`) before the formal test suite (Task 2 `test`). Per the `<verify>` block on Task 1, RED-step verification was performed via the acceptance-criteria `python -c ...` commands, which all failed (ModuleNotFoundError) before the implementation was written and all succeeded immediately after. The formal Wave 0 test suite (Task 2) was then committed as the lasting GREEN record. Git log order: `9949901` (feat — GREEN) then `e11985e` (test — formal Wave 0 lock).

If a stricter "test commit must precede feat commit" interpretation is required by downstream gates, the test file can be cherry-pick-reordered without changing semantics — both commits are atomic and self-contained.

---
*Phase: 01-architecture-foundation-spec-correction*
*Plan: 05*
*Completed: 2026-05-24*
