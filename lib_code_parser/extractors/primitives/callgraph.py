"""Python internal call graph extractor (pure CAV consumer, no GPL deps, no subprocess).

Walks the CAV's ast.Module payload once and emits (caller, callee) edges.
Resolution rules are inherited verbatim from v0.1.0 callgraph_builder.py
(RESEARCH §4 for the full 7-fixture truth table):

- self.foo() in method → callee is bare ``foo`` (not Class.foo)
- chain a.b().c() → 2 edges (callee=c and callee=b), reflecting the AST walk
  visiting both Call nodes; future expansion deferred to Phase 3 if
  sequence-diagram rendering requires single-edge semantics
- nested function bodies → callees flattened to the enclosing top-level /
  method node; nested function itself is NOT a graph node
- deep attribute a.b.c.d() → 1 edge (callee=d, innermost Call only)
- emission order before sort = v0.1.0 (classes+methods 1st pass, top-level
  functions 2nd pass, AST appearance order within each pass)
- emission order after sort = lexicographic by (caller, callee) per DET-04

Implements: AST-02, AST-05, DET-04
Traces: AST-02, AST-05, DET-04, US-01, US-22, US-25
"""

from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.callgraph import CallEdge, CallGraph

__all__ = ["extract"]


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


def extract(cav: CAV, config: ParserConfig) -> CallGraph:
    """AST-02: emit deterministic CallGraph from cav.payload (ast.Module).

    Sort invariant (DET-04 / ROADMAP Phase 2 SC-2): edges are lexicographically
    sorted by (caller, callee) before emission. Nodes are kept in insertion
    order with duplicate elimination via dict.fromkeys (v0.1.0 parity).

    config is accepted for FrontendFn/PrimitiveFn signature alignment but is
    not consumed; call graph extraction does not depend on per-config flags.
    """
    tree = cav.payload  # type: ignore[assignment]
    assert isinstance(tree, ast.Module), (
        f"callgraph extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )
    module_name = get_module_name(cav.path)
    nodes: list[str] = []
    edges: list[CallEdge] = []

    # 1st pass: classes and their methods (v0.1.0 parity emit order)
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

    # 2nd pass: top-level functions
    for top_node in tree.body:
        if isinstance(top_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_id = f"{module_name}.{top_node.name}"
            nodes.append(func_id)
            for callee in _collect_calls(top_node.body):
                edges.append(CallEdge(caller=func_id, callee=callee))

    # DET-04 / ROADMAP Phase 2 SC-2: edge sort by (caller, callee) lex
    edges.sort(key=lambda e: (e.caller, e.callee))

    return CallGraph(nodes=list(dict.fromkeys(nodes)), edges=edges)
