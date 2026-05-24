"""Primitive type-dependency model — TypeDep.

Traces: SCH-02. Phase 2 fills via build_type_deps().

NOTE: TypeDep.kind is a free-form str at the primitives layer per D-14; the closed
EdgeKind Literal applies only to verifier-facing evaluations/.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TypeDep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    kind: str = "uses"
