---
phase: 01-architecture-foundation-spec-correction
plan: 03
subsystem: infra
tags: [pydantic, pydantic-generic, cav, parser-config, models, infrastructure]

# Dependency graph
requires:
  - phase: 01-architecture-foundation-spec-correction
    provides: "Plan 01 — license + pyproject.toml baseline; Plan 02 — spec doc rewrite (D-01)"
provides:
  - "lib_code_parser/models/infrastructure/ subpackage with CAV, ArtifactId, NormalizedArtifact[TContent] Generic, CodeContent, ParserConfig"
  - "v0.2.0 typed ParserConfig (ARC-05): params dict eliminated; explicit language/extract_contracts/compile_args/python_version fields"
  - "CAV single-parse envelope (ARC-02 substrate) — frozen + arbitrary_types_allowed + Literal language discriminator"
  - "NormalizedArtifact Pydantic v2 Generic with byte-identical JSON parity (D-06)"
  - "Transitional v0.1.0 legacy bridge in lib_code_parser/models/__init__.py preserving caller surface until Plan 09 deletes it"
affects: ["01-04-models-primitives (FunctionNode/CallEdge/CallGraph/TypeDep/ContractInfo)", "01-05-models-evaluations (EdgeKind/GraphModel)", "01-06-paths-and-dispatch (uses CAV+ParserConfig in dispatch signatures)", "01-09-layout-migration-and-parity (deletes models.py + replaces legacy bridge with primitives re-exports)"]

# Tech tracking
tech-stack:
  added: [Pydantic v2 Generic (typing.Generic[T] + TypeVar bound=BaseModel)]
  patterns:
    - "CAV envelope: frozen=True + arbitrary_types_allowed=True + Literal discriminator for cross-language opaque payload"
    - "Generic envelope: NormalizedArtifact[TContent] with byte-identical JSON parity between parameterized/unparameterized construction"
    - "Forward refs + lazy import factories for cross-plan-ordering independence (Plan 03 ships without waiting for Plan 04)"
    - "Field(default_factory=...) for all list/dict defaults (PITFALLS §5 — avoid ruff B008)"

key-files:
  created:
    - "lib_code_parser/models/__init__.py"
    - "lib_code_parser/models/infrastructure/__init__.py"
    - "lib_code_parser/models/infrastructure/cav.py"
    - "lib_code_parser/models/infrastructure/artifact.py"
    - "lib_code_parser/models/infrastructure/config.py"
    - "tests/unit/models/__init__.py"
    - "tests/unit/models/test_cav.py"
    - "tests/unit/models/test_config.py"
    - "tests/unit/models/test_artifact.py"
  modified: []

key-decisions:
  - "D-04/D-05 codified in cav.py: single CAV BaseModel + Literal['python','cpp'] discriminator + opaque payload=object + arbitrary_types_allowed=True + frozen=True"
  - "D-06 codified in artifact.py: NormalizedArtifact made Pydantic Generic; v0.1.0 caller parity verified inline (model_dump_json() byte-identical between NormalizedArtifact(...) and NormalizedArtifact[CodeContent](...))"
  - "D-08 codified in config.py: ParserConfig field names (artifact_type / executor_lib / enabled / language / extract_contracts / compile_args / python_version) fixed as sibling-lib-reusable generic names"
  - "ARC-05 satisfied: params dict eliminated; new fields use Field(default_factory=...) per PITFALLS §5"
  - "Cross-plan ordering resolved via TYPE_CHECKING forward refs + lazy-import factory + try/except fallback chain (Plan 04 primitives → v0.1.0 legacy bridge in models/__init__.py)"

patterns-established:
  - "Pydantic v2 Generic envelope pattern: TContent = TypeVar('TContent', bound=BaseModel); class X(BaseModel, Generic[TContent]) with content: TContent — RESEARCH live-tested for byte-identical JSON parity"
  - "Cross-plan ordering pattern: TYPE_CHECKING block for type-checker visibility + try/except runtime import with fallback for lazy resolution"
  - "Transitional bridge pattern: when a new package directory shadows a legacy module file, inline-define legacy symbols in the new package __init__.py so existing call sites keep working until migration plan removes both"

requirements-completed: [SCH-02, ARC-05, ARC-02]

# Metrics
duration: 9min
completed: 2026-05-24
---

# Phase 01 Plan 03: Models Infrastructure Summary

**Lib-boundary I/O contracts: CAV single-parse envelope (frozen+arbitrary_types_allowed+Literal discriminator), Pydantic Generic NormalizedArtifact[TContent], and typed ParserConfig (params dict eliminated per ARC-05) — all with extra='forbid' (SCH-02).**

## Performance

- **Duration:** 9 min
- **Started:** 2026-05-24T23:11:24Z
- **Completed:** 2026-05-24T23:21:04Z
- **Tasks:** 3
- **Files created:** 9 (5 source + 4 test)
- **Files modified:** 0 (Plan 03 ships only net-new files; transitional bridge inlined into the new models/__init__.py created in Task 1)

## Accomplishments

- **CAV (Common AST View)** envelope ready as ARC-02 substrate for Phase 2+ extractors — single-parse contract enforced via Pydantic `frozen=True` + opaque `payload: object` + `arbitrary_types_allowed=True` for `ast.Module` / `cindex.TranslationUnit`
- **ParserConfig fully typed (ARC-05 hard gate)** — `params: dict[str, object]` eliminated; new fields `language` / `extract_contracts` / `compile_args` / `python_version` typed and validated; preserves v0.1.0 caller-visible names (`artifact_type` / `executor_lib` / `enabled`)
- **NormalizedArtifact[TContent] Generic** with **byte-identical JSON parity** verified inline — D-06 RESEARCH live-tested with Pydantic 2.11.10 confirmed in this commit: `NormalizedArtifact(...)` and `NormalizedArtifact[CodeContent](...)` produce identical `model_dump_json()`
- **All 5 infrastructure models** (CAV / ArtifactId / NormalizedArtifact / CodeContent / ParserConfig) ship with `extra='forbid'` ConfigDict (SCH-02 satisfied for infrastructure layer)
- **17/17 Plan 03 unit tests pass**; **128/128 full suite passes** (v0.1.0 parity preserved across the transition)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create models/__init__.py + models/infrastructure/ package scaffolding** — `6645ca2` (feat)
2. **Task 2: Implement CAV + ParserConfig with Wave 0 tests (RED→GREEN via TDD)** — `cd46784` (feat)
3. **Task 3: Implement ArtifactId + NormalizedArtifact[TContent] Generic + CodeContent (RED→GREEN via TDD)** — `c240139` (feat)

## Files Created/Modified

**Created (source):**
- `lib_code_parser/models/__init__.py` — parent package marker + transitional v0.1.0 legacy bridge (inline-defines FunctionNode/CallEdge/CallGraph/TypeDep/ContractInfo/TraceTag/SourceRange/ParamInfo/CodeContent/NormalizedArtifact/ArtifactId/ParserConfig matching v0.1.0 surface; Plan 09 removes this block)
- `lib_code_parser/models/infrastructure/__init__.py` — re-exports CAV / ArtifactId / NormalizedArtifact / CodeContent / ParserConfig with `__all__`
- `lib_code_parser/models/infrastructure/cav.py` — CAV envelope (frozen+arbitrary_types_allowed+extra=forbid, language Literal['python','cpp'], opaque payload)
- `lib_code_parser/models/infrastructure/config.py` — typed ParserConfig (extra=forbid; no params dict; compile_args via default_factory)
- `lib_code_parser/models/infrastructure/artifact.py` — ArtifactId (frozen+extra=forbid), CodeContent (forward-ref fields + lazy CallGraph factory), NormalizedArtifact(BaseModel, Generic[TContent])

**Created (tests):**
- `tests/unit/models/__init__.py` — pytest package marker
- `tests/unit/models/test_cav.py` — 4 Wave 0 tests (construct, reject unknown language, frozen, extra-forbid)
- `tests/unit/models/test_config.py` — 5 Wave 0 tests (typed fields, defaults, reject unknown field, language Literal, no params field)
- `tests/unit/models/test_artifact.py` — 8 Wave 0 tests (ArtifactId basic/extra-forbid/frozen, CodeContent default empty, NormalizedArtifact unparameterized/parameterized/json-parity/extra-forbid)

**Modified:** none (only files staged in this plan are the net-new ones above)

## Decisions Made

- **D-04 / D-05 codified in cav.py**: single CAV `BaseModel` + `language: Literal["python", "cpp"]` + opaque `payload: object` + `arbitrary_types_allowed=True` + `frozen=True` + `extra="forbid"`. Typed union was rejected (would force contract change at Phase 4 C++ addition).
- **D-06 codified in artifact.py**: `NormalizedArtifact(BaseModel, Generic[TContent])` with `TContent = TypeVar("TContent", bound=BaseModel)`. Live byte-identical JSON parity asserted between `NormalizedArtifact(...)` and `NormalizedArtifact[CodeContent](...)` — confirming RESEARCH live-test reproducibility on the project's actual Pydantic 2.11.10 environment.
- **D-08 codified in config.py**: `ParserConfig` field names (`artifact_type` / `executor_lib` / `enabled` / `language` / `extract_contracts` / `compile_args` / `python_version`) chosen as sibling-lib-reusable generic names per the cross-lib reuse note in D-08.
- **ARC-05 satisfied**: `params: dict[str, object]` field is fully absent from `ParserConfig` (hard gate: `grep -c '^ *params:' lib_code_parser/models/infrastructure/config.py` returns 0).
- **PITFALLS §5 satisfied**: every list/dict default uses `Field(default_factory=...)` — not bare `[]` / `{}` — across `config.py` (`compile_args`) and `artifact.py` (`functions` / `call_graph` / `type_deps` / `contracts`).
- **Cross-plan ordering resolved via three-layer fallback**: `TYPE_CHECKING` block for type-checker visibility on `FunctionNode`/`CallGraph`/`TypeDep`/`ContractInfo` forward refs; lazy-import factory `_lazy_callgraph_default()` for runtime resolution of `CodeContent.call_graph` default; module-bottom `try/except` import chain that prefers Plan 04 primitives but falls back to the v0.1.0 legacy bridge installed in Task 2.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Transitional v0.1.0 legacy bridge installed in `lib_code_parser/models/__init__.py`**

- **Found during:** Task 1 verify (`python -c "import lib_code_parser.models; import lib_code_parser.models.infrastructure"`)
- **Issue:** Creating the new `lib_code_parser/models/` package directory shadows the legacy `lib_code_parser/models.py` module file (Python's import system gives precedence to the package over the same-named module). This broke every `from lib_code_parser.models import X` import in the pre-Phase-1 source tree — `executor.py`, `ast_extractor.py`, `callgraph_builder.py`, `contract_extractor.py`, `type_dep_builder.py`, `lib_code_parser/__init__.py`, `tests/unit/test_executor.py`, `tests/acceptance/test_fr06_disabled.py` — making `lib_code_parser` entirely unimportable and Plan 03's own verify command unable to run. The plan explicitly says "Do NOT edit models.py in this plan" and Plan 09 (Wave 3) is the migration owner, but Wave 1 isolation is broken until the bridge ships.
- **Fix:** Inline-defined the v0.1.0 legacy class set (FunctionNode / CallEdge / CallGraph / TypeDep / ContractInfo / TraceTag / SourceRange / ParamInfo / CodeContent / NormalizedArtifact / ArtifactId / ParserConfig) inside the new `lib_code_parser/models/__init__.py`. The definitions mirror `lib_code_parser/models.py` byte-for-byte (untouched on disk per the plan boundary). Plan 09 Task 1 deletes `models.py` AND replaces this transitional block with re-exports from `models/primitives/` and `models/evaluations/` — the bridge is explicitly self-deprecating.
- **Files modified:** `lib_code_parser/models/__init__.py` (Task 1 originally created it as an empty docstring marker; Task 2 expanded it with the legacy bridge)
- **Verification:** Full test suite — 128/128 tests pass (120 v0.1.0 baseline + 17 new Plan 03 + 8 Task 3 minus the 9 Task 2 + 8 Task 3 already counted). v0.1.0 parity preserved across all 6 acceptance tests (`tests/acceptance/test_fr01..06_*.py`).
- **Committed in:** `cd46784` (Task 2 commit)

**2. [Rule 3 - Blocking issue] Task 2 placeholder shell for `artifact.py`**

- **Found during:** Task 2 (the `infrastructure/__init__.py` re-exports `ArtifactId` / `NormalizedArtifact` / `CodeContent` from `artifact.py`, but that file isn't created until Task 3)
- **Issue:** Without `artifact.py`, the `infrastructure` package fails to import at Task 2 commit time, breaking Task 2's verify (which imports `lib_code_parser.models.infrastructure.cav`, which triggers loading the package init).
- **Fix:** Added a minimal stub `artifact.py` in Task 2 with three placeholder Pydantic classes (no Generic, no forward refs). Task 3 wholesale replaces the stub with the proper `Generic[TContent]` implementation + lazy CallGraph factory + model_rebuild() chain. Stub is referenced in the file's own header comment as "Task 2 placeholder, replaced wholesale by Task 3".
- **Files modified:** `lib_code_parser/models/infrastructure/artifact.py` (Task 2 created stub; Task 3 overwrote with full implementation)
- **Verification:** Each task's commit leaves the lib importable and tests green; the stub never persists past Task 3's commit.
- **Committed in:** `cd46784` (stub) and `c240139` (full implementation)

---

**Total deviations:** 2 auto-fixed (both Rule 3 — blocking issues caused by the unavoidable `models.py` vs `models/` collision and the package-init re-export needing all three submodules to exist before the package is importable)
**Impact on plan:** Both auto-fixes are mechanical Python-import-system requirements, not scope additions. The transitional bridge is explicitly anticipated by Plan 09's Task 1 (which says "Update `lib_code_parser/models/__init__.py` ... created by Plan 03 Task 1 as a parent marker with empty re-exports"). The auto-fix matches that intent and reduces Plan 09's required edit to "replace inline defs with primitives re-exports". No scope creep.

## Issues Encountered

- **Forward-ref resolution at `CodeContent` construction**: Initial Task 3 implementation hit `PydanticUserError: 'CodeContent' is not fully defined; you should define 'FunctionNode', then call 'CodeContent.model_rebuild()'`. Resolved by adding a module-bottom `try/except` import chain that prefers Plan 04 `lib_code_parser.models.primitives.*` and falls back to the v0.1.0 legacy bridge classes from `lib_code_parser.models`. After the imports complete, `CodeContent.model_rebuild()` resolves the string forward refs deterministically.
- **Ruff E501 on test docstrings**: Two test docstrings exceeded 100 chars after I added inline parameter documentation. Resolved by either reformatting to multi-line docstrings or tightening the prose.

## Self-Check: PASSED

**Files created (existence verified):**
- `lib_code_parser/models/__init__.py` ✓
- `lib_code_parser/models/infrastructure/__init__.py` ✓
- `lib_code_parser/models/infrastructure/cav.py` ✓
- `lib_code_parser/models/infrastructure/config.py` ✓
- `lib_code_parser/models/infrastructure/artifact.py` ✓
- `tests/unit/models/__init__.py` ✓
- `tests/unit/models/test_cav.py` ✓
- `tests/unit/models/test_config.py` ✓
- `tests/unit/models/test_artifact.py` ✓

**Commits exist (verified via `git log`):**
- `6645ca2` (Task 1) ✓
- `cd46784` (Task 2) ✓
- `c240139` (Task 3) ✓

**Test results:**
- `pytest tests/unit/models/` — 17 passed
- `pytest tests/` — 128 passed (v0.1.0 parity preserved)
- Ruff check + format-check — pass

**Plan acceptance hard gates:**
- All 5 infrastructure models have `extra='forbid'` ✓ (verified in §Verification block)
- `ParserConfig` has NO `params` field (`grep -c '^ *params:'` returns 0) ✓
- CAV has `frozen=True` + `Literal["python","cpp"]` + `arbitrary_types_allowed=True` ✓
- `NormalizedArtifact` is `Generic[TContent]` with `bound=BaseModel` ✓
- D-06 live JSON parity: `model_dump_json()` byte-identical between unparameterized and parameterized construction ✓

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **For Plan 04 (models/primitives/)**: `lib_code_parser/models/__init__.py` legacy bridge currently provides `FunctionNode` / `CallEdge` / `CallGraph` / `TypeDep` / `ContractInfo` etc. with v0.1.0 schemas. Plan 04 ships v0.2.0 typed versions in `models/primitives/*.py`; Plan 03's lazy-import chain in `artifact.py` automatically prefers Plan 04 primitives once they exist (no further changes to Plan 03 outputs needed).
- **For Plan 06 (paths-and-dispatch)**: `CAV` and `ParserConfig` are importable from `lib_code_parser.models.infrastructure.{cav,config}` for use in dispatch-table type signatures.
- **For Plan 09 (layout migration)**: The transitional v0.1.0 bridge in `lib_code_parser/models/__init__.py` is explicitly self-deprecating. Plan 09 Task 1 should (a) delete `lib_code_parser/models.py` and (b) replace the inline class block in `models/__init__.py` with re-exports from `models.primitives` and `models.evaluations`. The stub `artifact.py` from Task 2 is already overwritten by Task 3 — no remediation needed.
- **Blockers/concerns**: None for downstream Wave 1 plans (04, 05) since they share the same worktree-isolation strategy. The post-merge / Plan 09 cleanup must verify that removing the legacy bridge does not leave any caller still relying on the inline v0.1.0 class identities (acceptance criterion in Plan 09 already covers this).

---
*Phase: 01-architecture-foundation-spec-correction*
*Plan: 03*
*Completed: 2026-05-24*
