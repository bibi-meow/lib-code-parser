"""FR-04: Contract extraction from Pydantic validators."""

from __future__ import annotations

import pytest

from lib_code_parser.contract_extractor import extract_contracts


@pytest.fixture
def example_source() -> str:
    from tests.conftest import EXAMPLE_SOURCE

    return EXAMPLE_SOURCE


@pytest.fixture
def example_path() -> str:
    return "src/order_service.py"


class TestPydanticContracts:
    def test_order_model_has_contracts(self, example_source: str, example_path: str) -> None:
        contracts = extract_contracts(example_source, example_path)
        assert "order_service.OrderModel" in contracts

    def test_field_validator_is_precondition(self, example_source: str, example_path: str) -> None:
        contracts = extract_contracts(example_source, example_path)
        ci = contracts["order_service.OrderModel"]
        assert "validate_status" in ci.preconditions

    def test_model_validator_is_invariant(self, example_source: str, example_path: str) -> None:
        contracts = extract_contracts(example_source, example_path)
        ci = contracts["order_service.OrderModel"]
        assert "check_total" in ci.invariants

    def test_order_service_has_no_contracts(self, example_source: str, example_path: str) -> None:
        contracts = extract_contracts(example_source, example_path)
        # OrderService has no validators
        assert "order_service.OrderService" not in contracts


class TestPostInitContract:
    def test_post_init_is_precondition(self) -> None:
        source = """
class MyData:
    def __post_init__(self):
        pass
"""
        contracts = extract_contracts(source, "data.py")
        assert "data.MyData" in contracts
        assert "__post_init__" in contracts["data.MyData"].preconditions


class TestContractMinimal:
    def test_empty_source(self) -> None:
        contracts = extract_contracts("", "mod.py")
        assert contracts == {}

    def test_class_without_validators(self) -> None:
        source = "class Foo:\n    def bar(self): pass\n"
        contracts = extract_contracts(source, "mod.py")
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
        contracts = extract_contracts(source, "mod.py")
        assert "mod.Foo" in contracts
        assert "validate_field" in contracts["mod.Foo"].preconditions
