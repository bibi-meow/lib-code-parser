"""Artifact envelope models.

ArtifactId, NormalizedArtifact[TContent] (Generic per D-06), CodeContent aggregate.

Traces: ARC-02, SCH-02.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:  # pragma: no cover — forward-ref carriers
    # Imports referenced only by string annotations on CodeContent fields.
    # Plan 04 owns the primitives subpackage; using TYPE_CHECKING avoids a
    # hard import-time dependency on Plan 04 so Plan 03 can ship independently.
    from lib_code_parser.models.primitives.callgraph import CallGraph
    from lib_code_parser.models.primitives.contracts import ContractInfo
    from lib_code_parser.models.primitives.functions import FunctionNode
    from lib_code_parser.models.primitives.type_deps import TypeDep


TContent = TypeVar("TContent", bound=BaseModel)


def _lazy_callgraph_default() -> object:
    """Lazy-import CallGraph from primitives subpackage at first instantiation.

    Mirrors v0.1.0 ``CodeContent.call_graph = CallGraph()`` default semantics
    without forcing Plan 03 to load Plan 04 at module-import time. Falls back
    to the v0.1.0 legacy ``CallGraph`` re-exported via
    ``lib_code_parser.models`` until Plan 04 ships ``primitives/callgraph.py``.
    """
    try:
        mod = import_module("lib_code_parser.models.primitives.callgraph")
        callgraph_cls = mod.CallGraph
    except ImportError:
        # Plan 04 hasn't shipped yet — fall back to the v0.1.0 legacy
        # CallGraph living in ``lib_code_parser.models`` package __init__.py
        # (the transitional bridge installed by Plan 03 Task 2).
        legacy = import_module("lib_code_parser.models")
        callgraph_cls = legacy.CallGraph
    return callgraph_cls()


class ArtifactId(BaseModel):
    """Stable identifier for a parsed artifact (file path)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str


class CodeContent(BaseModel):
    """Aggregate of parsed code primitives produced by all extractors.

    Field types reference primitives from Plan 04 via string forward refs so
    Plan 03 can ship independently. ``call_graph``'s default uses a lazy
    importing factory; ``contracts`` is a new v0.2.0 field per D-04 / AST-04
    keyed by class node_id.
    """

    model_config = ConfigDict(extra="forbid")

    functions: list["FunctionNode"] = Field(default_factory=list)
    call_graph: "CallGraph" = Field(default_factory=_lazy_callgraph_default)
    type_deps: list["TypeDep"] = Field(default_factory=list)
    contracts: dict[str, "ContractInfo"] = Field(default_factory=dict)


class NormalizedArtifact(BaseModel, Generic[TContent]):
    """Generic envelope for parsed artifacts.

    The library exposes ``NormalizedArtifact[CodeContent]`` to typed callers;
    untyped callers can still write
    ``NormalizedArtifact(artifact_id=..., artifact_type=..., content=...)``
    and Pydantic accepts any BaseModel as ``content`` (validated by the
    TypeVar bound). RESEARCH live-tested with Pydantic 2.11.10: parameterized
    and unparameterized construction produce byte-identical JSON (D-06).
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    artifact_id: ArtifactId
    artifact_type: str
    content: TContent


# Resolve CodeContent's string forward refs. Plan 04 will land
# ``lib_code_parser.models.primitives.*``; until then we fall back to the
# v0.1.0 legacy classes re-exported via ``lib_code_parser.models`` (the
# transitional bridge installed by Plan 03 Task 2). After Plan 04 ships,
# the primitives modules win the import race and forward refs bind to the
# v0.2.0 typed primitives.
try:
    from lib_code_parser.models.primitives.callgraph import CallGraph  # noqa: F401
    from lib_code_parser.models.primitives.contracts import ContractInfo  # noqa: F401
    from lib_code_parser.models.primitives.functions import FunctionNode  # noqa: F401
    from lib_code_parser.models.primitives.type_deps import TypeDep  # noqa: F401
except ImportError:
    # Plan 04 not shipped yet — bind to v0.1.0 legacy bridge.
    from lib_code_parser.models import (  # noqa: F401
        CallGraph,
        ContractInfo,
        FunctionNode,
        TypeDep,
    )

CodeContent.model_rebuild()
