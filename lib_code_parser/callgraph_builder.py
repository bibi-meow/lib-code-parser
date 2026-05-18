"""Static call-graph builder from Python AST."""

from __future__ import annotations

import ast
from pathlib import Path

from lib_code_parser.models import CallEdge, CallGraph


def _get_module_name(path: str) -> str:
    return Path(path).stem


def _get_call_name(func_node: ast.expr) -> str | None:
    """Extract callee name from a Call's func node."""
    if isinstance(func_node, ast.Name):
        return func_node.id
    if isinstance(func_node, ast.Attribute):
        return func_node.attr
    return None


def _collect_calls(body_nodes: list[ast.stmt]) -> list[str]:
    """Walk body nodes and collect all direct call names."""
    names: list[str] = []
    for stmt in body_nodes:
        for call in ast.walk(stmt):
            if isinstance(call, ast.Call):
                name = _get_call_name(call.func)
                if name:
                    names.append(name)
    return names


def build_callgraph(source: str, path: str) -> CallGraph:
    """Build CallGraph from Python source using static AST analysis."""
    tree = ast.parse(source)
    module_name = _get_module_name(path)

    nodes: list[str] = []
    edges: list[CallEdge] = []

    # Classes and their methods
    for top_node in tree.body:
        if isinstance(top_node, ast.ClassDef):
            class_id = f"{module_name}.{top_node.name}"
            nodes.append(class_id)

            for item in top_node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_id = f"{module_name}.{top_node.name}.{item.name}"
                    nodes.append(method_id)

                    for callee in _collect_calls(item.body):
                        edges.append(CallEdge(caller=method_id, callee=callee))

    # Top-level functions
    for top_node in tree.body:
        if isinstance(top_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_id = f"{module_name}.{top_node.name}"
            nodes.append(func_id)

            for callee in _collect_calls(top_node.body):
                edges.append(CallEdge(caller=func_id, callee=callee))

    return CallGraph(nodes=list(dict.fromkeys(nodes)), edges=edges)
