---
phase: 04-c-frontend-c-extractors
plan: 03
subsystem: frontend
tags: [libclang, clang.cindex, cpp, frontend, runtime-guard, det-02, lng-03, lng-05, dispatch]

# Dependency graph
requires:
  - phase: 04-01
    provides: language-nested dispatch; flat FRONTENDS dict[language, fn] with no cpp frontend yet
  - phase: 04-02
    provides: build_cpp_cav conftest helper + tests/fixtures/cpp/ corpus (missing_include.cpp etc.)
provides:
  - "frontends/cpp.py — the SINGLE libclang parse site for the C++ language path (build_cav) producing the cpp CAV"
  - "_ensure_libclang_ready D-07 lazy import-time runtime guard (DET-02 ABI pin + LNG-03 override rejection + dylib smoke test)"
  - "FRONTENDS['cpp'] registration — executor now selects the cpp frontend for cpp CAV"
affects: [04-04, 04-05, 04-06, 04-07, cpp-extractors, cpp-acceptance-tests]

# Tech tracking
tech-stack:
  added: []  # libclang already pinned in Phase 1; this plan is the first in-process production use
  patterns:
    - "Lazy idempotent runtime guard (_READY flag) so libclang loads ONCE at first cpp parse and never on the pure-Python path (D-07 no-I/O-at-import)"
    - "ABI pin via importlib.metadata.version only — never FFI-poke the libclang version function (Pitfall 2 segfault)"
    - "Single libclang parse site mirrors frontends/python.py structurally (swap ast.parse for Index.create().parse), config.compile_args consumed (inverts python.py signature-parity note)"

key-files:
  created:
    - lib_code_parser/frontends/cpp.py
    - tests/unit/frontends/test_cpp_guard.py
    - tests/unit/frontends/test_cpp_frontend.py
  modified:
    - lib_code_parser/_dispatch.py

key-decisions:
  - "D-06 honored: libclang is in-process ctypes in frontends/cpp.py; the module never imports or references the subprocess-only adapters layer (verified: literal 'adapters' substring absent)"
  - "D-07 honored: _ensure_libclang_ready runs once via the module-level _READY flag; build_cav calls it first; Python-only callers never import this module so libclang never loads on the pure-Python path"
  - "DET-02 via importlib.metadata.version('libclang') == '18.1.1'; NEVER FFI-pokes conf.lib.*.restype (Pitfall 2)"
  - "LNG-03 rejects Config.library_file override (set_library_file) and asserts Config.library_path resolves into the bundled clang/native/ dir; Index.create() smoke test raises clear RuntimeError + platform hint on dylib load failure"
  - "LNG-05 parses with ['-x','c++',*config.compile_args] + PARSE_INCOMPLETE; build_cav never inspects tu.diagnostics to raise — unresolved #include is a warning carried on the TranslationUnit"
  - "FRONTENDS['cpp'] = build_cav appended flat (Pitfall 1: not nested); FRONTENDS['python'] unchanged"

patterns-established:
  - "cpp frontend produces a CAV equivalent to the 04-02 test-side build_cpp_cav builder (same parse args, PARSE_INCOMPLETE, raw_content carried) — the production parse site downstream extractors will run against"

requirements-completed: [LNG-03, LNG-05, DET-02, LNG-04]

# Metrics
duration: 3min
completed: 2026-06-03
---

# Phase 4 Plan 03: C++ Frontend (libclang parse site + D-07 guard) Summary

**`frontends/cpp.py` is now the single libclang parse site for the C++ path: `build_cav` parses once via `Index.create().parse(...)` behind a lazy idempotent runtime guard that enforces the libclang 18.1.1 ABI pin (DET-02), rejects `Config.set_library_file` overrides + asserts the bundled `clang/native/` lib (LNG-03), and parses with `PARSE_INCOMPLETE` so unresolved `#include`s warn rather than error (LNG-05); `FRONTENDS["cpp"]` is registered.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-03T16:52:31Z
- **Completed:** 2026-06-03T16:55:15Z
- **Tasks:** 3
- **Files modified:** 4 (1 modified, 3 created)

## Accomplishments
- `frontends/cpp.py` mirrors `frontends/python.py` structurally: `from __future__ import annotations`, module docstring declaring it the ONLY libclang parse site (AST-05 analog) and that `config.compile_args` IS consumed, `__all__ = ["build_cav"]`.
- `_ensure_libclang_ready()` implements the verified RESEARCH §Code Examples skeleton: module-level `_READY=False` / `_EXPECTED_VERSION="18.1.1"`, `_platform_install_hint()` (darwin/win/Linux messages), guard body in order — `importlib.metadata.version("libclang")` equality (DET-02, no FFI), reject `Config.library_file is not None` (LNG-03 override rejection), assert `Config.library_path` contains a `native` segment, `Index.create()` smoke test raising `RuntimeError(... hint) from exc`, then `_READY=True`.
- `build_cav` decodes utf-8 `errors="replace"` verbatim from python.py, parses ONCE with `args=["-x","c++",*config.compile_args]`, `unsaved_files=[(path,source)]`, `options=TranslationUnit.PARSE_INCOMPLETE`, returns `CAV(language="cpp", path=path, payload=tu, raw_content=raw_content)`; never raises on `tu.diagnostics`. No `PARSE_DETAILED_PROCESSING_RECORD` (Pitfall 3), no `adapters/` import (D-06).
- `FRONTENDS["cpp"] = _build_cav_cpp` appended flat in `_dispatch.py` (Pitfall 1); `FRONTENDS["python"]` byte-unchanged.
- 9 new unit tests (guard + frontend) all green; full unit suite **334 passed, 1 skipped** (was 325+1 after 04-01 → +9 new cpp tests, zero regressions); ruff check + format clean on all touched files.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement frontends/cpp.py — lazy guard + single libclang parse site** - `1cb7c32` (feat)
2. **Task 2: Register FRONTENDS["cpp"] in _dispatch.py** - `0f7329f` (feat)
3. **Task 3: Guard + frontend behavior unit tests (LNG-03/DET-02/LNG-05)** - `65c9da1` (test)

_Tasks 1 & 3 were declared `tdd="true"`. Task 1's inline automated verify (one-liner asserting the parse + static no-FFI/no-detailed-record/no-adapters checks) gated GREEN; Task 3 added the persistent guard-failure and behavior tests that prove the RuntimeError paths and LNG-05 warn-not-error._

## Files Created/Modified
- `lib_code_parser/frontends/cpp.py` (created) - libclang `build_cav` single parse site + `_ensure_libclang_ready` D-07 guard + `_platform_install_hint`; module-level `from clang.cindex import Index, TranslationUnit` (acceptable — Python-only callers never import this module).
- `lib_code_parser/_dispatch.py` (modified) - appended `from lib_code_parser.frontends.cpp import build_cav as _build_cav_cpp  # noqa: E402` and `FRONTENDS["cpp"] = _build_cav_cpp` after the Python registrations; flat, append-only, `FRONTENDS["python"]` untouched.
- `tests/unit/frontends/test_cpp_guard.py` (created) - `test_abi_pin` (monkeypatch wrong version → RuntimeError), `test_rejects_set_library_file_override` (monkeypatch non-None `Config.library_file` → RuntimeError), `test_happy_path_sets_ready` (real env succeeds, `_READY` True); each failure test resets `_READY=False` first.
- `tests/unit/frontends/test_cpp_frontend.py` (created) - language="cpp", payload `TranslationUnit`, raw_content carry, utf-8 replace decode, path carry, and `test_missing_include_warns` using the `missing_include.cpp` fixture (no raise, `missing_header` diagnostic present, `Ok` struct cursor still built — LNG-05).

## Decisions Made
- Reset `_READY=False` explicitly at the top of each guard-failure test so the idempotency short-circuit cannot mask the failure path; the happy-path test runs last in file order and leaves `_READY=True` matching the real pinned/bundled environment.
- Monkeypatched `importlib.metadata.version` (the exact symbol the module calls) for the ABI-pin test and `clang.cindex.Config.library_file` for the override-rejection test — both reach the guard's real branch conditions without touching libclang internals.
- Module-level `from clang.cindex import Index, TranslationUnit` (not lazy) is acceptable per the plan/D-07: pure-Python callers never import `frontends/cpp.py`, so no-I/O-at-import is preserved for the Python path; the guard's first-parse `_READY` gate keeps the dylib smoke test from running until the first cpp parse.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reworded docstring/comment wording to satisfy Task 1's literal-substring static verify**
- **Found during:** Task 1 (running the inline automated verify)
- **Issue:** The Task 1 verify asserts `'restype' not in s` and `'adapters' not in s` against the raw `cpp.py` source text. My explanatory docstring/comments described the Pitfall-2 *intent* using the words `restype` (the FFI member to avoid) and `adapters` (the D-06 layer to avoid). The code never FFI-pokes `restype` and never imports the subprocess-only layer — but the literal words tripped the substring guard.
- **Fix:** Reworded the two comment passages to convey the same meaning without the literal substrings ("FFI-poke the libclang version function"; "the subprocess-only layer"). No behavior change; the intent (no FFI version poke, no `adapters/` usage) is unchanged and is the precise property the verify enforces.
- **Files modified:** lib_code_parser/frontends/cpp.py
- **Verification:** Task 1 verify one-liner prints `OK`; ruff check + format clean.
- **Committed in:** `1cb7c32` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** A wording-only adjustment required to pass the plan's own static guard; the substantive code (no FFI version poke, no `adapters/` import, no `PARSE_DETAILED_PROCESSING_RECORD`) matches the plan's must-haves exactly. No scope creep.

## Issues Encountered
- A `RequestsDependencyWarning` (urllib3/chardet version mismatch) prints during pytest collection — pre-existing environment noise unrelated to this plan; tests pass cleanly.
- Pre-existing untracked harness/planning artifacts (`.claude/gsd-*.json`, `.claude/scheduled_tasks.lock`, `04-PATTERNS.md`) are out of scope and were left untouched.

## User Setup Required
None - libclang 18.1.1 is already pinned/installed (verified `importlib.metadata.version("libclang") == "18.1.1"`, `Config.library_file is None`, `library_path` resolves into `clang\native`). No external service configuration required.

## Next Phase Readiness
- `FRONTENDS["cpp"]` is live: the executor selects `cpp.build_cav` for any cpp CAV, with a 0-line executor diff (D-01/D-03 from 04-01 already in place).
- Downstream cpp extractor plans (04-04..04-07) register into the reserved `PRIMITIVES["cpp"]` / `EVALUATIONS["cpp"]` sub-dicts and consume `cav.payload` (the libclang `TranslationUnit`) produced here; the production parse site now matches the 04-02 test-side `build_cpp_cav` contract (same args, `PARSE_INCOMPLETE`, raw_content carried).
- LNG-03/DET-02/LNG-05 enforcement points are established at the single parse site; no blockers.

## Self-Check: PASSED

- All 3 created files + 1 modified file verified present on disk.
- All 3 task commits verified in git history: `1cb7c32` (Task 1), `0f7329f` (Task 2), `65c9da1` (Task 3).

---
*Phase: 04-c-frontend-c-extractors*
*Completed: 2026-06-03*
