"""Wave 0 tests for lib_code_parser/models/evaluations/spec.py.

Locks the four spec models (FunctionSpec / ClassSpec / DocstringSection /
SpecCondition) with extra="forbid" (SCH-02) and the SPC-04 source_kind closed
Literal before any spec extractor is written. Direct submodule import path is
used so the suite stays valid once the package barrel is rewritten.

Traces: SPC-01, SPC-02, SPC-04.
"""

from __future__ import annotations

from typing import get_args

import pytest
from pydantic import ValidationError

from lib_code_parser.models.evaluations.spec import (
    ClassSpec,
    DocstringSection,
    FunctionSpec,
    SpecCondition,
    SpecConditionSourceKind,
)

CANONICAL_SOURCE_KINDS = {
    "docstring",
    "icontract_require",
    "icontract_ensure",
    "icontract_invariant",
    "deal_pre",
    "deal_post",
    "deal_ensure",
    "deal_inv",
    "pep316_pre",
    "pep316_post",
}


class TestFunctionSpec:
    def test_constructible_with_defaults(self) -> None:
        spec = FunctionSpec(node_id="m.f")
        assert spec.node_id == "m.f"
        assert spec.signature == ""
        assert spec.docstring_sections == []
        assert spec.preconditions == []
        assert spec.postconditions == []
        assert spec.source_range is None

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            FunctionSpec(node_id="m.f", unknown_field=1)  # type: ignore[call-arg]


class TestClassSpec:
    def test_constructible_with_defaults(self) -> None:
        spec = ClassSpec(node_id="m.C")
        assert spec.node_id == "m.C"
        assert spec.definition == ""
        assert spec.members == []
        assert spec.invariants == []

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            ClassSpec(node_id="m.C", unknown_field=1)  # type: ignore[call-arg]


class TestDocstringSection:
    def test_constructible_with_defaults(self) -> None:
        sec = DocstringSection(kind="summary")
        assert sec.kind == "summary"
        assert sec.name == ""
        assert sec.type_ref == ""
        assert sec.text == ""

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            DocstringSection(kind="summary", unknown_field=1)  # type: ignore[call-arg]

    def test_rejects_unknown_kind(self) -> None:
        with pytest.raises(ValidationError):
            DocstringSection(kind="examples")  # type: ignore[arg-type]


class TestSpecCondition:
    def test_constructible(self) -> None:
        cond = SpecCondition(
            kind="precondition",
            text="x > 0",
            source_kind="docstring",
        )
        assert cond.kind == "precondition"
        assert cond.text == "x > 0"
        assert cond.source_kind == "docstring"
        assert cond.line_no == 0

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            SpecCondition(
                kind="precondition",
                text="x > 0",
                source_kind="docstring",
                unknown_field=1,  # type: ignore[call-arg]
            )

    def test_rejects_unknown_source_kind(self) -> None:
        with pytest.raises(ValidationError):
            SpecCondition(
                kind="precondition",
                text="x > 0",
                source_kind="random_lib",  # type: ignore[arg-type]
            )


class TestSpecConditionSourceKind:
    def test_spc04_values_present(self) -> None:
        values = set(get_args(SpecConditionSourceKind))
        assert values == CANONICAL_SOURCE_KINDS
