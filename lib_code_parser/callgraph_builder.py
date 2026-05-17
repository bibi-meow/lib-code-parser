"""Static call graph builder using AST analysis."""

from __future__ import annotations

import ast

from lib_code_parser.models import CallGraph, FunctionNode


def build_callgraph(
    source: str,
    functions: list[FunctionNode],
    module_name: str,
) -> CallGraph:
    """Build a static call graph from Python source.

    Only edges between functions that exist in the provided function list are included.

    Args:
        source: Python source code.
        functions: List of FunctionNode already extracted from this source.
        module_name: Logical module name prefix.

    Returns:
        CallGraph with nodes and edges.
    """
    nodes = [fn.node_id for fn in functions]
    # Build a set of simple names → full node_ids for lookup
    # e.g. "bar" → "mymod.bar", "A.bar" → "mymod.A.bar"
    name_to_ids: dict[str, list[str]] = {}
    for nid in nodes:
        # Strip module prefix to get short name
        without_prefix = nid[len(module_name) + 1 :] if nid.startswith(module_name + ".") else nid
        short_name = without_prefix.split(".")[-1]
        name_to_ids.setdefault(short_name, []).append(nid)

    if not source.strip():
        return CallGraph(nodes=nodes, edges=[])

    tree = ast.parse(source)
    edges: list[tuple[str, str]] = []

    # Map function def nodes to their node_id for context
    func_def_to_id: dict[ast.AST, str] = {}

    def _register_func(node: ast.FunctionDef | ast.AsyncFunctionDef, prefix: str) -> str:
        node_id = f"{prefix}.{node.name}"
        func_def_to_id[node] = node_id
        return node_id

    # First pass: register all top-level functions and class methods
    for item in ast.iter_child_nodes(tree):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _register_func(item, module_name)
        elif isinstance(item, ast.ClassDef):
            class_id = f"{module_name}.{item.name}"
            for child in ast.iter_child_nodes(item):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _register_func(child, class_id)

    # Second pass: find call sites within each function/method
    for func_node, caller_id in func_def_to_id.items():
        for node in ast.walk(func_node):
            if not isinstance(node, ast.Call):
                continue
            callee_name: str | None = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr

            if callee_name is None:
                continue

            # Resolve callee_name to full node_ids
            for callee_id in name_to_ids.get(callee_name, []):
                if callee_id != caller_id:
                    edge = (caller_id, callee_id)
                    if edge not in edges:
                        edges.append(edge)

    return CallGraph(nodes=nodes, edges=edges)
