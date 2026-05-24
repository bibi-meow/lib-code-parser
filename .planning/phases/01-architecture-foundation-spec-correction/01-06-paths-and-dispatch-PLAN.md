---
phase: 01-architecture-foundation-spec-correction
plan: 06
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/_paths.py
  - lib_code_parser/_dispatch.py
  - tests/unit/test_paths.py
  - tests/unit/test_dispatch.py
autonomous: true
requirements: [ARC-04, DET-04]
must_haves:
  truths:
    - "lib_code_parser/_paths.py:get_module_name(path: str) -> str is the single source of truth for module name derivation"
    - "lib_code_parser/_dispatch.py declares 3 empty dispatch dicts (FRONTENDS / PRIMITIVES / EVALUATIONS) with typed Callable signatures"
    - "Dispatch dicts are append-only per Open-Closed contract (enforced via code review + docs/09 per pre-resolved decision #4)"
    - "D-10: nested layout under lib_code_parser/ — models/{infrastructure,primitives,evaluations}/, frontends/, extractors/{primitives,...}/, adapters/ (this plan ships _paths.py + _dispatch.py at the top of that layout)"
    - "D-11: design axis is the evaluation unit (output); shared primitives are obtained in pull mode (evaluation units import primitives), not push injection"
    - "D-12: _dispatch.py manages 3 dicts (FRONTENDS / PRIMITIVES / EVALUATIONS); executor walks the dicts (Task 2 ships the empty typed dicts; entries added in Phase 2-4)"
  artifacts:
    - path: "lib_code_parser/_paths.py"
      provides: "get_module_name() single source"
      contains: "def get_module_name"
    - path: "lib_code_parser/_dispatch.py"
      provides: "Static FRONTENDS/PRIMITIVES/EVALUATIONS dispatch tables (Phase 1: empty + typed)"
      contains: "FRONTENDS: dict|PRIMITIVES: dict|EVALUATIONS: dict"
  key_links:
    - from: "get_module_name(path)"
      to: "Path(path).stem"
      via: "v0.1.0 implementation parity"
      pattern: "Path\\(path\\)\\.stem"
    - from: "FRONTENDS / PRIMITIVES / EVALUATIONS"
      to: "Callable type aliases"
      via: "typing.Callable + forward refs to CAV / ParserConfig"
      pattern: "Callable\\["
---

<objective>
Per ARC-04 / DET-04 / D-12: create `lib_code_parser/_paths.py` with the single `get_module_name()` helper (eliminating the v0.1.0 4× duplication of `_get_module_name` across `ast_extractor.py`, `callgraph_builder.py`, `type_dep_builder.py`, `contract_extractor.py`) and `lib_code_parser/_dispatch.py` with the 3 typed dispatch dicts (FRONTENDS / PRIMITIVES / EVALUATIONS) per D-12 / D-13 invariant #4 (append-only).

Purpose: Locks the centralization point for module-name derivation BEFORE the existing 4 v0.1.0 extractors are patched (Plan 09 does the patch). Locks the dispatch surface BEFORE any extractor is registered (Phase 2-4 add entries). Both files are net-new in Wave 1; they do NOT modify existing v0.1.0 files (Plan 09 owns that wiring), so this plan ships completely in Wave 1 with no cross-plan dependency.

Output:
- `lib_code_parser/_paths.py` with `get_module_name(path: str) -> str` (returns `Path(path).stem`, mirroring v0.1.0 semantics)
- `lib_code_parser/_dispatch.py` with 3 empty typed dispatch dicts + module docstring stating the Open-Closed append-only invariant + reference to docs/09-extending.md
- Two Wave 0 tests: tests/unit/test_paths.py (happy path + no-duplication grep test, the latter currently expected to fail until Plan 09 lands) + tests/unit/test_dispatch.py (typed signature + empty + append-only docstring assertion)
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/ast_extractor.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/callgraph_builder.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/type_dep_builder.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/contract_extractor.py

<interfaces>
<!-- v0.1.0 _get_module_name signature (duplicated in 4 files, per .planning/codebase/CONCERNS.md): -->

def _get_module_name(path: str) -> str:
    """Convert file path to module name (stem only)."""
    return Path(path).stem

The new public function get_module_name() in _paths.py MUST have identical semantics. Plan 09 will patch the 4 v0.1.0 extractor files to make their `_get_module_name` a thin shim that re-exports from `lib_code_parser._paths.get_module_name`.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement _paths.py with get_module_name() + Wave 0 test</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/ast_extractor.py (existing _get_module_name implementation — preserve semantics exactly)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Nested Module Layout Migration — _paths.py is the single source per ARC-04; the 4 v0.1.0 extractor _get_module_name duplications are kept as thin re-exports by Plan 09 for v0.1.0 test backward-compat)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md (snake_case, type annotations on all params and returns)
  </read_first>
  <behavior>
    Tests in tests/unit/test_paths.py:
    - test_get_module_name_basic: get_module_name("foo.py") == "foo"
    - test_get_module_name_with_directory: get_module_name("src/order_service.py") == "order_service"
    - test_get_module_name_with_dots: get_module_name("path/to/my.module.py") == "my.module"  # Path.stem strips only the LAST extension — preserves v0.1.0 behavior
    - test_get_module_name_no_extension: get_module_name("Makefile") == "Makefile"
    - test_get_module_name_empty: get_module_name("") == ""
    - test_get_module_name_backslash_windows: get_module_name("src\\\\foo.py") returns "foo" on Windows (Path on win normalizes backslash); on POSIX returns "src\\\\foo" — the test should NOT pin OS-specific behavior beyond what pathlib provides; use a forward-slash path for cross-platform parity test
    - test_no_duplicate_module_name_helper: grep test — `_get_module_name` should appear in `_paths.py` (as `def get_module_name`) AND in the 4 v0.1.0 extractor files (these become thin shims after Plan 09). Phase 1 acceptance for this test is RELAXED: assert that `_paths.py` contains `def get_module_name(` exactly once. The hard "no duplication outside _paths.py" gate is asserted by Plan 09's parity test, not this plan.
  </behavior>
  <action>
    Implement `lib_code_parser/_paths.py`:
    - Module docstring: "Single source of truth for path → module-name derivation (ARC-04 / DET-04). Eliminates the v0.1.0 4× duplication of _get_module_name across ast_extractor.py / callgraph_builder.py / type_dep_builder.py / contract_extractor.py. Traces: ARC-04, DET-04."
    - Imports: `from __future__ import annotations`, `from pathlib import Path`.
    - Function `def get_module_name(path: str) -> str` with one-line docstring "Convert file path to module name (stem only)." Body: `return Path(path).stem`. This is byte-equivalent to v0.1.0 `_get_module_name`. Type annotations on parameter and return are required per CONVENTIONS.md.
    - Add `__all__ = ["get_module_name"]` at module top after imports.

    Implement `tests/unit/test_paths.py` per the `<behavior>` block above. Cross-platform note: use only forward-slash paths in tests (`"src/foo.py"`, NOT `"src\\\\foo.py"`) to avoid OS-specific test failure; pathlib handles both internally but tests should not depend on platform. Mark the `test_get_module_name_backslash_windows` test as a documented design choice — either include it with `if sys.platform == "win32"` guard OR omit it entirely (the simpler option is to OMIT it and document why in a comment: "pathlib normalizes path separators per OS; we test forward-slash for cross-OS determinism").

    Do NOT add any other helpers to `_paths.py` in this plan. Phase 2+ may add more path utilities if needed; Phase 1 ships only `get_module_name()` per ARC-04 scope.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/test_paths.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/test_paths.py -x -q` exits 0 with at least 5 passing tests (the backslash test may be omitted; the suite must include happy path / directory / dots / no-extension / empty)
    - `grep -c '^def get_module_name(path: str) -> str' lib_code_parser/_paths.py` returns exactly 1
    - `grep -c 'return Path(path).stem' lib_code_parser/_paths.py` returns exactly 1
    - `grep -c '__all__' lib_code_parser/_paths.py` returns >= 1
    - `python -c "from lib_code_parser._paths import get_module_name; assert get_module_name('foo.py') == 'foo'; assert get_module_name('src/order_service.py') == 'order_service'"` exits 0
    - File has module docstring with `Traces: ARC-04, DET-04`
  </acceptance_criteria>
  <done>_paths.py ships with get_module_name() single-source helper + Wave 0 unit tests passing; no duplication gate is enforced by Plan 09 parity test.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement _dispatch.py with 3 typed empty dispatch dicts + Wave 0 test</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md (D-12 — 3 dispatch dicts named FRONTENDS / PRIMITIVES / EVALUATIONS; D-13 invariant #4 — dispatch dicts are append-only)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Dispatch Dict Pattern — exact pinned form including Callable type aliases, TYPE_CHECKING forward refs to CAV/ParserConfig, and the explicit rationale for NOT using Protocol or entry-points / pluggy)
  </read_first>
  <behavior>
    Tests in tests/unit/test_dispatch.py:
    - test_frontends_dict_exists_and_empty: `FRONTENDS` is a `dict` and has length 0
    - test_primitives_dict_exists_and_empty: `PRIMITIVES` is a `dict` and has length 0
    - test_evaluations_dict_exists_and_empty: `EVALUATIONS` is a `dict` and has length 0
    - test_dispatch_module_docstring_mentions_append_only: the `_dispatch.py` module docstring contains the substring "append-only" (Open-Closed invariant #4)
    - test_dispatch_module_docstring_mentions_extending: the module docstring contains the substring "docs/09-extending.md" (forward-reference per D-13)
    - test_callable_aliases_imported: `FrontendFn`, `PrimitiveFn`, `EvaluationFn` are importable from `lib_code_parser._dispatch`
  </behavior>
  <action>
    Implement `lib_code_parser/_dispatch.py`:
    - Module docstring (multi-line): "Static dispatch tables for frontends, primitives, and evaluations. This module is the single point of registration for new extractors. After Phase 1 freezes the dict types, every new extractor in Phase 2-4 adds exactly one entry to the appropriate dict. The executor never grows logic; it only walks these dicts. INVARIANT (Open-Closed contract #4): dicts are append-only. Existing entries are never modified or removed. See docs/09-extending.md for the full 6-invariant Open-Closed contract. Traces: ARC-04."
    - Imports: `from __future__ import annotations`, `from typing import Callable, TYPE_CHECKING`.
    - Under `if TYPE_CHECKING:` block, forward-import the types referenced in Callable aliases: `from lib_code_parser.models.infrastructure.cav import CAV`, `from lib_code_parser.models.infrastructure.config import ParserConfig`. (TYPE_CHECKING avoids the import cycle: _dispatch is imported by executor, which is imported eagerly; the models layer should not be loaded unless concretely needed.)
    - Define type aliases:
      - `FrontendFn = Callable[[bytes, str, "ParserConfig"], "CAV"]`  # signature: (raw_content, path, config) -> CAV
      - `PrimitiveFn = Callable[["CAV", "ParserConfig"], object]`  # signature: (cav, config) -> primitive model instance (concrete type per primitive)
      - `EvaluationFn = Callable[["CAV", "ParserConfig"], object]`  # signature: (cav, config) -> evaluation model instance (concrete type per evaluation)
    - Define the 3 empty dicts EXACTLY:
      - `FRONTENDS: dict[str, FrontendFn] = {}`
      - `PRIMITIVES: dict[str, PrimitiveFn] = {}`
      - `EVALUATIONS: dict[str, EvaluationFn] = {}`
    - Add `__all__ = ["FrontendFn", "PrimitiveFn", "EvaluationFn", "FRONTENDS", "PRIMITIVES", "EVALUATIONS"]`.
    - Place a clearly-labeled comment above each dict explaining "Phase N will add: ..." (FRONTENDS: Phase 2 adds 'python'; Phase 4 adds 'cpp'. PRIMITIVES: Phase 2 adds 4 entries. EVALUATIONS: Phase 3 adds 5 diagrams + 2 specs).
    - Do NOT use `MappingProxyType` (would prevent legitimate Phase 2 additions). Do NOT use `Protocol` instead of `Callable` (rationale documented in RESEARCH.md §Dispatch Dict Pattern — Protocol would attract method-shaped expectations that conflict with module-level pure-function entries).

    Implement `tests/unit/test_dispatch.py` per the `<behavior>` block above. The append-only assertion is documentary, not runtime-enforced (per pre-resolved Open Question #4: code review gate, not hook/lint). The test verifies the docstring mentions the invariant.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/test_dispatch.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/test_dispatch.py -x -q` exits 0 with all 6 tests passing
    - `grep -c '^FRONTENDS: dict\[str, FrontendFn\] = {}$' lib_code_parser/_dispatch.py` returns exactly 1
    - `grep -c '^PRIMITIVES: dict\[str, PrimitiveFn\] = {}$' lib_code_parser/_dispatch.py` returns exactly 1
    - `grep -c '^EVALUATIONS: dict\[str, EvaluationFn\] = {}$' lib_code_parser/_dispatch.py` returns exactly 1
    - `grep -c 'FrontendFn = Callable\[' lib_code_parser/_dispatch.py` returns exactly 1
    - `grep -c 'PrimitiveFn = Callable\[' lib_code_parser/_dispatch.py` returns exactly 1
    - `grep -c 'EvaluationFn = Callable\[' lib_code_parser/_dispatch.py` returns exactly 1
    - `grep -ic 'append-only' lib_code_parser/_dispatch.py` returns >= 1 (D-13 invariant #4 documentary gate)
    - `grep -c 'docs/09-extending.md' lib_code_parser/_dispatch.py` returns >= 1 (forward reference)
    - `python -c "from lib_code_parser._dispatch import FRONTENDS, PRIMITIVES, EVALUATIONS, FrontendFn, PrimitiveFn, EvaluationFn; assert FRONTENDS == {}; assert PRIMITIVES == {}; assert EVALUATIONS == {}"` exits 0
    - `grep -c 'from typing import Callable, TYPE_CHECKING' lib_code_parser/_dispatch.py` returns >= 1 (TYPE_CHECKING used for import-cycle avoidance)
    - `grep -ci 'MappingProxyType' lib_code_parser/_dispatch.py` returns 0 (NOT used — would block Phase 2 additions)
    - `grep -c 'Protocol' lib_code_parser/_dispatch.py` returns 0 (NOT used — Callable is the chosen pattern per RESEARCH)
  </acceptance_criteria>
  <done>_dispatch.py ships with 3 typed empty dispatch dicts, append-only invariant documented in docstring, 6-test Wave 0 suite passing.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Phase 2+ contributor → dispatch dict mutation | A contributor may attempt to overwrite an existing dict entry instead of adding a new one; Open-Closed invariant #4 (append-only) is enforced at code review per pre-resolved decision #4 |
| extractor module → `get_module_name()` import | All extractors must use the centralized helper; Plan 09 patches the 4 v0.1.0 extractors to call through to `_paths.get_module_name` |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-06-01 | Tampering | `get_module_name` semantics drift from v0.1.0 | mitigate | Implementation is `Path(path).stem` byte-equivalent; Wave 0 tests assert happy path + edge cases (empty / no-extension / multiple dots) |
| T-06-02 | Tampering | Dispatch dict entry overwrite (append-only violation) | accept | Per pre-resolved Open Question #4: code review gate, no hook/lint enforcement in Phase 1. Documented in module docstring + docs/09-extending.md (Plan 08) |
| T-06-03 | Tampering | Plugin-mechanism abuse via entry_points / pluggy | mitigate | RESEARCH.md §Dispatch Dict Pattern explicitly rejects external plugin mechanisms; module-level dict is a closed registry; pyproject.toml does not declare any `[project.entry-points]` section that could populate dispatch dicts externally |
| T-06-04 | Tampering | Import cycle between _dispatch and models layer | mitigate | TYPE_CHECKING block + string forward refs `"CAV"`, `"ParserConfig"` ensure models layer is not imported at _dispatch.py load time |
</threat_model>

<verification>
- _paths.py:get_module_name() is the single function in that module; Wave 0 unit tests assert v0.1.0 parity
- _dispatch.py has 3 empty typed dicts with Callable aliases and append-only docstring
- TYPE_CHECKING used for CAV/ParserConfig forward refs (no import cycle)
- No MappingProxyType or Protocol used (per RESEARCH design choices)
</verification>

<success_criteria>
- ROADMAP §Phase 1 Success Criterion 3 partial: `_dispatch.py` exists with FRONTENDS / PRIMITIVES / EVALUATIONS dicts and `_paths.py:get_module_name()` is the single function (the grep gate `grep -rn '_get_module_name' lib_code_parser/` returning only _paths.py is finalized by Plan 09 after the 4 v0.1.0 extractors are patched to shim through _paths)
- ARC-04 substrate in place (`_paths.py:get_module_name()` exists)
- DET-04 substrate in place (dispatch invariants documented)
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-06-SUMMARY.md` when done with pytest output for tests/unit/test_paths.py + tests/unit/test_dispatch.py and grep verification.
</output>
