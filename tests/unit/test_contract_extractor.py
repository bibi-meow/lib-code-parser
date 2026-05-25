"""Unit tests for contract_extractor module."""

from __future__ import annotations

from lib_code_parser.contract_extractor import extract_contracts


class TestExtractContracts:
    def test_empty_source(self) -> None:
        assert extract_contracts("", "mod.py") == {}

    def test_class_no_validators(self) -> None:
        source = "class Foo:\n    def bar(self): pass\n"
        assert "mod.Foo" not in extract_contracts(source, "mod.py")

    def test_field_validator(self) -> None:
        source = """
class Foo:
    @field_validator("x")
    @classmethod
    def validate_x(cls, v):
        return v
"""
        contracts = extract_contracts(source, "mod.py")
        assert "mod.Foo" in contracts
        assert "validate_x" in contracts["mod.Foo"].preconditions

    def test_validator_legacy(self) -> None:
        source = """
class Bar:
    @validator("field")
    @classmethod
    def check_field(cls, v):
        return v
"""
        contracts = extract_contracts(source, "mod.py")
        assert "mod.Bar" in contracts
        assert "check_field" in contracts["mod.Bar"].preconditions

    def test_model_validator(self) -> None:
        source = """
class Baz:
    @model_validator(mode="after")
    def check_all(self):
        return self
"""
        contracts = extract_contracts(source, "mod.py")
        assert "mod.Baz" in contracts
        assert "check_all" in contracts["mod.Baz"].invariants

    def test_post_init(self) -> None:
        source = "class D:\n    def __post_init__(self): pass\n"
        contracts = extract_contracts(source, "mod.py")
        assert "mod.D" in contracts
        assert "__post_init__" in contracts["mod.D"].preconditions

    def test_module_name_from_path(self) -> None:
        source = """
class MyModel:
    @field_validator("x")
    @classmethod
    def val_x(cls, v): return v
"""
        contracts = extract_contracts(source, "src/my_module.py")
        assert "my_module.MyModel" in contracts

    def test_mixed_pre_and_invariants(self) -> None:
        source = """
class Mixed:
    @field_validator("a")
    @classmethod
    def check_a(cls, v): return v

    @model_validator(mode="after")
    def check_all(self): return self
"""
        contracts = extract_contracts(source, "mod.py")
        ci = contracts["mod.Mixed"]
        assert "check_a" in ci.preconditions
        assert "check_all" in ci.invariants
