"""DIA-02 sequence diagram extractor (linear call flow + SP-2 branch frames).

Linear must-have (D-07): pull the Phase 2 ``callgraph`` primitive — the
authoritative source of ``(caller, callee)`` interactions — and map each
``CallEdge`` to a ``GraphEdge(edge_type="calls", source=caller, target=callee)``.
Every distinct caller and callee becomes a ``GraphNode(node_type="participant")``.

Branch fidelity (SP-2 verdict = SHIP — see
``.planning/spikes/SP-2-sequence-branch-fidelity.md``): each call's nearest
enclosing control-flow construct is encoded as a Mermaid-style *frame* on the
edge ``label`` field — NO schema change, NO new EdgeKind:

- ``ast.If``                          → ``"alt"``
- ``ast.For`` / ``ast.AsyncFor`` / ``ast.While`` → ``"loop"``
- ``ast.AsyncWith`` enclosing, or an awaited call (``await foo()``) → ``"par"``
- otherwise (top-level / linear)      → ``""`` (empty label)

The frame rule is a pure function of the source AST (the D-08 determinism
criterion proven by the SP-2 probe): the frame for a call is decided solely by
the Python AST node *type* of its nearest enclosing statement and by source
order, with deepest-enclosing-frame-wins. An awaited call is ``par`` regardless
of the enclosing frame. No symbol table, no heuristic, no set/dict iteration in
the output path → byte-identical across PYTHONHASHSEED.

The frame walk mirrors the callgraph primitive's caller-id scheme and
per-body ``ast.walk`` call-collection order exactly, so frames align with the
callgraph edges occurrence-for-occurrence (one frame consumed per callgraph
edge, in callgraph emission order).

DET-04: nodes sorted by ``node_id``; edges sorted by
``(source, target, edge_type, label)`` on exit → byte-identical across
PYTHONHASHSEED. ``dict.fromkeys`` gives ordered dedup before sorting.

Implements: DIA-02, DIA-07
Traces: DIA-02, DIA-07, US-25, US-32
"""

from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name
from lib_code_parser.extractors.primitives import callgraph
from lib_code_parser.models.evaluations.graph_base import GraphEdge, GraphModel, GraphNode
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]

# Statement node type → frame kind (the SP-2 SHIP rule, pure source-only).
_FRAME_BY_STMT: list[tuple[type, str]] = [
    (ast.If, "alt"),
    (ast.For, "loop"),
    (ast.AsyncFor, "loop"),
    (ast.While, "loop"),
    (ast.AsyncWith, "par"),
]


def _frame_for_stmt(node: ast.AST) -> str | None:
    """Frame kind for a statement node by its AST type, else None (no frame)."""
    for node_type, kind in _FRAME_BY_STMT:
        if isinstance(node, node_type):
            return kind
    return None


def _call_name(func_node: ast.expr) -> str | None:
    """Callee name from a Call's func node (mirrors callgraph._get_call_name)."""
    if isinstance(func_node, ast.Name):
        return func_node.id
    if isinstance(func_node, ast.Attribute):
        return func_node.attr
    return None


def _frames_for_body(body_nodes: list[ast.stmt]) -> list[tuple[str, str]]:
    """Ordered ``(callee, frame)`` for every call in ``body_nodes``.

    Emission order MUST match the callgraph primitive's ``_collect_calls``:
    that helper does ``for stmt in body: for call in ast.walk(stmt)`` and
    appends each callee name in ``ast.walk`` pre-order. We reproduce that exact
    traversal, additionally tracking the nearest enclosing frame so each call's
    frame aligns 1:1 with the callgraph edge it produces.
    """
    out: list[tuple[str, str]] = []

    def walk(node: ast.AST, frame: str) -> None:
        # Recompute the frame if THIS node is a control-flow statement.
        stmt_frame = _frame_for_stmt(node)
        current = stmt_frame if stmt_frame is not None else frame
        # An awaited call is `par` regardless of the enclosing frame.
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            name = _call_name(node.value.func)
            if name is not None:
                out.append((name, "par"))
            # Descend into the awaited call's args (rare nested calls) WITHOUT
            # re-emitting the awaited call itself.
            for child in ast.iter_child_nodes(node.value):
                walk(child, current)
            return
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name is not None:
                out.append((name, current))
        for child in ast.iter_child_nodes(node):
            walk(child, current)

    for stmt in body_nodes:
        walk(stmt, "")
    return out


def _add_frames(
    queues: dict[tuple[str, str], list[str]], caller_id: str, body: list[ast.stmt]
) -> None:
    """Append each call's frame to the (caller, callee) queue, in source order."""
    for callee, frame in _frames_for_body(body):
        queues.setdefault((caller_id, callee), []).append(frame)


def _build_frame_queues(tree: ast.Module, module_name: str) -> dict[tuple[str, str], list[str]]:
    """Per-(caller, callee) FIFO queue of frame labels, in source order.

    Mirrors the callgraph primitive's two-pass caller-id construction
    (classes+methods first, then top-level functions) and its per-body
    ``ast.walk`` call order, so each frame lines up with the matching callgraph
    edge occurrence-for-occurrence.
    """
    queues: dict[tuple[str, str], list[str]] = {}

    # 1st pass: classes and their methods (callgraph parity emit order).
    for top_node in tree.body:
        if isinstance(top_node, ast.ClassDef):
            for item in top_node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_id = f"{module_name}.{top_node.name}.{item.name}"
                    _add_frames(queues, method_id, item.body)

    # 2nd pass: top-level functions.
    for top_node in tree.body:
        if isinstance(top_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_id = f"{module_name}.{top_node.name}"
            _add_frames(queues, func_id, top_node.body)

    return queues


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """DIA-02: emit a sequence GraphModel (participants + calls edges) from cav.

    The linear ``calls`` edges come from the authoritative ``callgraph``
    primitive (D-07 must-have). Branch frames (SP-2 SHIP) are attached to each
    edge's ``label`` via a parallel pure-AST frame walk that mirrors the
    callgraph emission order.
    """
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"sequence_diagram extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )
    module_name = get_module_name(cav.path)

    cg = callgraph.extract(cav, config)

    # Per-caller frame queue keyed by callee name. The frame walk reproduces the
    # callgraph primitive's exact per-body traversal order, so for any given
    # (caller, callee) the frame labels line up occurrence-for-occurrence with
    # the callgraph edges. We pop from a per-(caller, callee) queue so that when
    # a callee is called multiple times in different frames each call edge gets
    # its own frame, deterministically and in source order.
    frame_queues = _build_frame_queues(tree, module_name)

    edges: list[GraphEdge] = []
    node_ids: list[str] = list(cg.nodes)

    # Consume callgraph edges (authoritative `calls` interactions, D-07). The
    # callgraph already sorted edges by (caller, callee); within each
    # (caller, callee) group we consume frames in source order from the queue.
    for edge in cg.edges:
        queue = frame_queues.get((edge.caller, edge.callee))
        label = queue.pop(0) if queue else ""
        edges.append(
            GraphEdge(source=edge.caller, target=edge.callee, edge_type="calls", label=label)
        )
        node_ids.append(edge.caller)
        node_ids.append(edge.callee)

    node_ids = list(dict.fromkeys(node_ids))
    nodes = [GraphNode(node_id=nid, node_type="participant", label=nid) for nid in node_ids]

    # DET-04 sort-on-exit with stable composite keys.
    nodes.sort(key=lambda n: n.node_id)
    edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))

    return GraphModel(nodes=nodes, edges=edges)
