---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 05
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/adapters/pyright.py
  - tests/unit/adapters/__init__.py
  - tests/unit/test_pyright_adapter.py
autonomous: true
requirements: [AST-03, DET-03, ARC-03, DET-05, TRC-02, TRC-03]
must_haves:
  truths:
    - "Caller can write `from lib_code_parser.adapters.pyright import PyrightAdapter; PyrightAdapter(python_version='3.12').analyze(raw_bytes, 'src.py')` and get a typed PyrightOutput Pydantic model populated from pyright --outputjson generalDiagnostics, with deterministic env (PYRIGHT_PYTHON_FORCE_VERSION=1.1.409 + PYRIGHT_PYTHON_IGNORE_WARNINGS=1) injected via run_subprocess (DET-03 + DET-05)"
    - "PyrightAdapter writes raw_bytes to internal tempfile.TemporaryDirectory()/{module_name}.py, then runs pyright with `-p {tmpdir}/pyrightconfig.json` so the caller's pyproject.toml is never auto-loaded (Pitfall 3 mitigation) — caller-agnostic I/O (D-05) is preserved end-to-end"
    - "Pyright CLI argv per D-08 / RESEARCH §2.2: ['pyright', '--outputjson', '--pythonversion', python_version, '-p', '{tmpdir}/pyrightconfig.json', '{tmpdir}/{module_name}.py'] — no other flags (--verbose / --dependencies / --verifytypes excluded)"
    - "PyrightAdapter raises RuntimeError on subprocess failure (returncode not in {0,1}), JSON parse failure (json.JSONDecodeError), or subprocess timeout (TimeoutExpired) per D-06 fail-loudly; silent empty PyrightOutput is NEVER returned (DET-01 byte-identical 維持)"
    - "PyrightOutput is a typed Pydantic v2 BaseModel with model_config = ConfigDict(extra='forbid'); only generalDiagnostics[].{file, severity, message, rule, range.start.line, range.end.line} are extracted per RESEARCH §2.3 (other subkeys discarded)"
    - "File paths in PyrightOutput.diagnostics are forward-slash normalized (`\\` → `/`) and the tmpdir prefix is stripped → replaced with caller-supplied path string (D-07 canonicalization)"
    - "Module docstring contains 'Implements: AST-03, DET-03, ARC-03, DET-05' and 'Traces: AST-03, DET-03, DET-05, ARC-03'"
  artifacts:
    - path: "lib_code_parser/adapters/pyright.py"
      provides: "PyrightAdapter (SubprocessAdapter subclass) — caller-agnostic I/O + DET-03 env + D-06 fail-loudly + D-07 canonicalization"
      contains: "class PyrightAdapter"
    - path: "tests/unit/test_pyright_adapter.py"
      provides: "PyrightAdapter unit: argv build, env vars, JSON parse error path, timeout path, tmpdir prefix strip, fail-loudly"
      contains: "def test_pyright|def test_det_03_env_var_set"
  key_links:
    - from: "PyrightAdapter._DET_ENV"
      to: "PYRIGHT_PYTHON_FORCE_VERSION=1.1.409, PYRIGHT_PYTHON_IGNORE_WARNINGS=1"
      via: "extra_env passed to run_subprocess"
      pattern: "PYRIGHT_PYTHON_FORCE_VERSION"
    - from: "PyrightAdapter.analyze"
      to: "tempfile.TemporaryDirectory() + write bytes + pyrightconfig.json"
      via: "internal tmpdir context manager (D-05 caller-agnostic I/O)"
      pattern: "TemporaryDirectory"
    - from: "PyrightAdapter.parse_output"
      to: "RuntimeError on returncode not in {0,1} / JSONDecodeError"
      via: "raise from chain"
      pattern: "RuntimeError"
---

<objective>
Wave 1 並列の 5 件目。 Phase 1 `adapters/base.py` の `SubprocessAdapter` ABC を subclass する形で `PyrightAdapter` を実装し、 Phase 2 Wave 2 (Plan 02-06 type_deps extractor) が「pyright を `resolved` flag 判定者として使う」算法 (RESEARCH §2.3) に必要な PyrightOutput 型を提供する。

`PyrightAdapter.analyze(raw_content, path)` の動作:
1. `tempfile.TemporaryDirectory()` で internal tmpdir を context manager 作成 (D-05 caller-agnostic I/O 維持)
2. `{tmpdir}/{module_name}.py` に raw_content を bytes 書き出し
3. `{tmpdir}/pyrightconfig.json` に固定 JSON `{"include": ["."], "reportMissingImports": "error"}` を書き出し (Pitfall 3 — caller 環境の pyproject.toml auto-load を回避)
4. `run_subprocess(argv, cwd=tmpdir, timeout=60.0, extra_env={"PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409", "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1"})` を呼ぶ
5. stdout を JSON parse、 D-06 fail-loudly: returncode not in {0, 1} / JSONDecodeError / TimeoutExpired → `RuntimeError` を raise from
6. `generalDiagnostics[]` のうち `file / severity / message / rule / range.start.line / range.end.line` のみを抽出 (D-07 — `version` も `time` も `summary` も捨てる; これは RESEARCH §2.3 で確認した「pyright JSON は diagnostics-only」 = 解決済 type 情報を持たない事実に基づく)
7. file path を forward-slash 正規化 + tmpdir prefix を caller_path に置換 (D-07)
8. `PyrightOutput` (Pydantic v2 BaseModel) を返す

`PyrightAdapter` は SubprocessAdapter ABC の `tool_argv()` / `parse_output()` を override する。 `execute()` template method は base class のものをそのまま使う (D-09 hardening 継承)。 ただし `analyze()` は `execute()` と並行する Adapter-固有 entry point として提供する (`execute()` の signature `(target_path, cwd, timeout, extra_env)` は raw bytes carry を持たないため、 PyrightAdapter は tmpdir 管理を内包する `analyze(raw_content, path)` を独自 public method として持つ)。

CONTEXT.md D-07-revised が確定した方針: pyright `--outputjson` は型解決済み import / annotation を返さない (RESEARCH §2.1 実機検証で invalidate)。 PyrightAdapter は **`generalDiagnostics` のみ** を意味あるデータとして抽出する。 Plan 02-06 type_deps extractor がこの diagnostics を使って `reportMissingImports` rule の発火行から `resolved` flag を算出する。

Purpose: ROADMAP Phase 2 success criterion 2 のうち pyright subprocess 部分 + DET-03 env injection + D-08 CLI 選定 + D-09 fail-loudly を成立。 Plan 02-06 type_deps extractor のための入力 (PyrightOutput.diagnostics) を提供。

Output:
- `lib_code_parser/adapters/pyright.py` — 新規 1 ファイル、 `PyrightAdapter` + `PyrightOutput` + `PyrightDiagnostic` の 3 class + 固定 env 定数
- `tests/unit/adapters/__init__.py` — empty 包装
- `tests/unit/test_pyright_adapter.py` — argv assertion / env var assertion / JSON parse error path / timeout path / tmpdir prefix strip / 統合 smoke (実 pyright 起動)
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/PROJECT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/REQUIREMENTS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/ROADMAP.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-DISCUSSION-LOG.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/adapters/base.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_paths.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/config.py

<interfaces>
<!-- Phase 1 SubprocessAdapter ABC + run_subprocess helper (lib_code_parser/adapters/base.py):

run_subprocess(argv: Sequence[str], *, cwd: str, timeout: float = 60.0,
               extra_env: Mapping[str, str] | None = None
               ) -> subprocess.CompletedProcess[str]
  — DET-05 hardening: utf-8 + errors=replace + capture_output + shell=False
  — _DETERMINISTIC_ENV (LC_ALL=C, LANG=C, PYTHONHASHSEED=0, PYTHONIOENCODING=utf-8)
    is unconditionally applied; extra_env is layered on top

class SubprocessAdapter(ABC):
    @abstractmethod
    def tool_argv(self, target_path: str) -> Sequence[str]: ...
    @abstractmethod
    def parse_output(self, stdout: str, stderr: str, returncode: int) -> BaseModel: ...
    def execute(self, target_path, *, cwd, timeout=60.0, extra_env=None) -> BaseModel: ...
-->

<!-- D-07-revised + RESEARCH §2.3 algorithm — pyright JSON schema actually returned:

{
    "version": "1.1.409",
    "time": "1780...",
    "generalDiagnostics": [
        {
            "file": "c:\\Users\\...\\tmp\\bad.py",
            "severity": "error",
            "message": "...",
            "range": {"start": {"line": 2, "character": 5},
                      "end": {"line": 2, "character": 20}},
            "rule": "reportMissingImports"
        },
        ...
    ],
    "summary": {"filesAnalyzed": 1, "errorCount": 2, ...}
}

Only `generalDiagnostics[].{file, severity, message, rule, range.start.line, range.end.line}`
is meaningful. Everything else is discarded.

Pyright returncode: 0 (clean) / 1 (errors found, JSON still valid). Anything else = subprocess failure.
-->

<!-- ParserConfig.python_version (Phase 1, default "3.12") — PyrightAdapter accepts this string
     and passes it via `--pythonversion <ver>`. -->
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement lib_code_parser/adapters/pyright.py — PyrightAdapter + PyrightOutput + PyrightDiagnostic</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/adapters/base.py (Phase 1 locked SubprocessAdapter + run_subprocess — subclass の正しい使い方を参照)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§2 全章 — schema 実機検証 / CLI flag 選定 / DET-03 env / Pitfall 2-3 / §Code Examples §例 2 PyrightAdapter 骨子)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md (D-05/D-06/D-07-revised/D-08/D-09 + canonical references)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_paths.py (`get_module_name` を tmpdir のファイル名に使う)
  </read_first>
  <behavior>
    - `PyrightAdapter(python_version="3.12")` を構築できる; `python_version` default = `"3.12"`
    - `PyrightAdapter(python_version="bad ver; rm -rf /")` で構築は許容するが、 `tool_argv` の戻り値は `Sequence[str]` で argv 上は単一文字列として扱われる (shell=False 保護) — 別の入力検証層で型を絞るのは Plan 02-06 type_deps extractor の責任 (ParserConfig.python_version は Phase 1 で `str` field、 厳密な Literal 化は本 plan の scope 外)
    - `adapter.tool_argv("/tmp/xx/foo.py")` が `["pyright", "--outputjson", "--pythonversion", "3.12", "-p", "/tmp/xx/pyrightconfig.json", "/tmp/xx/foo.py"]` を返す (D-08 verbatim)
    - `adapter.analyze(b"from missing_pkg import X\n", "src/foo.py")` が以下の流れで動作:
      - internal tmpdir 作成
      - `{tmpdir}/foo.py` に bytes 書き出し
      - `{tmpdir}/pyrightconfig.json` に固定 JSON 書き出し
      - run_subprocess を `extra_env = {"PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409", "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1"}` で起動
      - stdout を JSON parse、 PyrightOutput を返す
      - tmpdir は context manager で自動 cleanup
    - `parse_output(stdout="not json", stderr="...", returncode=0)` が `RuntimeError("pyright JSON parse failed: ... stdout=...")` raise from json.JSONDecodeError (D-06)
    - `parse_output(stdout="{}", stderr="...", returncode=2)` (returncode が 0/1 以外) → `RuntimeError("pyright exited with code 2: stderr=...")` raise (D-06)
    - `parse_output(stdout='{"version":"1.1.409","generalDiagnostics":[],"summary":{"errorCount":0}}', stderr="", returncode=0)` が `PyrightOutput(version="1.1.409", diagnostics=[])` を返す
    - tmpdir prefix の strip: diagnostic.file = `c:\\Users\\...\\tmp\\foo.py` → forward-slash 正規化 → tmpdir prefix が startswith マッチすれば caller_path (例 `"src/foo.py"`) に置換
    - DET-05 timeout: `analyze(...)` のタイムアウトは run_subprocess default 60.0s を継承; subprocess.TimeoutExpired → `RuntimeError("pyright timed out: ...")` raise from
    - PyrightAdapter は SubprocessAdapter 継承 → `tool_argv` / `parse_output` を override (ABC 契約) ; `execute()` base method は本 adapter では使わないが ABC として保持
    - module docstring: `Implements: AST-03, DET-03, ARC-03, DET-05` + `Traces: AST-03, DET-03, DET-05, ARC-03`
  </behavior>
  <action>
    `lib_code_parser/adapters/pyright.py` を新規作成。 RESEARCH §Code Examples §例 2 を template に実装。

    Module docstring:
    ```
    """Pyright subprocess adapter (Pydantic-validated JSON parser + canonicalizer).

    Writes raw_content to an internal tempfile.TemporaryDirectory() then runs
    `pyright --outputjson --pythonversion <ver> -p <tmpdir>/pyrightconfig.json
    <tmpdir>/<module_name>.py` with extra_env locking PYRIGHT_PYTHON_FORCE_VERSION
    to 1.1.409 (DET-03) plus PYRIGHT_PYTHON_IGNORE_WARNINGS=1 (suppresses
    nondeterministic stderr — RESEARCH §2.4). Parses ONLY generalDiagnostics
    (file, severity, message, rule, range.start.line, range.end.line) into a
    typed PyrightOutput Pydantic v2 model.

    Per RESEARCH §2.1 empirical finding: pyright --outputjson does NOT include
    resolved import / annotation type information. generalDiagnostics is the
    only meaningful payload. CONTEXT.md D-07-revised adopts this fact: Plan
    02-06 type_deps extractor extracts TypeDeps via stdlib ast walk and uses
    PyrightAdapter's reportMissingImports diagnostics solely to annotate a
    boolean `resolved` flag per TypeDep.

    Pitfall 3 mitigation: pyright auto-loads caller's pyproject.toml from cwd
    upward — we write our own pyrightconfig.json in the tmpdir and pass `-p`
    explicitly so caller config is invisible.

    D-06 fail-loudly: any subprocess failure (returncode not in {0, 1}),
    json.JSONDecodeError, or subprocess.TimeoutExpired is re-raised as
    RuntimeError with diagnostic context. Silent empty PyrightOutput is never
    returned — that would let DET-01 byte-identical depend on environment state.

    Implements: AST-03, DET-03, ARC-03, DET-05
    Traces: AST-03, DET-03, DET-05, ARC-03
    """
    ```

    Imports:
    ```
    from __future__ import annotations

    import json
    import subprocess
    import tempfile
    from collections.abc import Sequence
    from pathlib import Path

    from pydantic import BaseModel, ConfigDict, Field

    from lib_code_parser._paths import get_module_name
    from lib_code_parser.adapters.base import SubprocessAdapter, run_subprocess

    __all__ = ["PyrightAdapter", "PyrightOutput", "PyrightDiagnostic"]
    ```

    Constants:
    ```
    # DET-03 + RESEARCH §2.4: hard-code both env vars; do not allow caller override.
    _PYRIGHT_DET_ENV: dict[str, str] = {
        "PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409",
        "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1",
    }

    # Pyright config locking caller pyproject.toml out (Pitfall 3) and forcing
    # reportMissingImports to error level (so generalDiagnostics fires for unresolved).
    _PYRIGHT_CONFIG_JSON: str = json.dumps({
        "include": ["."],
        "reportMissingImports": "error",
    })

    # Accepted pyright returncodes per CLI docs:
    # 0 = analysis completed, no errors
    # 1 = analysis completed, errors were reported (JSON still emitted to stdout)
    # Anything else = startup / argv / fatal subprocess error
    _OK_RETURNCODES: frozenset[int] = frozenset({0, 1})
    ```

    Models:
    ```
    class PyrightDiagnostic(BaseModel):
        """One generalDiagnostics entry extracted from pyright --outputjson.

        Only the fields needed by Plan 02-06 type_deps extractor's `resolved`
        annotation logic are retained. Other pyright fields (range.character
        offsets, end positions in some cases) are discarded per D-07.
        """

        model_config = ConfigDict(extra="forbid")

        file: str                        # forward-slash, tmpdir-stripped to caller_path
        severity: str                    # "error" | "warning" | "information"
        message: str
        rule: str = ""                   # e.g. "reportMissingImports"; empty if pyright omits
        start_line: int                  # 0-based per pyright; Plan 02-06 may +1 if needed
        end_line: int = 0


    class PyrightOutput(BaseModel):
        """Top-level parsed output of pyright --outputjson.

        Only `version` (DET-03 audit evidence) and `diagnostics` (RESEARCH §2.3
        unresolved-line detection) are retained. version / time / summary fields
        are discarded as nondeterministic or unused.
        """

        model_config = ConfigDict(extra="forbid")

        version: str
        diagnostics: list[PyrightDiagnostic] = Field(default_factory=list)
    ```

    PyrightAdapter class:
    ```
    class PyrightAdapter(SubprocessAdapter):
        """Subprocess adapter for pyright --outputjson (single-file analysis).

        Caller passes raw_content (bytes) + path (caller-supplied label); the
        adapter creates an internal tmpdir, writes the bytes there, runs pyright
        with the locked env, parses generalDiagnostics, and tears down the tmpdir.
        Caller's file-system state is never touched (D-05).
        """

        def __init__(self, python_version: str = "3.12") -> None:
            self.python_version = python_version

        # SubprocessAdapter abstract method implementations ----------------------

        def tool_argv(self, target_path: str) -> Sequence[str]:
            """Build the pyright CLI argv per D-08 / RESEARCH §2.2."""
            tmpdir = str(Path(target_path).parent)
            return [
                "pyright",
                "--outputjson",
                "--pythonversion",
                self.python_version,
                "-p",
                str(Path(tmpdir) / "pyrightconfig.json"),
                target_path,
            ]

        def parse_output(
            self,
            stdout: str,
            stderr: str,
            returncode: int,
            *,
            tmpdir: str = "",
            caller_path: str = "",
        ) -> PyrightOutput:
            """Parse pyright stdout into typed PyrightOutput; fail-loudly per D-06.

            tmpdir / caller_path are adapter-specific kwargs (not part of the
            SubprocessAdapter ABC); the base ABC's parse_output signature accepts
            only stdout/stderr/returncode, so this override widens it with
            keyword-only canonicalization context. SubprocessAdapter.execute()
            does not pass these — analyze() calls parse_output directly with them.
            """
            if returncode not in _OK_RETURNCODES:
                raise RuntimeError(
                    f"pyright exited with code {returncode}: stderr={stderr[:500]}"
                )
            try:
                raw = json.loads(stdout)
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"pyright JSON parse failed: {e}; stdout={stdout[:500]}"
                ) from e

            tmpdir_fwd = tmpdir.replace("\\", "/") if tmpdir else ""
            diagnostics: list[PyrightDiagnostic] = []
            for d in raw.get("generalDiagnostics", []):
                file_path = str(d.get("file", "")).replace("\\", "/")
                if tmpdir_fwd and file_path.startswith(tmpdir_fwd):
                    file_path = caller_path or file_path
                rng = d.get("range", {})
                start = rng.get("start", {})
                end = rng.get("end", {})
                diagnostics.append(
                    PyrightDiagnostic(
                        file=file_path,
                        severity=str(d.get("severity", "")),
                        message=str(d.get("message", "")),
                        rule=str(d.get("rule", "")),
                        start_line=int(start.get("line", 0)),
                        end_line=int(end.get("line", 0)),
                    )
                )
            return PyrightOutput(
                version=str(raw.get("version", "")),
                diagnostics=diagnostics,
            )

        # Adapter-specific public entry point -----------------------------------

        def analyze(self, raw_content: bytes, path: str) -> PyrightOutput:
            """Run pyright on raw_content (bytes) labelled as `path`; return PyrightOutput.

            D-05: caller-agnostic I/O — raw_content is written only to an internal
            tempfile.TemporaryDirectory(), torn down on exit.
            D-06: fail-loudly via parse_output's RuntimeError raises; TimeoutExpired
            is re-raised here as RuntimeError too.
            """
            module_name = get_module_name(path)
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                target = tmpdir_path / f"{module_name}.py"
                target.write_bytes(raw_content)
                config_path = tmpdir_path / "pyrightconfig.json"
                config_path.write_text(_PYRIGHT_CONFIG_JSON, encoding="utf-8")

                argv = self.tool_argv(str(target))
                try:
                    result = run_subprocess(
                        argv,
                        cwd=tmpdir,
                        timeout=60.0,
                        extra_env=_PYRIGHT_DET_ENV,
                    )
                except subprocess.TimeoutExpired as e:
                    raise RuntimeError(
                        f"pyright timed out after {e.timeout}s on {path}"
                    ) from e
                except FileNotFoundError as e:
                    # pyright executable not installed — D-06 fail-loudly
                    raise RuntimeError(
                        f"pyright executable not found ({e}); install pyright[nodejs]==1.1.409"
                    ) from e

                return self.parse_output(
                    stdout=result.stdout,
                    stderr=result.stderr,
                    returncode=result.returncode,
                    tmpdir=tmpdir,
                    caller_path=path,
                )
    ```

    `lib_code_parser/adapters/__init__.py` の barrel re-export 拡張は本 plan では行わない (Phase 1 で `run_subprocess` / `SubprocessAdapter` のみが re-export 済、 PyrightAdapter の barrel exposure は Plan 02-07 Wave 3 closer で実施 — 02-07 が `lib_code_parser/__init__.py` barrel と executor を編集する権限を持つ)。

    `tests/unit/adapters/__init__.py` を空 (1-line docstring `"""Unit tests for adapters (subprocess isolation layer)."""`) で新規作成。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/test_pyright_adapter.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `python -c "from lib_code_parser.adapters.pyright import PyrightAdapter, PyrightOutput, PyrightDiagnostic; a = PyrightAdapter('3.12'); print(a.python_version)"` 出力 `3.12`
    - `grep -c "PYRIGHT_PYTHON_FORCE_VERSION" lib_code_parser/adapters/pyright.py` >= 2 (constant 定義 + extra_env で使用 — DET-03 grep gate)
    - `grep -c "\"1.1.409\"" lib_code_parser/adapters/pyright.py` >= 1 (DET-03 pin の grep 証跡)
    - `grep -c "PYRIGHT_PYTHON_IGNORE_WARNINGS" lib_code_parser/adapters/pyright.py` >= 1 (RESEARCH §2.4 抑止の grep 証跡)
    - `grep -c "TemporaryDirectory" lib_code_parser/adapters/pyright.py` >= 1 (D-05 internal tmpdir)
    - `grep -c "raise RuntimeError" lib_code_parser/adapters/pyright.py` >= 3 (D-06 3 件の fail-loudly path: returncode / JSONDecodeError / TimeoutExpired)
    - `grep -c "ast\.parse" lib_code_parser/adapters/pyright.py` が 0 (adapter は parse しない — AST-05 適用範囲外だが整合)
    - `grep -c "Implements: AST-03" lib_code_parser/adapters/pyright.py` = 1 (TRC-02)
    - `grep -c "Traces: AST-03" lib_code_parser/adapters/pyright.py` >= 1 (TRC-03)
    - `grep -c '"--outputjson"' lib_code_parser/adapters/pyright.py` = 1 (D-08 CLI flag)
    - `grep -c '"--pythonversion"' lib_code_parser/adapters/pyright.py` = 1
    - `grep -c '"-p"' lib_code_parser/adapters/pyright.py` >= 1 (Pitfall 3 mitigation grep 証跡)
    - `grep -c "extra=\"forbid\"" lib_code_parser/adapters/pyright.py` >= 2 (SCH-02 — PyrightDiagnostic と PyrightOutput 両方)
    - Phase 1 baseline parity: `pytest tests/parity/ tests/acceptance/test_fr01_function_extraction.py tests/acceptance/test_fr02_callgraph.py tests/acceptance/test_fr03_type_deps.py tests/acceptance/test_fr05_trace_tags.py tests/acceptance/test_fr06_disabled.py -x -q` exit 0 (Phase 1 既存 baseline + Plan 02-04 で意図的に壊れる test_fr04_contracts.py を除外)
    - `ruff check lib_code_parser/adapters/pyright.py` exit 0
  </acceptance_criteria>
  <done>PyrightAdapter が SubprocessAdapter ABC を正しく subclass。 DET-03 env + D-06 fail-loudly + D-07 tmpdir strip + Pitfall 3 mitigation + caller-agnostic I/O が grep gate で固定。 PyrightOutput / PyrightDiagnostic が typed Pydantic v2 (extra="forbid")。</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Wave 0 — tests/unit/test_pyright_adapter.py (argv / env / parse error / timeout / smoke)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-VALIDATION.md (Wave 0 必須リスト: `tests/unit/test_pyright_adapter.py` + その期待 test 群)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§2 全章 + §Pitfall 2-3 / §6.3 docstring template)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/adapters/base.py (run_subprocess は subprocess.run を呼ぶ — monkeypatch の対象は `lib_code_parser.adapters.base.subprocess.run` ではなく、 PyrightAdapter から呼ばれる関数を mock するため、 直接 `lib_code_parser.adapters.pyright.run_subprocess` を monkeypatch する設計が cleaner)
  </read_first>
  <behavior>
    Tests in `tests/unit/test_pyright_adapter.py` — pyright が install されている前提を持つ test と mock-only test を分離:

    **mock-based tests (CI で確定動作):**
    1. `test_tool_argv_includes_outputjson_pythonversion_p_target` — `adapter.tool_argv("/tmp/x/foo.py")` の戻り値が `["pyright", "--outputjson", "--pythonversion", "3.12", "-p", "/tmp/x/pyrightconfig.json", "/tmp/x/foo.py"]` であることを assert (リスト equality)
    2. `test_det_03_env_var_set` (VALIDATION.md 必須 — `test_det_03_env_var_set`) — `monkeypatch.setattr("lib_code_parser.adapters.pyright.run_subprocess", mock_run)` で run_subprocess を mock 化、 `adapter.analyze(b"", "x.py")` を呼んだとき mock_run が受け取った `extra_env` dict が `{"PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409", "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1"}` を含むことを assert (両 key 必須)
    3. `test_pyrightconfig_json_written_to_tmpdir` — mock_run を呼ぶ前に tmpdir 内の `pyrightconfig.json` が存在し、 内容が `{"include": ["."], "reportMissingImports": "error"}` の JSON であることを assert (mock 内で `cwd` 引数経由で tmpdir パスを取り、 Path から読む)
    4. `test_target_file_written_with_module_name_basename` — `analyze(b"def foo(): pass\n", "src/order_service.py")` で tmpdir 内に `order_service.py` (get_module_name 結果) が作成されることを assert
    5. `test_parse_output_returncode_2_raises_runtime_error` — `adapter.parse_output(stdout="{}", stderr="boom", returncode=2)` が `RuntimeError` を raise、 メッセージに `"pyright exited with code 2"` を含むことを assert
    6. `test_parse_output_returncode_0_or_1_accepted` — returncode 0 と 1 の両方で `RuntimeError` を raise しないことを assert (空 stdout の場合は JSON parse error が出るが、 `stdout='{"version":"1.1.409","generalDiagnostics":[]}'` のような minimal payload では成功する)
    7. `test_parse_output_invalid_json_raises_runtime_error` — `adapter.parse_output(stdout="not json", stderr="", returncode=0)` が `RuntimeError` を raise、 メッセージに `"pyright JSON parse failed"` を含むこと、 cause chain (`raise ... from`) で `json.JSONDecodeError` が `__cause__` であることを assert
    8. `test_parse_output_strips_tmpdir_prefix_in_file_path` — input `{"version":"1.1.409","generalDiagnostics":[{"file":"/tmp/xx/foo.py","severity":"error","message":"x","rule":"reportMissingImports","range":{"start":{"line":2,"character":0},"end":{"line":2,"character":5}}}]}` を `tmpdir="/tmp/xx"`、 `caller_path="src/foo.py"` で渡したら、 戻りの diagnostic.file が `"src/foo.py"` (caller_path に置換) であることを assert
    9. `test_parse_output_forward_slash_normalizes_backslash_paths` — Windows path `c:\\Users\\bothe\\AppData\\foo.py` を含む input が `c:/Users/bothe/AppData/foo.py` に変換される (caller_path 置換が startswith match しない場合の normalize 行動)
    10. `test_parse_output_discards_unused_fields` — input が `{"version":"1.1.409","time":"123","summary":{"errorCount":0},"generalDiagnostics":[]}` で、 PyrightOutput の `extra="forbid"` を破らないため `version` + `diagnostics` のみ抽出される。 `model_dump_json()` 出力に `"time"` も `"summary"` も含まれない
    11. `test_timeout_raises_runtime_error` — `monkeypatch` で run_subprocess を `raise subprocess.TimeoutExpired(cmd=[], timeout=60.0)` に差し替え、 `analyze(b"", "x.py")` が `RuntimeError("pyright timed out after 60.0s on x.py")` を raise from することを assert
    12. `test_file_not_found_raises_runtime_error` — `monkeypatch` で run_subprocess を `raise FileNotFoundError("pyright")` に差し替え、 RuntimeError に re-raise されることを assert (D-06 install 失敗 path)

    **smoke test (実 pyright 起動、 環境依存):**
    13. `test_real_pyright_analyzes_clean_python` (`@pytest.mark.skipif(not _has_pyright(), reason="pyright not installed")`) — 実 PyrightAdapter で `b"def foo() -> int:\n    return 1\n"` を analyze、 `PyrightOutput.version` が空でない (pyright が実際に起動した) ことと `len(diagnostics) == 0` (clean Python なので no diagnostics) を assert

    `_has_pyright()` helper:
    ```
    def _has_pyright() -> bool:
        try:
            subprocess.run(
                ["pyright", "--version"],
                capture_output=True, timeout=10.0, check=False,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    ```
  </behavior>
  <action>
    `tests/unit/test_pyright_adapter.py` を新規作成。 上記 13 件の test を実装。 共通 import:

    ```
    from __future__ import annotations

    import json
    import subprocess
    from pathlib import Path

    import pytest

    from lib_code_parser.adapters.pyright import (
        PyrightAdapter, PyrightOutput, PyrightDiagnostic,
    )
    ```

    `monkeypatch.setattr("lib_code_parser.adapters.pyright.run_subprocess", mock_run)` の pattern で run_subprocess を差し替える。 mock_run は副作用として received argv + cwd + extra_env をテスト側で参照可能な class attribute / list に push する。 例:

    ```
    class _MockRun:
        def __init__(self, stdout: str = "{}", stderr: str = "", returncode: int = 0):
            self.calls: list[dict] = []
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode

        def __call__(self, argv, *, cwd, timeout=60.0, extra_env=None):
            self.calls.append({
                "argv": list(argv),
                "cwd": cwd,
                "timeout": timeout,
                "extra_env": dict(extra_env) if extra_env else {},
            })
            return subprocess.CompletedProcess(
                args=list(argv),
                returncode=self.returncode,
                stdout=self.stdout,
                stderr=self.stderr,
            )
    ```

    test #3 (`test_pyrightconfig_json_written_to_tmpdir`) では mock_run の `cwd` 引数から tmpdir パスを取り、 `Path(cwd) / "pyrightconfig.json"` を open して assert する。

    test #13 (smoke) は VALIDATION.md の sampling rate を満たすために必要だが、 pyright が CI runner に install されていない場合に skip するべき。 `@pytest.mark.skipif(not _has_pyright(), reason="pyright not installed")` を付ける。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/test_pyright_adapter.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/test_pyright_adapter.py -x -q` exit 0; mock-based test 12 件は必ず pass、 smoke test 1 件は環境次第で skip もしくは pass (どちらも fail にしない)
    - VALIDATION.md 必須の `test_det_03_env_var_set` test 関数が存在し pass する: `grep -c "def test_det_03_env_var_set" tests/unit/test_pyright_adapter.py` = 1
    - `grep -c "PYRIGHT_PYTHON_FORCE_VERSION" tests/unit/test_pyright_adapter.py` >= 1 (test 内で env var assertion を持つ)
    - `grep -c "PYRIGHT_PYTHON_IGNORE_WARNINGS" tests/unit/test_pyright_adapter.py` >= 1
    - `grep -c "TimeoutExpired" tests/unit/test_pyright_adapter.py` >= 1 (timeout path test 存在)
    - `grep -c "JSONDecodeError" tests/unit/test_pyright_adapter.py` >= 1 (JSON parse error path test 存在)
    - `grep -c "raise RuntimeError\|RuntimeError" tests/unit/test_pyright_adapter.py` >= 2 (fail-loudly test 群)
    - フル baseline: `pytest tests/parity/ tests/acceptance/test_fr01_function_extraction.py tests/acceptance/test_fr02_callgraph.py tests/acceptance/test_fr03_type_deps.py tests/acceptance/test_fr05_trace_tags.py tests/acceptance/test_fr06_disabled.py -x -q` exit 0 (test_fr04_contracts.py は Plan 02-04 で意図的に壊れている)
    - `ruff check tests/unit/test_pyright_adapter.py` exit 0
  </acceptance_criteria>
  <done>VALIDATION.md Wave 0 必須リストの `tests/unit/test_pyright_adapter.py` charge close、 12 + 1 件 (12 mock + 1 smoke) で argv / env / parse error / timeout / tmpdir strip / Pitfall 3 mitigation を全 mock 単位で実証。 DET-03 env injection が grep + pytest で固定。</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| caller raw_content (bytes) → internal tmpdir file write | bytes は internal tmpdir に書き出されるだけ; 退場時 (`__exit__`) で削除。 caller の file system 不可視 (D-05) |
| pyright stdout (untrusted JSON) → PyrightOutput model | json.loads + Pydantic extra="forbid" で schema drift を catch; subkey 抽出は明示的 5 件のみ (RESEARCH §2.3 D-07 解釈) |
| pyright stderr → log/抑止 | PYRIGHT_PYTHON_IGNORE_WARNINGS=1 で「new pyright version」 warning を抑止 (RESEARCH §2.4 Pitfall 2 mitigation) |
| caller python_version str → pyright `--pythonversion` argv | shell=False で injection 不可、 caller の任意文字列が argv 1 単位として渡される。 Pydantic ParserConfig.python_version の Literal 化は本 plan の scope 外 (Phase 3+ で検討) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-22 | Tampering | DET-03 env var 未注入で pyright wrapper が caller 環境の latest version を起動 | mitigate | `_PYRIGHT_DET_ENV` を adapter 内 hard-code、 caller override 不可。 Task 2 `test_det_03_env_var_set` で grep + pytest 二重防御 |
| T-02-23 | Tampering | Pitfall 3: pyright が caller 環境の pyproject.toml を auto-load して decision drift | mitigate | tmpdir に固定 `pyrightconfig.json` を書き出し `-p` で明示指定。 Task 2 `test_pyrightconfig_json_written_to_tmpdir` で実証 |
| T-02-24 | DoS | pyright 起動失敗 / hang | mitigate | run_subprocess timeout=60.0 (Phase 1 既定)、 TimeoutExpired → RuntimeError raise from。 FileNotFoundError 同様 |
| T-02-25 | Tampering | silent empty PyrightOutput (DET-01 byte-identical 前提 違反) | mitigate | D-06 fail-loudly: 全 error path で RuntimeError raise (空 PyrightOutput を返さない)。 Task 2 で 3 件の error path を unit 実証 |
| T-02-26 | Information disclosure | tmpdir cleanup 失敗で raw_content が file system に残留 | mitigate | tempfile.TemporaryDirectory() context manager で `__exit__` 保証 (例外時も削除)、 Phase 1 `run_subprocess` 規約と integrating |
| T-02-27 | Tampering | argv injection via python_version str | accept | shell=False enforced; caller の python_version が argv 1 単位として安全に渡る (Phase 1 `run_subprocess` の `shell=False` 既定で防護)。 Literal 化は Phase 3+ |
| T-02-28 | Supply chain | pyright wrapper script の lockfile drift | mitigate | DET-03 = `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` で pin、 Task 1 grep gate で固定; Phase 1 で `pyright[nodejs]==1.1.409` を pyproject.toml に declared 済 |
</threat_model>

<verification>
- `pytest tests/unit/test_pyright_adapter.py -x -q` 12 mock test pass + 1 smoke (skip or pass)
- DET-03 grep gate: `grep -c "PYRIGHT_PYTHON_FORCE_VERSION" lib_code_parser/adapters/pyright.py` >= 2, `grep -c "\"1.1.409\"" lib_code_parser/adapters/pyright.py` >= 1
- Pitfall 2 抑止 grep: `grep -c "PYRIGHT_PYTHON_IGNORE_WARNINGS" lib_code_parser/adapters/pyright.py` >= 1
- D-06 fail-loudly grep: `grep -c "raise RuntimeError" lib_code_parser/adapters/pyright.py` >= 3 (returncode / json / timeout 3 件)
- Pitfall 3 mitigation grep: `grep -c "pyrightconfig.json" lib_code_parser/adapters/pyright.py` >= 2
- D-05 caller-agnostic I/O grep: `grep -c "TemporaryDirectory" lib_code_parser/adapters/pyright.py` >= 1
- TRC-02 / TRC-03 docstring grep
- フル baseline parity (test_fr04_contracts.py 除外) 維持
- `ruff check lib_code_parser/adapters/ tests/unit/test_pyright_adapter.py` exit 0
</verification>

<success_criteria>
- ROADMAP Phase 2 success criterion 2 のうち pyright subprocess + DET-03 + D-08 CLI 選定 + 1.1.409 pin が実装される
- ROADMAP Phase 2 success criterion 4 の前提として PyrightAdapter が isolated 呼び出し可能 (`from lib_code_parser.adapters.pyright import PyrightAdapter`)
- D-05 caller-agnostic I/O (internal tmpdir + bytes) が grep + unit で実証
- D-06 fail-loudly 3 path (returncode / JSON / timeout) が unit で実証
- D-07 forward-slash 正規化 + tmpdir strip が unit で実証
- RESEARCH §A1 mitigation の前提として PyrightOutput が raw_content を必要としない (Plan 02-06 で raw_content を CAV.raw_content 経由で取得する設計が成立)
- Pitfall 2 / 3 mitigation が hard-coded で固定
</success_criteria>

<output>
Create `.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-05-SUMMARY.md` when done. Include:
1. pytest output (12 mock + 1 smoke = 13 件 status)
2. DET-03 / Pitfall 2-3 / D-06 grep gate evidence
3. PyrightOutput / PyrightDiagnostic model 構造 dump
4. 実 pyright 起動 smoke test の結果 (skip / pass / version)
5. v0.1.0 baseline parity (test_fr04_contracts.py 除外) 維持
</output>
