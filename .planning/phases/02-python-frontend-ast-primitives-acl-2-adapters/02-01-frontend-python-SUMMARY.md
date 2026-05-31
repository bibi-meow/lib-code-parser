---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 01
subsystem: frontends + models.infrastructure
tags: [ast-05, cav, python-frontend, parity-gate, trc-02, arc-02]
requires:
  - "Phase 1 locked CAV (frozen + extra=forbid + arbitrary_types_allowed + Literal language)"
  - "Phase 1 _dispatch.FrontendFn signature (bytes, str, ParserConfig) -> CAV"
  - "Phase 1 typed ParserConfig"
provides:
  - "lib_code_parser.frontends.python.build_cav — single ast.parse() per file, CAV producer"
  - "CAV.raw_content: bytes additive field for Wave 2 type_deps -> PyrightAdapter bytes carry"
  - "AST-05 grep static gate + monkeypatch dynamic gate (tests/parity/test_ast_05_one_parse.py)"
affects:
  - "Wave 2 plan 02-06 (registers build_cav into _dispatch.FRONTENDS['python'])"
  - "Wave 1/2 extractor plans (blocked from calling ast.parse by the grep gate)"
tech-stack:
  added: []
  patterns:
    - "Frontend = single parse site; extractors = CAV consumers"
    - "additive Pydantic field with default for backward-compatible model extension"
key-files:
  created:
    - lib_code_parser/frontends/python.py
    - tests/unit/models/test_cav_raw_content.py
    - tests/unit/frontends/__init__.py
    - tests/unit/frontends/test_python_frontend.py
    - tests/parity/test_ast_05_one_parse.py
  modified:
    - lib_code_parser/models/infrastructure/cav.py
    - lib_code_parser/frontends/__init__.py
decisions:
  - "CAV.raw_content keeps lax Pydantic validation (str coerced to bytes), not strict — model has no strict=True; documented in test rename"
  - "AST-05 dynamic monkeypatch gate placed in both unit (frontend) and parity (test_ast_05_one_parse) per RESEARCH §5.2 defence-in-depth"
metrics:
  duration: ~25m
  completed: 2026-05-31
  tasks: 3
  files: 7
  tests_added: 15
  tests_total: 202
---

# Phase 2 Plan 01: Python Frontend Summary

Implemented the Python Frontend (`build_cav`) as the single `ast.parse()` site per file, extended the CAV envelope with an additive `raw_content: bytes` field for the Wave 2 type_deps -> PyrightAdapter bytes carry, and stood up the AST-05 grep static gate plus monkeypatch dynamic gate that permanently block extractors from re-parsing.

## What Was Built

- **Task 1** — `CAV.raw_content: bytes = b""` additive field. Phase 1's four invariants (frozen / extra="forbid" / arbitrary_types_allowed / Literal language) are unchanged. 4 Wave 0 unit tests (`test_cav_raw_content.py`).
- **Task 2** — `frontends/python.py::build_cav(raw_content, path, config) -> CAV`. Single `ast.parse(source, filename=path)` call, UTF-8 decode with `errors="replace"`, SyntaxError propagated (fail-loudly D-06). Barrel re-export in `frontends/__init__.py`. 7 Wave 0 unit tests.
- **Task 3** — `tests/parity/test_ast_05_one_parse.py`: 4 tests — grep static gate (extractors/ = 0, adapters/ = 0, frontends/ single python.py site) + monkeypatch dynamic gate (call_count == 1).

## Verification Evidence

### pytest counts (per directory)
| Directory | Result |
|-----------|--------|
| tests/acceptance/ | 58 passed |
| tests/parity/ | 15 passed (11 v01_v02_compat + 4 ast_05_one_parse) |
| tests/unit/models/ | 40 passed (incl. 4 new raw_content) |
| tests/unit/frontends/ | 7 passed (new) |
| tests/unit/ (all) | 129 passed |
| **tests/ (full suite)** | **202 passed** (187 Phase 1 baseline + 4 cav + 7 frontend + 4 parity) |

### AST-05 static gate
```
$ grep -rn -E "ast\.parse\(|from ast import parse" lib_code_parser/extractors/ --include=*.py
(0 matches — exit 1)
$ grep -rn "module = ast.parse(" lib_code_parser/frontends/ --include=*.py
lib_code_parser/frontends/python.py:36:    module = ast.parse(source, filename=path)   (1 real call site)
```

### CAV model diff (before -> after)
Only additive change to the class body:
```diff
     language: Literal["python", "cpp"]
     path: str
     payload: object
+    raw_content: bytes = b""
```
Plus a docstring paragraph (rationale) and a one-line class-docstring pointer. `model_config` (frozen / extra="forbid" / arbitrary_types_allowed) is byte-for-byte unchanged.

### ruff
`ruff check lib_code_parser/ tests/` -> All checks passed!

### Phase 1 baseline parity
`tests/parity/test_v01_v02_compat.py` -> 11 passed (unchanged). No retrogression in the 187-test Phase 1 baseline.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the `test_build_cav_decodes_utf8_with_replace` assertion**
- **Found during:** Task 2
- **Issue:** The plan's `<behavior>` claimed `build_cav(b"\xff\xfe invalid utf-8 \x80", ...)` would `ast.parse` successfully after `errors="replace"`. In fact, replacement chars (U+FFFD) prepended to bare tokens are not valid Python and raise `SyntaxError`. The decode step itself is what `errors="replace"` protects (T-02-03 DoS mitigation), not the parse.
- **Fix:** Test now embeds the invalid bytes inside a comment (`b"# \xff\xfe bad bytes \x80\ndef f(): pass\n"`) so the replaced source is still valid Python. This asserts the true invariant: decode never crashes, and surrounding valid source parses. The implementation (`decode(..., errors="replace")`) was already correct and unchanged.
- **Files modified:** tests/unit/frontends/test_python_frontend.py
- **Commit:** ad93faf

**2. [Rule 1/3 - Bug] grep helper Windows cp932 decode crash in parity test**
- **Found during:** Task 3
- **Issue:** `subprocess.run(..., text=True)` decodes grep stdout with the platform codec (cp932 on this Windows host). Source files contain a non-ASCII em-dash; cp932 raised `UnicodeDecodeError` in the reader thread, leaving `result.stdout = None` -> `AttributeError: 'NoneType' object has no attribute 'splitlines'`.
- **Fix:** Capture grep output as bytes (drop `text=True`) and decode explicitly `result.stdout.decode("utf-8", errors="replace")`. Consistent with the project's windows-shell-encoding guidance.
- **Files modified:** tests/parity/test_ast_05_one_parse.py
- **Commit:** 4db45e1

### Acceptance-criteria literal-count notes (no fix needed)
- Task 1 criterion expected `grep -c raw_content cav.py == 1` and `grep -c frozen=True == 1`. Actual counts are 3 and 2 respectively, because the plan's own `<action>` mandated docstring prose that references `raw_content` and the pre-existing class docstring references `frozen=True`. The **intent** holds exactly: one field *declaration* (line 45), frozen preserved in `model_config` (line 39), `extra="forbid"` exactly 1. The literal counts diverge only from plan-mandated docstring text, not from any structural deviation.
- Task 2 criterion expected `grep -c "ast\.parse" python.py == 1`. Actual is 4 — one real call (line 36) plus three docstring mentions written verbatim from the plan's `<action>` docstring template. The AST-05 parity gate (Task 3) verifies the structural invariant precisely via the `module = ast.parse(` real-call filter, so the intent is fully enforced.

## Known Stubs
None. `build_cav` is fully wired; only `_dispatch.FRONTENDS['python']` registration is deferred to Wave 2 plan 02-06 by design (file-ownership separation), as stated in the plan interfaces.

## Self-Check: PASSED
- Created files: all 7 FOUND (cav.py, python.py, frontends/__init__.py, test_cav_raw_content.py, tests/unit/frontends/__init__.py, test_python_frontend.py, test_ast_05_one_parse.py)
- Commits: 82a642d (Task 1), ad93faf (Task 2), 4db45e1 (Task 3) all present in git log
