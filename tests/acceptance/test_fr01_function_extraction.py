"""FR-01: Function and class extraction acceptance tests (Phase 2 v0.2.0 form).

Consumes the typed ParserConfig + dispatch-driven executor through the public
v0.2.0 surface (`from lib_code_parser import CodeParserExecutor, ParserConfig`).
No legacy direct-extractor imports remain.
Assertions preserve v0.1.0 FunctionNode parity (node_id / kind / params /
docstring / return_type / source_range) per RESEARCH §7.1.
"""

from __future__ import annotations

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig
from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE


@pytest.fixture
def nodes() -> dict:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, EXAMPLE_SOURCE.encode("utf-8"), EXAMPLE_PATH)
    return {fn.node_id: fn for fn in result.content.functions}


class TestClassExtraction:
    def test_class_node_extracted(self, nodes: dict) -> None:
        assert "order_service.OrderService" in nodes

    def test_class_kind(self, nodes: dict) -> None:
        assert nodes["order_service.OrderService"].kind == "class"

    def test_model_class_extracted(self, nodes: dict) -> None:
        assert "order_service.OrderModel" in nodes

    def test_class_docstring(self, nodes: dict) -> None:
        doc = nodes["order_service.OrderService"].docstring
        assert "Order management service" in doc


class TestMethodExtraction:
    def test_create_order_method(self, nodes: dict) -> None:
        assert "order_service.OrderService.create_order" in nodes

    def test_calculate_total_method(self, nodes: dict) -> None:
        assert "order_service.OrderService._calculate_total" in nodes

    def test_cancel_order_method(self, nodes: dict) -> None:
        assert "order_service.OrderService.cancel_order" in nodes

    def test_method_kind(self, nodes: dict) -> None:
        assert nodes["order_service.OrderService.create_order"].kind == "method"

    def test_method_params_no_self(self, nodes: dict) -> None:
        params = nodes["order_service.OrderService.create_order"].params
        param_names = [p.name for p in params]
        assert "self" not in param_names
        assert "items" in param_names
        assert "user_id" in param_names

    def test_method_return_type(self, nodes: dict) -> None:
        rt = nodes["order_service.OrderService.create_order"].return_type
        assert rt == "dict"

    def test_method_source_range(self, nodes: dict) -> None:
        sr = nodes["order_service.OrderService.create_order"].source_range
        assert sr.start_line > 0
        assert sr.end_line >= sr.start_line


class TestTopLevelFunctionExtraction:
    def test_process_payment_extracted(self, nodes: dict) -> None:
        assert "order_service.process_payment" in nodes

    def test_process_payment_kind(self, nodes: dict) -> None:
        assert nodes["order_service.process_payment"].kind == "function"

    def test_process_payment_params(self, nodes: dict) -> None:
        params = nodes["order_service.process_payment"].params
        param_names = [p.name for p in params]
        assert "amount" in param_names
        assert "method" in param_names

    def test_process_payment_return_type(self, nodes: dict) -> None:
        rt = nodes["order_service.process_payment"].return_type
        assert rt == "bool"

    def test_process_payment_docstring(self, nodes: dict) -> None:
        doc = nodes["order_service.process_payment"].docstring
        assert "Process payment" in doc
