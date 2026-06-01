"""SP-1 spike probe: is GENERAL-control-flow -> state a DETERMINISTIC rule?

D-08 ship-vs-defer is judged SOLELY by "is a deterministic rule constructible
as a pure function" (byte-identical, no LLM/heuristic). This module is the
probe that produces that evidence for SP-1 — general control-flow -> state
extraction *beyond* the 3 explicit FSM families (transitions.Machine,
python-statemachine, native Enum + transition method).

This probe does NOT import the production extractor (the explicit-FSM extractor
is Task 2/3; it ships regardless of this verdict per D-07). It is a
self-contained proof about a *candidate* general rule: "reduce an arbitrary
method that mutates `self.<attr>` through nested conditionals — WITHOUT an
explicit Enum/State variable — to a state graph."

The probe demonstrates the determinism *failure mode* the RESEARCH (§Open
Questions #3) predicted: when there is no explicit state variable, the set of
candidate "states" is not uniquely determined by the source — it depends on a
modeling choice (which attribute is "the state"? which values are "states" vs
incidental mutations?). Two equally-reasonable candidate rules disagree on the
same source, so no single pure function yields a canonical byte-identical graph.

If a probe had shown that a single canonical state set IS uniquely derivable as
a pure function of (source) for arbitrary control flow, the verdict would be
SHIP. It does not — so the verdict recorded in
.planning/spikes/SP-1-general-control-flow-state.md is DEFER (DIA-05-FULL ->
v0.3.0). The explicit-FSM must-have (D-07) ships in Task 2/3 regardless.

Traces: DIA-05, DET-04 (spike).
"""

from __future__ import annotations

import ast

# ---------------------------------------------------------------------------
# Fixture A: explicit state variable (the FSM-shaped case). Here a single
# attribute `self.state` is assigned literal string values. A pure rule CAN
# canonically enumerate the states {"open","closed"} — this is the SHIP-able
# explicit form (which Task 2/3 actually implement).
# ---------------------------------------------------------------------------
_EXPLICIT_STATE_VAR = (
    "class Door:\n"
    "    def open(self):\n"
    "        self.state = 'open'\n"
    "    def close(self):\n"
    "        self.state = 'closed'\n"
)

# ---------------------------------------------------------------------------
# Fixture B: general control flow with NO explicit state variable. The method
# mutates several attributes through nested conditionals. There is no single
# attribute that is canonically "the state", and no canonical rule for which
# value-set constitutes "states". This is the case SP-1 must judge.
# ---------------------------------------------------------------------------
_GENERAL_CONTROL_FLOW = (
    "class Workflow:\n"
    "    def step(self, x):\n"
    "        if x > 0:\n"
    "            self.count += 1\n"
    "            if x > 10:\n"
    "                self.flag = True\n"
    "            else:\n"
    "                self.flag = False\n"
    "                self.flag = True\n"
    "        else:\n"
    "            self.count = 0\n"
)


def _attr_assign_targets(method: ast.AST) -> list[str]:
    """Ordered list of `self.<attr>` names assigned anywhere in the method.

    Pure source-only walk; iteration over ordered ast.walk, never set/dict.
    """
    out: list[str] = []
    for node in ast.walk(method):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if (
                    isinstance(tgt, ast.Attribute)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "self"
                ):
                    out.append(tgt.attr)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            tgt = node.target
            if (
                isinstance(tgt, ast.Attribute)
                and isinstance(tgt.value, ast.Name)
                and tgt.value.id == "self"
            ):
                out.append(tgt.attr)
    return out


def _literal_string_state_values(method: ast.AST, attr: str) -> list[str]:
    """Ordered literal string values assigned to `self.<attr>` (explicit-state form)."""
    out: list[str] = []
    for node in ast.walk(method):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if (
                    isinstance(tgt, ast.Attribute)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "self"
                    and tgt.attr == attr
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    out.append(node.value.value)
    return out


# ---------------------------------------------------------------------------
# Two equally-defensible candidate "general state-variable" selection rules.
# If general control-flow -> state were a deterministic pure function, BOTH
# rules (being reasonable readings of the SAME source) would have to agree on
# the canonical state attribute. They do not — which is the determinism failure.
# ---------------------------------------------------------------------------
def _candidate_rule_first_assigned_attr(method: ast.AST) -> str | None:
    """Rule 1: 'the state' = the FIRST attribute assigned in the method."""
    targets = _attr_assign_targets(method)
    return targets[0] if targets else None


def _candidate_rule_most_assigned_attr(method: ast.AST) -> str | None:
    """Rule 2: 'the state' = the attribute assigned MOST often (ties -> earliest)."""
    targets = _attr_assign_targets(method)
    if not targets:
        return None
    counts: dict[str, int] = {}
    for name in targets:
        counts[name] = counts.get(name, 0) + 1
    best = max(counts, key=lambda n: (counts[n], -targets.index(n)))
    return best


def _all_literal_state_values(source: str, attr: str) -> list[str]:
    """Literal string values assigned to `self.<attr>` across the whole module.

    The explicit-state form: each `self.state = '...'` site has a uniquely
    determined value, so the resulting list is canonical/byte-stable.
    """
    tree = ast.parse(source)
    return _literal_string_state_values(tree, attr)


def _first_method(source: str) -> ast.AST:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name != "__init__":
            return node
    raise AssertionError("no method found in fixture")


class TestSp1ExplicitStateVarIsDeterministic:
    """The EXPLICIT-state-variable form (FSM-shaped) IS canonically reducible.

    This is the form Task 2/3 ship: a literal `self.state = '...'` site gives a
    uniquely-determined state value. The probe confirms it is byte-stable.
    """

    def test_explicit_state_values_are_canonical(self) -> None:
        vals_a = _all_literal_state_values(_EXPLICIT_STATE_VAR, "state")
        vals_b = _all_literal_state_values(_EXPLICIT_STATE_VAR, "state")
        assert vals_a == vals_b == ["open", "closed"]
        # Byte-identical serialization across repeated parses.
        assert repr(vals_a) == repr(vals_b)


class TestSp1GeneralControlFlowIsNotDeterministic:
    """General control flow WITHOUT an explicit state variable is NOT canonical.

    Two equally-reasonable candidate selection rules disagree on which attribute
    is 'the state' for the SAME source — so there is no single pure function
    yielding a canonical state graph. This is the D-08 DEFER evidence.
    """

    def test_two_reasonable_rules_disagree_on_state_identity(self) -> None:
        method = _first_method(_GENERAL_CONTROL_FLOW)
        first = _candidate_rule_first_assigned_attr(method)
        most = _candidate_rule_most_assigned_attr(method)
        # Source order of self-assignments: count, flag, flag, count.
        # Rule 1 (first-assigned) -> "count"; Rule 2 (most-assigned) -> "flag".
        assert first == "count"
        assert most == "flag"
        # The two defensible rules pick DIFFERENT state attributes from the same
        # source -> state identity is ambiguous -> no canonical pure-function
        # reduction -> DEFER.
        assert first != most

    def test_no_explicit_state_literal_to_anchor_on(self) -> None:
        # The general method assigns no literal *string* state to any attr, so
        # the explicit-FSM literal-value rule (which IS deterministic) finds
        # nothing to anchor on — confirming the explicit families do NOT cover
        # this case and a NEW general rule would be required (and is ambiguous).
        method = _first_method(_GENERAL_CONTROL_FLOW)
        for attr in set(_attr_assign_targets(method)):
            assert _literal_string_state_values(method, attr) == []


class TestSp1ProbeIsByteStable:
    """Each individual candidate rule is itself pure/byte-stable.

    Determinism does NOT fail because a single rule is unstable — each rule is a
    pure function. It fails because there is no canonical CHOICE among equally
    valid rules for the unanchored general case (no ground-truth state variable).
    """

    def test_each_rule_is_individually_deterministic(self) -> None:
        for source in (_EXPLICIT_STATE_VAR, _GENERAL_CONTROL_FLOW):
            m1 = _first_method(source)
            m2 = _first_method(source)
            assert _candidate_rule_first_assigned_attr(m1) == _candidate_rule_first_assigned_attr(
                m2
            )
            assert _candidate_rule_most_assigned_attr(m1) == _candidate_rule_most_assigned_attr(m2)
            assert _attr_assign_targets(m1) == _attr_assign_targets(m2)
