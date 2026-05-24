"""Wave 0 tests for ArtifactId, NormalizedArtifact[TContent] Generic, CodeContent.

Traces: ARC-02, SCH-02, D-06.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lib_code_parser.models.infrastructure.artifact import (
    ArtifactId,
    CodeContent,
    NormalizedArtifact,
)


def test_artifact_id_basic() -> None:
    """ArtifactId(path=...) constructs and exposes .path."""
    aid = ArtifactId(path="src/foo.py")
    assert aid.path == "src/foo.py"


def test_artifact_id_rejects_extra_field() -> None:
    """ArtifactId is extra='forbid'; unknown kwargs must raise ValidationError."""
    with pytest.raises(ValidationError):
        ArtifactId(path="x", unknown=1)  # type: ignore[call-arg]


def test_artifact_id_frozen() -> None:
    """ArtifactId is frozen=True per RESEARCH §Pydantic v2 Generic ArtifactId pattern."""
    aid = ArtifactId(path="x")
    with pytest.raises(ValidationError):
        aid.path = "y"  # type: ignore[misc]


def test_code_content_default_empty() -> None:
    """CodeContent() succeeds with empty primitive collections.

    Note: call_graph default factory relies on Plan 04 primitives.callgraph.CallGraph;
    this test is marked skip-friendly until Plan 04 ships.
    """
    cc = CodeContent()
    assert cc.functions == []
    assert cc.type_deps == []
    assert hasattr(cc, "call_graph")


def test_normalized_artifact_constructible_unparameterized() -> None:
    """v0.1.0 caller surface: NormalizedArtifact(...) without Generic param works."""
    na = NormalizedArtifact(
        artifact_id=ArtifactId(path="x"),
        artifact_type="code",
        content=CodeContent(),
    )
    assert na.artifact_id.path == "x"
    assert na.artifact_type == "code"
    assert isinstance(na.content, CodeContent)


def test_normalized_artifact_constructible_parameterized() -> None:
    """v0.2.0 typed surface: NormalizedArtifact[CodeContent](...) works."""
    na = NormalizedArtifact[CodeContent](
        artifact_id=ArtifactId(path="x"),
        artifact_type="code",
        content=CodeContent(),
    )
    assert na.artifact_id.path == "x"
    assert na.artifact_type == "code"
    assert isinstance(na.content, CodeContent)


def test_normalized_artifact_json_parity() -> None:
    """D-06: parameterized and unparameterized NormalizedArtifact produce
    byte-identical JSON output (RESEARCH live-tested with Pydantic 2.11.10).
    """
    aid = ArtifactId(path="x")
    cc = CodeContent()
    na1 = NormalizedArtifact(artifact_id=aid, artifact_type="code", content=cc)
    na2 = NormalizedArtifact[CodeContent](artifact_id=aid, artifact_type="code", content=cc)
    assert na1.model_dump_json() == na2.model_dump_json()


def test_normalized_artifact_rejects_extra_field() -> None:
    """NormalizedArtifact is extra='forbid'; unknown kwargs raise ValidationError."""
    with pytest.raises(ValidationError):
        NormalizedArtifact(  # type: ignore[call-arg]
            artifact_id=ArtifactId(path="x"),
            artifact_type="code",
            content=CodeContent(),
            extra="x",
        )
