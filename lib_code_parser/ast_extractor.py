"""AST-based function/class/method extractor for Python source code."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from lib_code_parser.models import FunctionNode, ParamInfo, SourceRange, TraceTag


def _get_module_name(path: str) -> str:
    """Convert file path to module name (stem only)."""
    return Path(path).stem


def _extract_annotation(node: ast.expr | None) -> str:
    """Unparse an annotation AST node to string."""
    if node is None:
        return ""
    return ast.unparse(node)


def _extract_trace_tags(docstring: str) -> list[TraceTag]:
    """Extract Traces: tags from a docstring."""
    tags: list[TraceTag] = []
    pattern = re.compile(r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)", re.MULTILINE)
    for m in pattern.finditer(docstring):
        refs = [r.strip() for r in m.group(1).split(",")]
        tags.append(TraceTag(tag="Traces", refs=refs))
    return tags


def _make_source_range(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> SourceRange:
    end = node.end_lineno if node.end_lineno is not None else node.lineno
    return SourceRange(start_line=node.lineno, end_line=end)


def _extract_params(
    args: ast.arguments, skip_self_cls: bool = True
) -> list[ParamInfo]:
    """Extract ParamInfo list from ast.arguments."""
    params: list[ParamInfo] = []
    for arg in args.args:
        if skip_self_cls and arg.arg in ("self", "cls"):
            continue
        params.append(
            ParamInfo(
                name=arg.arg,
                type_annotation=_extract_annotation(arg.annotation),
            )
        )
    return params


def extract_functions(source: str, path: str) -> list[FunctionNode]:
    """Parse Python source and extract FunctionNode list."""
    tree = ast.parse(source)
    module_name = _get_module_name(path)
    functions: list[FunctionNode] = []

    # Track which top-level items are in classes to avoid double-counting
    class_body_items: set[int] = set()  # ids of ast nodes inside classes

    # First pass: process classes and their methods
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_id = f"{module_name}.{node.name}"
            doc = ast.get_docstring(node) or ""
            trace_tags = _extract_trace_tags(doc)
            functions.append(
                FunctionNode(
                    node_id=class_id,
                    kind="class",
                    docstring=doc,
                    trace_tags=trace_tags,
                    source_range=_make_source_range(node),
                )
            )

            # Methods inside class
            for item in node.body:
                class_body_items.add(id(item))
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_id = f"{module_name}.{node.name}.{item.name}"
                    method_doc = ast.get_docstring(item) or ""
                    method_tags = _extract_trace_tags(method_doc)
                    functions.append(
                        FunctionNode(
                            node_id=method_id,
                            kind="method",
                            params=_extract_params(item.args, skip_self_cls=True),
                            return_type=_extract_annotation(item.returns),
                            docstring=method_doc,
                            trace_tags=method_tags,
                            source_range=_make_source_range(item),
                        )
                    )

    # Second pass: top-level functions (not inside classes)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_id = f"{module_name}.{node.name}"
            doc = ast.get_docstring(node) or ""
            tags = _extract_trace_tags(doc)
            functions.append(
                FunctionNode(
                    node_id=func_id,
                    kind="function",
                    params=_extract_params(node.args, skip_self_cls=False),
                    return_type=_extract_annotation(node.returns),
                    docstring=doc,
                    trace_tags=tags,
                    source_range=_make_source_range(node),
                )
            )

    return functions
