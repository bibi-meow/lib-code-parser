"""FR-01: Function and class extraction acceptance tests."""

from __future__ import annotations

import pytest

from lib_code_parser.ast_extractor import extract_functions


@pytest.fixture
def example_source() -> str:
    from tests.conftest import EXAMPLE_SOURCE
    return EXAMPLE_SOURCE


@pytest.fixture
def example_path() -> str:
    return "src/order_service.py"


def _nodes_by_id(source: str, path: str) -> dict:
    fns = extract_functions(source, path)
    return {fn.node_id: fn for fn in fns}


class TestClassExtraction:
    def test_class_node_extracted(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        assert "order_service.OrderService" in nodes

    def test_class_kind(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        assert nodes["order_service.OrderService"].kind == "class"

    def test_model_class_extracted(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        assert "order_service.OrderModel" in nodes

    def test_class_docstring(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        doc = nodes["order_service.OrderService"].docstring
        assert "Order management service" in doc


class TestMethodExtraction:
    def test_create_order_method(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        assert "order_service.OrderService.create_order" in nodes

    def test_calculate_total_method(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        assert "order_service.OrderService._calculate_total" in nodes

    def test_cancel_order_method(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        assert "order_service.OrderService.cancel_order" in nodes

    def test_method_kind(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        assert nodes["order_service.OrderService.create_order"].kind == "method"

    def test_method_params_no_self(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        params = nodes["order_service.OrderService.create_order"].params
        param_names = [p.name for p in params]
        assert "self" not in param_names
        assert "items" in param_names
        assert "user_id" in param_names

    def test_method_return_type(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        rt = nodes["order_service.OrderService.create_order"].return_type
        assert rt == "dict"

    def test_method_source_range(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        sr = nodes["order_service.OrderService.create_order"].source_range
        assert sr.start_line > 0
        assert sr.end_line >= sr.start_line


class TestTopLevelFunctionExtraction:
    def test_process_payment_extracted(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        assert "order_service.process_payment" in nodes

    def test_process_payment_kind(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        assert nodes["order_service.process_payment"].kind == "function"

    def test_process_payment_params(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        params = nodes["order_service.process_payment"].params
        param_names = [p.name for p in params]
        assert "amount" in param_names
        assert "method" in param_names

    def test_process_payment_return_type(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        rt = nodes["order_service.process_payment"].return_type
        assert rt == "bool"

    def test_process_payment_docstring(self, example_source: str, example_path: str) -> None:
        nodes = _nodes_by_id(example_source, example_path)
        doc = nodes["order_service.process_payment"].docstring
        assert "Process payment" in doc


class TestModuleNameFromPath:
    def test_nested_path(self) -> None:
        from lib_code_parser.ast_extractor import _get_module_name
        assert _get_module_name("src/order_service.py") == "order_service"

    def test_flat_path(self) -> None:
        from lib_code_parser.ast_extractor import _get_module_name
        assert _get_module_name("order_service.py") == "order_service"

    def test_deep_nested(self) -> None:
        from lib_code_parser.ast_extractor import _get_module_name
        assert _get_module_name("lib_code_parser/executor.py") == "executor"
