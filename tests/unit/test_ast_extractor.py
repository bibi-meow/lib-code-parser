"""Unit tests for ast_extractor module."""

from __future__ import annotations

from lib_code_parser.ast_extractor import (
    _extract_annotation,
    _extract_trace_tags,
    _get_module_name,
    extract_functions,
)


class TestGetModuleName:
    def test_stem_extraction(self) -> None:
        assert _get_module_name("foo.py") == "foo"

    def test_nested_path(self) -> None:
        assert _get_module_name("a/b/c.py") == "c"

    def test_no_extension(self) -> None:
        assert _get_module_name("module") == "module"


class TestExtractAnnotation:
    def test_none_returns_empty(self) -> None:
        assert _extract_annotation(None) == ""

    def test_name_node(self) -> None:
        import ast
        node = ast.parse("x: str").body[0].annotation  # type: ignore[union-attr]
        assert _extract_annotation(node) == "str"

    def test_subscript(self) -> None:
        import ast
        node = ast.parse("x: list[str]").body[0].annotation  # type: ignore[union-attr]
        result = _extract_annotation(node)
        assert "list" in result
        assert "str" in result


class TestExtractTraceTags:
    def test_single_trace(self) -> None:
        tags = _extract_trace_tags("Traces: FR-01")
        assert len(tags) == 1
        assert "FR-01" in tags[0].refs

    def test_multiple_refs(self) -> None:
        tags = _extract_trace_tags("Traces: US-01, FR-02")
        assert len(tags) == 1
        assert "US-01" in tags[0].refs
        assert "FR-02" in tags[0].refs

    def test_no_traces(self) -> None:
        tags = _extract_trace_tags("Some docstring without traces")
        assert tags == []

    def test_tag_name_is_traces(self) -> None:
        tags = _extract_trace_tags("Traces: FR-01")
        assert tags[0].tag == "Traces"

    def test_traces_in_multiline(self) -> None:
        doc = "Summary.\n\nTraces: US-10, FR-20\n"
        tags = _extract_trace_tags(doc)
        refs = tags[0].refs
        assert "US-10" in refs
        assert "FR-20" in refs


class TestExtractFunctions:
    def test_empty_source(self) -> None:
        result = extract_functions("", "mod.py")
        assert result == []

    def test_simple_function(self) -> None:
        source = "def hello(): pass\n"
        fns = extract_functions(source, "mod.py")
        ids = [f.node_id for f in fns]
        assert "mod.hello" in ids

    def test_async_function(self) -> None:
        source = "async def fetch(): pass\n"
        fns = extract_functions(source, "mod.py")
        ids = [f.node_id for f in fns]
        assert "mod.fetch" in ids

    def test_class_and_method(self) -> None:
        source = "class A:\n    def foo(self): pass\n"
        fns = extract_functions(source, "mod.py")
        ids = [f.node_id for f in fns]
        assert "mod.A" in ids
        assert "mod.A.foo" in ids

    def test_method_self_excluded_from_params(self) -> None:
        source = "class A:\n    def foo(self, x: int): pass\n"
        fns = extract_functions(source, "mod.py")
        method = next(f for f in fns if f.node_id == "mod.A.foo")
        param_names = [p.name for p in method.params]
        assert "self" not in param_names
        assert "x" in param_names

    def test_function_with_type_params(self) -> None:
        source = "def greet(name: str, count: int) -> bool: pass\n"
        fns = extract_functions(source, "mod.py")
        fn = next(f for f in fns if f.node_id == "mod.greet")
        assert fn.return_type == "bool"
        assert fn.params[0].type_annotation == "str"
        assert fn.params[1].type_annotation == "int"

    def test_source_range_set(self) -> None:
        source = "def foo():\n    pass\n"
        fns = extract_functions(source, "mod.py")
        fn = fns[0]
        assert fn.source_range.start_line == 1
        assert fn.source_range.end_line >= 1
