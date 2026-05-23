# Technology Stack

**Analysis Date:** 2026-05-23

## Languages

**Primary:**
- Python >=3.11 - All library source (`lib_code_parser/`) and tests (`tests/`)

**Secondary:**
- Not applicable - This is a pure Python library

## Runtime

**Environment:**
- CPython 3.11+ (declared in `pyproject.toml` `requires-python = ">=3.11"` and CI matrix in `.github/workflows/ci.yml`)

**Package Manager:**
- `pip` (used for editable install via `pip install -e ".[dev]"`)
- Lockfile: missing (no `requirements.txt` or `poetry.lock`; only `pyproject.toml` declares dependencies)

## Frameworks

**Core:**
- No application framework - This is a standalone library; the only runtime dependency is `pydantic` for data modeling.

**Testing:**
- `pytest` >=8 - Test runner, configured via `[tool.pytest.ini_options]` in `pyproject.toml` (`testpaths = ["tests"]`)
- `pytest-cov` - Coverage reporting (dev extra)

**Build/Dev:**
- `setuptools` >=68 + `wheel` - PEP 517 build backend (`pyproject.toml` `[build-system]`)
- `ruff` - Linter and formatter (configured under `[tool.ruff]` and `[tool.ruff.lint]` with `select = ["E", "F", "I"]`, `line-length = 100`, `target-version = "py311"`)
- `pyright` - Static type checker (dev extra; no project config file detected)

## Key Dependencies

**Critical:**
- `pydantic` >=2.0 - All output models in `lib_code_parser/models.py` inherit from `pydantic.BaseModel` (`ArtifactId`, `FunctionNode`, `CallGraph`, `TypeDep`, `ContractInfo`, `CodeContent`, `NormalizedArtifact`, `ParserConfig`, etc.). Also the *target domain* the parser analyzes - `contract_extractor.py` recognizes `field_validator` / `model_validator` decorators from Pydantic v2.

**Infrastructure:**
- Python stdlib `ast` - Source parsing in `lib_code_parser/ast_extractor.py`, `callgraph_builder.py`, `contract_extractor.py`, `type_dep_builder.py`
- Python stdlib `re` - Trace tag extraction in `lib_code_parser/ast_extractor.py` (regex `Traces:\s*([A-Z]+-\d+...)`)
- Python stdlib `pathlib` - Module name resolution from file paths across all extractor modules

## Configuration

**Environment:**
- No environment variables required - The library is purely in-process; runtime behavior is configured exclusively via the `ParserConfig` pydantic model (`lib_code_parser/models.py`).
- `ParserConfig.params` dict keys recognized by `CodeParserExecutor.execute` (`lib_code_parser/executor.py`):
  - `language`: `"python"` | `"cpp"` (default `"python"`; `"cpp"` returns empty `CodeContent`)
  - `extract_contracts`: `bool` (default `True`)
- `ParserConfig.enabled`: `bool` (when `False`, executor returns empty `CodeContent` immediately)

**Build:**
- `pyproject.toml` - Single source of truth for build, packaging, dependency, lint, and test config
- `lib_code_parser.egg-info/` - Generated metadata from editable install (committed in tree; not source-controlled secrets)
- `.gitignore` - Excludes `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.pyright/`, `htmlcov/`, `.coverage`

## Platform Requirements

**Development:**
- Python 3.11+
- `pip install -e ".[dev]"` for editable install with `pytest`, `pytest-cov`, `ruff`, `pyright`
- OS-agnostic - All file I/O uses `pathlib`, no shell calls or OS-specific paths in library code

**Production:**
- Distributed as `pip install lib-code-parser` (per `README.md`)
- Pure-Python wheel - No native extensions, no C compilation step
- Target: any environment that can run CPython 3.11+ and import Pydantic 2.x

---

*Stack analysis: 2026-05-23*
