---
phase: 01-architecture-foundation-spec-correction
plan: 03
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/models/__init__.py
  - lib_code_parser/models/infrastructure/__init__.py
  - lib_code_parser/models/infrastructure/cav.py
  - lib_code_parser/models/infrastructure/artifact.py
  - lib_code_parser/models/infrastructure/config.py
  - tests/unit/models/__init__.py
  - tests/unit/models/test_cav.py
  - tests/unit/models/test_config.py
  - tests/unit/models/test_artifact.py
autonomous: true
requirements: [SCH-02, ARC-05, ARC-02]
must_haves:
  truths:
    - "Caller can import CAV, NormalizedArtifact, ArtifactId, CodeContent, ParserConfig from lib_code_parser.models.infrastructure.* with no side effects"
    - "CAV is frozen + extra='forbid' + arbitrary_types_allowed and rejects unknown languages"
    - "NormalizedArtifact is a Pydantic Generic with TContent bound to BaseModel; unparameterized construction still works for v0.1.0 callers"
    - "ParserConfig is typed (no params: dict[str, object]) and rejects unknown fields with ValidationError"
    - "D-05: CAV ConfigDict(extra="forbid", arbitrary_types_allowed=True, frozen=True) enforces immutability via Pydantic v2 (Task 2)"
    - "D-06: NormalizedArtifact made Pydantic Generic (NormalizedArtifact[TContent]); v0.1.0 caller parity asserted via byte-identical JSON parity test (Task 3)"
    - "D-08: execute(config, raw_content, path) -> NormalizedArtifact[CodeContent] signature is stable; ParserConfig field names (enabled / language / extract_* / *_version) fixed as sibling-lib-reusable generic names (Task 2)"
  artifacts:
    - path: "lib_code_parser/models/infrastructure/cav.py"
      provides: "Common AST View envelope (single-parse contract)"
      contains: "class CAV"
    - path: "lib_code_parser/models/infrastructure/artifact.py"
      provides: "NormalizedArtifact[TContent] Generic + ArtifactId + CodeContent"
      contains: "Generic\\[TContent\\]|class NormalizedArtifact"
    - path: "lib_code_parser/models/infrastructure/config.py"
      provides: "Typed ParserConfig (ARC-05)"
      contains: "class ParserConfig"
    - path: "tests/unit/models/test_cav.py"
      provides: "CAV frozen + Literal discriminator assertions"
      contains: "test_cav"
  key_links:
    - from: "NormalizedArtifact"
      to: "TContent: TypeVar bound=BaseModel"
      via: "Pydantic v2 Generic"
      pattern: "Generic\\[TContent\\]"
    - from: "CAV"
      to: "ast.Module / clang.cindex.TranslationUnit"
      via: "payload: object + arbitrary_types_allowed=True"
      pattern: "arbitrary_types_allowed"
---

<objective>
Create the `models/infrastructure/` subpackage that holds lib-boundary I/O contracts per D-10 / D-14: CAV (Common AST View, D-04/D-05), NormalizedArtifact[TContent] Generic (D-06), ArtifactId, CodeContent aggregate, and typed ParserConfig (D-08 / ARC-05). All models use Pydantic v2 `ConfigDict(extra="forbid")` (SCH-02).

Purpose: Locks the lib's I/O envelope and the single-parse CAV contract before any extractor is written. Without this, Phase 2 extractors would each re-parse the AST (anti-pattern) and downstream callers would not see a typed config surface.

Output:
- `lib_code_parser/models/__init__.py` — parent package marker
- `lib_code_parser/models/infrastructure/__init__.py` — re-exports CAV / ArtifactId / NormalizedArtifact / CodeContent / ParserConfig
- `lib_code_parser/models/infrastructure/cav.py` — CAV (Pydantic frozen+arbitrary_types_allowed+extra=forbid)
- `lib_code_parser/models/infrastructure/artifact.py` — ArtifactId, NormalizedArtifact[TContent], CodeContent
- `lib_code_parser/models/infrastructure/config.py` — ParserConfig (typed fields per ARC-05)
- Wave 0 tests (Nyquist): tests/unit/models/test_cav.py / test_config.py / test_artifact.py
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/PROJECT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/REQUIREMENTS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-VALIDATION.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models.py

<interfaces>
<!-- Existing v0.1.0 contract — preserved as parity baseline; Plan 09 removes models.py after this plan ships its replacements. Do NOT edit models.py in this plan. -->

From lib_code_parser/models.py (v0.1.0):
```python
class ArtifactId(BaseModel):
    path: str
class CodeContent(BaseModel):
    functions: list[FunctionNode] = []
    call_graph: CallGraph = CallGraph()
    type_deps: list[TypeDep] = []
class NormalizedArtifact(BaseModel):
    artifact_id: ArtifactId
    artifact_type: str
    content: CodeContent
class ParserConfig(BaseModel):
    artifact_type: str
    executor_lib: str
    params: dict[str, object] = {}
    enabled: bool = True
```

The new contract MUST preserve v0.1.0 caller-visible field names AND add typed fields (Plan 09 wires the `__init__.py` re-exports). FunctionNode / CallEdge / CallGraph / TypeDep / ContractInfo / ParamInfo / SourceRange / TraceTag are owned by Plan 04 (models/primitives/), but `CodeContent` references them — use forward refs (`list["FunctionNode"]`) in CodeContent's field types to avoid a Plan 03 → Plan 04 ordering dependency.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Create models/__init__.py + models/infrastructure/ package scaffolding</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md (Pydantic v2 model conventions, absolute imports, snake_case, naming rules)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/__init__.py (current v0.1.0 public surface — for parity reference; NOT modified in this plan)
  </read_first>
  <behavior>
    - `from lib_code_parser.models.infrastructure import CAV, ArtifactId, NormalizedArtifact, CodeContent, ParserConfig` succeeds
    - `lib_code_parser.models` is recognized as a package (has `__init__.py`)
    - `lib_code_parser.models.infrastructure` is recognized as a package
    - Importing these does not trigger side effects (no network, no I/O, no file writes)
  </behavior>
  <action>
    Create the package skeleton:
    1. `lib_code_parser/models/__init__.py` — empty docstring "Subpackages: infrastructure, primitives, evaluations." (parent marker, no re-exports here; the lib-level `__init__.py` re-export is owned by Plan 09).
    2. `lib_code_parser/models/infrastructure/__init__.py` — re-export `CAV`, `ArtifactId`, `NormalizedArtifact`, `CodeContent`, `ParserConfig` from the three sibling modules (cav.py, artifact.py, config.py). Use `__all__` to declare the public surface. Use absolute imports (`from lib_code_parser.models.infrastructure.cav import CAV`) per CONVENTIONS.md.
    3. `tests/unit/models/__init__.py` — empty file (pytest package marker).
    Files cav.py / artifact.py / config.py are implemented in Tasks 2 / 3. This task only creates the package shells and the import surface; the re-export imports will resolve once Tasks 2 / 3 land.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; python -c "import lib_code_parser.models; import lib_code_parser.models.infrastructure"</automated>
  </verify>
  <acceptance_criteria>
    - `lib_code_parser/models/__init__.py` exists (file, not directory) with module docstring
    - `lib_code_parser/models/infrastructure/__init__.py` exists, contains `__all__` listing exactly `["CAV", "ArtifactId", "NormalizedArtifact", "CodeContent", "ParserConfig"]`
    - `lib_code_parser/models/infrastructure/__init__.py` uses absolute imports: `grep "^from lib_code_parser\\.models\\.infrastructure\\." lib_code_parser/models/infrastructure/__init__.py` returns >= 3 matches (cav, artifact, config)
    - `grep "^from \\." lib_code_parser/models/infrastructure/__init__.py` returns 0 matches (no relative imports — CONVENTIONS.md rule)
    - `tests/unit/models/__init__.py` exists (zero or one line, package marker)
    - After Tasks 2-3 complete: `python -c "from lib_code_parser.models.infrastructure import CAV, ArtifactId, NormalizedArtifact, CodeContent, ParserConfig"` exits 0
  </acceptance_criteria>
  <done>Package scaffolding for models/infrastructure/ created; imports resolve after Tasks 2-3.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement CAV + ParserConfig with Wave 0 tests</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Pydantic v2 Generic — exact pinned form for CAV and ParserConfig; D-04, D-05, D-08 codified there; live-tested with Pydantic 2.11.10)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-VALIDATION.md (Wave 0 test list: tests/unit/test_cav.py and tests/unit/test_config.py — to be placed under tests/unit/models/ per package structure in Task 1)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models.py (v0.1.0 ParserConfig — preserve `artifact_type: str`, `executor_lib: str`, `enabled: bool = True` field names; remove `params` per ARC-05)
  </read_first>
  <behavior>
    CAV tests (tests/unit/models/test_cav.py):
    - `test_cav_constructs_with_python_payload`: `CAV(language="python", path="foo.py", payload=ast.parse("x=1"))` succeeds and `cav.payload` is the parsed `ast.Module`
    - `test_cav_rejects_unknown_language`: `CAV(language="java", path="x.java", payload=None)` raises `ValidationError`
    - `test_cav_is_frozen`: After construction, `cav.language = "cpp"` raises `ValidationError` (or `TypeError`/`pydantic_core._pydantic_core.ValidationError` — Pydantic v2 raises ValidationError for `frozen=True` mutation attempts)
    - `test_cav_rejects_extra_fields`: `CAV(language="python", path="x", payload=None, extra="surprise")` raises `ValidationError`
    ParserConfig tests (tests/unit/models/test_config.py):
    - `test_parser_config_typed_fields`: `ParserConfig(artifact_type="code", executor_lib="lib_code_parser", language="python", extract_contracts=True, compile_args=["-std=c++17"], python_version="3.12", enabled=True)` succeeds with all field values accessible
    - `test_parser_config_defaults`: `ParserConfig(artifact_type="code", executor_lib="lib_code_parser")` succeeds with `language="python"`, `extract_contracts=True`, `compile_args=["-std=c++17"]`, `python_version="3.12"`, `enabled=True` as defaults
    - `test_parser_config_rejects_unknown_field`: `ParserConfig(artifact_type="code", executor_lib="lib_code_parser", unknown_field=1)` raises `ValidationError` (SCH-02 / ARC-05 unknown-field rejection)
    - `test_parser_config_language_literal`: `ParserConfig(artifact_type="code", executor_lib="lib_code_parser", language="rust")` raises `ValidationError` (Literal type constraint)
    - `test_parser_config_no_params_dict_field`: `ParserConfig.model_fields` does NOT contain a key named `params` (ARC-05 — the v0.1.0 untyped params dict is gone)
  </behavior>
  <action>
    Implement `lib_code_parser/models/infrastructure/cav.py`:
    - Module docstring: 'Common AST View (CAV) — single-parse envelope shared by all extractors. Implements ARC-02, satisfies D-04/D-05. Traces: ARC-02.'
    - Class `CAV(BaseModel)` with `model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True, frozen=True)`.
    - Fields exactly: `language: Literal["python", "cpp"]`, `path: str`, `payload: object`.
    - Use `from __future__ import annotations`, `from typing import Literal`, `from pydantic import BaseModel, ConfigDict`.

    Implement `lib_code_parser/models/infrastructure/config.py`:
    - Module docstring: 'Typed ParserConfig (ARC-05). Replaces v0.1.0 untyped `params: dict[str, object]` with explicit typed fields per D-08. Traces: ARC-05, SCH-02.'
    - Class `ParserConfig(BaseModel)` with `model_config = ConfigDict(extra="forbid")`.
    - Fields exactly: `artifact_type: str` (no default — required, preserves v0.1.0 surface), `executor_lib: str` (no default — required, preserves v0.1.0 surface), `enabled: bool = True` (preserves v0.1.0 default), `language: Literal["python", "cpp"] = "python"` (new typed field per ARC-05), `extract_contracts: bool = True` (new typed field per ARC-05), `compile_args: list[str] = Field(default_factory=lambda: ["-std=c++17"])` (new typed field; use default_factory to avoid mutable default ruff B008 — per PITFALLS guidance), `python_version: str = "3.12"` (new typed field per ARC-05).
    - DO NOT include a `params` field. ARC-05 is satisfied only if `params` is fully absent from the model.
    - Imports: `from __future__ import annotations`, `from typing import Literal`, `from pydantic import BaseModel, ConfigDict, Field`.

    Implement tests `tests/unit/models/test_cav.py` and `tests/unit/models/test_config.py` per the `<behavior>` block above. Tests use `pytest.raises(ValidationError)` from `pydantic` (NOT `pydantic_core.ValidationError` — use the public alias for stability). Use the existing pytest configuration (`tests/conftest.py` is unchanged in Phase 1).
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/models/test_cav.py tests/unit/models/test_config.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/models/test_cav.py -x -q` exits 0 with all 4 tests passing
    - `pytest tests/unit/models/test_config.py -x -q` exits 0 with all 5 tests passing
    - `grep -c 'class CAV(BaseModel)' lib_code_parser/models/infrastructure/cav.py` returns exactly 1
    - `grep -c 'frozen=True' lib_code_parser/models/infrastructure/cav.py` returns >= 1
    - `grep -c 'arbitrary_types_allowed=True' lib_code_parser/models/infrastructure/cav.py` returns >= 1
    - `grep -c 'extra="forbid"' lib_code_parser/models/infrastructure/cav.py` returns >= 1
    - `grep -c 'Literal\["python", "cpp"\]' lib_code_parser/models/infrastructure/cav.py` returns >= 1
    - `grep -c 'class ParserConfig(BaseModel)' lib_code_parser/models/infrastructure/config.py` returns exactly 1
    - `grep -c 'extra="forbid"' lib_code_parser/models/infrastructure/config.py` returns >= 1
    - `grep -c '^ *params:' lib_code_parser/models/infrastructure/config.py` returns 0 (no `params` field — ARC-05 hard gate)
    - `grep -c 'language: Literal\["python", "cpp"\]' lib_code_parser/models/infrastructure/config.py` returns >= 1
    - `grep -c 'compile_args' lib_code_parser/models/infrastructure/config.py` returns >= 1
    - `grep -c 'default_factory' lib_code_parser/models/infrastructure/config.py` returns >= 1 (compile_args uses default_factory, not mutable default)
    - Both files have module docstrings declaring REQ-IDs (TRC-02 substrate): `head -3 lib_code_parser/models/infrastructure/cav.py | grep -c "Traces:"` returns 1
  </acceptance_criteria>
  <done>CAV and ParserConfig implemented with extra=forbid, frozen=True (CAV), Literal discriminators, typed fields per ARC-05, Wave 0 unit tests all passing.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Implement ArtifactId + NormalizedArtifact[TContent] Generic + CodeContent</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Pydantic v2 Generic — verified live with Pydantic 2.11.10 that `Envelope(...)` and `Envelope[Inner](...)` produce byte-identical JSON; D-06 implementation pinned here)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models.py (v0.1.0 CodeContent: `functions: list[FunctionNode] = []`, `call_graph: CallGraph = CallGraph()`, `type_deps: list[TypeDep] = []` — preserve field names; primitives types come from Plan 04 — use forward references)
  </read_first>
  <behavior>
    Tests in tests/unit/models/test_artifact.py:
    - `test_artifact_id_basic`: `ArtifactId(path="src/foo.py")` succeeds, `.path == "src/foo.py"`
    - `test_artifact_id_rejects_extra_field`: `ArtifactId(path="x", unknown=1)` raises `ValidationError`
    - `test_artifact_id_frozen`: After construction, `aid.path = "y"` raises `ValidationError` (frozen=True per RESEARCH §Pydantic v2 Generic ArtifactId pattern)
    - `test_code_content_default_empty`: `CodeContent()` succeeds with `functions == []`, `type_deps == []`; `call_graph` is a CallGraph-shaped value (forward-ref placeholder is OK at this stage — Plan 04 lands the real CallGraph model and CodeContent will auto-resolve)
    - `test_normalized_artifact_constructible_unparameterized`: `NormalizedArtifact(artifact_id=ArtifactId(path="x"), artifact_type="code", content=CodeContent())` succeeds — the v0.1.0 caller form, no Generic parameter (D-06 parity)
    - `test_normalized_artifact_constructible_parameterized`: `NormalizedArtifact[CodeContent](artifact_id=ArtifactId(path="x"), artifact_type="code", content=CodeContent())` succeeds — the typed v0.2.0 form
    - `test_normalized_artifact_json_parity`: `NormalizedArtifact(artifact_id=..., artifact_type=..., content=...).model_dump_json()` equals `NormalizedArtifact[CodeContent](artifact_id=..., artifact_type=..., content=...).model_dump_json()` for the same field values — byte-identical (RESEARCH live-test asserts this; D-06 parity)
    - `test_normalized_artifact_rejects_extra_field`: `NormalizedArtifact(artifact_id=..., artifact_type=..., content=..., extra="x")` raises `ValidationError`
  </behavior>
  <action>
    Implement `lib_code_parser/models/infrastructure/artifact.py`:
    - Module docstring: 'Artifact envelope models — ArtifactId, NormalizedArtifact[TContent] (Generic per D-06), CodeContent aggregate. Traces: ARC-02, SCH-02.'
    - Imports: `from __future__ import annotations`, `from typing import Generic, TypeVar, TYPE_CHECKING`, `from pydantic import BaseModel, ConfigDict, Field`.
    - Inside `if TYPE_CHECKING:` block (so Plan 03 has no import-time dependency on Plan 04): forward-import the primitives types for CodeContent's annotations — `from lib_code_parser.models.primitives.functions import FunctionNode`, `from lib_code_parser.models.primitives.callgraph import CallGraph`, `from lib_code_parser.models.primitives.type_deps import TypeDep`, `from lib_code_parser.models.primitives.contracts import ContractInfo`. Use string-form forward refs (e.g., `list["FunctionNode"]`) on the CodeContent field types.
    - `TContent = TypeVar("TContent", bound=BaseModel)`.
    - Class `ArtifactId(BaseModel)`: `model_config = ConfigDict(extra="forbid", frozen=True)`; field `path: str`.
    - Class `CodeContent(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields: `functions: list["FunctionNode"] = Field(default_factory=list)`, `call_graph: "CallGraph" = Field(default_factory=lambda: __import__("lib_code_parser.models.primitives.callgraph", fromlist=["CallGraph"]).CallGraph())` (use lazy import in the default factory to avoid hard-cycling on Plan 04 at import time — once Plan 04 lands, the import resolves on first instantiation), `type_deps: list["TypeDep"] = Field(default_factory=list)`, `contracts: dict[str, "ContractInfo"] = Field(default_factory=dict)` (new v0.2.0 field per D-04 / AST-04 — keyed by class node_id). For Phase 1 robustness, the lazy-import factory MAY be replaced with a simpler `Field(default=None)` for `call_graph` IF the test allows; preferred form is lazy factory to mirror v0.1.0 default semantics.
    - Class `NormalizedArtifact(BaseModel, Generic[TContent])`: `model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)`; fields `artifact_id: ArtifactId`, `artifact_type: str`, `content: TContent`. Use Generic exactly as in RESEARCH §Pydantic v2 Generic live-tested pattern.
    - At module bottom, call `CodeContent.model_rebuild()` if forward refs require it (Pydantic 2.11 typically auto-resolves; include the rebuild call as defense-in-depth — comment: "Resolve forward refs from primitives subpackage; harmless no-op if already resolved").

    Implement `tests/unit/models/test_artifact.py` per the `<behavior>` block above. Important: the `test_code_content_default_empty` test must NOT instantiate CallGraph directly (Plan 04 owns it); test only that `CodeContent()` succeeds and `cc.functions == []` and `cc.type_deps == []`. The call_graph field check is satisfied if `hasattr(cc, "call_graph")` is True after Plan 04 lands.

    Cross-plan note: This task ships with forward refs (string annotations) so Plan 03 can ship without waiting for Plan 04. Once Plan 04 lands the primitive models and Plan 09 wires the lib `__init__.py`, the forward refs resolve transparently. If `test_code_content_default_empty` fails at this stage because Plan 04 hasn't shipped yet, mark the affected assertions as `pytest.mark.skip(reason="Resolves after Plan 04 ships primitives")` — but the structural tests (test_artifact_id_*, test_normalized_artifact_*) MUST pass independently.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/models/test_artifact.py -x -q -k "not test_code_content_default_empty"</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/models/test_artifact.py -x -q -k "not test_code_content_default_empty"` exits 0 (CodeContent default-empty test is allowed to skip until Plan 04 lands; all 6 other tests pass independently of Plan 04)
    - `grep -c 'class ArtifactId(BaseModel)' lib_code_parser/models/infrastructure/artifact.py` returns exactly 1
    - `grep -c 'class CodeContent(BaseModel)' lib_code_parser/models/infrastructure/artifact.py` returns exactly 1
    - `grep -c 'class NormalizedArtifact(BaseModel, Generic\[TContent\])' lib_code_parser/models/infrastructure/artifact.py` returns exactly 1
    - `grep -c 'TContent = TypeVar' lib_code_parser/models/infrastructure/artifact.py` returns exactly 1
    - `grep -c 'bound=BaseModel' lib_code_parser/models/infrastructure/artifact.py` returns exactly 1
    - `grep -c 'extra="forbid"' lib_code_parser/models/infrastructure/artifact.py` returns >= 3 (one per model)
    - `grep -c 'frozen=True' lib_code_parser/models/infrastructure/artifact.py` returns >= 1 (ArtifactId)
    - `grep -c 'default_factory' lib_code_parser/models/infrastructure/artifact.py` returns >= 2 (list/dict fields use factory, not mutable default)
    - Parity assertion: `python -c "from lib_code_parser.models.infrastructure.artifact import NormalizedArtifact, ArtifactId, CodeContent; a=NormalizedArtifact(artifact_id=ArtifactId(path='x'), artifact_type='code', content=CodeContent()); b=NormalizedArtifact[CodeContent](artifact_id=ArtifactId(path='x'), artifact_type='code', content=CodeContent()); assert a.model_dump_json() == b.model_dump_json(), 'parity broken'"` exits 0 (D-06 live parity check)
    - File has module docstring with `Traces:` tag (TRC-02 substrate)
  </acceptance_criteria>
  <done>ArtifactId, NormalizedArtifact[TContent] Generic, and CodeContent shipped with extra=forbid + (ArtifactId) frozen=True; parameterized vs unparameterized JSON parity asserted; tests pass independently of Plan 04 forward refs.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| caller → ParserConfig | Untyped/unknown fields cross into the lib; SCH-02 + ARC-05 catch them via Pydantic ValidationError |
| caller → CAV payload | Caller passes opaque AST tree; `arbitrary_types_allowed=True` accepts non-Pydantic objects but Pydantic still enforces frozen / language Literal / extra="forbid" |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-03-01 | Tampering | Unknown-field schema drift (cross-lib Pitfall 6) | mitigate | All 5 models (CAV / ArtifactId / NormalizedArtifact / CodeContent / ParserConfig) set `extra="forbid"`; grep gates assert presence |
| T-03-02 | Tampering | CAV payload mutation between extractors | mitigate | CAV `frozen=True`; test asserts mutation raises ValidationError |
| T-03-03 | Tampering | v0.1.0 caller breaks due to Generic-rewrite | mitigate | Task 3 live parity assertion: byte-identical JSON between unparameterized and parameterized construction (D-06 RESEARCH live test) |
| T-03-04 | Spoofing | Unknown `language` value passed via ParserConfig or CAV | mitigate | `Literal["python", "cpp"]` discriminator on both; test asserts ValidationError on "java", "rust" |
| T-03-05 | Tampering | Mutable default trap (`= []` / `= {}`) | mitigate | All list/dict fields use `Field(default_factory=...)` per PITFALLS §5 |
</threat_model>

<verification>
- `pytest tests/unit/models/ -x -q` (Plan 03 subset) returns >= 13 passing tests (1 may skip if Plan 04 not yet shipped; structural tests independent)
- All 5 infrastructure model classes have `extra="forbid"` ConfigDict
- ParserConfig has NO `params` field (ARC-05 hard gate)
- CAV `frozen=True` + `Literal["python","cpp"]` discriminator + `arbitrary_types_allowed=True` all present
- NormalizedArtifact is `Generic[TContent]` with `bound=BaseModel`
- Unparameterized and parameterized NormalizedArtifact produce byte-identical JSON (live parity check passes)
</verification>

<success_criteria>
- ROADMAP §Phase 1 Success Criterion 1 partial: caller can import `from lib_code_parser.models.infrastructure import CAV, ParserConfig` (the final `from lib_code_parser.models import ...` flat surface is wired in Plan 09)
- ROADMAP §Phase 1 Success Criterion 2: `ParserConfig(language="python", extract_contracts=True, compile_args=["-std=c++17"], python_version="3.12")` succeeds AND `ParserConfig(unknown_field=1)` raises ValidationError ✓
- SCH-02 satisfied for infrastructure layer (extra="forbid" on all 5 models)
- ARC-05 satisfied (params dict eliminated)
- ARC-02 substrate in place (CAV envelope ready; Plan 09 / Phase 2 will wire frontend single-parse contract)
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-03-SUMMARY.md` when done, including pytest output for tests/unit/models/test_cav.py + test_config.py + test_artifact.py and grep verification of structural acceptance criteria.
</output>
