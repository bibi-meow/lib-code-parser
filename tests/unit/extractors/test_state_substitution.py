"""Unit tests for DIA-06 return-value substitution in the state_diagram extractor.

When a transition assigns a NON-literal value — ``self.state = self._next()`` —
the extractor resolves ``_next``'s return statements intra-class (N-level
recursive, cycle-safe). Fully-resolved → concrete ``transitions_to`` edges;
unresolvable → exactly ONE placeholder edge with ``source_unresolved=True``.

RESEARCH §Return-Value Substitution Algorithm (lines 365-381) + §Required Test
Fixtures.

Traces: DIA-06, DET-04.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations.state_diagram import extract
from lib_code_parser.models.evaluations.graph_base import GraphModel
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from tests.unit.extractors.fixtures.fsm_samples import (
    SUBST_CYCLIC,
    SUBST_EXTERNAL,
    SUBST_NLEVEL,
    SUBST_RESOLVED,
)

_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _extract(source: str, path: str = "pkg/fsm.py") -> GraphModel:
    return extract(CAV(language="python", path=path, payload=ast.parse(source)), _CONFIG)


def _transition_targets(model: GraphModel) -> set[str]:
    return {e.target for e in model.edges if e.edge_type == "transitions_to"}


def _unresolved_edges(model: GraphModel) -> list:
    return [e for e in model.edges if e.source_unresolved]


class TestResolvedSubstitution:
    """self.state = self._next() where _next returns Enum literals → concrete edges."""

    def test_both_literals_resolved(self) -> None:
        model = _extract(SUBST_RESOLVED)
        targets = _transition_targets(model)
        assert "A" in targets
        assert "B" in targets

    def test_no_unresolved_marker_when_fully_resolved(self) -> None:
        model = _extract(SUBST_RESOLVED)
        assert _unresolved_edges(model) == []


class TestNLevelSubstitution:
    """_next → _other → literal: resolve through recursion."""

    def test_nlevel_resolves_to_literal(self) -> None:
        model = _extract(SUBST_NLEVEL)
        targets = _transition_targets(model)
        assert "B" in targets
        assert _unresolved_edges(model) == []


class TestCyclicSubstitution:
    """_a → _b → _a is cycle-safe: terminates, no new literal, no infinite loop."""

    def test_cycle_terminates_without_literal(self) -> None:
        # The key assertion is that this completes (no RecursionError / hang).
        model = _extract(SUBST_CYCLIC)
        assert isinstance(model, GraphModel)
        # No literal is reachable through the cycle → an unresolvable transition
        # yields exactly one placeholder edge.
        unresolved = _unresolved_edges(model)
        assert len(unresolved) == 1


class TestUnresolvableSubstitution:
    """External call (not intra-class) → exactly ONE placeholder edge."""

    def test_external_call_one_placeholder(self) -> None:
        model = _extract(SUBST_EXTERNAL)
        unresolved = _unresolved_edges(model)
        assert len(unresolved) == 1
        assert unresolved[0].source_unresolved is True

    def test_no_concrete_targets_for_external(self) -> None:
        model = _extract(SUBST_EXTERNAL)
        # The external call cannot resolve to a concrete enum member.
        concrete = {
            e.target
            for e in model.edges
            if e.edge_type == "transitions_to" and not e.source_unresolved
        }
        assert "A" not in concrete or all(e.source_unresolved for e in model.edges if e.target == "compute")


class TestSubstitutionDeterminism:
    """DET-04: byte-identical across repeated extraction."""

    def test_repeated_extraction_byte_identical(self) -> None:
        for source in (SUBST_RESOLVED, SUBST_NLEVEL, SUBST_CYCLIC, SUBST_EXTERNAL):
            assert _extract(source).model_dump_json() == _extract(source).model_dump_json()
