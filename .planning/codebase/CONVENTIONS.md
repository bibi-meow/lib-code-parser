# Coding Conventions

**Analysis Date:** 2026-05-23

## Naming Patterns

**Files:**
- Source modules: `snake_case.py` (e.g., `ast_extractor.py`, `callgraph_builder.py`, `contract_extractor.py`, `type_dep_builder.py`)
- Package directory uses underscores: `lib_code_parser/` (PEP 8 conformant), distribution name uses hyphens: `lib-code-parser`
- Test files: `test_<module>.py` for unit tests (`tests/unit/test_ast_extractor.py`), `test_fr<NN>_<feature>.py` for acceptance tests tied to FR ids (`tests/acceptance/test_fr01_function_extraction.py`)

**Functions:**
- Public functions: `snake_case` verbs — `extract_functions`, `build_callgraph`, `build_type_deps`, `extract_contracts` (see `lib_code_parser/ast_extractor.py:56`, `callgraph_builder.py:36`)
- Private helpers: leading underscore `_snake_case` — `_get_module_name`, `_extract_annotation`, `_extract_trace_tags`, `_make_source_range`, `_extract_params`, `_get_call_name`, `_collect_calls`, `_collect_annotation_deps`, `_get_decorator_name`
- Boolean flags use `_flag` suffix in local variables: `extract_contracts_flag` (`lib_code_parser/executor.py:60`)

**Variables:**
- `snake_case` everywhere — `module_name`, `class_id`, `method_id`, `func_id`, `trace_tags`, `from_module`, `param_names`, `edge_pairs`
- Module-level constants: `UPPER_SNAKE` with leading underscore for private — `_CPP_EXTENSIONS`, `_PRECONDITION_DECORATORS`, `_INVARIANT_DECORATORS` (frozenset literals); test fixtures use unprefixed `UPPER_SNAKE` — `EXAMPLE_SOURCE`, `EXAMPLE_PATH`, `EXAMPLE_MODULE`, `SIMPLE_SOURCE`

**Types:**
- Pydantic models: `PascalCase` nouns — `ArtifactId`, `TraceTag`, `SourceRange`, `ParamInfo`, `ContractInfo`, `FunctionNode`, `CallEdge`, `CallGraph`, `TypeDep`, `CodeContent`, `NormalizedArtifact`, `ParserConfig` (all in `lib_code_parser/models.py`)
- Classes: `PascalCase` — `CodeParserExecutor` (`lib_code_parser/executor.py:19`)
- Test classes: `Test<Subject>` PascalCase — `TestGetModuleName`, `TestExtractAnnotation`, `TestExtractFunctions`, `TestExecutorBasic`, `TestExecutorContracts`, `TestExecutorEdgeCases`, `TestDisabledExecutor`, `TestCppNotSupported`

## Code Style

**Formatting:**
- Tool: `ruff format` enforced by CI (`.github/workflows/ci.yml:20`)
- Line length: 100 chars (`pyproject.toml:23`)
- Target Python version: 3.11+ (`pyproject.toml:9`, `pyproject.toml:24`)

**Linting:**
- Tool: `ruff check` enforced by CI (`.github/workflows/ci.yml:18`)
- Enabled rule groups: `E` (pycodestyle errors), `F` (Pyflakes), `I` (isort import sorting) — `pyproject.toml:27`
- Type checking: `pyright` listed in optional dev dependencies (`pyproject.toml:13`) — not enforced in CI but available

## Import Organization

**Order** (enforced by ruff `I` rules):
1. `from __future__ import annotations` — present at the top of every source and test module
2. Standard library: `import ast`, `import re`, `from pathlib import Path`
3. Third-party: `from pydantic import BaseModel`, `import pytest`
4. First-party (local package): `from lib_code_parser.models import ...`, `from lib_code_parser.ast_extractor import ...`

A blank line separates each group. Example: `lib_code_parser/executor.py:3-14`, `tests/unit/test_executor.py:3-8`.

**Path Aliases:**
- None. Always absolute imports from the package root (e.g., `from lib_code_parser.models import ParserConfig`). No relative imports (`from .models import ...`) anywhere in `lib_code_parser/`.

## Error Handling

**Patterns:**
- **No try/except blocks** anywhere in `lib_code_parser/`. Parser propagates exceptions from `ast.parse` (e.g., `SyntaxError`) directly to caller.
- **Empty-result defensive returns** for known unsupported cases: if `config.enabled` is False, or file extension is C/C++/H, the executor returns a `NormalizedArtifact` with empty `CodeContent` instead of raising (`lib_code_parser/executor.py:34-39`, `lib_code_parser/executor.py:51-57`).
- **Lenient byte decoding**: `raw_content.decode("utf-8", errors="replace")` replaces malformed UTF-8 instead of raising (`lib_code_parser/executor.py:59`).
- **None-coalescing for optional AST attributes**: `node.end_lineno if node.end_lineno is not None else node.lineno` (`lib_code_parser/ast_extractor.py:35`); `ast.get_docstring(node) or ""` (`ast_extractor.py:70`).
- **Pydantic validation** raises `ValidationError` at model construction — relied on for input contract enforcement, never caught.

## Logging

**Framework:** None. The library performs no logging.

**Patterns:**
- The library is pure: input → output. No side effects, no logger calls, no print statements outside `README.md` examples.
- Callers are expected to log around the executor invocation.

## Comments

**When to Comment:**
- Section/phase markers in multi-pass algorithms — e.g., `# First pass: process classes and their methods`, `# Second pass: top-level functions` (`lib_code_parser/ast_extractor.py:65, 100`); `# Classes and their methods`, `# Top-level functions` (`callgraph_builder.py:44, 58`); `# Import statements`, `# Type annotations in function parameters and return types` (`type_dep_builder.py:21, 44`).
- Edge-case explanations inline: `# __post_init__ counts as precondition` (`contract_extractor.py:55`); `# C++ not yet supported — return empty content` (`executor.py:52`); `# Only collect names starting with uppercase (class types) or builtins` (`type_dep_builder.py:65`).
- Type narrowing hints for static checkers: `# type: ignore[union-attr]` (`tests/unit/test_ast_extractor.py:30, 35`).

**Docstrings:**
- Module-level docstring on every file — single-line purpose statement (e.g., `"""AST-based function/class/method extractor for Python source code."""`).
- Public function/class docstrings — one line summary, optionally followed by detail paragraphs. Example: `lib_code_parser/executor.py:28-33` documents return shape and edge cases.
- Private helpers (`_*`) get a single-line docstring describing intent (e.g., `"""Convert file path to module name (stem only)."""` at `ast_extractor.py:13`).
- No formal JSDoc/Sphinx markup. Plain prose only.
- `Traces: FR-NN` lines inside docstrings are domain-specific traceability tags consumed by this library itself (see `ast_extractor.py:_extract_trace_tags`).

## Function Design

**Size:**
- Most helpers are 5–15 lines. Largest function `extract_functions` is ~63 lines (`ast_extractor.py:56-118`) split into clearly labelled passes.
- Single responsibility per function — `_extract_annotation` only unparses, `_extract_params` only walks `ast.arguments`, `_collect_calls` only walks bodies.

**Parameters:**
- All public functions take primitive `source: str` and `path: str` (no file I/O inside library — caller decodes bytes upstream). `CodeParserExecutor.execute` is the only entry that accepts `bytes` and decodes internally.
- Default values only on optional behaviour flags: `skip_self_cls: bool = True` (`ast_extractor.py:40`).
- Type annotations required on every parameter and return value across all source modules.

**Return Values:**
- Always typed and explicit. Builders return concrete collections: `list[FunctionNode]`, `list[TypeDep]`, `dict[str, ContractInfo]`, `CallGraph`.
- Empty-input convention: return empty collection of the same shape (`[]`, `{}`, or `CallGraph(nodes=[], edges=[])`) — never `None`.
- Helpers that may produce nothing return `str | None` only when "absence" is semantically distinct from empty (`_get_call_name` at `callgraph_builder.py:15`).

## Module Design

**Exports:**
- Package public API enumerated explicitly in `lib_code_parser/__init__.py:22-36` via `__all__`. Re-exports the executor plus every Pydantic model from `models.py`.
- Internal helpers (`extract_functions`, `build_callgraph`, `build_type_deps`, `extract_contracts`) are not in `__all__` but remain importable from their submodules for unit tests (`tests/unit/test_ast_extractor.py:5-10`).
- `__version__` defined as a module-level string in `__init__.py:20`.

**Barrel Files:**
- Single barrel at `lib_code_parser/__init__.py`. Submodules do not re-export each other; consumers either use the package barrel or import from the leaf module.

## Pydantic Model Conventions

- All data classes inherit from `pydantic.BaseModel` (`lib_code_parser/models.py`).
- Default values supplied with literal factories at field declaration: `refs: list[str] = []`, `params: list[ParamInfo] = []`, `contracts: ContractInfo = ContractInfo()`, `source_range: SourceRange = SourceRange(start_line=0, end_line=0)`. This relies on Pydantic v2's safe default-handling — do not replicate this pattern with stdlib `dataclasses`.
- No custom `field_validator` or `model_validator` is defined inside this library's own models (the library detects such validators in *parsed* code, but does not author them in its own models).
- `kind` discriminator fields are plain `str` with documented enum-like value sets via inline `# "function" | "method" | "class"` comments (`models.py:34`), not Python `Enum` types.

---

*Convention analysis: 2026-05-23*
