"""Parent package marker for `lib_code_parser.models`.

Plan 04 transition state — re-exports the v0.1.0 primitive surface (FunctionNode,
ParamInfo, SourceRange, TraceTag, CallEdge, CallGraph, TypeDep, ContractInfo) from
`lib_code_parser.models.primitives`. The remaining v0.1.0 infra surface
(ArtifactId, CodeContent, NormalizedArtifact, ParserConfig) is provided here as
minimal transitional stubs so existing v0.1.0 extractors and the executor continue
to import via `from lib_code_parser.models import X` until Plan 03 (infrastructure
subpackage) and Plan 09 (final wiring) supersede this file.

Rationale: Plan 04 (this worktree) and Plan 03 (sibling Wave 1 worktree) both
create `lib_code_parser/models/__init__.py`. To keep this worktree's verification
self-contained (Task 1 acceptance: `from lib_code_parser.models.primitives.functions
import FunctionNode` succeeds — which transitively imports the `lib_code_parser`
top-level `__init__.py` which itself imports all 12 v0.1.0 names from
`lib_code_parser.models`), we provide the union surface here. The orchestrator's
Wave 1 merge step is responsible for combining the primitive re-exports (this file)
with Plan 03's infrastructure re-exports.

Traces: SCH-02 (Phase 1 substrate).
"""

from __future__ import annotations

# Infra surface — transitional stubs preserving v0.1.0 field surface. Plan 03
# (infrastructure subpackage) will supersede these with the hardened
# (frozen / extra="forbid" / Generic[TContent]) versions and Plan 09 finalizes
# the public re-exports.
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
