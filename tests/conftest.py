"""Shared fixtures for lib-code-parser tests."""

from __future__ import annotations

import ast

import pytest

from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig


def build_python_cav(source: str, path: str) -> CAV:
    """Build a Python CAV from source (test-side ``ast.parse`` only).

    Shared Wave-0 harness lifted from test_contracts_extractor.py so every
    Phase 3 extractor test (Plans 02-06) imports ONE CAV builder. The library
    never parses on its own in tests; the test side stashes ``ast.Module`` into
    the CAV payload, matching what the python frontend does at runtime.
    """
    return CAV(language="python", path=path, payload=ast.parse(source))


@pytest.fixture
def parser_config() -> ParserConfig:
    """Reusable default ParserConfig for Phase 3 extractor tests."""
    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


# The "example" source code from the design spec
EXAMPLE_SOURCE = '''
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional


class OrderService:
    """Order management service.

    Traces: US-01, FR-02
    """

    def create_order(self, items: list[str], user_id: str) -> dict:
        """Create a new order.

        Traces: FR-01
        """
        total = self._calculate_total(items)
        return {"order_id": "ORD-001", "total": total}

    def _calculate_total(self, items: list[str]) -> float:
        return len(items) * 10.0

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        return True


class OrderModel(BaseModel):
    order_id: str
    status: str
    total: float

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("pending", "confirmed", "cancelled"):
            raise ValueError("Invalid status")
        return v

    @model_validator(mode="after")
    def check_total(self) -> "OrderModel":
        if self.total < 0:
            raise ValueError("Total cannot be negative")
        return self


def process_payment(amount: float, method: str) -> bool:
    """Process payment.

    Traces: FR-03, US-22
    """
    return True
'''

EXAMPLE_PATH = "src/order_service.py"
EXAMPLE_MODULE = "order_service"


@pytest.fixture
def example_source() -> str:
    return EXAMPLE_SOURCE


@pytest.fixture
def example_path() -> str:
    return EXAMPLE_PATH


@pytest.fixture
def example_raw() -> bytes:
    return EXAMPLE_SOURCE.encode("utf-8")
