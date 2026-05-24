"""Primitive contract model — ContractInfo with source_kind discriminator per AST-04.

Distinguishes Pydantic validator decorators from dataclass ``__post_init__`` per
D-04 substrate.

Traces: SCH-02, AST-04.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = ""
    source_kind: Literal[
        "pydantic_validator",
        "pydantic_model_validator",
        "pydantic_field_validator",
        "dataclass_post_init",
    ] = "pydantic_validator"
    preconditions: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
