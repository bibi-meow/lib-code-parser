"""AST-05 parity gate — one ast.parse() per file is structurally enforced.

RESEARCH §5.2 defence-in-depth:
  - primary (static grep): no ``ast.parse(`` / ``from ast import parse`` may
    appear under ``lib_code_parser/extractors/`` — primitive extractors are
    CAV consumers, never parsers. The single parse site lives in
    ``lib_code_parser/frontends/python.py``.
  - backup (dynamic monkeypatch): instrumenting ``ast.parse`` shows exactly one
    call per ``build_cav()`` invocation, proving the Frontend is the single
    parse site even before the Wave 2 executor is wired.
  - foundation (signature): the FrontendFn dispatch contract constrains the
    parse to a single callable boundary (asserted indirectly via build_cav).

Wave 1/2/3 plans that re-introduce ``ast.parse`` inside extractors will be
caught by ``test_no_ast_parse_in_extractors_directory``.

Traces: AST-05, ARC-02.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _grep_ast_parse(target: str) -> list[str]:
    # capture as bytes and decode UTF-8 explicitly: source files contain
    # non-ASCII (e.g. em-dash) and the default text-mode decode uses the
    # platform codec (cp932 on Windows), which raises on those bytes and
    # leaves result.stdout as None.
    result = subprocess.run(
        [
            "grep",
            "-rn",
            "-E",
            r"ast\.parse\(|from ast import parse",
            str(_REPO_ROOT / target),
            "--include=*.py",
        ],
        check=False,
        capture_output=True,
    )
    stdout = result.stdout.decode("utf-8", errors="replace")
    return [line for line in stdout.splitlines() if line.strip()]


def test_no_ast_parse_in_extractors_directory() -> None:
    """Primary static gate: extractors/ must never call ast.parse()."""
    matches = _grep_ast_parse("lib_code_parser/extractors/")
    assert matches == [], (
        "AST-05 violation: ast.parse found in lib_code_parser/extractors/. "
        "Extractors are CAV consumers and must read cav.payload, never parse:\n"
        + "\n".join(matches)
    )


def test_frontends_python_is_only_ast_parse_site() -> None:
    """The single ast.parse() call site lives in frontends/python.py."""
    matches = _grep_ast_parse("lib_code_parser/frontends/")
    # The real call site is the assignment ``module = ast.parse(...)``; the
    # other grep hits are docstring prose referencing ast.parse(). Exactly one
    # real call site must exist, and it must be in python.py.
    real_calls = [m for m in matches if "module = ast.parse(" in m]
    assert len(real_calls) == 1, (
        f"Expected exactly one ast.parse() call site in frontends/, got "
        f"{len(real_calls)}:\n" + "\n".join(matches)
    )
    assert "python.py" in real_calls[0], (
        f"The single parse site must be python.py, got: {real_calls[0]}"
    )


def test_no_ast_parse_in_adapters_directory() -> None:
    """Adapters call subprocesses; they must not parse Python AST."""
    matches = _grep_ast_parse("lib_code_parser/adapters/")
    assert matches == [], (
        "AST-05 violation: ast.parse found in lib_code_parser/adapters/. "
        "Adapters invoke subprocesses and must not parse:\n" + "\n".join(matches)
    )


def test_single_parse_per_build_cav(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dynamic backup gate: build_cav calls ast.parse exactly once."""
    from lib_code_parser.frontends.python import build_cav
    from lib_code_parser.models.infrastructure.config import ParserConfig

    real_parse = ast.parse
    call_count = 0

    def spy(*args: object, **kwargs: object) -> ast.Module:
        nonlocal call_count
        call_count += 1
        return real_parse(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(ast, "parse", spy)
    cav = build_cav(
        b"class Foo:\n    def bar(self): pass\n",
        "foo.py",
        ParserConfig(artifact_type="code", executor_lib="lib_code_parser"),
    )
    assert call_count == 1, (
        f"AST-05 violation: build_cav called ast.parse {call_count} times; "
        f"expected 1. The Frontend must be the SINGLE parse site."
    )
    assert isinstance(cav.payload, ast.Module)
