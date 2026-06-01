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


# DET-03 + RESEARCH §2.4: hard-code both env vars; do not allow caller override.
_PYRIGHT_DET_ENV: dict[str, str] = {
    "PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409",
    "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1",
}

# Pyright config locking caller pyproject.toml out (Pitfall 3) and forcing
# reportMissingImports to error level (so generalDiagnostics fires for unresolved).
_PYRIGHT_CONFIG_JSON: str = json.dumps(
    {
        "include": ["."],
        "reportMissingImports": "error",
    }
)

# Accepted pyright returncodes per CLI docs:
# 0 = analysis completed, no errors
# 1 = analysis completed, errors were reported (JSON still emitted to stdout)
# Anything else = startup / argv / fatal subprocess error
_OK_RETURNCODES: frozenset[int] = frozenset({0, 1})


class PyrightDiagnostic(BaseModel):
    """One generalDiagnostics entry extracted from pyright --outputjson.

    Only the fields needed by Plan 02-06 type_deps extractor's `resolved`
    annotation logic are retained. Other pyright fields (range.character
    offsets, end positions in some cases) are discarded per D-07.
    """

    model_config = ConfigDict(extra="forbid")

    file: str  # forward-slash, tmpdir-stripped to caller_path
    severity: str  # "error" | "warning" | "information"
    message: str
    rule: str = ""  # e.g. "reportMissingImports"; empty if pyright omits
    start_line: int  # 0-based per pyright; Plan 02-06 may +1 if needed
    end_line: int = 0


class PyrightOutput(BaseModel):
    """Top-level parsed output of pyright --outputjson.

    Only `version` (DET-03 audit evidence) and `diagnostics` (RESEARCH §2.3
    unresolved-line detection) are retained. time / summary fields are
    discarded as nondeterministic or unused.
    """

    model_config = ConfigDict(extra="forbid")

    version: str
    diagnostics: list[PyrightDiagnostic] = Field(default_factory=list)


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

        tmpdir / caller_path are adapter-specific keyword-only kwargs (not part
        of the SubprocessAdapter ABC, whose parse_output signature accepts only
        stdout/stderr/returncode). SubprocessAdapter.execute() does not pass
        these — analyze() calls parse_output directly with them.
        """
        if returncode not in _OK_RETURNCODES:
            raise RuntimeError(f"pyright exited with code {returncode}: stderr={stderr[:500]}")
        try:
            raw = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"pyright JSON parse failed: {e}; stdout={stdout[:500]}") from e

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
        and FileNotFoundError are re-raised here as RuntimeError too.
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
                raise RuntimeError(f"pyright timed out after {e.timeout}s on {path}") from e
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
