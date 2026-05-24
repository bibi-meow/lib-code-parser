---
phase: 01-architecture-foundation-spec-correction
plan: 09
type: execute
wave: 2
depends_on: [01-03, 01-04, 01-05, 01-06, 01-07]
files_modified:
  - lib_code_parser/__init__.py
  - lib_code_parser/models.py
  - lib_code_parser/ast_extractor.py
  - lib_code_parser/callgraph_builder.py
  - lib_code_parser/type_dep_builder.py
  - lib_code_parser/contract_extractor.py
  - lib_code_parser/executor.py
  - lib_code_parser/frontends/__init__.py
  - lib_code_parser/extractors/__init__.py
  - lib_code_parser/extractors/primitives/__init__.py
  - tests/parity/__init__.py
  - tests/parity/test_v01_v02_compat.py
autonomous: true
requirements: [ARC-01, ARC-04, DET-04]
must_haves:
  truths:
    - "v0.1.0 caller import surface intact: from lib_code_parser import CodeParserExecutor, ArtifactId, CallEdge, CallGraph, CodeContent, ContractInfo, FunctionNode, NormalizedArtifact, ParamInfo, ParserConfig, SourceRange, TraceTag, TypeDep all succeed"
    - "Existing tests/acceptance/test_fr01..06_*.py (6 files) pass unchanged"
    - "Existing tests/unit/test_*.py (5 files) pass unchanged (including the two that import _get_module_name)"
    - "grep -rn '_get_module_name' lib_code_parser/ shows _paths.py is the implementation source; the 4 v0.1.0 extractors retain only a thin shim that re-exports _paths.get_module_name"
    - "lib_code_parser/__init__.py exposes CAV, EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr alongside the v0.1.0 13-name surface"
    - "lib_code_parser/models.py file is removed (replaced by the models/ subpackage; legacy imports redirected through __init__.py)"
  artifacts:
    - path: "lib_code_parser/__init__.py"
      provides: "v0.1.0 backward-compat + v0.2.0 additions on the public surface"
      contains: "CodeParserExecutor|CAV|EdgeKind"
    - path: "tests/parity/test_v01_v02_compat.py"
      provides: "Parity gate: v0.1.0 surface intact, JSON byte-identical, _get_module_name single source"
      contains: "test_v01_caller_surface_intact|test_no_duplicate_module_name_helper"
    - path: "lib_code_parser/frontends/__init__.py"
      provides: "Empty Phase 1 placeholder (Phase 2 adds python.py; Phase 4 adds cpp.py)"
      contains: ""
    - path: "lib_code_parser/extractors/primitives/__init__.py"
      provides: "Empty Phase 1 placeholder (Phase 2 implements primitives extractors)"
      contains: ""
  key_links:
    - from: "lib_code_parser/__init__.py"
      to: "lib_code_parser.models.{infrastructure,primitives,evaluations}"
      via: "absolute import re-exports"
      pattern: "from lib_code_parser\\.models\\."
    - from: "ast_extractor.py / callgraph_builder.py / type_dep_builder.py / contract_extractor.py"
      to: "lib_code_parser._paths.get_module_name"
      via: "thin shim: _get_module_name = get_module_name"
      pattern: "from lib_code_parser\\._paths import get_module_name"
---

<objective>
Wave 2 sequential closer that wires together Wave 1 outputs (Plans 03 / 04 / 05 / 06 / 07) into a working v0.2.0 layout where v0.1.0 callers see ZERO surface changes (D-06 parity) and the v0.1.0 anti-pattern of 4× `_get_module_name` duplication is closed at the source-of-truth level (ARC-04 / DET-04 hard gate).

This plan modifies the existing v0.1.0 files — the LICENSE-protected ones from Plans 01-02 are not touched; we work only on Python source. The 4 v0.1.0 extractors are patched to import `get_module_name` from `_paths` (replacing their local `_get_module_name` body with a one-line shim). The v0.1.0 `models.py` file is deleted (replaced by the `models/` subpackage from Plans 03/04/05). The v0.1.0 `__init__.py` is rewritten to re-export from the new nested layout while preserving the 13-name v0.1.0 public surface. The v0.1.0 `executor.py` is updated to import models from the new layout but does NOT yet become dispatch-dict-driven (per CONTEXT.md `## code_context` §"v0.1.0 の 4 つの extractor (.py) ファイルを そのまま残す + Phase 2 で nested layout に動かす" — this Phase 1 retains the v0.1.0 extractor implementations and only fixes module-name + import paths; full dispatch-dict-driven executor is a Phase 2 deliverable). Three placeholder package directories are created so Phase 2-4 have stable import paths from day one.

Purpose: Honors ROADMAP §Phase 1 Success Criterion 3 hard gate (`grep -r "_get_module_name" lib_code_parser/` returns only `_paths.py` as the implementation source) AND the parity contract (v0.1.0 caller tests pass unchanged). Without this plan, Wave 1's models/infrastructure/primitives/evaluations subpackages exist but are not reachable from the legacy `from lib_code_parser import X` surface, breaking 13 v0.1.0 caller imports + 6 acceptance tests.

Output:
- Patched v0.1.0 extractor files (4 files, ~4 lines changed each — local `_get_module_name` becomes shim)
- Rewritten `lib_code_parser/__init__.py` with v0.1.0 13-name re-export + v0.2.0 additions
- Removed `lib_code_parser/models.py` (replaced by models/ subpackage)
- Updated `lib_code_parser/executor.py` import paths (no logic change)
- Placeholder packages: `frontends/`, `extractors/`, `extractors/primitives/` (empty `__init__.py` files for Phase 2+ to extend)
- Parity test `tests/parity/test_v01_v02_compat.py` with the no-duplication grep gate (ROADMAP SC-3 finalizer)
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/STRUCTURE.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/__init__.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/executor.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/ast_extractor.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/callgraph_builder.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/type_dep_builder.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/contract_extractor.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/acceptance/test_fr01_function_extraction.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/unit/test_ast_extractor.py

<interfaces>
<!-- v0.1.0 lib_code_parser/__init__.py 13-name __all__ (must preserve in this exact order for backward-compat): -->

__all__ = [
    "CodeParserExecutor", "ArtifactId", "CallEdge", "CallGraph", "CodeContent",
    "ContractInfo", "FunctionNode", "NormalizedArtifact", "ParamInfo",
    "ParserConfig", "SourceRange", "TraceTag", "TypeDep",
]

<!-- Verified via grep (2026-05-24): tests that import _get_module_name from extractor modules: -->
tests/acceptance/test_fr01_function_extraction.py (3 import sites)
tests/unit/test_ast_extractor.py (1 import site)
<!-- The other 3 unit tests (test_callgraph_builder, test_type_dep_builder, test_contract_extractor) do NOT import _get_module_name (research assumption A1 verified — only 2 test files in scope). -->

<!-- Plan 03/04/05 outputs (Wave 1 outputs that this Wave 2 plan depends on): -->
lib_code_parser/models/infrastructure/__init__.py — re-exports CAV, ArtifactId, NormalizedArtifact, CodeContent, ParserConfig
lib_code_parser/models/primitives/__init__.py — re-exports FunctionNode, ParamInfo, SourceRange, TraceTag, CallEdge, CallGraph, TypeDep, ContractInfo
lib_code_parser/models/evaluations/__init__.py — re-exports EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr
lib_code_parser/_paths.py — get_module_name(path: str) -> str
lib_code_parser/_dispatch.py — FRONTENDS / PRIMITIVES / EVALUATIONS empty dicts
lib_code_parser/adapters/__init__.py — re-exports run_subprocess, SubprocessAdapter
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Rewrite lib_code_parser/__init__.py + delete models.py + update executor.py imports</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/__init__.py (current v0.1.0 — verify 13-name __all__ before rewrite)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models.py (v0.1.0 — being deleted; verify all symbols are present in the new models/ subpackage via Plans 03/04/05)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/executor.py (current v0.1.0 — imports from `lib_code_parser.models` which becomes the subpackage)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Nested Module Layout Migration — Phase 1 で書くべき lib_code_parser/__init__.py 完全版 with exact `__all__` order)
  </read_first>
  <behavior>
    - `from lib_code_parser import CodeParserExecutor, ArtifactId, CallEdge, CallGraph, CodeContent, ContractInfo, FunctionNode, NormalizedArtifact, ParamInfo, ParserConfig, SourceRange, TraceTag, TypeDep` succeeds (v0.1.0 13-name parity)
    - `from lib_code_parser import CAV, EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr` succeeds (v0.2.0 6 new names)
    - `lib_code_parser.__version__ == "0.2.0"`
    - `import lib_code_parser.models` succeeds AND `lib_code_parser.models` is a package (not a module — the v0.1.0 models.py is gone)
    - Executor `import lib_code_parser.executor` succeeds and `CodeParserExecutor().execute(...)` returns NormalizedArtifact on the v0.1.0 EXAMPLE_SOURCE fixture (logic unchanged)
  </behavior>
  <action>
    Step 1 — Rewrite `lib_code_parser/__init__.py` to mirror RESEARCH.md §Nested Module Layout Migration verbatim. Specifically:
    - Module docstring: "lib-code-parser — Deterministic Python/C++ source parser. v0.2.0 introduces nested module layout. The flat v0.1.0 import surface is preserved via re-exports below — any v0.1.0 caller that wrote `from lib_code_parser import FunctionNode` continues to work unchanged."
    - Re-export `CodeParserExecutor` from `lib_code_parser.executor`.
    - Re-export infrastructure: `ArtifactId`, `NormalizedArtifact`, `CodeContent` from `lib_code_parser.models.infrastructure.artifact`; `CAV` from `lib_code_parser.models.infrastructure.cav`; `ParserConfig` from `lib_code_parser.models.infrastructure.config`.
    - Re-export primitives: `CallEdge`, `CallGraph` from `lib_code_parser.models.primitives.callgraph`; `ContractInfo` from `lib_code_parser.models.primitives.contracts`; `FunctionNode`, `ParamInfo`, `SourceRange`, `TraceTag` from `lib_code_parser.models.primitives.functions`; `TypeDep` from `lib_code_parser.models.primitives.type_deps`.
    - Re-export evaluations: `EdgeKind`, `GraphEdge`, `GraphModel`, `GraphNode`, `GuardExpr` from `lib_code_parser.models.evaluations.graph_base`.
    - Set `__version__ = "0.2.0"`.
    - Define `__all__` as a list whose contents are FIXED by the v0.1.0 backward-compat contract (parity test in Task 3 enforces order and membership). The list MUST contain exactly 19 string entries in two segments. Segment A (v0.1.0 13-name compat — ORDER PRESERVED, positional order MUST match v0.1.0): `"CodeParserExecutor"`, then `"ArtifactId"`, `"CallEdge"`, `"CallGraph"`, `"CodeContent"`, `"ContractInfo"`, `"FunctionNode"`, `"NormalizedArtifact"`, `"ParamInfo"`, `"ParserConfig"`, `"SourceRange"`, `"TraceTag"`, `"TypeDep"`. Segment B (v0.2.0 additions appended AFTER Segment A): `"CAV"`, `"EdgeKind"`, `"GraphEdge"`, `"GraphModel"`, `"GraphNode"`, `"GuardExpr"`. Use a `# v0.1.0 compat — ORDER PRESERVED` comment immediately before Segment A and a `# v0.2.0 additions` comment immediately before Segment B so future maintainers see the contract at a glance. Do NOT alphabetize Segment A — the v0.1.0 positional order is the contract.
    - All imports MUST be absolute per CONVENTIONS.md.

    Step 2 — Delete `lib_code_parser/models.py`. Use git-aware delete: `git rm lib_code_parser/models.py` (or `Remove-Item` on Windows / `rm` on POSIX with stage). The symbols previously declared there are now provided by the `models/` subpackage; the `__init__.py` re-exports above make `from lib_code_parser import X` work identically.

    Step 3 — Update `lib_code_parser/executor.py` import block ONLY (do NOT change executor logic in Phase 1 — per code_context note in CONTEXT.md, the dispatch-dict-driven rewrite is a Phase 2 deliverable; Phase 1 only fixes the import path because models.py is gone):
    - Current line 8-13 imports `from lib_code_parser.models import ArtifactId, CodeContent, NormalizedArtifact, ParserConfig`. After Step 2, `lib_code_parser.models` is a PACKAGE, not a module — the import still resolves IF the new package has these names re-exported via its `__init__.py`. Two options:
      - Option A (recommended): Update the import to `from lib_code_parser import ArtifactId, CodeContent, NormalizedArtifact, ParserConfig` (use the lib's own __init__.py — guaranteed since Step 1).
      - Option B: Update `lib_code_parser/models/__init__.py` (created by Plan 03 Task 1 as a parent marker with empty re-exports) to ALSO re-export from infrastructure subpackage, so `from lib_code_parser.models import X` still works. This is the more conservative choice because tests/unit/test_ast_extractor.py L8 reads `from lib_code_parser.models import ...` (legacy import path).
    - Recommendation: Implement Option B. Update `lib_code_parser/models/__init__.py` (originally created as empty parent marker in Plan 03) to add: `from lib_code_parser.models.infrastructure import CAV, ArtifactId, NormalizedArtifact, CodeContent, ParserConfig`, `from lib_code_parser.models.primitives import FunctionNode, ParamInfo, SourceRange, TraceTag, CallEdge, CallGraph, TypeDep, ContractInfo`, `from lib_code_parser.models.evaluations import EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr`, plus an `__all__` listing all 19 names. This preserves BOTH `from lib_code_parser.models import X` AND `from lib_code_parser import X` legacy paths.
    - Apply Option B in this task: modify `lib_code_parser/models/__init__.py` (extending Plan 03's parent marker) to include all 19 re-exports + `__all__`. Then `lib_code_parser/executor.py` import block can remain UNCHANGED (still works because `from lib_code_parser.models import X` resolves to the package __init__'s re-export).
    - Executor logic body (lines 19-86 in v0.1.0) MUST remain unchanged. The dispatch-dict-driven rewrite per D-12 is explicitly a Phase 2 deliverable — Phase 1 only locks the dispatch dict types (Plan 06) without populating them.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; python -c "from lib_code_parser import CodeParserExecutor, ArtifactId, CallEdge, CallGraph, CodeContent, ContractInfo, FunctionNode, NormalizedArtifact, ParamInfo, ParserConfig, SourceRange, TraceTag, TypeDep, CAV, EdgeKind, GraphEdge, GraphModel, GraphNode, GuardExpr; import lib_code_parser; assert lib_code_parser.__version__ == '0.2.0', lib_code_parser.__version__; import lib_code_parser.models; assert hasattr(lib_code_parser.models, 'FunctionNode'), 'package __init__ re-export missing'"</automated>
  </verify>
  <acceptance_criteria>
    - All 19 names (`CodeParserExecutor`, `ArtifactId`, `CallEdge`, `CallGraph`, `CodeContent`, `ContractInfo`, `FunctionNode`, `NormalizedArtifact`, `ParamInfo`, `ParserConfig`, `SourceRange`, `TraceTag`, `TypeDep`, `CAV`, `EdgeKind`, `GraphEdge`, `GraphModel`, `GraphNode`, `GuardExpr`) importable from `lib_code_parser`
    - `lib_code_parser.__version__ == "0.2.0"`
    - File `lib_code_parser/models.py` does NOT exist (`test ! -f lib_code_parser/models.py` exits 0)
    - File `lib_code_parser/models/__init__.py` exists AND re-exports all 19 names (test: `python -c "from lib_code_parser.models import CAV, ArtifactId, NormalizedArtifact, CodeContent, ParserConfig, FunctionNode, ParamInfo, SourceRange, TraceTag, CallEdge, CallGraph, TypeDep, ContractInfo, EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr"` exits 0)
    - `grep -c "^__version__ = \"0.2.0\"" lib_code_parser/__init__.py` returns exactly 1
    - `grep -c '"CodeParserExecutor"' lib_code_parser/__init__.py` returns >= 1 (first item in __all__)
    - `grep -c '"CAV"' lib_code_parser/__init__.py` returns >= 1
    - `grep -c '"EdgeKind"' lib_code_parser/__init__.py` returns >= 1
    - `grep "^from \\." lib_code_parser/__init__.py` returns 0 (no relative imports)
    - executor.py UNCHANGED at logic level: `diff lib_code_parser/executor.py <(git show HEAD:lib_code_parser/executor.py)` may show only import-block whitespace / re-organization, but the body of `class CodeParserExecutor` and its `def execute` MUST be unchanged. If executor.py imports `from lib_code_parser.models import ...`, that line is preserved.
    - `python -c "from lib_code_parser import CodeParserExecutor; exe = CodeParserExecutor(); result = exe.execute(__import__('lib_code_parser').ParserConfig(artifact_type='code', executor_lib='lib_code_parser'), b'def foo(): pass', 'foo.py'); assert result.content.functions[0].node_id == 'foo.foo'"` exits 0 (executor logic still works end-to-end through the new layout)
  </acceptance_criteria>
  <done>v0.1.0 13-name surface intact, v0.2.0 6 new names exposed, models.py deleted, models/ subpackage exposes all 19 names from package __init__.py, executor.py logic preserved.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Patch the 4 v0.1.0 extractors to shim _get_module_name through _paths.get_module_name + create empty Phase 2-4 placeholders</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/ast_extractor.py (current — has local def _get_module_name)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/callgraph_builder.py (current — has local def _get_module_name)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/type_dep_builder.py (current — has local def _get_module_name)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/contract_extractor.py (current — has local def _get_module_name)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_paths.py (Plan 06 output — exports get_module_name)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/acceptance/test_fr01_function_extraction.py (L111, L115, L119 import `_get_module_name` from `lib_code_parser.ast_extractor` — shim must preserve this import path)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/unit/test_ast_extractor.py (L8 imports `_get_module_name` from `lib_code_parser.ast_extractor` — same)
  </read_first>
  <behavior>
    - `from lib_code_parser.ast_extractor import _get_module_name` still resolves AND `_get_module_name is lib_code_parser._paths.get_module_name` (identity check — they are the same object)
    - Same for `callgraph_builder._get_module_name`, `type_dep_builder._get_module_name`, `contract_extractor._get_module_name`
    - Each extractor file no longer defines a local function body `def _get_module_name(path: str) -> str: return Path(path).stem` — only the import-as-alias shim line remains
    - `grep -rn "_get_module_name" lib_code_parser/` shows _paths.py as the only place a function body is defined; the 4 extractor files show only the shim alias (which counts as a reference, not a definition)
    - All existing tests pass (acceptance + unit) unchanged
  </behavior>
  <action>
    For each of the 4 extractor files (`lib_code_parser/ast_extractor.py`, `lib_code_parser/callgraph_builder.py`, `lib_code_parser/type_dep_builder.py`, `lib_code_parser/contract_extractor.py`):
    - Remove the local `def _get_module_name(path: str) -> str: return Path(path).stem` function body (3 lines per file).
    - Add at the top of the file (after existing imports): `from lib_code_parser._paths import get_module_name as _get_module_name  # ARC-04: single source of truth; preserves v0.1.0 private symbol export for test backward-compat`.
    - All other content of these extractor files MUST remain unchanged (extractor logic, helper functions like `_extract_annotation` / `_extract_params` / etc., regex patterns, frozenset constants). Phase 1 does NOT relocate these files to extractors/primitives/ — that is a Phase 2 deliverable. Phase 1 only patches the `_get_module_name` source.
    - If the file uses `Path` only via `_get_module_name`, you may remove the `from pathlib import Path` import to keep ruff happy (`ruff check` enforces F401 unused-import). If `Path` is used elsewhere in the file, leave the import.

    Create empty Phase 2-4 placeholder packages:
    - `lib_code_parser/frontends/__init__.py` — single-line file with docstring: `"""Frontends (Phase 2 adds python.py; Phase 4 adds cpp.py). Empty placeholder in Phase 1."""`
    - `lib_code_parser/extractors/__init__.py` — single-line file: `"""Extractors (Phase 2-4 add primitives/ and top-level evaluation modules). Empty placeholder in Phase 1."""`
    - `lib_code_parser/extractors/primitives/__init__.py` — single-line file: `"""Primitives extractors (Phase 2 implements functions/callgraph/type_deps/contracts). Empty placeholder in Phase 1."""`

    Do NOT also create `lib_code_parser/frontends/python.py` / `cpp.py` or any extractor implementation file — those are Phase 2-4 deliverables.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/acceptance/ tests/unit/ -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/acceptance/ tests/unit/ -x -q` exits 0 (all v0.1.0 acceptance tests pass + all v0.1.0 unit tests pass + new Plans 03-08 tests pass)
    - `from lib_code_parser.ast_extractor import _get_module_name` succeeds AND identity check: `python -c "from lib_code_parser.ast_extractor import _get_module_name; from lib_code_parser._paths import get_module_name; assert _get_module_name is get_module_name"` exits 0
    - Same identity check for `callgraph_builder`, `type_dep_builder`, `contract_extractor`
    - **HARD GATE (ROADMAP SC-3 finalizer)**: `grep -rn "^def _get_module_name\|^def get_module_name" lib_code_parser/ --include="*.py"` shows exactly one definition (in `_paths.py`); the 4 extractor files contain ONLY the import-as-alias shim (which `grep -rn "_get_module_name" lib_code_parser/` returns matches in 5 files but only `_paths.py` has a `def`). Concrete command: `[ $(grep -rn "^def _get_module_name\|^def get_module_name" lib_code_parser/ --include="*.py" | wc -l) -eq 1 ]`
    - Each of the 4 extractor files has `grep -c 'from lib_code_parser\._paths import get_module_name' <file>` returns exactly 1
    - Each of the 4 extractor files has `grep -c '^def _get_module_name' <file>` returns 0 (local def removed)
    - Placeholders exist: `test -f lib_code_parser/frontends/__init__.py && test -f lib_code_parser/extractors/__init__.py && test -f lib_code_parser/extractors/primitives/__init__.py` all return 0
    - The placeholders are EMPTY (one-line docstring at most): `[ $(wc -l < lib_code_parser/frontends/__init__.py) -le 2 ]` — Phase 2 will add real entries
    - `ruff check lib_code_parser/` exits 0 (no F401 unused-import errors from leftover `from pathlib import Path` in files that no longer use it)
  </acceptance_criteria>
  <done>4 v0.1.0 extractors patched (local _get_module_name replaced with shim from _paths.get_module_name); 3 Phase 2-4 placeholder packages created; pytest acceptance+unit suites both green; single-source-of-truth grep gate satisfies ROADMAP SC-3 hard gate.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Wave 0 parity test — tests/parity/test_v01_v02_compat.py</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/__init__.py (post-Task-1 output — verify 19-name re-export surface)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/conftest.py (existing EXAMPLE_SOURCE fixture — used as parity input)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-VALIDATION.md (Wave 0: tests/parity/test_v01_v02_compat.py — v0.1.0 caller surface + JSON byte-identical)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Pydantic v2 Generic — parity strategy + live byte-identical assertion)
  </read_first>
  <behavior>
    Tests in tests/parity/test_v01_v02_compat.py:
    - test_v01_caller_surface_intact: All 13 v0.1.0 names importable: CodeParserExecutor, ArtifactId, CallEdge, CallGraph, CodeContent, ContractInfo, FunctionNode, NormalizedArtifact, ParamInfo, ParserConfig, SourceRange, TraceTag, TypeDep — none is None.
    - test_v02_new_surface_present: All 6 v0.2.0 additions importable: CAV, EdgeKind, GraphEdge, GraphModel, GraphNode, GuardExpr.
    - test_version_bumped: `lib_code_parser.__version__ == "0.2.0"`.
    - test_no_duplicate_module_name_helper: ROADMAP SC-3 hard gate — invokes subprocess `["grep", "-rn", "^def _get_module_name", "lib_code_parser/", "--include=*.py"]` and asserts the result has exactly 0 matches OR `["grep", "-rn", "^def get_module_name", "lib_code_parser/", "--include=*.py"]` returns exactly 1 match in `_paths.py`. Use Python's `subprocess.run` with `shell=False` (using the project's own `lib_code_parser.adapters.base.run_subprocess` is acceptable but not required — a direct `subprocess.run([...], check=False, capture_output=True, text=True)` is fine for a test).
    - test_normalized_artifact_unparameterized_works: `NormalizedArtifact(artifact_id=ArtifactId(path="x"), artifact_type="code", content=CodeContent()).model_dump_json()` succeeds.
    - test_normalized_artifact_parameterized_works: `NormalizedArtifact[CodeContent](artifact_id=ArtifactId(path="x"), artifact_type="code", content=CodeContent()).model_dump_json()` succeeds.
    - test_normalized_artifact_json_byte_identical: The two model_dump_json() outputs above are byte-identical (D-06 parity gate from RESEARCH live-test).
    - test_executor_runs_on_example_source: Run `CodeParserExecutor().execute(ParserConfig(artifact_type="code", executor_lib="lib_code_parser"), b"def foo(): pass\n", "foo.py")` and assert result has at least 1 FunctionNode with `node_id == "foo.foo"` (v0.1.0 fixture parity end-to-end).
    - test_parser_config_unknown_field_raises: `ParserConfig(artifact_type="code", executor_lib="lib_code_parser", surprise=1)` raises ValidationError (ARC-05 hard gate).
    - test_edge_kind_rejects_uses: `GraphEdge(source="A", target="B", edge_type="uses")` raises ValidationError (SCH-03 hard gate; redundant with Plan 05 but kept here for ROADMAP SC-1 omnibus parity gate).
  </behavior>
  <action>
    Implement `tests/parity/__init__.py`:
    - Empty file or single-line docstring `"""v0.1.0 → v0.2.0 parity tests."""`.

    Implement `tests/parity/test_v01_v02_compat.py` per the `<behavior>` block above. Use absolute imports throughout. Use `from pydantic import ValidationError` (public alias, NOT `pydantic_core`). The grep-based test invokes subprocess to scan the actual file tree (not an in-memory check) so it catches any drift after Plan 09's patches. Place the parity tests in their own directory (`tests/parity/`) so the existing acceptance/unit hierarchy stays clean.

    Add a one-line entry to the `[tool.pytest.ini_options]` section of `pyproject.toml` ONLY if `testpaths` needs `parity` added — verify current value first. The current value is `testpaths = ["tests"]` (Plan 01 preserves this), which already auto-discovers tests/parity/ as a subdirectory. NO pyproject.toml change needed.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/parity/test_v01_v02_compat.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/parity/test_v01_v02_compat.py -x -q` exits 0 with all 10 tests passing
    - File `tests/parity/__init__.py` exists
    - File `tests/parity/test_v01_v02_compat.py` exists
    - `grep -c "def test_v01_caller_surface_intact" tests/parity/test_v01_v02_compat.py` returns exactly 1
    - `grep -c "def test_no_duplicate_module_name_helper" tests/parity/test_v01_v02_compat.py` returns exactly 1
    - `grep -c "def test_normalized_artifact_json_byte_identical" tests/parity/test_v01_v02_compat.py` returns exactly 1
    - FULL phase-level parity gate: `cd C:/work/agent_company/spec-reviewer-libs/lib-code-parser && pytest tests/ -x -q` exits 0 (entire test suite green: acceptance + unit + parity + Plans 03-08 Wave 0 tests)
    - `pytest tests/ --cov=lib_code_parser --cov-fail-under=80` exits 0 (coverage gate per Validation strategy; if 80% is unreachable for Phase 1 because frontends/extractors placeholders inflate the denominator, use `--cov-fail-under=70` instead and document the relaxation in the SUMMARY)
  </acceptance_criteria>
  <done>tests/parity/test_v01_v02_compat.py shipped with 10 tests including the ROADMAP SC-3 grep-based no-duplication hard gate; full phase test suite green; Plans 03-08 Wave 1 outputs verified to integrate cleanly.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| v0.1.0 caller → lib_code_parser public surface | Existing downstream code imports `from lib_code_parser import FunctionNode`; layout migration MUST NOT break this |
| extractor → centralized _paths module | All 4 extractors now shim through `_paths.get_module_name`; the shim must preserve `lib_code_parser.ast_extractor._get_module_name` as a private symbol because 2 existing test files import it |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-09-01 | Tampering | v0.1.0 caller breaks because import path changed | mitigate | Task 1 preserves all 13 v0.1.0 names in `lib_code_parser/__init__.py` `__all__` AND re-exports them via the `models/` package init AND keeps `from lib_code_parser.models import X` working; Task 3 parity test asserts all 13 names import successfully |
| T-09-02 | Tampering | Existing test files (test_fr01, test_ast_extractor) break because `_get_module_name` private symbol moved | mitigate | Task 2 keeps `lib_code_parser.ast_extractor._get_module_name` (and the other 3) as `from lib_code_parser._paths import get_module_name as _get_module_name` — the private symbol name survives at the same import path; identity check `_get_module_name is get_module_name` asserted in Task 3 parity tests |
| T-09-03 | Spoofing | Duplicate `_get_module_name` def survives in some extractor file undetected | mitigate | Task 2 and Task 3 acceptance both run the grep gate `grep -rn '^def _get_module_name\|^def get_module_name' lib_code_parser/ --include=*.py` and assert exactly 1 def (in _paths.py); this is the ROADMAP SC-3 hard gate |
| T-09-04 | Tampering | Generic NormalizedArtifact breaks JSON output for v0.1.0 callers (D-06 promise) | mitigate | Task 3 parity test `test_normalized_artifact_json_byte_identical` runs the live byte-identical assertion from RESEARCH (Plan 03 already asserts this at the model level; Plan 09 asserts it at the lib boundary) |
| T-09-05 | Supply chain | None — this plan only modifies source files; no new package installs | accept | No `pip install` invoked in this plan; pyproject.toml Phase 1 declarations from Plan 01 are referenced but not actuated |
</threat_model>

<verification>
- Full test suite green: `pytest tests/ -x -q` exits 0
- ROADMAP SC-3 hard gate: `grep -rn '^def _get_module_name\|^def get_module_name' lib_code_parser/ --include=*.py` returns exactly 1 line (in _paths.py)
- All 19 names (13 v0.1.0 + 6 v0.2.0) importable from `lib_code_parser`
- v0.1.0 models.py file deleted; models/ subpackage __init__.py re-exports legacy path
- 3 Phase 2-4 placeholder package directories created
- NormalizedArtifact unparameterized vs parameterized JSON byte-identical
- coverage >= 80% (or >= 70% with documented relaxation)
</verification>

<success_criteria>
- ROADMAP §Phase 1 Success Criterion 1 finalized: caller can write `from lib_code_parser.models import CAV, EdgeKind, GraphNode, GraphEdge, GraphModel, ParserConfig` and ALSO `from lib_code_parser import CAV, EdgeKind, ...` ✓
- ROADMAP §Phase 1 Success Criterion 3 finalized: grep gate satisfied — `_paths.py:get_module_name()` is the SOLE definition; the 4 v0.1.0 extractors carry only shim imports ✓
- ARC-01 substrate present: each model layer (infrastructure / primitives / evaluations) is importable independently (frontends/extractors empty placeholders mark Phase 2-4 extension points). Full ARC-01 (each extractor callable in isolation) is a Phase 2 deliverable when extractors actually exist as separate functions; Phase 1 only locks the import topology.
- ARC-04 + DET-04 finalized via parity grep gate
- D-06 parity asserted (byte-identical JSON live-tested)
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-09-SUMMARY.md` when done with: (1) pytest output for full suite (acceptance + unit + parity + plans 03-08); (2) grep output for the ROADMAP SC-3 hard gate (exactly 1 def line); (3) coverage % attained; (4) any documented coverage-gate relaxation rationale.
</output>
