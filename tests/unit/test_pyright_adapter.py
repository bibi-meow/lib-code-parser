"""Unit tests for PyrightAdapter (subprocess-isolated pyright wrapper).

Covers: CLI argv build (D-08), DET-03 env injection, Pitfall 3 config
isolation, D-06 fail-loudly (returncode / JSONDecodeError / TimeoutExpired /
FileNotFoundError), D-07 tmpdir-prefix strip + forward-slash normalization,
and one environment-dependent smoke test against real pyright.

run_subprocess is monkeypatched at ``lib_code_parser.adapters.pyright``
import site so the adapter's own call path is exercised without spawning a
real subprocess.

Traces: AST-03, DET-03, DET-05, ARC-03
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from lib_code_parser.adapters.pyright import (
    PyrightAdapter,
    PyrightDiagnostic,
    PyrightOutput,
)


class _MockRun:
    """Stand-in for run_subprocess; records every call and returns a canned result."""

    def __init__(self, stdout: str = "{}", stderr: str = "", returncode: int = 0):
        self.calls: list[dict] = []
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def __call__(self, argv, *, cwd, timeout=60.0, extra_env=None):
        self.calls.append(
            {
                "argv": list(argv),
                "cwd": cwd,
                "timeout": timeout,
                "extra_env": dict(extra_env) if extra_env else {},
            }
        )
        return subprocess.CompletedProcess(
            args=list(argv),
            returncode=self.returncode,
            stdout=self.stdout,
            stderr=self.stderr,
        )


def _has_pyright() -> bool:
    try:
        subprocess.run(
            ["pyright", "--version"],
            capture_output=True,
            timeout=10.0,
            check=False,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# --- 1. argv build (D-08) -------------------------------------------------


def test_tool_argv_includes_outputjson_pythonversion_p_target() -> None:
    adapter = PyrightAdapter("3.12")
    argv = list(adapter.tool_argv("/tmp/x/foo.py"))
    assert argv == [
        "pyright",
        "--outputjson",
        "--pythonversion",
        "3.12",
        "-p",
        str(Path("/tmp/x") / "pyrightconfig.json"),
        "/tmp/x/foo.py",
    ]


# --- 2. DET-03 env injection (VALIDATION.md required) ---------------------


def test_det_03_env_var_set(monkeypatch: pytest.MonkeyPatch) -> None:
    mock = _MockRun(stdout='{"version":"1.1.409","generalDiagnostics":[]}')
    monkeypatch.setattr("lib_code_parser.adapters.pyright.run_subprocess", mock)
    adapter = PyrightAdapter("3.12")
    adapter.analyze(b"", "x.py")
    assert len(mock.calls) == 1
    env = mock.calls[0]["extra_env"]
    assert env.get("PYRIGHT_PYTHON_FORCE_VERSION") == "1.1.409"
    assert env.get("PYRIGHT_PYTHON_IGNORE_WARNINGS") == "1"


# --- 3. Pitfall 3: pyrightconfig.json written to tmpdir -------------------


def test_pyrightconfig_json_written_to_tmpdir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    class _CfgRun(_MockRun):
        def __call__(self, argv, *, cwd, timeout=60.0, extra_env=None):
            cfg = Path(cwd) / "pyrightconfig.json"
            seen["content"] = cfg.read_text(encoding="utf-8")
            return super().__call__(
                argv, cwd=cwd, timeout=timeout, extra_env=extra_env
            )

    mock = _CfgRun(stdout='{"version":"1.1.409","generalDiagnostics":[]}')
    monkeypatch.setattr("lib_code_parser.adapters.pyright.run_subprocess", mock)
    PyrightAdapter().analyze(b"x = 1\n", "src/foo.py")
    parsed = json.loads(seen["content"])
    assert parsed == {"include": ["."], "reportMissingImports": "error"}


# --- 4. target file written under module-name basename --------------------


def test_target_file_written_with_module_name_basename(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, bool] = {}

    class _FileRun(_MockRun):
        def __call__(self, argv, *, cwd, timeout=60.0, extra_env=None):
            seen["exists"] = (Path(cwd) / "order_service.py").is_file()
            return super().__call__(
                argv, cwd=cwd, timeout=timeout, extra_env=extra_env
            )

    mock = _FileRun(stdout='{"version":"1.1.409","generalDiagnostics":[]}')
    monkeypatch.setattr("lib_code_parser.adapters.pyright.run_subprocess", mock)
    PyrightAdapter().analyze(b"def foo(): pass\n", "src/order_service.py")
    assert seen["exists"] is True


# --- 5. returncode not in {0,1} -> RuntimeError (D-06) --------------------


def test_parse_output_returncode_2_raises_runtime_error() -> None:
    adapter = PyrightAdapter()
    with pytest.raises(RuntimeError, match="pyright exited with code 2"):
        adapter.parse_output(stdout="{}", stderr="boom", returncode=2)


# --- 6. returncode 0 and 1 both accepted ---------------------------------


def test_parse_output_returncode_0_or_1_accepted() -> None:
    adapter = PyrightAdapter()
    payload = '{"version":"1.1.409","generalDiagnostics":[]}'
    out0 = adapter.parse_output(stdout=payload, stderr="", returncode=0)
    out1 = adapter.parse_output(stdout=payload, stderr="", returncode=1)
    assert out0.version == "1.1.409"
    assert out1.version == "1.1.409"
    assert out0.diagnostics == []
    assert out1.diagnostics == []


# --- 7. invalid JSON -> RuntimeError from JSONDecodeError (D-06) ----------


def test_parse_output_invalid_json_raises_runtime_error() -> None:
    adapter = PyrightAdapter()
    with pytest.raises(RuntimeError, match="pyright JSON parse failed") as exc:
        adapter.parse_output(stdout="not json", stderr="", returncode=0)
    assert isinstance(exc.value.__cause__, json.JSONDecodeError)


# --- 8. tmpdir prefix stripped -> caller_path -----------------------------


def test_parse_output_strips_tmpdir_prefix_in_file_path() -> None:
    adapter = PyrightAdapter()
    stdout = json.dumps(
        {
            "version": "1.1.409",
            "generalDiagnostics": [
                {
                    "file": "/tmp/xx/foo.py",
                    "severity": "error",
                    "message": "x",
                    "rule": "reportMissingImports",
                    "range": {
                        "start": {"line": 2, "character": 0},
                        "end": {"line": 2, "character": 5},
                    },
                }
            ],
        }
    )
    out = adapter.parse_output(
        stdout=stdout,
        stderr="",
        returncode=1,
        tmpdir="/tmp/xx",
        caller_path="src/foo.py",
    )
    assert len(out.diagnostics) == 1
    assert out.diagnostics[0].file == "src/foo.py"
    assert out.diagnostics[0].start_line == 2
    assert out.diagnostics[0].end_line == 2
    assert out.diagnostics[0].rule == "reportMissingImports"


# --- 9. backslash forward-slash normalization (no prefix match) ----------


def test_parse_output_forward_slash_normalizes_backslash_paths() -> None:
    adapter = PyrightAdapter()
    stdout = json.dumps(
        {
            "version": "1.1.409",
            "generalDiagnostics": [
                {
                    "file": "c:\\Users\\bothe\\AppData\\foo.py",
                    "severity": "warning",
                    "message": "y",
                    "rule": "",
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 0},
                    },
                }
            ],
        }
    )
    out = adapter.parse_output(
        stdout=stdout,
        stderr="",
        returncode=1,
        tmpdir="/some/other/dir",
        caller_path="src/foo.py",
    )
    assert out.diagnostics[0].file == "c:/Users/bothe/AppData/foo.py"


# --- 10. unused top-level fields discarded (extra="forbid") --------------


def test_parse_output_discards_unused_fields() -> None:
    adapter = PyrightAdapter()
    stdout = json.dumps(
        {
            "version": "1.1.409",
            "time": "123",
            "summary": {"errorCount": 0},
            "generalDiagnostics": [],
        }
    )
    out = adapter.parse_output(stdout=stdout, stderr="", returncode=0)
    dumped = out.model_dump_json()
    assert "time" not in dumped
    assert "summary" not in dumped
    assert out.version == "1.1.409"
    assert out.diagnostics == []


# --- 11. timeout -> RuntimeError (D-06) -----------------------------------


def test_timeout_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(argv, *, cwd, timeout=60.0, extra_env=None):
        raise subprocess.TimeoutExpired(cmd=list(argv), timeout=60.0)

    monkeypatch.setattr("lib_code_parser.adapters.pyright.run_subprocess", _boom)
    adapter = PyrightAdapter()
    with pytest.raises(RuntimeError, match="pyright timed out after 60.0s on x.py"):
        adapter.analyze(b"", "x.py")


# --- 12. FileNotFoundError -> RuntimeError (D-06 install failure) ---------


def test_file_not_found_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _missing(argv, *, cwd, timeout=60.0, extra_env=None):
        raise FileNotFoundError("pyright")

    monkeypatch.setattr("lib_code_parser.adapters.pyright.run_subprocess", _missing)
    adapter = PyrightAdapter()
    with pytest.raises(RuntimeError, match="pyright executable not found"):
        adapter.analyze(b"", "x.py")


# --- 13. real pyright smoke (env-dependent) -------------------------------


@pytest.mark.skipif(not _has_pyright(), reason="pyright not installed")
def test_real_pyright_analyzes_clean_python() -> None:
    adapter = PyrightAdapter("3.12")
    out = adapter.analyze(b"def foo() -> int:\n    return 1\n", "clean.py")
    assert isinstance(out, PyrightOutput)
    assert out.version != ""
    assert len(out.diagnostics) == 0


def test_models_are_pydantic_with_forbid() -> None:
    # Sanity: both models reject unknown keys (SCH-02 extra="forbid").
    with pytest.raises(Exception):
        PyrightDiagnostic(
            file="a",
            severity="error",
            message="m",
            start_line=0,
            bogus=1,  # type: ignore[call-arg]
        )
    with pytest.raises(Exception):
        PyrightOutput(version="1.1.409", bogus=1)  # type: ignore[call-arg]
