"""Tests for LIB-FR-02: CallGraph generation."""

from lib_code_parser.callgraph_builder import build_callgraph
from lib_code_parser.models import FunctionNode


def _make_node(node_id: str, kind: str = "function") -> FunctionNode:
    return FunctionNode(node_id=node_id, kind=kind)


def test_caller_to_callee_edge():
    source = "def bar():\n    pass\n\ndef foo():\n    bar()\n"
    functions = [_make_node("mymod.foo"), _make_node("mymod.bar")]
    cg = build_callgraph(source, functions, module_name="mymod")
    assert ("mymod.foo", "mymod.bar") in cg.edges


def test_no_calls_empty_edges():
    source = "def foo():\n    pass\n"
    functions = [_make_node("mymod.foo")]
    cg = build_callgraph(source, functions, module_name="mymod")
    assert cg.edges == []


def test_nodes_contain_all_functions():
    source = "def foo():\n    pass\ndef bar():\n    pass\n"
    functions = [_make_node("mymod.foo"), _make_node("mymod.bar")]
    cg = build_callgraph(source, functions, module_name="mymod")
    assert "mymod.foo" in cg.nodes
    assert "mymod.bar" in cg.nodes


def test_method_call_graph():
    source = "class A:\n    def foo(self):\n        self.bar()\n    def bar(self):\n        pass\n"
    functions = [
        _make_node("mymod.A", kind="class"),
        _make_node("mymod.A.foo", kind="method"),
        _make_node("mymod.A.bar", kind="method"),
    ]
    cg = build_callgraph(source, functions, module_name="mymod")
    # self.bar() call — should appear as edge from A.foo to A.bar
    assert ("mymod.A.foo", "mymod.A.bar") in cg.edges


def test_external_call_not_in_edges():
    """Calls to functions not in the module function list are excluded."""
    source = "def foo():\n    print('hello')\n"
    functions = [_make_node("mymod.foo")]
    cg = build_callgraph(source, functions, module_name="mymod")
    # print is external; no edge should be created
    assert cg.edges == []
