"""CodeParserExecutor — dispatch-dict-driven orchestrator (Phase 2 D-03 rewrite).

Phase 2 Plan 02-06 replaces the v0.1.0 if/elif body with a walk over
_dispatch.FRONTENDS / PRIMITIVES. Adding a new primitive becomes a single
line in _dispatch.py (Open-Closed invariant #4 + #6) — executor body never
changes. Frontend selection is config.language -> FRONTENDS[language].
Contract merger (ContractInfo into FunctionNode.contracts) is the only
cross-primitive coordination logic; it mirrors v0.1.0 executor.py L72-76.

Traces: ARC-01, ARC-02, D-03, D-12.
"""

from __future__ import annotations

import pathlib

from lib_code_parser._dispatch import EVALUATIONS, FRONTENDS, PRIMITIVES
from lib_code_parser.models.infrastructure.artifact import (
    ArtifactId,
    CodeContent,
    NormalizedArtifact,
)
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.callgraph import CallGraph
from lib_code_parser.models.primitives.contracts import ContractInfo
from lib_code_parser.models.primitives.functions import FunctionNode
from lib_code_parser.models.primitives.type_deps import TypeDep

_CPP_EXTENSIONS = frozenset({".cpp", ".c", ".h", ".cc"})


class CodeParserExecutor:
    """Execute the dispatch-dict pipeline for a single source file."""

    def execute(
        self,
        config: ParserConfig,
        raw_content: bytes,
        path: str,
    ) -> NormalizedArtifact[CodeContent]:
        """Parse raw_content (bytes) from path using config.

        D-03 dispatch-driven flow:
            Frontend (FRONTENDS[language]) -> CAV
              |
            for each primitive in PRIMITIVES -> primitive(cav, config) -> CodeContent slot
              |
            ContractInfo merger -> FunctionNode.contracts
              |
            for each evaluation in EVALUATIONS -> eval(cav, config) -> setattr CodeContent slot
              |
            NormalizedArtifact[CodeContent]

        EVALUATIONS gating (invariant #6): run-all-registered. ParserConfig
        exposes no per-evaluation enable flag, so every registered evaluation
        runs unconditionally and its result is set into the same-named
        CodeContent slot. Adding a future evaluation needs ONLY a _dispatch.py
        registration — this executor body never changes. Phase 3 registers 7
        evaluations (5 diagrams + 2 specs); see _dispatch.py.

        Disabled / C++ extension early returns preserve v0.1.0 parity.
        """
        if not config.enabled:
            return NormalizedArtifact[CodeContent](
                artifact_id=ArtifactId(path=path),
                artifact_type="code",
                content=CodeContent(),
            )

        language = config.language
        suffix = pathlib.Path(path).suffix.lower()
        if suffix in _CPP_EXTENSIONS:
            language = "cpp"

        if language not in FRONTENDS:
            # Phase 4 will register "cpp"; until then, empty content (v0.1.0 parity)
            return NormalizedArtifact[CodeContent](
                artifact_id=ArtifactId(path=path),
                artifact_type="code",
                content=CodeContent(),
            )

        frontend = FRONTENDS[language]
        cav = frontend(raw_content, path, config)

        functions: list[FunctionNode] = []
        call_graph: CallGraph = CallGraph()
        type_deps: list[TypeDep] = []
        contracts_dict: dict[str, ContractInfo] = {}

        for name, primitive_fn in PRIMITIVES[cav.language].items():
            if name == "contracts" and not config.extract_contracts:
                continue
            result = primitive_fn(cav, config)
            if name == "functions":
                functions = result  # type: ignore[assignment]
            elif name == "call_graph":
                call_graph = result  # type: ignore[assignment]
            elif name == "type_deps":
                type_deps = result  # type: ignore[assignment]
            elif name == "contracts":
                contracts_dict = result  # type: ignore[assignment]

        # ContractInfo merger (v0.1.0 parity): assign per-class ContractInfo to
        # the matching FunctionNode.contracts where node_id aligns.
        for fn in functions:
            if fn.node_id in contracts_dict:
                fn.contracts = contracts_dict[fn.node_id]

        content = CodeContent(
            functions=functions,
            call_graph=call_graph,
            type_deps=type_deps,
            contracts=contracts_dict,
        )

        # EVALUATIONS walk (invariant #6, run-all-registered): each registered
        # evaluation produces its slot value, set by matching name. Phase 3
        # registered 7 evaluations (5 diagrams + 2 specs), append-only; the
        # name→slot correspondence is guarded at import time in _dispatch.py.
        for name, eval_fn in EVALUATIONS[cav.language].items():
            setattr(content, name, eval_fn(cav, config))

        return NormalizedArtifact[CodeContent](
            artifact_id=ArtifactId(path=path),
            artifact_type="code",
            content=content,
        )
