"""Subpackages: infrastructure, primitives, evaluations.

Transitional v0.1.0 legacy symbol re-exports live here until Plan 09 wires the
final flat surface from primitives/evaluations subpackages. The legacy class
definitions below mirror ``lib_code_parser/models.py`` byte-for-byte (which is
shadowed by this package directory but kept in tree per Plan 03 boundary).

Plan 09 deletes ``lib_code_parser/models.py`` and replaces these inline defs
with re-exports from ``lib_code_parser.models.primitives`` and
``lib_code_parser.models.evaluations``.

Traces: ARC-02, ARC-05, SCH-02.
"""

from __future__ import annotations

from pydantic import BaseModel

# --- v0.1.0 legacy bridge -----------------------------------------------------
# These mirror the v0.1.0 class definitions previously in
# ``lib_code_parser/models.py``. Required because the new ``models/`` package
# directory shadows the legacy ``models.py`` module, breaking every
# ``from lib_code_parser.models import FunctionNode, ...`` import in the
# pre-Phase-1 source tree (executor.py, ast_extractor.py, callgraph_builder.py,
# contract_extractor.py, type_dep_builder.py, lib_code_parser/__init__.py,
# tests/). Plan 09 replaces this block with re-exports from the new primitives
# subpackage.


class ArtifactId(BaseModel):
    path: str


class TraceTag(BaseModel):
    tag: str
    refs: list[str] = []


class SourceRange(BaseModel):
    start_line: int
    end_line: int


class ParamInfo(BaseModel):
    name: str
    type_annotation: str = ""


class ContractInfo(BaseModel):
    preconditions: list[str] = []
    invariants: list[str] = []


class FunctionNode(BaseModel):
    node_id: str
    kind: str  # "function" | "method" | "class"
    params: list[ParamInfo] = []
    return_type: str = ""
    contracts: ContractInfo = ContractInfo()
    docstring: str = ""
    trace_tags: list[TraceTag] = []
    source_range: SourceRange = SourceRange(start_line=0, end_line=0)


class CallEdge(BaseModel):
    caller: str
    callee: str


class CallGraph(BaseModel):
    nodes: list[str] = []
    edges: list[CallEdge] = []


class TypeDep(BaseModel):
    source: str
    target: str
    kind: str = "uses"


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
    "TraceTag",
    "SourceRange",
    "ParamInfo",
    "ContractInfo",
    "FunctionNode",
    "CallEdge",
    "CallGraph",
    "TypeDep",
    "CodeContent",
    "NormalizedArtifact",
    "ParserConfig",
]
