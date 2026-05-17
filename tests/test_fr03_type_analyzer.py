"""Tests for LIB-FR-03: TypeDep analysis with pyright/ast fallback."""

from lib_code_parser.type_analyzer import analyze_type_deps


def test_return_type_dep_extracted():
    source = "def process(data: MyData) -> ResultType:\n    pass\n"
    deps = analyze_type_deps(source, path="mymod.py", use_pyright=False, module_name="mymod")
    targets = [d.target for d in deps]
    assert "MyData" in targets
    assert "ResultType" in targets


def test_no_annotations_no_deps():
    source = "def foo(x, y):\n    return x + y\n"
    deps = analyze_type_deps(source, path="mymod.py", use_pyright=False, module_name="mymod")
    assert deps == []


def test_builtin_types_excluded():
    """str, int, float, bool, None, list, dict, etc. are not reported as deps."""
    source = "def foo(x: str, y: int) -> bool:\n    pass\n"
    deps = analyze_type_deps(source, path="mymod.py", use_pyright=False, module_name="mymod")
    targets = [d.target for d in deps]
    assert "str" not in targets
    assert "int" not in targets
    assert "bool" not in targets


def test_pyright_true_no_exception_when_unavailable():
    """When use_pyright=True but pyright is unavailable, fall back gracefully."""
    source = "def foo(x: MyData) -> None:\n    pass\n"
    # Should not raise even if pyright binary is absent
    deps = analyze_type_deps(
        source, path="nonexistent_module.py", use_pyright=True, module_name="mymod"
    )
    assert isinstance(deps, list)


def test_type_dep_source_id():
    source = "def process(data: MyData) -> ResultType:\n    pass\n"
    deps = analyze_type_deps(source, path="mymod.py", use_pyright=False, module_name="mymod")
    for d in deps:
        assert d.source == "mymod.process"
        assert d.dep_type == "typing"


def test_class_attribute_type_dep():
    source = "class Processor:\n    def run(self, data: InputData) -> OutputData:\n        pass\n"
    deps = analyze_type_deps(source, path="mymod.py", use_pyright=False, module_name="mymod")
    targets = [d.target for d in deps]
    assert "InputData" in targets
    assert "OutputData" in targets
