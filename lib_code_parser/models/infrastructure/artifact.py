"""Artifact envelope models — placeholder shell, implemented in Plan 03 Task 3.

Traces: ARC-02, SCH-02.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# Task 2 placeholder definitions — replaced wholesale by Task 3 with the real
# ``ArtifactId`` / ``NormalizedArtifact[TContent]`` Generic / ``CodeContent``
# implementations. Kept here only so that
# ``lib_code_parser/models/infrastructure/__init__.py`` can import these names
# at Task 2 commit time without breaking the package.


class ArtifactId(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    path: str


class CodeContent(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NormalizedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    artifact_id: ArtifactId
    artifact_type: str
    content: BaseModel
