"""Models package barrel — re-exports all 19 v0.1.0 + v0.2.0 names.

Plan 09 (Phase 1 closer) wires the final flat surface that combines Plan 03
(infrastructure), Plan 04 (primitives), and Plan 05 (evaluations) into a single
import barrel. Both `from lib_code_parser.models import X` and
`from lib_code_parser import X` are supported and resolve to identical objects.

v0.1.0 ParserConfig parity stub:
    Phase 1 retains the v0.1.0 ParserConfig field-shape (`params: dict[str, object]`,
    no `extra="forbid"`) at this `lib_code_parser.models.ParserConfig` symbol because
    the v0.1.0 executor body (preserved in `lib_code_parser/executor.py` per Plan 09
    objective) reads `config.params.get(...)` and the v0.1.0 acceptance / unit tests
    pass `ParserConfig(..., params={...}, enabled=...)`. The TYPED ParserConfig
    introduced by Plan 03 (ARC-05 — `extra="forbid"` + explicit `language` /
    `extract_contracts` / `compile_args` / `python_version` fields) lives at
    `lib_code_parser.models.infrastructure.config.ParserConfig` and will become the
    barrel-level ParserConfig in Phase 2 when the executor is rewritten as
    dispatch-driven (per D-12). This dual-path is the documented v0.1.0 → v0.2.0
    migration bridge; the parity test
    `tests/parity/test_v01_v02_compat.py::test_parser_config_unknown_field_raises`
    asserts the typed contract at the infrastructure path while the legacy stub
    here preserves caller-side parity at the barrel path.

Traces: ARC-02, ARC-05, SCH-02, D-06, D-08.
"""

from __future__ import annotations

from pydantic import BaseModel

# v0.2.0 evaluations layer (Plan 05) — verifier-facing graph schema.
from lib_code_parser.models.evaluations.graph_base import (
    EdgeKind,
    GraphEdge,
    GraphModel,
    GraphNode,
    GuardExpr,
)

# v0.2.0 infrastructure layer (Plan 03) — re-export CAV + the artifact envelope.
# ParserConfig (typed, ARC-05) is intentionally NOT re-exported here; the legacy
# stub below preserves v0.1.0 caller parity. The typed ParserConfig remains
# importable via `lib_code_parser.models.infrastructure.config.ParserConfig`.
from lib_code_parser.models.infrastructure.artifact import (
    ArtifactId,
    CodeContent,
    NormalizedArtifact,
)
from lib_code_parser.models.infrastructure.cav import CAV

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


class ParserConfig(BaseModel):
    """v0.1.0 ParserConfig parity stub (see module docstring for rationale).

    Field shape and defaults are byte-identical to the v0.1.0 model in
    `lib_code_parser/models.py` (deleted by Plan 09). The typed v0.2.0 variant
    that satisfies ARC-05 lives at
    `lib_code_parser.models.infrastructure.config.ParserConfig`.
    """

    artifact_type: str
    executor_lib: str
    params: dict[str, object] = {}
    enabled: bool = True


__all__ = [
    # Infrastructure (Plan 03) — barrel surface (5 names, ParserConfig is the
    # v0.1.0 stub defined above).
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
