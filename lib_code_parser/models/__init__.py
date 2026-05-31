"""Models package barrel — re-exports all 19 v0.1.0 + v0.2.0 names.

Plan 09 (Phase 1 closer) wires the final flat surface that combines Plan 03
(infrastructure), Plan 04 (primitives), and Plan 05 (evaluations) into a single
import barrel. Both `from lib_code_parser.models import X` and
`from lib_code_parser import X` are supported and resolve to identical objects.

ParserConfig graduation (Phase 2 Plan 02-07, D-01 / D-02):
    The barrel-level `lib_code_parser.models.ParserConfig` is now the TYPED
    v0.2.0 variant (`lib_code_parser.models.infrastructure.config.ParserConfig`,
    ARC-05 — `extra="forbid"` + explicit `language` / `extract_contracts` /
    `compile_args` / `python_version` fields). The v0.1.0 parity stub class
    (`params: dict[str, object]`, no `extra="forbid"`) that Phase 1 Plan 09
    retained here is DELETED. v0.1.0 dict-style callers
    (`ParserConfig(..., params={...})`) now raise `ValidationError` — this is the
    D-02 explicit break, sanctioned by PROJECT.md §Constraints (互換性破壊明示要件)
    via CONTEXT.md D-02.

Traces: ARC-02, ARC-05, SCH-02, D-01, D-02, D-06, D-08.
"""

from __future__ import annotations

# v0.2.0 evaluations layer (Plan 05) — verifier-facing graph schema.
from lib_code_parser.models.evaluations.graph_base import (
    EdgeKind,
    GraphEdge,
    GraphModel,
    GraphNode,
    GuardExpr,
)

# v0.2.0 infrastructure layer (Plan 03) — re-export CAV + the artifact envelope.
# ParserConfig is the TYPED v0.2.0 variant graduated to the barrel in Plan 02-07
# (D-01 / D-02); the v0.1.0 parity stub class is deleted.
from lib_code_parser.models.infrastructure.artifact import (
    ArtifactId,
    CodeContent,
    NormalizedArtifact,
)
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

# v0.2.0 primitives layer (Plan 04) — single source of truth for the 8 primitive
# Pydantic v2 models.
from lib_code_parser.models.primitives.callgraph import CallEdge, CallGraph
from lib_code_parser.models.primitives.contracts import ContractInfo
from lib_code_parser.models.primitives.functions import (
    FunctionNode,
    ParamInfo,
    SourceRange,
    TraceTag,
)
from lib_code_parser.models.primitives.type_deps import TypeDep

__all__ = [
    # Infrastructure (Plan 03) — barrel surface (5 names). ParserConfig is the
    # TYPED v0.2.0 variant graduated in Plan 02-07.
    "CAV",
    "ArtifactId",
    "NormalizedArtifact",
    "CodeContent",
    "ParserConfig",
    # Primitives (Plan 04) — 8 names.
    "FunctionNode",
    "ParamInfo",
    "SourceRange",
    "TraceTag",
    "CallEdge",
    "CallGraph",
    "TypeDep",
    "ContractInfo",
    # Evaluations (Plan 05) — 5 names.
    "EdgeKind",
    "GraphNode",
    "GraphEdge",
    "GraphModel",
    "GuardExpr",
]
