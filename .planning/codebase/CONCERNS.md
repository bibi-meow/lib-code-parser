# Codebase Concerns

**Analysis Date:** 2026-05-23

## Tech Debt

**Design documents are unfilled templates:**
- Issue: All `docs/00-07` and `docs/99-trace-matrix.md` files are template skeletons with placeholder text (`[要求の説明]`, `[FR の概要]`, `LIB-FR-01`, `#5-1`, etc.) — no concrete content. Git log shows commit `23f00cb docs(trace-matrix): fill FR→AT→Code→Test matrix for all 6 FR + 2 NFR` was followed by `ac62121 chore: remove all code and documentation (wrong implementation)` which wiped them. The current `feat: implement lib-code-parser v0.1.0` commit added code but did not refill design docs.
- Files: `docs/00-decision-log.md`, `docs/01-user-stories.md`, `docs/02-diagram-spec.md`, `docs/03-diagram-generation.md`, `docs/04-oss-selection.md`, `docs/05-requirements.md`, `docs/06-architecture.md`, `docs/07-spec.md`, `docs/99-trace-matrix.md`
- Impact: No documented FR IDs, no decision rationale, no traceability. The README references LIB-FR-NN style trace tags in docstrings but there is no list of what FR-01…FR-06 actually mean. Audit/review impossible from documentation alone — readers must reverse-engineer requirements from `tests/acceptance/test_fr0N_*.py` filenames.
- Fix approach: Backfill `99-trace-matrix.md` from the 6 acceptance test files (FR-01 function extraction → FR-06 disabled), then fill `05-requirements.md` with Gherkin scenarios reflecting actual test assertions. Document decisions in `00-decision-log.md` (e.g. "AST stdlib chosen over libCST", "qualified node_id format `module.Class.method`").

**Inline import inside hot path:**
- Issue: `lib_code_parser/executor.py` line 45 does `import pathlib` inside `execute()` instead of at module top
- Files: `lib_code_parser/executor.py:45`
- Impact: Minor perf hit on every call; inconsistent style — `Path` is already imported from `pathlib` in other modules at top level
- Fix approach: Move `from pathlib import Path` to module imports, drop the inline `import pathlib` and `pathlib.Path(path).suffix` to `Path(path).suffix`

**Mutable default values on Pydantic models:**
- Issue: `models.py` uses `= []` and `= ContractInfo()` directly as field defaults. Pydantic 2 handles this safely via copy semantics, but the pattern triggers `ruff B008`/`mutable-default` style warnings on stricter configs and conflicts with idiomatic `Field(default_factory=list)`
- Files: `lib_code_parser/models.py:14,28,29,35,37,39,40,49,50,60,62,74`
- Impact: Style noise; future ruff configs adding `B` ruleset will flag these
- Fix approach: Switch to `Field(default_factory=list)` and `Field(default_factory=ContractInfo)` for collection/model defaults

**Default `SourceRange(0, 0)` is semantically invalid:**
- Issue: `FunctionNode.source_range` defaults to `SourceRange(start_line=0, end_line=0)`. Python AST line numbers start at 1, so 0 is never a real value
- Files: `lib_code_parser/models.py:40`
- Impact: Downstream consumers may treat 0 as a valid line; sentinel checks need to know `start_line == 0` means "missing". No documentation states this convention.
- Fix approach: Either make `source_range` required (no default) or document the sentinel convention in the docstring and README

**No `py.typed` marker:**
- Issue: Package exports Pydantic models with full type hints but ships no `py.typed` file, so downstream `pyright`/`mypy` will not pick up type stubs
- Files: `lib_code_parser/` (missing `py.typed`)
- Impact: Consumers calling `executor.execute(...)` get `Any` returns under strict type checking
- Fix approach: Add empty `lib_code_parser/py.typed` file and `package_data = {"lib_code_parser": ["py.typed"]}` in `pyproject.toml`

**`pyproject.toml` lacks PyPI metadata:**
- Issue: No `authors`, `license`, `readme`, `urls`, `classifiers` keys. Package version 0.1.0 cannot be cleanly published.
- Files: `pyproject.toml:5-10`
- Impact: PyPI listing would be bare; downstream installers cannot see homepage / repo link
- Fix approach: Add `authors`, `readme = "README.md"`, `license = {text = "MIT"}`, `urls = {Repository = "https://github.com/bibi-meow/lib-code-parser"}`, and standard `classifiers`

## Known Bugs

**Nested classes and nested functions are silently dropped:**
- Symptoms: A source file containing `class Outer:\n    class Inner:\n        def foo(self): ...` will produce a `FunctionNode` for `mod.Outer` but no node for `mod.Outer.Inner` and no node for `mod.Outer.Inner.foo`. Functions defined inside other functions (closures) are also dropped.
- Files: `lib_code_parser/ast_extractor.py:66-116` (iterates only `tree.body` top-level, not recursive)
- Trigger: Any Python source with nested class or nested `def`
- Workaround: None at API level — consumers cannot retrieve nested entities
- Fix approach: Recurse into class bodies for nested classes; recurse into function bodies for nested defs. Update `node_id` qualification to handle arbitrary nesting (e.g. `mod.Outer.Inner.foo`).

**Contract extractor walks nested classes, function extractor does not — inconsistent attachment:**
- Symptoms: `contract_extractor.py` uses `ast.walk(tree)` (full recursion) and will produce `ContractInfo` for nested classes, but `extract_functions` only looks at top-level classes. In `executor.execute()`, the contract map is keyed by `class_id` (e.g. `mod.Outer.Inner`) but no matching `FunctionNode` exists, so the contract is computed and then **silently discarded**.
- Files: `lib_code_parser/contract_extractor.py:43` (uses `ast.walk`), `lib_code_parser/ast_extractor.py:66` (uses `tree.body` only), `lib_code_parser/executor.py:73-76` (attachment loop never finds the orphan key)
- Trigger: Nested class with `@field_validator` / `@model_validator`
- Workaround: Flatten classes to top level
- Fix approach: Either make both modules consistent (both recursive or both top-level) — recursive is the correct fix and aligns with the nested-class bug above

**`_collect_calls` attributes nested-function calls to the outer function:**
- Symptoms: A method `def foo(self):\n    def helper():\n        bar()\n    helper()` produces edges `foo → helper` AND `foo → bar` because `ast.walk(stmt)` recurses into the nested `def`. The `bar` call is logically inside `helper`, not `foo`.
- Files: `lib_code_parser/callgraph_builder.py:24-33` (`ast.walk` traverses unbounded)
- Trigger: Closures / nested defs that themselves make calls
- Workaround: None
- Fix approach: Replace `ast.walk` with manual traversal that stops at `FunctionDef`/`AsyncFunctionDef` boundaries, or pre-collect inner-function node IDs and exclude their bodies

**Call-graph callees are unqualified names — collisions silently merge:**
- Symptoms: `self.bar()` (method on self), `obj.bar()` (method on something else), and top-level `bar()` all produce identical `CallEdge.callee = "bar"`. No way to distinguish call targets in the output.
- Files: `lib_code_parser/callgraph_builder.py:15-21` (`_get_call_name` returns only the attribute name)
- Trigger: Any non-trivial method dispatch
- Workaround: Consumers must do their own resolution from `node_id` candidates
- Fix approach: Document the limitation explicitly in `README.md` (currently silent); or for `Attribute` calls, preserve the receiver expression text (e.g. `"self.bar"`) so consumers can disambiguate

**TypeDep collects every `Name` node in annotations, including builtins and generics:**
- Symptoms: `def foo(x: list[Optional[str]]) -> dict` produces `TypeDep` rows for `list`, `Optional`, `str`, `dict` — none of which are user-defined types. No deduplication: the same `(source, target, kind)` triple appears multiple times.
- Files: `lib_code_parser/type_dep_builder.py:63-72`
- Trigger: Any annotated function
- Workaround: Consumers must filter/deduplicate
- Fix approach: Maintain a builtin-typename blacklist (`list`, `dict`, `set`, `tuple`, `str`, `int`, `float`, `bool`, `bytes`, `Optional`, `Union`, `Any`, `Callable`, ...), and deduplicate the result list

**TraceTag regex requires uppercase prefix and numeric suffix:**
- Symptoms: `Traces: us-01` or `Traces: REQ_123` or `Traces: NFR-A1` are not recognized
- Files: `lib_code_parser/ast_extractor.py:27`
- Trigger: Non-standard ID schemes
- Workaround: Force IDs to match `[A-Z]+-\d+`
- Fix approach: Document the constraint in README (currently mentioned but not the explicit regex limit), or relax to `[A-Za-z][\w]*-[\w]+`

**`raw_content.decode("utf-8", errors="replace")` silently corrupts non-UTF-8:**
- Symptoms: A source file with cp932/latin-1 bytes that happen to be invalid UTF-8 gets replacement characters inserted, which may cause `ast.parse` to fail later with cryptic SyntaxError, or worse, parse incorrectly
- Files: `lib_code_parser/executor.py:59`
- Trigger: Non-UTF-8 source files
- Workaround: Pre-decode upstream
- Fix approach: Either accept a `str` overload, or use `errors="strict"` and let the caller see a clear `UnicodeDecodeError`

**Unhandled `SyntaxError` from `ast.parse`:**
- Symptoms: Malformed source bytes cause `executor.execute()` to raise `SyntaxError` with no wrapping or context about which file failed. No `ParserError` model in the public API.
- Files: `lib_code_parser/ast_extractor.py:58`, `callgraph_builder.py:38`, `contract_extractor.py:39`, `type_dep_builder.py:17` (`ast.parse(source)` everywhere unguarded)
- Trigger: Invalid Python source
- Workaround: Caller wraps `execute()` in try/except
- Fix approach: Wrap `ast.parse` in each extractor or in `executor.execute()`; return `NormalizedArtifact` with empty `CodeContent` plus a documented error field, or define a `ParseError` exception

**Unknown `language` param silently falls through to Python parsing:**
- Symptoms: `params={"language": "java"}` does not match `"cpp"` so the code proceeds to `ast.parse(java_source)` which then raises `SyntaxError`. No validation, no warning.
- Files: `lib_code_parser/executor.py:42-57` (only `"cpp"` is special-cased)
- Trigger: Future language params that haven't been implemented
- Workaround: Caller validates language string before invoking
- Fix approach: Whitelist supported languages; raise `ValueError("Unsupported language: ...")` for unknowns, or return empty `CodeContent`

**`test_h_extension_returns_empty` is a vacuous test:**
- Symptoms: Passes `b""` as source — the function would also return empty for any extension because there is no code to parse
- Files: `tests/unit/test_executor.py:118-122`
- Trigger: N/A — test does not actually exercise C++ short-circuit
- Workaround: N/A
- Fix approach: Pass a non-empty source like `b"int main() { return 0; }"` to verify the C++ skip path actually short-circuits before `ast.parse`

## Security Considerations

**`ast.parse` on arbitrary bytes is generally safe but not bounded:**
- Risk: An adversarial input could be a pathologically large or deeply nested source (e.g. 100k levels of nested parens) that triggers a `RecursionError` or exhausts memory in `ast.parse`/`ast.walk`. No size limit, no recursion guard.
- Files: `lib_code_parser/executor.py:59` (no `len(raw_content)` check), all extractor modules use `ast.walk`
- Current mitigation: None
- Recommendations: Add a configurable `max_source_bytes` (e.g. 1 MiB) in `ParserConfig.params`; check before `ast.parse`. Consider catching `RecursionError` and returning empty content with a logged warning.

**No input validation on `path` parameter:**
- Risk: `path` is used only to derive `module_name = Path(path).stem`. No path traversal or null-byte risk in the current implementation since the file is not opened, but if future revisions add file I/O the parameter must be sanitized.
- Files: `lib_code_parser/ast_extractor.py:14`, `callgraph_builder.py:11`, `contract_extractor.py:14`, `type_dep_builder.py:11`, `executor.py:47`
- Current mitigation: No file system access — path is only string-processed
- Recommendations: If future versions add `from_file(path)` API, validate against directory traversal and absolute paths upstream

## Performance Bottlenecks

**Multiple `ast.parse` calls per file:**
- Problem: `executor.execute()` parses the same source four times: once each in `extract_functions`, `build_callgraph`, `extract_contracts`, `build_type_deps`. For a 1k-line file this triples parse-time vs a single parse.
- Files: `lib_code_parser/executor.py:63-73`
- Cause: Each extractor independently calls `ast.parse(source)`
- Improvement path: Parse once in `executor.execute()`, pass the resulting `ast.Module` to each extractor. Requires changing extractor signatures from `(source, path)` to `(tree, path)` or adding `(tree=None, source=None)` overloads.

**`ast.walk` traverses entire tree multiple times per file:**
- Problem: `extract_contracts` walks the whole tree; `type_dep_builder.build_type_deps` walks twice (imports + annotations); for large files this is O(n) repeated work
- Files: `lib_code_parser/contract_extractor.py:43`, `lib_code_parser/type_dep_builder.py:22,45`
- Cause: Each pass is independent
- Improvement path: Combine walks into a single visitor pass using `ast.NodeVisitor` subclass; collect imports, annotations, classes, validators in one traversal

## Fragile Areas

**Contract attachment depends on string equality of `node_id`:**
- Files: `lib_code_parser/executor.py:73-76`
- Why fragile: If `extract_functions` and `extract_contracts` ever disagree about how to qualify a class (e.g. one uses `module.Class`, the other `module.Outer.Inner`), the attachment loop silently drops the contract with no error
- Safe modification: Always change both modules' `node_id` generation logic together; add an assertion test that every key in `contracts_map` matches at least one `FunctionNode.node_id`
- Test coverage: No test verifies the attachment loop actually attaches in the orphan case

**Module name derived from file stem only:**
- Files: `_get_module_name` duplicated in 4 files: `ast_extractor.py:12`, `callgraph_builder.py:11`, `contract_extractor.py:14`, `type_dep_builder.py:11`
- Why fragile: Two files with the same basename in different directories (`pkg_a/utils.py` and `pkg_b/utils.py`) produce identical `node_id` prefixes — collisions across a multi-file analysis. The lib is single-file by design, but consumers aggregating across files will get silent ID collisions.
- Safe modification: Document the single-file scope clearly; or add an optional `module_prefix` param to `ParserConfig.params`
- Test coverage: No test exercises cross-file ID collision

**Helper function duplication across four modules:**
- Files: `_get_module_name(path)` is reimplemented identically in `ast_extractor.py:12`, `callgraph_builder.py:11`, `contract_extractor.py:14`, `type_dep_builder.py:11`
- Why fragile: A change to module-naming rules requires updating four files; divergence is the bug pattern in the contract-attachment fragility above
- Safe modification: Extract to a shared `lib_code_parser/_paths.py` helper

## Scaling Limits

**Single-file API only — no batch interface:**
- Current capacity: One source file per `execute()` call
- Limit: Analyzing a repo of N files requires N executor invocations; no shared parser state, no incremental analysis, no caching
- Scaling path: Add a `execute_batch(configs_and_sources)` method or expose lower-level extractors so consumers can build pipelines

**No streaming / lazy iteration:**
- Current capacity: All output lists are materialized in memory
- Limit: A 100k-line file with 10k functions produces a single in-memory `list[FunctionNode]` of ~50 MiB Pydantic objects
- Scaling path: Add generator-style extractors (`yield FunctionNode(...)`)

## Dependencies at Risk

**`pydantic >= 2.0`:**
- Risk: Major-version pin only; Pydantic 3 (when released) may break field-default semantics
- Impact: Models construction breaks
- Migration plan: Tighten the pin to `pydantic>=2.0,<3.0` and add Pydantic-3 compatibility shim when v3 ships

**`urllib3 (2.3.0) or chardet (7.4.0.post1)/charset_normalizer (3.4.4) doesn't match a supported version!`:**
- Risk: Warning surfaced when running pytest in the local env. Not a direct dependency of this package (comes from `requests` in the parent Python install), but indicates the dev environment has dependency drift
- Impact: Local-only test noise; CI uses a clean ubuntu-latest image so the warning will not appear there
- Migration plan: N/A for this lib — env issue

## Missing Critical Features

**No C++ support despite `_CPP_EXTENSIONS` and `language="cpp"` accepted:**
- Problem: README and code accept `.cpp/.c/.h/.cc` and `language="cpp"` but always return empty `CodeContent`. Calling code cannot distinguish "C++ file, intentionally skipped" from "Python file, no functions found".
- Files: `lib_code_parser/executor.py:16,48-57`
- Blocks: Any consumer that needs cross-language function/call-graph extraction (which is part of the stated mission per README "Parse Python source files...")

**No way to retrieve decorator metadata:**
- Problem: `@staticmethod`, `@property`, `@classmethod`, `@dataclass`, custom decorators are not surfaced in `FunctionNode`. The contract extractor uses decorators to derive `ContractInfo`, but consumers cannot see what other decorators were present.
- Files: `lib_code_parser/ast_extractor.py:84-98`
- Blocks: Downstream analysis like "find all properties", "find all dataclasses", "find all functions decorated with `@app.route`"

**No `py.typed` marker (also under Tech Debt):**
- Problem: Types are not exported to downstream type checkers
- Blocks: Strict-typed consumer projects

**No CHANGELOG, CONTRIBUTING, SECURITY policy:**
- Problem: README is the only project metadata; no record of version history or contribution flow
- Blocks: External contributors / security disclosures

## Test Coverage Gaps

**Nested classes and nested functions are completely untested:**
- What's not tested: No test asserts behavior for `class Outer: class Inner: pass` or `def outer(): def inner(): pass`. The bug "nested entities silently dropped" is undetected by the test suite.
- Files: `tests/unit/test_ast_extractor.py`, `tests/acceptance/test_fr01_function_extraction.py`
- Risk: Behavior is undefined and may change without notice
- Priority: High — common Python pattern, current behavior is a silent data loss bug

**Call graph attribution of nested-function calls is untested:**
- What's not tested: No test asserts that calls inside an inner `def` are NOT attributed to the outer function
- Files: `tests/unit/test_callgraph_builder.py`, `tests/acceptance/test_fr02_callgraph.py`
- Risk: The current `ast.walk(stmt)` behavior misattributes; consumers may rely on the (wrong) edges
- Priority: High

**Cross-file `node_id` collision behavior is untested:**
- What's not tested: Two files `a/utils.py` and `b/utils.py` produce identical `utils.foo` IDs — no test exercises this aggregation case
- Files: All tests use one source per test
- Risk: Consumers aggregating across files get silent ID collisions
- Priority: Medium — current API is single-file by design

**`SyntaxError` / malformed source handling is untested:**
- What's not tested: No test passes invalid Python source to verify error behavior
- Files: All unit and acceptance tests use valid sources
- Risk: API contract for malformed input is undefined
- Priority: High — user-facing failure mode

**Unknown language strings are untested:**
- What's not tested: `params={"language": "java"}` behavior is not asserted; would currently fall through to Python parsing
- Files: `tests/acceptance/test_fr06_disabled.py:85-108` (only `cpp` is tested)
- Risk: Silent wrong-language parsing
- Priority: Medium

**Empty bytes through C++ extension is a vacuous test:**
- What's not tested: `test_h_extension_returns_empty` passes `b""` so the C++ short-circuit is not actually proven to fire before `ast.parse`
- Files: `tests/unit/test_executor.py:118-122`
- Risk: Refactor that breaks the C++ short-circuit might pass the test
- Priority: Low (cosmetic fix)

**No test for `extract_contracts` recursive walk vs `extract_functions` top-level walk inconsistency:**
- What's not tested: A nested class with `@field_validator` will have its contract computed but never attached
- Files: `tests/unit/test_contract_extractor.py`, `tests/unit/test_executor.py`
- Risk: Silent contract drop, same bug as nested-class extraction
- Priority: High

**No test exercises non-UTF-8 source bytes:**
- What's not tested: `errors="replace"` decode path
- Files: `tests/unit/test_executor.py:103-122`
- Risk: Encoding bugs go unnoticed
- Priority: Low — Python source is typically UTF-8

**No CI coverage gate:**
- What's not tested: `pytest-cov` is in `[project.optional-dependencies].dev` but `.github/workflows/ci.yml` never runs it
- Files: `pyproject.toml:13`, `.github/workflows/ci.yml:15-20`
- Risk: Coverage can silently regress
- Priority: Medium — add `pytest --cov=lib_code_parser --cov-fail-under=80` to CI

---

*Concerns audit: 2026-05-23*
