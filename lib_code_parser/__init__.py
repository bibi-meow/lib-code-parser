"""lib-code-parser — Deterministic Python/C++ source parser.

v0.2.0 introduces the nested module layout (`models/{infrastructure,primitives,
evaluations}`, `frontends/`, `extractors/`, `adapters/`, `_paths`, `_dispatch`).
The flat v0.1.0 import surface is preserved via re-exports below — any v0.1.0
caller that wrote `from lib_code_parser import FunctionNode` continues to work
unchanged. v0.2.0 adds six new names (`CAV`, `EdgeKind`, `GraphNode`,
`GraphEdge`, `GraphModel`, `GuardExpr`) on the same barrel.

ParserConfig parity note (Phase 1):
    `lib_code_parser.ParserConfig` re-exports the v0.1.0 ParserConfig parity
    stub from `lib_code_parser.models` (`params: dict[str, object]` field, no
    `extra="forbid"`). The typed v0.2.0 ParserConfig (ARC-05) lives at
    `lib_code_parser.models.infrastructure.config.ParserConfig`. Phase 2's
    dispatch-driven executor rewrite (D-12) is the planned migration point
    where the typed variant graduates to the barrel.

Traces: ARC-01, ARC-04, DET-04, D-06.
"""

from lib_code_parser.executor import CodeParserExecutor
from lib_code_parser.models import (
    CAV,
    ArtifactId,
    CallEdge,
    CallGraph,
    CodeContent,
    ContractInfo,
    EdgeKind,
    FunctionNode,
    GraphEdge,
    GraphModel,
    GraphNode,
    GuardExpr,
    NormalizedArtifact,
    ParamInfo,
    ParserConfig,
    SourceRange,
    TraceTag,
    TypeDep,
)

__version__ = "0.2.0"

__all__ = [
    # v0.1.0 compat — ORDER PRESERVED
    "CodeParserExecutor",
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
    # v0.2.0 additions
    "CAV",
    "EdgeKind",
    "GraphEdge",
    "GraphModel",
    "GraphNode",
    "GuardExpr",
]
