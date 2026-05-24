"""Primitive intermediate-data models.

Consumed by extractors, not directly verifier-facing per D-14. Re-exports the 8
primitive Pydantic v2 models (SCH-02 surface) shipped by Plan 04.

Traces: SCH-02, AST-04.
"""

from __future__ import annotations

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
    "FunctionNode",
    "ParamInfo",
    "SourceRange",
    "TraceTag",
    "CallEdge",
    "CallGraph",
    "TypeDep",
    "ContractInfo",
]
