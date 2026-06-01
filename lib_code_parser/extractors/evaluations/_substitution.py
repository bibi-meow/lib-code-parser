"""DIA-06 return-value substitution (N-level, cycle-safe) — Task 3.

Task 2 wires this module in as a no-op so the explicit-FSM families (DIA-05)
ship first; Task 3 replaces the body with the full intra-class return-value
resolution algorithm. See state_diagram.py for the integration point.

Traces: DIA-06
"""

from __future__ import annotations

import ast

from lib_code_parser.models.evaluations.graph_base import GraphEdge

__all__ = ["resolve_substitution_edges"]


def resolve_substitution_edges(module: ast.Module) -> tuple[list[str], list[GraphEdge]]:
    """Return (extra_state_ids, extra_edges) from non-literal state mutations.

    Task 2 placeholder: returns empty. Task 3 implements the algorithm.
    """
    return [], []
