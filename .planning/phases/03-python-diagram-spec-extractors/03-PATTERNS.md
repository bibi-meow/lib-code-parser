# Phase 3: Python Diagram + Spec Extractors - Pattern Map

**Mapped:** 2026-06-01
**Files analyzed:** 22 (7 NEW extractors, 3 NEW shared helpers/init, 1 NEW spec model module, 2 MODIFIED source files, ~11 NEW test modules + fixtures, plus executor/CodeContent integration assessment)
**Analogs found:** 21 / 22 (1 partial — DET-04 unresolved-marker placement has no exact analog)

This file answers "what existing code should each new Phase 3 file copy patterns from?" All analogs are real, read first-hand. Every excerpt below cites a concrete file + line range so the planner can lift the pattern directly into a PLAN action.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `lib_code_parser/extractors/evaluations/class_diagram.py` (DIA-01) | evaluation extractor | transform (AST→GraphModel) | `extractors/primitives/type_deps.py` + `callgraph.py` | role-match (pull-primitive + sort) |
| `lib_code_parser/extractors/evaluations/sequence_diagram.py` (DIA-02) | evaluation extractor | transform (CallGraph→GraphModel) | `extractors/primitives/callgraph.py` | role-match |
| `lib_code_parser/extractors/evaluations/component_diagram.py` (DIA-03) | evaluation extractor | transform (TypeDep→GraphModel, edge=`imports`) | `extractors/primitives/type_deps.py` | exact (consumes import TypeDeps) |
| `lib_code_parser/extractors/evaluations/package_diagram.py` (DIA-04) | evaluation extractor | transform (path hierarchy→GraphModel, node_type=`package`) | `extractors/primitives/type_deps.py` + `_paths.get_module_name` | role-match |
| `lib_code_parser/extractors/evaluations/state_diagram.py` (DIA-05/06) | evaluation extractor | transform (FSM detect + return-subst→GraphModel+guards) | `extractors/primitives/contracts.py` (provenance) | role-match (detection-only AST) |
| `lib_code_parser/extractors/evaluations/function_spec.py` (SPC-01) | evaluation extractor | transform (FunctionNode+docstring→FunctionSpec) | `extractors/primitives/contracts.py` | role-match |
| `lib_code_parser/extractors/evaluations/class_spec.py` (SPC-02/04) | evaluation extractor | transform (FunctionNode+ContractInfo+markers→ClassSpec) | `extractors/primitives/contracts.py` | exact (class-keyed aggregate) |
| `lib_code_parser/extractors/evaluations/_docstring.py` (shared helper) | utility | transform (str→DocstringSection list) | `_paths.py` (stdlib-only helper module) | partial (new algorithm) |
| `lib_code_parser/extractors/evaluations/_fsm_detect.py` (shared helper, optional) | utility | transform (AST→state/transition tuples) | `callgraph.py:_get_call_name` + `contracts.py:_resolve_decorator_aliases` | role-match |
| `lib_code_parser/extractors/evaluations/__init__.py` | config/barrel | n/a | `extractors/primitives/__init__.py` | exact |
| `lib_code_parser/models/evaluations/spec.py` (FunctionSpec/ClassSpec/...) | model | n/a | `models/primitives/contracts.py` + `models/evaluations/graph_base.py` | exact (Pydantic conventions) |
| `lib_code_parser/models/evaluations/graph_base.py` (MODIFIED: EdgeKind += `imports`/`contains`; maybe `source_unresolved`) | model | n/a | self (append-only edit) | exact (in-place append-only) |
| `lib_code_parser/_dispatch.py` (MODIFIED: EVALUATIONS += 7) | config | n/a | self (PRIMITIVES registration block L45-60) | exact (append-only registration) |
| `lib_code_parser/executor.py` + `models/infrastructure/artifact.py` (MODIFIED: EVALUATIONS walk + CodeContent diagram/spec slots) | orchestrator + model | request-response | `executor.py` PRIMITIVES loop L82-94 + `CodeContent` L56-70 | role-match (INTEGRATION GAP — see §No Analog) |
| `tests/unit/extractors/test_class_diagram.py` (+6 more DIA/SPC unit tests) | test | n/a | `tests/unit/extractors/test_contracts_extractor.py` | exact |
| `tests/unit/extractors/test_diagram_schema.py` (DIA-07) | test | n/a | `tests/unit/models/test_graph_base.py` | exact |
| `tests/unit/models/test_spec_extra_forbid.py` | test | n/a | `tests/unit/models/test_graph_base.py` (TestExtraForbid) | exact |
| `tests/unit/test_dispatch.py` (MODIFIED: 7 EVALUATIONS entries) | test | n/a | self (TestDispatchDictsPopulated L25-49) | exact |
| `tests/acceptance/test_dia0X_*.py` / `test_spc0X_*.py` | test | n/a | `tests/acceptance/test_fr04_contracts.py` | exact |
| `tests/unit/extractors/fixtures/` (golden + dialect + FSM positive/negative) | test fixture | n/a | (none — new directory; build from RESEARCH §Required Test Fixtures) | partial |

---

## Shared Patterns

These cross-cutting patterns apply to **all 7 extractors** and must be copied into each.

### Shared 1: Pure-CAV evaluation extractor skeleton (the `def extract(cav, config)` contract)

**Source:** `lib_code_parser/extractors/primitives/type_deps.py:69-96` and `callgraph.py:55-70`
**Apply to:** all 7 `extractors/evaluations/*.py`

Every Phase 2 extractor opens identically: typed signature, pull `cav.payload`, assert it is an `ast.Module`, derive `module_name` via the shared `_paths` helper. Copy this exact opening:

```python
# Source: extractors/primitives/callgraph.py:55-70 + type_deps.py:91-96
from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]


def extract(cav: CAV, config: ParserConfig) -> GraphModel:   # or FunctionSpec / list[ClassSpec]
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"<name> extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )
    module_name = get_module_name(cav.path)
    ...
```

- `from __future__ import annotations` is the first line of every source module.
- Imports are **absolute from `lib_code_parser.`** (CLAUDE.md: no relative imports anywhere).
- `__all__ = ["extract"]` exports only the entry function; private helpers are `_snake_case` and importable from the leaf module for unit tests (not in `__all__`).
- The `assert isinstance(tree, ast.Module)` guard with the f-string message is verbatim convention (anti-Pitfall 5: never `ast.parse` inside an evaluation — use `cav.payload`).
- `config` is accepted for signature alignment even when unused (see `callgraph.py:62-64` docstring note "config is accepted ... but is not consumed").

### Shared 2: Pull primitives, never re-parse (Open-Closed invariant #5)

**Source:** `docs/09-extending.md` §不変条件#5 + the import shape in `type_deps.py:26-30`
**Apply to:** every extractor that needs functions / callgraph / type_deps / contracts

Diagram/spec extractors **call the primitive `extract()` functions** rather than re-walking the AST for facts the primitives already produce:

```python
from lib_code_parser.extractors.primitives import callgraph, type_deps, functions, contracts

def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    tree = cav.payload
    assert isinstance(tree, ast.Module), ...
    tds = type_deps.extract(cav, config)     # DIA-03 import edges
    cg  = callgraph.extract(cav, config)     # DIA-02 sequence
    fns = functions.extract(cav, config)     # DIA-01 / SPC-01-02 members
    ...
```

Per-extractor primitive map (from RESEARCH §Architectural Responsibility Map):
- DIA-01 class_diagram → `functions` (annotations/inheritance); may also re-walk `cav.payload` for `ast.AnnAssign` annotations the FunctionNode model does not carry.
- DIA-02 sequence_diagram → `callgraph`.
- DIA-03 component_diagram → `type_deps` (filter `kind=="imports"`).
- DIA-04 package_diagram → `_paths.get_module_name` + path hierarchy (no primitive needed).
- DIA-05/06 state_diagram → walks `cav.payload` directly (FSM detection + return-subst is AST-local, not a primitive fact).
- SPC-01 function_spec → `functions` + `ast.get_docstring`.
- SPC-02 class_spec → `functions` + `contracts` + SPC-04 marker walk.

> Note: re-walking `cav.payload` for **new** AST facts (class annotations, FSM call shapes) is allowed and expected — what is forbidden is `ast.parse()` (re-parsing the source string). The single parse site stays `frontends/python.py`.

### Shared 3: DET-04 sort-on-exit with stable composite keys

**Source:** `callgraph.py:94-97` and `type_deps.py:144-146,170-172`
**Apply to:** every collection in every output, before `return`

```python
# Source: callgraph.py:95
edges.sort(key=lambda e: (e.caller, e.callee))
# Source: type_deps.py:145
raw_deps.sort(key=lambda d: (d.source, d.target, d.kind, d.source_line))
```

Recommended composite keys for Phase 3 outputs (RESEARCH §Pattern 3):
- diagram `nodes` → `key=lambda n: n.node_id`
- diagram `edges` → `key=lambda e: (e.source, e.target, e.edge_type, e.label)`
- diagram `guards` → `key=lambda g: (g.from_state, g.to_state, g.condition)`
- spec `members` → by name; `preconditions`/`postconditions` → `(source_kind, line_no, text)`

For ordered dedup before sorting, copy the `callgraph.py:97` idiom `list(dict.fromkeys(nodes))` (anti-Pitfall 3: never emit set-iteration order).

### Shared 4: Import-provenance restriction for library detection (anti-false-positive)

**Source:** `lib_code_parser/extractors/primitives/contracts.py:89-140`
**Apply to:** state_diagram.py (FSM `transitions.Machine` / `python-statemachine`), class_spec.py/function_spec.py (`icontract`/`deal` markers — SPC-04)

This is the single most important reuse for DIA-05 and SPC-04. The Phase 2 `contracts.py` already solved "a user's own `Machine`/`require`/`pre` must not be misdetected as the library's." Copy the three-function shape:

```python
# Source: extractors/primitives/contracts.py:89-110 — build {local_name: canonical}
def _resolve_aliases(module: ast.Module, target_pkgs: tuple[str, ...]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod in target_pkgs or any(mod.startswith(p + ".") for p in target_pkgs):
                for a in node.names:
                    aliases[a.asname or a.name] = a.name
        elif isinstance(node, ast.Import):           # `import transitions` / `import deal`
            for a in node.names:
                if a.name in target_pkgs:
                    aliases[a.asname or a.name] = a.name
    return aliases
```

Then mirror `contracts.py:_is_attribute_form` (L77-86) for the `@pkg.attr`/`pkg.Machine` attribute form, and `_classify_decorator` (L113-140) which classifies **only** when provenance is established (in alias map OR attribute form) — bare names are rejected. The SPC-04 marker table from RESEARCH §Code Examples L575-583 plugs into this `_classify_*` shape directly.

### Shared 5: Call-name / annotation extraction helpers (don't hand-roll)

**Source:** `callgraph.py:_get_call_name` (L34-40); `ast.unparse` usage in Phase 2 type_deps annotation walk (L37-66)
**Apply to:** all diagram extractors

- Callee/attr name extraction: copy `callgraph.py:34-40` (`ast.Name→id`, `ast.Attribute→attr`).
- Annotation→string: use `ast.unparse(node.annotation)` then structurally inspect (DIA-01 composition/aggregation, RESEARCH §composition-vs-aggregation L460-476). Do NOT hand-join `ast.Attribute`/`ast.Name`.
- Docstring: `ast.get_docstring(node)` (SPC-01), never a manual first-statement walk.
- Path→module/package name: `lib_code_parser._paths.get_module_name()` — never a new `_get_module_name` per extractor (ARC-04; v0.1.0 had 4× duplication).

---

## Pattern Assignments

### `extractors/evaluations/component_diagram.py` (DIA-03, evaluation, transform)

**Analog:** `extractors/primitives/type_deps.py` (exact — it already classifies imports)

This is the **closest exact analog** in the codebase: DIA-03 consumes the `kind=="imports"` TypeDeps that `type_deps.extract` already emits (see `type_deps.py:101-122`), maps each to a `GraphEdge(edge_type="imports", source=module, target=imported)`, and emits module `GraphNode(node_type="component")`. The new `imports` EdgeKind value (D-01) is the only schema change this requires.

**Pull + map pattern (lines 99-122 of type_deps.py show the import facts to consume):**
```python
# type_deps already produces, for `import X` / `from M import N`:
#   TypeDep(source=module_name, target="X" | "M.N", kind="imports", source_line=...)
tds = type_deps.extract(cav, config)
edges = [
    GraphEdge(source=td.source, target=td.target, edge_type="imports")
    for td in tds if td.kind == "imports"
]
edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))   # DET-04
```

### `extractors/evaluations/class_diagram.py` (DIA-01, evaluation, transform)

**Analog:** `extractors/primitives/type_deps.py` (annotation-walk shape `_collect_annotation_deps` L37-66) + `contracts.py` (per-class iteration `extract` L159-200)

Copy two things: (1) the `for class_node in tree.body: if not isinstance(class_node, ast.ClassDef): continue` iteration from `contracts.py:159-161`; (2) the annotation-walk discipline from `type_deps.py:37-66`. Inheritance edges come from `ast.ClassDef.bases`. Composition/aggregation/association decision rule is RESEARCH §composition-vs-aggregation L460-476 (`Optional[X]`/`list[X]` → `aggregates`; direct class type → `composes`; undecidable → `associates` fallback). Edge values `inherits`/`composes`/`aggregates`/`associates` all already exist in EdgeKind (`graph_base.py:33-45`) — no schema change for DIA-01.

### `extractors/evaluations/sequence_diagram.py` (DIA-02, evaluation, transform)

**Analog:** `extractors/primitives/callgraph.py` (exact source of edges)

Pull `callgraph.extract(cav, config)` → `CallGraph(nodes, edges)`, map each `CallEdge(caller, callee)` to `GraphEdge(edge_type="calls", source=caller, target=callee)`. The `calls` value already exists in EdgeKind. SP-2 spike (branch fidelity alt/loop/par) runs as the first deliverable inside this plan (D-08); if it ships, branch frames map from `ast.If`/`ast.For`/`ast.While` over `cav.payload`. Record verdict in `.planning/spikes/SP-2-sequence-branch-fidelity.md`.

### `extractors/evaluations/package_diagram.py` (DIA-04, evaluation, transform)

**Analog:** `type_deps.py` (skeleton) + `_paths.get_module_name` (path derivation)

Emit `GraphNode(node_type="package", ...)` (D-04/D-05/D-06 — plain `str`, no schema change to GraphNode). **Discretion decision (D-01 sub-decision, RESEARCH Open Question #2):** prefer expressing containment via `GraphNode.attributes={"parent_package": "..."}` (GraphNode already has `attributes: dict[str,str]` — `graph_base.py:61`); add `contains` to EdgeKind **only** if a containment *edge* is genuinely needed for verifier comparison. Decide at DIA-04 design.

### `extractors/evaluations/state_diagram.py` (DIA-05/06, evaluation, transform)

**Analog:** `contracts.py` provenance pattern (L89-140) for library detection; `callgraph.py:_get_call_name` for call shapes

Three FSM families (RESEARCH §FSM Detection L286-363) detected via the Shared-4 provenance map. Emit `GraphNode(node_type="state")` + `GraphEdge(edge_type="transitions_to")` + `GuardExpr` for guards. DIA-06 return-value substitution (RESEARCH §Return-Value Substitution L365-381) is a recursive intra-class AST walk with a `visited: set` (cycle-safe). Negative case (`class Color(Enum): RED/GREEN/BLUE` → 0 states) is fixture-asserted (ROADMAP SC3). `transitions_to` already exists in EdgeKind. SP-1 spike runs as first deliverable; record verdict in `.planning/spikes/SP-1-general-control-flow-state.md`.

**⚠ Schema reconciliation (see §No Analog, Pitfall 1):** the DIA-06 `unresolved=true` marker has NO clean analog — `GraphEdge` has no `attributes` field and is `extra="forbid"` (`graph_base.py:77-83`). Planner MUST pick at design time: (a) add `source_unresolved: bool = False` to `GraphEdge` (SCH-02 `source_` prefix, recommended by RESEARCH A4), (b) `label="unresolved"`, or (c) mark the state `GraphNode.attributes`.

### `extractors/evaluations/function_spec.py` (SPC-01, evaluation, transform)

**Analog:** `contracts.py` (per-member iteration) + new `_docstring.py` helper

Pull `functions.extract` for signatures, `ast.get_docstring` for the raw docstring, delegate dialect parsing to `_docstring.py`. Pre/post derivation is a fixed keyword/regex heuristic (RESEARCH §Docstring pre/post L405-411) — mark `source_kind="docstring"`. No external dep (D-09).

### `extractors/evaluations/class_spec.py` (SPC-02/04, evaluation, transform)

**Analog:** `extractors/primitives/contracts.py` (exact — class-keyed aggregate, L143-202)

This is the closest analog for the class-iteration + member-aggregation shape. SPC-04 markers (`icontract`/`deal`/PEP-316) use Shared-4 provenance + the marker table (RESEARCH L575-583). **Anti-Pitfall 6 (A6):** do NOT edit the frozen `primitives/contracts.py` `SourceKind` Literal; SPC-04 markers live in the new `models/evaluations/spec.py` with their own `source_kind` set.

### `extractors/evaluations/_docstring.py` (shared helper, utility)

**Analog:** `lib_code_parser/_paths.py` (partial — a stdlib-only private helper module; no domain analog for the parser itself)

New algorithm (state machine over `docstring.splitlines()`, RESEARCH §Docstring Dialect Parsing L383-411). No exact analog exists — it is genuinely new. Follow the module conventions (module docstring, `from __future__ import annotations`, `_snake_case` helpers, typed signatures). Dialect detection order Sphinx→NumPy→Google is byte-stable (first match wins).

### `models/evaluations/spec.py` (FunctionSpec / ClassSpec / DocstringSection / SpecCondition)

**Analog:** `models/primitives/contracts.py` (exact — Literal `SourceKind`, `ContractEntry`/`ContractInfo` nesting) + `models/evaluations/graph_base.py` (model conventions)

Copy the Pydantic conventions verbatim:
```python
# Source: models/primitives/contracts.py:22-55 + graph_base.py:56
from pydantic import BaseModel, ConfigDict, Field

class FunctionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")   # SCH-03 — MANDATORY (graph_base.py:56,77,89,105)
    node_id: str
    docstring_sections: list["DocstringSection"] = Field(default_factory=list)
    preconditions: list["SpecCondition"] = Field(default_factory=list)
    postconditions: list["SpecCondition"] = Field(default_factory=list)
    # physical-only metadata → physical_*/source_* prefix optional fields (SCH-02)
```
- `model_config = ConfigDict(extra="forbid")` on **every** model (not negotiable — SCH-03).
- Closed `Literal` for discriminator fields, mirroring `contracts.py:26-34` `SourceKind`/`ContractKind`. SPC-04 adds values like `icontract_require`/`deal_pre`/`pep316_pre` here.
- `Field(default_factory=list)` for collections; defaults so "empty" returns are inert (graph_base.py:107-109 pattern).
- physical-only metadata uses `physical_*`/`source_*` prefix optional fields (graph_base.py:83 `physical_module: str | None = None` is the canonical example).
- `model_rebuild()` at module bottom if forward refs are used (functions.py:58, contracts.py is self-contained).

### `models/evaluations/graph_base.py` (MODIFIED — append-only)

**Analog:** self (in-place append-only edit)

D-01: append `"imports"` (and conditionally `"contains"`) to the `EdgeKind` Literal at L33-45, and add a docstring line in the L17-32 semantic table for each new value (mirroring the existing `inherits — type subtype` comment style). Existing 11 values are **immutable** (anti-Pitfall 2: never add `uses`/`other`/`misc`/`dep`/`depends`). Update `models/evaluations/__init__.py` `__all__` only if new symbols are exported (EdgeKind value additions need no `__all__` change). **The existing `tests/unit/models/test_graph_base.py:40-49` asserts exactly 11 values — that test MUST be updated to the new count in the same commit.**

### `_dispatch.py` (MODIFIED — append-only EVALUATIONS registration)

**Analog:** self — the PRIMITIVES registration block at `_dispatch.py:45-60` (exact)

Copy the exact registration shape into the bottom block:
```python
# Source: _dispatch.py:50-60 (PRIMITIVES registration) — mirror for EVALUATIONS
from lib_code_parser.extractors.evaluations.class_diagram import extract as _extract_class_diagram
# ... 6 more imports ...
EVALUATIONS["class_diagram"] = _extract_class_diagram
EVALUATIONS["sequence_diagram"] = _extract_sequence_diagram
EVALUATIONS["component_diagram"] = _extract_component_diagram
EVALUATIONS["package_diagram"] = _extract_package_diagram
EVALUATIONS["state_diagram"] = _extract_state_diagram
EVALUATIONS["function_spec"] = _extract_function_spec
EVALUATIONS["class_spec"] = _extract_class_spec
```
Imports go at module **bottom** after the dict declarations (the `# ruff: noqa: E402` at L14-16 already covers this; the existing block proves the convention). Append-only — never reorder/remove existing entries (invariant #4). `tests/unit/test_dispatch.py:46-49` currently asserts `len(EVALUATIONS) == 0` — that test MUST be updated to assert the 7 keys in registration order (mirror `test_primitives_dict_has_4_entries_in_append_only_order` at L36-44).

---

## Test Pattern Assignments

### Unit extractor tests → `tests/unit/extractors/test_<diagram|spec>.py`

**Analog:** `tests/unit/extractors/test_contracts_extractor.py` (exact)

Copy the test harness verbatim:
```python
# Source: tests/unit/extractors/test_contracts_extractor.py:19-24
_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")

def _build_cav(source: str, path: str) -> CAV:
    """Build a Python CAV from source (test-side parse only)."""
    return CAV(language="python", path=path, payload=ast.parse(source))
```
- The test builds the CAV via `ast.parse` (test-side only); the extractor must NOT parse (L22-24 note).
- One test function per behavior, descriptive docstring citing the requirement ID (e.g. `"""DIA-05 negative: class Color(Enum) → 0 states."""`).
- False-positive defense tests are mandatory for state_diagram + aux markers — copy `test_non_pydantic_import_not_classified` (L180-198) and `test_no_import_bare_decorator_not_classified` (L201-210) shapes for the decoy `def require(...)` / non-importing `Machine` cases.
- `test_isolated_import_no_executor` (L213-222) shape proves the extractor doesn't transitively import the executor — replicate for each new extractor.

### Schema-validation test (DIA-07) → `tests/unit/extractors/test_diagram_schema.py` and `tests/unit/models/test_spec_extra_forbid.py`

**Analog:** `tests/unit/models/test_graph_base.py` (exact)

Copy `TestExtraForbid` (L100-110) and the `get_args(EdgeKind)` value-set assertions (L39-68). For DIA-07, assert every diagram extractor's output validates as `GraphModel` and that no field outside `physical_*`/`source_*` carries physical metadata. **Update the `test_edge_kind_has_eleven_values` (L40-42) + `CANONICAL_EDGE_KINDS` set (L24-36) to the new EdgeKind count/values when D-01 lands.**

### Acceptance tests → `tests/acceptance/test_dia0X_*.py` / `test_spc0X_*.py`

**Analog:** `tests/acceptance/test_fr04_contracts.py` (exact)

Copy the public-surface harness:
```python
# Source: tests/acceptance/test_fr04_contracts.py:19-24
from lib_code_parser import CodeParserExecutor, ParserConfig

def _run(source: str, path: str):
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content   # then read .class_diagram / .function_spec / etc.
```
Acceptance tests exercise the full `execute()` path (depends on the executor/CodeContent integration below). Mirror the `test_frNN_*` naming → `test_dia01_class_diagram.py`, `test_spc01_function_spec.py`.

### Fixtures → `tests/unit/extractors/fixtures/`

**Analog:** none (new directory). Build from RESEARCH §Required Test Fixtures L676-682. Existing `tests/parity/fixtures/v01_snapshot.json` shows the golden-JSON precedent. The strongest determinism proof (SPC-01) is the *same* function documented Google/NumPy/Sphinx → assert byte-identical normalized output.

---

## No Analog Found / Integration Gaps

| File / Concern | Role | Reason | Planner Guidance |
|----------------|------|--------|------------------|
| `executor.py` EVALUATIONS walk | orchestrator | **INTEGRATION GAP** — `executor.py:82-94` walks `PRIMITIVES` only, with **hardcoded 4 slots** (functions/call_graph/type_deps/contracts). It does NOT walk `EVALUATIONS`. docs/09 §不変条件#6 (L132-141) shows the *intended* `for name, fn in EVALUATIONS.items(): setattr(content, name, fn(cav, config))` shape, but the real executor never implemented it. The planner must add an EVALUATIONS walk **without** breaking the existing PRIMITIVES path. The docs/09 pseudo-code is the design target; the existing PRIMITIVES loop (L82-94) is the structural analog to copy. | Add an `EVALUATIONS` for-loop after the PRIMITIVES loop, gated by a config flag per evaluation (config flag scheme is Claude's discretion — see `config.is_enabled(name)` in docs/09 L138). Keep executor body change minimal; invariant #6 wants it dict-driven. |
| `CodeContent` diagram/spec slots | model | `models/infrastructure/artifact.py:56-70` `CodeContent` has only 4 primitive fields. Phase 3 outputs (5 GraphModels + 2 spec models) need **new optional fields** per invariant #3 (additive, optional, defaulted). | Add `class_diagram: GraphModel = Field(default_factory=GraphModel)` etc. as optional fields with defaults (anti-break v0.1.0 compat). Follow the `contracts: dict[...] = Field(default_factory=dict)` additive pattern (L70) and the forward-ref + `model_rebuild()` discipline (L91-111). This is an invariant-#3 additive edit, not a breaking change. |
| DIA-06 `unresolved` marker | model/extractor | `GraphEdge` (`graph_base.py:64-83`) has no `attributes` field and `extra="forbid"` — the DIA-06 contract wording "`unresolved=true` attribute" has no place to land. Partial analog: `GraphNode.attributes` (L61) and `physical_module` optional field (L83). | Pick one (RESEARCH A4 recommends `source_unresolved: bool = False` on GraphEdge — SCH-02 `source_` prefix, append-only optional field). Reconcile at DIA-06 design. |
| `_docstring.py` parser algorithm | utility | The Google/NumPy/Sphinx state-machine parser is genuinely new — no codebase analog for the parsing logic (only `_paths.py` as a stdlib-helper-module *shape* analog). | Implement per RESEARCH §Docstring Dialect Parsing L383-411 (fixed keyword/regex, no NLP, byte-stable dialect order). |

---

## Metadata

**Analog search scope:** `lib_code_parser/extractors/primitives/*.py`, `lib_code_parser/models/{primitives,evaluations,infrastructure}/*.py`, `lib_code_parser/_dispatch.py`, `lib_code_parser/executor.py`, `lib_code_parser/_paths.py`, `docs/09-extending.md`, `tests/{unit,acceptance,parity}/`.
**Files scanned:** 14 source/doc files read first-hand + full source/test tree enumerated.
**Pattern extraction date:** 2026-06-01

**Key insight (confirms RESEARCH):** Phase 3 is overwhelmingly **composition of Phase 2 primitives + small pure transforms**. The genuinely new algorithmic content with no analog is: (a) `_docstring.py` dialect state-machine, (b) FSM AST matchers (though library *detection* reuses `contracts.py` provenance verbatim), (c) DIA-06 return-value substitution, (d) the executor/CodeContent EVALUATIONS integration (a real gap, not just new code). Everything else has an exact or strong analog in `extractors/primitives/` and `models/`.
