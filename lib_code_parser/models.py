"""Data models for lib-code-parser."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParamInfo:
    name: str
    type_annotation: str | None = None


@dataclass
class SourceRange:
    start_line: int
    end_line: int


@dataclass
class TraceTag:
    tag_type: str  # "Traces"
    source_id: str
    target_id: str = ""


@dataclass
class ContractInfo:
    preconditions: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)


@dataclass
class FunctionNode:
    node_id: str  # "module.ClassName.method_name"
    kind: str  # "function" | "method" | "class"
    params: list[ParamInfo] = field(default_factory=list)
    return_type: str | None = None
    contracts: ContractInfo = field(default_factory=ContractInfo)
    docstring: str | None = None
    trace_tags: list[TraceTag] = field(default_factory=list)
    source_range: SourceRange | None = None


@dataclass
class CallGraph:
    nodes: list[str] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class TypeDep:
    source: str
    target: str
    dep_type: str = "typing"


@dataclass
class CodeContent:
    functions: list[FunctionNode] = field(default_factory=list)
    call_graph: CallGraph = field(default_factory=CallGraph)
    type_deps: list[TypeDep] = field(default_factory=list)


@dataclass
class ArtifactId:
    path: str
    version: str = "HEAD"


@dataclass
class NormalizedArtifact:
    artifact_id: ArtifactId
    artifact_type: str  # always "code"
    content: CodeContent


@dataclass
class ParserConfig:
    artifact_type: str = "code"
    executor_lib: str = "lib_code_parser.parser"
    params: dict = field(
        default_factory=lambda: {
            "callgraph_tool": "internal",
            "type_tool": "pyright",
            "extract_contracts": True,
            "language": "python",
        }
    )
    enabled: bool = True
