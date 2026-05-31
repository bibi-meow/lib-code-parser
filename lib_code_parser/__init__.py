"""lib-code-parser — Deterministic Python/C++ source parser.

v0.2.0 introduces the nested module layout (`models/{infrastructure,primitives,
evaluations}`, `frontends/`, `extractors/`, `adapters/`, `_paths`, `_dispatch`).
The flat v0.1.0 import surface is preserved via re-exports below — any v0.1.0
caller that wrote `from lib_code_parser import FunctionNode` continues to work
unchanged. v0.2.0 Phase 1 added six names (`CAV`, `EdgeKind`, `GraphNode`,
`GraphEdge`, `GraphModel`, `GuardExpr`); v0.2.0 Phase 2 adds three more
(`PyrightAdapter`, `PyrightOutput`, `PyrightDiagnostic`) on the same barrel.

Phase 2 graduation (Plan 02-07, D-01 / D-02):
    `lib_code_parser.ParserConfig` is now the TYPED v0.2.0 variant
    (`lib_code_parser.models.infrastructure.config.ParserConfig`, `extra="forbid"`
    + typed `language` / `extract_contracts` / `python_version` / `compile_args`).
    The v0.1.0 dict-style API `ParserConfig(..., params={...})` is explicitly
    broken (raises `ValidationError`) — D-02 explicit break.

Traces: ARC-01, ARC-04, DET-04, D-01, D-02, D-06.
"""

from lib_code_parser.adapters.pyright import (
    PyrightAdapter,
    PyrightDiagnostic,
    PyrightOutput,
)
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
    # v0.2.0 Phase 1 additions
    "CAV",
    "EdgeKind",
    "GraphEdge",
    "GraphModel",
    "GraphNode",
    "GuardExpr",
    # v0.2.0 Phase 2 additions
    "PyrightAdapter",
    "PyrightOutput",
    "PyrightDiagnostic",
]
