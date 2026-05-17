"""Tests for LIB-FR-04: ContractInfo extraction."""

import ast

from lib_code_parser.contract_extractor import extract_contract_info


def _parse_class(source: str) -> ast.ClassDef:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            return node
    raise ValueError("No ClassDef found")


def test_field_validator_adds_precondition():
    source = (
        "class MyModel:\n"
        "    name: str\n"
        "    @field_validator('name')\n"
        "    def validate_name(cls, v):\n"
        "        return v\n"
    )
    class_node = _parse_class(source)
    contract = extract_contract_info(class_node)
    assert any("name" in p for p in contract.preconditions)


def test_post_init_precondition():
    source = (
        "class Params:\n"
        "    value: int\n"
        "    def __post_init__(self):\n"
        "        if self.value < 0:\n"
        "            raise ValueError('negative')\n"
    )
    class_node = _parse_class(source)
    contract = extract_contract_info(class_node)
    assert len(contract.preconditions) >= 1


def test_no_validators_empty_contract():
    source = "class Simple:\n    def greet(self):\n        pass\n"
    class_node = _parse_class(source)
    contract = extract_contract_info(class_node)
    assert contract.preconditions == []
    assert contract.invariants == []


def test_extract_contracts_false_returns_empty():
    """When extract_contracts=False, ContractInfo should be empty."""
    source = (
        "class MyModel:\n"
        "    name: str\n"
        "    @field_validator('name')\n"
        "    def validate_name(cls, v):\n"
        "        return v\n"
    )
    class_node = _parse_class(source)
    contract = extract_contract_info(class_node, extract_contracts=False)
    assert contract.preconditions == []
    assert contract.invariants == []


def test_validator_decorator_variant():
    source = (
        "class User:\n"
        "    email: str\n"
        "    @validator('email')\n"
        "    def validate_email(cls, v):\n"
        "        return v\n"
    )
    class_node = _parse_class(source)
    contract = extract_contract_info(class_node)
    assert any("email" in p for p in contract.preconditions)
