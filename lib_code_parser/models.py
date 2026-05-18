"""Data models for lib-code-parser."""

from __future__ import annotations

from pydantic import BaseModel


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
