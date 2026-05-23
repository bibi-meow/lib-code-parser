# Codebase Structure

**Analysis Date:** 2026-05-23

## Directory Layout

```
lib-code-parser/
├── LICENSE                          # MIT license
├── README.md                        # pip-user facing usage docs
├── pyproject.toml                   # Build, deps, ruff, pytest config
├── .gitignore                       # Standard Python ignores
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions: pytest + ruff
├── docs/                            # Design-time documents (SDD chain)
│   ├── README.md                    # Index of design docs
│   ├── 00-decision-log.md           # Design decisions + rationale
│   ├── 01-user-stories.md           # User stories
│   ├── 02-diagram-spec.md           # Diagram block specs
│   ├── 03-diagram-generation.md     # Diagram generation algorithm
│   ├── 04-oss-selection.md          # OSS choice rationale
│   ├── 05-requirements.md           # Functional requirements (LIB-FR)
│   ├── 06-architecture.md           # Module composition + DFD
│   ├── 07-spec.md                   # Public API + dataclass + pseudocode
│   └── 99-trace-matrix.md           # FR → AT → Code → Test traceability
├── lib_code_parser/                 # The actual library package
│   ├── __init__.py                  # Public re-exports + __version__
│   ├── executor.py                  # CodeParserExecutor (orchestrator)
│   ├── models.py                    # All Pydantic data models
│   ├── ast_extractor.py             # Function / class / method extraction
│   ├── callgraph_builder.py         # Static call graph builder
│   ├── type_dep_builder.py          # Type dependency extractor
│   └── contract_extractor.py        # Pydantic / dataclass validator extractor
└── tests/                           # All tests (pytest)
    ├── __init__.py
    ├── conftest.py                  # Shared EXAMPLE_SOURCE fixture
    ├── acceptance/                  # FR-level acceptance tests
    │   ├── __init__.py
    │   ├── test_fr01_function_extraction.py
    │   ├── test_fr02_callgraph.py
    │   ├── test_fr03_type_deps.py
    │   ├── test_fr04_contracts.py
    │   ├── test_fr05_trace_tags.py
    │   └── test_fr06_disabled.py
    └── unit/                        # Per-module unit tests
        ├── __init__.py
        ├── test_ast_extractor.py
        ├── test_callgraph_builder.py
        ├── test_contract_extractor.py
        ├── test_executor.py
        └── test_type_dep_builder.py
```

## Directory Purposes

**`lib_code_parser/` (package root):**
- Purpose: The published pip package — everything imported by consumers lives here.
- Contains: One module per extraction aspect plus the orchestrator and shared models. Flat layout (no submodules).
- Key files: `executor.py` (entry point), `models.py` (shared contract), `__init__.py` (public surface).

**`docs/`:**
- Purpose: Design documentation chain (Spec-Driven Development). Numbered 00–99 in the order they should be read.
- Contains: Decision log, user stories, requirements, architecture, API spec, trace matrix.
- Key files: `06-architecture.md`, `07-spec.md`, `99-trace-matrix.md`.

**`tests/`:**
- Purpose: All automated tests. Split into `acceptance/` (one file per functional requirement FR-01…FR-06) and `unit/` (one file per source module).
- Contains: Pytest test files and `conftest.py` shared fixtures.
- Key files: `conftest.py` (defines `EXAMPLE_SOURCE` used by acceptance tests).

**`.github/workflows/`:**
- Purpose: CI pipeline configuration.
- Contains: `ci.yml` running pytest + `ruff check` + `ruff format --check` on push/PR.

**`.planning/codebase/`:**
- Purpose: Generated codebase maps (this directory). Used by `/gsd:plan-phase` and `/gsd:execute-phase`.
- Contains: `ARCHITECTURE.md`, `STRUCTURE.md` (and other docs when other focus areas are mapped).
- Committed: Yes (intended as repo-tracked reference material).

## Key File Locations

**Entry Points:**
- `lib_code_parser/__init__.py`: Public re-exports — only symbols listed in `__all__` are part of the API.
- `lib_code_parser/executor.py`: `CodeParserExecutor.execute(...)` is the single runtime entry point.

**Configuration:**
- `pyproject.toml`: Build backend (`setuptools`), runtime deps (`pydantic>=2.0`), dev deps (`pytest`, `ruff`, `pyright`), ruff settings (`line-length=100`, `target-version=py311`, `select=["E","F","I"]`), pytest `testpaths=["tests"]`.
- `.github/workflows/ci.yml`: CI matrix (Python 3.11 only, Ubuntu only).

**Core Logic:**
- `lib_code_parser/executor.py`: Orchestrator + language/enabled gating.
- `lib_code_parser/ast_extractor.py`: FR-01 (function extraction) + FR-05 (trace tag extraction).
- `lib_code_parser/callgraph_builder.py`: FR-02 (call graph).
- `lib_code_parser/type_dep_builder.py`: FR-03 (type dependencies).
- `lib_code_parser/contract_extractor.py`: FR-04 (validator contracts).
- `lib_code_parser/models.py`: All Pydantic data contracts shared across the package.

**Testing:**
- `tests/conftest.py`: `EXAMPLE_SOURCE` constant + `example_source` / `example_path` / `example_raw` fixtures.
- `tests/acceptance/test_fr*.py`: Acceptance tests, one per FR.
- `tests/unit/test_*.py`: Unit tests, one per source module.

## Naming Conventions

**Files:**
- Library modules: `snake_case.py`, named after the noun-phrase of their responsibility (`ast_extractor.py`, `callgraph_builder.py`, `type_dep_builder.py`, `contract_extractor.py`).
- The orchestrator is named `executor.py` (not `code_parser.py`) — reflecting the "executor" role pattern from the broader `spec-reviewer-libs` family.
- Tests mirror sources: `test_<module>.py` (unit) or `test_fr<NN>_<feature>.py` (acceptance).
- Docs in `docs/` are numbered `NN-kebab-case.md` with `00-`…`07-` for the main chain and `99-` for the trace matrix.

**Directories:**
- Package dir uses `snake_case` (`lib_code_parser`) — matches PEP 8 package naming.
- The pip distribution name in `pyproject.toml` is `lib-code-parser` (kebab-case), per Python packaging convention.
- Test subdirectories use lowercase single-word names: `acceptance/`, `unit/`.

**Symbols:**
- Public classes use `PascalCase`: `CodeParserExecutor`, `FunctionNode`, `CallGraph`, `NormalizedArtifact`, `ParserConfig`.
- Internal helpers prefixed with `_`: `_get_module_name`, `_extract_annotation`, `_collect_calls`, `_make_source_range`, `_extract_params`, `_extract_trace_tags`, `_collect_annotation_deps`, `_get_call_name`, `_get_decorator_name`.
- Module-level constants use `_UPPER_SNAKE` with leading underscore: `_CPP_EXTENSIONS`, `_PRECONDITION_DECORATORS`, `_INVARIANT_DECORATORS`.
- Public functions exported as the module's primary verb: `extract_functions`, `build_callgraph`, `build_type_deps`, `extract_contracts`.

## Where to Add New Code

**New extraction aspect (e.g. complexity metrics, dead-code detection):**
- Primary code: `lib_code_parser/<aspect>_extractor.py` (or `<aspect>_builder.py` if it produces a graph-like output). Use a single public module-level function `extract_<aspect>(source: str, path: str) -> <ResultType>`.
- Models: Add the result type to `lib_code_parser/models.py`. Add it as a field on `CodeContent`.
- Wire-up: Call from `CodeParserExecutor.execute` in `lib_code_parser/executor.py`, after the existing extractors.
- Re-export: Add the new model class to `lib_code_parser/__init__.py` `__all__`.
- Tests: Add `tests/unit/test_<aspect>_extractor.py` and an acceptance file `tests/acceptance/test_fr<NN>_<aspect>.py` (next available FR number).

**New language support (e.g. real C++ parsing):**
- Do **not** add ad-hoc branches in existing extractors. Instead:
  - Add a new dispatch table or dict at module level in `executor.py` mapping `language → extractor_set`.
  - Implement a parallel module family (e.g. `cpp_ast_extractor.py`) returning the same `FunctionNode` / `CallGraph` / `TypeDep` shapes.
  - The existing `_CPP_EXTENSIONS` constant (`executor.py:16`) is the seam to extend.

**New `ParserConfig` option:**
- Preferred: Add a typed field on `ParserConfig` in `models.py` rather than another magic key in `params: dict[str, object]`. The existing `enabled: bool` field is the precedent.
- Read it in `executor.py`; never read it from inside extractors (extractors should remain pure functions of `(source, path)`).

**New shared utility (e.g. a stable module-name resolver):**
- Shared helpers: Create `lib_code_parser/_utils.py` (or extend `models.py`). The current `_get_module_name` duplication across 4 files is a known anti-pattern (see ARCHITECTURE.md) — fold new helpers into a single shared module rather than re-duplicating.

**New public model:**
- Definition: `lib_code_parser/models.py`. All public models live here, no submodules.
- Re-export: Add to both `__all__` in `lib_code_parser/__init__.py` and to the import block at the top of that file.

**New test:**
- Unit test for one module: `tests/unit/test_<module>.py` — import from `lib_code_parser.<module>` directly.
- Acceptance test for an FR: `tests/acceptance/test_fr<NN>_<short_name>.py` — use `EXAMPLE_SOURCE` from `tests.conftest` and call through `CodeParserExecutor` (end-to-end) or directly through the top-level extractor function.

## Special Directories

**`docs/`:**
- Purpose: Spec-Driven Development document chain. Read in numeric order.
- Generated: No — hand-authored.
- Committed: Yes.
- Notable: `99-trace-matrix.md` maps every FR → acceptance test → code module → unit test. Updating it is required when adding a new FR.

**`lib_code_parser.egg-info/`:**
- Purpose: Setuptools build metadata generated by `pip install -e .`.
- Generated: Yes (by setuptools).
- Committed: No (covered by `*.egg-info/` in `.gitignore`).

**`.pytest_cache/`, `.ruff_cache/`:**
- Purpose: Tool caches.
- Generated: Yes (by pytest / ruff).
- Committed: No (covered by `.gitignore`).

**`.claude/dynamic-prompt-harness/`:**
- Purpose: Local Claude Code session logs (per-developer artifact).
- Generated: Yes (by the dynamic-prompt-harness plugin).
- Committed: No (this directory exists locally; not part of the package distribution).

**`.planning/`:**
- Purpose: GSD planning artifacts including this codebase map.
- Generated: Yes (by `/gsd:map-codebase` and other GSD commands).
- Committed: Yes (intended as repo-tracked reference).

---

*Structure analysis: 2026-05-23*
