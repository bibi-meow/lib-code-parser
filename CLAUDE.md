<!-- GSD:project-start source:PROJECT.md -->
## Project

**lib-code-parser (spec_reviewer_code_parser)**

Python (現状) と C++ (新規) のソースコードから、構造化されたアーキテクチャ表現を
**決定論的に・最大忠実度で・spec 側と同形式で** 抽出する pip ライブラリ。
spec-reviewer パイプラインの `spec_code_verifier` (US-01/US-22) と `architecture_verifier`
(US-32) に物理アーキの入力を供給する Parser lib として機能する。

**Core Value:** **コードから抽出する全てのアーキ表現が、`lib-diagram-parser` が spec から抽出するものと
同形式で比較可能であること。** 物理 (code) と論理 (spec) の表現幅ギャップの解釈は
verifier (LLM agent) の責務であり、本 lib は事実抽出のみを担って決定論性を維持する。
これが崩れると Layer M bisimulation (構造一致判定) が成立せず、検証パイプライン全体が機能しない。

### Constraints

- **Tech stack**: Python `>=3.11` (上限なし; 3.13/3.14 サポート), Pydantic `>=2.13.0,<3.0`, stdlib `ast`, `pyright[nodejs]==1.1.409` (subprocess), `libclang==18.1.1` (in-process ctypes、厳密 pin)
  — spec と兄弟 libs の整合性。pyan3/ACL-2/callgraph.py は不採用 (spec 表記は Phase 1 で訂正)
- **Determinism**: LLM / network / clock / 動的解析を一切使わない。出力は `(raw_content, path, config)` の純粋関数
  — Layer M bisimulation の前提条件
- **I/O policy**: ライブラリは I/O・ログ出力・設定読込を一切行わない。呼び出し側が bytes + path を渡す
  — caller-agnostic 原則 (兄弟 libs と同じ規約)
- **Distribution**: 単一 pip パッケージ `spec_reviewer_code_parser`
  — リポジトリ作成済み、配布名確定
- **Schema compatibility**: Diagram 出力は `lib-diagram-parser` 互換 schema (物理側追加メタデータは optional フィールドで)
  — verifier が同形式で比較できることが Core Value の前提
- **言語**: Python と C++ を最初から対象。"Python-first, C++-later" の段階分けは取らない
  — user 指示 (2026-05-23 QUESTIONING)
- **アーキ重視**: 実装前にアーキを独立 phase で固定する
  — 内部疎結合 + lib-internal 呼び出し可能性が要件
- **既存資産**: v0.1.0 (commit cf7e7ec) を baseline とし、互換性破壊は Key Decisions に明示する場合のみ
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python >=3.11 - All library source (`lib_code_parser/`) and tests (`tests/`)
- Not applicable - This is a pure Python library
## Runtime
- CPython 3.11+ (declared in `pyproject.toml` `requires-python = ">=3.11"` and CI matrix in `.github/workflows/ci.yml`)
- `pip` (used for editable install via `pip install -e ".[dev]"`)
- Lockfile: missing (no `requirements.txt` or `poetry.lock`; only `pyproject.toml` declares dependencies)
## Frameworks
- No application framework - This is a standalone library; the only runtime dependency is `pydantic` for data modeling.
- `pytest` >=8 - Test runner, configured via `[tool.pytest.ini_options]` in `pyproject.toml` (`testpaths = ["tests"]`)
- `pytest-cov` - Coverage reporting (dev extra)
- `setuptools` >=68 + `wheel` - PEP 517 build backend (`pyproject.toml` `[build-system]`)
- `ruff` - Linter and formatter (configured under `[tool.ruff]` and `[tool.ruff.lint]` with `select = ["E", "F", "I"]`, `line-length = 100`, `target-version = "py311"`)
- `pyright` - Static type checker (dev extra; no project config file detected)
## Key Dependencies
- `pydantic` >=2.0 - All output models in `lib_code_parser/models.py` inherit from `pydantic.BaseModel` (`ArtifactId`, `FunctionNode`, `CallGraph`, `TypeDep`, `ContractInfo`, `CodeContent`, `NormalizedArtifact`, `ParserConfig`, etc.). Also the *target domain* the parser analyzes - `contract_extractor.py` recognizes `field_validator` / `model_validator` decorators from Pydantic v2.
- Python stdlib `ast` - Source parsing in `lib_code_parser/ast_extractor.py`, `callgraph_builder.py`, `contract_extractor.py`, `type_dep_builder.py`
- Python stdlib `re` - Trace tag extraction in `lib_code_parser/ast_extractor.py` (regex `Traces:\s*([A-Z]+-\d+...)`)
- Python stdlib `pathlib` - Module name resolution from file paths across all extractor modules
## Configuration
- No environment variables required - The library is purely in-process; runtime behavior is configured exclusively via the `ParserConfig` pydantic model (`lib_code_parser/models.py`).
- `ParserConfig.params` dict keys recognized by `CodeParserExecutor.execute` (`lib_code_parser/executor.py`):
- `ParserConfig.enabled`: `bool` (when `False`, executor returns empty `CodeContent` immediately)
- `pyproject.toml` - Single source of truth for build, packaging, dependency, lint, and test config
- `lib_code_parser.egg-info/` - Generated metadata from editable install (committed in tree; not source-controlled secrets)
- `.gitignore` - Excludes `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.pyright/`, `htmlcov/`, `.coverage`
## Platform Requirements
- Python 3.11+
- `pip install -e ".[dev]"` for editable install with `pytest`, `pytest-cov`, `ruff`, `pyright`
- OS-agnostic - All file I/O uses `pathlib`, no shell calls or OS-specific paths in library code
- Distributed as `pip install lib-code-parser` (per `README.md`)
- Pure-Python wheel - No native extensions, no C compilation step
- Target: any environment that can run CPython 3.11+ and import Pydantic 2.x
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Source modules: `snake_case.py` (e.g., `ast_extractor.py`, `callgraph_builder.py`, `contract_extractor.py`, `type_dep_builder.py`)
- Package directory uses underscores: `lib_code_parser/` (PEP 8 conformant), distribution name uses hyphens: `lib-code-parser`
- Test files: `test_<module>.py` for unit tests (`tests/unit/test_ast_extractor.py`), `test_fr<NN>_<feature>.py` for acceptance tests tied to FR ids (`tests/acceptance/test_fr01_function_extraction.py`)
- Public functions: `snake_case` verbs — `extract_functions`, `build_callgraph`, `build_type_deps`, `extract_contracts` (see `lib_code_parser/ast_extractor.py:56`, `callgraph_builder.py:36`)
- Private helpers: leading underscore `_snake_case` — `_get_module_name`, `_extract_annotation`, `_extract_trace_tags`, `_make_source_range`, `_extract_params`, `_get_call_name`, `_collect_calls`, `_collect_annotation_deps`, `_get_decorator_name`
- Boolean flags use `_flag` suffix in local variables: `extract_contracts_flag` (`lib_code_parser/executor.py:60`)
- `snake_case` everywhere — `module_name`, `class_id`, `method_id`, `func_id`, `trace_tags`, `from_module`, `param_names`, `edge_pairs`
- Module-level constants: `UPPER_SNAKE` with leading underscore for private — `_CPP_EXTENSIONS`, `_PRECONDITION_DECORATORS`, `_INVARIANT_DECORATORS` (frozenset literals); test fixtures use unprefixed `UPPER_SNAKE` — `EXAMPLE_SOURCE`, `EXAMPLE_PATH`, `EXAMPLE_MODULE`, `SIMPLE_SOURCE`
- Pydantic models: `PascalCase` nouns — `ArtifactId`, `TraceTag`, `SourceRange`, `ParamInfo`, `ContractInfo`, `FunctionNode`, `CallEdge`, `CallGraph`, `TypeDep`, `CodeContent`, `NormalizedArtifact`, `ParserConfig` (all in `lib_code_parser/models.py`)
- Classes: `PascalCase` — `CodeParserExecutor` (`lib_code_parser/executor.py:19`)
- Test classes: `Test<Subject>` PascalCase — `TestGetModuleName`, `TestExtractAnnotation`, `TestExtractFunctions`, `TestExecutorBasic`, `TestExecutorContracts`, `TestExecutorEdgeCases`, `TestDisabledExecutor`, `TestCppNotSupported`
## Code Style
- Tool: `ruff format` enforced by CI (`.github/workflows/ci.yml:20`)
- Line length: 100 chars (`pyproject.toml:23`)
- Target Python version: 3.11+ (`pyproject.toml:9`, `pyproject.toml:24`)
- Tool: `ruff check` enforced by CI (`.github/workflows/ci.yml:18`)
- Enabled rule groups: `E` (pycodestyle errors), `F` (Pyflakes), `I` (isort import sorting) — `pyproject.toml:27`
- Type checking: `pyright` listed in optional dev dependencies (`pyproject.toml:13`) — not enforced in CI but available
## Import Organization
- None. Always absolute imports from the package root (e.g., `from lib_code_parser.models import ParserConfig`). No relative imports (`from .models import ...`) anywhere in `lib_code_parser/`.
## Error Handling
- **No try/except blocks** anywhere in `lib_code_parser/`. Parser propagates exceptions from `ast.parse` (e.g., `SyntaxError`) directly to caller.
- **Empty-result defensive returns** for known unsupported cases: if `config.enabled` is False, or file extension is C/C++/H, the executor returns a `NormalizedArtifact` with empty `CodeContent` instead of raising (`lib_code_parser/executor.py:34-39`, `lib_code_parser/executor.py:51-57`).
- **Lenient byte decoding**: `raw_content.decode("utf-8", errors="replace")` replaces malformed UTF-8 instead of raising (`lib_code_parser/executor.py:59`).
- **None-coalescing for optional AST attributes**: `node.end_lineno if node.end_lineno is not None else node.lineno` (`lib_code_parser/ast_extractor.py:35`); `ast.get_docstring(node) or ""` (`ast_extractor.py:70`).
- **Pydantic validation** raises `ValidationError` at model construction — relied on for input contract enforcement, never caught.
## Logging
- The library is pure: input → output. No side effects, no logger calls, no print statements outside `README.md` examples.
- Callers are expected to log around the executor invocation.
## Comments
- Section/phase markers in multi-pass algorithms — e.g., `# First pass: process classes and their methods`, `# Second pass: top-level functions` (`lib_code_parser/ast_extractor.py:65, 100`); `# Classes and their methods`, `# Top-level functions` (`callgraph_builder.py:44, 58`); `# Import statements`, `# Type annotations in function parameters and return types` (`type_dep_builder.py:21, 44`).
- Edge-case explanations inline: `# __post_init__ counts as precondition` (`contract_extractor.py:55`); `# C++ not yet supported — return empty content` (`executor.py:52`); `# Only collect names starting with uppercase (class types) or builtins` (`type_dep_builder.py:65`).
- Type narrowing hints for static checkers: `# type: ignore[union-attr]` (`tests/unit/test_ast_extractor.py:30, 35`).
- Module-level docstring on every file — single-line purpose statement (e.g., `"""AST-based function/class/method extractor for Python source code."""`).
- Public function/class docstrings — one line summary, optionally followed by detail paragraphs. Example: `lib_code_parser/executor.py:28-33` documents return shape and edge cases.
- Private helpers (`_*`) get a single-line docstring describing intent (e.g., `"""Convert file path to module name (stem only)."""` at `ast_extractor.py:13`).
- No formal JSDoc/Sphinx markup. Plain prose only.
- `Traces: FR-NN` lines inside docstrings are domain-specific traceability tags consumed by this library itself (see `ast_extractor.py:_extract_trace_tags`).
## Function Design
- Most helpers are 5–15 lines. Largest function `extract_functions` is ~63 lines (`ast_extractor.py:56-118`) split into clearly labelled passes.
- Single responsibility per function — `_extract_annotation` only unparses, `_extract_params` only walks `ast.arguments`, `_collect_calls` only walks bodies.
- All public functions take primitive `source: str` and `path: str` (no file I/O inside library — caller decodes bytes upstream). `CodeParserExecutor.execute` is the only entry that accepts `bytes` and decodes internally.
- Default values only on optional behaviour flags: `skip_self_cls: bool = True` (`ast_extractor.py:40`).
- Type annotations required on every parameter and return value across all source modules.
- Always typed and explicit. Builders return concrete collections: `list[FunctionNode]`, `list[TypeDep]`, `dict[str, ContractInfo]`, `CallGraph`.
- Empty-input convention: return empty collection of the same shape (`[]`, `{}`, or `CallGraph(nodes=[], edges=[])`) — never `None`.
- Helpers that may produce nothing return `str | None` only when "absence" is semantically distinct from empty (`_get_call_name` at `callgraph_builder.py:15`).
## Module Design
- Package public API enumerated explicitly in `lib_code_parser/__init__.py:22-36` via `__all__`. Re-exports the executor plus every Pydantic model from `models.py`.
- Internal helpers (`extract_functions`, `build_callgraph`, `build_type_deps`, `extract_contracts`) are not in `__all__` but remain importable from their submodules for unit tests (`tests/unit/test_ast_extractor.py:5-10`).
- `__version__` defined as a module-level string in `__init__.py:20`.
- Single barrel at `lib_code_parser/__init__.py`. Submodules do not re-export each other; consumers either use the package barrel or import from the leaf module.
## Pydantic Model Conventions
- All data classes inherit from `pydantic.BaseModel` (`lib_code_parser/models.py`).
- Default values supplied with literal factories at field declaration: `refs: list[str] = []`, `params: list[ParamInfo] = []`, `contracts: ContractInfo = ContractInfo()`, `source_range: SourceRange = SourceRange(start_line=0, end_line=0)`. This relies on Pydantic v2's safe default-handling — do not replicate this pattern with stdlib `dataclasses`.
- No custom `field_validator` or `model_validator` is defined inside this library's own models (the library detects such validators in *parsed* code, but does not author them in its own models).
- `kind` discriminator fields are plain `str` with documented enum-like value sets via inline `# "function" | "method" | "class"` comments (`models.py:34`), not Python `Enum` types.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## System Overview
```text
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
- Stateless, pure-function extractors — each takes `(source: str, path: str)` and returns a typed value.
- Single public class (`CodeParserExecutor`) acts as the only orchestration point; extractors are module-level functions, not classes.
- Pydantic v2 `BaseModel` is the single shared data contract between layers.
- Library is **caller-agnostic**: no I/O, no configuration loading, no logging — the caller passes bytes and a path string.
- Determinism: all extraction is pure AST walking via the stdlib `ast` module (no LLM, no network).
## Layers
- Purpose: Stable import surface for pip consumers.
- Location: `lib_code_parser/__init__.py`
- Contains: Re-exports of `CodeParserExecutor` and all public models.
- Depends on: executor + models.
- Used by: External pip users.
- Purpose: Sequence the extractors, apply gating (enabled / language), assemble the final artifact.
- Location: `lib_code_parser/executor.py`
- Contains: Single class `CodeParserExecutor` with `execute(...)` method.
- Depends on: All four extractor modules + models.
- Used by: `__init__.py` (re-export) and external callers.
- Purpose: One module per analysis aspect; pure functions over AST.
- Location: `lib_code_parser/ast_extractor.py`, `callgraph_builder.py`, `type_dep_builder.py`, `contract_extractor.py`
- Contains: Module-level functions and small `_helper` functions.
- Depends on: stdlib `ast`, stdlib `pathlib`, stdlib `re`, and `models.py`.
- Used by: `executor.py` only.
- Purpose: Typed, immutable-by-convention data contracts.
- Location: `lib_code_parser/models.py`
- Contains: Pydantic `BaseModel` subclasses.
- Depends on: `pydantic` only.
- Used by: All extractor modules, the executor, and external callers.
## Data Flow
### Primary Request Path
### Trace-tag Extraction Flow
- None. All functions are pure; no caches, no module-level mutable state, no singletons.
- AST is re-parsed independently by each extractor (deliberate simplicity over performance).
## Key Abstractions
- Purpose: The single returned envelope; pairs an `ArtifactId` (path) with typed content.
- Examples: `lib_code_parser/models.py:65-68`
- Pattern: Anemic data container (Pydantic `BaseModel`).
- Purpose: Aggregate of the four extraction results (functions, call graph, type deps).
- Examples: `lib_code_parser/models.py:59-62`
- Pattern: Composition of model collections; defaults to empty lists/objects so the "disabled" / "C++" paths can return an inert value.
- Purpose: Canonical representation of any callable/class with metadata.
- Examples: `lib_code_parser/models.py:32-40`
- Pattern: Discriminator field `kind ∈ {"function", "method", "class"}` rather than subclasses.
- Purpose: Caller-supplied behavior flags (`enabled`, `params.language`, `params.extract_contracts`).
- Examples: `lib_code_parser/models.py:71-75`
- Pattern: Dict-of-untyped-params (`params: dict[str, object]`) for forward-compatibility with new languages/flags.
- Purpose: Convert a file path to a stable `node_id` prefix.
- Examples: `_get_module_name` is duplicated in `ast_extractor.py:12`, `callgraph_builder.py:11`, `type_dep_builder.py:11`, `contract_extractor.py:14`.
- Pattern: `Path(path).stem` — file-stem only, intentionally **not** a dotted package path.
## Entry Points
- Location: `lib_code_parser/executor.py:22`
- Triggers: Direct invocation by pip consumers.
- Responsibilities: Validate config gating, decode bytes, dispatch to extractors, merge results, return `NormalizedArtifact`.
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
### Re-parsing the AST per extractor
### `params: dict[str, object]` instead of typed config fields
### Implicit treatment of `__post_init__` as a Pydantic concept
## Error Handling
- Invalid Python source → `ast.parse` raises `SyntaxError`; the library lets it bubble up to the caller (no try/except anywhere).
- Non-UTF-8 bytes → silently replaced via `decode("utf-8", errors="replace")` (`executor.py:59`). Not an error condition.
- Pydantic validation failures on caller-supplied `ParserConfig` → `pydantic.ValidationError` raised at construction time.
- Disabled / unsupported-language paths → no error; return empty `CodeContent`.
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
