---
phase: 01-architecture-foundation-spec-correction
plan: 07
subsystem: infra
tags: [subprocess, hardening, adapter, abc, determinism, pyright-prep, libclang-prep]

# Dependency graph
requires:
  - phase: 01-architecture-foundation-spec-correction
    provides: pydantic + project layout (plans 01-01 through 01-06 do not gate plan 01-07 — depends_on=[] in frontmatter)
provides:
  - lib_code_parser/adapters/base.py — run_subprocess() helper enforcing all 6 DET-05 hardening invariants
  - lib_code_parser/adapters/base.py — SubprocessAdapter abstract base class (tool_argv + parse_output, concrete execute() template)
  - lib_code_parser/adapters/__init__.py — package barrel re-exporting run_subprocess + SubprocessAdapter
  - tests/unit/adapters/ — 15 live-subprocess Wave 0 tests proving the 6 hardening invariants and the ABC contract
affects:
  - Phase 2 PyrightAdapter implementation (will subclass SubprocessAdapter)
  - Any future C++ tool adapter (libclang in-process is exempt, but external tool helpers must go through run_subprocess)
  - Sibling libs that copy the transferable helper verbatim (D-09)

# Tech tracking
tech-stack:
  added:
    - stdlib subprocess + os + abc (no new third-party deps in this plan)
    - pydantic.BaseModel as the ABC return-type contract (already in pyproject)
  patterns:
    - "Subprocess hardening single-point-of-truth: every subprocess invocation in the library MUST route through run_subprocess() (no extractor may import subprocess directly)"
    - "Transferable helper: pure-function, no internal state, sibling libs can copy verbatim (D-09)"
    - "ABC template method: SubprocessAdapter.execute() drives run via the hardened helper; subclasses cannot bypass DET-05"
    - "Keyword-only required parameter: cwd has no default, enforced at call-site via TypeError (prevents directory traversal via inherited os.getcwd())"
    - "Closed Pydantic return contract from parse_output() (Pitfall 4 defense against schema drift)"

key-files:
  created:
    - lib_code_parser/adapters/__init__.py
    - lib_code_parser/adapters/base.py
    - tests/unit/adapters/__init__.py
    - tests/unit/adapters/test_base.py
    - tests/unit/adapters/test_package_init.py
  modified: []

key-decisions:
  - "D-09 enacted: shipped BOTH an abstract base class (in-lib boilerplate reduction) AND a transferable pure-function helper (sibling-lib re-use). The ABC delegates to the helper internally, so the two paths cannot diverge."
  - "All 4 deterministic env keys (LC_ALL=C, LANG=C, PYTHONHASHSEED=0, PYTHONIOENCODING=utf-8) injected unconditionally on every subprocess call (DET-05). extra_env overlays last so callers can deliberately override but never silently lose the determinism floor."
  - "cwd kept as a *required* keyword-only parameter (no default). Forces callers to think about where the subprocess runs and prevents inherited-os.getcwd() directory-traversal risk (threat T-07-06)."
  - "timeout default 60.0 (per RESEARCH.md §Subprocess Hardening Contract). Caller may shorten or lengthen but cannot pass None (would defeat Pitfall 3 mitigation)."
  - "check=False — the helper returns the CompletedProcess even on non-zero exit; the subclass parse_output() decides what to do. Different adapters have different tolerance policies (pyright type errors are normal output; callgraph subprocess errors might be fatal)."
  - "subprocess.Popen is forbidden in adapters/base.py and the gate proves it (grep count must be 0). All references in docstrings use 'low-level Popen API' as the term-of-art instead, satisfying both the literal grep gate and the intent of documenting the prohibition."

patterns-established:
  - "Subprocess hardening contract: 6 invariants (utf-8, errors=replace, deterministic env, capture_output=True, shell=False, explicit timeout + cwd) — pinned at adapters/base.py and tested live in tests/unit/adapters/test_base.py"
  - "ABC + transferable helper pairing (D-09): in-lib subclasses get boilerplate reduction; sibling libs get a single pure function they can copy"
  - "Live subprocess tests over mocks for hardening assertions: the test suite actually spawns sys.executable to assert env vars are injected, $PATH stays literal, TimeoutExpired propagates, and the return type is the decoded CompletedProcess[str]"

requirements-completed: [ARC-03, DET-05]

# Metrics
duration: ~14 min
completed: 2026-05-24
---

# Phase 01 Plan 07: adapters/base — Subprocess Hardening Foundation Summary

**Single-point-of-truth `run_subprocess()` helper + `SubprocessAdapter` ABC locking the 6 DET-05 hardening invariants (utf-8 encoding, errors=replace, deterministic env LC_ALL/LANG/PYTHONHASHSEED/PYTHONIOENCODING, capture_output=True, shell=False, explicit timeout + cwd) BEFORE any subprocess-using adapter ships in Phase 2.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-05-24T23:04:00Z (approx)
- **Completed:** 2026-05-24T23:18:03Z
- **Tasks:** 2 (each TDD: RED + GREEN)
- **Files modified:** 0 (this plan only creates new files)
- **Files created:** 5 (2 lib files + 3 test files)

## Accomplishments

- `run_subprocess()` helper enforces all 6 hardening invariants in a single function (no extractor or adapter may bypass DET-05).
- `SubprocessAdapter` ABC delegates to the hardened helper via a concrete `execute()` template method, so Phase 2's PyrightAdapter and any future tool adapter cannot bypass the contract.
- 15 live-subprocess tests prove every invariant on the actual `sys.executable` (no mocks): all 4 deterministic env keys present, `$PATH` stays literal (shell=False), `TimeoutExpired` propagates on `timeout=1` + `time.sleep(60)`, `cwd` is keyword-only required, `result.stdout` is `str` (decoded), and the ABC refuses bare instantiation.
- Helper is transferable per D-09 — pure-function, no internal state, importable as `from lib_code_parser.adapters import run_subprocess` for sibling libs to copy.
- Full library test suite (existing v0.1.0 + new): **126 passed, 0 failed**. No regressions.

## Task Commits

Each task was committed atomically following the TDD RED → GREEN cycle:

1. **Task 1 RED — failing Wave 0 tests for adapters/base subprocess hardening** — `b03207f` (test)
2. **Task 1 GREEN — implement adapters/base.py: run_subprocess() helper + SubprocessAdapter ABC** — `ac3f2c0` (feat)
3. **Task 2 RED — failing test for adapters package re-export contract** — `34c3ecb` (test)
4. **Task 2 GREEN — re-export run_subprocess + SubprocessAdapter from adapters package** — `921f8b9` (feat)

## Files Created/Modified

- `lib_code_parser/adapters/__init__.py` — package barrel; re-exports `run_subprocess` and `SubprocessAdapter`; `__all__` declared; absolute imports only.
- `lib_code_parser/adapters/base.py` — module docstring with full hardening rationale + `Traces: ARC-03, DET-05`; module-level `_DETERMINISTIC_ENV` dict with all 4 required keys; `run_subprocess()` pure function (165-ish lines including docstrings) enforcing every invariant; `SubprocessAdapter(ABC)` with two `@abstractmethod`s (`tool_argv`, `parse_output`) + concrete `execute()` template method that delegates to `run_subprocess()`.
- `tests/unit/adapters/__init__.py` — pytest package marker.
- `tests/unit/adapters/test_base.py` — 12 live-subprocess tests covering all 6 invariants + ABC contract.
- `tests/unit/adapters/test_package_init.py` — 3 tests covering package re-export identity + `__all__` membership.

## Verification

### pytest output

```
tests/unit/adapters/test_base.py::test_run_subprocess_sets_lc_all_c PASSED
tests/unit/adapters/test_base.py::test_run_subprocess_sets_pythonhashseed_zero PASSED
tests/unit/adapters/test_base.py::test_run_subprocess_sets_lang_c PASSED
tests/unit/adapters/test_base.py::test_run_subprocess_sets_pythonioencoding_utf8 PASSED
tests/unit/adapters/test_base.py::test_run_subprocess_extra_env_overlays PASSED
tests/unit/adapters/test_base.py::test_run_subprocess_raises_on_timeout PASSED
tests/unit/adapters/test_base.py::test_run_subprocess_does_not_use_shell PASSED
tests/unit/adapters/test_base.py::test_run_subprocess_returns_completed_process PASSED
tests/unit/adapters/test_base.py::test_run_subprocess_decodes_utf8 PASSED
tests/unit/adapters/test_base.py::test_run_subprocess_requires_cwd PASSED
tests/unit/adapters/test_base.py::test_subprocess_adapter_is_abstract PASSED
tests/unit/adapters/test_base.py::test_subprocess_adapter_subclass_works PASSED
tests/unit/adapters/test_package_init.py::test_package_reexports_run_subprocess_identity PASSED
tests/unit/adapters/test_package_init.py::test_package_reexports_subprocess_adapter_identity PASSED
tests/unit/adapters/test_package_init.py::test_package_all_lists_public_symbols PASSED

============================= 15 passed in 2.07s ==============================
```

Full project suite: **126 passed in 2.10s** (111 prior + 15 new).

### Acceptance-criteria gate checks (Task 1)

| Gate | Required | Actual |
|------|----------|--------|
| `def run_subprocess(` | == 1 | 1 |
| `class SubprocessAdapter(ABC)` | == 1 | 1 |
| `@abstractmethod` | == 2 | 2 |
| `_DETERMINISTIC_ENV` | >= 2 | 2 |
| `"LC_ALL": "C"` | >= 1 | 1 |
| `"LANG": "C"` | >= 1 | 1 |
| `"PYTHONHASHSEED": "0"` | >= 1 | 1 |
| `"PYTHONIOENCODING": "utf-8"` | >= 1 | 1 |
| `capture_output=True` | >= 1 | 3 |
| `encoding="utf-8"` | >= 1 | 3 |
| `errors="replace"` | >= 1 | 3 |
| `shell=False` | >= 1 | 5 |
| `timeout=timeout` | >= 1 | 2 |
| `check=False` | >= 1 | 2 |
| `subprocess.Popen` | == 0 | 0 (after rephrase — see deviation) |
| `shell=True` | == 0 | 0 |
| `__all__` | >= 1 | 1 |
| `Traces: ARC-03, DET-05` in module docstring | yes | 3 occurrences |

### Acceptance-criteria gate checks (Task 2)

| Gate | Required | Actual |
|------|----------|--------|
| `python -c "from lib_code_parser.adapters import run_subprocess, SubprocessAdapter"` | exit 0 | OK |
| `python -c "from lib_code_parser.adapters.base import run_subprocess, SubprocessAdapter"` | exit 0 | OK |
| Identity check (re-export same object) | True | True |
| `__all__` in `__init__.py` | >= 1 | 1 |
| Relative imports in `__init__.py` | == 0 | 0 |
| `tests/unit/adapters/__init__.py` exists | yes | yes |

### Lint / format

```
ruff check  lib_code_parser/adapters/ tests/unit/adapters/  → All checks passed!
ruff format lib_code_parser/adapters/ tests/unit/adapters/ --check → 5 files already formatted
```

## Decisions Made

See `key-decisions` in the frontmatter. The most consequential: shipping BOTH the ABC and the transferable helper (D-09), with the ABC delegating to the helper so they cannot diverge.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Internal contradiction between Task 1 `<action>` and `<acceptance_criteria>` regarding the literal string `subprocess.Popen` in `base.py`**

- **Found during:** Task 1 GREEN (acceptance-gate verification step)
- **Issue:** The plan's `<action>` block instructs the function docstring to say *"NEVER calls subprocess.Popen directly; only subprocess.run"*, while the `<acceptance_criteria>` block requires `grep -c 'subprocess\.Popen' lib_code_parser/adapters/base.py` to return **0**. Following the action verbatim makes the gate fail; following the gate verbatim drops the rationale the action explicitly mandates. Both cannot be satisfied with the literal string `subprocess.Popen` anywhere in the file.
- **Fix:** Kept the docstring rationale (the actionable safety message survives) but rephrased the two occurrences to use the synonym **"low-level `Popen` API"** instead of the literal string `subprocess.Popen`. Module docstring (line 20): `the low-level `Popen` API is forbidden in this module (use `subprocess.run` only)`. Function docstring (line 80): `This function NEVER calls the low-level `Popen` API directly; only `subprocess.run`.` Both convey the same prohibition. Both grep gates now return 0 as required.
- **Files modified:** `lib_code_parser/adapters/base.py` (only docstring rephrase; no executable-code change)
- **Verification:** `grep -c 'subprocess\.Popen' lib_code_parser/adapters/base.py` → `0`. All 12 Task 1 tests still pass.
- **Committed in:** `ac3f2c0` (Task 1 GREEN commit — fix included in the same commit since the gate is part of GREEN acceptance)

**2. [Rule 3 - Blocking] Minimal `lib_code_parser/adapters/__init__.py` created in Task 1 to make `lib_code_parser.adapters.base` importable**

- **Found during:** Task 1 GREEN (running the test suite)
- **Issue:** `lib_code_parser/` is a regular package (has `__init__.py`), so `lib_code_parser/adapters/` also requires an `__init__.py` to be a regular subpackage — otherwise `from lib_code_parser.adapters.base import …` fails. Task 1 only mandates `base.py`; the full re-export `__init__.py` is the subject of Task 2. Without a minimal init, Task 1's tests cannot import the module.
- **Fix:** Created a 4-line `lib_code_parser/adapters/__init__.py` in Task 1 GREEN with only a module docstring (no re-exports yet, no `__all__`). Task 2 then upgraded it to the full re-export contract.
- **Files modified:** `lib_code_parser/adapters/__init__.py` (created in Task 1 GREEN, upgraded in Task 2 GREEN)
- **Verification:** Task 1 tests pass; Task 2 then verified the full re-export contract.
- **Committed in:** `ac3f2c0` (initial minimal init) and `921f8b9` (Task 2 upgrade to re-export contract)

**3. [Rule 3 - Blocking] Added a third test file `test_package_init.py` for Task 2's TDD cycle**

- **Found during:** Task 2 (tdd="true" required)
- **Issue:** Task 2's `<behavior>` block specifies import-resolution behavior (`from lib_code_parser.adapters import run_subprocess, SubprocessAdapter` must succeed) but does not name a test file. To preserve the TDD cycle for Task 2 (write a failing test first, then make it pass), I added `tests/unit/adapters/test_package_init.py` with three assertions: (1) package-level `run_subprocess` is the same object as `base.run_subprocess`; (2) same for `SubprocessAdapter`; (3) `__all__` membership.
- **Fix:** Added the test file in Task 2 RED commit (`34c3ecb`). Test failed with `ImportError` until the re-export was added in `921f8b9` GREEN.
- **Files modified:** `tests/unit/adapters/test_package_init.py` (new file)
- **Verification:** All 3 tests pass after Task 2 GREEN.
- **Committed in:** `34c3ecb` (RED) → `921f8b9` (GREEN makes it pass)

**4. [Rule 1 - Style] Test-count discrepancy in plan acceptance criterion**

- **Found during:** Task 1 acceptance verification
- **Issue:** Plan acceptance criterion says *"`pytest tests/unit/adapters/test_base.py -x -q` exits 0 with all 11 tests passing"*, but the plan's own `<behavior>` block enumerates **12** distinct test names. Sticking to the enumerated 12 (since the test list is the source of truth) means the criterion's `11` is stale.
- **Fix:** Implemented all 12 tests as enumerated in `<behavior>`. Test suite passes 12/12. The plan author can correct the count on next revision.
- **Files modified:** `tests/unit/adapters/test_base.py`
- **Verification:** `pytest tests/unit/adapters/test_base.py -x -q` → `12 passed in 1.81s`. Exit 0.
- **Committed in:** `b03207f` (RED) → `ac3f2c0` (GREEN)

---

**Total deviations:** 4 auto-fixed (1 Rule 1 — gate-vs-action contradiction; 2 Rule 3 — necessary scaffolding for the TDD + test cycle to function; 1 Rule 1 — minor plan acceptance-text discrepancy).

**Impact on plan:** All 4 deviations were necessary to actually execute the plan as written. No scope creep — every change directly supports the plan's stated objective and the threat-model dispositions.

## TDD Gate Compliance

The plan's `type: execute` frontmatter with task-level `tdd="true"` requires per-task RED → GREEN commits. All 4 commits in `git log --oneline` confirm the order:

```
921f8b9 feat(01-07): re-export run_subprocess + SubprocessAdapter from adapters package   ← Task 2 GREEN
34c3ecb test(01-07): add failing test for adapters package re-export contract             ← Task 2 RED
ac3f2c0 feat(01-07): implement adapters/base.py — run_subprocess() helper + ABC           ← Task 1 GREEN
b03207f test(01-07): add failing Wave 0 tests for adapters/base subprocess hardening       ← Task 1 RED
```

Both tasks satisfied RED → GREEN with the RED commit containing only the test (verified failing) and the GREEN commit containing the implementation (verified passing).

## Threat Surface Scan

The plan's `<threat_model>` enumerates seven STRIDE entries; all are addressed by the shipped code. No new threat surface introduced beyond what the plan enumerated. No `## Threat Flags` section needed.

| Threat ID | Disposition in plan | How addressed | Test that proves it |
|-----------|---------------------|---------------|---------------------|
| T-07-01 (shell injection) | mitigate | `shell=False` literal in `run_subprocess`; argv typed as `Sequence[str]` | `test_run_subprocess_does_not_use_shell` (asserts `$PATH` literal) |
| T-07-02 (locale non-determinism) | mitigate | `LC_ALL=C` + `LANG=C` in `_DETERMINISTIC_ENV` | `test_run_subprocess_sets_lc_all_c`, `test_run_subprocess_sets_lang_c` |
| T-07-03 (DoS via missing timeout) | mitigate | `timeout: float = 60.0` keyword-only with non-None default | `test_run_subprocess_raises_on_timeout` (asserts `TimeoutExpired` raised) |
| T-07-04 (Pitfall 3 deadlock) | mitigate | `subprocess.run(..., capture_output=True)`; `Popen` literally absent (grep gate = 0) | All 12 tests run without hanging |
| T-07-05 (Windows cp1252 bug) | mitigate | `encoding="utf-8"`, `errors="replace"` | `test_run_subprocess_decodes_utf8` (asserts `isinstance(result.stdout, str)`) |
| T-07-06 (cwd directory traversal) | mitigate | `cwd: str` keyword-only **required** parameter, no default | `test_run_subprocess_requires_cwd` (asserts `TypeError` when `cwd` omitted) |
| T-07-07 (supply chain) | accept | Only `sys.executable` invoked in tests; no external binary calls | n/a — acceptance |

## Known Stubs

None — every shipped symbol has a complete implementation and is exercised by tests.

## Issues Encountered

None beyond the four deviations documented above.

## User Setup Required

None — this plan only adds Python source files. No new external services, no env vars, no dashboard config. Phase 2 PyrightAdapter (separate plan) will require Node.js for the `pyright[nodejs]` extra.

## Next Phase Readiness

- **Phase 1 wave 1 plans 01-03 through 01-07 unblock plan 01-08 (docs Common AST View + extending)** if those plans share wave 1 readiness. Plan 01-07's frontmatter is `wave: 1, depends_on: []` so 01-07 itself does not consume any wave-1 outputs but provides the subprocess substrate for downstream waves.
- **Phase 2 PyrightAdapter is now ready to be planned**: it will be a `SubprocessAdapter` subclass, fill in `tool_argv` and `parse_output`, and inherit the entire DET-05 hardening contract for free.
- **Sibling libs** (`lib-spec-parser`, `lib-diagram-parser`, etc.) may now copy `lib_code_parser/adapters/base.py::run_subprocess` verbatim if they need the same subprocess discipline — the function has no internal state and no lib-specific imports beyond stdlib + `pydantic.BaseModel` (only used by the ABC, not by the helper itself).
- **No blockers** for the rest of Phase 1.

## Self-Check: PASSED

Verified via filesystem + git inspection at commit `921f8b9`:

- `lib_code_parser/adapters/__init__.py` — FOUND
- `lib_code_parser/adapters/base.py` — FOUND
- `tests/unit/adapters/__init__.py` — FOUND
- `tests/unit/adapters/test_base.py` — FOUND
- `tests/unit/adapters/test_package_init.py` — FOUND
- Commit `b03207f` (Task 1 RED) — FOUND
- Commit `ac3f2c0` (Task 1 GREEN) — FOUND
- Commit `34c3ecb` (Task 2 RED) — FOUND
- Commit `921f8b9` (Task 2 GREEN) — FOUND
- Full test suite `python -m pytest -x -q` — **126 passed in 2.10s**
- `ruff check` + `ruff format --check` on the new files — both pass

---
*Phase: 01-architecture-foundation-spec-correction*
*Plan: 07 — adapters/base subprocess hardening foundation*
*Completed: 2026-05-24*
