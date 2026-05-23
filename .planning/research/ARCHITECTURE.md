# Architecture Research

**Domain:** Multi-language deterministic code parser (Python AST + libclang for C++) with ACL-2 subprocess integration and schema compatibility to a sibling diagram parser.
**Researched:** 2026-05-24
**Confidence:** HIGH (verified against sibling lib source, libclang docs, recent academic work on deterministic LSP integration, and tree-sitter ecosystem references)

---

## Verdict Up-Front (so the roadmap can use this directly)

| Question | Verdict |
|----------|---------|
| Component boundary for multi-language | **Per-language Frontend** that emits a thin **Common AST View (CAV)** → **per-aspect extractors** consume CAV (not raw AST). Frontend = adapter; CAV = port. |
| Internally lib-callable modules | **Pure-function modules + explicit dispatch table** (no decorator registry, no import-time side effects). Each extractor importable and callable on its own. |
| Subprocess isolation | **ACL-2 Adapter layer** sitting between Frontend and Extractors. Adapters run subprocess, normalize/canonicalize output, return Pydantic models. Core never touches `subprocess` directly. |
| Determinism preservation | (1) Frozen tool versions pinned in config, (2) canonical sort order on all collections in models, (3) timestamps/paths-with-cwd stripped at adapter boundary, (4) `errors="replace"` decode policy explicit, (5) AST shared once per file. |
| Shared AST data flow | **Parse once at Frontend, share immutable `CAV` to all extractors.** Fixes existing v0.1.0 "4× re-parse" anti-pattern. |
| Sibling schema alignment | **Reuse `GraphNode` / `GraphEdge` / `GraphModel` semantics, do not import the package.** Define structurally-compatible types in this lib with optional physical-side metadata fields. Verifier compares by structural keys (`node_id`, `edge_type`, `source`/`target`). |
| Registry vs explicit dispatch | **Explicit dispatch.** Determinism requirement + small extractor count (5–8) + need for traceable build order → registry is over-engineering and risks import-time side effects. |
| Build order | **Models → Frontend (CAV) → ACL-2 Adapters → Per-aspect extractors → Diagram extractors (depend on AST extractors) → Orchestrator (Facade).** |

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Caller (spec-reviewer pipeline)                      │
│                  imports CodeParserExecutor                           │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ execute(config, raw_content, path)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Orchestration Layer  —  CodeParserExecutor (Facade)                  │
│  - gating (enabled / language / extractor flags)                      │
│  - selects Frontend by language                                       │
│  - dispatches extractors (explicit table, not registry)               │
│  - assembles NormalizedArtifact                                       │
└───────┬──────────────────────────────────────────────────────────────┘
        │ raw_content, path, config
        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Frontend Layer  —  Per-Language Adapters                             │
│  ┌────────────────────┐         ┌────────────────────┐                │
│  │  PythonFrontend    │         │  CppFrontend       │                │
│  │  stdlib `ast`      │         │  libclang          │                │
│  │  parses once       │         │  TU + cursor       │                │
│  └─────────┬──────────┘         └─────────┬──────────┘                │
│            │  produces                    │ produces                  │
│            ▼                              ▼                           │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Common AST View (CAV)  —  immutable Pydantic envelope        │   │
│  │  - language: "python"|"cpp"                                   │   │
│  │  - source: str, path: str, module_name: str                   │   │
│  │  - raw_tree: <ast.Module> | <cindex.TranslationUnit> (Opaque) │   │
│  │  - precomputed: imports, class_decls, func_decls (light view) │   │
│  └──────────────────────────────────────────────────────────────┘    │
└───────┬──────────────────────────────────────────────────────────────┘
        │ CAV
        ├─────────────────────┬─────────────────────┬─────────────────┐
        ▼                     ▼                     ▼                 ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐
│ Aspect Extractors                                                            │
│  functions   │  │  callgraph(AST) │  │  type_deps(AST) │  │  contracts   │
│  (CAV)       │  │  + ACL-2 adapter│  │  + ACL-2 adapter│  │  (CAV)       │
│              │  │  (callgraph.py) │  │  (pyright/clang)│  │              │
└──────┬───────┘  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘
       │                   │                    │                   │
       └────────┬──────────┴──────────┬─────────┴──────────┬────────┘
                ▼                     ▼                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Diagram Extractors  (depend on functions + callgraph + type_deps)    │
│  class_diagram │ sequence_diagram │ component_diagram │ package_diagram│ │
│  state_diagram (FSM-pattern only; spike for general flow)            │
└──────┬──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Models Layer (Pydantic v2) — single shared data contract             │
│  CAV, FunctionNode, CallGraph, TypeDep, ContractInfo,                 │
│  DiagramRef, GraphNode, GraphEdge, GraphModel (schema-compatible      │
│  with lib-diagram-parser; physical metadata in optional fields)       │
└──────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                          NormalizedArtifact
                          (returned to caller)
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Orchestrator** (`executor.py`) | Public entry, gating, explicit dispatch to language frontend + extractors, assembly | Single `CodeParserExecutor` class with `execute()` method; dispatch via dict `{language: Frontend, extractor_name: ExtractorFn}` |
| **Language Frontend** (`frontends/python.py`, `frontends/cpp.py`) | Parse once, produce CAV, expose light precomputed views (imports, class decls, func decls) | Pure function `parse(source, path) -> CAV`; raises `ParseError` for invalid input |
| **Common AST View (CAV)** (`models.py`) | Immutable envelope carrying raw tree + light metadata + language tag | Pydantic `BaseModel` with `model_config = {"arbitrary_types_allowed": True, "frozen": True}` to wrap opaque `ast.Module` / `cindex.TranslationUnit` |
| **Aspect Extractor** (`extractors/functions.py`, `extractors/callgraph.py`, etc.) | One file = one analysis aspect. Pure function `extract(cav, config) -> ModelCollection` | Module-level function importable directly by callers; no class wrapper |
| **ACL-2 Adapter** (`adapters/callgraph_tool.py`, `adapters/pyright.py`, `adapters/clang_subprocess.py`) | Wrap `subprocess.run` for external tools; canonicalize output; strip volatile fields (timestamps, cwd-prefixed paths); return Pydantic models | Thin wrapper functions; pinned tool version asserted; fixed env vars (`LC_ALL=C`, `PYTHONHASHSEED=0`); deterministic ordering applied |
| **Diagram Extractor** (`diagrams/class_diagram.py`, etc.) | Synthesize a `GraphModel` from already-extracted aspect data (FunctionNode list, CallGraph, etc.). No re-parsing. | Pure function `build(functions, callgraph, type_deps) -> GraphModel`; depends on aspect extractors via Pydantic models only |
| **Models** (`models.py`) | All Pydantic types. Single source of truth. | Pydantic v2 `BaseModel` subclasses, validators for canonical ordering on `__init__` |

---

## Recommended Project Structure

```
lib_code_parser/
├── __init__.py                       # Public re-exports only
├── executor.py                       # CodeParserExecutor (Facade/Orchestrator)
├── models.py                         # All Pydantic models (single source of truth)
├── _paths.py                         # Shared `module_name(path)` helper (kills v0.1.0 4× duplication)
├── frontends/
│   ├── __init__.py
│   ├── base.py                       # Frontend Protocol/ABC defining parse(source, path) -> CAV
│   ├── python_frontend.py            # stdlib ast → CAV
│   └── cpp_frontend.py               # libclang (clang.cindex) → CAV
├── extractors/
│   ├── __init__.py
│   ├── functions.py                  # extract_functions(cav, config) -> list[FunctionNode]
│   ├── callgraph.py                  # build_callgraph(cav, config) -> CallGraph
│   ├── type_deps.py                  # build_type_deps(cav, config) -> list[TypeDep]
│   └── contracts.py                  # extract_contracts(cav, config) -> dict[class_id, ContractInfo]
├── adapters/                         # subprocess isolation layer (ACL-2 wrappers)
│   ├── __init__.py
│   ├── base.py                       # Adapter Protocol; common subprocess hardening helpers
│   ├── callgraph_tool.py             # wraps `callgraph.py` (Python deterministic call graph)
│   ├── pyright_tool.py               # wraps `pyright --outputjson` (Python type-resolved deps)
│   └── clang_tool.py                 # wraps `clang -Xclang -ast-dump=json` (C++ fallback if libclang Python binding unavailable)
├── diagrams/                         # depend on extractors via models only
│   ├── __init__.py
│   ├── class_diagram.py              # build_class_diagram(functions, type_deps) -> GraphModel
│   ├── sequence_diagram.py           # build_sequence_diagram(callgraph, functions) -> GraphModel
│   ├── component_diagram.py          # build_component_diagram(type_deps) -> GraphModel
│   ├── package_diagram.py            # build_package_diagram(functions, paths) -> GraphModel
│   └── state_diagram.py              # build_state_diagram_fsm(functions, callgraph) -> GraphModel
├── spec_extractors/                  # function/class spec extraction (parallel to lib-spec-parser semantics)
│   ├── __init__.py
│   ├── function_spec.py              # extract_function_specs(functions) -> list[FunctionSpec]
│   └── class_spec.py                 # extract_class_specs(functions, contracts) -> list[ClassSpec]
└── _dispatch.py                      # Explicit dispatch tables: {language: Frontend}, {aspect: ExtractorFn}
                                      # No decorators; no import-time side effects
tests/
├── unit/
│   ├── test_python_frontend.py
│   ├── test_cpp_frontend.py
│   ├── extractors/test_functions.py  # callable in isolation
│   ├── extractors/test_callgraph.py
│   ├── adapters/test_pyright.py      # mocked subprocess
│   ├── adapters/test_callgraph_tool.py
│   └── diagrams/test_class_diagram.py
├── acceptance/
│   ├── test_python_full_pipeline.py  # end-to-end with real tools
│   ├── test_cpp_full_pipeline.py
│   ├── test_determinism.py           # same input → byte-identical output across runs
│   └── test_diagram_compat.py        # output GraphModel matches lib-diagram-parser schema
└── fixtures/
    ├── python/
    └── cpp/
```

### Structure Rationale

- **`frontends/` separate from `extractors/`:** Encodes the "parse once, extract many" decision in the directory tree itself. A reviewer reading the structure immediately sees that language-specific code is bounded.
- **`adapters/` is its own layer:** Subprocess is a cross-cutting concern; placing it next to extractors would let extractors call subprocess directly. A dedicated layer enforces "extractors talk to adapters only via models."
- **`diagrams/` after `extractors/`:** Build-order visible. Diagram extractors are second-tier consumers — they never see raw AST.
- **`_dispatch.py` is private:** Dispatch tables are an implementation detail, not API. Keeping them out of `__init__.py` prevents callers from monkey-patching extractors at runtime (which would break determinism).
- **`_paths.py`:** Kills the v0.1.0 anti-pattern of 4 copies of `_get_module_name`. One module, one definition.
- **Every extractor / adapter / diagram module is independently importable and callable.** This is the "lib-internal callable" requirement. The orchestrator is a convenience, not a gatekeeper. Direct calls like `from lib_code_parser.extractors.functions import extract_functions` work for advanced consumers.

---

## Architectural Patterns

### Pattern 1: Frontend + Common AST View (CAV) — multi-language unification

**What:** A per-language `Frontend` produces a single `CAV` (Common AST View) Pydantic envelope. All downstream extractors consume `CAV`, not raw `ast.Module` or `cindex.TranslationUnit`. The CAV wraps the raw tree as an opaque object (for language-specific extractors that need it) plus a small precomputed neutral view (imports list, class decl list, func decl list) for language-agnostic extractors.

**When to use:** Multi-language parsers where (a) downstream analyses are mostly language-agnostic at the *structural* level (call graph nodes, class names, type names) but (b) language-specific extractors still need full AST access. This is the standard pattern in modern multi-language tools — DP-LARA, CrossTL, tree-sitter-analyzer all use a virtual/common AST layer ([CrossTL paper](https://arxiv.org/pdf/2508.21256), [DP-LARA paper](https://arxiv.org/html/2506.03903)).

**Trade-offs:**
- ✅ Single parse cost (~4× speedup vs v0.1.0 re-parse anti-pattern)
- ✅ Language-agnostic extractors (e.g., `class_diagram`) work for both Python and C++ with one implementation
- ✅ Adding a 3rd language requires only a new `Frontend`, no extractor changes
- ❌ CAV interface must be designed carefully — too thin = extractors fall back to raw tree (defeats purpose); too thick = becomes a leaky abstraction
- ❌ Opaque raw tree in Pydantic requires `arbitrary_types_allowed=True` — slightly weaker validation

**Example:**
```python
# frontends/base.py
from typing import Protocol
from lib_code_parser.models import CAV

class Frontend(Protocol):
    def parse(self, source: str, path: str) -> CAV: ...

# frontends/python_frontend.py
import ast
from lib_code_parser.models import CAV, ClassDecl, FuncDecl

def parse(source: str, path: str) -> CAV:
    tree = ast.parse(source)
    return CAV(
        language="python",
        source=source,
        path=path,
        module_name=_module_name(path),
        raw_tree=tree,  # opaque; only python_frontend extractors should touch
        class_decls=[ClassDecl(name=n.name, lineno=n.lineno)
                     for n in ast.walk(tree) if isinstance(n, ast.ClassDef)],
        func_decls=[FuncDecl(name=n.name, lineno=n.lineno)
                    for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)],
        imports=[...],
    )
```

### Pattern 2: Explicit Dispatch Table (not Plugin Registry)

**What:** Dispatch is a `dict[str, Callable]` defined statically in `_dispatch.py`. No decorators, no entry points, no import-time side effects.

**When to use:** Deterministic systems where (a) extension is rare (5–8 extractors, not 50), (b) build-order traceability matters, (c) testing must be reproducible. The registry-pattern community itself warns that decorator-based registration "only runs when files are imported; if a module is never explicitly imported, the decorator won't work" — forcing implicit imports that fight determinism ([Tihomir Manushev — Registry Pattern with Decorators](https://medium.com/@tihomir.manushev/implementing-the-registry-pattern-with-decorators-in-python-de8daf4a452a)).

**Trade-offs:**
- ✅ One file to read = full list of all extractors → build order obvious
- ✅ No import-time side effects = test isolation
- ✅ Static analysis tools (pyright itself!) can see all dispatch targets
- ❌ Adding a new extractor requires editing `_dispatch.py` (closed for modification — violates strict Open/Closed)
- ❌ Less "magical" — but for a deterministic parser, magic is a liability

**Example:**
```python
# _dispatch.py
from lib_code_parser.frontends import python_frontend, cpp_frontend
from lib_code_parser.extractors import functions, callgraph, type_deps, contracts

FRONTENDS: dict[str, Frontend] = {
    "python": python_frontend,
    "cpp": cpp_frontend,
}

ASPECT_EXTRACTORS: dict[str, Callable[[CAV, ParserConfig], object]] = {
    "functions":  functions.extract_functions,
    "callgraph":  callgraph.build_callgraph,
    "type_deps":  type_deps.build_type_deps,
    "contracts":  contracts.extract_contracts,
}

# executor.py uses it
class CodeParserExecutor:
    def execute(self, config, raw_content, path):
        lang = self._detect_language(path, config)
        frontend = FRONTENDS[lang]
        cav = frontend.parse(raw_content.decode("utf-8", errors="replace"), path)
        results = {name: fn(cav, config) for name, fn in ASPECT_EXTRACTORS.items() if config.is_enabled(name)}
        ...
```

### Pattern 3: Subprocess Adapter with Canonicalization Boundary

**What:** Every external tool (callgraph.py, pyright, clang) is invoked through an Adapter module in `adapters/`. The adapter (a) pins the tool version, (b) sets a fixed locale/env, (c) runs subprocess, (d) parses JSON output, (e) **canonicalizes** — sorts collections by stable keys, strips volatile fields (timestamps, run IDs, cwd-prefixed paths), (f) returns a Pydantic model. Extractors call adapters, never `subprocess` directly.

**When to use:** Any deterministic pipeline that needs to wrap a tool whose output may include non-deterministic noise. This is exactly what recent academic work on Lanser-CLI describes for pyright integration: "equivalent requests should produce byte-stable artifacts after response normalization. Lists are deterministically ordered by (uri, sL, sC, eL, eC) with explicit tie-breakers" ([Reinforcement Learning from Compiler and Language Server Feedback](https://arxiv.org/pdf/2510.22907)).

**Trade-offs:**
- ✅ Single chokepoint for determinism hardening — auditing one file proves the whole subprocess surface is safe
- ✅ Extractors stay pure (testable without spawning real subprocesses; mock the adapter)
- ✅ Tool version drift is detectable (adapter asserts version on first call)
- ❌ Extra layer means one more indirection to debug
- ❌ JSON parsing cost — but negligible compared to running the tool

**Example:**
```python
# adapters/pyright_tool.py
import subprocess, json, os
from lib_code_parser.models import TypeDep

_PINNED_VERSION = "1.1.350"  # exact match required

def run(path: str, source: str) -> list[TypeDep]:
    # Determinism hardening
    env = {**os.environ, "LC_ALL": "C", "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        ["pyright", "--outputjson", path],
        input=source, capture_output=True, text=True, env=env, check=False,
    )
    raw = json.loads(result.stdout)
    _assert_version(raw, _PINNED_VERSION)
    # Canonicalize: strip cwd prefix, sort by (file, line, col)
    deps = [_to_type_dep(item, base_path=path) for item in raw["typeCompletions"]]
    return sorted(deps, key=lambda d: (d.source_file, d.lineno, d.col, d.symbol))
```

### Pattern 4: Schema Compatibility by Structural Duplication (not Import)

**What:** The diagram output uses the **same field names and semantics** as `lib_diagram_parser.models` (`GraphNode`, `GraphEdge`, `GraphModel`, `DiagramRef`) but **defines them independently in this lib's `models.py`**. Optional fields are added for physical-side metadata (e.g., `source_range`, `physical_module`). Verifier code performs structural comparison on shared field names; never type-equality.

**When to use:** Sibling libraries that must produce comparable output but should not depend on each other (avoids version coupling, circular dependencies, and forces explicit schema contract maintenance).

**Trade-offs:**
- ✅ Zero runtime coupling between libs
- ✅ Each lib can evolve its model on its own release cadence
- ✅ Verifier sees both outputs as the same structural shape
- ❌ Schema drift risk if the two models are not kept in sync — mitigation: a `schema_contract_test.py` in **both** repos that loads both packages and asserts field-name parity for shared types
- ❌ Cannot share validators (must be duplicated)

**Example:**
```python
# lib_code_parser/models.py — structurally compatible with lib_diagram_parser.models
class GraphNode(BaseModel):
    node_id: str
    node_type: str        # SHARED VOCABULARY: "class"|"component"|"state"|...
    label: str
    attributes: dict = {}
    # Physical-side additions (lib-diagram-parser does NOT have these):
    source_range: SourceRange | None = None
    physical_module: str | None = None

class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str        # SHARED VOCABULARY
    label: str = ""
    # Physical-side additions:
    call_site_lineno: int | None = None
```

### Pattern 5: Hexagonal Boundary for the Whole Lib

**What:** Apply ports-and-adapters at the lib level. The "domain" is the extraction logic (CAV → models). The "ports" are: `ParserConfig` in, `NormalizedArtifact` out, plus internal `Frontend` and `Adapter` protocols. The "adapters" are: `python_frontend`, `cpp_frontend`, `pyright_tool`, `callgraph_tool`, `clang_tool`. The caller and the external tools are the "outside world."

**When to use:** Libraries with multiple external integration points (here: 2 languages × 3 tools). Hexagonal makes the integration surface explicit and testable ([Hexagonal Architecture in Python — Douwe van der Meij](https://douwevandermeij.medium.com/hexagonal-architecture-in-python-7468c2606b63)).

**Trade-offs:**
- ✅ Domain logic (extractors, diagram builders) is testable with fake CAVs and fake adapter outputs — no subprocess in unit tests
- ✅ Adding a new language = new Frontend adapter, no domain changes
- ❌ Pattern overhead for tiny libs is real — but lib-code-parser is genuinely multi-integration, so it earns its keep

---

## Data Flow

### Primary Request Flow

```
[Caller passes (config, raw_content, path)]
              ↓
[Orchestrator: gating + language detection]
              ↓
[Frontend selected via FRONTENDS[lang]]
              ↓
[Frontend.parse(source, path) → CAV]            ← single parse here
              ↓
[CAV passed to each enabled aspect extractor in parallel-safe order:]
   functions(cav)  →  list[FunctionNode]
   callgraph(cav)  →  CallGraph         (may invoke callgraph_tool adapter)
   type_deps(cav)  →  list[TypeDep]     (may invoke pyright_tool adapter)
   contracts(cav)  →  dict[id, ContractInfo]
              ↓
[Merge: contracts attached to matching FunctionNode by class_id]
              ↓
[Diagram extractors consume aspect models (no CAV needed):]
   class_diagram(functions, type_deps) → GraphModel
   sequence_diagram(callgraph, functions) → GraphModel
   component_diagram(type_deps) → GraphModel
   package_diagram(functions, paths) → GraphModel
   state_diagram(functions, callgraph) → GraphModel
              ↓
[Spec extractors consume aspect models:]
   function_spec(functions) → list[FunctionSpec]
   class_spec(functions, contracts) → list[ClassSpec]
              ↓
[NormalizedArtifact assembled and returned]
```

### Determinism Flow (cross-cutting)

```
raw_content (bytes)
   │
   ├── decode("utf-8", errors="replace") ── deterministic, documented in API
   │
   ▼
source (str) ── pure function input
   │
   ▼
Frontend.parse ── ast / libclang: deterministic on fixed Python/clang version
   │
   ▼
CAV (Pydantic frozen) ── immutable, hash-stable
   │
   ▼
Extractor ── pure function on CAV
   │
   ├── (subprocess?) ── Adapter: pinned version + LC_ALL=C + canonical sort
   │
   ▼
Pydantic model ── sorted collections in __init__ via field_validator
   │
   ▼
NormalizedArtifact ── deterministic output (verifiable via re-run hash test)
```

### Build-Order Dependencies (which extractor blocks which)

```
                              [Models]
                                 │
                  ┌──────────────┴──────────────┐
                  ▼                              ▼
              [_paths.py]                   [CAV definition]
                  │                              │
                  └──────────────┬───────────────┘
                                 ▼
                         [Frontend (Python)]  ← can build first; v0.1.0 has stdlib `ast` already
                                 │
                                 ▼
                         [Aspect Extractors: functions, contracts]
                                 │              ← no subprocess; pure CAV consumers
                                 ▼
                         [ACL-2 Adapters: pyright, callgraph.py]
                                 │              ← can be developed in parallel with extractors
                                 ▼
                         [Aspect Extractors: callgraph, type_deps]
                                 │              ← depend on adapters
                                 ▼
                         [Diagram Extractors]    ← depend on aspect models only
                                 │
                                 ▼
                         [Spec Extractors]       ← depend on functions + contracts
                                 │
                                 ▼
                         [Orchestrator]          ← integrates everything
                                 │
                                 ▼
                         [C++ Frontend (libclang)] ← parallel track once CAV is stable
```

**Critical path:** Models → CAV → Python Frontend → functions extractor → orchestrator skeleton. Everything else can be developed in parallel branches once CAV is fixed.

**Key insight for roadmapping:** CAV is the **single contract that gates all parallel work.** Treat its design like a `parallel-contract-first` exercise — fix CAV first, then fan out.

---

## Scaling Considerations

This is a library, not a service — "scale" means "size and count of source files processed in one pipeline run."

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **Small repo** (≤ 100 Python files) | Default architecture is fine. Single-threaded, ~ms per file. Most of the cost is `pyright` startup (~500ms per file when invoked per-file). |
| **Medium repo** (100–10,000 files) | (1) **Batch the pyright adapter** — invoke pyright once on a directory instead of per-file (pyright is designed for project-mode). The adapter exposes both `run_one(path)` and `run_batch(paths)`. (2) **Cache CAV per file** — if the caller pipelines multiple analyses, cache by `(path, source_hash)`. |
| **Large repo** (10,000+ files) | (1) **Parallel processing at the caller layer** — the lib stays single-threaded inside, but documents that `execute()` is safe to call from multiple processes (it is, since it has no global state). (2) **Process pool** for libclang — `cindex.TranslationUnit` is heavy; pool 4–8 workers. |

### Scaling Priorities

1. **First bottleneck: pyright subprocess startup** — ~500ms per invocation regardless of file size. Fix: batch mode adapter (`pyright --outputjson` on a project, then post-process to per-file results).
2. **Second bottleneck: libclang parse time on C++ headers** — easily 1–10 seconds per translation unit with deep includes. Fix: PCH (precompiled headers) cache, configurable include paths.
3. **Third bottleneck: AST walk for large functions** — solved by CAV (one parse, multiple cheap walks).

---

## Anti-Patterns

### Anti-Pattern 1: Decorator-based Plugin Registry

**What people do:** Use `@register_extractor("functions")` decorators that populate a module-level dict on import.
**Why it's wrong:** Determinism guarantees break because (a) the order of extractors becomes import-order-dependent, (b) entry points like `setup.py entry_points` introduce environment-dependent behavior, (c) tests that import modules in a different order get different dispatch tables, (d) the warning from the Python community itself: "decorator-based registration only runs when files are imported; if a module is never explicitly imported, the decorator won't work" ([Tihomir Manushev — Registry Pattern with Decorators](https://medium.com/@tihomir.manushev/implementing-the-registry-pattern-with-decorators-in-python-de8daf4a452a)).
**Do this instead:** Explicit `dict[str, Callable]` in `_dispatch.py`. Boring but provably deterministic.

### Anti-Pattern 2: Re-parsing the AST per extractor (v0.1.0's mistake)

**What people do:** Each extractor takes raw `source: str` and calls `ast.parse(source)` itself (current v0.1.0 behavior — 4× re-parse per file).
**Why it's wrong:** ~4× wasted CPU; couples each extractor to the parsing tool (so swapping `ast` for `libcst` or tree-sitter requires 4 edits).
**Do this instead:** Frontend parses once, hands CAV to all extractors. Extractors take `CAV`, not `str`.

### Anti-Pattern 3: Extractor directly calling `subprocess`

**What people do:** `callgraph_builder.py` shells out to `callgraph.py` itself.
**Why it's wrong:** (1) Subprocess concerns (env, encoding, version pinning, output canonicalization) get duplicated across extractors; (2) unit tests for the extractor must mock subprocess; (3) determinism hardening (LC_ALL, PYTHONHASHSEED) gets forgotten in some extractors; (4) the lib's "no I/O" contract is silently violated.
**Do this instead:** Subprocess lives **only** in `adapters/`. Extractors call adapter functions and receive Pydantic models.

### Anti-Pattern 4: Hidden global state for "caching"

**What people do:** Module-level `_AST_CACHE: dict[str, ast.Module] = {}` to avoid re-parse.
**Why it's wrong:** Breaks determinism across test runs (cache persists between tests), breaks process safety, hides the parse cost from callers. **AND** the CAV pattern (parse once at Frontend, share immutable) already solves the re-parse problem without state.
**Do this instead:** CAV is request-scoped; no module-level mutables anywhere. v0.1.0's "no global state" guarantee must be preserved.

### Anti-Pattern 5: Dynamic dispatch via `getattr(module, fn_name)`

**What people do:** `extractor = getattr(extractors_module, config.extractor_name)`.
**Why it's wrong:** Pyright and other static analyzers cannot see the dispatch targets; refactoring breaks silently; typos become runtime errors; security risk if `config.extractor_name` is ever caller-influenced.
**Do this instead:** Explicit dispatch dict. If a key isn't in the dict, raise `ValueError("unknown extractor")` with the list of valid keys.

### Anti-Pattern 6: Subprocess output trusted as-is (no canonicalization)

**What people do:** Take `pyright --outputjson` output, parse JSON, return directly.
**Why it's wrong:** pyright's JSON contains timestamps, version metadata, and unordered lists; same source → different output bytes → bisimulation breaks. Recent academic work explicitly identifies this as the failure mode of naïve LSP integration: "Language servers were designed for interactive IDEs, not autonomous optimization loops" ([Lanser-CLI paper](https://arxiv.org/pdf/2510.22907)).
**Do this instead:** Adapter strips volatile fields, sorts collections by stable composite keys, asserts pinned tool version.

### Anti-Pattern 7: Diagram extractors re-parsing source

**What people do:** `class_diagram.py` walks AST again to find class declarations.
**Why it's wrong:** Duplicates work the functions extractor already did; introduces drift (what if the two interpretations of "class" diverge?); breaks the layering rule that diagram extractors are second-tier consumers.
**Do this instead:** Diagram extractors take `list[FunctionNode]` (which includes class kind), `CallGraph`, `list[TypeDep]` as input. No AST. No CAV. Only aspect models.

### Anti-Pattern 8: Tight import coupling to `lib_diagram_parser`

**What people do:** `from lib_diagram_parser.models import GraphModel` to "stay compatible."
**Why it's wrong:** Sibling lib's version becomes a hard dependency; circular maintenance; if `lib_diagram_parser` renames a field, this lib breaks even if its own schema didn't change.
**Do this instead:** Define structurally-compatible `GraphModel` independently in `lib_code_parser/models.py`. Verifier-side handles the comparison. A `schema_contract_test.py` in both repos asserts field-name parity to catch drift early.

---

## Integration Points

### External Services / Tools

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **callgraph.py** (ACL-2) | Subprocess via `adapters/callgraph_tool.py` | Pin version; assert on first call; canonicalize node IDs by removing cwd prefix |
| **pyright** (ACL-2) | Subprocess via `adapters/pyright_tool.py`, prefer batch mode | Pin version (e.g. `1.1.350`); set `LC_ALL=C`, `PYTHONHASHSEED=0`; sort `typeCompletions` by `(file, line, col, symbol)` |
| **libclang / clang.cindex** | Python binding via `frontends/cpp_frontend.py`; subprocess fallback via `adapters/clang_tool.py` if binding unavailable | Use `Config.set_library_path()` once at frontend init; filter cursors by location to avoid include pollution ([Libclang tutorial — LLVM](https://clang.llvm.org/docs/LibClang.html)) |
| **lib-diagram-parser** | **No runtime dependency.** Schema compatibility via structurally-duplicated Pydantic models. Verified by contract test. | See Pattern 4 |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Orchestrator ↔ Frontend | Frontend.parse(source, path) → CAV | Frontend is a Protocol, selected via FRONTENDS dispatch table |
| Orchestrator ↔ Aspect Extractor | extractor(cav, config) → ModelCollection | Extractor is a free function, importable directly by external advanced callers (satisfies "lib-internal callable" requirement) |
| Aspect Extractor ↔ ACL-2 Adapter | adapter.run(args) → Pydantic model | Adapter is the only place `subprocess` appears |
| Aspect Extractor ↔ Diagram Extractor | Aspect produces Pydantic model; Diagram consumes the model | One-way; diagrams never call aspects directly, they receive already-computed models from orchestrator |
| Models layer ↔ everyone | All layers import from `models.py`; models import only `pydantic` | Acyclic dependency graph (current v0.1.0 invariant preserved) |
| Caller ↔ Public API | `from lib_code_parser import CodeParserExecutor, ParserConfig, NormalizedArtifact, ...` | Single import surface via `__init__.py` re-exports |
| Caller ↔ Internal modules | `from lib_code_parser.extractors.functions import extract_functions` | **Explicitly supported.** Each extractor module is part of the documented API for advanced callers. |

---

## Module-Level Lib-Internal Callability — explicit treatment

Per PROJECT.md target: "Internally loose-coupled, each extractor lib-internal callable independently."

**Realization:**

1. **Every extractor is a module-level pure function.** Not a class method, not a closure, not a decorator-registered handler. This means:
   ```python
   from lib_code_parser.extractors.functions import extract_functions
   from lib_code_parser.frontends.python_frontend import parse as parse_python

   cav = parse_python(source, "foo.py")
   funcs = extract_functions(cav, my_config)  # works in isolation
   ```

2. **Module contract = Pydantic model only.** Extractors take `CAV` (Pydantic) and `ParserConfig` (Pydantic), return Pydantic models. Never raw `ast.Module`, never callbacks, never mutable state. This is the "Module 間契約 — Pydantic model のみで依存、直接呼び出しなし" requirement from PROJECT.md Active Requirements §E.

3. **Adapters are also independently callable:**
   ```python
   from lib_code_parser.adapters.pyright_tool import run as run_pyright
   type_deps = run_pyright("foo.py", source)  # works in isolation
   ```

4. **Diagram extractors are independently callable:**
   ```python
   from lib_code_parser.diagrams.class_diagram import build_class_diagram
   graph = build_class_diagram(functions, type_deps)  # works in isolation; no CAV needed
   ```

5. **`__init__.py` re-exports the most common entry points only.** Advanced callers reach into submodules. This keeps the "main" API small while honoring the loose-coupling requirement.

**Testing implication:** Every module has its own unit test file that calls it in isolation. No "must run the orchestrator to test extractor X" coupling.

---

## Determinism Preservation Strategy (full detail)

This deserves its own section because it's the Core Value gate.

### Determinism Hazards in the Subprocess Boundary

| Hazard | Source | Mitigation |
|--------|--------|------------|
| Timestamps in tool output | pyright JSON metadata, callgraph.py headers | Strip in adapter `__call__` before constructing Pydantic |
| Locale-dependent sort order | Default LC_ALL on Linux/Windows differs | `env["LC_ALL"] = "C"` in subprocess.run |
| Hash-order iteration | `set` / `dict` iteration order in tool's internals | `env["PYTHONHASHSEED"] = "0"` for subprocesses we invoke |
| Path with cwd prefix | Tools output absolute paths with /home/user or C:\Users\… | Adapter normalizes to project-relative; orchestrator passes `path` arg through |
| Tool version drift | `pip install -U pyright` silently changes output schema | Adapter calls `tool --version` on first invocation, asserts pinned version |
| Re-execution caches | pyright `.pyright_cache/`, libclang PCH | Either point to fixed temp dir or set `PYRIGHT_NO_CACHE=1` |
| Multi-thread tool internals | clang TU parsing can be multi-threaded | Set `-j 1` or equivalent single-threaded flag |
| Floating-point lineno / col (rare) | Some tools emit float coordinates | Cast to int in adapter |

### Determinism Test (must be in acceptance suite)

```python
# tests/acceptance/test_determinism.py
def test_byte_identical_output_across_runs(sample_python_file):
    raw = sample_python_file.read_bytes()
    config = ParserConfig(...)
    executor = CodeParserExecutor()

    runs = [executor.execute(config, raw, str(sample_python_file)) for _ in range(5)]
    serialized = [r.model_dump_json(sort_keys=True) for r in runs]

    assert all(s == serialized[0] for s in serialized), \
        "Non-deterministic output detected; check adapter canonicalization"
```

Run this test on every PR. If it fails, determinism is broken.

---

## Sources

- [CrossTL: A Universal Programming Language Translator with Unified Intermediate Representation (arXiv 2508.21256)](https://arxiv.org/pdf/2508.21256) — common IR pattern, modular frontend/backend architecture
- [Multi-Language Detection of Design Pattern Instances — DP-LARA (arXiv 2506.03903)](https://arxiv.org/html/2506.03903) — virtual AST common to multiple OOP languages
- [Architectural Design Patterns for Language Parsers (Köveskán et al., Acta Polytechnica Hungarica)](https://acta.uni-obuda.hu/Kovesdan_Asztalos_Lengyel_51.pdf) — parser architectural pattern catalog
- [Reinforcement Learning from Compiler and Language Server Feedback (arXiv 2510.22907)](https://arxiv.org/pdf/2510.22907) — Lanser-CLI determinism approach for pyright; canonical bundle hashing; stable ordering keys
- [Implementing the Registry Pattern with Decorators in Python — Tihomir Manushev](https://medium.com/@tihomir.manushev/implementing-the-registry-pattern-with-decorators-in-python-de8daf4a452a) — registry pattern import-time fragility warning
- [Python Registry Pattern: A Clean Alternative to Factory Classes — DEV Community](https://dev.to/dentedlogic/stop-writing-giant-if-else-chains-master-the-python-registry-pattern-ldm) — registry vs explicit dispatch tradeoffs
- [Libclang tutorial — Clang documentation](https://clang.llvm.org/docs/LibClang.html) — Translation Unit + cursor model
- [Clang Indexing Library Bindings — libclang Python readthedocs](https://libclang.readthedocs.io/) — clang.cindex API surface
- [TraversingClangASTwithPython — GitHub guide](https://github.com/tehranixyz/TraversingClangASTwithPython) — recursive cursor traversal pattern, location filtering
- [Hexagonal Architecture in Python — Douwe van der Meij](https://douwevandermeij.medium.com/hexagonal-architecture-in-python-7468c2606b63) — ports/adapters in Python
- [tree-sitter — GitHub](https://github.com/tree-sitter/tree-sitter) — alternative multi-language parser generator (considered and rejected for C++ — see below)
- [tree-sitter-analyzer (PyPI)](https://pypi.org/project/tree-sitter-analyzer/1.7.1/) — example of multi-language code analyzer with plugin architecture

### Why tree-sitter was considered and rejected for C++ frontend

Tree-sitter is the modern de-facto multi-language parser. We considered it as the unified frontend for both Python and C++. **Rejected** because:
- Tree-sitter is **syntactic only** — no type resolution, no name binding, no scope analysis ([Cycode — Tree-sitter queries](https://cycode.com/blog/tips-for-using-tree-sitter-queries/))
- The Core Value of this lib is type-resolved `TypeDep` extraction — tree-sitter cannot produce it
- For Python, stdlib `ast` is already deterministic and sufficient; bringing tree-sitter adds a C dependency for no gain
- For C++, libclang provides real type resolution that tree-sitter-cpp cannot match

Recorded as Key Decision in PROJECT.md ("C++ 解析 = `clang.cindex` (libclang)"). Confidence: HIGH.

---

*Architecture research for: lib-code-parser v0.2.0 target architecture*
*Researched: 2026-05-24*
