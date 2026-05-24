"""lib-code-parser — Parse Python source files to extract function graphs,
call graphs, type dependencies, and validator contracts.

Wave 1 transitional state (Plan 01-05): the legacy v0.1.0 top-level barrel
imports from ``lib_code_parser.models`` (the flat ``models.py`` file). When
Wave 1 parallel plans (01-03 infrastructure, 01-04 primitives, 01-05
evaluations) create the ``lib_code_parser/models/`` subpackage, Python's
import machinery shadows the legacy ``models.py`` with the new package
directory and the v0.1.0 14-name re-export breaks until Wave 2 Plan 01-09
rewrites this barrel.

The try/except below is a Wave 1 bridge so that the new subpackages
(``lib_code_parser.models.evaluations.*`` etc.) remain importable —
including from pytest test collection — while the legacy 14-name surface
is temporarily unavailable. Wave 2 Plan 01-09 will rewrite this file to
provide the full v0.1.0 + v0.2.0 public API and delete this transitional
guard. Do not rely on a top-level ``from lib_code_parser import
CodeParserExecutor`` during Wave 1 worktree-local validation.
"""

try:
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
except ImportError:
    # Wave 1 transitional: the legacy models.py is shadowed by the new
    # models/ subpackage until Wave 2 Plan 01-09 rewrites this barrel.
    # The new nested subpackages remain importable via their fully
    # qualified paths (e.g. lib_code_parser.models.evaluations.graph_base).
    pass

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
