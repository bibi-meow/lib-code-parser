"""Primitive AST data models.

FunctionNode aggregate and its leaf types (ParamInfo, SourceRange, TraceTag).

Traces: SCH-02. Phase 2 fills these via extract_functions().
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from lib_code_parser.models.primitives.contracts import ContractInfo


class TraceTag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag: str
    refs: list[str] = Field(default_factory=list)


class SourceRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_line: int
    end_line: int


class ParamInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type_annotation: str = ""


class FunctionNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    kind: str  # "function" | "method" | "class"
    params: list[ParamInfo] = Field(default_factory=list)
    return_type: str = ""
    contracts: "ContractInfo" = Field(
        default_factory=lambda: __import__(
            "lib_code_parser.models.primitives.contracts", fromlist=["ContractInfo"]
        ).ContractInfo()
    )
    docstring: str = ""
    trace_tags: list[TraceTag] = Field(default_factory=list)
    source_range: SourceRange = Field(default_factory=lambda: SourceRange(start_line=0, end_line=0))


from lib_code_parser.models.primitives.contracts import ContractInfo  # noqa: E402

FunctionNode.model_rebuild()
