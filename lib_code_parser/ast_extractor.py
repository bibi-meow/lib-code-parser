"""AST-based function/method/class node extractor."""

from __future__ import annotations

import ast

from lib_code_parser.models import ContractInfo, FunctionNode, ParamInfo, SourceRange


def _annotation_to_str(node: ast.expr | None) -> str | None:
    """Convert an AST annotation node to its string representation."""
    if node is None:
        return None
    return ast.unparse(node)


def _extract_params(args: ast.arguments) -> list[ParamInfo]:
    """Extract parameter list, skipping 'self' and 'cls'."""
    params: list[ParamInfo] = []
    all_args = args.posonlyargs + args.args + args.kwonlyargs
    for arg in all_args:
        if arg.arg in ("self", "cls"):
            continue
        params.append(
            ParamInfo(
                name=arg.arg,
                type_annotation=_annotation_to_str(arg.annotation),
            )
        )
    return params


def _get_docstring(node: ast.AST) -> str | None:
    """Extract the docstring from a function or class body."""
    body = getattr(node, "body", [])
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        val = body[0].value.value
        if isinstance(val, str):
            return val.strip()
    return None


def extract_functions(source: str, module_name: str) -> list[FunctionNode]:
    """Extract FunctionNode list from Python source.

    Args:
        source: Python source code string.
        module_name: Logical module name used as prefix for node_id.

    Returns:
        List of FunctionNode objects.

    Raises:
        SyntaxError: If source contains invalid Python syntax.
    """
    if not source.strip():
        return []

    tree = ast.parse(source)
    nodes: list[FunctionNode] = []

    def _visit_func(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        prefix: str,
        kind: str,
    ) -> FunctionNode:
        node_id = f"{prefix}.{node.name}"
        params = _extract_params(node.args)
        return_type = _annotation_to_str(node.returns)
        docstring = _get_docstring(node)
        source_range = SourceRange(start_line=node.lineno, end_line=node.end_lineno or node.lineno)
        return FunctionNode(
            node_id=node_id,
            kind=kind,
            params=params,
            return_type=return_type,
            contracts=ContractInfo(),
            docstring=docstring,
            source_range=source_range,
        )

    for item in ast.walk(tree):
        if isinstance(item, ast.ClassDef):
            class_node_id = f"{module_name}.{item.name}"
            class_docstring = _get_docstring(item)
            class_range = SourceRange(
                start_line=item.lineno, end_line=item.end_lineno or item.lineno
            )
            nodes.append(
                FunctionNode(
                    node_id=class_node_id,
                    kind="class",
                    docstring=class_docstring,
                    source_range=class_range,
                )
            )
            # Extract methods belonging to this class
            for child in ast.iter_child_nodes(item):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nodes.append(_visit_func(child, prefix=class_node_id, kind="method"))

    # Top-level functions (not inside classes)
    for item in ast.iter_child_nodes(tree):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes.append(_visit_func(item, prefix=module_name, kind="function"))

    return nodes
