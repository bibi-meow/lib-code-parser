"""Unit tests for CodeParserExecutor."""

from __future__ import annotations

import pytest

from lib_code_parser.executor import CodeParserExecutor
from lib_code_parser.models import ParserConfig


@pytest.fixture
def executor() -> CodeParserExecutor:
    return CodeParserExecutor()


@pytest.fixture
def basic_config() -> ParserConfig:
    return ParserConfig(
        artifact_type="code",
        executor_lib="lib_code_parser",
        params={"language": "python", "extract_contracts": True},
        enabled=True,
    )


SIMPLE_SOURCE = b"def hello(name: str) -> str:\n    return 'Hello ' + name\n"


class TestExecutorBasic:
    def test_returns_normalized_artifact(
        self, executor: CodeParserExecutor, basic_config: ParserConfig
    ) -> None:
        result = executor.execute(basic_config, SIMPLE_SOURCE, "mod.py")
        assert result.artifact_id.path == "mod.py"
        assert result.artifact_type == "code"

    def test_functions_populated(
        self, executor: CodeParserExecutor, basic_config: ParserConfig
    ) -> None:
        result = executor.execute(basic_config, SIMPLE_SOURCE, "mod.py")
        assert len(result.content.functions) > 0

    def test_callgraph_present(
        self, executor: CodeParserExecutor, basic_config: ParserConfig
    ) -> None:
        result = executor.execute(basic_config, SIMPLE_SOURCE, "mod.py")
        assert isinstance(result.content.call_graph.nodes, list)

    def test_type_deps_present(
        self, executor: CodeParserExecutor, basic_config: ParserConfig
    ) -> None:
        result = executor.execute(basic_config, SIMPLE_SOURCE, "mod.py")
        assert isinstance(result.content.type_deps, list)


class TestExecutorContracts:
    def test_contracts_applied_when_enabled(
        self, executor: CodeParserExecutor
    ) -> None:
        source = b'''
class Foo:
    @field_validator("x")
    @classmethod
    def val_x(cls, v): return v
'''
        config = ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            params={"extract_contracts": True},
            enabled=True,
        )
        result = executor.execute(config, source, "mod.py")
        class_node = next(
            (f for f in result.content.functions if f.node_id == "mod.Foo"), None
        )
        assert class_node is not None
        assert "val_x" in class_node.contracts.preconditions

    def test_contracts_skipped_when_disabled(
        self, executor: CodeParserExecutor
    ) -> None:
        source = b'''
class Foo:
    @field_validator("x")
    @classmethod
    def val_x(cls, v): return v
'''
        config = ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            params={"extract_contracts": False},
            enabled=True,
        )
        result = executor.execute(config, source, "mod.py")
        class_node = next(
            (f for f in result.content.functions if f.node_id == "mod.Foo"), None
        )
        assert class_node is not None
        # contracts should be empty (default ContractInfo)
        assert class_node.contracts.preconditions == []


class TestExecutorEdgeCases:
    def test_empty_source(
        self, executor: CodeParserExecutor, basic_config: ParserConfig
    ) -> None:
        result = executor.execute(basic_config, b"", "mod.py")
        assert result.content.functions == []

    def test_bytes_decoded(
        self, executor: CodeParserExecutor, basic_config: ParserConfig
    ) -> None:
        source = "def foo(): pass\n".encode("utf-8")
        result = executor.execute(basic_config, source, "mod.py")
        ids = [f.node_id for f in result.content.functions]
        assert "mod.foo" in ids

    def test_h_extension_returns_empty(
        self, executor: CodeParserExecutor, basic_config: ParserConfig
    ) -> None:
        result = executor.execute(basic_config, b"", "header.h")
        assert result.content.functions == []
