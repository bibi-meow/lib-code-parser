"""LNG-04 structural schema parity: cpp NormalizedArtifact ≡ Python CodeContent.

Runs the PUBLIC ``CodeParserExecutor.execute`` once on a Python fixture and once
on a C++ fixture (the ``.cpp`` suffix selects the cpp track) and asserts the two
``NormalizedArtifact.content`` objects expose the IDENTICAL set of
``CodeContent`` field names (same slots) AND the same annotated Pydantic type per
shared slot. This proves the cpp output has byte-identical Pydantic shape to the
Python output — the LNG-04 success criterion — through the public surface, not
just by inspecting the class.

The shared slots are common across languages by construction (the executor
``setattr``s EVALUATIONS[cav.language] results into the SAME-named CodeContent
slots), so this test is the structural assertion that the cpp track never drifts
a slot name or type away from the Python track.

Traces: LNG-04.
"""

from __future__ import annotations

from pathlib import Path

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.models.infrastructure.artifact import CodeContent
from tests.conftest import EXAMPLE_SOURCE

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "cpp"


def _execute(raw: bytes, path: str) -> CodeContent:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    return CodeParserExecutor().execute(config, raw, path).content


def _py_content() -> CodeContent:
    return _execute(EXAMPLE_SOURCE.encode("utf-8"), "src/order_service.py")


def _cpp_content() -> CodeContent:
    raw = (_FIXTURES / "relations.cpp").read_bytes()
    return _execute(raw, "relations.cpp")


def test_identical_codecontent_slots() -> None:
    """Python and C++ content expose the IDENTICAL set of CodeContent slots."""
    py = _py_content()
    cpp = _cpp_content()
    py_slots = set(type(py).model_fields.keys())
    cpp_slots = set(type(cpp).model_fields.keys())
    assert py_slots == cpp_slots
    # Both are the SAME CodeContent class — the strongest structural parity.
    assert type(py) is type(cpp) is CodeContent


def test_identical_slot_types() -> None:
    """Each shared slot has the same annotated Pydantic type for both languages."""
    py = _py_content()
    cpp = _cpp_content()
    py_fields = type(py).model_fields
    cpp_fields = type(cpp).model_fields
    for name in py_fields:
        assert py_fields[name].annotation == cpp_fields[name].annotation, name


def test_diagram_slots_are_graphmodel_for_both() -> None:
    """The 5 diagram slots are GraphModel instances on BOTH language outputs."""
    from lib_code_parser.models.evaluations.graph_base import GraphModel

    diagram_slots = (
        "class_diagram",
        "sequence_diagram",
        "component_diagram",
        "package_diagram",
        "state_diagram",
    )
    py = _py_content()
    cpp = _cpp_content()
    for slot in diagram_slots:
        assert isinstance(getattr(py, slot), GraphModel), f"py {slot}"
        assert isinstance(getattr(cpp, slot), GraphModel), f"cpp {slot}"
