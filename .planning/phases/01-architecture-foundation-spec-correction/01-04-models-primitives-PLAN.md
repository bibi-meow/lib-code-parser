---
phase: 01-architecture-foundation-spec-correction
plan: 04
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/models/primitives/__init__.py
  - lib_code_parser/models/primitives/functions.py
  - lib_code_parser/models/primitives/callgraph.py
  - lib_code_parser/models/primitives/type_deps.py
  - lib_code_parser/models/primitives/contracts.py
  - tests/unit/models/test_primitives_extra_forbid.py
autonomous: true
requirements: [SCH-02]
must_haves:
  truths:
    - "Caller can import FunctionNode, ParamInfo, SourceRange, TraceTag, CallEdge, CallGraph, TypeDep, ContractInfo from lib_code_parser.models.primitives.* with no side effects"
    - "All 8 primitive models declare ConfigDict(extra='forbid') and reject unknown fields with ValidationError"
    - "v0.1.0 field names and default values preserved (parity surface for Plan 09 to wire)"
    - "ContractInfo gains source_kind discriminator (Pydantic v2 validator vs dataclass __post_init__) per D-04 / AST-04 substrate"
  artifacts:
    - path: "lib_code_parser/models/primitives/functions.py"
      provides: "FunctionNode, ParamInfo, SourceRange, TraceTag (v0.1.0 field parity)"
      contains: "class FunctionNode|class ParamInfo|class SourceRange|class TraceTag"
    - path: "lib_code_parser/models/primitives/callgraph.py"
      provides: "CallEdge, CallGraph"
      contains: "class CallEdge|class CallGraph"
    - path: "lib_code_parser/models/primitives/type_deps.py"
      provides: "TypeDep"
      contains: "class TypeDep"
    - path: "lib_code_parser/models/primitives/contracts.py"
      provides: "ContractInfo with source_kind discriminator (Phase 1 substrate for AST-04)"
      contains: "class ContractInfo"
  key_links:
    - from: "ContractInfo"
      to: "source_kind discriminator"
      via: "Literal[pydantic_validator, pydantic_model_validator, pydantic_field_validator, dataclass_post_init]"
      pattern: "source_kind"
---

<objective>
Create the `models/primitives/` subpackage holding intermediate-data Pydantic models per D-10 / D-14: FunctionNode aggregate + leaf types (functions.py); CallEdge, CallGraph (callgraph.py); TypeDep (type_deps.py); ContractInfo (contracts.py). All models use Pydantic v2 `ConfigDict(extra="forbid")` (SCH-02). Per D-14, these are intermediate data shapes consumed by extractors — NOT verifier-facing — but remain part of the caller-visible public surface (Plan 09 re-exports from `lib_code_parser`).

Purpose: Locks the v0.1.0 primitive schema with Phase 1 SCH-02 hardening (extra="forbid") and adds the AST-04 schema substrate (`source_kind` discriminator on ContractInfo). Plan 03 (infrastructure) and Plan 04 (primitives) ship independently in Wave 1.

Output:
- 4 new primitive model files preserving v0.1.0 field names + adding extra="forbid"
- `ContractInfo.source_kind: Literal[...]` field added per AST-04 substrate
- One Wave 0 omnibus test asserting SCH-02 on all primitive models
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models.py

<interfaces>
<!-- v0.1.0 model definitions from lib_code_parser/models.py — preserve field names and defaults EXACTLY. Phase 1 only adds: (1) ConfigDict(extra="forbid") on every model (SCH-02), (2) ContractInfo gains node_id + source_kind Literal discriminator + postconditions list (per AST-04 / D-04 RESEARCH substrate). Plan 09 deletes the old models.py after this plan ships replacements. -->

v0.1.0 surface (from lib_code_parser/models.py):

class TraceTag(BaseModel): tag: str ; refs: list[str] = []
class SourceRange(BaseModel): start_line: int ; end_line: int
class ParamInfo(BaseModel): name: str ; type_annotation: str = ""
class ContractInfo(BaseModel): preconditions: list[str] = [] ; invariants: list[str] = []
class FunctionNode(BaseModel): node_id: str ; kind: str ; params: list[ParamInfo] = [] ; return_type: str = "" ; contracts: ContractInfo = ContractInfo() ; docstring: str = "" ; trace_tags: list[TraceTag] = [] ; source_range: SourceRange = SourceRange(start_line=0, end_line=0)
class CallEdge(BaseModel): caller: str ; callee: str
class CallGraph(BaseModel): nodes: list[str] = [] ; edges: list[CallEdge] = []
class TypeDep(BaseModel): source: str ; target: str ; kind: str = "uses"

Note: TypeDep.kind default is the string "uses" (v0.1.0). DO NOT change this to EdgeKind Literal — primitives layer is verifier-INVISIBLE per D-14; the closed EdgeKind Literal applies only to models/evaluations/graph_base.py (Plan 05).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement functions.py + callgraph.py</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models.py (v0.1.0 source — preserve field names + defaults)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md (Pydantic v2 conventions, absolute imports, mutable defaults via Field(default_factory=list))
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Pydantic v2 Generic Pitfall 5 — mutable default trap; uses Field(default_factory=...))
  </read_first>
  <behavior>
    - Importing functions.py succeeds with no side effects
    - FunctionNode(node_id="foo", kind="function") constructs with defaults; .params == [] ; .trace_tags == [] ; .source_range.start_line == 0
    - FunctionNode(node_id="x", kind="function", unknown_field=1) raises ValidationError
    - CallGraph() constructs with nodes == [] and edges == []
    - CallEdge(caller="a", callee="b") constructs; CallEdge(caller="a", callee="b", extra="x") raises ValidationError
    - ParamInfo, SourceRange, TraceTag constructable with v0.1.0 field surface; all reject unknown fields
  </behavior>
  <action>
    Implement `lib_code_parser/models/primitives/functions.py`:
    - Module docstring: "Primitive AST data models — FunctionNode aggregate and its leaf types (ParamInfo, SourceRange, TraceTag). Traces: SCH-02. Phase 2 fills these via extract_functions()."
    - Imports: `from __future__ import annotations`, `from typing import TYPE_CHECKING`, `from pydantic import BaseModel, ConfigDict, Field`. Under `if TYPE_CHECKING:` add `from lib_code_parser.models.primitives.contracts import ContractInfo` (forward ref for FunctionNode.contracts annotation).
    - Class `TraceTag(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields: `tag: str`, `refs: list[str] = Field(default_factory=list)`.
    - Class `SourceRange(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields: `start_line: int`, `end_line: int`.
    - Class `ParamInfo(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields: `name: str`, `type_annotation: str = ""`.
    - Class `FunctionNode(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields exactly: `node_id: str`, `kind: str` with inline comment `# "function" | "method" | "class"` (preserve plain str per v0.1.0 parity — promoting to Literal would break v0.1.0 callers that pass any-string kind), `params: list[ParamInfo] = Field(default_factory=list)`, `return_type: str = ""`, `contracts: "ContractInfo" = Field(default_factory=lambda: __import__("lib_code_parser.models.primitives.contracts", fromlist=["ContractInfo"]).ContractInfo())` (lazy import in factory to avoid hard import-time cycle if needed; the forward-ref string `"ContractInfo"` is resolved by Pydantic at validation time), `docstring: str = ""`, `trace_tags: list[TraceTag] = Field(default_factory=list)`, `source_range: SourceRange = Field(default_factory=lambda: SourceRange(start_line=0, end_line=0))`.
    - At module bottom: `from lib_code_parser.models.primitives.contracts import ContractInfo  # noqa: E402` then `FunctionNode.model_rebuild()` (resolve the forward ref deterministically).

    Implement `lib_code_parser/models/primitives/callgraph.py`:
    - Module docstring: "Primitive call graph models — CallEdge, CallGraph. Traces: SCH-02. Phase 2 fills these via build_callgraph()."
    - Imports: `from __future__ import annotations`, `from pydantic import BaseModel, ConfigDict, Field`.
    - Class `CallEdge(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields: `caller: str`, `callee: str`.
    - Class `CallGraph(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields: `nodes: list[str] = Field(default_factory=list)`, `edges: list[CallEdge] = Field(default_factory=list)`.

    DO NOT add `EdgeKind` Literal in either file — that belongs in Plan 05 (`models/evaluations/graph_base.py`) per D-14 layer purity.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; python -c "from lib_code_parser.models.primitives.functions import FunctionNode, ParamInfo, SourceRange, TraceTag; from lib_code_parser.models.primitives.callgraph import CallEdge, CallGraph; fn=FunctionNode(node_id='x', kind='function'); cg=CallGraph(); ce=CallEdge(caller='a', callee='b'); print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `python -c "from lib_code_parser.models.primitives.functions import FunctionNode, ParamInfo, SourceRange, TraceTag"` exits 0
    - `python -c "from lib_code_parser.models.primitives.callgraph import CallEdge, CallGraph"` exits 0
    - `grep -c 'class FunctionNode(BaseModel)' lib_code_parser/models/primitives/functions.py` returns exactly 1
    - `grep -c 'class ParamInfo(BaseModel)' lib_code_parser/models/primitives/functions.py` returns exactly 1
    - `grep -c 'class SourceRange(BaseModel)' lib_code_parser/models/primitives/functions.py` returns exactly 1
    - `grep -c 'class TraceTag(BaseModel)' lib_code_parser/models/primitives/functions.py` returns exactly 1
    - `grep -c 'class CallEdge(BaseModel)' lib_code_parser/models/primitives/callgraph.py` returns exactly 1
    - `grep -c 'class CallGraph(BaseModel)' lib_code_parser/models/primitives/callgraph.py` returns exactly 1
    - `grep -c 'extra="forbid"' lib_code_parser/models/primitives/functions.py` returns >= 4
    - `grep -c 'extra="forbid"' lib_code_parser/models/primitives/callgraph.py` returns >= 2
    - `grep -c 'default_factory' lib_code_parser/models/primitives/functions.py` returns >= 4 (params, trace_tags, source_range, contracts)
    - `grep -c 'default_factory' lib_code_parser/models/primitives/callgraph.py` returns >= 2 (nodes, edges)
    - `grep -v '^#' lib_code_parser/models/primitives/functions.py | grep -c 'EdgeKind'` returns 0 (D-14 layer purity — primitives MUST NOT reference EdgeKind)
    - `grep -v '^#' lib_code_parser/models/primitives/callgraph.py | grep -c 'EdgeKind'` returns 0
    - Both files have module docstrings with `Traces:` tag (TRC-02 substrate)
  </acceptance_criteria>
  <done>FunctionNode + leaf types + CallEdge + CallGraph implemented with extra="forbid", v0.1.0 field parity preserved, default_factory used for all list defaults, no EdgeKind leakage.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement type_deps.py + contracts.py (TypeDep + ContractInfo with source_kind)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models.py (v0.1.0 TypeDep and ContractInfo)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (D-14 layer purity for TypeDep.kind; D-04 / AST-04 substrate for ContractInfo source_kind values)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/REQUIREMENTS.md (AST-04: distinguish Pydantic v2 field_validator / model_validator / validator from dataclass __post_init__ — 4 values)
  </read_first>
  <behavior>
    - TypeDep(source="a", target="b") succeeds with default kind == "uses"
    - TypeDep(source="a", target="b", unknown=1) raises ValidationError
    - ContractInfo() succeeds with default node_id == "", source_kind == "pydantic_validator", empty preconditions/invariants/postconditions
    - ContractInfo(node_id="x", source_kind="dataclass_post_init") succeeds
    - ContractInfo(node_id="x", source_kind="bogus") raises ValidationError (Literal constraint)
    - ContractInfo(node_id="x", extra="y") raises ValidationError
  </behavior>
  <action>
    Implement `lib_code_parser/models/primitives/type_deps.py`:
    - Module docstring: "Primitive type-dependency model — TypeDep. Traces: SCH-02. Phase 2 fills via build_type_deps(). NOTE: TypeDep.kind is a free-form str at the primitives layer per D-14; the closed EdgeKind Literal applies only to verifier-facing evaluations/."
    - Imports: `from __future__ import annotations`, `from pydantic import BaseModel, ConfigDict`.
    - Class `TypeDep(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields exactly: `source: str`, `target: str`, `kind: str = "uses"` (v0.1.0 default preserved; D-14 primitives layer purity).

    Implement `lib_code_parser/models/primitives/contracts.py`:
    - Module docstring: "Primitive contract model — ContractInfo with source_kind discriminator per AST-04. Distinguishes Pydantic validator decorators from dataclass __post_init__ per D-04 substrate. Traces: SCH-02, AST-04."
    - Imports: `from __future__ import annotations`, `from typing import Literal`, `from pydantic import BaseModel, ConfigDict, Field`.
    - Class `ContractInfo(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields exactly: `node_id: str = ""` (new — Phase 1 substrate; default empty string preserves the v0.1.0 default-construction usage `ContractInfo()` from FunctionNode.contracts default factory), `source_kind: Literal["pydantic_validator", "pydantic_model_validator", "pydantic_field_validator", "dataclass_post_init"] = "pydantic_validator"` (AST-04 discriminator; default "pydantic_validator" because v0.1.0 unconditionally tagged everything as Pydantic — Phase 2 will set the correct value at extraction time), `preconditions: list[str] = Field(default_factory=list)` (v0.1.0 preserved), `invariants: list[str] = Field(default_factory=list)` (v0.1.0 preserved), `postconditions: list[str] = Field(default_factory=list)` (new — AST-04 substrate for Phase 3 SPC-01 docstring pre/post extraction).
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; python -c "from lib_code_parser.models.primitives.type_deps import TypeDep; from lib_code_parser.models.primitives.contracts import ContractInfo; td=TypeDep(source='a', target='b'); ci=ContractInfo(node_id='x'); assert td.kind == 'uses', repr(td.kind); assert ci.source_kind == 'pydantic_validator', repr(ci.source_kind); print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `python -c "from lib_code_parser.models.primitives.type_deps import TypeDep"` exits 0
    - `python -c "from lib_code_parser.models.primitives.contracts import ContractInfo"` exits 0
    - `grep -c 'class TypeDep(BaseModel)' lib_code_parser/models/primitives/type_deps.py` returns exactly 1
    - `grep -c 'kind: str = "uses"' lib_code_parser/models/primitives/type_deps.py` returns exactly 1 (v0.1.0 default preserved — D-14)
    - `grep -c 'class ContractInfo(BaseModel)' lib_code_parser/models/primitives/contracts.py` returns exactly 1
    - `grep -c 'source_kind:' lib_code_parser/models/primitives/contracts.py` returns exactly 1
    - `grep -c 'pydantic_validator' lib_code_parser/models/primitives/contracts.py` returns >= 1
    - `grep -c 'pydantic_model_validator' lib_code_parser/models/primitives/contracts.py` returns >= 1
    - `grep -c 'pydantic_field_validator' lib_code_parser/models/primitives/contracts.py` returns >= 1
    - `grep -c 'dataclass_post_init' lib_code_parser/models/primitives/contracts.py` returns >= 1
    - `grep -c 'postconditions' lib_code_parser/models/primitives/contracts.py` returns >= 1 (new field present)
    - `grep -c 'extra="forbid"' lib_code_parser/models/primitives/type_deps.py` returns >= 1
    - `grep -c 'extra="forbid"' lib_code_parser/models/primitives/contracts.py` returns >= 1
    - Both files have module docstrings with `Traces:` tag
  </acceptance_criteria>
  <done>TypeDep + ContractInfo implemented. TypeDep retains free-form str kind per D-14; ContractInfo gains source_kind Literal with 4 values + postconditions list per AST-04 substrate.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Create primitives __init__.py + omnibus extra="forbid" Wave 0 test</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/functions.py (Task 1 output)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/callgraph.py (Task 1 output)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/type_deps.py (Task 2 output)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/contracts.py (Task 2 output)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-VALIDATION.md (Wave 0 list — tests/unit/test_models_extra_forbid.py loops over all models)
  </read_first>
  <behavior>
    Test in tests/unit/models/test_primitives_extra_forbid.py:
    - test_all_primitive_models_forbid_extra: For every imported primitive model class, assert `model.model_config.get("extra") == "forbid"`
    - test_function_node_rejects_extra: FunctionNode(node_id="x", kind="function", surprise=1) raises ValidationError
    - test_call_edge_rejects_extra: CallEdge(caller="a", callee="b", surprise=1) raises ValidationError
    - test_type_dep_rejects_extra: TypeDep(source="a", target="b", surprise=1) raises ValidationError
    - test_contract_info_rejects_extra: ContractInfo(node_id="x", surprise=1) raises ValidationError
    - test_contract_info_source_kind_literal: ContractInfo(node_id="x", source_kind="bogus") raises ValidationError
  </behavior>
  <action>
    Implement `lib_code_parser/models/primitives/__init__.py`:
    - Module docstring: "Primitive intermediate-data models — consumed by extractors, not directly verifier-facing per D-14."
    - Re-export `FunctionNode`, `ParamInfo`, `SourceRange`, `TraceTag` from `lib_code_parser.models.primitives.functions`.
    - Re-export `CallEdge`, `CallGraph` from `lib_code_parser.models.primitives.callgraph`.
    - Re-export `TypeDep` from `lib_code_parser.models.primitives.type_deps`.
    - Re-export `ContractInfo` from `lib_code_parser.models.primitives.contracts`.
    - Declare `__all__ = ["FunctionNode", "ParamInfo", "SourceRange", "TraceTag", "CallEdge", "CallGraph", "TypeDep", "ContractInfo"]`.
    - All imports MUST be absolute (`from lib_code_parser.models.primitives.functions import FunctionNode`) per CONVENTIONS.md.

    Implement `tests/unit/models/test_primitives_extra_forbid.py` per the `<behavior>` block above. Use the `pydantic.ValidationError` public import (NOT `pydantic_core._pydantic_core.ValidationError`). The first test iterates over a list of all 8 model classes and asserts `extra == "forbid"`.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/models/test_primitives_extra_forbid.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/models/test_primitives_extra_forbid.py -x -q` exits 0 with all 6 tests passing
    - `python -c "from lib_code_parser.models.primitives import FunctionNode, ParamInfo, SourceRange, TraceTag, CallEdge, CallGraph, TypeDep, ContractInfo"` exits 0 (all 8 names re-exported)
    - `grep -c '__all__' lib_code_parser/models/primitives/__init__.py` returns >= 1
    - `grep "^from \\." lib_code_parser/models/primitives/__init__.py` returns 0 (no relative imports per CONVENTIONS.md)
    - `python -c "from lib_code_parser.models.primitives import FunctionNode, CallEdge, CallGraph, TypeDep, ContractInfo, TraceTag, SourceRange, ParamInfo; classes = [FunctionNode, CallEdge, CallGraph, TypeDep, ContractInfo, TraceTag, SourceRange, ParamInfo]; assert all(c.model_config.get('extra') == 'forbid' for c in classes), [c.__name__ for c in classes if c.model_config.get('extra') != 'forbid']"` exits 0 (SCH-02 omnibus assertion across all 8 primitive models)
  </acceptance_criteria>
  <done>primitives/__init__.py re-exports 8 model names; omnibus SCH-02 test passes for all primitive models.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| extractor → primitive model | Phase 2 extractors will pass values into primitive constructors; SCH-02 catches unknown field names from buggy extractor code |
| primitive → CodeContent → caller | Caller-visible surface; extra="forbid" prevents silent schema drift across lib versions (Pitfall 6) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-04-01 | Tampering | Unknown-field schema drift (Pitfall 6 cross-lib) | mitigate | All 8 primitive models declare `extra="forbid"`; omnibus test asserts the config across the whole layer |
| T-04-02 | Tampering | Mutable default trap on list/dict fields (Pitfall 5) | mitigate | All list defaults use `Field(default_factory=list)`; grep gates assert >= 4 / >= 2 occurrences |
| T-04-03 | Spoofing | ContractInfo.source_kind accepts arbitrary string | mitigate | Literal["pydantic_validator", "pydantic_model_validator", "pydantic_field_validator", "dataclass_post_init"]; Pydantic raises ValidationError on bogus values |
| T-04-04 | Tampering | EdgeKind leaks into primitives layer (D-14 purity violation) | mitigate | Layer purity grep gate in Task 1 acceptance: `grep EdgeKind` on functions.py/callgraph.py returns 0 |
</threat_model>

<verification>
- All 8 primitive models declare extra="forbid"
- ContractInfo source_kind discriminator present with 4 Literal values
- TypeDep.kind remains free-form str (D-14 layer purity)
- No EdgeKind reference in primitives/ files
- v0.1.0 field names + defaults preserved (ready for Plan 09 to re-export from `lib_code_parser`)
</verification>

<success_criteria>
- ROADMAP §Phase 1 Success Criterion 1 partial: primitive models importable from `lib_code_parser.models.primitives` and all enforce `extra="forbid"` (the final flat `from lib_code_parser import FunctionNode` is wired in Plan 09)
- SCH-02 satisfied for primitives layer
- AST-04 schema substrate ready (ContractInfo.source_kind discriminator)
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-04-SUMMARY.md` when done, with pytest output for tests/unit/models/test_primitives_extra_forbid.py and grep verification of structural acceptance criteria.
</output>
