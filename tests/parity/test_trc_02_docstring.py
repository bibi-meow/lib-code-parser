"""TRC-02 / TRC-03 docstring grep gates (Wave 0, VALIDATION.md required).

Static grep over every extractor / frontend / pyright-adapter module:
- TRC-02: each module docstring declares `Implements: <REQ>-NN`.
- TRC-03: each module docstring carries a `Traces: <REQ>-NN` line (the same
  verbatim form the functions extractor scans for in user code).
- Scope guard: non-extractor files (_paths.py / _dispatch.py) must NOT declare
  `Implements: AST-NN` (prevents false-positive TRC-02 attribution drift).

Traces: TRC-02, TRC-03.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_EXPECTED_EXTRACTOR_FILES = [
    "lib_code_parser/extractors/primitives/functions.py",
    "lib_code_parser/extractors/primitives/callgraph.py",
    "lib_code_parser/extractors/primitives/type_deps.py",
    "lib_code_parser/extractors/primitives/contracts.py",
    "lib_code_parser/frontends/python.py",
    "lib_code_parser/adapters/pyright.py",
]


def _grep(pattern: str, target: str) -> list[str]:
    # Capture bytes + decode UTF-8 explicitly: source files contain non-ASCII
    # (em-dash etc.) which the platform codec (cp932 on Windows) would choke on.
    result = subprocess.run(
        ["grep", "-rn", "-E", pattern, str(_REPO_ROOT / target), "--include=*.py"],
        check=False,
        capture_output=True,
    )
    stdout = result.stdout.decode("utf-8", errors="replace")
    return [line for line in stdout.splitlines() if line.strip()]


def test_all_extractor_modules_declare_implements_req_id() -> None:
    """TRC-02: every extractor / frontend / pyright adapter declares Implements: REQ-ID."""
    for target in _EXPECTED_EXTRACTOR_FILES:
        # NOTE: GNU grep ERE does not support `\d`; use POSIX [0-9].
        matches = _grep(r"^Implements: (AST|DET|TRC|SCH|ARC)-[0-9]+", target)
        assert matches, f"TRC-02 violation: no `Implements: AST-NN` line in {target}"


def test_all_extractor_modules_have_traces_line() -> None:
    """TRC-03: every extractor / frontend / pyright adapter has a Traces: REQ-ID line."""
    for target in _EXPECTED_EXTRACTOR_FILES:
        matches = _grep(r"Traces:[[:space:]]*[A-Z]+-[0-9]+", target)
        assert matches, f"TRC-03 violation: no `Traces: ...` line in {target}"


def test_no_implements_in_non_extractor_files() -> None:
    """TRC-02 scope: Implements: AST-NN must NOT appear in non-extractor files."""
    for target in ["lib_code_parser/_paths.py", "lib_code_parser/_dispatch.py"]:
        matches = _grep(r"^Implements: AST-[0-9]+", target)
        assert not matches, (
            f"Unexpected `Implements: AST-NN` in non-extractor file {target}: {matches}"
        )
