"""Unit tests for lib_code_parser.extractors.primitives.functions.extract.

Covers kind discriminator / skip_self_cls / TraceTag verbatim regex parity /
source_range / docstring extraction / emit order / isolated-call semantics.

CAV is assembled via the Python Frontend's build_cav (Plan 02-01 deliverable),
not via a direct parse call in the test, per RESEARCH §Pitfall 7 — this keeps
the AST-05 "single parse site" intent intact even at the test layer.
"""

from __future__ import annotations

import pytest

from lib_code_parser.extractors.primitives.functions import extract
from lib_code_parser.frontends.python import build_cav
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.functions import FunctionNode, TraceTag
from tests.conftest import EXAMPLE_SOURCE


@pytest.fixture
def example_config() -> ParserConfig:
    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


@pytest.fixture
def example_cav(example_config: ParserConfig):
    return build_cav(EXAMPLE_SOURCE.encode("utf-8"), "src/order_service.py", example_config)


def _by_id(nodes: list[FunctionNode], node_id: str) -> FunctionNode:
    matches = [n for n in nodes if n.node_id == node_id]
    assert matches, f"expected node_id {node_id!r}; got {[n.node_id for n in nodes]}"
    return matches[0]


def test_extract_class_node(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    cls = _by_id(nodes, "order_service.OrderService")
    assert cls.kind == "class"


def test_extract_method_node(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    method = _by_id(nodes, "order_service.OrderService.create_order")
    assert method.kind == "method"


def test_extract_top_level_function(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    func = _by_id(nodes, "order_service.process_payment")
    assert func.kind == "function"
    param_names = {p.name for p in func.params}
    assert "amount" in param_names
    assert "method" in param_names


def test_extract_return_type_annotation(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    method = _by_id(nodes, "order_service.OrderService.create_order")
    assert method.return_type == "dict"


def test_extract_docstring(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    cls = _by_id(nodes, "order_service.OrderService")
    assert "Order management service" in cls.docstring


def test_extract_trace_tags_verbatim_regex_parity(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    cls = _by_id(nodes, "order_service.OrderService")
    # v0.1.0 baseline: `Traces: US-01, FR-02` -> one TraceTag, refs == ["US-01", "FR-02"]
    assert cls.trace_tags == [TraceTag(tag="Traces", refs=["US-01", "FR-02"])]


def test_extract_source_range_positive(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    method = _by_id(nodes, "order_service.OrderService.create_order")
    assert method.source_range.start_line > 0
    assert method.source_range.end_line >= method.source_range.start_line


def test_extract_emit_order_classes_first_then_top_level(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    kinds = [n.kind for n in nodes]
    # First class appears before the top-level function (v0.1.0 parity emit order).
    first_function_idx = kinds.index("function")
    first_class_idx = kinds.index("class")
    assert first_class_idx < first_function_idx
    # And every "function" entry comes after every "class"/"method" entry.
    last_non_function_idx = max(
        i for i, k in enumerate(kinds) if k in ("class", "method")
    )
    assert first_function_idx > last_non_function_idx


def test_extract_isolated_call_without_executor(example_cav, example_config) -> None:
    # extract() must complete with no CodeParserExecutor involvement (ROADMAP SC-4).
    nodes = extract(example_cav, example_config)
    assert isinstance(nodes, list)
    assert all(isinstance(n, FunctionNode) for n in nodes)
    assert len(nodes) > 0


def test_extract_no_self_in_method_params(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    method = _by_id(nodes, "order_service.OrderService.create_order")
    param_names = {p.name for p in method.params}
    assert "self" not in param_names
    assert "items" in param_names
    assert "user_id" in param_names


def test_extract_no_self_for_top_level(example_cav, example_config) -> None:
    nodes = extract(example_cav, example_config)
    func = _by_id(nodes, "order_service.process_payment")
    param_names = {p.name for p in func.params}
    assert param_names == {"amount", "method"}
