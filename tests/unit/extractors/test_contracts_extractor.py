"""Unit tests for the pure-CAV contracts extractor (AST-04).

Covers RESEARCH §3.1 C1-C7 plus the D-13 mixed case, alias scope restriction,
isolated-import (SC-4), and EXAMPLE_SOURCE semantic parity. The extractor consumes
a CAV (ast.Module payload) and must NOT call ast.parse itself; the test fixture
builds the CAV via ast.parse (test-side only).

Traces: AST-04, AST-05, D-11, D-12, D-13, US-01, US-22.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.primitives.contracts import extract
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _build_cav(source: str, path: str) -> CAV:
    """Build a Python CAV from source (test-side parse only)."""
    return CAV(language="python", path=path, payload=ast.parse(source))


def test_c1_simple_validator() -> None:
    """C1: @validator("x") (simple Name) → pydantic_validator/precondition."""
    source = """
from pydantic import validator

class Foo:
    @validator("x")
    @classmethod
    def val_x(cls, v):
        return v
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    ci = result["mod.Foo"]
    assert len(ci.entries) == 1
    e = ci.entries[0]
    assert e.name == "val_x"
    assert e.source_kind == "pydantic_validator"
    assert e.kind == "precondition"
    assert e.decorator_name == "validator"


def test_c2_attribute_field_validator() -> None:
    """C2: @pydantic.field_validator("x") (Attribute) → pydantic_field_validator."""
    source = """
import pydantic

class Foo:
    @pydantic.field_validator("x")
    @classmethod
    def val_x(cls, v):
        return v
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    ci = result["mod.Foo"]
    assert len(ci.entries) == 1
    assert ci.entries[0].source_kind == "pydantic_field_validator"
    assert ci.entries[0].decorator_name == "field_validator"


def test_c3_alias_resolution_fixes_v01_bug() -> None:
    """C3: aliased `from pydantic import field_validator as fv; @fv(...)` resolves.

    v0.1.0 failed to detect this. Phase 2 resolves the alias to the canonical
    field_validator name.
    """
    source = """
from pydantic import field_validator as fv

class Foo:
    @fv("x")
    @classmethod
    def val_x(cls, v):
        return v
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    ci = result["mod.Foo"]
    assert len(ci.entries) == 1
    assert ci.entries[0].source_kind == "pydantic_field_validator"
    assert ci.entries[0].decorator_name == "field_validator"


def test_c4_root_validator_recognized() -> None:
    """C4: @root_validator → pydantic_model_validator/invariant (v0.1.0 bug fix)."""
    source = """
from pydantic import root_validator

class Foo:
    @root_validator
    def check(cls, values):
        return values
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    ci = result["mod.Foo"]
    assert len(ci.entries) == 1
    assert ci.entries[0].source_kind == "pydantic_model_validator"
    assert ci.entries[0].kind == "invariant"
    assert ci.entries[0].decorator_name == "root_validator"


def test_c5_decorator_chain_first_match() -> None:
    """C5: @field_validator + @classmethod → exactly 1 entry (first match wins)."""
    source = """
from pydantic import field_validator

class Foo:
    @field_validator("x")
    @classmethod
    def val_x(cls, v):
        return v
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    ci = result["mod.Foo"]
    assert len(ci.entries) == 1


def test_c6_factory_call_form() -> None:
    """C6: @validator("x", pre=True) (Call form) → 1 entry."""
    source = """
from pydantic import validator

class Foo:
    @validator("x", pre=True)
    def val_x(cls, v):
        return v
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    ci = result["mod.Foo"]
    assert len(ci.entries) == 1
    assert ci.entries[0].source_kind == "pydantic_validator"


def test_c7_post_init_in_plain_class_gets_dataclass_post_init() -> None:
    """C7: __post_init__ in a plain class → dataclass_post_init (ROADMAP SC-3).

    The verifier must no longer see __post_init__ as an unconditional Pydantic
    concept; method-name-only detection tags it dataclass_post_init.
    """
    source = """
class PlainClass:
    def __post_init__(self):
        pass
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    ci = result["mod.PlainClass"]
    assert len(ci.entries) == 1
    e = ci.entries[0]
    assert e.name == "__post_init__"
    assert e.source_kind == "dataclass_post_init"
    assert e.source_kind != "pydantic_validator"
    assert e.decorator_name == ""


def test_mixed_validator_and_post_init() -> None:
    """D-13: @field_validator + __post_init__ in one class → 2 entries, distinct source_kind."""
    source = """
from pydantic import field_validator

class Mixed:
    @field_validator("x")
    @classmethod
    def val_x(cls, v):
        return v

    def __post_init__(self):
        pass
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    ci = result["mod.Mixed"]
    assert len(ci.entries) == 2
    kinds = {e.source_kind for e in ci.entries}
    assert kinds == {"pydantic_field_validator", "dataclass_post_init"}


def test_non_pydantic_import_not_classified() -> None:
    """T-02-19: a same-name decorator imported from a non-pydantic lib is not classified.

    Detection requires the decorator's local name to resolve through the
    pydantic-scoped import map (or be a `pydantic.X` attribute form). A bare
    `from other_lib import field_validator` never enters that map, so it is
    excluded — preventing false positives that would leak function names into
    the physical-architecture output.
    """
    source = """
from other_lib import field_validator

class Foo:
    @field_validator("x")
    def val_x(cls, v):
        return v
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    assert "mod.Foo" not in result


def test_no_import_bare_decorator_not_classified() -> None:
    """A decorator name with no import at all is not classified (no pydantic provenance)."""
    source = """
class Foo:
    @field_validator("x")
    def val_x(cls, v):
        return v
"""
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    assert "mod.Foo" not in result


def test_isolated_import_no_executor() -> None:
    """SC-4: extract() is callable without importing CodeParserExecutor."""
    import sys

    # The extractor module must not transitively import the executor.
    mod = sys.modules["lib_code_parser.extractors.primitives.contracts"]
    assert mod is not None
    source = "class Foo:\n    def __post_init__(self): pass\n"
    result = extract(_build_cav(source, "mod.py"), _CONFIG)
    assert "mod.Foo" in result


def test_extract_on_example_source_returns_order_model_contracts() -> None:
    """EXAMPLE_SOURCE: OrderModel has validate_status (precondition) + check_total (invariant)."""
    from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE

    result = extract(_build_cav(EXAMPLE_SOURCE, EXAMPLE_PATH), _CONFIG)
    assert "order_service.OrderModel" in result
    ci = result["order_service.OrderModel"]
    assert "validate_status" in ci.preconditions
    assert "check_total" in ci.invariants
    # OrderService has no validators
    assert "order_service.OrderService" not in result
