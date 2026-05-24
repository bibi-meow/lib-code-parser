---
phase: 01-architecture-foundation-spec-correction
plan: 04
subsystem: models
tags: [pydantic, pydantic-v2, models, primitives, schema, sch-02, ast-04]

# Dependency graph
requires:
  - phase: 01-architecture-foundation-spec-correction
    provides: v0.1.0 baseline (commit cf7e7ec) with models.py defining the primitive surface
provides:
  - lib_code_parser.models.primitives subpackage with 8 Pydantic v2 BaseModel classes (FunctionNode, ParamInfo, SourceRange, TraceTag, CallEdge, CallGraph, TypeDep, ContractInfo)
  - SCH-02 omnibus assertion (all 8 primitives declare ConfigDict(extra="forbid"))
  - AST-04 schema substrate (ContractInfo.source_kind 4-value Literal discriminator + node_id + postconditions fields)
  - Transitional models/__init__.py compat shim that preserves the v0.1.0 import surface (from lib_code_parser.models import X) for Plan 03 / Plan 09 to supersede
affects: [01-03-models-infrastructure, 01-05-models-evaluations, 01-09-layout-migration-and-parity, phase-02-extractors]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pydantic v2 ConfigDict(extra='forbid') on every model (SCH-02)"
    - "Field(default_factory=list) for all mutable defaults (Pitfall 5)"
    - "Literal[...] closed enumeration for source_kind discriminator (AST-04)"
    - "Forward reference + model_rebuild() pattern for cross-file Pydantic models (FunctionNode -> ContractInfo)"
    - "Absolute imports only (lib_code_parser.models.primitives.*) per CONVENTIONS.md"

key-files:
  created:
    - lib_code_parser/models/__init__.py
    - lib_code_parser/models/primitives/__init__.py
    - lib_code_parser/models/primitives/functions.py
    - lib_code_parser/models/primitives/callgraph.py
    - lib_code_parser/models/primitives/contracts.py
    - lib_code_parser/models/primitives/type_deps.py
    - tests/unit/models/__init__.py
    - tests/unit/models/test_primitives_extra_forbid.py
  modified: []

key-decisions:
  - "Bundle contracts.py + type_deps.py + models/__init__.py + primitives/__init__.py into Task 1 commit (Rule 3 blocking-fix consolidation) — Task 1's verify command imports lib_code_parser.models.primitives.functions, which transitively triggers lib_code_parser/__init__.py and would break unless all 12 v0.1.0 names remain importable from lib_code_parser.models"
  - "models/__init__.py contains a transitional v0.1.0 compat shim (ArtifactId, CodeContent, NormalizedArtifact, ParserConfig as minimal stubs + primitive re-exports). Plan 03 (sibling Wave 1 worktree) provides the hardened infra layer; the orchestrator's Wave 1 merge is responsible for combining the two __init__.py contributions"
  - "ContractInfo gains node_id ('') and postconditions ([]) fields plus the source_kind Literal discriminator (4 values) per AST-04 substrate — default source_kind='pydantic_validator' matches v0.1.0 unconditional Pydantic tagging so Phase 2 extractor will only override when it sees __post_init__ or specific @field_validator/@model_validator decorators"
  - "TypeDep.kind remains free-form str = 'uses' (D-14 layer purity) — the closed EdgeKind Literal applies only to verifier-facing models/evaluations/graph_base.py (Plan 05)"

patterns-established:
  - "Module docstring with `Traces: <REQ-ID>` line at top of every primitive model file (TRC-02 substrate)"
  - "All 8 primitive models follow the same shape: `model_config = ConfigDict(extra='forbid')` first, then declarative Pydantic v2 fields with type annotations and `Field(default_factory=...)` for mutable defaults"
  - "Wave 0 omnibus pattern: a single test (`test_all_primitive_models_forbid_extra`) loops over `PRIMITIVE_MODELS = [...]` and asserts the SCH-02 invariant across the entire layer at once, plus per-class ValidationError tests for the most-likely-misused models"

requirements-completed: [SCH-02]

# Metrics
duration: 13min
completed: 2026-05-24
---

# Phase 01 Plan 04: Models — Primitives Summary

**Created lib_code_parser.models.primitives subpackage with 8 Pydantic v2 BaseModel classes, every one hardened with ConfigDict(extra="forbid") (SCH-02), plus AST-04 schema substrate (ContractInfo.source_kind 4-value Literal discriminator + postconditions list)**

## Performance

- **Duration:** 13 min
- **Started:** 2026-05-24T23:11:49Z
- **Completed:** 2026-05-24T23:24:58Z
- **Tasks:** 3 (Task 2 verification-only — files committed under Task 1 per Rule 3 deviation)
- **Files created:** 8

## Accomplishments
- 8 primitive Pydantic v2 models locked at the v0.1.0 field surface with SCH-02 hardening (`ConfigDict(extra="forbid")` on every model + `Field(default_factory=...)` for every mutable default)
- ContractInfo upgraded with the AST-04 schema substrate: new `node_id: str = ""`, new `source_kind: Literal[4 values] = "pydantic_validator"` closed discriminator, and new `postconditions: list[str]` field — ready for Phase 2 extractor + Phase 3 SPC-01 docstring pre/post extraction
- Wave 0 omnibus SCH-02 test (`tests/unit/models/test_primitives_extra_forbid.py`, 6 tests) asserting the invariant across all 8 primitives plus per-class ValidationError tests
- v0.1.0 caller surface preserved end-to-end: all 111 v0.1.0 baseline tests continue to pass (117 total with the 6 new Wave 0 tests) via a transitional `models/__init__.py` compat shim

## Task Commits

Each task was committed atomically (per the per-task commit protocol):

1. **Task 1: Implement functions.py + callgraph.py** — `d23fdbd` (feat)
   - In scope (per plan): `lib_code_parser/models/primitives/functions.py` (FunctionNode, ParamInfo, SourceRange, TraceTag) and `lib_code_parser/models/primitives/callgraph.py` (CallEdge, CallGraph)
   - Rule 3 blocking-fix scope bundled into the same commit: `lib_code_parser/models/__init__.py` compat shim, `lib_code_parser/models/primitives/__init__.py` marker, `lib_code_parser/models/primitives/contracts.py` and `lib_code_parser/models/primitives/type_deps.py` spec-correct implementations. Without these, `lib_code_parser/__init__.py` (which imports all 12 v0.1.0 names from `lib_code_parser.models`) fails at import time and Task 1's own verify command (`python -c "from lib_code_parser.models.primitives.functions import ..."`) cannot run.
2. **Task 2: Implement type_deps.py + contracts.py (TypeDep + ContractInfo with source_kind)** — verification only (files already in Task 1 commit). All Task 2 acceptance grep + behavior checks PASS against `d23fdbd`; no separate commit needed per "do not create an empty commit" rule.
3. **Task 3: Create primitives __init__.py + omnibus extra="forbid" Wave 0 test** — `ba7799c` (feat)
   - Rewrote `lib_code_parser/models/primitives/__init__.py` from the Task 1 minimal stub to the full 8-name `__all__` re-export contract; added `tests/unit/models/test_primitives_extra_forbid.py` (6 tests, all PASS) plus the `tests/unit/models/__init__.py` package marker.

**Plan metadata commit:** This SUMMARY.md is committed by the orchestrator (worktree mode — Plan 04 worker does not touch STATE.md / ROADMAP.md).

_Note: TDD tasks ran RED → GREEN cycles inline. RED for Task 1 / Task 2 was the verify command failing at import time (ModuleNotFoundError / ImportError); GREEN was the same command passing after the files landed. RED for Task 3 was `pytest` failing collection with `ImportError: cannot import name 'CallEdge' from 'lib_code_parser.models.primitives'`; GREEN was 6 tests passing after `primitives/__init__.py` re-exported the 8 names._

## Files Created/Modified

**Created (8 files):**
- `lib_code_parser/models/__init__.py` — Parent package marker + Plan-04 transitional v0.1.0 compat shim (re-exports the 8 primitives from `models/primitives/` and provides minimal v0.1.0 stubs for ArtifactId / CodeContent / NormalizedArtifact / ParserConfig until Plan 03 / Plan 09 supersede)
- `lib_code_parser/models/primitives/__init__.py` — 8-name re-export barrel for the primitives layer (FunctionNode, ParamInfo, SourceRange, TraceTag, CallEdge, CallGraph, TypeDep, ContractInfo) with `__all__`
- `lib_code_parser/models/primitives/functions.py` — FunctionNode aggregate + leaf types (ParamInfo, SourceRange, TraceTag). All 4 models declare extra="forbid". FunctionNode.contracts uses a forward reference (`"ContractInfo"`) resolved at module-bottom via `from lib_code_parser.models.primitives.contracts import ContractInfo` + `FunctionNode.model_rebuild()`.
- `lib_code_parser/models/primitives/callgraph.py` — CallEdge, CallGraph with `Field(default_factory=list)` defaults
- `lib_code_parser/models/primitives/contracts.py` — ContractInfo with the AST-04 schema substrate: `node_id`, `source_kind` 4-value Literal discriminator (`pydantic_validator | pydantic_model_validator | pydantic_field_validator | dataclass_post_init`), `preconditions`, `invariants`, `postconditions`
- `lib_code_parser/models/primitives/type_deps.py` — TypeDep with free-form `kind: str = "uses"` per D-14 layer purity (NOT the closed EdgeKind Literal — that lives in evaluations/, Plan 05)
- `tests/unit/models/__init__.py` — Test package marker
- `tests/unit/models/test_primitives_extra_forbid.py` — 6 tests: omnibus SCH-02 loop assertion + 4 per-class extra-forbid ValidationError tests + 1 ContractInfo source_kind Literal test

## Decisions Made

- **Task scope consolidation under Task 1 (Rule 3 deviation, see "Deviations from Plan" below)** — accepted as the only viable path given the v0.1.0 import chain dependency on the full v0.1.0 model name set.
- **Transitional compat shim in `models/__init__.py`** — the cleanest reconcilable contract between Plan 03 and Plan 04 (both Wave 1) is a shim that single-sources the primitives from `models/primitives/` and provides minimal v0.1.0 stubs for the 4 infrastructure-layer names. Plan 03's worktree will ship its own `models/__init__.py` with the hardened infrastructure classes; the orchestrator's Wave 1 merge step combines both contributions.
- **`FunctionNode.contracts` forward reference resolution** — used the documented `default_factory=lambda: __import__(...).ContractInfo()` pattern from the plan action block plus the module-bottom `from ... import ContractInfo` + `FunctionNode.model_rebuild()` for deterministic Pydantic v2 forward-ref binding. Verified that `FunctionNode(node_id="x", kind="function").contracts` returns a real `ContractInfo` instance, not a `ForwardRef`.
- **ContractInfo default source_kind = "pydantic_validator"** — preserves v0.1.0 behavior where every detected contract was unconditionally tagged as Pydantic. Phase 2's `contract_extractor.py` rewrite will override this to the precise value at extraction time (D-04 / AST-04).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Bundled contracts.py / type_deps.py / models/__init__.py / primitives/__init__.py into Task 1 commit**
- **Found during:** Task 1 GREEN-phase verification (the `python -c "from lib_code_parser.models.primitives.functions import ..."` verify command exit non-zero)
- **Issue:** Plan 04's Task 1 acceptance verify command transitively triggers `lib_code_parser/__init__.py`, which imports 12 names from `lib_code_parser.models`. In Wave 1, `lib_code_parser/models.py` (the v0.1.0 module) is shadowed the moment `lib_code_parser/models/__init__.py` exists as a package marker. So Task 1's own acceptance test cannot run unless: (a) `models/__init__.py` exists (forcing the directory to be a package), AND (b) `models/__init__.py` re-exports the full v0.1.0 surface (including ContractInfo and TypeDep). The latter requires `contracts.py` and `type_deps.py` to exist first — but those are scoped to Task 2 per the plan's `<tasks>` block. Without resolving this, Task 1's commit cannot even verify, breaking the per-task commit cycle.
- **Fix:** Created `lib_code_parser/models/__init__.py` as a transitional Plan-04 compat shim that re-exports the 8 primitives from `models/primitives/*` and provides minimal v0.1.0 stub classes for the 4 infrastructure-layer names (ArtifactId, CodeContent, NormalizedArtifact, ParserConfig). Created `lib_code_parser/models/primitives/__init__.py` as a minimal package marker (Task 3 later rewrites it with the full re-export contract). Created `lib_code_parser/models/primitives/contracts.py` and `lib_code_parser/models/primitives/type_deps.py` with the exact spec from Task 2's `<action>` block, so Task 2 became a verification-only step.
- **Files modified:** `lib_code_parser/models/__init__.py`, `lib_code_parser/models/primitives/__init__.py`, `lib_code_parser/models/primitives/contracts.py`, `lib_code_parser/models/primitives/type_deps.py` (all created)
- **Verification:** After the bundle: (1) Task 1 verify command exits 0 with "OK"; (2) all 111 v0.1.0 baseline tests still pass; (3) Task 2's grep / behavior / verify checks all pass against the Task 1 commit; (4) Task 3 was able to upgrade `primitives/__init__.py` independently without revisiting contracts.py / type_deps.py.
- **Committed in:** `d23fdbd` (Task 1 commit)

### Out-of-Scope Items (logged for deferred handling)

None. No pre-existing warnings or unrelated regressions discovered during execution.

---

**Total deviations:** 1 auto-fixed (Rule 3 blocking)
**Impact on plan:** Necessary to make Task 1's own acceptance test runnable. No scope creep — every bundled file is named in Plan 04's `files_modified` frontmatter (just under a different task than the plan author originally split). The orchestrator's Wave 1 merge will need to reconcile `lib_code_parser/models/__init__.py` between Plan 03 and Plan 04 — flagged for the merge step.

## Issues Encountered

- **cwd-drift safety violation (caught and remediated mid-execution)** — Early in Task 1, several `Bash` calls used `cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser"` (the main repo root) instead of staying inside the worktree at `C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/worktrees/agent-a5f57ba26ed28e8e5/`. As a result, several `Write` tool calls used absolute paths under the main repo. Verified via `git worktree list` + `pwd` that the worktree was unaffected (clean working tree) and the files had landed in the main repo. Read each misplaced file back, rewrote them to the worktree using the correct absolute path (worktree-rooted), removed the misplaced files from the main repo with `rm -rf` (file-level removals only, no git operations against the main repo), re-ran Task 1 verification in the worktree to confirm correctness. The worktree-path-safety guard from `references/worktree-path-safety.md` is what caught this — followed the remediation procedure exactly.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Plan 03 (Wave 1 sibling)** — `lib_code_parser/models/__init__.py` collision is expected. Orchestrator's merge step must combine: Plan 04's primitive re-exports + v0.1.0 infra stubs (this plan) with Plan 03's hardened infrastructure classes (CAV, NormalizedArtifact[TContent] Generic, typed ParserConfig). Plan 03's version of those 4 classes supersedes Plan 04's transitional stubs.
- **Plan 05 (Wave 2)** — Will introduce the `models/evaluations/` subpackage with the closed `EdgeKind: Literal[...]` enum and the verifier-facing GraphNode / GraphEdge / GraphModel / GuardExpr. No collision with Plan 04 (D-14 layer purity already enforced: `grep -v '^#' lib_code_parser/models/primitives/{callgraph,functions}.py | grep -c EdgeKind` returns 0).
- **Plan 09 (final phase)** — Will delete `lib_code_parser/models.py` (the v0.1.0 module) and rewrite `lib_code_parser/__init__.py` + `lib_code_parser/models/__init__.py` for the final 19-name `__all__`. The transitional shim in Plan 04's `models/__init__.py` will be entirely replaced.
- **Phase 2 (extractors)** — Has the schema substrate it needs: `ContractInfo.source_kind` 4-value Literal is ready for the `contract_extractor` rewrite; `ContractInfo.postconditions: list[str]` is ready for SPC-01 docstring pre/post wiring.

## Self-Check: PASSED

Verified before SUMMARY commit:

- `[ -f lib_code_parser/models/__init__.py ]` → FOUND
- `[ -f lib_code_parser/models/primitives/__init__.py ]` → FOUND
- `[ -f lib_code_parser/models/primitives/functions.py ]` → FOUND
- `[ -f lib_code_parser/models/primitives/callgraph.py ]` → FOUND
- `[ -f lib_code_parser/models/primitives/contracts.py ]` → FOUND
- `[ -f lib_code_parser/models/primitives/type_deps.py ]` → FOUND
- `[ -f tests/unit/models/__init__.py ]` → FOUND
- `[ -f tests/unit/models/test_primitives_extra_forbid.py ]` → FOUND
- `git log --oneline --all | grep -q d23fdbd` → FOUND (Task 1 commit)
- `git log --oneline --all | grep -q ba7799c` → FOUND (Task 3 commit)
- `python -m pytest tests/unit/models/test_primitives_extra_forbid.py -x -q` → 6 passed in 0.30s
- `python -m pytest tests/ -q` → 117 passed in 0.44s (baseline 111 + 6 new)
- `python -m ruff check lib_code_parser/models/ tests/unit/models/` → All checks passed!
- `python -m ruff format --check lib_code_parser/models/ tests/unit/models/` → 8 files already formatted

---
*Phase: 01-architecture-foundation-spec-correction*
*Completed: 2026-05-24*
