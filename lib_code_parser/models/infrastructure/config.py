"""Typed ParserConfig (ARC-05).

Replaces v0.1.0 untyped ``params: dict[str, object]`` with explicit typed fields
per D-08.

Traces: ARC-05, SCH-02.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ParserConfig(BaseModel):
    """Typed configuration for the code parser executor.

    All previously-untyped ``params`` keys are now explicit typed fields.
    Unknown keyword arguments are rejected at construction time via
    ``extra="forbid"`` (SCH-02).
    """

    model_config = ConfigDict(extra="forbid")

    artifact_type: str
    executor_lib: str
    enabled: bool = True
    language: Literal["python", "cpp"] = "python"
    extract_contracts: bool = True
    compile_args: list[str] = Field(default_factory=lambda: ["-std=c++17"])
    python_version: str = "3.12"
    # CR-01 (Option B): opt-in pyright import-resolution oracle. Default False
    # keeps execute() a PURE function of (raw_content, path, config) — no
    # subprocess, no network, no environment dependence. Set True only when the
    # verifier's Layer M bisimulation path needs the reportMissingImports
    # `resolved` flag (then the D-06 fail-loudly pyright path applies).
    resolve_imports: bool = False
