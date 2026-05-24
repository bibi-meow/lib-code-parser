"""Parent package marker for `lib_code_parser.models`.

Wave 1 transitional state — combines Plan 03 (infrastructure subpackage),
Plan 04 (primitives subpackage), and Plan 05 (evaluations subpackage). The
12 v0.1.0 names are preserved at this barrel for caller-side parity until
Plan 09 (Wave 2) wires the final flat surface (re-exports from infrastructure
+ primitives + evaluations and deletes the legacy `lib_code_parser/models.py`).

Primitive surface (FunctionNode, ParamInfo, SourceRange, TraceTag, CallEdge,
CallGraph, TypeDep, ContractInfo) re-exports from `models.primitives`.
The remaining infra surface (ArtifactId, CodeContent, NormalizedArtifact,
ParserConfig) is provided here as transitional v0.1.0-shape stubs so existing
v0.1.0 extractors and the executor continue to import via
`from lib_code_parser.models import X`. Plan 09 will replace these stubs with
re-exports from `models.infrastructure`.

Traces: ARC-02, ARC-05, SCH-02.
"""

from __future__ import annotations

from pydantic import BaseModel

# Primitive surface — single source of truth lives in models/primitives/
from lib_code_parser.models.primitives.callgraph import CallEdge, CallGraph
from lib_code_parser.models.primitives.contracts import ContractInfo
from lib_code_parser.models.primitives.functions import (
    FunctionNode,
    ParamInfo,
    SourceRange,
    TraceTag,
)
from lib_code_parser.models.primitives.type_deps import TypeDep


# Infra surface — transitional stubs preserving v0.1.0 field surface. Plan 03
# infrastructure/* provides hardened versions (frozen / extra="forbid" /
# Generic[TContent]); Plan 09 finalizes the public re-exports.
class ArtifactId(BaseModel):
    path: str


class CodeContent(BaseModel):
    functions: list[FunctionNode] = []
    call_graph: CallGraph = CallGraph()
    type_deps: list[TypeDep] = []


class NormalizedArtifact(BaseModel):
    artifact_id: ArtifactId
    artifact_type: str
    content: CodeContent


class ParserConfig(BaseModel):
    artifact_type: str
    executor_lib: str
    params: dict[str, object] = {}
    enabled: bool = True


__all__ = [
    "ArtifactId",
    "CallEdge",
    "CallGraph",
    "CodeContent",
    "ContractInfo",
    "FunctionNode",
    "NormalizedArtifact",
    "ParamInfo",
    "ParserConfig",
    "SourceRange",
    "TraceTag",
    "TypeDep",
]
