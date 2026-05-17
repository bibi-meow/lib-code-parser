"""lib-code-parser — spec-reviewer pip package."""

from lib_code_parser.models import (
    ArtifactId,
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
from lib_code_parser.parser import parse_code

__version__ = "0.1.0"
__all__ = [
    "parse_code",
    "ArtifactId",
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
