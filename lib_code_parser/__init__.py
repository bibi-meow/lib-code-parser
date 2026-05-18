"""lib-code-parser — Parse Python source files to extract function graphs,
call graphs, type dependencies, and validator contracts."""

from lib_code_parser.executor import CodeParserExecutor
from lib_code_parser.models import (
    ArtifactId,
    CallEdge,
    CallGraph,
    CodeContent,
    ContractInfo,
    FunctionNode,
    NormalizedArtifact,
    ParamInfo,
    ParserConfig,
    SourceRange,
    TraceTag,
    TypeDep,
)

__version__ = "0.1.0"

__all__ = [
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
]
