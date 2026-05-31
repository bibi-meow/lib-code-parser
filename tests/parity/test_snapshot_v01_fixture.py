"""D-04 snapshot test: shipped v0.1.0 EXAMPLE_SOURCE fixture byte-identical comparison.

Locks the Phase 2 dispatch-driven executor output for the conftest fixture so
that any future drift (Phase 3+ primitive additions, sort changes, model field
changes) is caught at PR time. The fixture
(tests/parity/fixtures/v01_snapshot.json) is regenerated via
scripts/generate_v01_snapshot.py.

The executor's type_deps extractor invokes the PyrightAdapter subprocess, so the
module skips when pyright is not installed or the fixture has not been captured.

Traces: D-04, DET-01.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig
from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE

_SNAPSHOT_PATH = Path(__file__).parent / "fixtures" / "v01_snapshot.json"


def _has_pyright() -> bool:
    try:
        subprocess.run(
            ["pyright", "--version"],
            capture_output=True,
            timeout=30.0,
            check=False,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


pytestmark = pytest.mark.skipif(
    not _has_pyright() or not _SNAPSHOT_PATH.exists(),
    reason="pyright not installed or snapshot fixture missing",
)


def _execute() -> str:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, EXAMPLE_SOURCE.encode("utf-8"), EXAMPLE_PATH)
    return result.model_dump_json(indent=2)


def test_v01_fixture_snapshot_byte_identical() -> None:
    """D-04 byte-identical: executor output equals the captured snapshot."""
    actual = _execute()
    expected = _SNAPSHOT_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "v0.1.0 fixture snapshot drift detected.\n"
        "Run scripts/generate_v01_snapshot.py to update if intentional.\n"
        f"First 200 chars actual: {actual[:200]!r}\n"
        f"First 200 chars expected: {expected[:200]!r}"
    )


def test_v01_fixture_snapshot_deterministic_across_3_runs() -> None:
    """DET-01 prerequisite: executor output is byte-identical across re-runs."""
    outputs = [_execute() for _ in range(3)]
    assert outputs[0] == outputs[1] == outputs[2], (
        "Determinism broken: executor output varies across 3 consecutive runs."
    )
