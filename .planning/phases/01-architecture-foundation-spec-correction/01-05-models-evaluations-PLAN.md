---
phase: 01-architecture-foundation-spec-correction
plan: 05
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/models/evaluations/__init__.py
  - lib_code_parser/models/evaluations/graph_base.py
  - tests/unit/models/test_graph_base.py
autonomous: true
requirements: [SCH-01, SCH-03, SCH-02]
must_haves:
  truths:
    - "EdgeKind is a closed Literal of exactly 11 values; 'uses' / 'other' / 'misc' raise ValidationError"
    - "GraphNode, GraphEdge, GraphModel, GuardExpr defined in lib-code-parser's evaluations layer with extra='forbid'"
    - "Schema is structurally compatible with lib-diagram-parser (same field names + types) per pre-resolved decision #5"
    - "GraphEdge supports optional physical_module field for SCH-02 physical-side metadata convention"
  artifacts:
    - path: "lib_code_parser/models/evaluations/graph_base.py"
      provides: "EdgeKind Literal + GraphNode/GraphEdge/GraphModel/GuardExpr (lib-diagram-parser compatible schema, locally defined per pre-resolved decision #5)"
      contains: "EdgeKind = Literal|class GraphNode|class GraphEdge"
    - path: "tests/unit/models/test_graph_base.py"
      provides: "Closed Literal assertion + extra=forbid + 11-value coverage tests"
      contains: "test_edge_kind|test_graph_node"
  key_links:
    - from: "EdgeKind Literal"
      to: "11 enumerated values"
      via: "Pydantic v2 Literal type"
      pattern: "Literal\\["
    - from: "GraphEdge"
      to: "physical_module field"
      via: "SCH-02 physical_* prefix convention"
      pattern: "physical_module"
---

<objective>
Create the `models/evaluations/` subpackage that holds verifier-facing diagram and spec output models per D-10 / D-14. Phase 1 ships only `graph_base.py` with `EdgeKind` (closed Literal, 11 values, no "uses"/"other"/"misc" — SCH-03 per Pitfall 7) and the four schema models `GraphNode`, `GraphEdge`, `GraphModel`, `GuardExpr` compatible with `lib-diagram-parser`. Per pre-resolved Open Question #5, Phase 1 does NOT import `lib_diagram_parser` at runtime — the models are self-contained and structurally compatible (field-name + type-shape parity); Phase 3 will decide whether to switch to direct import or subclass once the sibling-lib `node_type="package"` situation is re-evaluated.

Purpose: Locks the verifier-facing schema and the closed EdgeKind taxonomy before any diagram extractor is written. This is the entire purpose of D-14 — to make the verifier-facing layer impossible to drift via Pydantic-enforced contracts.

Output:
- `lib_code_parser/models/evaluations/__init__.py` — re-exports EdgeKind + 4 graph models
- `lib_code_parser/models/evaluations/graph_base.py` — EdgeKind Literal + GraphNode/GraphEdge/GraphModel/GuardExpr
- Wave 0 test asserting 11-value EdgeKind coverage + reject of "uses" + extra="forbid" on all 4 models + physical_module field present
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/research/PITFALLS.md

<interfaces>
<!-- lib-diagram-parser v0.1.0 schema (from RESEARCH.md §lib-diagram-parser Schema Snapshot, live-read from c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser/lib_diagram_parser/models.py): -->

class GraphNode(BaseModel):
    node_id: str
    node_type: str  # "class"|"component"|"state"|"interface"|"participant"|"node"|"pseudostate"
    label: str
    attributes: dict = {}

class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str  # informal value list
    label: str = ""

class GuardExpr(BaseModel):
    from_state: str
    to_state: str
    condition: str
    action: str = ""

class GraphModel(BaseModel):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    guards: list[GuardExpr] = []

Phase 1 (per pre-resolved Open Question #5) defines structurally-compatible copies of these models inside lib-code-parser, with the addition of EdgeKind Literal on GraphEdge.edge_type (strict) and `physical_module` optional field on GraphEdge (SCH-02 physical-side extension). Phase 3 will re-evaluate whether to switch to direct lib_diagram_parser import + subclass.
</interfaces>

<edge_kind_reference>
<!-- The exact 11 values from RESEARCH.md §EdgeKind Closed Literal — Coverage Table. Inclusion is closed; "uses"/"other"/"misc" are forbidden per Pitfall 7. -->

EdgeKind = Literal[
    "inherits",          # type subtype (Python class A(B), C++ class A : public B)
    "implements",        # interface conformance (Python ABCMeta, C++ pure virtual)
    "composes",          # ownership with shared lifetime (concrete field)
    "aggregates",        # has-a without lifetime (Optional / list / reference)
    "associates",        # undecidable fallback (NEVER a catch-all for unknown — explicit semantic)
    "field_of",          # A is the declared type of a field on B
    "param_of",          # A is the declared type of a parameter on a method of B
    "returns",           # A is the declared return type of a method on B
    "instantiates",      # A constructs B (new B() / B())
    "calls",             # A method calls B method (sequence + callgraph)
    "transitions_to",    # FSM: state A → state B
]
</edge_kind_reference>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement evaluations/graph_base.py (EdgeKind + 4 graph models)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§EdgeKind Closed Literal — coverage table per diagram + ValidationError live-pattern showing all 11 values listed in the error message; §lib-diagram-parser Schema Snapshot — exact field names/types to mirror)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/research/PITFALLS.md §Pitfall 7 (EdgeKind ad-hoc growth — explicit ban on "uses"/"other"/"misc"; resolution: 11-value closed Literal)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md (D-14 — evaluations layer is the ONLY verifier-facing layer; D-15 — Phase 1 does NOT submit sibling-lib PR; D-16 — SCH-01 interpretation broadened to "direct utilization including subclass")
  </read_first>
  <behavior>
    Implicit — verified by Plan 05 Task 2 tests:
    - `EdgeKind` exposes exactly 11 string values: inherits / implements / composes / aggregates / associates / field_of / param_of / returns / instantiates / calls / transitions_to
    - "uses", "other", "misc", "depends" are NOT in EdgeKind
    - GraphNode(node_id="A", node_type="class", label="A") succeeds; same with `attributes={}` default
    - GraphEdge(source="A", target="B", edge_type="inherits") succeeds; edge_type="uses" raises ValidationError
    - GraphEdge.physical_module defaults to None; GraphEdge(source="A", target="B", edge_type="calls", physical_module="order_service.OrderService") succeeds
    - GraphModel() defaults: nodes == [], edges == [], guards == []
    - GuardExpr(from_state="X", to_state="Y", condition="x>0") succeeds with default action == ""
    - All 4 models raise ValidationError on unknown extra fields (SCH-02)
  </behavior>
  <action>
    Implement `lib_code_parser/models/evaluations/graph_base.py`:
    - Module docstring: "Verifier-facing evaluation graph models. EdgeKind closed Literal per SCH-03 / Pitfall 7. Schema structurally compatible with lib-diagram-parser>=0.1.0; Phase 1 keeps models self-contained per pre-resolved Open Question #5 (Phase 3 will re-evaluate direct-import vs subclass switch per D-15/D-17). Traces: SCH-01, SCH-02, SCH-03."
    - Imports: `from __future__ import annotations`, `from typing import Literal`, `from pydantic import BaseModel, ConfigDict, Field`. DO NOT import from `lib_diagram_parser` (pre-resolved decision #5: Phase 1 self-contained).
    - Define `EdgeKind` as a module-level Literal with EXACTLY these 11 string values in this order: `"inherits"`, `"implements"`, `"composes"`, `"aggregates"`, `"associates"`, `"field_of"`, `"param_of"`, `"returns"`, `"instantiates"`, `"calls"`, `"transitions_to"`. Use one Literal alias: `EdgeKind = Literal["inherits", "implements", "composes", "aggregates", "associates", "field_of", "param_of", "returns", "instantiates", "calls", "transitions_to"]`. Place a docstring-style comment above explaining each value briefly (verbatim from RESEARCH.md §EdgeKind Closed Literal coverage table — one short comment per line) so that downstream developers see the intended semantic without consulting external docs. DO NOT add "uses" / "other" / "misc" / "depends" / "other_kind" or any other catch-all.
    - Class `GraphNode(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields exactly: `node_id: str`, `node_type: str` (kept as plain str per lib-diagram-parser parity AND because DIA-04 will add `"package"` in Phase 3 — keeping str leaves that path open without local Literal drift), `label: str`, `attributes: dict[str, str] = Field(default_factory=dict)`.
    - Class `GraphEdge(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields exactly: `source: str`, `target: str`, `edge_type: EdgeKind` (strict closed Literal — this is the SCH-03 enforcement point), `label: str = ""`, `physical_module: str | None = None` (SCH-02 physical-side extension; optional `None` default — verifier ignores `physical_*` fields when comparing).
    - Class `GuardExpr(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields exactly: `from_state: str`, `to_state: str`, `condition: str`, `action: str = ""`.
    - Class `GraphModel(BaseModel)`: `model_config = ConfigDict(extra="forbid")`. Fields exactly: `nodes: list[GraphNode] = Field(default_factory=list)`, `edges: list[GraphEdge] = Field(default_factory=list)`, `guards: list[GuardExpr] = Field(default_factory=list)`.

    Notes on what NOT to do:
    - Do NOT add a `source_range: SourceRange | None = None` to GraphEdge in Phase 1 (forward-ref to primitives would create a cross-layer dependency; SCH-02 only mandates the `physical_module` and `source_*` prefix CONVENTION, not the actual SourceRange field — Phase 3 extractors can add it when they need it via `extra="forbid"`-friendly model extension).
    - Do NOT use `enum.Enum` for EdgeKind. Pydantic v2 `Literal[...]` produces clearer ValidationError messages (see RESEARCH §EdgeKind ValidationError example which lists all 11 values).
    - Do NOT include node_type Literal — keep it `str` to leave the `"package"` extension path open for Phase 3 (D-15 / D-17).
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; python -c "from lib_code_parser.models.evaluations.graph_base import EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr; gn=GraphNode(node_id='A', node_type='class', label='A'); ge=GraphEdge(source='A', target='B', edge_type='inherits'); gm=GraphModel(); guard=GuardExpr(from_state='X', to_state='Y', condition='x>0'); print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `python -c "from lib_code_parser.models.evaluations.graph_base import EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr"` exits 0
    - `python -c "from lib_code_parser.models.evaluations.graph_base import EdgeKind; from typing import get_args; vals = get_args(EdgeKind); assert len(vals) == 11, f'expected 11 values, got {len(vals)}: {vals}'; assert set(vals) == {'inherits','implements','composes','aggregates','associates','field_of','param_of','returns','instantiates','calls','transitions_to'}, f'wrong set: {vals}'"` exits 0
    - `python -c "from typing import get_args; from lib_code_parser.models.evaluations.graph_base import EdgeKind; assert 'uses' not in get_args(EdgeKind); assert 'other' not in get_args(EdgeKind); assert 'misc' not in get_args(EdgeKind)"` exits 0 (Pitfall 7 hard gate)
    - `python -c "from lib_code_parser.models.evaluations.graph_base import GraphEdge; from pydantic import ValidationError; import sys; \nfrom contextlib import suppress; \nraised = False\ntry: GraphEdge(source='A', target='B', edge_type='uses')\nexcept ValidationError: raised = True\nassert raised, 'GraphEdge should reject edge_type uses'"` exits 0 (live ValidationError check on uses)
    - `grep -c '^EdgeKind = Literal\[' lib_code_parser/models/evaluations/graph_base.py` returns exactly 1
    - `grep -c 'class GraphNode(BaseModel)' lib_code_parser/models/evaluations/graph_base.py` returns exactly 1
    - `grep -c 'class GraphEdge(BaseModel)' lib_code_parser/models/evaluations/graph_base.py` returns exactly 1
    - `grep -c 'class GraphModel(BaseModel)' lib_code_parser/models/evaluations/graph_base.py` returns exactly 1
    - `grep -c 'class GuardExpr(BaseModel)' lib_code_parser/models/evaluations/graph_base.py` returns exactly 1
    - `grep -c 'extra="forbid"' lib_code_parser/models/evaluations/graph_base.py` returns >= 4
    - `grep -c 'edge_type: EdgeKind' lib_code_parser/models/evaluations/graph_base.py` returns exactly 1 (strict Literal applied to GraphEdge.edge_type)
    - `grep -c 'physical_module:' lib_code_parser/models/evaluations/graph_base.py` returns exactly 1 (SCH-02 substrate)
    - `grep -c 'from lib_diagram_parser' lib_code_parser/models/evaluations/graph_base.py` returns 0 (Phase 1 self-contained per pre-resolved decision #5)
    - `grep -v '^[[:space:]]*#' lib_code_parser/models/evaluations/graph_base.py | grep -c '"uses"\|"other"\|"misc"'` returns 0 (no forbidden values in source code outside comments)
    - File has module docstring with `Traces:` tag
  </acceptance_criteria>
  <done>EdgeKind closed Literal (11 values) + GraphNode/GraphEdge/GraphModel/GuardExpr implemented, "uses"/"other"/"misc" banned, physical_module field present on GraphEdge for SCH-02 substrate, all 4 models extra="forbid".</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Create evaluations/__init__.py + Wave 0 test_graph_base.py</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/evaluations/graph_base.py (Task 1 output — exact symbols to re-export)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-VALIDATION.md (Wave 0: tests/unit/test_graph_base.py — to live under tests/unit/models/test_graph_base.py per package structure)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md (absolute imports + test class naming Test<Subject>)
  </read_first>
  <behavior>
    Test suite in tests/unit/models/test_graph_base.py:
    - test_edge_kind_has_eleven_values: `get_args(EdgeKind)` length is exactly 11
    - test_edge_kind_value_set: the 11-value set matches the canonical set exactly (assert via `set(get_args(EdgeKind)) == {...11 strings...}`)
    - test_edge_kind_rejects_uses: GraphEdge(source="A", target="B", edge_type="uses") raises ValidationError (Pitfall 7)
    - test_edge_kind_rejects_other: edge_type="other" raises ValidationError
    - test_edge_kind_rejects_misc: edge_type="misc" raises ValidationError
    - test_edge_kind_accepts_all_eleven: a loop over the 11 canonical values constructs GraphEdge each time without raising
    - test_graph_node_constructible: GraphNode(node_id="A", node_type="class", label="A") works
    - test_graph_node_node_type_str_allows_package: GraphNode(node_id="P", node_type="package", label="P") succeeds (node_type is plain str; the DIA-04 `"package"` extension path stays open per D-15)
    - test_graph_edge_physical_module_default_none: GraphEdge(source="A", target="B", edge_type="calls").physical_module is None
    - test_graph_edge_physical_module_settable: GraphEdge(source="A", target="B", edge_type="calls", physical_module="order_service.OrderService").physical_module == "order_service.OrderService"
    - test_all_evaluation_models_forbid_extra: GraphNode, GraphEdge, GraphModel, GuardExpr all reject `extra=...` kwarg with ValidationError
    - test_graph_model_default_empty: GraphModel() yields nodes==[], edges==[], guards==[]
    - test_guard_expr_default_action_empty: GuardExpr(from_state="X", to_state="Y", condition="c").action == ""
  </behavior>
  <action>
    Implement `lib_code_parser/models/evaluations/__init__.py`:
    - Module docstring: "Verifier-facing evaluation models (D-14). EdgeKind + 4 graph models in graph_base.py; Phase 3 adds 5 diagrams + 2 specs."
    - Re-export `EdgeKind`, `GraphNode`, `GraphEdge`, `GraphModel`, `GuardExpr` from `lib_code_parser.models.evaluations.graph_base`.
    - `__all__ = ["EdgeKind", "GraphNode", "GraphEdge", "GraphModel", "GuardExpr"]`.
    - Absolute imports only.

    Implement `tests/unit/models/test_graph_base.py` per the `<behavior>` block above. Use `from pydantic import ValidationError` and `from typing import get_args` for the Literal introspection. The 11-value canonical set test should fail-loudly with a clear assertion message listing extra/missing values. Use the existing conftest.py without modification.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/models/test_graph_base.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/models/test_graph_base.py -x -q` exits 0 with all 12 tests passing
    - `python -c "from lib_code_parser.models.evaluations import EdgeKind, GraphNode, GraphEdge, GraphModel, GuardExpr"` exits 0
    - `grep -c '__all__' lib_code_parser/models/evaluations/__init__.py` returns >= 1
    - `grep "^from \\." lib_code_parser/models/evaluations/__init__.py` returns 0 (no relative imports)
    - Test file has at least one test that iterates all 11 EdgeKind values (`grep -c 'for kind in' tests/unit/models/test_graph_base.py` returns >= 1)
  </acceptance_criteria>
  <done>evaluations/__init__.py re-exports 5 symbols; 12-test Wave 0 suite passes with closed-Literal enforcement + SCH-02 + physical_module substrate.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Phase 3 diagram extractor → GraphEdge construction | Diagram code attempts to instantiate GraphEdge; EdgeKind closed Literal rejects ad-hoc edge types at construction time |
| lib-code-parser → lib-diagram-parser schema-compat | Verifier consumes GraphModel; structural compatibility ensures cross-lib bisimulation (Pitfall 6) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-05-01 | Tampering | EdgeKind ad-hoc growth via "uses"/"other"/"misc" catch-all (Pitfall 7) | mitigate | Closed Literal with exactly 11 enumerated values; live ValidationError on "uses"; grep gate + get_args length assertion in Task 1 & 2 acceptance |
| T-05-02 | Tampering | Unknown-field schema drift on GraphNode/GraphEdge/GraphModel/GuardExpr (Pitfall 6) | mitigate | All 4 models declare extra="forbid"; omnibus test asserts |
| T-05-03 | Spoofing | Schema drift between lib-code-parser and lib-diagram-parser (cross-lib Pitfall 6) | mitigate | Field names + types mirror lib-diagram-parser v0.1.0 exactly (RESEARCH live-read); Phase 5 SCH-04 cross-lib test will exercise structural equivalence; Phase 1 keeps physical_module as `physical_*` prefix per SCH-02 to mark physical-side-only data invisibly to verifier diffs |
| T-05-04 | Tampering | DIA-04 `"package"` extension blocked by Literal | accept | node_type kept as plain `str` deliberately to leave Phase 3 path open per D-15 / D-17; rationale documented in code comment |
</threat_model>

<verification>
- EdgeKind get_args length is exactly 11
- "uses", "other", "misc" all raise ValidationError
- All 4 graph models declare extra="forbid"
- GraphEdge.physical_module field present (SCH-02 substrate)
- graph_base.py does NOT import from lib_diagram_parser (Phase 1 self-contained per pre-resolved decision)
- Tests/unit/models/test_graph_base.py 12-test suite all passes
</verification>

<success_criteria>
- ROADMAP §Phase 1 Success Criterion 1: caller can import EdgeKind + GraphNode + GraphEdge + GraphModel from `lib_code_parser.models.evaluations` (Plan 09 wires `from lib_code_parser.models import ...` flat alias)
- SCH-01 satisfied via structural compatibility with lib-diagram-parser v0.1.0 (D-16 interpretation; sibling-lib PR deferred per D-15)
- SCH-02 satisfied for evaluations layer (extra="forbid" on all 4 models + physical_module field for physical-side prefix substrate)
- SCH-03 satisfied (closed 11-value Literal, "uses" rejected at construction time)
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-05-SUMMARY.md` when done, with pytest output for tests/unit/models/test_graph_base.py and grep verification of EdgeKind closure + no forbidden tokens.
</output>
