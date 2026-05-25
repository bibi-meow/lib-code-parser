"""Unit tests for callgraph_builder module."""

from __future__ import annotations

from lib_code_parser.callgraph_builder import _get_call_name, build_callgraph


class TestGetCallName:
    def test_simple_name(self) -> None:
        import ast

        node = ast.parse("foo()").body[0].value  # type: ignore[union-attr]
        assert isinstance(node, ast.Call)
        assert _get_call_name(node.func) == "foo"

    def test_attribute_call(self) -> None:
        import ast

        node = ast.parse("self.bar()").body[0].value  # type: ignore[union-attr]
        assert isinstance(node, ast.Call)
        assert _get_call_name(node.func) == "bar"


class TestBuildCallGraph:
    def test_empty(self) -> None:
        cg = build_callgraph("", "mod.py")
        assert cg.nodes == []
        assert cg.edges == []

    def test_function_no_calls(self) -> None:
        source = "def foo():\n    pass\n"
        cg = build_callgraph(source, "mod.py")
        assert "mod.foo" in cg.nodes
        assert cg.edges == []

    def test_function_with_call(self) -> None:
        source = "def foo():\n    bar()\n"
        cg = build_callgraph(source, "mod.py")
        callee_names = {e.callee for e in cg.edges}
        assert "bar" in callee_names

    def test_method_with_call(self) -> None:
        source = "class A:\n    def foo(self):\n        self.helper()\n"
        cg = build_callgraph(source, "mod.py")
        callee_names = {e.callee for e in cg.edges}
        assert "helper" in callee_names

    def test_no_duplicate_nodes(self) -> None:
        source = "class A:\n    def foo(self): pass\n    def bar(self): pass\n"
        cg = build_callgraph(source, "mod.py")
        assert len(cg.nodes) == len(set(cg.nodes))

    def test_caller_is_qualified(self) -> None:
        source = "class A:\n    def foo(self):\n        bar()\n"
        cg = build_callgraph(source, "mod.py")
        callers = {e.caller for e in cg.edges}
        assert "mod.A.foo" in callers
