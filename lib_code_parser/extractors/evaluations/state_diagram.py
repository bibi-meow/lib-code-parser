"""DIA-05 / DIA-06 state diagram extractor (explicit FSM families + substitution).

Detects three explicit FSM families deterministically via import-provenance
(``_fsm_detect``) and emits a verifier-facing ``GraphModel``:

- ``GraphNode(node_type="state")`` per detected state.
- ``GraphEdge(edge_type="transitions_to")`` per transition; the trigger/event is
  carried on the edge ``label``.
- ``GuardExpr`` per transition that carries an event/condition.

D-07 must-haves shipped here regardless of the SP-1 verdict (see
``.planning/spikes/SP-1-general-control-flow-state.md``, verdict = DEFER):

- **DIA-05** — Family A ``transitions.Machine(...)``, Family B
  ``python-statemachine`` ``StateMachine`` subclass, Family C native ``Enum`` +
  literal ``self.state = EnumClass.MEMBER``. A bare ``Color(Enum)`` (no
  transition) yields ZERO state nodes (SC3 negative case).
- **DIA-06** — return-value substitution: a non-literal
  ``self.<attr> = self._next()`` resolves ``_next``'s returns intra-class,
  N-level recursive + cycle-safe; fully-resolved → concrete edges, unresolvable
  → exactly one placeholder edge with ``source_unresolved=True`` (Task 3).

D-10: target FSM libraries are detected by AST shape, NEVER imported.
T-03-08: import-provenance restriction → a user's own Machine/State without a
real import is not misdetected.

DET-04: nodes sorted by ``node_id``; edges sorted by
``(source, target, edge_type, label)``; guards sorted by
``(from_state, to_state, condition, action)`` on exit → byte-identical across
PYTHONHASHSEED. ``dict.fromkeys`` gives ordered dedup before sorting.

Implements: DIA-05, DIA-06, DIA-07
Traces: DIA-05, DIA-06, DIA-07, US-25, US-32
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations import _fsm_detect
from lib_code_parser.extractors.evaluations._substitution import resolve_substitution_edges
from lib_code_parser.models.evaluations.graph_base import (
    GraphEdge,
    GraphModel,
    GraphNode,
    GuardExpr,
)
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """DIA-05/06: emit a state GraphModel (states + transitions + guards) from cav.

    Runs the three import-provenance-gated FSM matchers (DIA-05) and the
    return-value-substitution pass (DIA-06), unioning their states/transitions
    into one DET-04-sorted GraphModel.
    """
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"state_diagram extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )

    machines: list[_fsm_detect.MachineModel] = []
    machines.extend(_fsm_detect.detect_transitions_machine(tree))
    machines.extend(_fsm_detect.detect_python_statemachine(tree))
    machines.extend(_fsm_detect.detect_native_enum(tree))

    state_ids: list[str] = []
    edges: list[GraphEdge] = []
    guards: list[GuardExpr] = []

    for machine in machines:
        state_ids.extend(machine.states)
        for trans in machine.transitions:
            # A transition's target is always a state node.
            state_ids.append(trans.target)
            if trans.source:
                state_ids.append(trans.source)
            edges.append(
                GraphEdge(
                    source=trans.source,
                    target=trans.target,
                    edge_type="transitions_to",
                    label=trans.event,
                    source_unresolved=trans.source_unresolved,
                )
            )
            if trans.event:
                guards.append(
                    GuardExpr(
                        from_state=trans.source,
                        to_state=trans.target,
                        condition=trans.event,
                    )
                )

    # DIA-06 (Task 3): non-literal self.<attr> = self._method() substitution.
    subst_states, subst_edges = resolve_substitution_edges(tree)
    state_ids.extend(subst_states)
    edges.extend(subst_edges)

    state_ids = list(dict.fromkeys(state_ids))
    nodes = [GraphNode(node_id=sid, node_type="state", label=sid) for sid in state_ids]

    # DET-04 sort-on-exit with stable composite keys.
    nodes.sort(key=lambda n: n.node_id)
    edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))
    guards.sort(key=lambda g: (g.from_state, g.to_state, g.condition, g.action))

    return GraphModel(nodes=nodes, edges=edges, guards=guards)
