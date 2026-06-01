"""Unit tests for the DIA-05 state_diagram extractor (3 FSM families + negative).

Detection is gated by import-provenance (contracts.py pattern): a user's own
Machine/State with NO import of transitions/statemachine is NOT detected
(false-positive defense, mirrors test_contracts_extractor.py:180-222 shapes).
The bare `Color(Enum)` is the SC3 fixture-asserted negative case (0 state nodes).

Traces: DIA-05, DIA-07, DET-04.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations.state_diagram import extract
from lib_code_parser.models.evaluations.graph_base import GraphModel
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from tests.unit.extractors.fixtures.fsm_samples import (
    DECOY_MACHINE_NO_IMPORT,
    DECOY_STATEMACHINE_NO_IMPORT,
    FAMILY_A_DICTS,
    FAMILY_A_LISTS,
    FAMILY_B_BASIC,
    FAMILY_B_COMBINE,
    FAMILY_C_LITERAL,
    NEGATIVE_BARE_ENUM,
)

_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _extract(source: str, path: str = "pkg/fsm.py") -> GraphModel:
    return extract(CAV(language="python", path=path, payload=ast.parse(source)), _CONFIG)


def _state_nodes(model: GraphModel) -> list[str]:
    return [n.node_id for n in model.nodes if n.node_type == "state"]


def _transitions(model: GraphModel) -> set[tuple[str, str, str]]:
    return {
        (e.source, e.target, e.label) for e in model.edges if e.edge_type == "transitions_to"
    }


class TestFamilyATransitionsMachine:
    """Family A: transitions.Machine(...) kwargs (list-of-dicts + list-of-lists)."""

    def test_dict_form_states(self) -> None:
        model = _extract(FAMILY_A_DICTS)
        assert set(_state_nodes(model)) == {"idle", "ringing", "connected"}

    def test_dict_form_transitions(self) -> None:
        model = _extract(FAMILY_A_DICTS)
        trans = _transitions(model)
        assert ("idle", "ringing", "ring") in trans
        assert ("ringing", "connected", "answer") in trans

    def test_list_form_attribute_call(self) -> None:
        model = _extract(FAMILY_A_LISTS)
        assert set(_state_nodes(model)) == {"red", "green"}
        trans = _transitions(model)
        assert ("red", "green", "go") in trans
        assert ("green", "red", "stop") in trans


class TestFamilyBPythonStatemachine:
    """Family B: StateMachine subclass — State() attrs + src.to(dst) events."""

    def test_basic_states_and_transitions(self) -> None:
        model = _extract(FAMILY_B_BASIC)
        assert set(_state_nodes(model)) == {"pending", "confirmed", "shipped"}
        trans = _transitions(model)
        assert ("pending", "confirmed", "confirm") in trans
        assert ("confirmed", "shipped", "ship") in trans

    def test_combine_and_reverse_form(self) -> None:
        model = _extract(FAMILY_B_COMBINE)
        trans = _transitions(model)
        # `go = a.to(b) | a.to(c)` -> two edges under one event.
        assert ("a", "b", "go") in trans
        assert ("a", "c", "go") in trans
        # `back = b.from_(c)` -> reverse: source=c, target=b.
        assert ("c", "b", "back") in trans


class TestFamilyCNativeEnum:
    """Family C: Enum-typed state attr + literal self.state = Enum.MEMBER."""

    def test_literal_reassignment_transitions(self) -> None:
        model = _extract(FAMILY_C_LITERAL)
        states = set(_state_nodes(model))
        assert {"OPEN", "CLOSED"} <= states
        targets = {e.target for e in model.edges if e.edge_type == "transitions_to"}
        assert "OPEN" in targets
        assert "CLOSED" in targets


class TestNegativeBareEnum:
    """SC3: a bare Enum with no transition method -> ZERO state machines."""

    def test_color_enum_yields_zero_states(self) -> None:
        model = _extract(NEGATIVE_BARE_ENUM)
        assert len([n for n in model.nodes if n.node_type == "state"]) == 0
        assert [e for e in model.edges if e.edge_type == "transitions_to"] == []


class TestFalsePositiveDefense:
    """Import-provenance: user's own Machine/State without import -> NOT detected.

    Mirrors test_contracts_extractor.py:180-222 same-name false-positive shapes.
    """

    def test_decoy_machine_no_import_not_detected(self) -> None:
        model = _extract(DECOY_MACHINE_NO_IMPORT)
        assert len([n for n in model.nodes if n.node_type == "state"]) == 0
        assert model.edges == []

    def test_decoy_statemachine_no_import_not_detected(self) -> None:
        model = _extract(DECOY_STATEMACHINE_NO_IMPORT)
        assert len([n for n in model.nodes if n.node_type == "state"]) == 0
        assert model.edges == []


class TestDeterminism:
    """DET-04: sort-on-exit -> byte-identical output across repeated extraction."""

    def test_repeated_extraction_byte_identical_sort(self) -> None:
        for source in (FAMILY_A_DICTS, FAMILY_B_BASIC, FAMILY_C_LITERAL):
            a = _extract(source)
            b = _extract(source)
            assert a.model_dump_json() == b.model_dump_json()
            # Explicitly sorted on exit.
            node_ids = [n.node_id for n in a.nodes]
            assert node_ids == sorted(node_ids)
            edge_keys = [(e.source, e.target, e.edge_type, e.label) for e in a.edges]
            assert edge_keys == sorted(edge_keys)
