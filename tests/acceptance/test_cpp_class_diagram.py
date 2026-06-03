"""D-04 acceptance: C++ class diagram via the public execute() surface.

Exercises the full ``CodeParserExecutor`` path on ``.cpp`` artifacts (the suffix
override selects the cpp track) and reads ``result.content.class_diagram``.
Proves the C++ analog of the Python DIA-01 acceptance:

- inheritance edges (incl. MULTIPLE inheritance -> >=2 ``inherits`` edges),
- the composes / aggregates / associates relationship spectrum from FIELD_DECLs,
- NO catch-all ``"uses"`` / ``"other"`` edge is ever emitted,
- builtin members produce no edge, nodes are ``node_type="class"``.

Traces: LNG-04, LNG-05.
"""

from __future__ import annotations

from pathlib import Path

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.evaluations.graph_base import GraphModel

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "cpp"


def _class_diagram(fixture_name: str, path: str) -> GraphModel:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    raw = (_FIXTURES / fixture_name).read_bytes()
    result = exe.execute(config, raw, path)
    return result.content.class_diagram


class TestCppClassDiagramInheritance:
    def test_multiple_inheritance_two_edges(self) -> None:
        model = _class_diagram("inheritance.cpp", "inheritance.cpp")
        assert isinstance(model, GraphModel)
        inherits = {(e.source, e.target) for e in model.edges if e.edge_type == "inherits"}
        # Circle : public Shape, public Point  -> two inherits edges (multiple).
        assert ("Circle", "Shape") in inherits
        assert ("Circle", "Point") in inherits
        # Single inheritance still present.
        assert ("Square", "Shape") in inherits
        circle_inherits = [
            e for e in model.edges if e.source == "Circle" and e.edge_type == "inherits"
        ]
        assert len(circle_inherits) >= 2

    def test_class_nodes_are_class_type(self) -> None:
        model = _class_diagram("inheritance.cpp", "inheritance.cpp")
        assert all(n.node_type == "class" for n in model.nodes)
        node_ids = {n.node_id for n in model.nodes}
        assert {"Shape", "Point", "Square", "Circle"} <= node_ids


class TestCppClassDiagramRelations:
    def test_relationship_spectrum(self) -> None:
        model = _class_diagram("relations.cpp", "relations.cpp")
        edges = {(e.source, e.target, e.edge_type) for e in model.edges}
        # Point center; -> value member of known type -> composes
        assert ("Diagram", "Point", "composes") in edges
        # Shape* parent; -> pointer of known type -> aggregates
        assert ("Diagram", "Shape", "aggregates") in edges
        # Point& ref; -> reference of known type -> aggregates
        assert ("Diagram", "Point", "aggregates") in edges
        # Unknown* widget; -> pointer of an undeclared (not-in-known) type ->
        # associates (the explicit undecidable fallback). NOTE: under
        # PARSE_INCOMPLETE libclang recovers the never-declared `Unknown` to
        # implicit `int`, so the associates TARGET is libclang's recovered base
        # (a deterministic artifact documented in 04-04); the must-have is that
        # the edge is `associates` from Diagram and NEVER a `uses`/`other`.
        assoc = {(e.source, e.target) for e in model.edges if e.edge_type == "associates"}
        assert any(src == "Diagram" for src, _ in assoc)

    def test_full_spectrum_present(self) -> None:
        model = _class_diagram("relations.cpp", "relations.cpp")
        kinds = {e.edge_type for e in model.edges}
        assert {"composes", "aggregates", "associates"} <= kinds

    def test_no_uses_catch_all_and_builtin_skipped(self) -> None:
        model = _class_diagram("relations.cpp", "relations.cpp")
        kinds = {e.edge_type for e in model.edges}
        assert "uses" not in kinds
        assert "other" not in kinds
        # `int count;` is a builtin value member -> NO structural relation edge.
        # (The only `int` target that appears is the associates fallback from
        # libclang's implicit-int recovery of `Unknown*` — never composes/
        # aggregates, which would mean a builtin value field leaked.)
        structural_int = {
            (e.source, e.target)
            for e in model.edges
            if e.target == "int" and e.edge_type in ("composes", "aggregates")
        }
        assert structural_int == set()
