"""Verifier-facing evaluation graph models.

EdgeKind closed Literal per SCH-03 / Pitfall 7. Schema structurally compatible
with lib-diagram-parser>=0.1.0; Phase 1 keeps models self-contained per
pre-resolved Open Question #5 (Phase 3 will re-evaluate direct-import vs
subclass switch per D-15/D-17).

Traces: SCH-01, SCH-02, SCH-03.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Closed taxonomy of inter-node edge kinds for verifier-facing graph models.
# This is the SCH-03 enforcement point — Pitfall 7 forbids catch-all values
# like "uses" / "other" / "misc" / "depends". Each value below has a single
# semantic, sourced from RESEARCH.md §EdgeKind Closed Literal coverage table:
#
#   inherits        — type subtype (Python `class A(B)`, C++ `class A : public B`)
#   implements      — interface conformance (Python ABCMeta, C++ pure virtual)
#   composes        — ownership with shared lifetime (concrete field)
#   aggregates      — has-a without lifetime (Optional / list / reference)
#   associates      — undecidable fallback (NEVER a catch-all for unknown — explicit semantic)
#   field_of        — A is the declared type of a field on B
#   param_of        — A is the declared type of a parameter on a method of B
#   returns         — A is the declared return type of a method on B
#   instantiates    — A constructs B (`new B()` / `B()`)
#   calls           — A method calls B method (sequence + callgraph)
#   transitions_to  — FSM: state A → state B
EdgeKind = Literal[
    "inherits",
    "implements",
    "composes",
    "aggregates",
    "associates",
    "field_of",
    "param_of",
    "returns",
    "instantiates",
    "calls",
    "transitions_to",
]


class GraphNode(BaseModel):
    """Verifier-facing graph node (structurally compatible with lib-diagram-parser).

    `node_type` is intentionally kept as a plain `str` (not a Literal) so that
    Phase 3 DIA-04 can add `"package"` per D-15 / D-17 without local schema
    drift while the sibling-lib `node_type="package"` situation is re-evaluated.
    """

    model_config = ConfigDict(extra="forbid")

    node_id: str
    node_type: str
    label: str
    attributes: dict[str, str] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Verifier-facing graph edge with closed EdgeKind taxonomy.

    The strict closed Literal on the edge-type field is the SCH-03 enforcement
    point — ad-hoc values forbidden by Pitfall 7 raise ValidationError at
    construction time.

    physical_module is the SCH-02 physical-side extension: optional metadata
    that physical (code-side) extractors may attach. The verifier ignores any
    field prefixed with physical_ when diffing against logical (spec-side)
    GraphEdge instances. Default None keeps lib-diagram-parser parity.
    """

    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    edge_type: EdgeKind
    label: str = ""
    physical_module: str | None = None


class GuardExpr(BaseModel):
    """Verifier-facing state-machine guard expression (structurally compatible)."""

    model_config = ConfigDict(extra="forbid")

    from_state: str
    to_state: str
    condition: str
    action: str = ""


class GraphModel(BaseModel):
    """Verifier-facing graph model (nodes + edges + guards).

    Structurally compatible with lib_diagram_parser.GraphModel; all collections
    default to empty so the "disabled" / "C++ not yet supported" extractor
    paths can return an inert value without conditional construction.
    """

    model_config = ConfigDict(extra="forbid")

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    guards: list[GuardExpr] = Field(default_factory=list)
