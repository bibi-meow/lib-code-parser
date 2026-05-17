"""Tests for LIB-FR-01: Python code FunctionNode extraction."""

from lib_code_parser.ast_extractor import extract_functions


def test_simple_function_extracted():
    source = "def greet(name: str) -> str:\n    return f'Hello {name}'\n"
    nodes = extract_functions(source, module_name="mymod")
    assert len(nodes) == 1
    node = nodes[0]
    assert node.node_id == "mymod.greet"
    assert node.kind == "function"
    assert node.return_type == "str"
    assert len(node.params) == 1
    assert node.params[0].name == "name"
    assert node.params[0].type_annotation == "str"


def test_class_and_method_extracted():
    source = "class MyClass:\n    def my_method(self, x: int) -> None:\n        pass\n"
    nodes = extract_functions(source, module_name="mymod")
    # Should contain both class node and method node
    node_ids = [n.node_id for n in nodes]
    assert "mymod.MyClass" in node_ids
    assert "mymod.MyClass.my_method" in node_ids

    method = next(n for n in nodes if n.node_id == "mymod.MyClass.my_method")
    assert method.kind == "method"
    # self should be excluded or type_annotation = None
    non_self_params = [p for p in method.params if p.name != "self"]
    assert len(non_self_params) == 1
    assert non_self_params[0].name == "x"
    assert non_self_params[0].type_annotation == "int"


def test_empty_source_returns_empty_list():
    nodes = extract_functions("", module_name="mymod")
    assert nodes == []


def test_function_no_annotations():
    source = "def add(a, b):\n    return a + b\n"
    nodes = extract_functions(source, module_name="mymod")
    assert len(nodes) == 1
    assert nodes[0].node_id == "mymod.add"
    assert nodes[0].return_type is None
    for p in nodes[0].params:
        assert p.type_annotation is None


def test_source_range_populated():
    source = "def foo():\n    pass\n"
    nodes = extract_functions(source, module_name="mymod")
    assert nodes[0].source_range is not None
    assert nodes[0].source_range.start_line == 1


def test_docstring_captured():
    source = 'def foo():\n    """My docstring."""\n    pass\n'
    nodes = extract_functions(source, module_name="mymod")
    assert nodes[0].docstring == "My docstring."


def test_class_only_no_methods():
    source = "class Empty:\n    pass\n"
    nodes = extract_functions(source, module_name="mymod")
    assert any(n.node_id == "mymod.Empty" and n.kind == "class" for n in nodes)
