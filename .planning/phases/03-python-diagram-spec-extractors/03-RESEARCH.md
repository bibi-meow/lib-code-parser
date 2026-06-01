# Phase 3: Python Diagram + Spec Extractors - Research

**Researched:** 2026-06-01
**Domain:** Deterministic AST-based architecture extraction (5 diagrams + 2 specs) over a single CAV, stdlib `ast` only, Pydantic v2 verifier-facing schema
**Confidence:** HIGH (internal contracts read first-hand; external detection-target APIs cross-verified against official docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

All GA-1..GA-4 and D-01..D-10 are **user-approved (2026-06-01 "OK") and LOCKED**. The planner MUST honor these verbatim — they are constraints to implement, not choices to re-litigate.

### Locked Decisions

- **D-01 (EdgeKind append-only extension):** `models/evaluations/graph_base.py`'s closed `EdgeKind` (11 values) has no value for import dependency. DIA-03 component diagram requires import-derived edges; natural value `dependency`/`depends` is **forbidden by Phase 1 Pitfall 7** (catch-all ban). → **Add explicit semantic value `imports`** (module A imports module B — explicit semantic, not catch-all, same philosophy as `associates` = "undecidable but explicit"). **`contains` may also be added** for package containment IF the planner judges (at DIA-04 design time) that node nesting/attributes cannot express containment. This is an **append-only update** to the Phase 1 locked closed Literal; existing 11 values are immutable.
- **D-02 (self-contained schema maintained):** Keep `graph_base.py` self-contained. Do NOT adopt SCH-01's literal "directly import `lib-diagram-parser` models." The sibling lib's models lack `extra="forbid"`, `physical_*` fields, and closed Literals; direct import would lose the strict Phase 1 schema. Cross-lib structural compatibility is verified by SCH-04 (Phase 5).
- **D-03 (vocabulary gap = verifier responsibility):** Sibling lib `edge_type` vocabulary (`dependency/inheritance/implementation/aggregation/composition/transition/call/association`, plain str) differs in spelling from this lib's `EdgeKind` (`inherits/composes/calls/transitions_to/...`). This lib keeps its **strict, self-contained vocabulary**; the `inherits` vs `inheritance` gap is interpreted by the verifier (LLM agent). Do NOT rename to sibling-lib spelling.
- **D-04 (DIA-07 schema basis = graph_base.py):** All 5 diagram outputs validate against `GraphNode`/`GraphEdge`/`GraphModel`/`GuardExpr`. Physical-only metadata uses `physical_*`/`source_*` prefixed optional fields (SCH-02). `GraphNode.node_type` stays plain `str` (emit `"class"`/`"component"`/`"package"`/`"state"` as values; do NOT Literal-ize — Phase 1 D-15).
- **D-05 (node_type is plain str → package needs no sibling code change):** Sibling lib's `node_type` is plain `str` (not enum/Literal), so `node_type="package"` requires **no sibling-lib code change**. The ROADMAP/REQUIREMENTS framing of "enum value addition PR" is diverged from reality; actual work is **docstring/comment vocabulary alignment only**.
- **D-06 (package diagram self-completes in this lib):** Phase 3 emits `node_type="package"` in this lib and completes package diagram. A **lightweight optional doc PR** to the sibling lib (adding `"package"` to the `node_type` comment) is the only sibling-lib work — **NON-blocking**. Do NOT block DIA-04 on PR merge. Cross-lib structural verification is SCH-04 (Phase 5).
- **D-07 (must-have = v0.2.0 confirmed):** DIA-02 linear sequence (call-graph-derived) + DIA-05 FSM explicit patterns (`transitions.Machine` / `python-statemachine` / native Enum) + DIA-06 return-value substitution are v0.2.0 must-haves, **independent of spike results**.
- **D-08 (spike ship-vs-defer = determinism only):** SP-2 (sequence branch fidelity alt/loop/par) and SP-1 (general control-flow → state) run as the **first deliverable of their respective plans**. Ship if AST-extractable **deterministically** (byte-identical pure function of `(raw_content, path, config)`); else defer to v0.3.0 (DIA-02-FULL / DIA-05-FULL) and record verdict in `.planning/spikes/SP-2-...md` / `SP-1-...md`. Sole criterion: **is a deterministic rule constructible** (no LLM/heuristic). Layer M bisimulation must not break.
- **D-09 (docstring parser = stdlib internal, no external dep):** Google / NumPy / Sphinx Napoleon section parsing (`Args:` / `Parameters` / `:param:`) is implemented with `ast.get_docstring()` + an internal parser. Do NOT add `docstring_parser` or any external lib — that would change the Tech-stack contract and delegate determinism to an external dependency.
- **D-10 (SPC-04 = detection only):** `icontract` / `deal` decorators + PEP-316 (`pre:`/`post:` docstring keywords) are **detected via AST/regex** to produce contract entries, WITHOUT importing/executing `icontract`/`deal` themselves.

### Claude's Discretion (agent decides autonomously from existing evidence; surface to user only if a contract-level change is needed)

- Final shape of EdgeKind additions (`imports` only / also `contains` / exact semantic wording) — within D-01, decided at DIA-03/DIA-04 design time.
- Each diagram extractor's signature / module placement — `extractors/evaluations/`, inheriting Phase 2 `def extract(cav, config) -> <Pydantic>`.
- DIA-01 composition/aggregation AST implementation detail (annotation parsing, `Optional[X]`/`list[X]` unwrap).
- DIA-02 participant resolution / self-call / chain-call decomposition — inherit Phase 2 callgraph representation (Phase 2 deferred "CallGraph resolution expansion" re-evaluated at Phase 3 entry).
- DIA-05/06 FSM AST detection detail + return-value substitution algorithm + cycle detection.
- Docstring section parser internals (dialect detection, section mapping, pre/post heuristics) — within D-09.
- Spec model field shapes (`FunctionSpec`/`ClassSpec` docstring_sections/preconditions/postconditions/members/invariants) — new `models/evaluations/`, `extra="forbid"` mandatory, physical metadata `physical_*`/`source_*` prefix.
- SP-1/SP-2 spike experiment design.
- sort key / DET-04 composite key construction.
- Test strategy (negative-case fixture `class Color(Enum): RED,GREEN,BLUE → 0 FSM` assertion, golden diagram fixtures).

### Deferred Ideas (OUT OF SCOPE)

- **Phase 4:** SPC-03 Doxygen contract extraction (`\pre`/`\post`/`\invariant`); C++ 5-diagram + 2-spec extraction (LNG-04 schema parity); C++ frontend + libclang.
- **Phase 5:** SCH-04 cross-lib schema compat test (direct import assert); DET-01 byte-identical snapshot completion; DOC-02 README platform compat matrix.
- **v0.3.0+ (spike-verdict-dependent):** DIA-02-FULL (sequence branch fidelity alt/loop/par) if SP-2 says "not deterministically constructible"; DIA-05-FULL (general control-flow → state) if SP-1 says "not deterministically constructible".
- **Sibling lib coordination (optional, non-blocking):** `lib-diagram-parser` node_type doc PR adding `"package"` to comment vocabulary.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DIA-01 | Class diagram: class nodes + inheritance + composition/aggregation/association edges; composition vs aggregation via type-annotation rule, `association` fallback | §Pattern: Class Diagram; §composition-vs-aggregation AST mechanics; pull `FunctionNode`/`TypeDep` primitives |
| DIA-02 | Sequence diagram: linear call flow from call graph (branch fidelity = SP-2 spike) | §Pattern: Sequence Diagram; SP-2 spike framing; pull `CallGraph` primitive |
| DIA-03 | Component diagram: file/module nodes + import-derived dependency edges | §Pattern: Component Diagram; D-01 `imports` EdgeKind; pull `TypeDep` primitive |
| DIA-04 | Package diagram: directory/namespace hierarchy, `node_type="package"`, multiple packages | §Pattern: Package Diagram; D-05/D-06 plain-str node_type; `contains` EdgeKind decision |
| DIA-05 | State diagram: FSM explicit patterns (`transitions.Machine`, `python-statemachine.StateMachine`, native Enum + transition method) | §FSM Detection AST Patterns (3 families + negative case) |
| DIA-06 | Return-value substitution analysis (intra-class, N-level recursive, cycle-safe; `unresolved=true` placeholder) | §Return-Value Substitution Algorithm |
| DIA-07 | All 5 diagrams serialize to `GraphNode`/`GraphEdge`/`GraphModel`/`GuardExpr`; physical-only metadata `physical_*`/`source_*` | §Architectural Responsibility Map; D-04; graph_base.py contract |
| SPC-01 | Function spec: signature + structured docstring (Google/NumPy/Sphinx) + pre/post conditions | §Docstring Dialect Parsing; stdlib-only grammar |
| SPC-02 | Class spec: definition + members + invariants | §Pattern: Class Spec; pull `FunctionNode`/`ContractInfo` |
| SPC-04 | Auxiliary contract markers: `icontract`/`deal` decorators + PEP-316 `pre:`/`post:` docstring keywords | §Auxiliary Contract Markers (detection-only AST shapes) |
</phase_requirements>

## Summary

Phase 3 builds seven evaluation-unit extractors (`extractors/evaluations/{class_diagram,sequence_diagram,component_diagram,package_diagram,state_diagram,function_spec,class_spec}.py`) on top of the Phase 2 CAV + primitive models. Every extractor is a pure function `def extract(cav: CAV, config: ParserConfig) -> <Pydantic>` that **pulls** the primitives it needs (Open-Closed invariant #5: `from lib_code_parser.extractors.primitives import callgraph, type_deps, ...`) and never re-parses the AST. The five diagram extractors emit `GraphModel` (nodes + edges + guards) from `graph_base.py`; the two spec extractors emit new `FunctionSpec` / `ClassSpec` models added under `models/evaluations/`. Registration is seven append-only entries in `_dispatch.py`'s `EVALUATIONS` dict; the executor body never changes (invariant #6). The hard constraint throughout: **determinism** — no LLM, no network, no clock, no dynamic analysis. Output is a byte-identical pure function of `(raw_content, path, config)`, preserving Layer M bisimulation.

The four genuinely novel research areas are (1) **FSM detection AST patterns** for three library families plus the native-Enum pattern, with a fixture-asserted negative case; (2) **return-value substitution** — an intra-procedural, N-level, cycle-detecting resolution of `self.state = self._next()` over `ast` return statements; (3) **docstring dialect parsing** (Google/NumPy/Sphinx Napoleon) implemented stdlib-only; and (4) **auxiliary contract marker detection** (`icontract`/`deal`/PEP-316) without importing those libraries. All four are deterministically expressible over `ast` and require no external dependencies — consistent with D-09/D-10. The two spikes (SP-2 sequence branch fidelity, SP-1 general control-flow → state) gate v0.2.0-vs-v0.3.0 scope purely on whether a deterministic rule is constructible.

**Primary recommendation:** Implement the five diagram extractors as pure `CallGraph`/`TypeDep`/`FunctionNode`-pulling functions emitting `GraphModel`; add `imports` (and decide on `contains`) to `EdgeKind` as the first task; implement the docstring parser as a small stdlib state-machine over `docstring.splitlines()`; detect FSM/contract-marker libraries by their **decorator/call AST shape and import provenance** (mirroring the Phase 2 `contracts.py` provenance-restriction pattern) without importing them; run SP-2 and SP-1 as the first deliverable of their plans and record a ship/defer verdict.

## Architectural Responsibility Map

This is a single-tier in-process pure library — there is no browser/server/API/DB split. The relevant axis is the **lib's own layered architecture** (infrastructure → primitives → evaluations), which the planner must respect because the Open-Closed invariants and the verifier-comparison boundary (D-14) hinge on it.

| Capability | Primary Layer | Secondary Layer | Rationale |
|------------|--------------|-----------------|-----------|
| Class/sequence/component/package/state diagram extraction | `extractors/evaluations/` (verifier-facing) | pulls `extractors/primitives/` | Evaluations are the ONLY layer the verifier compares against logical arch (D-14); diagrams are evaluation units |
| Function/class spec extraction | `extractors/evaluations/` | pulls `primitives/functions`, `primitives/contracts` | Specs are verifier-facing evaluation units (SPC → US-01/US-22) |
| EdgeKind taxonomy (`imports`/`contains` add) | `models/evaluations/graph_base.py` | — | Closed Literal applies ONLY to verifier-facing surface; primitives keep free-form `str` (D-14) |
| Composition/aggregation decision | `extractors/evaluations/class_diagram.py` | pulls `primitives/functions` (annotations) | Annotation-rule logic is an evaluation-unit concern; primitive layer stays language-fact-only |
| Return-value substitution | `extractors/evaluations/state_diagram.py` | reads `cav.payload` (ast.Module) for callee bodies | Intra-class resolution needs raw AST of callee return statements; state_diagram owns the algorithm |
| Docstring dialect parsing | `extractors/evaluations/function_spec.py` (+ shared helper) | `ast.get_docstring()` from CAV | Stdlib-only parser; a shared `_docstring.py` helper module is permitted (new file, not a primitive) |
| FSM / contract-marker library detection | `extractors/evaluations/state_diagram.py` / `function_spec.py` / `class_spec.py` | import-provenance map (Phase 2 `contracts.py` pattern) | Detection-only; never import the target libs (D-10) |
| Spec/diagram model shapes | `models/evaluations/{spec,graph_base}.py` | — | New `FunctionSpec`/`ClassSpec` are evaluation models; `extra="forbid"` mandatory |
| Dispatch registration | `_dispatch.py` `EVALUATIONS` (append-only) | — | Invariant #4; 7 new entries, executor untouched (#6) |

## Standard Stack

**No new runtime dependencies.** D-09 (stdlib-only docstring parsing) and D-10 (detection-only, no `icontract`/`deal` import) explicitly forbid adding external libraries. The "stack" for Phase 3 is the existing pinned set plus stdlib modules already in use.

### Core (already in stack — verified against pyproject.toml / CLAUDE.md Tech Stack)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `ast` | CPython 3.11+ | All diagram/spec extraction (AST walking, `ast.get_docstring`, `ast.unparse`) [VERIFIED: codebase — used in every Phase 2 extractor] | The deterministic substrate; the single parse site is `frontends/python.py` |
| Python stdlib `re` | CPython 3.11+ | PEP-316 docstring keyword detection, NumPy underline detection, TraceTag regex (Phase 2) [VERIFIED: codebase] | Deterministic, no deps |
| Python stdlib `pathlib` | CPython 3.11+ | Module/package name derivation via `_paths.get_module_name()` (ARC-04) [VERIFIED: codebase] | Single source of truth for path→name |
| `pydantic` | `>=2.13.0,<3.0` | Evaluation models (`GraphModel`, new `FunctionSpec`/`ClassSpec`); `extra="forbid"` (SCH-03) [VERIFIED: codebase — all models use `ConfigDict(extra="forbid")`] | Schema contract with verifier |

### Supporting (test-time only — already dev deps)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | `>=8` | Unit + acceptance + golden tests [VERIFIED: codebase, pytest 9.0.3 in `.pyc` names] | All Phase 3 tests |
| `pytest-cov` | (dev extra) | Coverage | CI |
| `ruff` | (dev extra) | Lint/format, `select=["E","F","I"]`, line-length 100, target py311 [VERIFIED: CLAUDE.md] | Pre-commit |
| `pyright` | `1.1.409` pin | Type check (also the AST-03 subprocess oracle — NOT used by Phase 3 evaluations) | CI |

### Alternatives Considered (and REJECTED by locked decisions)

| Instead of | Could Use | Why REJECTED |
|------------|-----------|--------------|
| Internal docstring parser | `docstring_parser` (PyPI) | **D-09 forbids** — adding it changes Tech-stack contract + delegates determinism to external dep |
| Detecting `transitions`/`python-statemachine` by AST shape | Importing them and introspecting | **D-10/Determinism** — importing executes code, breaks pure-function guarantee |
| Importing `icontract`/`deal` | Detecting decorators by AST | **D-10 forbids** — detection-only |
| Direct-import `lib-diagram-parser` models | `from lib_diagram_parser import GraphNode` | **D-02 forbids** — would lose `extra="forbid"`/`physical_*`/closed Literal |
| `py2puml`/`pyreverse` for class diagrams | external diagram generators | Not deterministic-pure-function caller-agnostic; this lib emits structured data, not rendered diagrams. **(py2puml's annotation-only composition rule is a useful *reference* for DIA-01 logic — see §composition-vs-aggregation — but the lib is not a dependency.)** |

**Installation:** None. No `pip install` for Phase 3. The planner must NOT add any dependency to `pyproject.toml`.

## Package Legitimacy Audit

> Phase 3 installs **zero** external packages (D-09/D-10 stdlib-only). slopcheck/registry verification is **N/A** — there is nothing to install.

| Package | Registry | Disposition |
|---------|----------|-------------|
| (none) | — | Phase 3 adds no runtime/dev dependencies. `transitions`, `python-statemachine`, `icontract`, `deal`, `py2puml`, `docstring_parser` are **detection targets / reference material**, NOT installed or imported. |

**Packages removed due to slopcheck [SLOP] verdict:** none (nothing installed)
**Packages flagged as suspicious [SUS]:** none

*The external library names appearing in this document (`transitions`, `python-statemachine`, `icontract`, `deal`, PEP-316) are referenced only as **AST detection targets** — the extractor matches their decorator/call shapes in user code without importing them. Their exact API shapes below are `[CITED]` from official docs for detection-pattern accuracy, not for installation.*

## Architecture Patterns

### System Architecture Diagram

```
                    caller passes (raw_content: bytes, path: str, ParserConfig)
                                          │
                                          ▼
                          executor.py  CodeParserExecutor.execute
                                          │
                       FRONTENDS["python"](raw, path, config)   ← single ast.parse() site
                                          │
                                          ▼
                                  CAV (frozen envelope)
                            { language, path, payload=ast.Module, raw_content }
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            │ (Phase 2 primitives, PULLED by evaluations — never re-parse)│
            ▼                             ▼                              ▼
     primitives/functions          primitives/callgraph          primitives/type_deps
     → list[FunctionNode]          → CallGraph                    → list[TypeDep]
            │                             │                              │
            │                       primitives/contracts → dict[str,ContractInfo]
            │                             │                              │
            └──────────────┬──────────────┴───────────────┬─────────────┘
                           │ pull                          │ pull
                           ▼                               ▼
     ┌─────────────────────────────────────────────────────────────────────┐
     │  EVALUATIONS (Phase 3 — 7 append-only entries, each pure (cav,config))│
     │                                                                       │
     │  class_diagram  ── pulls functions(annotations)+inheritance → GraphModel
     │  sequence_diagram ─ pulls callgraph → GraphModel  [SP-2 branch frames?]│
     │  component_diagram ─ pulls type_deps(imports) → GraphModel (edge=imports)
     │  package_diagram ── pulls path hierarchy → GraphModel (node_type=package)
     │  state_diagram ──── FSM detect + return-value subst → GraphModel+guards │
     │                       [SP-1 general control-flow?]                     │
     │  function_spec ──── signature + docstring dialect + pre/post → FunctionSpec
     │  class_spec ─────── members + invariants + contracts → ClassSpec        │
     └─────────────────────────────────────────────────────────────────────┘
                           │ each → DET-04 sort-on-exit (stable composite key)
                           ▼
              NormalizedArtifact[CodeContent]  (model_dump_json byte-identical)
```

### Recommended Project Structure (new files only; existing files untouched per invariants #1/#2/#6)

```
lib_code_parser/
├── _dispatch.py                         # +7 append-only EVALUATIONS entries (only existing file touched)
├── models/evaluations/
│   ├── graph_base.py                    # EDIT: append "imports" (+ maybe "contains") to EdgeKind (D-01)
│   └── spec.py                          # NEW: FunctionSpec, ClassSpec, DocstringSection, SpecCondition
└── extractors/evaluations/
    ├── __init__.py                      # NEW
    ├── _docstring.py                    # NEW (shared helper): Google/NumPy/Sphinx dialect parser (D-09)
    ├── _fsm_detect.py                   # NEW (shared helper): 3 FSM-family AST matchers (optional split)
    ├── class_diagram.py                 # NEW (DIA-01)
    ├── sequence_diagram.py              # NEW (DIA-02; SP-2 spike inside)
    ├── component_diagram.py             # NEW (DIA-03)
    ├── package_diagram.py               # NEW (DIA-04)
    ├── state_diagram.py                 # NEW (DIA-05/06; SP-1 spike inside)
    ├── function_spec.py                 # NEW (SPC-01; pulls _docstring)
    └── class_spec.py                    # NEW (SPC-02; SPC-04 marker detection)
```

> Note: `docs/09-extending.md` §不変条件#2 lists the evaluation files as `extractors/{name}.py` (flat). The CONTEXT.md and PROJECT.md both specify `extractors/evaluations/{name}.py` (nested). **Use the nested `extractors/evaluations/` layout** — it matches CONTEXT.md §domain, the existing `extractors/primitives/` nesting, and the `models/{infrastructure,primitives,evaluations}/` 3-way split (ARC-01). [ASSUMED — the docs/09 flat paths are illustrative; the nested layout is the established convention. Planner should confirm and, if needed, note the doc as illustrative.]

### Pattern 1: Pure CAV-consuming evaluation extractor (inherit Phase 2 signature)

**What:** Each evaluation is `def extract(cav, config) -> <Pydantic>`, pulls primitives, never re-parses.
**When to use:** All 7 Phase 3 extractors.
**Example (verified pattern from Phase 2 + docs/09-extending §#5):**
```python
# Source: docs/09-extending.md §不変条件#5 + extractors/primitives/contracts.py (codebase)
from __future__ import annotations

import ast
from lib_code_parser.extractors.primitives import functions, type_deps
from lib_code_parser.models.evaluations.graph_base import GraphModel, GraphNode, GraphEdge
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    tree = cav.payload
    assert isinstance(tree, ast.Module)  # same guard as Phase 2 extractors
    fns = functions.extract(cav, config)      # PULL primitive (invariant #5)
    tds = type_deps.extract(cav, config)      # PULL primitive
    nodes, edges = _build(...)                # pure logic
    nodes.sort(key=lambda n: n.node_id)       # DET-04 sort-on-exit
    edges.sort(key=lambda e: (e.source, e.target, e.edge_type))
    return GraphModel(nodes=nodes, edges=edges)
```

### Pattern 2: Import-provenance restriction for library detection (reuse Phase 2 `contracts.py`)

**What:** Build a `{local_name: canonical_name}` map from `import`/`from X import` statements, classify a decorator/call ONLY if its name resolves through the target-library import map (or is an attribute form `lib.thing`). Prevents same-name false positives.
**When to use:** FSM library detection (`transitions.Machine`, `python-statemachine`), contract-marker detection (`icontract`/`deal`).
**Example (verified — verbatim pattern from Phase 2):**
```python
# Source: lib_code_parser/extractors/primitives/contracts.py:89-110 (codebase)
def _resolve_aliases(module: ast.Module, target_pkgs: tuple[str, ...]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod in target_pkgs or any(mod.startswith(p + ".") for p in target_pkgs):
                for a in node.names:
                    aliases[a.asname or a.name] = a.name
        elif isinstance(node, ast.Import):       # `import transitions` / `import deal`
            for a in node.names:
                if a.name in target_pkgs:
                    aliases[a.asname or a.name] = a.name
    return aliases
```

### Pattern 3: DET-04 sort-on-exit composite keys (mandatory for every output)

**What:** Sort all collections by a stable composite key before emission so output is byte-identical regardless of dict/set iteration order or `PYTHONHASHSEED`.
**When to use:** Every diagram (`nodes` by `node_id`; `edges` by `(source, target, edge_type, label)`; `guards` by `(from_state, to_state, condition)`) and every spec (`members` by name, `preconditions`/`postconditions` by `(source_kind, line_no, text)`).
**Example:**
```python
# Source: extractors/primitives/callgraph.py:95 (codebase) — same discipline
edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))
```

### Anti-Patterns to Avoid

- **Re-parsing the AST** (`ast.parse(...)` inside an evaluation) — violates AST-05 single-parse; the only parse site is `frontends/python.py`. Use `cav.payload`.
- **Adding a catch-all EdgeKind** (`uses`/`other`/`misc`/`dep`/`depends`) — Pitfall 7 / docs/09. `imports` is allowed because it is an explicit semantic; `dependency` is NOT.
- **Mutating an existing primitive/evaluation file** — invariant #1/#2. New aspects = new files.
- **`if config.extract_class_diagram:` branches in executor.py** — invariant #6. Registration is dict-driven.
- **Importing `transitions`/`python-statemachine`/`icontract`/`deal`** — D-10 + determinism. Detect by AST shape only.
- **Emitting unsorted output** — breaks DET-01/DET-04 byte-identical guarantee.
- **Renaming EdgeKind to sibling-lib spelling** (`inherits`→`inheritance`) — D-03; verifier bridges the gap.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Path → module/package name | A new `_get_module_name` in each extractor | `lib_code_parser._paths.get_module_name()` | ARC-04 single source of truth; v0.1.0 had 4× duplication |
| Decorator alias resolution | Fresh import-walk per extractor | Copy/share the `contracts.py:_resolve_decorator_aliases` provenance pattern | Phase 2 already solved same-name false-positive defense (T-02-19) |
| Annotation → string | Manual `ast.Attribute`/`ast.Name` joining | `ast.unparse(node)` | Phase 2 `_extract_annotation` already does exactly this |
| Docstring extraction | Manual first-statement string-literal walk | `ast.get_docstring(node)` | stdlib-correct, handles `\n`-dedent, concatenated literals |
| Call name extraction | New AST visitor | `callgraph.py:_get_call_name` shape (Name→id, Attribute→attr) | Phase 2 truth-table-tested over 7 fixtures |
| Sorting/determinism | Custom ordering | DET-04 sort-on-exit with composite keys | Established discipline; CI gates on byte-identical |

**Key insight:** Phase 3 is overwhelmingly **composition of Phase 2 primitives + small pure transforms**, not net-new parsing. The only genuinely new algorithmic content is (a) the docstring dialect state-machine, (b) FSM AST matchers, (c) return-value substitution. Everything else reuses solved Phase 2 mechanics.

## FSM Detection AST Patterns (DIA-05 / DIA-06)

Three explicit-pattern families must be detected deterministically. All matching is over `cav.payload` (ast.Module). For each, the extractor emits `GraphNode(node_type="state", ...)` per state and `GraphEdge(edge_type="transitions_to", ...)` per transition (and `GuardExpr` when a guard/event is present).

### Family A — `transitions.Machine(...)` library call [CITED: github.com/pytransitions/transitions; pypi.org/project/transitions]

States and transitions are passed as **keyword arguments** to a `Machine(...)` call. The deterministic extractor matches an `ast.Call` whose `func` resolves (via the import-provenance map, Pattern 2) to `transitions.Machine` or an imported `Machine`, then reads keyword args:

- `states=` — a `list` of **string literals** (`['A','B','C']`) OR list of `dict` literals (`[{'name':'A'}, ...]`) OR (rare) `Enum` reference.
- `transitions=` — a `list` of **dict literals** `{'trigger':..., 'source':..., 'dest':...}` OR **list-of-list literals** `[['walk','A','B'], ...]` (`[trigger, source, dest]`).
- `initial=` — string literal (initial state → emit a pseudostate edge if desired).

AST node shapes to match:
```
ast.Call(
  func = ast.Attribute(value=ast.Name(id="transitions"|<alias>), attr="Machine")
       | ast.Name(id="Machine")  # resolved via `from transitions import Machine`
  keywords = [
    ast.keyword(arg="states",      value=ast.List(elts=[ast.Constant(str) | ast.Dict | ...])),
    ast.keyword(arg="transitions", value=ast.List(elts=[ast.Dict(keys/values=Constant) | ast.List(elts=[Constant,Constant,Constant])])),
    ast.keyword(arg="initial",     value=ast.Constant(str)),
    ast.keyword(arg="model", ...),   # ignore for graph; affects method binding only
  ]
)
```
Determinism note: only `ast.Constant` (str) literals are resolvable. Variables/comprehensions for `states`/`transitions` are **undecidable statically** → emit what is resolvable; for unresolvable transitions, follow the DIA-06 `unresolved=true` placeholder discipline (see below). [VERIFIED: transitions list-of-dicts and list-of-lists forms confirmed via official GitHub README + PyPI examples.]

### Family B — `python-statemachine` `StateMachine`/`StateChart` subclass [CITED: python-statemachine.readthedocs.io/en/latest/transitions.html, /api.html]

States are **class attributes** assigned `State(...)`; transitions are class attributes assigned `source.to(target)` (the attribute name is the *event*). The `|` operator combines transitions into one event.

AST node shapes to match — find an `ast.ClassDef` whose bases resolve (Pattern 2) to `statemachine.StateMachine` / `StateChart`, then within its body:
```
# State declarations:
ast.Assign(targets=[ast.Name(id="pending")],
           value=ast.Call(func=ast.Name|Attribute(attr="State"),
                          keywords=[keyword(arg="initial"|"final", value=Constant(bool)), ...]))
    → GraphNode(node_id="pending", node_type="state", label="pending",
                attributes={"initial":"true"} if initial)

# Transition declarations (event = LHS attribute name):
ast.Assign(targets=[ast.Name(id="confirm")],
           value=ast.Call(func=ast.Attribute(value=ast.Name(id="pending"), attr="to"),
                          args=[ast.Name(id="confirmed")]))
    → GraphEdge(source="pending", target="confirmed", edge_type="transitions_to", label="confirm")

# Combined with | (BinOp):
ast.Assign(value=ast.BinOp(op=ast.BitOr(), left=Call(...to...), right=Call(...to...)))
    → multiple edges under one event label
```
`source.to(target)` is the canonical form; `target.from_(source)` is the reverse form (resolve `from_` → emit edge source→target). [VERIFIED: `State`/`.to()`/`.from_()`/`|`-combine confirmed via official readthedocs.]

### Family C — native `Enum`-typed instance attribute + transition-method pattern [ASSUMED — no single canonical library; this is a structural heuristic]

Pattern: a class has an instance attribute typed/assigned to an `Enum` member, and methods that reassign `self.<attr> = <EnumClass>.<MEMBER>`. Each such literal assignment is a transition from the method's entry state(s) to the assigned member.

AST shapes:
```
# State enum:
ast.ClassDef(bases=[Name(id="Enum")|Attribute(attr="Enum")], body=[Assign(targets=[Name], value=Constant), ...])
    → each member is a candidate state

# Transition (literal):
ast.Assign(targets=[ast.Attribute(value=ast.Name(id="self"), attr="state")],
           value=ast.Attribute(value=ast.Name(id="<EnumClass>"), attr="<MEMBER>"))
    → GraphEdge(target="<MEMBER>", edge_type="transitions_to")   # source resolved from current-state context

# Transition (non-literal → triggers DIA-06 substitution):
ast.Assign(targets=[ast.Attribute(attr="state")],
           value=ast.Call(func=ast.Attribute(value=Name(id="self"), attr="_next")))
    → resolve _next()'s return statements (see §Return-Value Substitution)
```

### Negative case (fixture-asserted, ROADMAP SC3)

```python
class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3
```
A bare `Enum` with **no transition method and no `self.<attr> = ...` reassignment** is NOT an FSM. The extractor must emit **zero** state machines / zero `GraphNode(node_type="state")` for this input. The discriminator: Family C requires *both* an Enum-typed state attribute *and* at least one transition assignment (`self.state = ...`). [VERIFIED: this is the SC3 fixture-asserted negative case; the rule follows directly from requiring a transition site.]

## Return-Value Substitution Algorithm (DIA-06 / SC4)

When a transition assigns a **non-literal** value — `self.state = self._next()` — the extractor must resolve the callee's return statements intra-class.

**Algorithm (deterministic, intra-procedural, N-level recursive, cycle-safe):**

1. **Resolve callee**: `self._next()` → look up method `_next` in the *same class* (intra-class only; cross-class/external = unresolvable). Match by `ast.FunctionDef.name` within the enclosing `ast.ClassDef`.
2. **Collect return values**: walk the callee body for `ast.Return` nodes. For each `return X`:
   - `X` is an `ast.Attribute` `EnumClass.MEMBER` or `ast.Constant` → **resolved literal state**.
   - `X` is another `self._other()` call → **recurse** (step 1) with a `visited: set[str]` of method names.
   - `X` is a conditional/ternary/variable → contributes a partial; unresolved fragment.
3. **Cycle detection**: maintain `visited` set of `(class, method)` keys; if a method is re-entered, stop that branch (do not infinite-loop). The branch that hit the cycle yields no new literal.
4. **Emit**:
   - **Fully resolved** (every return path reduced to a literal state): emit one `GraphEdge(source=<current>, target=<each-literal>, edge_type="transitions_to")` per distinct resolved target.
   - **Unresolvable** (at least one path cannot be reduced to a literal, or callee is external): emit **one placeholder edge** with `attributes={"unresolved":"true"}` (DIA-06 contract). Carry the unresolved marker on the `GraphEdge` — since `GraphEdge` has no free `unresolved` field and `extra="forbid"`, **put it in `GraphEdge.attributes`**... **CORRECTION:** `GraphEdge` in `graph_base.py` has NO `attributes` field (only `source/target/edge_type/label/physical_module`). The `unresolved` marker must go either in `label` (e.g., `label="unresolved"`) OR as a new `physical_*`/`source_*`-prefixed optional field. **[Discretion — planner decides]:** recommend adding `source_unresolved: bool = False` (SCH-02 `source_` prefix optional field, default False keeps parity) to `GraphEdge`, OR encoding via `GuardExpr`/`label`. Verify against the GraphNode (which *does* have `attributes: dict[str,str]`) — a state-node-level marker may be cleaner. The planner MUST reconcile DIA-06's "`unresolved=true` attribute" wording with the actual `GraphEdge` schema (no `attributes` field) at design time.

**Standard intra-procedural return-resolution approaches** surveyed: this is a bounded, AST-local form of **constant/return-value propagation** — a well-known deterministic dataflow technique restricted to literal returns. No external dependency needed; it is a recursive AST walk with a visited-set. Recursion depth is naturally bounded by the number of methods in the class (finite), and the visited-set guarantees termination. [ASSUMED — algorithm design is Claude's-discretion per CONTEXT.md; the approach is standard and deterministic.]

## Docstring Dialect Parsing (SPC-01 / D-09 — stdlib only)

`ast.get_docstring(node)` yields the raw docstring; the parser is a small state machine over `docstring.splitlines()`. Dialect is auto-detected, then sections mapped to a normalized `DocstringSection` list. Pre/post conditions are derived heuristically (see below).

### Section-header grammars (the three dialects)

| Dialect | Param section | Returns | Raises | Detection signal |
|---------|--------------|---------|--------|------------------|
| **Google** | `Args:` (or `Arguments:`) then indented `name (type): desc` | `Returns:` | `Raises:` | Line ending in `:` from a known header set, followed by an indented block [CITED: Napoleon docs — Google style] |
| **NumPy** | `Parameters\n----------` (header line + dashed underline ≥ header length) then `name : type` newline-indented desc | `Returns\n-------` | `Raises\n------` | A header line immediately followed by a line of only `-` (underline) [CITED: Napoleon docs — NumPy style] |
| **Sphinx (reST)** | `:param name:` / `:param type name:` | `:returns:` / `:return:` | `:raises Exc:` / `:raise:` | Lines matching `^\s*:(param|type|returns?|raises?|rtype)\b` [CITED: Sphinx reST field lists] |

**Deterministic dialect detection order** (first match wins, byte-stable):
1. If any line matches `^\s*:(param|returns?|raises?|type|rtype)\b` → **Sphinx**.
2. Else if any header line (`Parameters|Returns|Raises|Yields|...`) is immediately followed by a line of `^-{3,}$` → **NumPy**.
3. Else if any line is a Google header (`^(Args|Arguments|Returns|Raises|Yields|Attributes|Note|Example[s]?):\s*$`) → **Google**.
4. Else → **no structured sections** (treat whole docstring as `summary`).

### Section mapping → normalized model

Recommend a normalized `DocstringSection(kind: Literal["params","returns","raises","summary","other"], name: str = "", type_ref: str = "", text: str)` so the verifier sees one shape regardless of source dialect. Params explode into one section per parameter; `summary` is the leading prose. [ASSUMED — exact field shape is Claude's-discretion per CONTEXT.md.]

### Pre/post condition derivation (heuristic, deterministic)

- **Precondition candidates**: `:param ...` / `Args:` entries whose description contains an imperative constraint keyword (`must be`, `non-negative`, `> 0`, `not None`, `required`) → emit a `SpecCondition(kind="precondition", text=...)`. Also `Raises: ValueError if ...` → a documented precondition.
- **Postcondition candidates**: `Returns:` description constraints; `:returns:` clauses. `Raises:` entries are documented postcondition-failure modes.
- These are **documentation-derived** (lower fidelity than the Phase 2 `ContractInfo` decorator-derived contracts) — keep them in a separate field / mark `source_kind="docstring"` so the verifier can weight them. [ASSUMED — heuristic; CONTEXT.md leaves the heuristic to Claude's-discretion within D-09.]

> **Determinism caution:** keep the heuristic a fixed keyword/regex set (no NLP, no scoring). The same docstring → same conditions, every run.

## Auxiliary Contract Markers (SPC-04 / D-10 — detection only)

Detect (do NOT import) three marker families. All produce a `ContractEntry`-like record extending the Phase 2 `ContractInfo` model with a new `source_kind` value (e.g., `icontract_require`, `deal_pre`, `pep316_pre`). Detection uses the same import-provenance map (Pattern 2).

### icontract [CITED: icontract.readthedocs.io/en/latest/usage.html, /api.html]

- `@icontract.require(lambda x: x > 0)` — **precondition** (function/method decorator)
- `@icontract.ensure(lambda result: result >= 0)` — **postcondition** (`result` is reserved)
- `@icontract.invariant(lambda self: ...)` — **invariant** (**class decorator**)

AST shapes (decorator on `FunctionDef` / `ClassDef`):
```
ast.Call(func=ast.Attribute(value=ast.Name(id="icontract"|<alias>), attr="require"|"ensure"|"invariant"))
ast.Call(func=ast.Name(id="require"|"ensure"|"invariant"))   # via `from icontract import require, ensure, invariant`
```
The condition lambda can be `ast.unparse`'d into the `text` field for the verifier. [VERIFIED: require/ensure/invariant names + class-decorator invariant confirmed via official icontract docs.]

### deal [CITED: github.com/life4/deal; deal.readthedocs.io]

- `@deal.pre(lambda x: x > 0)` — precondition
- `@deal.post(lambda result: result >= 0)` — postcondition (validates return)
- `@deal.ensure(lambda _: ...)` — post-condition with args+result
- `@deal.inv(lambda self: ...)` — invariant (class)
- (also `@deal.raises(...)`, `@deal.has(...)` — out of scope for pre/post but detectable)

AST shapes: identical structure to icontract — `ast.Attribute(value=Name(id="deal"|<alias>), attr="pre"|"post"|"ensure"|"inv")` or bare `Name` via `from deal import pre, post`. [VERIFIED: `@deal.post(lambda result: ...)` confirmed via official GitHub README; `pre`/`ensure`/`inv` are the documented DbC trio per repo description "Classic DbC: precondition, postcondition, invariant".]

### PEP-316 docstring keywords [CITED: PEP 316 — Programming by Contract for Python]

PEP-316 was **deferred/never accepted**, but its `pre:`/`post:` docstring convention is a real marker some codebases use. Detect via regex over `ast.get_docstring()`:
```
^\s*pre:\s*(.+)$     → precondition text
^\s*post(?:\[\w+\])?:\s*(.+)$  → postcondition text   (PEP-316 allows post[old]: forms)
```
These are **docstring-derived** (mark `source_kind="pep316_pre"/"pep316_post"`). [VERIFIED: PEP-316 `pre:`/`post:` docstring keyword convention; CITED as a deferred PEP — detection is regex-only, no library exists to import.]

**Extending `ContractInfo`:** Phase 2's `SourceKind` Literal is closed (`pydantic_validator`, `pydantic_field_validator`, `pydantic_model_validator`, `dataclass_post_init`). Per invariant #1 (existing primitive files immutable) and #3 (optional/additive), **do NOT edit `primitives/contracts.py`**. Instead, SPC-04 markers belong to the **evaluation layer** (`class_spec.py`/`function_spec.py`) emitting into the new `FunctionSpec`/`ClassSpec` models with their own `source_kind` set — OR, if extending the primitive `SourceKind` Literal is desired, that is an append-only Literal change requiring care. **[Discretion — planner decides]:** recommend keeping SPC-04 markers in the evaluation-layer spec models (cleaner, respects invariant #1) rather than mutating the frozen Phase 2 `contracts.py`.

## composition vs aggregation (DIA-01 / SC1)

The type-annotation rule (ROADMAP SC1), implemented over `ast` annotations on declared instance attributes. This mirrors `py2puml`'s annotation-only approach [CITED: github.com/lucsorel/py2puml — "detection of composition relies on type annotations only; assigned values are never evaluated"] but is implemented internally (py2puml is NOT a dependency).

**Annotation sources** (deterministic, no value evaluation):
1. Class-level annotated assignments: `ast.AnnAssign(target=Name, annotation=...)` in the `ClassDef` body.
2. `__init__` self-attribute annotations: `self.x: Foo = ...` → `ast.AnnAssign(target=ast.Attribute(value=Name("self"), attr="x"), annotation=...)`.
3. (Lower fidelity) `self.x = Foo()` unannotated → only resolvable if RHS is a direct `ast.Call(func=Name)` of a known class → `instantiates`/`composes`; else skip (do not guess).

**Decision rule (annotation unwrap):**
```
annotation = ast.unparse(node.annotation)  then structurally inspect:
  • Direct class type      `x: Engine`                 → COMPOSITION  (composes)  [owned, lifetime-bound]
  • Optional[X] / X | None `x: Optional[Engine]`       → AGGREGATION (aggregates) [has-a, no lifetime]
  • Container[X]           `x: list[Engine]` / `set[X]` / `dict[K,V]` → AGGREGATION (aggregates)
  • Builtin/primitive      `x: int` / `x: str`         → NOT a relationship (field, not edge)
  • Undecidable            (forward ref str, Any, TypeVar, unresolved name) → ASSOCIATION (associates) fallback
```
**Annotation-unwrap mechanics (AST):**
- `Optional[X]` → `ast.Subscript(value=Name("Optional"), slice=...)`; unwrap to inner `X`.
- `X | None` → `ast.BinOp(op=ast.BitOr(), left=X, right=Constant(None))`; unwrap to `X`.
- `list[X]`/`set[X]` → `ast.Subscript(value=Name("list"|"set"), slice=X)` → inner `X`, edge=aggregates.
- `dict[K,V]` → `ast.Subscript(value=Name("dict"), slice=ast.Tuple([K,V]))` → consider value `V` (and/or `K`) types.
- Resolve whether the inner name is a "known class" by checking it against the set of `ClassDef` names in the module (+ imported class names from the `TypeDep`/import map). Unknown/builtin → no class edge.

Inheritance is separate and unambiguous: `ast.ClassDef.bases` → `edge_type="inherits"` (or `implements` for ABC/Protocol bases — discretion). [VERIFIED: composition=annotation-only rule corroborated by py2puml official docs; unwrap mechanics are standard `ast` per stdlib.]

## Common Pitfalls

### Pitfall 1: GraphEdge has no `attributes` field (DIA-06 `unresolved=true` mismatch)
**What goes wrong:** DIA-06 says "emit placeholder edge with `unresolved=true` attribute", but `GraphEdge` in `graph_base.py` has only `source/target/edge_type/label/physical_module` + `extra="forbid"`. Setting `edge.attributes["unresolved"]` raises `ValidationError`.
**Why:** Only `GraphNode` has `attributes: dict[str,str]`; `GraphEdge` does not.
**How to avoid:** Reconcile at design time — either (a) add a `source_unresolved: bool = False` SCH-02-prefixed optional field to `GraphEdge`, (b) use `label="unresolved"`, or (c) carry the marker on the state `GraphNode.attributes`. Recommend (a).
**Warning signs:** A test constructing `GraphEdge(attributes=...)` fails at validation.

### Pitfall 2: Adding a catch-all EdgeKind for component/package edges
**What goes wrong:** Reaching for `dependency`/`depends`/`uses` for DIA-03 import edges or DIA-04 containment.
**Why:** Phase 1 Pitfall 7 explicitly forbids catch-all values.
**How to avoid:** Use the D-01-approved explicit `imports` (and decide `contains` for DIA-04). Both are explicit semantics, not catch-alls.
**Warning signs:** PR diff to `graph_base.py` adding any of `uses/other/misc/dep/depends`.

### Pitfall 3: Non-deterministic ordering from dict/set iteration
**What goes wrong:** Emitting nodes/edges in `dict`/`set` insertion or hash order → output varies across `PYTHONHASHSEED`, breaking DET-01.
**Why:** Sets are unordered; dicts preserve insertion but extractors often build via sets for dedup.
**How to avoid:** DET-04 sort-on-exit with a total composite key on every collection. Use `dict.fromkeys` for ordered dedup (Phase 2 callgraph pattern), then sort.
**Warning signs:** Snapshot test flakes between runs.

### Pitfall 4: Same-name false positives in library detection
**What goes wrong:** A user's own `Machine` / `require` / `pre` function gets mis-detected as `transitions.Machine` / `icontract.require` / `deal.pre`.
**Why:** Bare-name matching without provenance.
**How to avoid:** Reuse the Phase 2 `contracts.py` import-provenance restriction (Pattern 2): classify only if the name resolves through the target-library import map or is an attribute form.
**Warning signs:** FSM/contract edges appearing for code that never imports the library.

### Pitfall 5: Re-parsing the AST inside an evaluation
**What goes wrong:** Calling `ast.parse()` in `class_diagram.py` etc.
**Why:** Convenience; forgetting CAV carries the parsed module.
**How to avoid:** Always `tree = cav.payload; assert isinstance(tree, ast.Module)`. The single parse site is `frontends/python.py` (AST-05).
**Warning signs:** `tests/parity/test_ast_05_one_parse.py` fails.

### Pitfall 6: Editing frozen Phase 2 files for SPC-04 source_kind
**What goes wrong:** Adding `icontract_require` to `primitives/contracts.py:SourceKind`.
**Why:** SPC-04 markers feel like "more contracts".
**How to avoid:** Keep SPC-04 detection in the evaluation layer (`class_spec.py`/`function_spec.py`) with its own source_kind set; invariant #1 freezes `primitives/contracts.py`.
**Warning signs:** `git diff` touches `extractors/primitives/contracts.py` or `models/primitives/contracts.py`.

### Pitfall 7: Nested vs flat extractor path divergence (docs/09 vs CONTEXT.md)
**What goes wrong:** docs/09-extending §#2 lists `extractors/{name}.py` (flat); CONTEXT/PROJECT say `extractors/evaluations/{name}.py` (nested).
**Why:** Doc illustrative paths not updated to nested convention.
**How to avoid:** Use nested `extractors/evaluations/` (matches `extractors/primitives/` + `models/evaluations/`). Note docs/09 as illustrative; do not let it drive layout.
**Warning signs:** Import paths inconsistent with `models/evaluations/`.

## Code Examples

### Detecting `transitions.Machine(...)` keyword args (FSM Family A)
```python
# Source: stdlib ast + transitions API shape [CITED: pytransitions/transitions README]
import ast

def _resolve_machine_kwargs(call: ast.Call) -> tuple[list[str], list[dict]]:
    states: list[str] = []
    transitions: list[dict] = []
    for kw in call.keywords:
        if kw.arg == "states" and isinstance(kw.value, ast.List):
            for elt in kw.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    states.append(elt.value)
                elif isinstance(elt, ast.Dict):  # {'name': 'A', ...}
                    for k, v in zip(elt.keys, elt.values):
                        if isinstance(k, ast.Constant) and k.value == "name" and isinstance(v, ast.Constant):
                            states.append(v.value)
        elif kw.arg == "transitions" and isinstance(kw.value, ast.List):
            for elt in kw.value.elts:
                if isinstance(elt, ast.Dict):       # {'trigger','source','dest'}
                    d = {ast.literal_eval(k): ast.literal_eval(v)
                         for k, v in zip(elt.keys, elt.values)
                         if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)}
                    transitions.append(d)
                elif isinstance(elt, ast.List) and len(elt.elts) >= 3:  # [trigger, source, dest]
                    vals = [e.value for e in elt.elts if isinstance(e, ast.Constant)]
                    if len(vals) >= 3:
                        transitions.append({"trigger": vals[0], "source": vals[1], "dest": vals[2]})
    return states, transitions
```

### Detecting `python-statemachine` transition (FSM Family B)
```python
# Source: stdlib ast + python-statemachine API [CITED: python-statemachine.readthedocs.io transitions.html]
def _is_to_transition(assign: ast.Assign) -> tuple[str, str, str] | None:
    """Return (event, source_state, target_state) for `event = src.to(dst)`."""
    if not (len(assign.targets) == 1 and isinstance(assign.targets[0], ast.Name)):
        return None
    event = assign.targets[0].id
    val = assign.value
    if (isinstance(val, ast.Call) and isinstance(val.func, ast.Attribute)
            and val.func.attr == "to"
            and isinstance(val.func.value, ast.Name) and val.args
            and isinstance(val.args[0], ast.Name)):
        return event, val.func.value.id, val.args[0].id
    return None
```

### Detecting icontract / deal decorators (SPC-04, detection-only)
```python
# Source: extractors/primitives/contracts.py provenance pattern + icontract/deal API [CITED]
_MARKER = {  # (package, attr) -> (kind, source_kind)
    ("icontract", "require"): ("precondition", "icontract_require"),
    ("icontract", "ensure"):  ("postcondition", "icontract_ensure"),
    ("icontract", "invariant"): ("invariant", "icontract_invariant"),
    ("deal", "pre"):    ("precondition", "deal_pre"),
    ("deal", "post"):   ("postcondition", "deal_post"),
    ("deal", "ensure"): ("postcondition", "deal_ensure"),
    ("deal", "inv"):    ("invariant", "deal_inv"),
}
# match `@<pkg>.<attr>(...)` (attribute form) or `@<attr>(...)` resolved via import map.
# condition text = ast.unparse(decorator_call.args[0]) when present.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `transitions` transitions as kwargs to `Machine` | Same (list-of-dicts and list-of-lists both supported) | stable | Detector must handle both literal forms |
| `python-statemachine` `<2.0` older transition API | `>=2.0` `State()` + `src.to(dst)` event-attribute syntax; v3.x adds `StateChart` | 2.0 (2023) / 3.x | Detect `State`/`.to`/`.from_`/`|`-combine; `StateChart` is also a valid base |
| Docstring parsing via external `docstring_parser` | **stdlib internal parser (D-09)** | Phase 3 decision | No external dep; determinism owned internally |
| PEP-316 `pre:`/`post:` | Deferred PEP, never accepted | 2003 | Detect as a convention only; no library to import |

**Deprecated/outdated:**
- `py2puml` / `pyreverse` as runtime tools — replaced by internal annotation-rule logic (referenced for the rule, not used).
- `docstring_parser` library — explicitly out by D-09.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Nested `extractors/evaluations/` layout (not docs/09's flat `extractors/{name}.py`) | §Project Structure / Pitfall 7 | Import paths inconsistent; low risk — convention strongly favors nested; planner confirms |
| A2 | Native-Enum FSM (Family C) requires *both* Enum state attr *and* a transition assignment | §FSM Family C / negative case | If the rule is looser, the `Color(Enum)` negative case could false-positive; rule is designed to prevent this |
| A3 | Return-value substitution = bounded recursive AST return-propagation with visited-set | §Return-Value Substitution | Algorithm is Claude's-discretion; standard technique, low risk |
| A4 | `unresolved` marker should be a new `source_unresolved: bool` field on `GraphEdge` (Pitfall 1) | §Return-Value Substitution / Pitfall 1 | Schema mismatch must be resolved; planner picks among 3 options |
| A5 | Docstring pre/post derivation uses a fixed keyword/regex heuristic (no NLP) | §Docstring pre/post | If heuristic too aggressive, false conditions; mitigated by fixed keyword set + `source_kind="docstring"` weighting |
| A6 | SPC-04 markers live in evaluation-layer spec models, not the frozen primitive `contracts.py` | §Auxiliary Contract Markers / Pitfall 6 | Editing frozen file violates invariant #1; recommendation avoids it |
| A7 | `deal.pre`/`ensure`/`inv` names (only `deal.post` had a code example in fetched docs) | §deal | Names are the documented DbC trio; low risk but planner should confirm against deal docs when writing the matcher table |
| A8 | Dialect detection order (Sphinx → NumPy → Google) is byte-stable and unambiguous | §Docstring Dialect Parsing | A docstring mixing dialects could mis-detect; order chosen to prefer most-specific markers first |

## Open Questions

1. **`unresolved` marker placement on edges**
   - What we know: DIA-06 mandates an `unresolved=true` attribute; `GraphEdge` has no `attributes` field and is `extra="forbid"`.
   - What's unclear: whether to add `source_unresolved: bool`, use `label`, or mark the node.
   - Recommendation: add `source_unresolved: bool = False` to `GraphEdge` (SCH-02 `source_` prefix, default keeps parity). Planner confirms at DIA-06 design.

2. **`contains` EdgeKind for package containment (D-01 open sub-decision)**
   - What we know: D-01 permits adding `contains` IF node-nesting/attributes can't express package→module containment.
   - What's unclear: whether DIA-04 can represent containment purely via `GraphNode.attributes` (e.g., `attributes={"parent_package": "..."}`).
   - Recommendation: prefer attribute-based containment first (avoids EdgeKind growth); add `contains` only if a containment *edge* is genuinely required for verifier comparison. Decide at DIA-04 design.

3. **SP-2 / SP-1 spike verdicts** (gate v0.2.0 scope)
   - What we know: D-08 — ship if deterministically AST-extractable, else defer to v0.3.0.
   - What's unclear: actual verdict (run the spike).
   - Recommendation: SP-2 — `ast.If`/`ast.For`/`ast.While`/`async` map cleanly to `alt`/`loop`/`par` frames deterministically, so SP-2 looks **shippable** (confirm with fixtures in the spike). SP-1 — general control-flow → state beyond explicit FSM is far harder to make deterministic (state identity is ambiguous without an explicit state variable), so SP-1 likely **defers to v0.3.0**. Record both verdicts in `.planning/spikes/`.

## Environment Availability

> Phase 3 is pure code/config changes over stdlib + existing pinned deps. No new external tools/services.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| CPython | all extraction | ✓ | 3.11 (CI: 3.11–3.14) | — |
| stdlib `ast`/`re`/`pathlib` | all extractors | ✓ | stdlib | — |
| `pydantic` | models | ✓ | >=2.13,<3.0 | — |
| `pytest`/`pytest-cov`/`ruff` | tests/lint | ✓ | dev extras | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

`transitions`, `python-statemachine`, `icontract`, `deal` are **NOT** required to be installed — they are AST detection targets. Test fixtures contain *source strings* that *look like* code using these libraries; the extractor never imports them. (Fixtures may include the import statements as text so the provenance map matches — but the libs need not be installed to parse the fixture string.)

## Validation Architecture

> nyquist_validation is enabled (`.planning/config.json` `workflow.nyquist_validation: true`). This section lets a VALIDATION.md be derived.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8 (observed 9.0.3) + pytest-cov |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`) |
| Quick run command | `pytest tests/unit/extractors -x -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DIA-01 | class hierarchy fixture → inheritance + composition(direct type) + aggregation(Optional/list) + association(undecidable) edges | unit + golden | `pytest tests/unit/extractors/test_class_diagram.py -x` | ❌ Wave 0 |
| DIA-02 | call-graph fixture → linear sequence edges (participants ordered) | unit + golden | `pytest tests/unit/extractors/test_sequence_diagram.py -x` | ❌ Wave 0 |
| DIA-02-FULL | SP-2: `if`/`for`/`while` → alt/loop/par frames (ship-or-defer) | spike + unit | `pytest tests/unit/extractors/test_sequence_branches.py -x` (if shipped) | ❌ Wave 0 |
| DIA-03 | imports fixture → component nodes + `edge_type="imports"` edges | unit + golden | `pytest tests/unit/extractors/test_component_diagram.py -x` | ❌ Wave 0 |
| DIA-04 | multi-package fixture → `node_type="package"` nodes; containment | unit + golden | `pytest tests/unit/extractors/test_package_diagram.py -x` | ❌ Wave 0 |
| DIA-05 | 3 positive fixtures (transitions.Machine / python-statemachine / native Enum) → states+transitions; **negative `Color(Enum)` → 0 FSM** | unit | `pytest tests/unit/extractors/test_state_diagram.py -x` | ❌ Wave 0 |
| DIA-06 | `self.state=self._next()` resolved (N-level, cycle) → concrete edges; unresolvable → `unresolved` placeholder | unit | `pytest tests/unit/extractors/test_state_substitution.py -x` | ❌ Wave 0 |
| DIA-07 | every diagram output validates against `GraphModel`/`GraphNode`/`GraphEdge`/`GuardExpr`; `physical_*`/`source_*` only | unit (validation) | `pytest tests/unit/extractors -k schema -x` | ❌ Wave 0 |
| SPC-01 | Google + NumPy + Sphinx docstring fixtures → identical normalized `FunctionSpec.docstring_sections` + pre/post | unit + golden | `pytest tests/unit/extractors/test_function_spec.py -x` | ❌ Wave 0 |
| SPC-02 | class fixture → `ClassSpec(definition, members, invariants)` | unit + golden | `pytest tests/unit/extractors/test_class_spec.py -x` | ❌ Wave 0 |
| SPC-04 | icontract / deal / PEP-316 fixtures → marker entries; non-importing code → no false markers | unit | `pytest tests/unit/extractors/test_aux_markers.py -x` | ❌ Wave 0 |
| (DET-04) | each extractor sorts on exit → byte-stable across hash seeds | unit | `PYTHONHASHSEED=random pytest tests/unit/extractors -k sort` | ❌ Wave 0 |
| (dispatch) | 7 EVALUATIONS entries registered append-only; executor unchanged | unit | `pytest tests/unit/test_dispatch.py -x` | ✅ extend existing |

### Required Test Fixtures (golden / positive / negative — deterministic proof material)
- **Class diagram:** a class hierarchy with `x: Engine` (composes), `y: Optional[Engine]` / `z: list[Engine]` (aggregates), `w: SomeUnknownForwardRef` (associates), and `class B(A)` (inherits).
- **State diagram (3 positive):** (a) `Machine(states=[...], transitions=[{...}])`, (b) `class TM(StateMachine): a=State(initial=True); go=a.to(b)`, (c) native `Enum` + `self.state = Color.RED` transition method.
- **State diagram (negative):** `class Color(Enum): RED=1; GREEN=2; BLUE=3` → asserts `len(states)==0`.
- **Return-value substitution:** `self.state = self._next()` where `_next` returns `Color.A`/`Color.B` (resolved), plus a cyclic `_a→_b→_a` case (cycle-safe), plus an external-call case (`unresolved`).
- **Docstring dialects:** the *same* function documented three ways (Google/NumPy/Sphinx) → assert identical normalized output (the strongest determinism proof for SPC-01).
- **Aux markers:** fixtures importing `icontract`/`deal` + a PEP-316 `pre:`/`post:` docstring; plus a decoy `def require(...)` user function that must NOT be flagged.

### Sampling Rate
- **Per task commit:** `pytest tests/unit/extractors -x -q`
- **Per wave merge:** `pytest -q` (full suite incl. parity/acceptance)
- **Phase gate:** full suite green + golden snapshots byte-identical before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/extractors/test_class_diagram.py` — DIA-01
- [ ] `tests/unit/extractors/test_sequence_diagram.py` — DIA-02
- [ ] `tests/unit/extractors/test_component_diagram.py` — DIA-03
- [ ] `tests/unit/extractors/test_package_diagram.py` — DIA-04
- [ ] `tests/unit/extractors/test_state_diagram.py` — DIA-05 (incl. negative case)
- [ ] `tests/unit/extractors/test_state_substitution.py` — DIA-06
- [ ] `tests/unit/extractors/test_function_spec.py` — SPC-01 (3-dialect golden)
- [ ] `tests/unit/extractors/test_class_spec.py` — SPC-02
- [ ] `tests/unit/extractors/test_aux_markers.py` — SPC-04
- [ ] `tests/unit/extractors/test_diagram_schema.py` — DIA-07 (GraphModel validation, physical_* discipline)
- [ ] Acceptance: `tests/acceptance/test_dia0X_*.py` / `test_spc0X_*.py` (mirror Phase 2 `test_frNN_*` style)
- [ ] Fixtures dir: `tests/unit/extractors/fixtures/` for golden diagrams + dialect samples
- Framework install: none — pytest already present.

## Security Domain

> `.planning/config.json` has no `security_enforcement` key. Per the convention (absent = enabled) this section is included, but Phase 3 has a **minimal attack surface**: a pure in-process library with no I/O, no network, no subprocess (the pyright subprocess is Phase 2/AST-03, not used by Phase 3 evaluations), no deserialization of untrusted formats beyond `ast.parse` of caller-supplied source.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface (library) |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | No access control surface |
| V5 Input Validation | yes (light) | Caller passes `bytes`; decoded `utf-8, errors="replace"` (existing). `ast.parse` raises `SyntaxError` on malformed source — propagated, not caught (existing policy). Pydantic `extra="forbid"` validates all model construction (SCH-03). |
| V6 Cryptography | no | No crypto |

### Known Threat Patterns for {stdlib ast / pure library}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Code execution via parsing untrusted source | Elevation | `ast.parse` does NOT execute code; never `eval`/`exec`/`compile(mode="exec")`. Use `ast.literal_eval` only on `ast.Constant` (never on arbitrary nodes). The §transitions example uses `ast.literal_eval` strictly on `ast.Constant` keys/values — safe. |
| Resource exhaustion via deeply nested AST (recursion) | DoS | Return-value substitution uses a visited-set + finite method count → bounded recursion; no unbounded `ast.walk` recursion on attacker-controlled depth beyond Python's recursion limit (same risk as any AST tool — acceptable for a parser lib). |
| Non-determinism leaking environment state | Tampering (Layer M integrity) | No `os.environ`, no clock, no network, no `PYTHONHASHSEED`-dependent ordering (DET-04 sort-on-exit). This is the project's core invariant, enforced by DET-01 snapshot. |
| False contract/FSM detection from same-name symbols | Spoofing (data integrity) | Import-provenance restriction (Pattern 2) — only library-sourced names classified. |

## Sources

### Primary (HIGH confidence)
- Codebase (read first-hand): `lib_code_parser/models/evaluations/graph_base.py`, `models/primitives/*.py`, `extractors/primitives/{functions,callgraph,contracts}.py`, `frontends/python.py`, `executor.py`, `_dispatch.py`, `_paths.py`, `models/infrastructure/{cav,config,artifact}.py`, `docs/09-extending.md`, `tests/` layout.
- `c:/.../lib-diagram-parser/lib_diagram_parser/models.py` (sibling schema, read-only) — confirms plain-`str` `node_type`/`edge_type`, no `extra=forbid`.
- `.planning/{PROJECT,REQUIREMENTS,ROADMAP,STATE}.md` + `.planning/phases/0{1,2,3}-*/0N-CONTEXT.md`.

### Secondary (MEDIUM confidence — official docs, cross-verified)
- pytransitions/transitions — README + PyPI: `Machine(states=, transitions=, initial=)`, list-of-dicts + list-of-lists transition forms. https://github.com/pytransitions/transitions
- python-statemachine readthedocs — `State()`, `src.to(dst)`, `target.from_(src)`, `|`-combine, `StateChart`. https://python-statemachine.readthedocs.io/en/latest/transitions.html
- icontract readthedocs — `require`/`ensure` (lambda; `result` reserved) + `invariant` (class decorator). https://icontract.readthedocs.io/en/latest/usage.html
- deal — `@deal.post(lambda result: ...)` + "Classic DbC: precondition, postcondition, invariant". https://github.com/life4/deal
- py2puml — "composition relies on type annotations only; values never evaluated" (reference for DIA-01 rule). https://github.com/lucsorel/py2puml

### Tertiary (LOW confidence — flagged in Assumptions Log)
- PEP-316 `pre:`/`post:` docstring keyword convention (deferred PEP; detection-only regex) — A8.
- `deal.pre`/`ensure`/`inv` exact names beyond the `deal.post` code sample — A7.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new deps; all internal contracts read first-hand.
- Architecture / patterns: HIGH — directly inherits Phase 2 codebase patterns + docs/09 invariants.
- FSM / docstring / marker detection: MEDIUM-HIGH — AST shapes verified against official docs; exact API edge cases flagged in Assumptions Log.
- Pitfalls: HIGH — GraphEdge `attributes` mismatch and catch-all ban verified against actual schema/docs.

**Research date:** 2026-06-01
**Valid until:** ~2026-07-01 (stable; detection-target library APIs change slowly, internal contracts frozen by phase decisions)
