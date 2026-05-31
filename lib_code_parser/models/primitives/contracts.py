"""Primitive contract models — ContractEntry + ContractInfo per-entry source_kind.

Per Phase 2 D-12 (β): each ContractInfo carries a list of ContractEntry, and
each entry has its own source_kind ∈ {pydantic_validator, pydantic_field_validator,
pydantic_model_validator, dataclass_post_init} per AST-04. This per-entry granularity
lets verifiers see exactly which validator decorator was used on each method, without
re-expanding a class-level discriminator (preserves PROJECT.md Core Value: physical-
side emits the maximum-fidelity facts; the verifier alone interprets the physical↔
logical gap).

Phase 2 restructure (D-14): the v0.1.0/Phase-1 class-level discriminator
(single source_kind + 3 list[str] for preconditions/invariants/postconditions) is
breaking-replaced by ContractEntry list. Backward-compat is provided via Pydantic v2
@computed_field helpers (preconditions / invariants / postconditions) so existing
callers reading `ci.preconditions` continue to get list[str].

Traces: SCH-02, AST-04, D-12, D-14.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

SourceKind = Literal[
    "pydantic_validator",
    "pydantic_model_validator",
    "pydantic_field_validator",
    "dataclass_post_init",
]


ContractKind = Literal["precondition", "invariant", "postcondition"]


class ContractEntry(BaseModel):
    """One contract statement (decorator or __post_init__) on a class member.

    - name: method name (e.g. "validate_status", "__post_init__")
    - source_kind: D-11 mapping result after alias resolution
    - kind: precondition / invariant / postcondition bucket (D-12)
    - decorator_name: canonical pydantic decorator name after alias resolution
      (e.g. "field_validator" even if the source said "@fv"); empty for __post_init__
    - line_no: source line of the decorated method (1-based)
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    source_kind: SourceKind
    kind: ContractKind
    decorator_name: str = ""
    line_no: int = 0


class ContractInfo(BaseModel):
    """Per-class contract aggregate with per-entry source_kind discriminator (D-12 β).

    Backward-compat: the v0.1.0 caller pattern ``ci.preconditions / ci.invariants /
    ci.postconditions`` (list[str] of method names) is preserved via @computed_field
    helpers derived from ``entries``. New callers should read ``entries`` directly.
    """

    model_config = ConfigDict(extra="forbid")

    node_id: str = ""
    entries: list[ContractEntry] = Field(default_factory=list)

    @computed_field
    @property
    def preconditions(self) -> list[str]:
        return [e.name for e in self.entries if e.kind == "precondition"]

    @computed_field
    @property
    def invariants(self) -> list[str]:
        return [e.name for e in self.entries if e.kind == "invariant"]

    @computed_field
    @property
    def postconditions(self) -> list[str]:
        return [e.name for e in self.entries if e.kind == "postcondition"]
