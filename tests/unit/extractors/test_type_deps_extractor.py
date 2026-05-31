"""Unit tests for the pure-CAV type_deps extractor (AST-03 / AST-05 / DET-03).

RESEARCH §2.3 hybrid algorithm: stdlib ast walk (v0.1.0 parity + source_line
tracking) + PyrightAdapter reportMissingImports oracle for the resolved flag.

PyrightAdapter is MOCKED here (no real pyright subprocess) so these units stay
fast and deterministic — the real adapter behavior is covered by Plan 02-05's
test_pyright_adapter.py. The mock is injected by monkeypatching the
PyrightAdapter symbol imported into the extractor module.

Traces: AST-03, AST-05, DET-03, DET-04, US-01, US-22.
"""

from __future__ import annotations

import ast

import pytest

from lib_code_parser.adapters.pyright import PyrightDiagnostic, PyrightOutput
from lib_code_parser.extractors.primitives.type_deps import extract
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

# Default config (resolve_imports=False) -> pure AST-only path, no pyright.
_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
# Opt-in config (resolve_imports=True) -> RESEARCH §2.3 pyright-hybrid path.
_CONFIG_RESOLVE = ParserConfig(
    artifact_type="code", executor_lib="lib_code_parser", resolve_imports=True
)


def _build_cav(source: str, path: str = "m.py") -> CAV:
    """Build a Python CAV from source (test-side parse only)."""
    raw = source.encode("utf-8")
    return CAV(
        language="python",
        path=path,
        payload=ast.parse(source),
        raw_content=raw,
    )


class _MockPyright:
    """Stand-in for PyrightAdapter that returns a fixed PyrightOutput."""

    def __init__(self, output: PyrightOutput | None = None, exc: Exception | None = None):
        self._output = output if output is not None else PyrightOutput(version="1.1.409")
        self._exc = exc

    def analyze(self, raw_content: bytes, path: str) -> PyrightOutput:
        if self._exc is not None:
            raise self._exc
        return self._output


def _patch_pyright(monkeypatch: pytest.MonkeyPatch, mock: _MockPyright) -> None:
    """Swap the PyrightAdapter constructor in the extractor module for the mock."""
    monkeypatch.setattr(
        "lib_code_parser.extractors.primitives.type_deps.PyrightAdapter",
        lambda **kw: mock,
    )


def test_extract_emits_import_typedep_with_source_line(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_pyright(monkeypatch, _MockPyright())
    cav = _build_cav("import os\n")
    deps = extract(cav, _CONFIG)
    assert len(deps) == 1
    d = deps[0]
    assert d.source == "m"
    assert d.target == "os"
    assert d.kind == "imports"
    assert d.source_line == 1
    assert d.resolved is True


def test_extract_emits_importfrom_with_dotted_target(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_pyright(monkeypatch, _MockPyright())
    cav = _build_cav("from os.path import join\n")
    deps = extract(cav, _CONFIG)
    targets = {(d.target, d.kind, d.source_line) for d in deps}
    assert ("os.path.join", "imports", 1) in targets


def test_extract_annotation_uses_uppercase_attribute_heuristic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_pyright(monkeypatch, _MockPyright())
    source = "import models\n\n\ndef f() -> models.OrderModel:\n    ...\n"
    cav = _build_cav(source)
    targets = {d.target for d in extract(cav, _CONFIG)}
    assert "OrderModel" in targets


def test_extract_excludes_none_true_false_names(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_pyright(monkeypatch, _MockPyright())
    source = "def f(x: None) -> None:\n    ...\n"
    cav = _build_cav(source)
    deps = extract(cav, _CONFIG)
    assert all(d.target not in ("None", "True", "False") for d in deps)


def test_extract_marks_unresolved_when_pyright_diagnostic_fires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # diagnostic at pyright 0-based line 0 -> 1-based 1..1 covers source_line 1
    out = PyrightOutput(
        version="1.1.409",
        diagnostics=[
            PyrightDiagnostic(
                file="x",
                severity="error",
                message="missing",
                rule="reportMissingImports",
                start_line=0,
                end_line=0,
            )
        ],
    )
    _patch_pyright(monkeypatch, _MockPyright(output=out))
    cav = _build_cav("import nonexistent_pkg\n")
    deps = extract(cav, _CONFIG_RESOLVE)
    assert len(deps) == 1
    assert deps[0].resolved is False


def test_extract_keeps_resolved_when_diagnostic_is_different_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = PyrightOutput(
        version="1.1.409",
        diagnostics=[
            PyrightDiagnostic(
                file="x",
                severity="error",
                message="bad type arg",
                rule="reportMissingTypeArgument",
                start_line=0,
                end_line=0,
            )
        ],
    )
    _patch_pyright(monkeypatch, _MockPyright(output=out))
    cav = _build_cav("import os\n")
    deps = extract(cav, _CONFIG_RESOLVE)
    assert deps[0].resolved is True


def test_extract_emits_sorted_by_source_target_kind_source_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_pyright(monkeypatch, _MockPyright())
    source = "import zlib\nimport abc\nfrom os import path\n"
    cav = _build_cav(source)
    deps = extract(cav, _CONFIG)
    keys = [(d.source, d.target, d.kind, d.source_line) for d in deps]
    assert keys == sorted(keys)


def test_extract_pyright_runtime_error_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_pyright(monkeypatch, _MockPyright(exc=RuntimeError("pyright timed out")))
    cav = _build_cav("import os\n")
    with pytest.raises(RuntimeError, match="pyright timed out"):
        extract(cav, _CONFIG_RESOLVE)


def test_extract_isolated_import_no_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    # SC-4: extractor is callable without CodeParserExecutor and must not import it.
    import sys

    _patch_pyright(monkeypatch, _MockPyright())
    cav = _build_cav("import os\n")
    deps = extract(cav, _CONFIG)
    assert isinstance(deps, list)

    mod = sys.modules["lib_code_parser.extractors.primitives.type_deps"]
    with open(mod.__file__ or "", encoding="utf-8") as fh:
        text = fh.read()
    assert "from lib_code_parser.executor" not in text
    assert "import lib_code_parser.executor" not in text


# --- CR-01 (Option B): resolve_imports gate — pure default path ---------------


def test_default_path_never_constructs_pyright(monkeypatch: pytest.MonkeyPatch) -> None:
    """CR-01: default ParserConfig (resolve_imports=False) must NOT construct
    PyrightAdapter at all — the execute() path stays pure & subprocess-free.
    """
    constructed: list[bool] = []

    def _boom(**kw: object) -> object:
        constructed.append(True)
        raise AssertionError("PyrightAdapter must not be constructed on default path")

    monkeypatch.setattr(
        "lib_code_parser.extractors.primitives.type_deps.PyrightAdapter",
        _boom,
    )
    cav = _build_cav("import os\nimport nonexistent_xyz\n")
    deps = extract(cav, _CONFIG)
    assert constructed == []
    # All deps optimistically resolved=True on the deterministic default path.
    assert len(deps) == 2
    assert all(d.resolved is True for d in deps)


def test_default_path_never_raises_when_pyright_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CR-01: even if PyrightAdapter would raise (pyright absent), the default
    path must never reach it — no RuntimeError, deterministic output.
    """

    def _raise(**kw: object) -> object:
        raise RuntimeError("pyright executable not found")

    monkeypatch.setattr(
        "lib_code_parser.extractors.primitives.type_deps.PyrightAdapter",
        _raise,
    )
    cav = _build_cav("import os\n")
    deps = extract(cav, _CONFIG)  # must not raise
    assert len(deps) == 1
    assert deps[0].resolved is True


def test_default_path_still_sorted_and_deduped_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    """CR-01: default path keeps DET-04 sort identical to the opt-in path."""

    def _boom(**kw: object) -> object:
        raise AssertionError("PyrightAdapter must not be constructed on default path")

    monkeypatch.setattr(
        "lib_code_parser.extractors.primitives.type_deps.PyrightAdapter",
        _boom,
    )
    cav = _build_cav("import zlib\nimport abc\nfrom os import path\n")
    deps = extract(cav, _CONFIG)
    keys = [(d.source, d.target, d.kind, d.source_line) for d in deps]
    assert keys == sorted(keys)


def test_opt_in_path_constructs_pyright(monkeypatch: pytest.MonkeyPatch) -> None:
    """CR-01: resolve_imports=True keeps the pyright-hybrid path (adapter used)."""
    used: list[bool] = []

    class _Tracking(_MockPyright):
        def analyze(self, raw_content: bytes, path: str) -> PyrightOutput:
            used.append(True)
            return super().analyze(raw_content, path)

    monkeypatch.setattr(
        "lib_code_parser.extractors.primitives.type_deps.PyrightAdapter",
        lambda **kw: _Tracking(),
    )
    cav = _build_cav("import os\n")
    deps = extract(cav, _CONFIG_RESOLVE)
    assert used == [True]
    assert deps[0].resolved is True
