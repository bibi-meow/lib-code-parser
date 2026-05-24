"""Omnibus SCH-02 test — all 8 primitive models must declare extra="forbid".

Wave 0 omnibus test per Plan 01-04 Task 3 / 01-VALIDATION.md.

Traces: SCH-02, AST-04.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lib_code_parser.models.primitives import (
    CallEdge,
    CallGraph,
    ContractInfo,
    FunctionNode,
    ParamInfo,
    SourceRange,
    TraceTag,
    TypeDep,
)

PRIMITIVE_MODELS = [
    FunctionNode,
    ParamInfo,
    SourceRange,
    TraceTag,
    CallEdge,
    CallGraph,
    TypeDep,
    ContractInfo,
]


def test_all_primitive_models_forbid_extra() -> None:
    """Every primitive model class declares ConfigDict(extra='forbid')."""
    offenders = [
        cls.__name__ for cls in PRIMITIVE_MODELS if cls.model_config.get("extra") != "forbid"
    ]
    assert offenders == [], f"Primitive models missing extra='forbid' (SCH-02): {offenders}"


def test_function_node_rejects_extra() -> None:
    """FunctionNode rejects unknown fields."""
    with pytest.raises(ValidationError):
        FunctionNode(node_id="x", kind="function", surprise=1)


def test_call_edge_rejects_extra() -> None:
    """CallEdge rejects unknown fields."""
    with pytest.raises(ValidationError):
        CallEdge(caller="a", callee="b", surprise=1)


def test_type_dep_rejects_extra() -> None:
    """TypeDep rejects unknown fields."""
    with pytest.raises(ValidationError):
        TypeDep(source="a", target="b", surprise=1)


def test_contract_info_rejects_extra() -> None:
    """ContractInfo rejects unknown fields."""
    with pytest.raises(ValidationError):
        ContractInfo(node_id="x", surprise=1)


def test_contract_info_source_kind_literal() -> None:
    """ContractInfo.source_kind is a closed Literal (AST-04)."""
    with pytest.raises(ValidationError):
        ContractInfo(node_id="x", source_kind="bogus")
