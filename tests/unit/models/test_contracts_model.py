"""Unit tests for the restructured ContractInfo / ContractEntry models (D-12 β).

Phase 2 Plan 02-04 Task 1: ContractInfo gains a ContractEntry list (per-entry
source_kind discriminator) and backward-compat @computed_field helpers
(preconditions / invariants / postconditions) derived from entries.

Traces: SCH-02, AST-04, D-12, D-14.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lib_code_parser.models.primitives.contracts import (
    ContractEntry,
    ContractInfo,
)


class TestContractEntry:
    def test_contract_entry_minimal_construction(self) -> None:
        """ContractEntry constructs with required name/source_kind/kind."""
        e = ContractEntry(
            name="validate_status",
            source_kind="pydantic_field_validator",
            kind="precondition",
        )
        assert e.name == "validate_status"
        assert e.source_kind == "pydantic_field_validator"
        assert e.kind == "precondition"
        assert e.decorator_name == ""
        assert e.line_no == 0

    def test_contract_entry_rejects_invalid_source_kind(self) -> None:
        """source_kind is a closed Literal of 4 values (AST-04)."""
        with pytest.raises(ValidationError):
            ContractEntry(name="x", source_kind="invalid_kind", kind="precondition")

    def test_contract_entry_rejects_invalid_kind(self) -> None:
        """kind is a closed Literal (precondition/invariant/postcondition)."""
        with pytest.raises(ValidationError):
            ContractEntry(name="x", source_kind="pydantic_field_validator", kind="unknown")

    def test_contract_entry_rejects_extra_field(self) -> None:
        """SCH-02 extra='forbid' on ContractEntry."""
        with pytest.raises(ValidationError):
            ContractEntry(
                extra_field="boom",
                name="x",
                source_kind="pydantic_field_validator",
                kind="precondition",
            )


class TestContractInfo:
    def test_contract_info_default_construction(self) -> None:
        """ContractInfo() (no args) yields empty entries + empty helper lists.

        This is the FunctionNode.contracts default-factory compatibility guard
        (T-02-16): the restructure MUST keep ContractInfo() no-args constructable.
        """
        ci = ContractInfo()
        assert ci.entries == []
        assert ci.preconditions == []
        assert ci.invariants == []
        assert ci.postconditions == []

    def test_contract_info_rejects_extra_field(self) -> None:
        """SCH-02 extra='forbid' on ContractInfo is preserved post-restructure."""
        with pytest.raises(ValidationError):
            ContractInfo(node_id="x", surprise=1)

    def test_helper_properties_bucket_by_kind(self) -> None:
        """preconditions/invariants/postconditions derive from entries by kind."""
        ci = ContractInfo(
            entries=[
                ContractEntry(
                    name="validate_status",
                    source_kind="pydantic_field_validator",
                    kind="precondition",
                ),
                ContractEntry(
                    name="__post_init__",
                    source_kind="dataclass_post_init",
                    kind="precondition",
                ),
            ]
        )
        assert ci.preconditions == ["validate_status", "__post_init__"]
        assert ci.invariants == []
        assert ci.postconditions == []

    def test_helper_properties_invariant_and_postcondition(self) -> None:
        """invariant / postcondition buckets are populated independently."""
        ci = ContractInfo(
            entries=[
                ContractEntry(
                    name="check_total",
                    source_kind="pydantic_model_validator",
                    kind="invariant",
                ),
                ContractEntry(
                    name="finalize",
                    source_kind="pydantic_model_validator",
                    kind="postcondition",
                ),
            ]
        )
        assert ci.invariants == ["check_total"]
        assert ci.postconditions == ["finalize"]
        assert ci.preconditions == []

    def test_model_dump_json_roundtrip_includes_entries(self) -> None:
        """JSON dump contains entries and reconstructs byte-identically.

        computed_field helpers appear in the dump (Pydantic v2 default), so a
        re-parse must drop them (they are not constructor fields) yet round-trip
        on `entries`.
        """
        ci = ContractInfo(
            node_id="mod.Foo",
            entries=[
                ContractEntry(
                    name="validate_status",
                    source_kind="pydantic_field_validator",
                    kind="precondition",
                    decorator_name="field_validator",
                    line_no=10,
                )
            ],
        )
        payload = ci.model_dump_json()
        assert '"entries"' in payload
        assert '"preconditions"' in payload  # computed_field present in dump
        # Reconstruct from entries only (computed_fields are read-only outputs).
        rebuilt = ContractInfo(node_id=ci.node_id, entries=ci.entries)
        assert rebuilt.model_dump_json() == payload


class TestFunctionNodeDefaultFactoryCompat:
    def test_function_node_default_contracts_is_empty_contract_info(self) -> None:
        """T-02-16: FunctionNode.contracts default factory still works.

        The default_factory constructs ContractInfo() with no args; the
        restructure preserves that constructability.
        """
        from lib_code_parser.models.primitives.functions import FunctionNode, SourceRange

        fn = FunctionNode(
            node_id="x",
            kind="function",
            source_range=SourceRange(start_line=0, end_line=0),
        )
        assert isinstance(fn.contracts, ContractInfo)
        assert fn.contracts.entries == []
        assert fn.contracts.preconditions == []
