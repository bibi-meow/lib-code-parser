"""CodeParserExecutor: orchestrates AST extraction into NormalizedArtifact."""

from __future__ import annotations

from lib_code_parser.ast_extractor import extract_functions
from lib_code_parser.callgraph_builder import build_callgraph
from lib_code_parser.contract_extractor import extract_contracts
from lib_code_parser.models import (
    ArtifactId,
    CodeContent,
    NormalizedArtifact,
    ParserConfig,
)
from lib_code_parser.type_dep_builder import build_type_deps

_CPP_EXTENSIONS = frozenset({".cpp", ".c", ".h", ".cc"})


class CodeParserExecutor:
    """Execute code parsing for a single source file."""

    def execute(
        self,
        config: ParserConfig,
        raw_content: bytes,
        path: str,
    ) -> NormalizedArtifact:
        """Parse *raw_content* (bytes) from *path* using *config*.

        Returns a NormalizedArtifact with CodeContent populated.
        If config.enabled is False, returns an empty CodeContent.
        If the language is C++ (or file extension indicates C++), returns empty CodeContent.
        """
        if not config.enabled:
            return NormalizedArtifact(
                artifact_id=ArtifactId(path=path),
                artifact_type="code",
                content=CodeContent(),
            )

        params = config.params
        language = str(params.get("language", "python"))

        # Detect language from file extension
        import pathlib

        suffix = pathlib.Path(path).suffix.lower()
        if suffix in _CPP_EXTENSIONS:
            language = "cpp"

        if language == "cpp":
            # C++ not yet supported — return empty content
            return NormalizedArtifact(
                artifact_id=ArtifactId(path=path),
                artifact_type="code",
                content=CodeContent(),
            )

        source = raw_content.decode("utf-8", errors="replace")
        extract_contracts_flag = bool(params.get("extract_contracts", True))

        # Extract functions/classes/methods
        functions = extract_functions(source, path)

        # Build call graph
        call_graph = build_callgraph(source, path)

        # Build type dependencies
        type_deps = build_type_deps(source, path)

        # Apply contract info to matching FunctionNode entries
        if extract_contracts_flag:
            contracts_map = extract_contracts(source, path)
            for fn in functions:
                if fn.node_id in contracts_map:
                    fn.contracts = contracts_map[fn.node_id]

        return NormalizedArtifact(
            artifact_id=ArtifactId(path=path),
            artifact_type="code",
            content=CodeContent(
                functions=functions,
                call_graph=call_graph,
                type_deps=type_deps,
            ),
        )
