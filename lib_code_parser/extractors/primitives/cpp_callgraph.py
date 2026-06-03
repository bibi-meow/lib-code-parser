r"""C++ libclang cursor -> CallGraph extractor (pure CAV consumer).

The C++ analog of ``extractors/primitives/callgraph.py`` (LNG-04 parity): walks
the CAV's ``clang.cindex.TranslationUnit`` payload and emits
``CallEdge(caller, callee)`` for every CALL_EXPR / MEMBER_REF_EXPR found inside a
main-file function or method body. The ``caller`` is the enclosing
function/method ``node_id`` (namespace-qualified, shared with cpp_functions); the
``callee`` is the call cursor's spelling (the called function / member name).

Nodes are the function/method/class node_ids in traversal order, deduped via
``dict.fromkeys`` (verbatim idiom from the Python sibling). DET-04: edges are
sorted by ``(caller, callee)`` on exit, absorbing libclang's nondeterministic
cursor-traversal order.

Best-effort (D-05): template / macro / overload completeness is not guaranteed;
an unresolved callee is still emitted by its spelling — never a fabricated edge.
Asserts a TranslationUnit payload and NEVER branches on ``cav.language``
(invariant #2).

Implements: LNG-04
Traces: LNG-04, DET-04, US-01, US-22, US-25
"""

from __future__ import annotations

import clang.cindex
from clang.cindex import Cursor, CursorKind

from lib_code_parser import _cpp_cursor
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.callgraph import CallEdge, CallGraph

__all__ = ["extract"]

_CLASS_KINDS = (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL)
_CALLABLE_KINDS = (CursorKind.CXX_METHOD, CursorKind.FUNCTION_DECL)
_CALL_KINDS = (CursorKind.CALL_EXPR, CursorKind.MEMBER_REF_EXPR)
# WR-04: callable boundaries that _collect_callees must NOT descend into, so a
# call inside a nested lambda / local function / local method is attributed to
# that nested callable (its own node) and not ALSO double-counted into the
# enclosing function — matching the Python sibling's flatten-to-enclosing rule
# (the Python sibling never double-emits a nested callable's calls).
_NESTED_CALLABLE_KINDS = (
    CursorKind.CXX_METHOD,
    CursorKind.FUNCTION_DECL,
    CursorKind.LAMBDA_EXPR,
)


def _has_body(cursor: Cursor) -> bool:
    return any(child.kind == CursorKind.COMPOUND_STMT for child in cursor.get_children())


def _collect_callees(cursor: Cursor) -> list[str]:
    """All call/member-ref names directly within a function/method body.

    Manual preorder walk that STOPS descending at nested callable boundaries
    (CXX_METHOD / FUNCTION_DECL / LAMBDA_EXPR) so calls inside a nested lambda
    or local function are not double-attributed to both this enclosing callable
    and the nested one (WR-04). The starting ``cursor`` is itself a callable, so
    its own children are always traversed; only DEEPER callables are pruned.
    """
    names: list[str] = []
    stack: list[Cursor] = list(cursor.get_children())
    while stack:
        node = stack.pop()
        if node.kind in _CALL_KINDS and node.spelling:
            names.append(node.spelling)
        if node.kind in _NESTED_CALLABLE_KINDS:
            # Do not descend into a nested callable's body — its calls belong to
            # that callable's own node, not this one.
            continue
        stack.extend(node.get_children())
    return names


def extract(cav: CAV, config: ParserConfig) -> CallGraph:
    """LNG-04 / DET-04: emit deterministic CallGraph from cav.payload (TranslationUnit).

    config is accepted for PrimitiveFn signature alignment but is not consumed,
    mirroring the Python sibling.
    """
    tu = cav.payload
    assert isinstance(tu, clang.cindex.TranslationUnit), (
        "cpp_callgraph extractor requires C++ CAV (TranslationUnit payload), "
        f"got {type(tu).__name__}"
    )
    path = cav.path
    nodes: list[str] = []
    edges: list[CallEdge] = []
    seen_callers: set[str] = set()

    for cursor in tu.cursor.walk_preorder():
        if not _cpp_cursor._in_main_file(cursor, path):
            continue
        kind = cursor.kind
        if kind in _CLASS_KINDS:
            nodes.append(_cpp_cursor.qualified_node_id(cursor))
            continue
        if kind in _CALLABLE_KINDS:
            node_id = _cpp_cursor.qualified_node_id(cursor)
            nodes.append(node_id)
            # Only the definition carries a body; the in-class declaration and
            # its out-of-line definition share node_id, so guard against
            # double-counting calls if both somehow have bodies.
            if _has_body(cursor) and node_id not in seen_callers:
                seen_callers.add(node_id)
                for callee in _collect_callees(cursor):
                    edges.append(CallEdge(caller=node_id, callee=callee))

    # DET-04: edge sort by (caller, callee) lex.
    edges.sort(key=lambda e: (e.caller, e.callee))
    return CallGraph(nodes=list(dict.fromkeys(nodes)), edges=edges)
