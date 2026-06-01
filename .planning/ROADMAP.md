# Roadmap: lib-code-parser v0.2.0

## Overview

lib-code-parser v0.2.0 extends the shipped v0.1.0 AST baseline (commit `cf7e7ec`) into a full multi-language reverse-engineering library that emits deterministic, schema-compatible structured artifacts (AST primitives + 5 diagram kinds + function/class specs) for both Python and C++ source. The journey is architecture-first per user direction (アーキ重視): Phase 1 locks every cross-cutting contract (CAV envelope, EdgeKind enum, schema compat boundary, subprocess determinism rules, dispatch table, license, spec doc fix) before any extractor code is written — eliminating the six highest-recovery-cost pitfalls (CAV lock, EdgeKind ad-hoc growth, schema drift, line-ending/Unicode normalization, sort-on-exit invariant, spec misidentification of ACL-2/callgraph.py) before they can occur. Phases 2 and 3 build the Python track (frontend → aspect extractors → ACL-2 adapters → diagram + spec extractors) on top of the locked CAV. Phase 4 brings up the C++ track via `libclang==18.1.1` (gated by the SP-3 spike for macOS arm64 + Python 3.13+ feasibility) and produces output with full schema parity to Python. Phase 5 closes with cross-cutting integration: byte-identical determinism snapshot, cross-lib schema compat test against `lib-diagram-parser`, full platform CI matrix, README compatibility matrix, and Apache-2.0 release artifacts. Every v1 requirement maps to exactly one phase; spikes SP-1 (general control-flow → state diagram), SP-2 (sequence diagram branch fidelity), SP-3 (libclang on macOS arm64 + Python 3.13+) run inside their gating phases as the first plan deliverable.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Architecture Foundation + Spec Correction** - Lock every cross-cutting contract (CAV, EdgeKind, schema compat layer, subprocess determinism, dispatch table, ACL-2/callgraph.py spec fix, Apache-2.0 license) before any extractor code is written; SP-3 libclang feasibility spike
 (completed 2026-05-25)
- [x] **Phase 2: Python Frontend + AST Primitives + ACL-2 Adapters** - Build the Python Frontend (one parse per file producing CAV), the four pure-CAV aspect extractors (functions / call graph / type deps / contracts) and the `pyright` subprocess adapter with full canonicalization
 (completed 2026-05-31)
- [ ] **Phase 3: Python Diagram + Spec Extractors** - Emit five `lib-diagram-parser`-compatible diagrams (class / sequence / component / package / state) and function/class spec extractors from Python source; SP-1 (general control flow → state) and SP-2 (sequence branch fidelity) spikes
- [ ] **Phase 4: C++ Frontend + C++ Extractors** - Bring up libclang-based C++ Frontend behind the locked CAV boundary, produce schema-parity output for AST primitives, diagrams, and Doxygen-driven specs; platform matrix incl. macOS arm64 best-effort
- [ ] **Phase 5: Cross-Cutting Integration + Acceptance** - Snapshot determinism test, cross-lib schema compatibility test against `lib-diagram-parser`, full CI mandatory + best-effort matrices, README platform compat table, v0.2.0 release

## Phase Details

### Phase 1: Architecture Foundation + Spec Correction
**Goal**: Lock every cross-cutting contract (CAV envelope, EdgeKind taxonomy, schema-compat boundary with `lib-diagram-parser`, subprocess determinism rules, explicit dispatch table, typed `ParserConfig`, `_paths.py` shared helper, Apache-2.0 license declaration) and correct the spec doc (`lib-code-parser.md` — remove `callgraph.py` and "ACL-2" misreferences) before any extractor code is written, so that every extractor in Phases 2–4 builds against immutable contracts and the six highest-recovery-cost pitfalls (CAV lock, EdgeKind ad-hoc growth, schema drift, line-ending/Unicode normalization, sort-on-exit invariant, spec misidentification) cannot occur. Also run SP-3 spike (libclang `==18.1.1` runtime on macOS arm64 + Python 3.13/3.14) to feed Phase 4 risk profile.
**Depends on**: Nothing (first phase)
**Requirements**: ARC-01, ARC-02, ARC-03, ARC-04, ARC-05, SCH-01, SCH-02, SCH-03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01
**Success Criteria** (what must be TRUE):
  1. Caller can import `from lib_code_parser.models import CAV, EdgeKind, GraphNode, GraphEdge, GraphModel, ParserConfig` and every model is a Pydantic v2 `BaseModel` with `model_config = ConfigDict(extra="forbid")`; `EdgeKind` enum is a closed `Literal` (no "uses"/"other"/"misc" catch-alls) covering `inherits / implements / field_of / param_of / returns / calls / instantiates / composes / aggregates / associates / transitions_to`
  2. Caller can construct `ParserConfig(language="python", extract_contracts=True, compile_args=["-std=c++17"], python_version="3.12")` with typed fields (no untyped `params: dict[str, object]` survives) and Pydantic raises `ValidationError` on unknown fields
  3. `lib_code_parser/_dispatch.py` exists with explicit static `FRONTENDS` and `EXTRACTORS` dispatch dicts and `lib_code_parser/_paths.py:get_module_name()` is the single source of truth (no `_get_module_name` duplication anywhere in the codebase) — verifiable by `grep -r "_get_module_name" lib_code_parser/` returning only `_paths.py`
  4. `lib_code_parser/adapters/base.py` defines the subprocess hardening contract (`encoding="utf-8"`, `errors="replace"`, `env={...,"LC_ALL":"C","PYTHONHASHSEED":"0"}`, explicit `timeout`, explicit `cwd`, `capture_output=True`, `shell=False`) and ships an enforcement helper used by every subsequent adapter
  5. `lib-code-parser.md` spec doc no longer mentions `callgraph.py` or "ACL-2" (replaced by the internal call graph extractor description + `pyright` for type resolution); `pyproject.toml` declares `license = "Apache-2.0"` with `LICENSE` file shipped and `README.md` includes a "No GPL bundled" license summary (call graph internal, pyright MIT, libclang Apache-2.0 with LLVM exception); SP-3 libclang feasibility spike result is recorded (verdict: ship / ship-best-effort / defer) under `.planning/spikes/SP-3-libclang-macos-arm64.md`
**Plans**: 10 plans across 3 waves
  - Wave 1 (8 parallel plans):
    - [x] 01-01-license-and-pyproject-PLAN.md — Apache-2.0 LICENSE + pyproject PEP 639 SPDX (DOC-04, DOC-03)
    - [x] 01-02-spec-doc-rewrite-PLAN.md — Full rewrite of lib-code-parser.md removing callgraph.py / ACL-2 (DOC-01, DOC-03)
    - [x] 01-03-models-infrastructure-PLAN.md — CAV + NormalizedArtifact[TContent] + typed ParserConfig (SCH-02, ARC-05, ARC-02)
    - [x] 01-04-models-primitives-PLAN.md — FunctionNode/CallGraph/TypeDep/ContractInfo + source_kind discriminator (SCH-02)
    - [x] 01-05-models-evaluations-PLAN.md — EdgeKind closed Literal (11 values) + GraphNode/Edge/Model/GuardExpr (SCH-01, SCH-03, SCH-02)
    - [x] 01-06-paths-and-dispatch-PLAN.md — _paths.py + _dispatch.py (ARC-04, DET-04)
    - [x] 01-07-adapters-base-PLAN.md — adapters/base.py subprocess hardening helper + ABC (ARC-03, DET-05)
    - [x] 01-08-docs-common-view-and-extending-PLAN.md — docs/08 + docs/09 (6 Open-Closed invariants) (ARC-04, DET-04 substrate)
  - Wave 2 (depends on Wave 1):
    - [x] 01-09-layout-migration-and-parity-PLAN.md — Lib __init__ rewrite + extractor shims + parity test (ARC-01, ARC-04, DET-04 finalizers)
  - Wave 3 (depends on Wave 2):
    - [x] 01-10-sp3-spike-and-trace-matrix-PLAN.md — CI sp3-libclang-spike job + spike doc + docs/99-trace-matrix.md (TRC-01 + ROADMAP SC-5 SP-3 closure per D-22)

### Phase 2: Python Frontend + AST Primitives + ACL-2 Adapters
**Goal**: Implement the Python Frontend that parses a source file exactly once and emits the immutable Common AST View (CAV), then build the four pure-CAV aspect extractors (functions / internal call graph / type deps / contracts with Pydantic-validator vs. `__post_init__` discrimination) and the single `pyright[nodejs]==1.1.409` subprocess adapter living in `adapters/`. This phase delivers everything needed to produce v0.1.0-equivalent `NormalizedArtifact` for Python source from the new locked architecture (so v0.1.0 callers see no regression) plus pyright-resolved `TypeDep` and explicit Pydantic/dataclass contract discrimination.
**Depends on**: Phase 1
**Requirements**: AST-01, AST-02, AST-03, AST-04, AST-05, DET-03, TRC-02, TRC-03
**Success Criteria** (what must be TRUE):
  1. Caller calling `CodeParserExecutor().execute(config, raw_content, path)` on the v0.1.0 baseline Python fixtures gets `NormalizedArtifact.content.functions` containing `FunctionNode` entries with `kind`, `params`, `return_type`, `docstring`, `trace_tags`, `source_range` populated and a single `ast.parse()` happens per file (instrumentable via mock — replaces v0.1.0 4× re-parse anti-pattern)
  2. Caller gets `CodeContent.callgraph` populated by the internal extractor (no GPL deps, no external subprocess) with caller→callee edges sorted lexicographically by `(caller, callee)` and `CodeContent.type_deps` populated by the `pyright` adapter that canonicalizes the JSON (paths normalized to forward-slash, lists sorted by composite keys, no timestamps) and pins pyright to `1.1.409` via `PYRIGHT_PYTHON_FORCE_VERSION`
  3. Caller can distinguish `ContractInfo.source_kind ∈ {"pydantic_validator", "pydantic_model_validator", "pydantic_field_validator", "dataclass_post_init"}` per validator, so the verifier no longer sees `__post_init__` unconditionally tagged as a Pydantic concept
  4. Every extractor module (`ast_extractor`, `callgraph_builder`, `type_dep_builder`, `contract_extractor`) is importable and callable in isolation (`from lib_code_parser.extractors.functions import extract_functions; extract_functions(cav, config)` works without going through `CodeParserExecutor`) and each module's docstring declares which REQ-IDs it implements; `Traces: REQ-ID, US-NN` regex still extracts the same tags as v0.1.0 (parity test against shipped fixtures)
**Plans**: TBD

### Phase 3: Python Diagram + Spec Extractors
**Goal**: Build the five `lib-diagram-parser`-compatible diagram extractors (class / sequence / component / package / state) and the two Python spec extractors (function spec from signature + Google/NumPy/Sphinx docstring + pre/post conditions; class spec with members + invariants) on top of the Phase 2 CAV + aspect models. Includes the spike work that decides the v0.2.0 vs v0.3.0 line for sequence branch fidelity (SP-2) and general control-flow → state extraction (SP-1). Also covers the `lib-diagram-parser` sibling-lib PR to add `node_type="package"` enum value (DIA-04 dependency).
**Depends on**: Phase 2
**Requirements**: DIA-01, DIA-02, DIA-03, DIA-04, DIA-05, DIA-06, DIA-07, SPC-01, SPC-02, SPC-04
**Success Criteria** (what must be TRUE):
  1. Caller can extract a class diagram with inheritance + composition/aggregation/association edges from a Python class hierarchy fixture, where composition vs aggregation is decided by the type-annotation rule (declared instance attribute typed as another class = composition; `Optional[...]` / `list[...]` / non-owned reference = aggregation; undecidable = `association` fallback — never emitted as undocumented "uses")
  2. Caller can extract a linear sequence diagram from the call graph (`alt`/`loop`/`par` branch fidelity is either present per SP-2 verdict or explicitly deferred to v0.3.0 in `.planning/spikes/SP-2-sequence-branch-fidelity.md`), a component diagram from import-derived module dependencies, and a package diagram where `node_type="package"` after the `lib-diagram-parser>=0.1.x` PR adding that enum value is merged
  3. Caller can extract a state diagram from FSM explicit patterns — `transitions.Machine(...)` library calls, `python-statemachine.StateMachine` subclasses, and native `Enum`-typed instance-attribute + transition-method patterns; `class Color(Enum): RED, GREEN, BLUE` produces zero FSMs (fixture-asserted negative case)
  4. State diagram extractor handles non-literal state mutation via return-value substitution analysis: when `self.state = self._next()` appears, the callee's return statements are resolved intra-class with N-level recursion and cycle detection; fully-resolved cases emit all concrete edges, unresolvable cases emit one placeholder edge with `unresolved=true` attribute (SP-1 spike result recorded — either ship general-control-flow FSM detection or defer to v0.3.0 with documented decision)
  5. Caller can extract `FunctionSpec(signature, docstring_sections, preconditions, postconditions)` from Sphinx Napoleon / Google / NumPy docstring styles and `ClassSpec(definition, members, invariants)` from Python source, plus auxiliary contract markers from `icontract` / `deal` decorators and PEP-316 `pre:` / `post:` docstring keywords (supplementary to Pydantic / dataclass already captured in Phase 2); all 5 diagram outputs validate against the shared `GraphNode` / `GraphEdge` / `GraphModel` schema with `physical_*` / `source_*` prefix fields used for physical-side-only metadata
**Plans**: 6 plans across 6 sequential waves (plans serialized because every extractor plan registers into the shared `_dispatch.py` EVALUATIONS dict + DIA-07 schema test — same-file ownership forces sequential waves)
  - Wave 0:
    - [x] 03-01-PLAN.md — Foundation: EdgeKind+=imports / GraphEdge.source_unresolved / spec.py (FunctionSpec/ClassSpec) / CodeContent 7 slots / executor EVALUATIONS walk / Wave-0 fixtures+conftest (closes 4 integration gaps)
  - Wave 1:
    - [x] 03-02-PLAN.md — DIA-01 class + DIA-03 component + DIA-04 package diagrams (+ DIA-07 schema conformance)
  - Wave 2:
    - [x] 03-03-PLAN.md — DIA-02 sequence diagram + SP-2 branch-fidelity spike verdict
  - Wave 3:
    - [x] 03-04-PLAN.md — DIA-05 FSM (3 families + negative case) + DIA-06 return-value substitution + SP-1 spike verdict
  - Wave 4:
    - [x] 03-05-PLAN.md — SPC-01 function spec + stdlib-only Google/NumPy/Sphinx docstring parser
  - Wave 5:
    - [ ] 03-06-PLAN.md — SPC-02 class spec + SPC-04 icontract/deal/PEP-316 marker detection (final EVALUATIONS entry)
**UI hint**: yes

### Phase 4: C++ Frontend + C++ Extractors
**Goal**: Bring up the C++ track behind the same CAV boundary established in Phase 1: implement the libclang-based C++ Frontend with the `compile_args` contract, deliver C++ AST primitive extractors (functions / classes / includes / type info) producing output with full schema parity to the Python track, run all five diagram extractors on C++ CAV, and implement the Doxygen contract extractor (`\pre` / `\post` / `\invariant`) so Python and C++ produce symmetric contract output. Includes the platform CI matrix bring-up (mandatory: Linux x86_64/aarch64 + Windows x86_64 across Python 3.11–3.14; best-effort continue-on-error: macOS arm64 + Python 3.13/3.14 per SP-3 result from Phase 1).
**Depends on**: Phase 3
**Requirements**: LNG-01, LNG-02, LNG-03, LNG-04, LNG-05, SPC-03, DET-02
**Success Criteria** (what must be TRUE):
  1. `pip install lib_code_parser` succeeds on CPython 3.11/3.12/3.13/3.14 on Linux x86_64, Linux aarch64, and Windows x86_64 (mandatory matrix all green), and on macOS arm64 + Python 3.13/3.14 (best-effort matrix observed with `continue-on-error: true`)
  2. `import lib_code_parser` triggers a runtime guard that calls `cindex.Index.create()` once and verifies the bundled `libclang==18.1.1` ABI version via `cindex.Config.library_path`; if the dylib fails to load, a clear `RuntimeError` is raised with platform-specific install instructions (one of: "install Xcode Command Line Tools", "install libclang-dev", "ensure msvc redistributable") and any caller override via `Config.set_library_file` is rejected
  3. Caller calling `CodeParserExecutor().execute(config, raw_content, "src.cpp")` with `config.language="cpp"` and `config.compile_args=["-std=c++17", "-I", "/path/to/headers"]` gets a `NormalizedArtifact` whose `CodeContent.functions / callgraph / type_deps` and all 5 diagrams have identical Pydantic shape to Python output (schema parity verified by structural assertion); unresolved `#include` directives surface as `diagnostics` warnings, never as parse errors
  4. Caller can extract Doxygen-driven contracts from C++ source — `\pre` / `\post` / `\invariant` markers become `ContractInfo` entries with the same schema as Python's Pydantic/dataclass contracts, so the spec_code_verifier processes both languages symmetrically; `TraceTag` extraction (`Traces: REQ-ID, US-NN`) works identically on Python docstrings and C++ Doxygen comments (parity test)
**Plans**: TBD

### Phase 5: Cross-Cutting Integration + Acceptance
**Goal**: Close the v0.2.0 release by verifying every cross-cutting acceptance criterion that spans phases — byte-identical determinism snapshot across 3 consecutive runs of the same fixture, cross-lib schema compatibility test that imports both `lib_code_parser` and `lib_diagram_parser` and asserts structural equivalence on representative `GraphModel` instances, the platform CI matrix gating PR merges, the README platform compatibility table (OS × Python version × C++ availability with "strongly supported" / "best-effort" labels), and the v0.2.0 release artifacts (tag, changelog, `pyproject.toml` final pins). No new extractor code; this phase is acceptance, integration test authoring, and release.
**Depends on**: Phase 4
**Requirements**: DET-01, SCH-04, DOC-02
**Success Criteria** (what must be TRUE):
  1. `tests/test_determinism.py` runs the full extractor pipeline on a representative Python + C++ fixture three consecutive times in fresh subprocesses (so each gets a distinct `PYTHONHASHSEED`) and asserts byte-identical `NormalizedArtifact.model_dump_json()` output; this test gates every PR merge in CI
  2. `tests/test_schema_compat.py` imports `from lib_diagram_parser import GraphNode, GraphEdge, GraphModel, GuardExpr` and `from lib_code_parser.models import GraphNode as CodeGraphNode, ...` and asserts (a) every required `lib_diagram_parser` field is present in the lib-code-parser model, (b) every shared field type matches, (c) `physical_*` / `source_*` extension fields exist only on the code-parser side — gating PR merges
  3. `README.md` ships a platform compatibility matrix table with rows for {Linux x86_64, Linux aarch64, Windows x86_64, macOS arm64} × columns for {Python 3.11, 3.12, 3.13, 3.14} × C++ availability, with explicit "strongly supported" (green) and "best-effort" (yellow) cells, and the `Definition of Done` checklist from REQUIREMENTS.md is fully `[x]` — 42/42 v1 requirements complete, CI green, snapshot tests passing, no regression vs. v0.1.0 baseline, Apache-2.0 license declared, sibling-lib PR merged
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Architecture Foundation + Spec Correction | 10/10 | Complete   | 2026-05-25 |
| 2. Python Frontend + AST Primitives + ACL-2 Adapters | 7/7 | Complete   | 2026-05-31 |
| 3. Python Diagram + Spec Extractors | 5/6 | In Progress|  |
| 4. C++ Frontend + C++ Extractors | 0/TBD | Not started | - |
| 5. Cross-Cutting Integration + Acceptance | 0/TBD | Not started | - |
