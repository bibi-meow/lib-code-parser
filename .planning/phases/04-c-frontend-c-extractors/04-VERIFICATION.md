---
phase: 04-c-frontend-c-extractors
verified: 2026-06-04T00:00:00Z
status: human_needed
score: 4/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Confirm CI mandatory matrix (Linux x86_64/aarch64 + Windows x86_64 x Py 3.11-3.14) runs all-green and macOS arm64 continue-on-error job runs on the first push/PR after Phase 4 completed"
    expected: "12 mandatory cells all green; macOS arm64 best-effort job runs with continue-on-error but does not gate the merge"
    why_human: "The YAML contract is structurally correct and verified below; actual cell execution (especially ubuntu-24.04-arm native aarch64 runner availability for this repo) requires a live CI run. The summary explicitly notes: 'the matrix can only be truly proven by an actual CI run'."
---

# Phase 4: C++ Frontend + C++ Extractors Verification Report

**Phase Goal:** Bring up the C++ track behind the same CAV boundary established in Phase 1: implement the libclang-based C++ Frontend with the `compile_args` contract, deliver C++ AST primitive extractors (functions / classes / includes / type info) producing output with full schema parity to the Python track, run all five diagram extractors on C++ CAV, and implement the Doxygen contract extractor (`\pre`/`\post`/`\invariant`) so Python and C++ produce symmetric contract output. Includes the platform CI matrix bring-up (mandatory: Linux x86_64/aarch64 + Windows x86_64 across Python 3.11-3.14; best-effort continue-on-error: macOS arm64 + Python 3.13/3.14).

**Verified:** 2026-06-04
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | CI matrix contract: mandatory all-green Linux x86_64/aarch64 + Windows x86_64 x Py 3.11-3.14 (no continue-on-error); macOS arm64 best-effort (continue-on-error: true) — YAML structure verifiable | ? UNCERTAIN (human) | YAML contract verified: `matrix.os: [ubuntu-latest, ubuntu-24.04-arm, windows-latest]` x `python-version: ["3.11","3.12","3.13","3.14"]`, `fail-fast: false`, no `continue-on-error` on mandatory job, `timeout-minutes: 20`. macOS job: `runs-on: macos-14`, `continue-on-error: true`, `matrix.python-version: ["3.13","3.14"]`. Runtime execution not verifiable without a live CI run. |
| 2 | `import lib_code_parser` loads the cpp frontend module (via `__init__` -> `executor` -> `_dispatch` -> `frontends/cpp.py`); calling `build_cav()` triggers the guard: ABI pin (importlib.metadata, not FFI), override rejection, platform-specific RuntimeError on load failure | VERIFIED | Module load chain confirmed: `"lib_code_parser.frontends.cpp" in sys.modules` after `import lib_code_parser` = True. `_ensure_libclang_ready`: version check at line 22, override check at line 31, `_READY` gate at line 45 — cheap checks run EVERY call (BL-02 addressed). Test `test_rejects_override_after_first_parse` with `_READY=True` passes. ABI-mismatch RuntimeError confirmed live. |
| 3 | `CodeParserExecutor().execute(config, raw, "src.cpp")` with language="cpp" yields a `NormalizedArtifact` whose `CodeContent` has identical Pydantic shape to Python output; all 5 diagram slots are `GraphModel` instances; unresolved `#include` surfaces as diagnostics warning, never a parse error | VERIFIED | `type(py_content) is type(cpp_content) is CodeContent` = True; `py_slots == cpp_slots` = True; all 5 diagram slots are `GraphModel` (live check). Unresolved `#include` test: 1 diagnostic severity=4 ("file not found"), no exception. `527 passed` in full test suite. |
| 4 | Doxygen `\pre`/`\post`/`\invariant` -> `ContractInfo` same schema as Python; `Traces:` extraction identical for Python docstrings and C++ Doxygen comments (TRC-03 parity) | VERIFIED | `test_schema_identical_to_python` in acceptance tests passes. `_TRACE_TAGS_RE.pattern` is byte-identical between `functions.py` and `_cpp_cursor.py`. `test_live_cpp_path_matches_python` passes. `SourceKind="doxygen"` in `ContractEntry` produced by `cpp_contracts.extract()`. `527 passed`. |
| 5 | `FRONTENDS["cpp"]`, `PRIMITIVES["cpp"]` (functions/call_graph/type_deps/contracts), `EVALUATIONS["cpp"]` (5 diagrams) are all registered in `_dispatch.py` | VERIFIED | Live registry check: `FRONTENDS: ['cpp', 'python']`, `PRIMITIVES['cpp']: ['call_graph', 'contracts', 'functions', 'type_deps']`, `EVALUATIONS['cpp']: ['class_diagram', 'component_diagram', 'package_diagram', 'sequence_diagram', 'state_diagram']`. Import-time slot guard for both EVALUATIONS and PRIMITIVES confirmed in `_dispatch.py:180-202`. |

**Score:** 4/5 truths verified (Truth 1 requires human CI confirmation)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `lib_code_parser/frontends/cpp.py` | C++ frontend + ABI guard | VERIFIED | 161 lines; `build_cav`, `_ensure_libclang_ready`, `_platform_install_hint`. BL-01/BL-02 fixes confirmed. |
| `lib_code_parser/_cpp_cursor.py` | Shared cursor helpers | VERIFIED | 147 lines; `_in_main_file` with `os.path.normcase/normpath` (CR-02 fix); `qualified_node_id` with `<anonymous@l:c>` synthetic segment (CR-01 fix); `field_relation` with cv-qualifier stripping (WR-03 fix). |
| `lib_code_parser/_dispatch.py` | Nested lang-dim dispatch | VERIFIED | `PRIMITIVES`/`EVALUATIONS` = `dict[str, dict[str, Fn]]`; `FRONTENDS` flat; cpp registrations present; import-time guard for both EVALUATIONS and PRIMITIVES keys. |
| `lib_code_parser/executor.py` | `cav.language` dispatch walk | VERIFIED | `PRIMITIVES[cav.language].items()`, `EVALUATIONS[cav.language].items()`; cpp suffix override. |
| `lib_code_parser/extractors/primitives/cpp_functions.py` | C++ function/class/method nodes | VERIFIED | Emits `FunctionNode` with kind/params/return_type/trace_tags/source_range; DET-04 sort-on-exit. |
| `lib_code_parser/extractors/primitives/cpp_callgraph.py` | C++ call graph | VERIFIED | `_collect_callees` stops at nested callable boundaries (WR-04 fix). DET-04 sort. |
| `lib_code_parser/extractors/primitives/cpp_type_deps.py` | C++ type deps + #includes | VERIFIED | `#include` via regex (no detailed-record macro pollution); member-type deps from FIELD_DECL; `source_line = cursor.extent.start.line` (WR-05 fix). |
| `lib_code_parser/extractors/primitives/cpp_contracts.py` | Doxygen \pre/\post/\invariant | VERIFIED | `_DOXY_RE` anchored with `re.MULTILINE` (WR-06 fix); prose `@pre` does NOT match; real commands do. |
| `lib_code_parser/extractors/evaluations/cpp_class_diagram.py` | C++ class diagram | VERIFIED | Inheritance + composes/aggregates/associates from `FIELD_DECL`; 5/5 acceptance tests pass. |
| `lib_code_parser/extractors/evaluations/cpp_sequence_diagram.py` | C++ sequence diagram | VERIFIED | Linear calls from cpp_callgraph; DET-04 sort. |
| `lib_code_parser/extractors/evaluations/cpp_component_diagram.py` | C++ component diagram | VERIFIED | `#include` imports from cpp_type_deps. |
| `lib_code_parser/extractors/evaluations/cpp_package_diagram.py` | C++ package diagram | VERIFIED | NAMESPACE cursors -> `node_type="package"` nodes with `parent_package` attribute. |
| `lib_code_parser/extractors/evaluations/cpp_state_diagram.py` | C++ state diagram (empty shape) | VERIFIED | Deliberately empty GraphModel (A1/D-05 parity-as-empty-shape); asserts TU payload; DET-04 sort tail. |
| `lib_code_parser/models/primitives/contracts.py` | `SourceKind` + `"doxygen"` | VERIFIED | Additive `"doxygen"` value in `SourceKind` Literal (D-08); existing 4 values unchanged. |
| `.github/workflows/ci.yml` | CI matrix structure | VERIFIED (YAML contract) | Mandatory job: `os: [ubuntu-latest, ubuntu-24.04-arm, windows-latest]` x `python-version: ["3.11","3.12","3.13","3.14"]`, no `continue-on-error`, `timeout-minutes: 20`. macOS job: `continue-on-error: true`, py 3.13/3.14, `timeout-minutes: 20`. Live run: human needed. |
| `tests/unit/frontends/test_cpp_guard.py` | Guard unit tests | VERIFIED | 5 tests; all `monkeypatch` (no global state leak — BL-01 fix); `test_rejects_override_after_first_parse` (BL-02); `test_expected_version_matches_pyproject_pin` (IN-04); all pass. |
| `tests/parity/test_cpp_python_schema_parity.py` | Schema parity tests | VERIFIED | `test_identical_codecontent_slots`, `test_identical_slot_types`, `test_diagram_slots_are_graphmodel_for_both`; all pass. |
| `tests/parity/test_trc03_cpp_parity.py` | TRC-03 parity tests | VERIFIED | `test_helper_byte_identical`, `test_regex_literal_byte_identical`, `test_live_cpp_path_matches_python`; all pass. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `lib_code_parser/__init__.py` | `lib_code_parser/frontends/cpp.py` | `__init__` -> `executor` -> `_dispatch` import chain | VERIFIED | `"lib_code_parser.frontends.cpp" in sys.modules` = True after `import lib_code_parser` |
| `frontends/cpp.py:_ensure_libclang_ready` | `importlib.metadata` | `importlib.metadata.version("libclang")` — NOT FFI | VERIFIED | Confirmed in source; `test_abi_pin` passes |
| `frontends/cpp.py:_ensure_libclang_ready` | `clang.cindex.Config.library_file` | Override rejection check — runs EVERY call (BL-02) | VERIFIED | Check at line 31, before `_READY` gate at line 45 |
| `_dispatch.py` | `frontends/cpp.py` | `FRONTENDS["cpp"] = _build_cav_cpp` | VERIFIED | Line 79 in `_dispatch.py` |
| `_dispatch.py` | `cpp_functions/callgraph/type_deps/contracts` | `PRIMITIVES["cpp"][*]` registrations | VERIFIED | Lines 94-105 in `_dispatch.py` |
| `_dispatch.py` | `cpp_*diagram` (5 extractors) | `EVALUATIONS["cpp"][*]` registrations | VERIFIED | Lines 167-171 in `_dispatch.py` |
| `executor.py` | `PRIMITIVES[cav.language]` / `EVALUATIONS[cav.language]` | Language-keyed walk (D-01) | VERIFIED | Lines 97, 127 in `executor.py` |
| `cpp_contracts.py` | `_cpp_cursor._TRACE_TAGS_RE` | Verbatim byte-identical regex (TRC-03) | VERIFIED | `_cpp_cursor._TRACE_TAGS_RE.pattern == functions._TRACE_TAGS_RE.pattern` = True |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `cpp_functions.py` | `by_id: dict[str, FunctionNode]` | `tu.cursor.walk_preorder()` | Yes — FUNCTION_DECL / CXX_METHOD / CLASS_DECL cursors | FLOWING |
| `cpp_contracts.py` | `result: dict[str, ContractInfo]` | `cursor.raw_comment` via `_DOXY_RE` | Yes — anchored regex on actual Doxygen comments | FLOWING |
| `cpp_class_diagram.py` | `nodes, edges: list[GraphNode/GraphEdge]` | `CXX_BASE_SPECIFIER` + `FIELD_DECL` children | Yes — inheritance + field relation classification | FLOWING |
| `cpp_type_deps.py` | `raw_deps: list[TypeDep]` | `_INCLUDE_RE` on `cav.raw_content` + FIELD_DECL | Yes — `#include` regex + member types | FLOWING |
| `cpp_state_diagram.py` | empty `GraphModel` | None (D-05 deliberate empty) | N/A — parity-as-empty-shape by design | FLOWING (intentional empty) |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full pytest suite | `pytest -q --tb=short` | 527 passed in 21.77s | PASS |
| FRONTENDS/PRIMITIVES/EVALUATIONS["cpp"] registrations | `python -c "from lib_code_parser._dispatch import FRONTENDS, PRIMITIVES, EVALUATIONS; ..."` | All 3 have "cpp" key; PRIMITIVES["cpp"] has 4 slots; EVALUATIONS["cpp"] has 5 slots | PASS |
| C++ execute returns CodeContent with GraphModel diagrams | Live spot-check with `src.cpp` | All 5 diagram slots are GraphModel instances | PASS |
| Unresolved #include produces diagnostic, not exception | `build_cav(b'#include <nonexistent.h>...', 'test.cpp', config)` | 1 diagnostic, severity=4, no exception | PASS |
| Doxygen @pre/@post/@invariant extraction | `cpp_contracts.extract(cav, config)` on annotated source | ContractInfo with 3 entries, source_kind="doxygen" | PASS |
| TRC-03 parity: regex patterns byte-identical | `functions._TRACE_TAGS_RE.pattern == _cpp_cursor._TRACE_TAGS_RE.pattern` | True | PASS |
| ABI guard rejects wrong version | `build_cav` with patched metadata returning "99.0.0" | RuntimeError "ABI pin violated" | PASS |
| Per-call override check (BL-02) | `_ensure_libclang_ready` with `_READY=True, library_file="/override"` | RuntimeError "override is rejected" | PASS |
| CI YAML mandatory matrix structure | Inspect `.github/workflows/ci.yml` | `os: [ubuntu-latest, ubuntu-24.04-arm, windows-latest]`, `python-version: [3.11-3.14]`, no `continue-on-error` on mandatory job, `timeout-minutes: 20` | PASS (contract) |
| CI YAML macOS best-effort job | Inspect `.github/workflows/ci.yml` | `continue-on-error: true`, `macos-14`, py 3.13/3.14, `timeout-minutes: 20` | PASS (contract) |

---

### Requirements Coverage

| Requirement | Description | Phase 4 Plan | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| LNG-01 | Library installs/runs on CPython 3.11-3.14 on Linux x86_64/aarch64 + Windows x86_64 (mandatory CI) | 04-07 | VERIFIED (contract) | CI YAML mandatory matrix: 3 OS x 4 Python = 12 cells, no `continue-on-error`, `timeout-minutes: 20`. Live run: human needed. |
| LNG-02 | macOS arm64 + Python 3.13+ best-effort (continue-on-error) | 04-07 | VERIFIED (contract) | CI YAML `macos-arm64-best-effort` job: `continue-on-error: true`, `macos-14`, py 3.13/3.14. Live run: human needed. |
| LNG-03 | Library import triggers guard: `Index.create()` once; RuntimeError on load failure with platform hint | 04-03 | VERIFIED | `frontends/cpp.py:_ensure_libclang_ready` runs on every `build_cav` call; platform hint function present for darwin/win/linux; 5 guard tests pass. `import lib_code_parser` loads `frontends/cpp.py` transitively. D-07: `Index.create()` is lazy (gated by `_READY`), not at module-import time. |
| LNG-04 | All AST primitives + 5 diagrams work on C++ with schema parity | 04-01, 04-04, 04-06 | VERIFIED | `type(py_content) is type(cpp_content) is CodeContent` = True. All 5 diagram slots are `GraphModel`. 527 tests pass. |
| LNG-05 | C++ extractors accept `compile_args`; unresolved `#include` -> warning not error | 04-03 | VERIFIED | `build_cav` forwards `config.compile_args` verbatim with `PARSE_INCOMPLETE`; missing-include test: 1 diagnostic, no exception. |
| SPC-03 | C++ Doxygen `\pre`/`\post`/`\invariant` -> `ContractInfo` same schema as Python | 04-05 | VERIFIED | `SourceKind="doxygen"` additive (D-08); `ContractEntry` same schema; 9 acceptance tests pass; `test_schema_identical_to_python` passes. |
| DET-02 | `libclang==18.1.1` ABI pin enforced; `Config.set_library_file` override rejected; version via `importlib.metadata` (not FFI) | 04-03 | VERIFIED | `importlib.metadata.version("libclang")` at line 22; `Config.library_file is not None` check at line 31; cheap checks run EVERY call (before `_READY` gate at line 45); `_EXPECTED_VERSION` == pyproject pin (test_expected_version_matches_pyproject_pin passes). |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `lib_code_parser/extractors/evaluations/cpp_state_diagram.py` | 66-72 | Sort no-ops on always-empty lists | Info | Deliberate by design (A1/D-05 parity-as-empty-shape). IN-03 from REVIEW accepted. Docstring explicitly states this is intentional. |
| `lib_code_parser/frontends/cpp.py` | 43 | `_EXPECTED_VERSION = "18.1.1"` duplicates `pyproject.toml` pin | Info | IN-04 addressed: `test_expected_version_matches_pyproject_pin` asserts the two stay in sync and fails CI on drift. |
| `lib_code_parser/_cpp_cursor.py` | — | `_get_module_name` is NOT duplicated here — uses `_paths.py` | Info (positive) | `cpp_type_deps.py` and `cpp_component_diagram.py` both import `from lib_code_parser._paths import get_module_name`. ARC-04 single-source respected on the cpp path. |

No TBD, FIXME, XXX, or unreferenced debt markers found in Phase 4 modified files.

---

### Context Decision Compliance

| Decision | Requirement | Implemented | Evidence |
|----------|-------------|-------------|---------|
| D-01: PRIMITIVES/EVALUATIONS nested `dict[language, dict[name, fn]]` | Dispatch parity | Yes | `_dispatch.py:51,54`; executor walks `PRIMITIVES[cav.language]` |
| D-02: FRONTENDS stays flat `dict[language, fn]` | Single frontend per language | Yes | `FRONTENDS: dict[str, FrontendFn]` flat; never double-nested |
| D-03: executor body: only walk headers changed | Open-Closed | Yes | `executor.py` line 97 and 127 only; all other lines unchanged |
| D-05: unresolved #include -> diagnostics warning | LNG-05 | Yes | `PARSE_INCOMPLETE`; no exception on missing header |
| D-06: libclang in-process in `frontends/cpp.py`, NOT in `adapters/` | In-process ctypes | Yes | `adapters/` not touched; no subprocess in cpp path |
| D-07: guard runs at C++ frontend module import (lazy `_READY`) | LNG-03 | Partially — cpp module is loaded at `import lib_code_parser`; `Index.create()` fires on first `build_cav` call, not at module import time | D-07 explicitly states "lazy load" is the design choice; CONTEXT.md says "LNG-03の「library import triggers guard」は「C++ frontend module の import」と解釈する" — i.e. the module being loaded (not `Index.create()`) satisfies the ROADMAP SC#2 intent |
| D-08: `SourceKind` additive `"doxygen"` value | SPC-03 | Yes | `contracts.py:31` — existing 4 values unchanged |
| D-09: `CodeContent.contracts` shared slot; TRC-03 regex verbatim | Doxygen parity | Yes | `_cpp_cursor._TRACE_TAGS_RE.pattern == functions._TRACE_TAGS_RE.pattern`; same slot name |

---

### Human Verification Required

#### 1. CI Mandatory Matrix Live Run

**Test:** Push or open a PR after Phase 4 completion and confirm the GitHub Actions `test` job matrix runs.

**Expected:**
- All 12 mandatory cells (3 OS x 4 Python versions) complete with no cell failures
- The `macos-arm64-best-effort` job runs and is marked as `continue-on-error: true` (failures allowed)
- The `ubuntu-24.04-arm` runner label successfully provisions for this repository; if not, the YAML comment documents the QEMU + `quay.io/pypa/manylinux2014_aarch64` fallback

**Why human:** The YAML contract (matrix structure, job configuration, timeout settings) is verified above. However, actual CI cell execution — particularly (a) whether `ubuntu-24.04-arm` is available for this repo and (b) whether `libclang==18.1.1` loads on all cells — requires a live run. The Phase 07 SUMMARY explicitly notes: "the matrix can only be truly proven by an actual CI run."

---

### Gaps Summary

No gaps. All 7 Phase 4 requirements (LNG-01, LNG-02, LNG-03, LNG-04, LNG-05, SPC-03, DET-02) have substantive implementation with passing tests. The single human verification item (live CI run) is a runtime confirmation of the structurally sound YAML contract, not a code gap.

**Review findings status:** The 04-REVIEW.md documents 12 findings (2 critical, 2 blocker, 6 warning, 4 info). All critical/blocker/warning findings are addressed in the actual codebase:
- CR-01 (anonymous decl ids): `<anonymous@l:c>` synthetic segment in `_cpp_cursor.py:107-111`
- CR-02 (path normalization): `os.path.normcase(os.path.normpath(...))` in `_cpp_cursor.py:63-66`
- BL-01 (test state leak): all guard tests use `monkeypatch` exclusively
- BL-02 (per-call checks): cheap checks precede the `_READY` gate in `cpp.py`
- WR-03 (cv-qualifier stripping): `const`/`volatile` stripped in `field_relation`
- WR-04 (lambda double-counting): `_NESTED_CALLABLE_KINDS` boundary stop in `cpp_callgraph.py`
- WR-05 (line provenance consistency): `extent.start.line` used in `cpp_type_deps.py:110`
- WR-06 (`_DOXY_RE` anchoring): anchored pattern with `re.MULTILINE` in `cpp_contracts.py:60-63`
- IN-01 (PRIMITIVES guard): `_KNOWN_PRIMITIVES` assertion at `_dispatch.py:195-202`
- IN-04 (version string single source): `test_expected_version_matches_pyproject_pin` test
- IN-02, IN-03: acknowledged by-design, documented in code comments

---

_Verified: 2026-06-04_
_Verifier: Claude (gsd-verifier)_
