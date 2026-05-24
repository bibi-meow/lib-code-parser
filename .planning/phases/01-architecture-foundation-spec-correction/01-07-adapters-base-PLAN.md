---
phase: 01-architecture-foundation-spec-correction
plan: 07
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/adapters/__init__.py
  - lib_code_parser/adapters/base.py
  - tests/unit/adapters/__init__.py
  - tests/unit/adapters/test_base.py
autonomous: true
requirements: [ARC-03, DET-05]
must_haves:
  truths:
    - "lib_code_parser/adapters/base.py exposes run_subprocess() helper enforcing encoding=utf-8, errors=replace, env LC_ALL=C + PYTHONHASHSEED=0 + LANG=C + PYTHONIOENCODING=utf-8, explicit timeout (default 60), explicit cwd (required), capture_output=True, shell=False"
    - "SubprocessAdapter abstract base class drives subprocess execution via run_subprocess() (subclasses implement tool_argv + parse_output)"
    - "Determinism env is injected on every subprocess call without exception"
    - "Helper is transferable — sibling libs can copy it verbatim (no internal state, pure-function style)"
  artifacts:
    - path: "lib_code_parser/adapters/base.py"
      provides: "run_subprocess() helper + SubprocessAdapter ABC"
      contains: "def run_subprocess|class SubprocessAdapter"
    - path: "tests/unit/adapters/test_base.py"
      provides: "Subprocess hardening live assertions (env / encoding / timeout / shell=False)"
      contains: "test_run_subprocess"
  key_links:
    - from: "run_subprocess()"
      to: "subprocess.run(..., capture_output=True, encoding=utf-8, errors=replace, shell=False, timeout=N, cwd=...)"
      via: "single helper enforcing all 6 hardening invariants"
      pattern: "subprocess\\.run"
    - from: "SubprocessAdapter"
      to: "run_subprocess()"
      via: "execute() template method"
      pattern: "self\\.tool_argv|self\\.parse_output"
---

<objective>
Per ARC-03 / DET-05 / D-09: create `lib_code_parser/adapters/base.py` containing the `run_subprocess()` hardening helper AND the `SubprocessAdapter` abstract base class. The helper is the single point where all subprocess invariants (encoding, errors=replace, deterministic env including LC_ALL/PYTHONHASHSEED/LANG/PYTHONIOENCODING, explicit timeout, explicit cwd, capture_output=True, shell=False) are enforced. The ABC enables subclasses (Phase 2 PyrightAdapter) to drop boilerplate. Per D-09, the helper is written in a transferable style (no internal state) so sibling libs can copy it.

Purpose: Locks the subprocess hardening contract BEFORE any subprocess-using adapter is written. Phase 2 PyrightAdapter and any future tool adapter MUST go through this helper — that contract is the only way DET-05 + Pitfall 3 (deadlock) + Pitfall 13 (Windows cp1252) are systemically prevented.

Output:
- `lib_code_parser/adapters/__init__.py` — re-exports `run_subprocess`, `SubprocessAdapter`
- `lib_code_parser/adapters/base.py` — helper + ABC
- Wave 0 tests at tests/unit/adapters/test_base.py asserting env injection, timeout behavior, shell=False, encoding override
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/research/PITFALLS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-VALIDATION.md
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement adapters/base.py with run_subprocess() helper + SubprocessAdapter ABC</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Subprocess Hardening Contract — pinned implementation incl. exact _DETERMINISTIC_ENV dict keys/values, function signature, and ABC method skeleton; live cross-platform considerations from Pitfall 13)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/research/PITFALLS.md §Pitfall 3 (subprocess Popen+wait deadlock — always use subprocess.run with capture_output=True + timeout), §Pitfall 13 (Windows cp1252 encoding bug — always pass encoding="utf-8")
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md (D-09 — helper is transferable, no internal state; ABC for in-lib boilerplate reduction)
  </read_first>
  <behavior>
    Tests in tests/unit/adapters/test_base.py:
    - test_run_subprocess_sets_lc_all_c: invokes `[sys.executable, "-c", "import os; print(os.environ.get('LC_ALL',''))"]`; asserts stdout contains "C"
    - test_run_subprocess_sets_pythonhashseed_zero: invokes `[sys.executable, "-c", "import os; print(os.environ.get('PYTHONHASHSEED',''))"]`; asserts stdout contains "0"
    - test_run_subprocess_sets_lang_c: invokes `[sys.executable, "-c", "import os; print(os.environ.get('LANG',''))"]`; asserts stdout contains "C"
    - test_run_subprocess_sets_pythonioencoding_utf8: invokes `[sys.executable, "-c", "import os; print(os.environ.get('PYTHONIOENCODING',''))"]`; asserts stdout contains "utf-8"
    - test_run_subprocess_extra_env_overlays: extra_env={"FOO": "bar"}; invokes shell-echo of FOO; asserts "bar" in stdout
    - test_run_subprocess_raises_on_timeout: invokes a `sys.executable -c "import time; time.sleep(60)"` with timeout=1; asserts `subprocess.TimeoutExpired` raised
    - test_run_subprocess_does_not_use_shell: invokes `[sys.executable, "-c", "print('$PATH')"]`; asserts "$PATH" appears literally in stdout (not expanded by shell)
    - test_run_subprocess_returns_completed_process: result has `.stdout`, `.stderr`, `.returncode` attributes
    - test_run_subprocess_decodes_utf8: invokes a script that prints UTF-8 emoji; asserts decoded correctly via errors=replace (no UnicodeDecodeError raised; if test env can't run emoji, use a plain ASCII echo plus assertion that `isinstance(result.stdout, str)` and not bytes)
    - test_run_subprocess_requires_cwd: pytest.raises(TypeError) when calling run_subprocess(argv) without cwd kwarg (TypeError because cwd is a keyword-only required parameter)
    - test_subprocess_adapter_is_abstract: pytest.raises(TypeError) when instantiating bare SubprocessAdapter() (ABC abstract methods not implemented)
    - test_subprocess_adapter_subclass_works: define an in-test FakeAdapter(SubprocessAdapter) implementing tool_argv and parse_output; instantiate; call .execute(); assert run_subprocess was called through the ABC and parse_output received stdout/stderr/returncode
  </behavior>
  <action>
    Implement `lib_code_parser/adapters/base.py`:
    - Module docstring (multi-line): "Subprocess adapter base class + hardening helper. All subprocess invocations in this library MUST go through run_subprocess(). The helper centralizes determinism guarantees (encoding, locale, hash seed, timeout, cwd) and cross-platform pitfalls (Windows cp1252 decode, Popen deadlock). The helper is intentionally transferable — sibling libs can copy it verbatim if they need the same subprocess discipline; no internal state. Traces: ARC-03, DET-05."
    - Imports: `from __future__ import annotations`, `import os`, `import subprocess`, `from abc import ABC, abstractmethod`, `from collections.abc import Mapping, Sequence`, `from pydantic import BaseModel`.
    - Define module-level `_DETERMINISTIC_ENV: dict[str, str] = {"LC_ALL": "C", "LANG": "C", "PYTHONHASHSEED": "0", "PYTHONIOENCODING": "utf-8"}` (all 4 entries exactly per RESEARCH.md §Subprocess Hardening Contract pinned dict).
    - Function `def run_subprocess(argv: Sequence[str], *, cwd: str, timeout: float = 60.0, extra_env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]`:
      - Note: `cwd` is keyword-only (after `*`) and has NO default — caller MUST provide it (DET-05 explicit cwd).
      - Note: `timeout` is keyword-only with default 60.0 (DET-05 explicit timeout).
      - Note: `argv` MUST be `Sequence[str]` (a list) — DO NOT accept a single string (security: prevents shell injection vector).
      - Body: build env dict by `env: dict[str, str] = dict(os.environ); env.update(_DETERMINISTIC_ENV); if extra_env is not None: env.update(extra_env)`. Return `subprocess.run(list(argv), cwd=cwd, env=env, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout, shell=False, check=False)`. Use `check=False` — let caller decide what to do with non-zero exit (per RESEARCH).
      - Docstring (function-level): "Run a subprocess with deterministic hardening. Enforces encoding=utf-8 (Pitfall 13), errors=replace, deterministic env (LC_ALL/LANG/PYTHONHASHSEED/PYTHONIOENCODING per DET-05), capture_output=True (Pitfall 3 — never block on full pipe), shell=False (security + determinism), explicit timeout (default 60.0 — never hang). NEVER calls subprocess.Popen directly; only subprocess.run. Required keyword args: cwd. Optional keyword args: timeout, extra_env."
    - Class `SubprocessAdapter(ABC)`:
      - Class docstring: "Abstract base for any subprocess-based adapter (pyright, future tools). Subclasses implement: (1) tool_argv(target_path) — build the argv list (no shell escape; argv is a list); (2) parse_output(stdout, stderr, returncode) — parse raw output into a typed Pydantic model (Pitfall 4 — defend against schema drift). The base class drives the run via run_subprocess() and never bypasses determinism."
      - `@abstractmethod def tool_argv(self, target_path: str) -> Sequence[str]: ...`
      - `@abstractmethod def parse_output(self, stdout: str, stderr: str, returncode: int) -> BaseModel: ...`
      - Concrete method `def execute(self, target_path: str, *, cwd: str, timeout: float = 60.0, extra_env: Mapping[str, str] | None = None) -> BaseModel`:
        - Body: `result = run_subprocess(self.tool_argv(target_path), cwd=cwd, timeout=timeout, extra_env=extra_env)`; `return self.parse_output(result.stdout, result.stderr, result.returncode)`
        - Docstring: "Template method — fetch argv from subclass, run via hardened helper, delegate parse to subclass."
    - Add `__all__ = ["run_subprocess", "SubprocessAdapter"]`.

    Cross-platform note: the test `test_run_subprocess_does_not_use_shell` invokes `[sys.executable, "-c", "print('$PATH')"]`. On Linux/macOS this stdout literal is `$PATH` (NOT the expanded value) because `shell=False`. On Windows the same argv produces `$PATH` literally too (cmd.exe is NOT invoked because shell=False). The test is OS-portable.

    Implementation note: Do NOT swallow exceptions. `subprocess.TimeoutExpired` MUST propagate to caller (test_run_subprocess_raises_on_timeout depends on this).
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/adapters/test_base.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/adapters/test_base.py -x -q` exits 0 with all 11 tests passing
    - `grep -c '^def run_subprocess(' lib_code_parser/adapters/base.py` returns exactly 1
    - `grep -c 'class SubprocessAdapter(ABC)' lib_code_parser/adapters/base.py` returns exactly 1
    - `grep -c '@abstractmethod' lib_code_parser/adapters/base.py` returns exactly 2 (tool_argv + parse_output)
    - `grep -c '_DETERMINISTIC_ENV' lib_code_parser/adapters/base.py` returns >= 2 (definition + use)
    - All 4 deterministic env keys present (single grep run):
      - `grep -c '"LC_ALL": "C"' lib_code_parser/adapters/base.py` returns >= 1
      - `grep -c '"LANG": "C"' lib_code_parser/adapters/base.py` returns >= 1
      - `grep -c '"PYTHONHASHSEED": "0"' lib_code_parser/adapters/base.py` returns >= 1
      - `grep -c '"PYTHONIOENCODING": "utf-8"' lib_code_parser/adapters/base.py` returns >= 1
    - `grep -c 'capture_output=True' lib_code_parser/adapters/base.py` returns >= 1
    - `grep -c 'encoding="utf-8"' lib_code_parser/adapters/base.py` returns >= 1
    - `grep -c 'errors="replace"' lib_code_parser/adapters/base.py` returns >= 1
    - `grep -c 'shell=False' lib_code_parser/adapters/base.py` returns >= 1
    - `grep -c 'timeout=timeout' lib_code_parser/adapters/base.py` returns >= 1
    - `grep -c 'check=False' lib_code_parser/adapters/base.py` returns >= 1
    - `grep -c 'subprocess\.Popen' lib_code_parser/adapters/base.py` returns 0 (Popen forbidden per Pitfall 3)
    - `grep -c 'shell=True' lib_code_parser/adapters/base.py` returns 0 (shell=True forbidden)
    - `grep -c '__all__' lib_code_parser/adapters/base.py` returns >= 1
    - File has module docstring with `Traces: ARC-03, DET-05`
  </acceptance_criteria>
  <done>adapters/base.py ships run_subprocess() with all 6 hardening invariants + SubprocessAdapter ABC + 11-test Wave 0 suite passing live subprocess assertions.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Create adapters/__init__.py + test package __init__.py</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/adapters/base.py (Task 1 output — exact symbols to re-export)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md (absolute imports, snake_case modules, package __init__ re-export pattern)
  </read_first>
  <behavior>
    - `from lib_code_parser.adapters import run_subprocess, SubprocessAdapter` succeeds
    - `from lib_code_parser.adapters.base import run_subprocess, SubprocessAdapter` also succeeds (sub-module path)
    - tests/unit/adapters/__init__.py exists (pytest package marker)
  </behavior>
  <action>
    Implement `lib_code_parser/adapters/__init__.py`:
    - Module docstring: "Adapters — subprocess-isolated tool wrappers (ARC-03). Phase 1 ships only the base helper + ABC; Phase 2 adds PyrightAdapter."
    - Re-exports: `from lib_code_parser.adapters.base import run_subprocess, SubprocessAdapter`.
    - `__all__ = ["run_subprocess", "SubprocessAdapter"]`.
    - Absolute imports only.

    Implement `tests/unit/adapters/__init__.py`:
    - Empty file (or single-line docstring `"""Subprocess adapter tests."""`). Pytest package marker.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; python -c "from lib_code_parser.adapters import run_subprocess, SubprocessAdapter; from lib_code_parser.adapters.base import run_subprocess as r2, SubprocessAdapter as S2; assert run_subprocess is r2; assert SubprocessAdapter is S2"</automated>
  </verify>
  <acceptance_criteria>
    - `python -c "from lib_code_parser.adapters import run_subprocess, SubprocessAdapter"` exits 0
    - `python -c "from lib_code_parser.adapters.base import run_subprocess, SubprocessAdapter"` exits 0
    - `grep -c '__all__' lib_code_parser/adapters/__init__.py` returns >= 1
    - `grep "^from \\." lib_code_parser/adapters/__init__.py` returns 0 (no relative imports)
    - `test -f tests/unit/adapters/__init__.py` returns 0 (file exists)
  </acceptance_criteria>
  <done>adapters/__init__.py re-exports the hardening contract; tests/unit/adapters/ package marker created.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| lib → subprocess tool (Phase 2 pyright, future C++ helpers) | Argv crosses process boundary; shell injection / path traversal / locale tampering possible without contract enforcement |
| caller → adapter cwd | Caller passes working directory; explicit cwd argument prevents directory traversal via inherited `os.getcwd()` |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-07-01 | Tampering (T1 from security_threat_model_required) | Subprocess shell injection | mitigate | shell=False enforced; argv is Sequence[str], not str; tests assert "$PATH" not expanded |
| T-07-02 | Tampering (T2) | Locale-dependent non-determinism | mitigate | LC_ALL=C + LANG=C injected unconditionally; tests assert via live subprocess echo |
| T-07-03 | Denial of Service | Subprocess hang via missing timeout (Pitfall 3) | mitigate | timeout default 60.0; explicit kwarg; test asserts TimeoutExpired raised on timeout=1 + sleep(60) |
| T-07-04 | Tampering | Subprocess buffer-full deadlock (Pitfall 3 — Popen+wait+stdout.read()) | mitigate | subprocess.run + capture_output=True; Popen explicitly forbidden (grep gate); RESEARCH-cited rationale in docstring |
| T-07-05 | Tampering | Windows cp1252 encoding bug (Pitfall 13) | mitigate | encoding="utf-8" + errors="replace" enforced; test asserts result.stdout is str-typed (decoded) |
| T-07-06 | Tampering (T3) | Directory traversal via inherited cwd | mitigate | cwd is keyword-only required parameter (no default); TypeError raised if missing; test asserts |
| T-07-07 | Supply chain | None — no package installs in this plan; only subprocess invocations of `sys.executable` in tests | accept | Test fixtures invoke only `sys.executable` (the current Python interpreter); no external binary called |
</threat_model>

<verification>
- run_subprocess() enforces all 6 hardening invariants (verified by 11-test Wave 0 suite running live subprocess calls)
- SubprocessAdapter ABC pattern works (Fake adapter subclass test passes)
- Popen and shell=True absent from base.py
- All 4 deterministic env keys present and injected
</verification>

<success_criteria>
- ROADMAP §Phase 1 Success Criterion 4: `lib_code_parser/adapters/base.py` defines the subprocess hardening contract (encoding="utf-8", errors="replace", env LC_ALL=C + PYTHONHASHSEED=0 + LANG=C + PYTHONIOENCODING=utf-8, explicit timeout, explicit cwd, capture_output=True, shell=False) and ships an enforcement helper ✓
- ARC-03 satisfied for Phase 1 substrate (Phase 2 PyrightAdapter will be a subclass)
- DET-05 satisfied via run_subprocess() helper
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-07-SUMMARY.md` when done with pytest output for tests/unit/adapters/test_base.py and grep verification of all 6 hardening invariants.
</output>
