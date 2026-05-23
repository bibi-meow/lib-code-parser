# Feature Research: lib-code-parser v0.2.0

**Domain:** Code-to-diagram & code-to-spec reverse engineering (Python + C++, deterministic static analysis)
**Researched:** 2026-05-24
**Confidence:** MEDIUM-HIGH (Class/Package/Component diagrams: HIGH — well-trodden territory with pyreverse/py2puml/pydeps/clang-uml as references. Sequence diagrams: MEDIUM — static SD reverse engineering has well-known polymorphism limits in literature. FSM extraction from enum+transition: MEDIUM — pattern-based detection is feasible but no canonical OSS extractor exists. Function/class spec extraction: HIGH — Griffe/Sphinx Napoleon set the standard.)

**Scope reminder:** This is a **brownfield v0.2.0** milestone. v0.1.0 already ships AST `FunctionNode` / `CallGraph` / `TypeDep` / Pydantic v2 `ContractInfo` / Trace tags. This research covers ONLY the *new* feature space: 5 diagram extractors, function/class spec extractors, Pydantic ↔ dataclass contract refinement, and C++ parity.

---

## Feature Landscape

### Table Stakes (Must-Have for v0.2.0 to be Useful)

Without these, the lib does not deliver on the Active scope declared in PROJECT.md (§Active items B + C + D + A.§3.7 refinement). Verifiers downstream (`spec_code_verifier` US-01/US-22, `architecture_verifier` US-32) cannot do their job.

| # | Feature | Why Expected | Complexity | US | Notes |
|---|---------|--------------|------------|-----|-------|
| TS-1 | **Class diagram extraction (Python + C++)** — classes + fields + methods + inheritance + composition + aggregation edges, schema-compatible with `lib-diagram-parser` `GraphModel` (`node_type="class"`, `edge_type∈{inheritance,composition,aggregation,association,implementation}`) | Every code-to-UML tool ships this. pyreverse and py2puml prove it is the baseline. `architecture_verifier` (US-32) cannot compare a spec `classDiagram` fence to physical code without it. | MEDIUM | US-32 | Python: ast + type annotations (py2puml approach). C++: libclang `CXCursor_ClassDecl` + `CXX_BASE_SPECIFIER`. Composition vs aggregation distinction is **known-hard** even for pyreverse (see [pylint #6543](https://github.com/pylint-dev/pylint/issues/6543), [#9045](https://github.com/pylint-dev/pylint/issues/9045)) — we adopt py2puml's rule: composition = type annotation on instance attribute defined in `__init__`/constructor with owning semantics; aggregation = same but with non-owning (Optional / external) semantics. Default to `association` when undecidable (do not guess). |
| TS-2 | **Package diagram extraction (Python + C++)** — directory + namespace hierarchy as nested `node_type="component"`/`"package"` nodes, edges = inter-package import dependencies | Directory-as-package convention is universal. Required for spec `packageDiagram` (Mermaid via subgraph / PlantUML `package`) comparison. | LOW-MEDIUM | US-25, US-32 | Python: directory walk + `__init__.py` namespace resolution. C++: directory walk + `#include` chain (libclang `CXCursor_InclusionDirective`). Use pydeps / Tach / Modulegraph2 as references for granularity controls (cluster collapse, depth limit). |
| TS-3 | **Component diagram extraction (Python + C++)** — module-level boundaries + import-derived dependency edges | Standard interpretation in industry; only differs from package diagram in granularity (module ≈ file vs package ≈ directory). `lib-diagram-parser` accepts both via `diagram_type=component`. | LOW-MEDIUM | US-25, US-32 | Reuses TS-2 infrastructure with finer granularity (per-file rather than per-directory). Python: AST `import` / `ImportFrom`. C++: libclang `CXCursor_InclusionDirective`. Granularity convention: **module = file**, configurable via `params.component_granularity ∈ {"file","package"}`. Default `"file"`. |
| TS-4 | **State diagram extraction via FSM pattern detection** — detect (a) `transitions` library usage (b) `python-statemachine` library usage (c) enum-state + transition-method pattern in client code. Emit `node_type="state"` + `edge_type="transition"` + `GuardExpr(from_state, to_state, condition, action)` matching `lib-diagram-parser` schema. | The **only** must-have FSM source in this milestone (PROJECT.md §Active B.5). Without it, spec `stateDiagram-v2` fences cannot be cross-verified. State machine is a §5.1 variant in the verification catalog (bisimulation basis). | MEDIUM-HIGH | US-25, US-32 | Detection strategies (cascade): (i) **library-anchored** — find `Machine(states=..., transitions=...)` calls (`transitions`) or `StateMachine` subclasses with `State` / `transition` decorators (`python-statemachine`); (ii) **enum-anchored** — class field annotated as `StateEnum` + methods that mutate that field with literal enum values on RHS in conditional branches. Skip dynamic state assignment (e.g. `self.state = compute_next(x)`) → emit no edge rather than wrong edge (determinism wins). |
| TS-5 | **Structured function spec extraction** — `FunctionSpec { signature: ParamInfo[], returns, docstring_summary, docstring_params, docstring_returns, docstring_raises, preconditions: list[str], postconditions: list[str], invariants: list[str] }` parsed from docstring + decorators | Required by `spec_code_verifier` (US-01/US-22) for spec ↔ code semantic comparison. Griffe and Sphinx Napoleon already define the standard parse model — we follow it. | MEDIUM | US-01, US-22 | Parse Google / NumPy / Sphinx docstring styles (Griffe parser as reference). Decorator scan: `@icontract.require` → precondition, `@icontract.ensure` → postcondition, `@icontract.invariant` → invariant, `@deal.pre/post/inv` → same. Plain docstring `pre:` / `post:` keywords (PEP 316 convention) as fallback when no decorator present. Multi-style support is non-negotiable (real codebases mix). |
| TS-6 | **Structured class spec extraction** — `ClassSpec { name, bases, fields: FieldSpec[], methods: FunctionSpec[], invariants: list[str], class_docstring }` | Parallel to TS-5. `spec_code_verifier` needs the class-level view for invariant checks. | MEDIUM | US-01, US-22 | Aggregates TS-5 results per class. Class-level invariants: Pydantic `model_validator(mode="after")`, dataclass `__post_init__` assertion bodies, `@icontract.invariant`, plain docstring `inv:` keyword. |
| TS-7 | **Pydantic ↔ dataclass contract differentiation (§3.7 refinement)** — split the currently-lumped `ContractInfo` into `PydanticContract` and `DataclassContract` subtypes, each tagged with its origin pattern | PROJECT.md §Active A.1 explicitly calls this out. v0.1.0 treats both as same shape, losing the distinction `spec_code_verifier` needs (Pydantic enforces at construction; dataclass `__post_init__` only at `__init__` time — different runtime semantics → different verifier behavior). | LOW-MEDIUM | US-01, US-22 | Schema change: `ContractInfo.kind: Literal["pydantic_v2","dataclass_post_init","icontract","deal","docstring_pep316"]`. Detection: `@field_validator` / `@model_validator` → `pydantic_v2`; `def __post_init__` inside `@dataclass` → `dataclass_post_init`. Backward compat: keep `ContractInfo` shape additive (new `kind` field with `pydantic_v2` as default to preserve v0.1.0 behavior). |
| TS-8 | **C++ language coverage for TS-1, TS-2, TS-3, TS-5, TS-6** — same extractors work on C++ source via libclang | PROJECT.md §Constraints: "Python と C++ を最初から対象". `clang-uml` and `hpp2plantuml` prove libclang-based C++ class extraction is well-trodden. | HIGH | US-25, US-32, US-01, US-22 | libclang (`clang.cindex`) cursor walking. Doxygen-style `\param` / `\return` / `\pre` / `\post` / `\invariant` for spec extraction (analogous to Sphinx/Google docstrings in Python). Template handling is the hardest part — emit instantiation skeleton, not all template specializations. |
| TS-9 | **ACL-2 integration: `callgraph.py` subprocess for Python deterministic call graph** | PROJECT.md §Active A.2. Replaces v0.1.0's home-rolled AST call edges with a more accurate decoupled tool. | LOW | US-32 | Subprocess wrap, parse output, fold into `CallGraph` schema. No semantic change for consumers, just better accuracy. |
| TS-10 | **ACL-2 integration: `pyright` subprocess for type-resolved Python `TypeDep`** | PROJECT.md §Active A.3. v0.1.0 `TypeDep` is from raw annotations without resolution; pyright resolves cross-module types. | LOW-MEDIUM | US-01, US-22 | Subprocess `pyright --outputjson` and fold. Determinism property holds (same input → same output). |
| TS-11 | **Schema compatibility layer with `lib-diagram-parser`** — every diagram extractor returns `DiagramRef` containing `GraphModel` (nodes/edges/guards) with `diagram_id`, `diagram_type`, `source_format="code"`, `raw_source=<file_path_or_excerpt>`. Add optional physical-side metadata fields (e.g. `source_range`, `qualified_name`) on `attributes` dict. | This is the **Core Value** of the milestone (PROJECT.md §Core Value): both sides comparable in same form. If schema drifts the entire verification pipeline fails. | LOW | US-32 | Schema fields are already specified in `lib-diagram-parser` README. The lib must import or mirror the `GraphModel`/`GraphNode`/`GraphEdge`/`GuardExpr` types (no parallel redefinition — drift risk). Physical metadata via existing `attributes: dict` (optional fields) to avoid breaking spec-side consumers. |

### Differentiators (Nice-to-Have for v0.2.0)

Add competitive value but not required to ship a useful v0.2.0. Defer cleanly if scope tightens.

| # | Feature | Value Proposition | Complexity | US | Notes |
|---|---------|-------------------|------------|-----|-------|
| DF-1 | **Sequence diagram extraction with branch fidelity** — emit `alt` / `loop` / `par` frames around call-site groups when control flow is statically resolvable, otherwise emit linear call sequence | Industry static SD extractors (pyan, code2flow) emit linear-only; branch fidelity is rare. For spec ↔ code SD comparison, branch markers materially help the verifier disambiguate. | HIGH | US-32 | Use CFG (control flow graph) per function, detect if/while around CallExpr, emit `GraphEdge` with `attributes={"frame":"alt","branch_condition":"..."}`. **Known limitation (literature consensus):** polymorphism + dynamic dispatch make static SDs strictly under-approximate. Document this clearly and emit a `confidence` field per edge. |
| DF-2 | **Package diagram with layered-architecture inference** — detect layer violations (lower-level imports higher-level) and emit them as `attributes={"violation":"layer_inversion"}` edges; infer layer order from directory depth or `layers.yml` config | Layer-linter / Tach do this for Python but not in a graph-extraction lib. Including it gives `architecture_verifier` a richer signal. | MEDIUM | US-25, US-32 | Optional `params.layer_config: dict | None` for explicit layer rules. Without config, attempt heuristic ordering (alphabetical / depth). **Heuristic mode** is a confidence-reducing fallback — emit `attributes={"inferred":true}` so verifier knows. |
| DF-3 | **State diagram spike: general control-flow → state extraction** — detect cases where state is held in a non-enum field (string literal, integer code) with conditional mutation | PROJECT.md §Active B.6 marks this as **spike**. If a decision rule can be made deterministic, expand FSM coverage to legacy codebases that pre-date `transitions`. | HIGH (spike) | US-25 | **Spike protocol**: write detection rule → run on 5–10 reference codebases → measure false-positive rate → if FPR ≤ 10% promote to differentiator, else **drop and document** (per PROJECT.md §Out of Scope item 5). Determinism is the gate. Cannot ship if rule produces nondeterministic edges. |
| DF-4 | **Cross-language call graph stitching for FFI boundaries (Python `ctypes`, `pybind11`, `cffi` → C++ functions)** | Hybrid Python+C++ codebases (common in scientific / embedded) gain trace continuity. Not in PROJECT.md but a natural extension for the C++ milestone. | HIGH | US-32 | Defer to v0.3.0 unless an actual consumer asks. Listed here for visibility; **recommend defer**. |
| DF-5 | **Cyclomatic complexity / fan-in / fan-out metadata on `FunctionNode`** | Verifier can use complexity to weight comparison confidence. Cheap to compute once we have AST. | LOW | US-32 | Add to `FunctionNode.attributes` as optional fields. Not in PROJECT.md scope but trivially cheap if AST traversal infrastructure is in place. |
| DF-6 | **Doxygen comment parsing for C++ contracts** (`\pre`, `\post`, `\invariant`) — mirrors TS-5 docstring contracts for Python | C++ contracts are typically in Doxygen blocks since the language lacks first-class decorators. Required for true Python ↔ C++ parity on TS-5/TS-6. | MEDIUM | US-01, US-22 | Listed as differentiator because Python TS-5/TS-6 cover the primary use case; C++ contract extraction is needed for full parity but can ship in patch release. **Recommend promoting to TS** if C++ is a first-class target (it is, per Constraints) — see Open Question O-1. |

### Anti-Features (Deliberately NOT Built — match PROJECT.md §Out of Scope)

These map to PROJECT.md §Out of Scope verbatim and are listed here so future contributors know the deliberate reasoning, not just the prohibition.

| # | Feature | Why Tempting | Why Anti-Feature | Alternative |
|---|---------|--------------|------------------|-------------|
| AF-1 | **LLM-based interpretation of physical ↔ logical gap** (e.g. "are these two class diagrams 'the same' even with renaming?") | LLMs naturally handle representation-gap fuzziness. Tempting to bake in. | Breaks the Core Value: this lib is the *deterministic* base for Layer M bisimulation. LLM interpretation belongs in `spec_code_verifier` (verifier layer), not the parser. Mixing collapses the architectural boundary. | Verifier consumes our deterministic output + spec output and applies LLM interpretation downstream. |
| AF-2 | **Dynamic analysis / runtime tracing** (instrumenting code to record actual call sequences) | Dynamic traces solve polymorphism — strictly more accurate sequence diagrams. | (a) Violates determinism (different inputs → different traces); (b) Requires executable environment, breaking the `(raw_content, path, config)` pure-function I/O policy; (c) Out of spec scope. | Static extraction with confidence annotations (see DF-1). |
| AF-3 | **Natural-language spec generation** (synthesizing English prose specs from code) | Tempting for documentation gen tools. | Verifier doesn't need prose — it compares structured `FunctionSpec` ↔ structured spec-side data. Adding prose synthesis adds an LLM dependency we don't need. | Structured `FunctionSpec` / `ClassSpec` (TS-5, TS-6) suffice. |
| AF-4 | **OAS / OpenAPI / IDL forward-generation from code** | Some teams want code-first API spec generation. | This lib does *reverse* engineering (code → structured data for verification). Forward generation is a separate concern with its own ecosystem (e.g. FastAPI auto-gen). | Use a dedicated forward-gen tool downstream; consume our `FunctionSpec` if you want the AST-level signature data. |
| AF-5 | **CrossHair symbolic execution integration** | spec mentions it as "possible" — tempting to integrate now. | Out of milestone Core Value. Adds dependency surface (CrossHair) and complicates determinism (CrossHair has its own time/randomness considerations). | Defer to a future milestone with explicit demand. v0.2.0 emits `ContractInfo` in a form CrossHair *could* consume externally. |
| AF-6 | **Test-code parsing** (e.g. extracting pytest fixtures, parameterize markers) | Tests are code, so it seems in-scope. | PROJECT.md §Out of Scope item 7: this is `lib-test-parser` territory. Mixing tests + product code blurs verifier responsibilities (spec ↔ product vs spec ↔ test are different US). | Use `lib-test-parser` (separate lib). |
| AF-7 | **General CFG → state diagram extraction (without enum anchor)** | Promised by some legacy reverse-engineering tools. | PROJECT.md §Out of Scope item 5: deterministic rule construction is the gate. If DF-3 spike fails, this lands here. | Document as "verifier should not assume state diagrams for non-FSM-pattern code". |
| AF-8 | **pip package splitting** (separate `code-parser-python`, `code-parser-cpp`) | Avoids users pulling in libclang for Python-only use. | PROJECT.md §Out of Scope item 6: premature. Internal module separation suffices for v0.2.0. | v0.3.0+ if real distribution pain emerges. |

### Spike Candidates

Items requiring proof-of-concept before commitment.

| # | Spike | Question | Success Criteria | Failure Path |
|---|-------|----------|------------------|--------------|
| SP-1 | **General control-flow → state diagram rule construction** (= DF-3) | Can we construct a deterministic rule that detects "this code is a state machine" from non-enum patterns without producing wrong edges? | (a) Rule produces zero edges on a corpus of 10 non-FSM code samples (false-positive rate = 0); (b) Rule produces correct edges on ≥ 7/10 known-FSM samples (sensitivity ≥ 70%); (c) Output is reproducible across runs. | Drop feature, document in PROJECT.md §Out of Scope (it's already there as a defer condition). Verifier informed that only enum-anchored FSMs are supported. |
| SP-2 | **Branch-frame fidelity in sequence diagrams** (= DF-1) | Can `alt`/`loop` frames be emitted deterministically from CFG without exploding edge count on complex functions? | (a) ≤ 3 frame edges per CallExpr on a corpus of 50 real-world functions; (b) Output deterministic; (c) Verifier downstream can consume frames meaningfully. | Ship linear-only sequence diagrams (matches pyan/code2flow baseline). DF-1 becomes "linear sequence diagram extraction" without frames — drops to TS or trivial differentiator. |
| SP-3 | **libclang determinism on incomplete C++ translation units** | libclang behavior on headers without full `compile_commands.json` — does it produce stable output? | Same input header → identical AST cursor traversal output across 3 successive runs in a clean env. | Require `compile_commands.json` as input (degrades UX but preserves determinism). Document as a TS-8 constraint. |

---

## Feature Dependencies

```
TS-11 (schema compat layer)
    └──required by──> TS-1 (class diagram)
                      TS-2 (package diagram)
                      TS-3 (component diagram)
                      TS-4 (state diagram)
                      DF-1 (sequence diagram with branches)
                      DF-2 (layer inference)

TS-1 (class diagram, Python+C++)
    └──reuses──> AST primitives (v0.1.0 FunctionNode infra) — already shipped
    └──reuses──> TS-10 (pyright type resolution) — for accurate type-based edge detection

TS-3 (component) ──extends──> TS-2 (package)  [same import-graph backbone, finer granularity]

TS-4 (state diagram)
    └──independent of── other diagrams, but shares schema layer (TS-11)
    └──optional dependency──> SP-1 (control-flow spike) for DF-3 expansion

TS-5 (function spec) ──aggregated by──> TS-6 (class spec)
TS-5 ──refines──> TS-7 (Pydantic/dataclass split sits inside ContractInfo, surfaced via FunctionSpec)

TS-8 (C++ coverage) ──parallel implementation of──> TS-1, TS-2, TS-3, TS-5, TS-6
    └──prerequisite──> SP-3 (libclang determinism)
    └──optional companion──> DF-6 (Doxygen contracts) for Python parity

TS-9 (callgraph.py) + TS-10 (pyright) ──independent of── diagram extractors,
    but TS-9 improves CallGraph used as input by DF-1 (sequence diagram fidelity)

DF-1 (sequence with branches) ──depends on──> SP-2 (CFG branch detection spike)
DF-3 (general CFG → state) ──depends on──> SP-1 (rule construction spike)
```

### Dependency Notes

- **TS-11 schema compat is the keystone** — every diagram extractor (TS-1 to TS-4, DF-1 to DF-3) writes to this schema. Lock it before parallel diagram implementation begins (matches `.claude/rules/parallel-contract-first.md`).
- **TS-8 (C++) parallelizes with Python implementations of TS-1/TS-2/TS-3/TS-5/TS-6** — once the schema (TS-11) is locked, Python and C++ tracks can proceed concurrently. They share extractor *interfaces*, not implementation.
- **TS-9/TS-10 (ACL-2 tools) gate accuracy improvements but not feature availability** — extractors can be built on v0.1.0 home-rolled call graph and degraded `TypeDep`; pyright/callgraph.py refine the results. Treat as accuracy upgrade, not blocking.
- **TS-7 (Pydantic/dataclass split) is small and unblocks `spec_code_verifier`'s downstream contract differentiation** — sequence it early so verifier work doesn't wait.
- **SP-1 must run before committing to DF-3**, SP-2 before DF-1 fidelity work, SP-3 before declaring TS-8 done. Spike failure = scope reduction without milestone derailment.

---

## MVP Definition

### Launch With (v0.2.0 — Table Stakes Only)

Minimum viable v0.2.0. Validates the Core Value: parser output is comparable to spec output (Layer M bisimulation works end-to-end).

- [ ] **TS-11** — Schema compatibility layer with `lib-diagram-parser` *(keystone, lock first)*
- [ ] **TS-1** — Class diagram extraction (Python + C++)
- [ ] **TS-2** — Package diagram extraction (Python + C++)
- [ ] **TS-3** — Component diagram extraction (Python + C++)
- [ ] **TS-4** — State diagram via FSM pattern detection (Python; C++ in same milestone if libclang time permits, otherwise deferred to v0.2.1)
- [ ] **TS-5** — Structured function spec extraction (Python with all 3 docstring styles + icontract + deal + PEP-316; C++ with Doxygen if DF-6 promoted)
- [ ] **TS-6** — Structured class spec extraction (Python + C++)
- [ ] **TS-7** — Pydantic/dataclass contract differentiation
- [ ] **TS-8** — C++ language coverage for TS-1/2/3/5/6 (linear sequence diagram for C++ deferred to v0.2.1 if needed)
- [ ] **TS-9** — `callgraph.py` ACL-2 integration
- [ ] **TS-10** — `pyright` ACL-2 integration
- [ ] **Linear sequence diagram extraction (Python)** — stripped-down DF-1 without branch frames; needed for US-32 SD comparison even at low fidelity

### Add After v0.2.0 Validation (v0.2.x patch releases)

Once Core Value is validated by `spec_code_verifier` + `architecture_verifier` consumption.

- [ ] **DF-1 with branch frames** — only if SP-2 spike succeeds and verifier feedback shows linear is insufficient
- [ ] **DF-2** — layered-architecture inference (cheap add once TS-2 is solid)
- [ ] **DF-5** — complexity / fan-in / fan-out metadata (trivial)
- [ ] **DF-6** — Doxygen contract parsing for C++ (if not already promoted to TS-5)

### Future Consideration (v0.3.0+)

Deferred until real demand or upstream prerequisite shifts.

- [ ] **DF-3** — general CFG → state diagram (only if SP-1 spike succeeds)
- [ ] **DF-4** — cross-language call graph stitching (FFI)
- [ ] **pip package splitting** — only if libclang dependency pain reported by Python-only users
- [ ] **CrossHair symbolic execution integration** — only if symbolic verification becomes a verifier requirement

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|-----------|---------------------|----------|
| TS-11 Schema compat layer | HIGH (keystone — nothing works without it) | LOW | **P1** |
| TS-1 Class diagram | HIGH (US-32 direct) | MEDIUM | **P1** |
| TS-2 Package diagram | HIGH (US-25, US-32) | LOW-MEDIUM | **P1** |
| TS-3 Component diagram | HIGH (US-25, US-32) | LOW-MEDIUM | **P1** |
| TS-4 State diagram (FSM) | HIGH (US-25, US-32; only must-have FSM source) | MEDIUM-HIGH | **P1** |
| TS-5 Function spec | HIGH (US-01, US-22 direct) | MEDIUM | **P1** |
| TS-6 Class spec | HIGH (US-01, US-22 direct) | MEDIUM | **P1** |
| TS-7 Pydantic/dataclass split | MEDIUM (refines existing v0.1.0 capability) | LOW-MEDIUM | **P1** |
| TS-8 C++ coverage | HIGH (Constraints: Python+C++ from start) | HIGH | **P1** |
| TS-9 callgraph.py integration | MEDIUM (accuracy upgrade) | LOW | **P1** |
| TS-10 pyright integration | MEDIUM-HIGH (type-resolved TypeDep) | LOW-MEDIUM | **P1** |
| Linear sequence diagram (Python) | MEDIUM-HIGH (US-32 SD comparison baseline) | MEDIUM | **P1** |
| DF-1 SD with branch frames | MEDIUM (improves verifier confidence) | HIGH | **P2** (gated by SP-2) |
| DF-2 Layer inference | MEDIUM | MEDIUM | **P2** |
| DF-6 Doxygen contracts (C++) | MEDIUM-HIGH (C++ TS-5 parity) | MEDIUM | **P1.5** (recommend promote — see O-1) |
| DF-3 General CFG → state | LOW (spike-dependent) | HIGH | **P3** (gated by SP-1) |
| DF-4 FFI call graph | LOW (no current consumer) | HIGH | **P3** |
| DF-5 Complexity metadata | LOW | LOW | **P2** |

**Priority key:**
- **P1:** Must have for v0.2.0 launch (Table Stakes)
- **P1.5:** Recommended promotion from P2 to P1 — flagged for decision
- **P2:** Should have, ship in v0.2.x patch
- **P3:** Nice to have or spike-gated, v0.3.0+

---

## Competitor / Reference Tool Analysis

| Feature | pyreverse (pylint) | py2puml | pydeps / Tach | clang-uml (C++) | Our Approach |
|---------|--------------------|---------|----|-----------------|-------|
| Class diagram (Python) | YES — inheritance + composition (imperfect) + aggregation (imperfect) | YES — type-annotation driven, composition focus | N/A | N/A | Combine: type annotations (py2puml) for high-precision composition + AST `__init__` walk (pyreverse) for fallback. Conservative on aggregation (default `association` when unclear). |
| Class diagram (C++) | N/A | N/A | N/A | YES — libclang based, mature | Adopt clang-uml's approach (libclang cursor walking, inheritance via `CX_CXXBaseSpecifier`, composition via member type analysis). Do *not* depend on clang-uml as a subprocess; reimplement on `clang.cindex` to keep determinism + dependency surface controlled. |
| Sequence diagram | NO | NO | N/A | YES (linear from call graph) | Linear SD from `CallGraph` for v0.2.0. Branch frames as DF-1 spike. Document polymorphism limitation explicitly (literature consensus: static SD is under-approximate). |
| Component / Package diagram | YES (packages) | NO | YES (pydeps strongest) | YES | Reuse pydeps-style approach (import graph + cluster controls) but emit `lib-diagram-parser` schema instead of dot/svg. Granularity: file = component, dir = package. |
| State diagram | NO | NO | NO | NO (basic) | **No standard OSS extractor exists** — we ship this as a differentiator. Pattern-based detection (library-anchored + enum-anchored) for must-have; CFG-based as spike. |
| Function/class spec (signature + structured docstring) | Partial (signatures only, no docstring parse) | Partial (signatures + type hints, no docstring parse) | N/A | N/A | Follow **Griffe** (mkdocstrings) and **Sphinx Napoleon** parser model for Google/NumPy/Sphinx docstring styles. Add contract extraction via decorator scan + PEP-316 docstring keywords. |
| Contract differentiation (Pydantic vs dataclass) | NO | NO | NO | N/A | Explicit `ContractInfo.kind` tag — novel value-add. |
| Deterministic output | YES (pyreverse via Graphviz dot) | YES | YES | YES | YES — pure function `(raw_content, path, config) → NormalizedArtifact`. No I/O, no LLM, no clock. |

**Strategic positioning:** Existing tools focus on visualization (graph image output for human reading). Our lib focuses on **structured data emission for downstream programmatic verification**. Same extraction backbone, different output target. This is the value-add gap.

---

## Open Questions

- **O-1 (decision needed pre-milestone):** Should **DF-6 (Doxygen contracts for C++)** be promoted to Table Stakes? Constraints declare "Python と C++ を最初から対象", and TS-5/TS-6 (function/class spec) are TS. C++ contracts without Doxygen parsing means Python and C++ spec extraction are unequal in fidelity. **Recommendation: promote to TS** — keeps Python/C++ symmetry, low marginal cost (Doxygen comment regex parsing is well-known). Flagged here for orchestrator's roadmap decision.
- **O-2:** Granularity convention for `node_type` in `lib-diagram-parser` — does it distinguish `"component"` vs `"package"`, or treat them as same `node_type` with `attributes`? Sibling lib README shows `"component"` only. **Recommend:** add `"package"` as a new `node_type` in `lib-diagram-parser` (small contract change to sibling lib) OR treat both as `"component"` with `attributes={"granularity":"file"|"package"}`. Decide before TS-2/TS-3 implementation.
- **O-3:** For TS-4 state diagram, when an enum-state class has a method that mutates state via a non-literal expression (e.g. `self.state = self._compute_next()`), do we (a) skip silently, (b) emit a placeholder edge with `attributes={"unresolved":true}`, or (c) raise? **Recommend (a) skip silently** with diagnostic logged through an out-of-band channel (caller's responsibility) — preserves determinism and avoids false edges.

---

## Sources

- [Pyreverse — pylint docs (4.1.0-dev0)](https://pylint.readthedocs.io/en/latest/additional_tools/pyreverse/index.html)
- [py2puml on PyPI](https://pypi.org/project/py2puml/) — type-annotation-driven composition detection
- [py2puml GitHub](https://github.com/lucsorel/py2puml)
- [pyreverse composition/aggregation arrow issues — pylint #9045](https://github.com/pylint-dev/pylint/issues/9045)
- [pyreverse aggregation vs composition — pylint #6543](https://github.com/pylint-dev/pylint/issues/6543)
- [pyan static call graph generator (Technologicat fork)](https://github.com/Technologicat/pyan)
- [code2flow on PyPI](https://pypi.org/project/code2flow/) — pretty-good call graphs for dynamic languages; AST-only limitations documented
- [pydeps — Python module dependency graphs](https://github.com/thebjorn/pydeps)
- [Modulegraph2 docs](https://modulegraph2.readthedocs.io/)
- [layer-linter on PyPI](https://pypi.org/project/layer-linter/) — layered architecture validation
- [Tach: dependency graph visualization for Python](https://www.gauge.sh/blog/how-to-visualize-your-python-projects-dependency-graph)
- [pytransitions/transitions](https://github.com/pytransitions/transitions) — `model_override` for static-analysis-friendly state machines
- [python-statemachine docs](https://python-statemachine.readthedocs.io/) — declarative statecharts with `State` + `transition` decorators
- [common-fsm on PyPI](https://pypi.org/project/common-fsm/) — enum-based FSM reference
- [clang.cindex docs (libclang 16.0.6)](https://libclang.readthedocs.io/en/latest/_modules/clang/cindex.html)
- [clang-uml — Customizable UML diagram generator for C++ based on Clang](https://github.com/bkryza/clang-uml)
- [hpp2plantuml](https://github.com/thibaultmarin/hpp2plantuml) — C++ header → PlantUML
- [Parsing C++ in Python with Clang (Eli Bendersky)](https://eli.thegreenplace.net/2011/07/03/parsing-c-in-python-with-clang)
- [Griffe docstring parsers](https://mkdocstrings.github.io/griffe/reference/docstrings/) — Google/NumPy/Sphinx parser models
- [Sphinx Napoleon extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
- [PEP 316 — Programming by Contract for Python](https://peps.python.org/pep-0316/) — `pre:`/`post:` docstring keyword convention
- [icontract on GitHub](https://github.com/Parquery/icontract) — `@require`/`@ensure`/`@invariant` decorators
- [CrossHair: Kinds of Contracts](https://crosshair.readthedocs.io/en/latest/kinds_of_contracts.html) — supports icontract + deal + PEP-316
- [Reverse-engineering of UML Sequence Diagrams from Execution Traces (research)](https://www.researchgate.net/publication/46047751_Reverse-engineering_of_UML_20_Sequence_Diagrams_from_Execution_Traces) — static SD limitations under polymorphism (literature consensus)
- [Static generation of UML sequence diagrams (Springer)](https://link.springer.com/article/10.1007/s10009-019-00545-z)
- [PlantUML Class Diagram syntax](https://plantuml.com/class-diagram) — schema reference

---

*Feature research for: lib-code-parser v0.2.0 (brownfield milestone — diagram extractors + spec extractors + C++ + contract refinement)*
*Researched: 2026-05-24*
