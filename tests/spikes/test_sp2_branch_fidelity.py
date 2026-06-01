"""SP-2 spike probe: is sequence-diagram branch fidelity a DETERMINISTIC rule?

D-08 ship-vs-defer is judged SOLELY by "is a deterministic rule constructible
as a pure function" (byte-identical, no LLM/heuristic). This module is the
probe that produces that evidence. It does NOT import the production extractor
(that is Task 2); it is a self-contained, throwaway-style proof that the
candidate mapping rule

    ast.If                       -> "alt"  frame
    ast.For / ast.While          -> "loop" frame
    ast.AsyncWith / await-expr   -> "par"  frame

can be applied as a pure structural AST walk that wraps the calls inside each
construct, producing a structured output that is byte-identical when the same
fixture is parsed and walked twice (and across PYTHONHASHSEED, since the walk
uses no set/dict iteration ordering for its output — only ordered lists).

If these probes pass, the verdict recorded in
.planning/spikes/SP-2-sequence-branch-fidelity.md is SHIP and Task 2 implements
the documented frame-marker scheme. If a probe had revealed non-determinism
(e.g. the rule needed to consult something outside (source) — a symbol table,
heuristic disambiguation, or order-dependent set iteration), the verdict would
be DEFER (DIA-02-FULL -> v0.3.0) and Task 2 would ship linear-only.

Traces: DIA-02, DET-04 (spike).
"""

from __future__ import annotations

import ast

# Candidate deterministic mapping rule under test (pure, source-only).
# Mirrors the scheme Task 2 will implement in sequence_diagram.py if SHIP.
_FRAME_FOR_NODE: list[tuple[type, str]] = [
    (ast.If, "alt"),
    (ast.For, "loop"),
    (ast.AsyncFor, "loop"),
    (ast.While, "loop"),
    (ast.AsyncWith, "par"),
]


def _call_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _frame_kind(node: ast.AST) -> str | None:
    """Pure rule: map a control-flow statement node to its frame kind, else None.

    `await` is handled at the expression level (see _probe_frames) because it is
    an ast.Await *expression*, not a statement; an awaited call is a `par`
    (concurrent) participant interaction in the candidate scheme.
    """
    for node_type, kind in _FRAME_FOR_NODE:
        if isinstance(node, node_type):
            return kind
    return None


def _child_stmt_bodies(stmt: ast.stmt) -> list[list[ast.stmt]]:
    """Return the nested statement bodies of a compound statement, in source order.

    Pure: reads only the node's own attributes; no set/dict iteration.
    """
    bodies: list[list[ast.stmt]] = []
    for attr in ("body", "orelse", "finalbody"):
        block = getattr(stmt, attr, None)
        if isinstance(block, list):
            bodies.append(block)
    # try/except handlers carry their own bodies.
    for handler in getattr(stmt, "handlers", []) or []:
        bodies.append(handler.body)
    return bodies


def _probe_frames(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[tuple[str, str]]:
    """Pure source-only recursive descent → ordered (frame_kind, callee) list.

    Deterministic by construction:
      • iteration is over each node's own ``body``/``orelse``/... lists in
        source order, never over a set/dict;
      • the frame kind for a call is decided solely by the *nearest enclosing*
        control-flow statement type ("deepest frame wins"), recomputed as the
        descent goes deeper;
      • an awaited call is always ``par`` regardless of enclosing frame;
      • the output is a plain ``list`` so equality is structural / byte-stable.
    """
    out: list[tuple[str, str]] = []

    def visit(stmts: list[ast.stmt], frame: str) -> None:
        for stmt in stmts:
            kind = _frame_kind(stmt)
            current = kind if kind is not None else frame
            # Calls on this statement's own expressions (e.g. the test of an
            # `if`, the iter of a `for`, a bare expr call) get `current`.
            for awaited, name in _own_expr_calls(stmt):
                out.append(("par", name) if awaited else (current, name))
            # Recurse into nested compound bodies with the updated frame.
            for body in _child_stmt_bodies(stmt):
                visit(body, current)

    visit(func.body, "")
    return out


def _own_expr_calls(stmt: ast.stmt) -> list[tuple[bool, str]]:
    """Ordered (is_awaited, callee) for calls in ``stmt``'s own expressions only.

    Excludes calls inside nested statement bodies (those recurse). Walks the
    statement's direct expression children (test/iter/value/...), never the
    nested ``body``/``orelse`` lists.
    """
    nested = {id(b) for bs in _child_stmt_bodies(stmt) for b in bs}
    out: list[tuple[bool, str]] = []

    def walk_expr(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt) and id(child) in nested:
                continue  # nested statement body — handled by recursion
            if isinstance(child, ast.Await) and isinstance(child.value, ast.Call):
                name = _call_name(child.value)
                if name is not None:
                    out.append((True, name))
                walk_expr(child.value)
            elif isinstance(child, ast.Call):
                name = _call_name(child)
                if name is not None:
                    out.append((False, name))
                walk_expr(child)
            else:
                walk_expr(child)

    walk_expr(stmt)
    return out


def _structured(source: str) -> str:
    """Parse + probe + serialize to a byte-comparable string (pure function)."""
    tree = ast.parse(source)
    frames: list[tuple[str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            frames.extend(_probe_frames(node))
    # Serialize deterministically: ordered list repr (no set/dict).
    return repr(frames)


# ---------------------------------------------------------------------------
# Deterministic probe fixtures: if/for/while/async wrapping calls.
# ---------------------------------------------------------------------------

_IF_FIXTURE = "def f(x):\n    if x:\n        do_a()\n    else:\n        do_b()\n"

_FOR_FIXTURE = "def g(xs):\n    for x in xs:\n        handle(x)\n"

_WHILE_FIXTURE = "def h():\n    while running():\n        tick()\n"

_ASYNC_FIXTURE = (
    "async def w():\n    async with lock():\n        await fetch()\n    await commit()\n"
)

_MIXED_FIXTURE = (
    "def m(items):\n"
    "    setup()\n"
    "    if items:\n"
    "        for it in items:\n"
    "            while busy():\n"
    "                process(it)\n"
)


class TestSp2DeterministicMapping:
    """The candidate alt/loop/par rule produces the expected frame kinds."""

    def test_if_maps_to_alt(self) -> None:
        out = _structured(_IF_FIXTURE)
        assert ("alt", "do_a") in eval(out)
        assert ("alt", "do_b") in eval(out)

    def test_for_maps_to_loop(self) -> None:
        assert ("loop", "handle") in eval(_structured(_FOR_FIXTURE))

    def test_while_maps_to_loop(self) -> None:
        assert ("loop", "tick") in eval(_structured(_WHILE_FIXTURE))

    def test_async_await_maps_to_par(self) -> None:
        frames = eval(_structured(_ASYNC_FIXTURE))
        # Awaited calls are `par` regardless of enclosing frame.
        assert ("par", "fetch") in frames
        assert ("par", "commit") in frames


class TestSp2ByteIdenticalDeterminism:
    """The SOLE ship criterion (D-08): byte-identical pure function output."""

    def test_repeated_extraction_byte_identical(self) -> None:
        for fixture in (_IF_FIXTURE, _FOR_FIXTURE, _WHILE_FIXTURE, _ASYNC_FIXTURE, _MIXED_FIXTURE):
            a = _structured(fixture)
            b = _structured(fixture)
            assert a == b, f"non-deterministic for fixture:\n{fixture}"

    def test_mixed_nesting_is_stable(self) -> None:
        # Nested if>for>while: the deepest frame wins for the innermost call,
        # and the result is byte-stable across two parses.
        a = _structured(_MIXED_FIXTURE)
        b = _structured(_MIXED_FIXTURE)
        assert a == b
        # `process` is inside the while loop → loop frame is reachable.
        assert ("loop", "process") in eval(a)

    def test_no_set_or_dict_in_output_path(self) -> None:
        # The output is an ordered list of tuples (structural, hashseed-stable).
        out = eval(_structured(_MIXED_FIXTURE))
        assert isinstance(out, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in out)
