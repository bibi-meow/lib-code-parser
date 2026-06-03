"""FR-06: enabled=False returns empty CodeContent (Phase 2 v0.2.0 form).

Consumes the typed ParserConfig + dispatch-driven executor through the public
v0.2.0 surface. The v0.1.0 dict-style `params={...}` is gone (D-02 explicit
break); `language` is now a typed top-level field.
"""

from __future__ import annotations

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig


@pytest.fixture
def executor() -> CodeParserExecutor:
    return CodeParserExecutor()


@pytest.fixture
def example_raw() -> bytes:
    from tests.conftest import EXAMPLE_SOURCE

    return EXAMPLE_SOURCE.encode("utf-8")


class TestDisabledExecutor:
    def test_disabled_returns_empty_functions(
        self, executor: CodeParserExecutor, example_raw: bytes
    ) -> None:
        config = ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            enabled=False,
        )
        result = executor.execute(config, example_raw, "src/order_service.py")
        assert result.content.functions == []

    def test_disabled_returns_empty_callgraph(
        self, executor: CodeParserExecutor, example_raw: bytes
    ) -> None:
        config = ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            enabled=False,
        )
        result = executor.execute(config, example_raw, "src/order_service.py")
        assert result.content.call_graph.nodes == []
        assert result.content.call_graph.edges == []

    def test_disabled_returns_empty_type_deps(
        self, executor: CodeParserExecutor, example_raw: bytes
    ) -> None:
        config = ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            enabled=False,
        )
        result = executor.execute(config, example_raw, "src/order_service.py")
        assert result.content.type_deps == []

    def test_disabled_artifact_id_preserved(
        self, executor: CodeParserExecutor, example_raw: bytes
    ) -> None:
        config = ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            enabled=False,
        )
        result = executor.execute(config, example_raw, "src/order_service.py")
        assert result.artifact_id.path == "src/order_service.py"

    def test_disabled_artifact_type_preserved(
        self, executor: CodeParserExecutor, example_raw: bytes
    ) -> None:
        config = ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            enabled=False,
        )
        result = executor.execute(config, example_raw, "src/order_service.py")
        assert result.artifact_type == "code"


class TestCppSupported:
    """Phase 4: the cpp frontend (04-03) + cpp extractors (04-04) are live.

    The pre-Phase-4 stub assumption ("cpp returns empty content") is obsolete:
    a .cpp suffix now forces language="cpp", selects FRONTENDS["cpp"], and runs
    the cpp PRIMITIVES so real FunctionNode/CallGraph/TypeDep content is emitted.
    """

    def test_cpp_extension_extracts_functions(self, executor: CodeParserExecutor) -> None:
        config = ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            language="python",
            enabled=True,
        )
        # .cpp suffix forces language="cpp" -> cpp frontend + cpp extractors run.
        result = executor.execute(config, b"int main() {}", "src/main.cpp")
        ids = {(f.node_id, f.kind) for f in result.content.functions}
        assert ("main", "function") in ids

    def test_cpp_empty_source_returns_empty(self, executor: CodeParserExecutor) -> None:
        # Empty source: a valid cpp parse with no declarations -> empty content.
        config = ParserConfig(
            artifact_type="code",
            executor_lib="lib_code_parser",
            language="cpp",
            enabled=True,
        )
        result = executor.execute(config, b"", "src/main.cpp")
        assert result.content.functions == []
