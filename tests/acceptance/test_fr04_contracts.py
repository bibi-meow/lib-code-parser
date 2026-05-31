"""FR-04: Contract extraction from Pydantic validators (Phase 2 v0.2.0 form).

Consumes the typed ParserConfig + dispatch-driven executor through the public
v0.2.0 surface. Reflects the Plan 02-04 ContractInfo restructure (D-12 β):
- per-entry `source_kind` on `ci.entries[i]`
  (pydantic_field_validator / pydantic_model_validator / dataclass_post_init)
- v0.1.0 backward-compat helpers `ci.preconditions` / `ci.invariants`
  (read-only @computed_field list[str] of method names)
"""

from __future__ import annotations

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig
from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE


def _contracts(source: str, path: str) -> dict:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, source.encode("utf-8"), path)
    return result.content.contracts


@pytest.fixture
def example_contracts() -> dict:
    return _contracts(EXAMPLE_SOURCE, EXAMPLE_PATH)


class TestPydanticContracts:
    def test_order_model_has_contracts(self, example_contracts: dict) -> None:
        assert "order_service.OrderModel" in example_contracts

    def test_field_validator_is_precondition(self, example_contracts: dict) -> None:
        ci = example_contracts["order_service.OrderModel"]
        # v0.1.0 backward-compat helper:
        assert "validate_status" in ci.preconditions
        # v0.2.0 per-entry source_kind verification:
        entry = next(e for e in ci.entries if e.name == "validate_status")
        assert entry.source_kind == "pydantic_field_validator"
        assert entry.kind == "precondition"

    def test_model_validator_is_invariant(self, example_contracts: dict) -> None:
        ci = example_contracts["order_service.OrderModel"]
        # v0.1.0 backward-compat helper:
        assert "check_total" in ci.invariants
        # v0.2.0 per-entry source_kind verification:
        entry = next(e for e in ci.entries if e.name == "check_total")
        assert entry.source_kind == "pydantic_model_validator"
        assert entry.kind == "invariant"

    def test_order_service_has_no_contracts(self, example_contracts: dict) -> None:
        # OrderService has no validators -> not in the contracts dict.
        assert "order_service.OrderService" not in example_contracts


class TestPostInitContract:
    def test_post_init_is_precondition(self) -> None:
        source = """
class MyData:
    def __post_init__(self):
        pass
"""
        contracts = _contracts(source, "data.py")
        assert "data.MyData" in contracts
        ci = contracts["data.MyData"]
        assert "__post_init__" in ci.preconditions
        entry = next(e for e in ci.entries if e.name == "__post_init__")
        assert entry.source_kind == "dataclass_post_init"


class TestContractMinimal:
    def test_empty_source(self) -> None:
        contracts = _contracts("", "mod.py")
        assert contracts == {}

    def test_class_without_validators(self) -> None:
        contracts = _contracts("class Foo:\n    def bar(self): pass\n", "mod.py")
        assert "mod.Foo" not in contracts

    def test_validator_decorator_name(self) -> None:
        source = """
from pydantic import validator

class Foo:
    @validator("field")
    @classmethod
    def validate_field(cls, v):
        return v
"""
        contracts = _contracts(source, "mod.py")
        assert "mod.Foo" in contracts
        ci = contracts["mod.Foo"]
        assert "validate_field" in ci.preconditions
        entry = next(e for e in ci.entries if e.name == "validate_field")
        assert entry.source_kind == "pydantic_validator"
