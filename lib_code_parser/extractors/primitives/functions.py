r"""Python AST → FunctionNode extractor (pure CAV consumer).

Walks the CAV's ast.Module payload once and emits FunctionNode entries for
each class, method, and top-level function with kind/params/return_type/
docstring/trace_tags/source_range populated.

The TRC-03 trace-tag regex is preserved verbatim from v0.1.0 ast_extractor.py
(`r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)"`) so the same
`Traces:` lines extracted in v0.1.0 are extracted in v0.2.0 byte-identically.

Implements: AST-01, AST-05
Traces: AST-01, AST-05, US-01, US-22
"""

from __future__ import annotations

import ast
import re

from lib_code_parser._paths import get_module_name
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.functions import (
    FunctionNode,
    ParamInfo,
    SourceRange,
    TraceTag,
)

__all__ = ["extract"]

_TRACE_TAGS_RE = re.compile(
    r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)", re.MULTILINE
)


def _extract_annotation(node: ast.expr | None) -> str:
    """Unparse an annotation AST node to string."""
    if node is None:
        return ""
    return ast.unparse(node)


def _extract_trace_tags(docstring: str) -> list[TraceTag]:
    """Extract Traces: tags from a docstring (TRC-03 verbatim regex)."""
    tags: list[TraceTag] = []
    for m in _TRACE_TAGS_RE.finditer(docstring):
        refs = [r.strip() for r in m.group(1).split(",")]
        tags.append(TraceTag(tag="Traces", refs=refs))
    return tags


def _make_source_range(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> SourceRange:
    end = node.end_lineno if node.end_lineno is not None else node.lineno
    return SourceRange(start_line=node.lineno, end_line=end)


def _extract_params(args: ast.arguments, skip_self_cls: bool = True) -> list[ParamInfo]:
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


def extract(cav: CAV, config: ParserConfig) -> list[FunctionNode]:
    """AST-01: emit FunctionNode list from cav.payload (ast.Module).

    config is accepted for FrontendFn / PrimitiveFn signature alignment but
    is not currently consumed (FunctionNode extraction does not depend on
    per-config flags). Phase 3+ may use config.python_version for
    language-version-aware annotation parsing.
    """
    tree = cav.payload  # ast.Module — declared opaque in CAV
    assert isinstance(tree, ast.Module), (
        f"functions extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )
    module_name = get_module_name(cav.path)
    functions: list[FunctionNode] = []

    # First pass: process classes and their methods (v0.1.0 parity emit order)
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
            for item in node.body:
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

    # Second pass: top-level functions (v0.1.0 parity)
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
