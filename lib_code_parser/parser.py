"""Main parser: integrates all extractors into a NormalizedArtifact."""

from __future__ import annotations

import ast
import os

from lib_code_parser.ast_extractor import extract_functions
from lib_code_parser.callgraph_builder import build_callgraph
from lib_code_parser.contract_extractor import extract_contract_info
from lib_code_parser.models import (
    ArtifactId,
    CodeContent,
    FunctionNode,
    NormalizedArtifact,
    ParserConfig,
)
from lib_code_parser.trace_extractor import extract_trace_tags
from lib_code_parser.type_analyzer import analyze_type_deps


def _module_name_from_path(path: str) -> str:
    """Derive a logical module name from a file path.

    Examples:
        "mypackage/mymodule.py" → "mymodule"
        "mod.py" → "mod"
    """
    basename = os.path.basename(path)
    return os.path.splitext(basename)[0]


def _attach_trace_tags(
    functions: list[FunctionNode],
    source: str,
    module_name: str,
) -> None:
    """Attach TraceTag objects to FunctionNode instances.

    Tags that appear in the file are attached to the first function in the list,
    or remain at file level if no functions exist.
    """
    tags_by_line = extract_trace_tags(source)
    if not tags_by_line or not functions:
        # Attach all tags to the first function if any exist
        if functions:
            for tag_list in tags_by_line.values():
                functions[0].trace_tags.extend(tag_list)
        return

    # Map line numbers to functions by proximity (nearest function after the tag)

    all_tags_flat = [t for ts in tags_by_line.values() for t in ts]
    if all_tags_flat and functions:
        # Attach all found tags to the first available function (simple strategy)
        functions[0].trace_tags.extend(all_tags_flat)


def parse_code(
    raw_content: str,
    path: str,
    config: ParserConfig,
) -> NormalizedArtifact:
    """Parse Python source code into a NormalizedArtifact.

    Args:
        raw_content: Python source code string.
        path: File path (used for module name derivation and ArtifactId).
        config: Parser configuration controlling extraction behavior.

    Returns:
        NormalizedArtifact with populated CodeContent.

    Raises:
        ValueError: If raw_content contains a syntax error.
    """
    # Validate syntax first
    if raw_content.strip():
        try:
            ast.parse(raw_content)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {path}: {e}") from e

    module_name = _module_name_from_path(path)
    extract_contracts = config.params.get("extract_contracts", True)
    use_pyright = config.params.get("type_tool", "pyright") == "pyright"

    # Step 1: Extract function nodes
    functions = extract_functions(raw_content, module_name=module_name)

    # Step 2: Attach contract info to class-related functions
    if raw_content.strip():
        tree = ast.parse(raw_content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_id = f"{module_name}.{node.name}"
                contract = extract_contract_info(node, extract_contracts=extract_contracts)
                # Attach contract to the class FunctionNode
                for fn in functions:
                    if fn.node_id == class_id:
                        fn.contracts = contract
                        break

    # Step 3: Build call graph
    call_graph = build_callgraph(raw_content, functions, module_name=module_name)

    # Step 4: Analyze type deps
    type_deps = analyze_type_deps(
        raw_content, path=path, module_name=module_name, use_pyright=use_pyright
    )

    # Step 5: Attach trace tags to functions
    _attach_trace_tags(functions, raw_content, module_name=module_name)

    content = CodeContent(
        functions=functions,
        call_graph=call_graph,
        type_deps=type_deps,
    )

    return NormalizedArtifact(
        artifact_id=ArtifactId(path=path),
        artifact_type="code",
        content=content,
    )
