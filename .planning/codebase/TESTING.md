# Testing Patterns

**Analysis Date:** 2026-05-23

## Test Framework

**Runner:**
- `pytest >= 8` (`pyproject.toml:13`)
- Config: `pyproject.toml` `[tool.pytest.ini_options]` section — `testpaths = ["tests"]` (`pyproject.toml:19-20`). No separate `pytest.ini` or `conftest`-level config.

**Assertion Library:**
- Built-in Python `assert` statements only. No `unittest.TestCase`, no `pytest.assume`, no `hamcrest`.

**Coverage Tool:**
- `pytest-cov` is declared in optional dev dependencies (`pyproject.toml:13`) but **not invoked** by CI. Local-only.

**Run Commands:**
```bash
pip install -e ".[dev]"   # Install with dev extras (pytest, pytest-cov, ruff, pyright)
pytest                    # Run all tests (testpaths = ["tests"])
pytest --tb=short         # CI default (.github/workflows/ci.yml:16)
pytest tests/unit         # Only unit tests
pytest tests/acceptance   # Only acceptance / FR tests
pytest -k fr01            # Run a specific FR family by keyword
pytest --cov=lib_code_parser   # Local coverage report (not enforced)
```

## Test File Organization

**Location:**
- Tests live in a top-level `tests/` directory, **not** co-located with source. Source files in `lib_code_parser/` have no `_test.py` siblings.
- Two-tier layout under `tests/`:
  - `tests/unit/` — one file per source module
  - `tests/acceptance/` — one file per Functional Requirement (FR-01 … FR-06)

**Naming:**
- Unit tests mirror source filenames: `test_<module>.py` (e.g., `test_ast_extractor.py`, `test_callgraph_builder.py`, `test_contract_extractor.py`, `test_executor.py`, `test_type_dep_builder.py`).
- Acceptance tests use the FR id as prefix: `test_fr<NN>_<feature>.py` (e.g., `test_fr01_function_extraction.py`, `test_fr06_disabled.py`). Mapping traces back to `docs/05-requirements.md` and `docs/99-trace-matrix.md`.

**Structure:**
```
tests/
├── __init__.py
├── conftest.py                          # Shared EXAMPLE_SOURCE fixture
├── unit/
│   ├── __init__.py
│   ├── test_ast_extractor.py            # Mirrors lib_code_parser/ast_extractor.py
│   ├── test_callgraph_builder.py
│   ├── test_contract_extractor.py
│   ├── test_executor.py
│   └── test_type_dep_builder.py
└── acceptance/
    ├── __init__.py
    ├── test_fr01_function_extraction.py # FR-01
    ├── test_fr02_callgraph.py           # FR-02
    ├── test_fr03_type_deps.py           # FR-03
    ├── test_fr04_contracts.py           # FR-04
    ├── test_fr05_trace_tags.py          # FR-05
    └── test_fr06_disabled.py            # FR-06
```

## Test Structure

**Suite Organization:**
Tests are grouped into `Test<Aspect>` classes per behaviour area, each containing focused single-assertion methods. Example from `tests/unit/test_executor.py:29-53`:

```python
class TestExecutorBasic:
    def test_returns_normalized_artifact(
        self, executor: CodeParserExecutor, basic_config: ParserConfig
    ) -> None:
        result = executor.execute(basic_config, SIMPLE_SOURCE, "mod.py")
        assert result.artifact_id.path == "mod.py"
        assert result.artifact_type == "code"

    def test_functions_populated(
        self, executor: CodeParserExecutor, basic_config: ParserConfig
    ) -> None:
        result = executor.execute(basic_config, SIMPLE_SOURCE, "mod.py")
        assert len(result.content.functions) > 0
```

Class names describe the scenario family — `TestClassExtraction`, `TestMethodExtraction`, `TestTopLevelFunctionExtraction`, `TestImportDeps`, `TestAnnotationDeps`, `TestExecutorEdgeCases`, `TestCppNotSupported`, `TestPydanticContracts`, `TestPostInitContract`, `TestContractMinimal`.

**Patterns:**
- **Arrange-Act-Assert per test**, often inlined into 2–4 statements.
- **No setup/teardown**: tests rely on stateless functions or freshly constructed `CodeParserExecutor()` instances per test (fixture creates a new one each call).
- **One concept per test**: each `test_*` method asserts a single observable behaviour. Compound checks reuse helper builders, not branching logic.
- **`from __future__ import annotations`** at the top of every test file (`tests/unit/test_ast_extractor.py:3`, etc.).
- **Type annotations on test methods**: `(self) -> None` everywhere; fixtures typed with their return type (`def executor() -> CodeParserExecutor`).

## Mocking

**Framework:** None. There is **no use of `unittest.mock`, `pytest-mock`, monkeypatching, or stub fakes** anywhere in the test suite.

**Patterns:**
The parser operates on in-memory strings/bytes, so tests pass literal source code directly:

```python
def test_function_with_call(self) -> None:
    source = "def foo():\n    bar()\n"
    cg = build_callgraph(source, "mod.py")
    callee_names = {e.callee for e in cg.edges}
    assert "bar" in callee_names
```
(`tests/unit/test_callgraph_builder.py:34-38`)

For richer scenarios, multi-line triple-quoted strings are used (e.g., `tests/unit/test_contract_extractor.py:17-23`, `tests/unit/test_executor.py:60-65`).

**What to Mock:**
- Nothing. The library has no I/O, no network, no clock, no randomness — pure transformation from `(bytes, path) → NormalizedArtifact`.

**What NOT to Mock:**
- Never mock `ast.parse`, `pydantic.BaseModel`, or any stdlib component. Tests treat them as part of the contract.

## Fixtures and Factories

**Test Data:**
The canonical example source is centralized in `tests/conftest.py` (lines 8–60) as a module-level `EXAMPLE_SOURCE` string. It contains:
- A service class with documented methods and `Traces:` tags (`OrderService`)
- A Pydantic model with `@field_validator` and `@model_validator` (`OrderModel`)
- A top-level function with `Traces:` tags (`process_payment`)

This single fixture exercises FR-01 through FR-05 simultaneously.

**Fixture Definitions** (`tests/conftest.py:66-78`):
```python
@pytest.fixture
def example_source() -> str:
    return EXAMPLE_SOURCE

@pytest.fixture
def example_path() -> str:
    return EXAMPLE_PATH

@pytest.fixture
def example_raw() -> bytes:
    return EXAMPLE_SOURCE.encode("utf-8")
```

**Local fixtures per file** (executor tests at `tests/unit/test_executor.py:11-23`):
```python
@pytest.fixture
def executor() -> CodeParserExecutor:
    return CodeParserExecutor()

@pytest.fixture
def basic_config() -> ParserConfig:
    return ParserConfig(
        artifact_type="code",
        executor_lib="lib_code_parser",
        params={"language": "python", "extract_contracts": True},
        enabled=True,
    )
```

**Quirk — re-declaration in acceptance tests:**
Acceptance test files re-declare `example_source` and `example_path` fixtures locally and import `EXAMPLE_SOURCE` inside the fixture body (e.g., `tests/acceptance/test_fr01_function_extraction.py:10-18`), even though `conftest.py` already provides them. This is **redundant** — see CONCERNS.md if generated.

**Helper functions inside test modules:**
Acceptance tests define a small helper `_nodes_by_id(source, path) -> dict` (e.g., `test_fr01_function_extraction.py:21-23`, `test_fr05_trace_tags.py:21-23`) that wraps `extract_functions` and produces a lookup dict — kept module-private with leading underscore.

**Location:**
- Shared fixtures: `tests/conftest.py`
- Per-file fixtures: top of each test module under `tests/unit/` and `tests/acceptance/`
- No `factories/`, `fixtures/`, or `data/` subdirectories. Test inputs are inline strings.

## Coverage

**Requirements:** None enforced. CI (`.github/workflows/ci.yml`) runs `pytest --tb=short` only — no `--cov` flag and no coverage gate.

**View Coverage (local):**
```bash
pytest --cov=lib_code_parser --cov-report=term-missing
pytest --cov=lib_code_parser --cov-report=html   # writes htmlcov/
```
`htmlcov/` and `.coverage` are in `.gitignore` (`.gitignore:16-17`).

## Test Types

**Unit Tests** (`tests/unit/`):
- Scope: one source module per file; exercises **both public and private (`_`-prefixed) helpers** directly (see `test_ast_extractor.py:5-10` importing `_extract_annotation`, `_extract_trace_tags`, `_get_module_name`).
- Approach: tiny synthetic source fragments (1–5 lines) targeting one branch each.

**Acceptance Tests** (`tests/acceptance/`):
- Scope: one Functional Requirement (FR-01 … FR-06) per file. Each file traces a row in `docs/99-trace-matrix.md`.
- Approach: feed the canonical `EXAMPLE_SOURCE` through the **public** API surface only (`extract_functions`, `build_callgraph`, `build_type_deps`, `extract_contracts`, `CodeParserExecutor.execute`). Private helpers are not imported here.
- FR-06 (`test_fr06_disabled.py`) covers both the `enabled=False` short-circuit and the C++ language stub.

**Integration Tests:**
- Acceptance tests on `CodeParserExecutor.execute` (e.g., `test_fr06_disabled.py`) serve as integration tests — they exercise the orchestration of all four builders.

**E2E Tests:**
- Not used. The library has no entry-point script, no CLI, no service.

## Common Patterns

**Async Testing:**
- Not used. Although `ast_extractor.py` recognises `ast.AsyncFunctionDef`, the library itself is fully synchronous and tests do not use `pytest-asyncio`. Async-function inputs are tested as plain source strings: `source = "async def fetch(): pass\n"` (`tests/unit/test_ast_extractor.py:81`).

**Error Testing:**
- The library raises no custom exceptions, and tests do not use `pytest.raises`. Pydantic `ValidationError` propagation is assumed from upstream contract, not asserted.
- "Negative" behaviours are validated via the **empty-result convention** instead:
  ```python
  def test_empty_source(self) -> None:
      assert extract_contracts("", "mod.py") == {}
  ```
  (`tests/unit/test_contract_extractor.py:9-10`)

**Edge-Case Coverage Patterns:**
- Empty input: every builder has a `test_empty_source` or `test_empty` case.
- Disabled/short-circuit: `test_disabled_*` family (`test_fr06_disabled.py:23-82`) asserts every component of `CodeContent` is empty when `enabled=False`.
- Unsupported language: `test_cpp_extension_returns_empty`, `test_cpp_language_param_returns_empty` (`test_fr06_disabled.py:85-108`).
- Defensive identity: `test_no_duplicate_nodes` checks dedup invariants in the call graph (`test_fr02_callgraph.py:35-37`, `test_callgraph_builder.py:46-49`).

**Set-Based Assertions:**
Edges and nodes are converted to sets before assertion to make ordering irrelevant:
```python
callee_names = {e.callee for e in cg.edges}
assert "bar" in callee_names
```
(`tests/unit/test_callgraph_builder.py:37-38`)

Edge tuples assert exact `(caller, callee)` pairs:
```python
edge_pairs = {(e.caller, e.callee) for e in cg.edges}
assert ("order_service.OrderService.create_order", "_calculate_total") in edge_pairs
```
(`tests/acceptance/test_fr02_callgraph.py:45-49`)

## CI Integration

GitHub Actions (`.github/workflows/ci.yml`) runs on `push` and `pull_request`:

1. Python 3.11 setup
2. `pip install -e ".[dev]"`
3. `pytest --tb=short`
4. `ruff check .`
5. `ruff format --check .`

All four steps must pass for a green build. There is **no coverage gate, no pyright/mypy gate, and no matrix across Python versions** despite `pyright` being installed as a dev dep.

---

*Testing analysis: 2026-05-23*
