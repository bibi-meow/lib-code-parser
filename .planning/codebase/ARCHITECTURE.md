<!-- refreshed: 2026-05-23 -->
# Architecture

**Analysis Date:** 2026-05-23

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                  Caller (pip user / library consumer)        │
│                  Imports from `lib_code_parser`              │
└──────────────────────────────┬──────────────────────────────┘
                               │ execute(config, raw_content, path)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  CodeParserExecutor (Orchestrator)           │
│                  `lib_code_parser/executor.py`               │
│   - enabled / language gating                                │
│   - decodes bytes → str                                      │
│   - fans out to 4 extractor modules                          │
└──────┬──────────┬──────────┬──────────┬─────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│   AST    │ │ CallGraph│ │ TypeDep  │ │ Contract │
│Extractor │ │ Builder  │ │ Builder  │ │Extractor │
│          │ │          │ │          │ │          │
│`ast_     │ │`callgrap-│ │`type_dep │ │`contract-│
│extractor.│ │h_builder.│ │_builder. │ │_extracto-│
│py`       │ │py`       │ │py`       │ │r.py`     │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │
     ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Pydantic Data Models                       │
│                  `lib_code_parser/models.py`                 │
│   FunctionNode / CallGraph / TypeDep / ContractInfo /        │
│   CodeContent / NormalizedArtifact / ParserConfig            │
└──────────────────────────────┬──────────────────────────────┘
                               │ NormalizedArtifact
                               ▼
                          (returned to caller)
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `CodeParserExecutor` | Public entry-point class; orchestrates the four extractors and assembles `NormalizedArtifact` | `lib_code_parser/executor.py` |
| `extract_functions` | Walks Python AST to produce `FunctionNode` entries (classes, methods, top-level functions) with params, return types, docstrings, source ranges, and trace tags | `lib_code_parser/ast_extractor.py` |
| `build_callgraph` | Performs static AST analysis to emit `CallGraph` (nodes + caller→callee edges) | `lib_code_parser/callgraph_builder.py` |
| `build_type_deps` | Collects `TypeDep` from `import` / `from … import` statements and from type annotations on params/returns | `lib_code_parser/type_dep_builder.py` |
| `extract_contracts` | Detects Pydantic `field_validator` / `validator` / `model_validator` decorators and `__post_init__`; produces `ContractInfo` per class | `lib_code_parser/contract_extractor.py` |
| Data models | Pydantic `BaseModel` definitions shared by all extractors and exposed publicly | `lib_code_parser/models.py` |
| Public re-exports | Single import surface for pip users | `lib_code_parser/__init__.py` |

## Pattern Overview

**Overall:** Pipeline-of-extractors behind a single Orchestrator (Facade) class. Independent per-aspect AST passes feeding a shared Pydantic model.

**Key Characteristics:**
- Stateless, pure-function extractors — each takes `(source: str, path: str)` and returns a typed value.
- Single public class (`CodeParserExecutor`) acts as the only orchestration point; extractors are module-level functions, not classes.
- Pydantic v2 `BaseModel` is the single shared data contract between layers.
- Library is **caller-agnostic**: no I/O, no configuration loading, no logging — the caller passes bytes and a path string.
- Determinism: all extraction is pure AST walking via the stdlib `ast` module (no LLM, no network).

## Layers

**Public API layer:**
- Purpose: Stable import surface for pip consumers.
- Location: `lib_code_parser/__init__.py`
- Contains: Re-exports of `CodeParserExecutor` and all public models.
- Depends on: executor + models.
- Used by: External pip users.

**Orchestration layer:**
- Purpose: Sequence the extractors, apply gating (enabled / language), assemble the final artifact.
- Location: `lib_code_parser/executor.py`
- Contains: Single class `CodeParserExecutor` with `execute(...)` method.
- Depends on: All four extractor modules + models.
- Used by: `__init__.py` (re-export) and external callers.

**Extractor layer:**
- Purpose: One module per analysis aspect; pure functions over AST.
- Location: `lib_code_parser/ast_extractor.py`, `callgraph_builder.py`, `type_dep_builder.py`, `contract_extractor.py`
- Contains: Module-level functions and small `_helper` functions.
- Depends on: stdlib `ast`, stdlib `pathlib`, stdlib `re`, and `models.py`.
- Used by: `executor.py` only.

**Model layer:**
- Purpose: Typed, immutable-by-convention data contracts.
- Location: `lib_code_parser/models.py`
- Contains: Pydantic `BaseModel` subclasses.
- Depends on: `pydantic` only.
- Used by: All extractor modules, the executor, and external callers.

## Data Flow

### Primary Request Path

1. Caller constructs `ParserConfig` and calls `CodeParserExecutor().execute(config, raw_content, path)` (`lib_code_parser/executor.py:22`).
2. Executor checks `config.enabled` — if false, returns empty `NormalizedArtifact` immediately (`executor.py:34-39`).
3. Executor inspects file extension; if it matches `_CPP_EXTENSIONS`, returns empty `CodeContent` (`executor.py:47-57`).
4. Executor decodes `raw_content` bytes to UTF-8 string with `errors="replace"` (`executor.py:59`).
5. `extract_functions(source, path)` parses AST and emits `list[FunctionNode]` (`ast_extractor.py:56-118`).
6. `build_callgraph(source, path)` re-parses AST and emits `CallGraph` (`callgraph_builder.py:36-67`).
7. `build_type_deps(source, path)` re-parses AST and emits `list[TypeDep]` (`type_dep_builder.py:15-55`).
8. If `extract_contracts` flag is true, `extract_contracts(source, path)` re-parses AST and emits `dict[class_id, ContractInfo]`; executor merges these into matching `FunctionNode.contracts` (`executor.py:72-76`).
9. Executor wraps results in `NormalizedArtifact(artifact_id, artifact_type="code", content=CodeContent(...))` and returns (`executor.py:78-86`).

### Trace-tag Extraction Flow

1. `extract_functions` reads each class/function docstring via `ast.get_docstring(node)`.
2. `_extract_trace_tags(docstring)` applies the regex `Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)` (`ast_extractor.py:24-31`).
3. Matching IDs are split, stripped, and packed into `TraceTag(tag="Traces", refs=[...])`.
4. Tags are attached directly to the corresponding `FunctionNode.trace_tags`.

**State Management:**
- None. All functions are pure; no caches, no module-level mutable state, no singletons.
- AST is re-parsed independently by each extractor (deliberate simplicity over performance).

## Key Abstractions

**`NormalizedArtifact`:**
- Purpose: The single returned envelope; pairs an `ArtifactId` (path) with typed content.
- Examples: `lib_code_parser/models.py:65-68`
- Pattern: Anemic data container (Pydantic `BaseModel`).

**`CodeContent`:**
- Purpose: Aggregate of the four extraction results (functions, call graph, type deps).
- Examples: `lib_code_parser/models.py:59-62`
- Pattern: Composition of model collections; defaults to empty lists/objects so the "disabled" / "C++" paths can return an inert value.

**`FunctionNode`:**
- Purpose: Canonical representation of any callable/class with metadata.
- Examples: `lib_code_parser/models.py:32-40`
- Pattern: Discriminator field `kind ∈ {"function", "method", "class"}` rather than subclasses.

**`ParserConfig`:**
- Purpose: Caller-supplied behavior flags (`enabled`, `params.language`, `params.extract_contracts`).
- Examples: `lib_code_parser/models.py:71-75`
- Pattern: Dict-of-untyped-params (`params: dict[str, object]`) for forward-compatibility with new languages/flags.

**Module-name derivation:**
- Purpose: Convert a file path to a stable `node_id` prefix.
- Examples: `_get_module_name` is duplicated in `ast_extractor.py:12`, `callgraph_builder.py:11`, `type_dep_builder.py:11`, `contract_extractor.py:14`.
- Pattern: `Path(path).stem` — file-stem only, intentionally **not** a dotted package path.

## Entry Points

**`CodeParserExecutor.execute`:**
- Location: `lib_code_parser/executor.py:22`
- Triggers: Direct invocation by pip consumers.
- Responsibilities: Validate config gating, decode bytes, dispatch to extractors, merge results, return `NormalizedArtifact`.

**Public re-exports:**
- Location: `lib_code_parser/__init__.py`
- Triggers: `from lib_code_parser import …`
- Responsibilities: Expose `CodeParserExecutor` plus 11 model classes; nothing else is part of the public API.

## Architectural Constraints

- **Threading:** Single-threaded synchronous execution. No async / threading / multiprocessing inside the library. Caller may parallelize across files at their own discretion.
- **Global state:** None. No module-level mutables; the only module-level data are two `frozenset` constants (`_CPP_EXTENSIONS` in `executor.py:16`, `_PRECONDITION_DECORATORS` / `_INVARIANT_DECORATORS` in `contract_extractor.py:10-11`).
- **Circular imports:** None. Dependency graph is acyclic: `__init__` → `executor` → {extractors} → `models`.
- **AST is re-parsed four times per file:** Deliberate; each extractor takes raw `source: str` rather than a shared `ast.Module`. Trade-off: simpler unit testing vs. ~4× parse cost.
- **Language gating is hardcoded:** Only `"python"` is actually processed; `"cpp"` returns empty content. New languages require executor changes — there is no plugin/strategy registry.
- **Decoding policy is fixed:** `raw_content.decode("utf-8", errors="replace")` (`executor.py:59`) — non-UTF-8 bytes are silently substituted with `�`; not configurable.
- **Determinism guarantee:** No LLM, no I/O, no network, no clock. All outputs are a pure function of `(raw_content, path, config)`.

## Anti-Patterns

### Duplicated `_get_module_name` helper

**What happens:** The same one-line `Path(path).stem` helper is redefined in four extractor modules (`ast_extractor.py:12`, `callgraph_builder.py:11`, `type_dep_builder.py:11`, `contract_extractor.py:14`).
**Why it's wrong:** If module-naming policy ever changes (e.g. to dotted package paths), four files must be edited in lockstep; CONVENTIONS drift is a real risk.
**Do this instead:** Promote to a shared `lib_code_parser/_paths.py` (or add to `models.py` as a free function) and import everywhere.

### Re-parsing the AST per extractor

**What happens:** Each of the four extractors calls `ast.parse(source)` independently from `executor.execute` (`ast_extractor.py:58`, `callgraph_builder.py:38`, `type_dep_builder.py:17`, `contract_extractor.py:39`).
**Why it's wrong:** Wastes CPU on large source files; the AST is immutable and can be safely shared.
**Do this instead:** Have `executor.execute` call `ast.parse(source)` once and pass the `ast.Module` (plus `module_name`) to each extractor. Keeps extractors testable by allowing both signatures during transition.

### `params: dict[str, object]` instead of typed config fields

**What happens:** `ParserConfig.params` is an untyped dict; callers must use string keys `"language"` and `"extract_contracts"` (`models.py:74`, consumed in `executor.py:42, 60`).
**Why it's wrong:** No autocomplete, no validation, no schema — typos become silent defaults.
**Do this instead:** Introduce explicit fields (`language: Literal["python","cpp"] = "python"`, `extract_contracts: bool = True`) on `ParserConfig` itself, or a nested `ParserParams(BaseModel)`.

### Implicit treatment of `__post_init__` as a Pydantic concept

**What happens:** `contract_extractor.py:56-58` records `__post_init__` as a precondition unconditionally, even though it is a `dataclasses` (not Pydantic) hook.
**Why it's wrong:** README and module docstring frame contracts as "Pydantic validators"; mixing dataclass semantics in is undocumented and may surprise callers.
**Do this instead:** Either document explicitly that `__post_init__` is included for dataclass support, or split into a separate `dataclass_extractor` keyed off the decorator chain.

## Error Handling

**Strategy:** The library does **not** define custom exception types. It relies on stdlib exceptions to propagate.

**Patterns:**
- Invalid Python source → `ast.parse` raises `SyntaxError`; the library lets it bubble up to the caller (no try/except anywhere).
- Non-UTF-8 bytes → silently replaced via `decode("utf-8", errors="replace")` (`executor.py:59`). Not an error condition.
- Pydantic validation failures on caller-supplied `ParserConfig` → `pydantic.ValidationError` raised at construction time.
- Disabled / unsupported-language paths → no error; return empty `CodeContent`.

## Cross-Cutting Concerns

**Logging:** None. The library never prints, logs, or writes to stderr/stdout.
**Validation:** Performed by Pydantic at model-construction boundaries; the executor itself does no manual validation beyond `config.enabled` and language-detection.
**Authentication:** Not applicable — library is offline and stateless.
**Observability:** None built in. Callers wanting tracing must wrap `execute(...)`.
**Configuration:** All behavior driven by the `ParserConfig` argument; no env vars, no config files, no CLI.

---

*Architecture analysis: 2026-05-23*
