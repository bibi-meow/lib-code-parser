"""Primitive call graph models — CallEdge, CallGraph.

Traces: SCH-02. Phase 2 fills these via build_callgraph().
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CallEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caller: str
    callee: str


class CallGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[str] = Field(default_factory=list)
    edges: list[CallEdge] = Field(default_factory=list)
