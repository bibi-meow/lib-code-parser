"""Verifier-facing spec models (FunctionSpec / ClassSpec).

Structured function/class specifications extracted from Python source — the
physical-side analog of lib-spec-parser's logical spec output, so the verifier
can diff code-derived specs against spec-derived ones (US-22). All models use
extra="forbid" (SCH-02). The SPC-04 contract-source taxonomy lives HERE as a
closed Literal (SpecConditionSourceKind), keeping the frozen Phase 2
primitives/contracts.py untouched (RESEARCH §449).

Traces: SPC-01, SPC-02, SPC-04.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:  # pragma: no cover — forward-ref carrier
    # Referenced only by the string annotation on FunctionSpec.source_range.
    # Plan 04 owns primitives; TYPE_CHECKING avoids a hard import-time dependency
    # so the evaluations layer ships independently.
    from lib_code_parser.models.primitives.functions import SourceRange

# SPC-04 home: the closed taxonomy of contract sources a SpecCondition may come
# from. "docstring" covers Google/NumPy/Sphinx Napoleon Raises/pre/post prose;
# the remaining values name auxiliary contract libraries (icontract / deal /
# PEP-316). This Literal lives in the evaluations layer (NOT in the frozen
# primitives/contracts.py SourceKind, which is the Pydantic-validator taxonomy).
SpecConditionSourceKind = Literal[
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
]


class DocstringSection(BaseModel):
    """One parsed docstring section (params/returns/raises/summary/other)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["params", "returns", "raises", "summary", "other"]
    name: str = ""
    type_ref: str = ""
    text: str = ""


class SpecCondition(BaseModel):
    """A pre/post-condition or invariant statement with its SPC-04 source."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["precondition", "postcondition", "invariant"]
    text: str
    source_kind: SpecConditionSourceKind
    line_no: int = 0


class FunctionSpec(BaseModel):
    """Structured specification of a single function/method (SPC-01)."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    signature: str = ""
    docstring_sections: list[DocstringSection] = Field(default_factory=list)
    preconditions: list[SpecCondition] = Field(default_factory=list)
    postconditions: list[SpecCondition] = Field(default_factory=list)
    source_range: "SourceRange | None" = None


class ClassSpec(BaseModel):
    """Structured specification of a single class (SPC-02)."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    definition: str = ""
    members: list[str] = Field(default_factory=list)
    invariants: list[SpecCondition] = Field(default_factory=list)


# Resolve FunctionSpec's "SourceRange" string forward ref. Plan 04 ships
# primitives/functions.py; the import is wrapped so the evaluations layer still
# rebuilds when primitives are present (they are, post-Phase-2).
try:
    from lib_code_parser.models.primitives.functions import SourceRange  # noqa: F401
except ImportError:  # pragma: no cover — primitives always present post-Phase-2
    pass
else:
    FunctionSpec.model_rebuild()
