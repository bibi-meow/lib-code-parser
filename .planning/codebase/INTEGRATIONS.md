# External Integrations

**Analysis Date:** 2026-05-23

## APIs & External Services

**No external API calls or remote services are made by this library at runtime.**

- `lib_code_parser/executor.py` orchestrates only in-process work: `ast` parsing, decorator inspection, regex matching.
- No HTTP client (`requests`, `httpx`, `urllib3`) imported anywhere in `lib_code_parser/` or `tests/`.
- No SDK clients for SaaS providers (Stripe, AWS, OpenAI, Anthropic, Supabase, etc.) imported.

## Data Storage

**Databases:**
- Not applicable - The library does not persist data. It receives `raw_content: bytes` and a `path: str` parameter and returns a `NormalizedArtifact` pydantic model in-memory (see `CodeParserExecutor.execute` in `lib_code_parser/executor.py`).

**File Storage:**
- The library does **not** read from or write to disk. The caller is responsible for reading source files; the library accepts already-loaded `bytes` via `execute(config, raw_content, path)`. The `path` argument is used solely as a label (module-name derivation via `pathlib.Path(path).stem`) - no filesystem access.

**Caching:**
- None.

## Authentication & Identity

**Auth Provider:**
- Not applicable - No authentication is required. The library is a local-only code analysis tool with no network surface.

## Monitoring & Observability

**Error Tracking:**
- None. No Sentry, Datadog, or similar client.

**Logs:**
- No logging framework is initialized. Errors surface as raised exceptions (e.g. `ast.parse` may raise `SyntaxError`; `raw_content.decode("utf-8", errors="replace")` in `lib_code_parser/executor.py` swallows decode errors by substitution).

## CI/CD & Deployment

**Hosting:**
- Published to PyPI as `lib-code-parser` (per `README.md` install instructions: `pip install lib-code-parser`).
- Source repository: `https://github.com/bibi-meow/lib-code-parser` (per `README.md` dev section).

**CI Pipeline:**
- GitHub Actions (`.github/workflows/ci.yml`)
  - Trigger: `on: [push, pull_request]`
  - Runner: `ubuntu-latest`
  - Python: 3.11 (via `actions/setup-python@v5`)
  - Steps:
    1. `actions/checkout@v4`
    2. `pip install -e ".[dev]"`
    3. `pytest --tb=short`
    4. `ruff check .`
    5. `ruff format --check .`

## Environment Configuration

**Required env vars:**
- None. The library has no environment-variable surface.

**Secrets location:**
- Not applicable - No secrets are required or read.
- No `.env*` files exist in the repository.

## Webhooks & Callbacks

**Incoming:**
- None - The library exposes a single synchronous API (`CodeParserExecutor.execute`). There are no HTTP endpoints, message queue consumers, or webhook handlers.

**Outgoing:**
- None - The library makes no outbound calls.

## Domain-Level Integrations (Source Code Being Analyzed)

While the library itself has no runtime integrations, the *analyzed source* is expected to use specific patterns that the library recognizes:

- **Pydantic v2 decorators** - `contract_extractor.py` recognizes:
  - `field_validator`, `validator` → emitted as `ContractInfo.preconditions`
  - `model_validator` → emitted as `ContractInfo.invariants`
  - (Decorator name matching, not import-aware - see `_PRECONDITION_DECORATORS` and `_INVARIANT_DECORATORS` in `lib_code_parser/contract_extractor.py`)
- **Trace-tag comments** - `Traces: FR-01, US-22` lines inside docstrings; pattern `[A-Z]+-\d+` in `lib_code_parser/ast_extractor.py` `_extract_trace_tags`.

These are *parsing targets*, not external integrations - no traffic leaves the process.

---

*Integration audit: 2026-05-23*
