"""DIA-07 shared schema-conformance scaffold for diagram outputs.

Every diagram extractor (Plans 02-04) must emit a ``GraphModel`` whose nodes,
edges, and guards validate against the closed graph_base.py schema, and whose
only physical-side metadata lives on ``physical_*`` / ``source_*`` prefixed
fields (SCH-02 / D-04 shared cross-diagram truth). This module provides the
reusable ``assert_valid_graphmodel`` helper; Plans 02-04 add cases that feed
real diagram outputs through it.

Traces: DIA-07, SCH-02, D-04.
"""

from __future__ import annotations

from lib_code_parser.models.evaluations.graph_base import (
    GraphEdge,
    GraphModel,
    GraphNode,
    GuardExpr,
)

# Fields on GraphEdge that carry physical-side (verifier-invisible) metadata.
# Any non-logical field a diagram extractor relies on MUST use one of these
# prefixes so the verifier's diff can drop them (Core Value: physical facts,
# logical interpretation lives in the verifier).
_PHYSICAL_PREFIXES = ("physical_", "source_")


def assert_valid_graphmodel(model: object) -> None:
    """Assert ``model`` is a schema-conformant GraphModel.

    Raises AssertionError if the value is not a GraphModel, or if any node /
    edge / guard is not the canonical graph_base type, or if any extra
    physical metadata leaks outside the physical_* / source_* prefix.
    """
    assert isinstance(model, GraphModel), f"expected GraphModel, got {type(model)!r}"

    for node in model.nodes:
        assert isinstance(node, GraphNode), f"non-GraphNode in nodes: {type(node)!r}"
    for edge in model.edges:
        assert isinstance(edge, GraphEdge), f"non-GraphEdge in edges: {type(edge)!r}"
    for guard in model.guards:
        assert isinstance(guard, GuardExpr), f"non-GuardExpr in guards: {type(guard)!r}"

    # No physical metadata may leak outside the physical_*/source_* prefix.
    # extra="forbid" already blocks unknown fields at construction; this guard
    # documents the prefix discipline for Plans 02-04 cases that set metadata.
    _logical_edge_fields = {"source", "target", "edge_type", "label"}
    for edge in model.edges:
        for field_name in type(edge).model_fields:
            if field_name in _logical_edge_fields:
                continue
            assert field_name.startswith(_PHYSICAL_PREFIXES), (
                f"non-logical edge field {field_name!r} must use a "
                f"physical_*/source_* prefix"
            )


def _cav(source: str, path: str) -> object:
    import ast

    from lib_code_parser.models.infrastructure.cav import CAV

    return CAV(
        language="python",
        path=path,
        payload=ast.parse(source),
        raw_content=source.encode("utf-8"),
    )


def _config() -> object:
    from lib_code_parser.models.infrastructure.config import ParserConfig

    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


# Source exercising all three Plan 03-02 diagrams at once: imports (component),
# a directory path (package), and a class hierarchy with relationships (class).
_DIA_SOURCE = (
    "from typing import Optional\n"
    "import os\n"
    "class Engine:\n"
    "    pass\n"
    "class Car(Engine):\n"
    "    motor: Engine\n"
    "    spare: Optional[Engine]\n"
    "    gizmo: Unknown\n"
)
_DIA_PATH = "src/pkg/auto.py"


class TestDia07RealOutputs:
    """DIA-07: every Plan 03-02 diagram output validates as a GraphModel and
    leaks no non-physical_/source_ metadata onto edges."""

    def test_class_diagram_output_valid(self) -> None:
        from lib_code_parser.extractors.evaluations.class_diagram import extract

        model = extract(_cav(_DIA_SOURCE, _DIA_PATH), _config())
        assert_valid_graphmodel(model)

    def test_component_diagram_output_valid(self) -> None:
        from lib_code_parser.extractors.evaluations.component_diagram import extract

        model = extract(_cav(_DIA_SOURCE, _DIA_PATH), _config())
        assert_valid_graphmodel(model)

    def test_package_diagram_output_valid(self) -> None:
        from lib_code_parser.extractors.evaluations.package_diagram import extract

        model = extract(_cav(_DIA_SOURCE, _DIA_PATH), _config())
        assert_valid_graphmodel(model)

    def test_sequence_diagram_output_valid(self) -> None:
        from lib_code_parser.extractors.evaluations.sequence_diagram import extract

        # Source with calls + control-flow frames so the sequence output has
        # both `calls` edges and alt/loop/par labels to validate.
        seq_source = (
            "def f(items):\n"
            "    setup()\n"
            "    if items:\n"
            "        notify()\n"
            "    for it in items:\n"
            "        handle(it)\n"
        )
        model = extract(_cav(seq_source, "src/pkg/seq.py"), _config())
        assert_valid_graphmodel(model)

    def test_state_diagram_output_valid(self) -> None:
        from lib_code_parser.extractors.evaluations.state_diagram import extract

        # transitions.Machine FSM → states + transitions_to edges + guards.
        state_source = (
            "from transitions import Machine\n"
            "class Phone:\n"
            "    def __init__(self):\n"
            "        self.m = Machine(\n"
            "            states=['idle', 'busy'],\n"
            "            transitions=[{'trigger': 'go', 'source': 'idle', 'dest': 'busy'}],\n"
            "        )\n"
        )
        model = extract(_cav(state_source, "src/pkg/fsm.py"), _config())
        assert_valid_graphmodel(model)
        assert any(e.edge_type == "transitions_to" for e in model.edges)

    def test_all_edges_use_closed_edgekinds(self) -> None:
        from lib_code_parser.extractors.evaluations.class_diagram import (
            extract as class_extract,
        )
        from lib_code_parser.extractors.evaluations.component_diagram import (
            extract as comp_extract,
        )

        allowed = {"inherits", "composes", "aggregates", "associates", "imports"}
        for extract_fn in (class_extract, comp_extract):
            model = extract_fn(_cav(_DIA_SOURCE, _DIA_PATH), _config())
            for edge in model.edges:
                assert edge.edge_type in allowed, edge.edge_type


class TestSchemaHelperOnEmptyModel:
    """The DIA-07 helper accepts an inert empty GraphModel (Wave-0 baseline)."""

    def test_empty_graphmodel_is_valid(self) -> None:
        assert_valid_graphmodel(GraphModel())

    def test_populated_graphmodel_is_valid(self) -> None:
        model = GraphModel(
            nodes=[GraphNode(node_id="A", node_type="class", label="A")],
            edges=[
                GraphEdge(
                    source="A",
                    target="B",
                    edge_type="imports",
                    physical_module="m",
                    source_unresolved=False,
                )
            ],
            guards=[GuardExpr(from_state="X", to_state="Y", condition="c")],
        )
        assert_valid_graphmodel(model)

    def test_non_graphmodel_rejected(self) -> None:
        import pytest

        with pytest.raises(AssertionError):
            assert_valid_graphmodel(object())
