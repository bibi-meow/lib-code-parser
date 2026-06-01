"""Unit tests for the DIA-01 class_diagram extractor.

Exercises the composition/aggregation/association decision rule + inheritance,
plus the association fallback (never a catch-all 'uses' edge) and the
builtin-field skip. Determinism (DET-04) asserted via sort + byte-stability.

Traces: DIA-01, DIA-07, DET-04.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations.class_diagram import extract
from lib_code_parser.models.evaluations.graph_base import GraphModel
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from tests.unit.extractors.fixtures.dia_structural import (
    CLASS_HIERARCHY_PATH,
    CLASS_HIERARCHY_SOURCE,
    INIT_ATTRS_PATH,
    INIT_ATTRS_SOURCE,
)

_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _build_cav(source: str, path: str) -> CAV:
    """Build a Python CAV from source (test-side parse only)."""
    return CAV(
        language="python",
        path=path,
        payload=ast.parse(source),
        raw_content=source.encode("utf-8"),
    )


def _edges(source: str, path: str = "m.py") -> set[tuple[str, str, str]]:
    model = extract(_build_cav(source, path), _CONFIG)
    return {(e.source, e.target, e.edge_type) for e in model.edges}


class TestInheritance:
    def test_subclass_emits_inherits_edge(self) -> None:
        edges = _edges("class A:\n    pass\nclass B(A):\n    pass\n")
        assert ("B", "A", "inherits") in edges

    def test_object_base_not_emitted(self) -> None:
        edges = _edges("class A(object):\n    pass\n")
        assert all(e[1] != "object" for e in edges)


class TestRelationshipRule:
    def test_full_hierarchy_spectrum(self) -> None:
        edges = _edges(CLASS_HIERARCHY_SOURCE, CLASS_HIERARCHY_PATH)
        assert ("B", "A", "inherits") in edges
        assert ("B", "Engine", "composes") in edges  # x: Engine
        assert ("B", "Engine", "aggregates") in edges  # y: Optional / z: list
        # w: SomeForwardRefUnknown → associates (undecidable fallback)
        assert ("B", "SomeForwardRefUnknown", "associates") in edges

    def test_builtins_are_skipped(self) -> None:
        edges = _edges(CLASS_HIERARCHY_SOURCE, CLASS_HIERARCHY_PATH)
        # n: int and s: str must NOT produce any edge.
        targets = {e[1] for e in edges}
        assert "int" not in targets
        assert "str" not in targets

    def test_direct_known_class_composes(self) -> None:
        src = "class Engine:\n    pass\nclass Car:\n    motor: Engine\n"
        assert ("Car", "Engine", "composes") in _edges(src)

    def test_optional_known_class_aggregates(self) -> None:
        src = (
            "from typing import Optional\n"
            "class Engine:\n    pass\n"
            "class Car:\n    motor: Optional[Engine]\n"
        )
        assert ("Car", "Engine", "aggregates") in _edges(src)

    def test_list_known_class_aggregates(self) -> None:
        src = "class Wheel:\n    pass\nclass Car:\n    wheels: list[Wheel]\n"
        assert ("Car", "Wheel", "aggregates") in _edges(src)

    def test_union_none_aggregates(self) -> None:
        src = "class Wheel:\n    pass\nclass Car:\n    spare: Wheel | None\n"
        assert ("Car", "Wheel", "aggregates") in _edges(src)

    def test_unknown_name_associates_never_uses(self) -> None:
        src = "class Car:\n    gizmo: TotallyUnknown\n"
        edges = _edges(src)
        assert ("Car", "TotallyUnknown", "associates") in edges
        assert all(e[2] != "uses" for e in edges)

    def test_init_self_attribute_annotations(self) -> None:
        edges = _edges(INIT_ATTRS_SOURCE, INIT_ATTRS_PATH)
        assert ("Car", "Wheel", "composes") in edges  # self.wheel: Wheel
        assert ("Car", "Wheel", "aggregates") in edges  # self.spare: "Wheel | None"


class TestCR04ForwardRefSubscript:
    """CR-04: string forward-ref annotations must extract the inner class from
    subscripted generics and Optional, not emit the literal composite string."""

    def test_string_list_of_known_aggregates_inner(self) -> None:
        # `"list[Engine] | None"` → aggregates Engine (not associates the
        # literal "list[Engine]").
        src = (
            "class Engine:\n    pass\n"
            "class Car:\n    parts: 'list[Engine] | None'\n"
        )
        edges = _edges(src)
        assert ("Car", "Engine", "aggregates") in edges
        assert not any(t == "list[Engine]" for _, t, _ in edges)

    def test_string_optional_of_known_aggregates_inner(self) -> None:
        src = (
            "class Engine:\n    pass\n"
            "class Car:\n    motor: 'Optional[Engine]'\n"
        )
        edges = _edges(src)
        assert ("Car", "Engine", "aggregates") in edges
        assert not any(t == "Optional[Engine]" for _, t, _ in edges)


class TestWR03UnionBothOperands:
    """WR-03: `X | Y` of two known classes must emit an edge for EACH operand."""

    def test_union_of_two_known_classes_emits_both(self) -> None:
        src = (
            "class Engine:\n    pass\n"
            "class Wheel:\n    pass\n"
            "class Car:\n    part: Engine | Wheel\n"
        )
        edges = _edges(src)
        assert ("Car", "Engine", "aggregates") in edges
        assert ("Car", "Wheel", "aggregates") in edges

    def test_union_with_none_still_aggregates_single(self) -> None:
        src = (
            "class Wheel:\n    pass\n"
            "class Car:\n    spare: Wheel | None\n"
        )
        edges = _edges(src)
        assert ("Car", "Wheel", "aggregates") in edges


class TestWR06TypingNamesNotEdges:
    """WR-06: typing special forms (ClassVar/Type/Final/...) are not classes
    and must not produce composes/associates edges."""

    def test_classvar_type_final_no_edge(self) -> None:
        src = (
            "from typing import ClassVar, Type, Final\n"
            "class Foo:\n"
            "    a: ClassVar\n"
            "    b: Type\n"
            "    c: Final\n"
        )
        edges = _edges(src)
        assert not any(t in {"ClassVar", "Type", "Final"} for _, t, _ in edges)


class TestClassNodes:
    def test_class_nodes_emitted(self) -> None:
        model = extract(_build_cav("class A:\n    pass\nclass B(A):\n    pass\n", "m.py"), _CONFIG)
        node_ids = {n.node_id for n in model.nodes}
        assert node_ids == {"A", "B"}
        assert all(n.node_type == "class" for n in model.nodes)

    def test_no_class_no_nodes(self) -> None:
        model = extract(_build_cav("x = 1\n", "m.py"), _CONFIG)
        assert model.nodes == []
        assert model.edges == []


class TestClassDiagramDeterminism:
    def test_nodes_sorted(self) -> None:
        model = extract(_build_cav("class Z:\n    pass\nclass A:\n    pass\n", "m.py"), _CONFIG)
        ids = [n.node_id for n in model.nodes]
        assert ids == sorted(ids)

    def test_edges_sorted(self) -> None:
        model = extract(_build_cav(CLASS_HIERARCHY_SOURCE, CLASS_HIERARCHY_PATH), _CONFIG)
        keys = [(e.source, e.target, e.edge_type, e.label) for e in model.edges]
        assert keys == sorted(keys)

    def test_byte_identical_repeated(self) -> None:
        a = extract(_build_cav(CLASS_HIERARCHY_SOURCE, CLASS_HIERARCHY_PATH), _CONFIG)
        b = extract(_build_cav(CLASS_HIERARCHY_SOURCE, CLASS_HIERARCHY_PATH), _CONFIG)
        assert a.model_dump_json() == b.model_dump_json()


class TestClassDiagramReturnType:
    def test_returns_graphmodel(self) -> None:
        model = extract(_build_cav("class A:\n    pass\n", "m.py"), _CONFIG)
        assert isinstance(model, GraphModel)
