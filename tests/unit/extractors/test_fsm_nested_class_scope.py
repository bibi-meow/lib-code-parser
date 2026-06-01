"""Regression tests for nested-class scope bugs in FSM detection (CR-02, CR-03).

Both ``_fsm_detect.detect_native_enum`` (Family C) and
``_substitution.resolve_substitution_edges`` (DIA-06) scanned the class body
with ``ast.walk(class_node)``, which descends into NESTED class definitions.
A ``self.state = ...`` inside an inner class therefore leaked transitions /
substitutions into the OUTER class's model, producing phantom FSMs and edges.
The fix restricts the scan to the class's DIRECT method bodies.

Traces: DIA-05, DIA-06.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations._fsm_detect import detect_native_enum
from lib_code_parser.extractors.evaluations._substitution import resolve_substitution_edges

# Outer class with a nested Inner class whose method does the state assignment.
NESTED_LITERAL = """
from enum import Enum


class State(Enum):
    A = 1
    B = 2


class Outer:
    def __init__(self) -> None:
        self.value = 1

    class Inner:
        def m(self) -> None:
            self.state = State.A
"""

# Outer has _compute; Inner calls self._compute() — must NOT resolve against Outer.
NESTED_SUBSTITUTION = """
from enum import Enum


class State(Enum):
    A = 1


class Outer:
    def _compute(self):
        return State.A

    class Inner:
        def m(self) -> None:
            self.state = self._compute()
"""


class TestCR03NativeEnumNestedScope:
    def test_nested_class_literal_assign_does_not_make_outer_an_fsm(self) -> None:
        # The only `self.state = State.A` lives in Outer.Inner.m, NOT in any
        # direct method of Outer. Outer must NOT be reported as an FSM.
        machines = detect_native_enum(ast.parse(NESTED_LITERAL))
        assert machines == []

    def test_direct_method_literal_assign_still_detected(self) -> None:
        # Sanity: a literal assign in a DIRECT method is still detected.
        src = (
            "from enum import Enum\n"
            "class State(Enum):\n    A = 1\n"
            "class M:\n    def go(self):\n        self.state = State.A\n"
        )
        machines = detect_native_enum(ast.parse(src))
        assert len(machines) == 1
        assert machines[0].states == ["A"]


class TestCR02SubstitutionNestedScope:
    def test_inner_self_call_does_not_resolve_against_outer_methods(self) -> None:
        # Inner.m's `self._compute()` must not resolve against Outer._compute.
        states, edges = resolve_substitution_edges(ast.parse(NESTED_SUBSTITUTION))
        assert states == []
        assert edges == []

    def test_direct_method_substitution_still_resolves(self) -> None:
        # Sanity: a substitution in a DIRECT method still resolves.
        src = (
            "from enum import Enum\n"
            "class State(Enum):\n    A = 1\n"
            "class M:\n"
            "    def _compute(self):\n        return State.A\n"
            "    def go(self):\n        self.state = self._compute()\n"
        )
        states, edges = resolve_substitution_edges(ast.parse(src))
        assert states == ["A"]
        assert [(e.target, e.source_unresolved) for e in edges] == [("A", False)]
