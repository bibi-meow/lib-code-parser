"""FSM detection fixtures for the DIA-05 / DIA-06 state_diagram extractor.

RESEARCH §FSM Detection AST Patterns: three explicit-pattern families must be
detected deterministically via import-provenance, plus a fixture-asserted
negative case (`Color(Enum)` -> 0 FSM) and a false-positive-defense decoy (a
user's own `Machine`/`State` with NO import of transitions/statemachine ->
NOT detected).

These are *source strings* only; the library parses them via the CAV. Nothing
here imports transitions / python-statemachine (D-10 detection-only): the
import statements in the fixtures are TEXT the provenance map matches against,
not real imports — the target libs need not be installed.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Family A — transitions.Machine(...) library call. Both literal forms.
# ---------------------------------------------------------------------------
FAMILY_A_DICTS = (
    "from transitions import Machine\n"
    "class Phone:\n"
    "    def __init__(self):\n"
    "        self.machine = Machine(\n"
    "            states=['idle', 'ringing', 'connected'],\n"
    "            transitions=[\n"
    "                {'trigger': 'ring', 'source': 'idle', 'dest': 'ringing'},\n"
    "                {'trigger': 'answer', 'source': 'ringing', 'dest': 'connected'},\n"
    "            ],\n"
    "            initial='idle',\n"
    "        )\n"
)

# List-of-list transition form `[trigger, source, dest]` + attribute-form call.
FAMILY_A_LISTS = (
    "import transitions\n"
    "class Light:\n"
    "    def __init__(self):\n"
    "        self.m = transitions.Machine(\n"
    "            states=['red', 'green'],\n"
    "            transitions=[['go', 'red', 'green'], ['stop', 'green', 'red']],\n"
    "        )\n"
)

# ---------------------------------------------------------------------------
# Family B — python-statemachine StateMachine subclass.
# State() attrs + src.to(dst) (event = LHS name) + |-combine + from_ reverse.
# ---------------------------------------------------------------------------
FAMILY_B_BASIC = (
    "from statemachine import StateMachine, State\n"
    "class Order(StateMachine):\n"
    "    pending = State(initial=True)\n"
    "    confirmed = State()\n"
    "    shipped = State()\n"
    "    confirm = pending.to(confirmed)\n"
    "    ship = confirmed.to(shipped)\n"
)

# |-combine (one event, multiple edges) + from_ reverse form.
FAMILY_B_COMBINE = (
    "from statemachine import StateMachine, State\n"
    "class Flow(StateMachine):\n"
    "    a = State(initial=True)\n"
    "    b = State()\n"
    "    c = State()\n"
    "    go = a.to(b) | a.to(c)\n"
    "    back = b.from_(c)\n"
)

# ---------------------------------------------------------------------------
# Family C — native Enum-typed state attr + literal self.state = Enum.MEMBER.
# ---------------------------------------------------------------------------
FAMILY_C_LITERAL = (
    "from enum import Enum\n"
    "class State(Enum):\n"
    "    OPEN = 1\n"
    "    CLOSED = 2\n"
    "class Door:\n"
    "    def __init__(self):\n"
    "        self.state = State.CLOSED\n"
    "    def open(self):\n"
    "        self.state = State.OPEN\n"
    "    def close(self):\n"
    "        self.state = State.CLOSED\n"
)

# ---------------------------------------------------------------------------
# NEGATIVE case (SC3 fixture-asserted): bare Enum, NO transition method, NO
# self.state = reassignment -> ZERO state machines / ZERO state nodes.
# ---------------------------------------------------------------------------
NEGATIVE_BARE_ENUM = (
    "from enum import Enum\nclass Color(Enum):\n    RED = 1\n    GREEN = 2\n    BLUE = 3\n"
)

# ---------------------------------------------------------------------------
# FALSE-POSITIVE DEFENSE: user's own Machine / State with NO import of
# transitions / statemachine -> NOT detected (no provenance).
# ---------------------------------------------------------------------------
DECOY_MACHINE_NO_IMPORT = (
    "class Machine:\n"
    "    def __init__(self, states=None, transitions=None):\n"
    "        self.states = states\n"
    "class App:\n"
    "    def __init__(self):\n"
    "        self.machine = Machine(\n"
    "            states=['a', 'b'],\n"
    "            transitions=[{'trigger': 't', 'source': 'a', 'dest': 'b'}],\n"
    "        )\n"
)

DECOY_STATEMACHINE_NO_IMPORT = (
    "class State:\n"
    "    def __init__(self, initial=False):\n"
    "        self.initial = initial\n"
    "    def to(self, other):\n"
    "        return (self, other)\n"
    "class StateMachine:\n"
    "    pass\n"
    "class Order(StateMachine):\n"
    "    pending = State(initial=True)\n"
    "    confirmed = State()\n"
    "    confirm = pending.to(confirmed)\n"
)

# ---------------------------------------------------------------------------
# DIA-06 return-value-substitution fixtures (used by test_state_substitution).
# ---------------------------------------------------------------------------
# Resolved: self.state = self._next() where _next returns Enum literals (both).
SUBST_RESOLVED = (
    "from enum import Enum\n"
    "class S(Enum):\n"
    "    A = 1\n"
    "    B = 2\n"
    "class M:\n"
    "    def __init__(self):\n"
    "        self.state = S.A\n"
    "    def step(self):\n"
    "        self.state = self._next()\n"
    "    def _next(self):\n"
    "        if self.flag:\n"
    "            return S.A\n"
    "        return S.B\n"
)

# N-level: _next -> _other -> literal.
SUBST_NLEVEL = (
    "from enum import Enum\n"
    "class S(Enum):\n"
    "    A = 1\n"
    "    B = 2\n"
    "class M:\n"
    "    def __init__(self):\n"
    "        self.state = S.A\n"
    "    def step(self):\n"
    "        self.state = self._next()\n"
    "    def _next(self):\n"
    "        return self._other()\n"
    "    def _other(self):\n"
    "        return S.B\n"
)

# Cyclic: _a -> _b -> _a (cycle-safe, no infinite loop).
SUBST_CYCLIC = (
    "from enum import Enum\n"
    "class S(Enum):\n"
    "    A = 1\n"
    "    B = 2\n"
    "class M:\n"
    "    def __init__(self):\n"
    "        self.state = S.A\n"
    "    def step(self):\n"
    "        self.state = self._a()\n"
    "    def _a(self):\n"
    "        return self._b()\n"
    "    def _b(self):\n"
    "        return self._a()\n"
)

# Unresolvable: external call (not intra-class) -> one placeholder edge.
SUBST_EXTERNAL = (
    "from enum import Enum\n"
    "import helper\n"
    "class S(Enum):\n"
    "    A = 1\n"
    "    B = 2\n"
    "class M:\n"
    "    def __init__(self):\n"
    "        self.state = S.A\n"
    "    def step(self):\n"
    "        self.state = helper.compute()\n"
)
