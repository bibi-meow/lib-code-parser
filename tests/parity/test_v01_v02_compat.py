"""Wave 0 parity gate for the v0.1.0 -> v0.2.0 nested-layout migration.

These tests lock the contract that closes ROADMAP §Phase 1:
- Success Criterion 1: callers can write `from lib_code_parser import X` for
  all 13 v0.1.0 names AND all 6 v0.2.0 additions (CAV, EdgeKind, GraphNode,
  GraphEdge, GraphModel, GuardExpr).
- Success Criterion 3 (hard gate): `_get_module_name` / `get_module_name` is
  defined exactly once in `lib_code_parser/` — in `_paths.py`. The 4 v0.1.0
  extractors are thin shims importing from `_paths`.
- D-06 parity: `NormalizedArtifact[CodeContent](...).model_dump_json()` is
  byte-identical to `NormalizedArtifact(...).model_dump_json()`.
- D-12 / ARC-05: the typed ParserConfig at
  `lib_code_parser.models.infrastructure.config.ParserConfig` rejects unknown
  fields (`extra="forbid"`). The barrel-level `lib_code_parser.ParserConfig`
  retains the v0.1.0 parity stub shape (`params: dict[str, object]`) for the
  Phase 1 transitional window; Phase 2's dispatch-driven executor rewrite
  graduates the typed variant to the barrel.
- SCH-03: `GraphEdge(edge_type="uses")` raises ValidationError (closed
  EdgeKind Literal).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# --- Surface tests -----------------------------------------------------------


def test_v01_caller_surface_intact() -> None:
    """All 13 v0.1.0 names importable from the top-level barrel."""
    from lib_code_parser import (
        ArtifactId,
        CallEdge,
        CallGraph,
        CodeContent,
        CodeParserExecutor,
        ContractInfo,
        FunctionNode,
        NormalizedArtifact,
        ParamInfo,
        ParserConfig,
        SourceRange,
        TraceTag,
        TypeDep,
    )

    for name, obj in {
        "CodeParserExecutor": CodeParserExecutor,
        "ArtifactId": ArtifactId,
        "CallEdge": CallEdge,
        "CallGraph": CallGraph,
        "CodeContent": CodeContent,
        "ContractInfo": ContractInfo,
        "FunctionNode": FunctionNode,
        "NormalizedArtifact": NormalizedArtifact,
        "ParamInfo": ParamInfo,
        "ParserConfig": ParserConfig,
        "SourceRange": SourceRange,
        "TraceTag": TraceTag,
        "TypeDep": TypeDep,
    }.items():
        assert obj is not None, f"v0.1.0 name '{name}' resolved to None"


def test_v02_new_surface_present() -> None:
    """All 6 v0.2.0 additions importable from the top-level barrel."""
    from lib_code_parser import (
        CAV,
        EdgeKind,
        GraphEdge,
        GraphModel,
        GraphNode,
        GuardExpr,
    )

    for name, obj in {
        "CAV": CAV,
        "EdgeKind": EdgeKind,
        "GraphEdge": GraphEdge,
        "GraphModel": GraphModel,
        "GraphNode": GraphNode,
        "GuardExpr": GuardExpr,
    }.items():
        assert obj is not None, f"v0.2.0 name '{name}' resolved to None"


def test_version_bumped() -> None:
    """lib_code_parser.__version__ is '0.2.0'."""
    import lib_code_parser

    assert lib_code_parser.__version__ == "0.2.0"


# --- ARC-04 / DET-04 hard gate (ROADMAP SC-3 finalizer) ----------------------


def test_no_duplicate_module_name_helper() -> None:
    """Exactly one definition of `_get_module_name` / `get_module_name` in
    `lib_code_parser/`, and it lives in `_paths.py`.

    This is the ROADMAP SC-3 hard gate. The 4 v0.1.0 extractors carry only
    a re-export shim (`from lib_code_parser._paths import get_module_name as
    _get_module_name`) — they have no local `def`.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    target = repo_root / "lib_code_parser"
    # Use grep to scan actual file tree (catches any drift introduced after
    # Plan 09's patches). We grep for `def _get_module_name` and
    # `def get_module_name` separately to surface duplicate symbols across
    # both the v0.1.0 private name and the canonical public name.
    result = subprocess.run(
        [
            "grep",
            "-rn",
            "-E",
            r"^def _get_module_name|^def get_module_name",
            str(target),
            "--include=*.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    matches = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(matches) == 1, (
        f"Expected exactly 1 definition of (_)get_module_name in lib_code_parser/, "
        f"got {len(matches)}:\n" + "\n".join(matches)
    )
    assert "_paths.py" in matches[0], (
        f"Expected the single definition to live in _paths.py, got: {matches[0]}"
    )


# --- D-06 byte-identical JSON parity -----------------------------------------


def test_normalized_artifact_unparameterized_works() -> None:
    """`NormalizedArtifact(...)` constructable without explicit type parameter."""
    from lib_code_parser import ArtifactId, CodeContent, NormalizedArtifact

    a = NormalizedArtifact(
        artifact_id=ArtifactId(path="x"),
        artifact_type="code",
        content=CodeContent(),
    )
    # Smoke-test JSON dump succeeds.
    payload = a.model_dump_json()
    assert isinstance(payload, str)
    assert '"artifact_type":"code"' in payload


def test_normalized_artifact_parameterized_works() -> None:
    """`NormalizedArtifact[CodeContent](...)` constructable with type parameter."""
    from lib_code_parser import ArtifactId, CodeContent, NormalizedArtifact

    a = NormalizedArtifact[CodeContent](
        artifact_id=ArtifactId(path="x"),
        artifact_type="code",
        content=CodeContent(),
    )
    payload = a.model_dump_json()
    assert isinstance(payload, str)
    assert '"artifact_type":"code"' in payload


def test_normalized_artifact_json_byte_identical() -> None:
    """D-06: unparameterized vs parameterized JSON serialization is byte-identical.

    This is the live-test of the RESEARCH-confirmed Pydantic v2 Generic parity
    promise. If this ever fails, NormalizedArtifact's contract has drifted.
    """
    from lib_code_parser import ArtifactId, CodeContent, NormalizedArtifact

    args = dict(
        artifact_id=ArtifactId(path="x"),
        artifact_type="code",
        content=CodeContent(),
    )
    a = NormalizedArtifact(**args).model_dump_json()
    b = NormalizedArtifact[CodeContent](**args).model_dump_json()
    assert a == b, f"D-06 byte-parity broken:\nunparam={a}\n  param={b}"


# --- Executor end-to-end ------------------------------------------------------


def test_executor_runs_on_example_source() -> None:
    """Executor still produces FunctionNode entries on a trivial example.

    Uses the v0.1.0-shape ParserConfig (which the barrel exposes for parity).
    """
    from lib_code_parser import CodeParserExecutor, ParserConfig

    exe = CodeParserExecutor()
    result = exe.execute(
        ParserConfig(artifact_type="code", executor_lib="lib_code_parser"),
        b"def foo(): pass\n",
        "foo.py",
    )
    ids = [f.node_id for f in result.content.functions]
    assert "foo.foo" in ids, f"Expected foo.foo in {ids}"


# --- ARC-05 typed ParserConfig contract --------------------------------------


def test_parser_config_unknown_field_raises() -> None:
    """ARC-05 hard gate: the typed ParserConfig rejects unknown fields.

    The typed v0.2.0 ParserConfig lives at
    `lib_code_parser.models.infrastructure.config.ParserConfig` per the
    Phase 1 layout (Plan 03). The barrel-level `lib_code_parser.ParserConfig`
    remains the v0.1.0 parity stub for the Phase 1 transitional window; the
    typed variant will graduate to the barrel in Phase 2 when the executor
    is rewritten as dispatch-driven (D-12). This test asserts the contract at
    the canonical typed location.
    """
    from lib_code_parser.models.infrastructure.config import ParserConfig

    with pytest.raises(ValidationError):
        ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            surprise=1,  # type: ignore[call-arg]  # intentional unknown field
        )


# --- SCH-03 EdgeKind closed Literal ------------------------------------------


def test_edge_kind_rejects_uses() -> None:
    """SCH-03 hard gate: `GraphEdge(edge_type="uses")` raises ValidationError.

    `EdgeKind` is a closed `Literal[...]` taxonomy. Catch-all values like
    `"uses"` / `"other"` / `"misc"` are forbidden by construction (Pitfall 7
    mitigation). This is redundant with Plan 05's unit test suite but is
    pinned here as part of the omnibus Phase 1 parity gate.
    """
    from lib_code_parser import GraphEdge

    with pytest.raises(ValidationError):
        GraphEdge(source="A", target="B", edge_type="uses")  # type: ignore[arg-type]


# --- Bonus determinism: sys reachability (defends against accidental scope shrink)


def test_lib_code_parser_module_is_a_package_not_a_module() -> None:
    """Defensive: `lib_code_parser.models` resolves to a package (directory),
    not a module (file). The v0.1.0 models.py is deleted by Plan 09 Task 1.
    """
    import lib_code_parser.models

    assert lib_code_parser.models.__file__ is not None
    p = Path(lib_code_parser.models.__file__)
    assert p.name == "__init__.py", (
        f"Expected lib_code_parser.models to be a package init, got {p.name}"
    )
    # Belt-and-suspenders: confirm sys path doesn't expose a stray models.py.
    parent = p.parent.parent
    assert not (parent / "models.py").exists(), (
        f"Legacy lib_code_parser/models.py file still exists at {parent / 'models.py'}"
    )


# Module-level marker so pytest collects this file even if the test discovery
# heuristic depends on it. (Belt-and-suspenders for testpaths=['tests'].)
__test__ = True


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-x", "-v"]))
