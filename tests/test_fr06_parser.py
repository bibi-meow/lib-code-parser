"""Tests for LIB-FR-06: NormalizedArtifact integration via parse_code."""

import pytest

from lib_code_parser.models import NormalizedArtifact, ParserConfig
from lib_code_parser.parser import parse_code


def test_normal_python_file_returns_artifact():
    source = "# Traces: US-01\ndef greet(name: str) -> str:\n    return f'Hello {name}'\n"
    config = ParserConfig()
    artifact = parse_code(source, path="greet.py", config=config)
    assert isinstance(artifact, NormalizedArtifact)
    assert artifact.artifact_type == "code"
    assert artifact.artifact_id.path == "greet.py"


def test_functions_populated():
    source = "def foo():\n    pass\ndef bar():\n    pass\n"
    config = ParserConfig()
    artifact = parse_code(source, path="mod.py", config=config)
    node_ids = [f.node_id for f in artifact.content.functions]
    assert "mod.foo" in node_ids
    assert "mod.bar" in node_ids


def test_call_graph_populated():
    source = "def bar():\n    pass\ndef foo():\n    bar()\n"
    config = ParserConfig()
    artifact = parse_code(source, path="mod.py", config=config)
    edges = artifact.content.call_graph.edges
    assert ("mod.foo", "mod.bar") in edges


def test_trace_tags_in_function_nodes():
    source = "# Traces: US-01\ndef greet(name: str) -> str:\n    return name\n"
    config = ParserConfig()
    artifact = parse_code(source, path="mod.py", config=config)
    all_tags = [t for fn in artifact.content.functions for t in fn.trace_tags]
    # Tags extracted from comments are attached to the artifact
    assert any(t.source_id == "US-01" for t in all_tags)


def test_syntax_error_raises_value_error():
    source = "def foo(\n    pass\n"
    config = ParserConfig()
    with pytest.raises(ValueError):
        parse_code(source, path="bad.py", config=config)


def test_extract_contracts_false():
    source = (
        "class MyModel:\n"
        "    name: str\n"
        "    @field_validator('name')\n"
        "    def validate_name(cls, v):\n"
        "        return v\n"
    )
    config = ParserConfig(
        params={
            "callgraph_tool": "internal",
            "type_tool": "pyright",
            "extract_contracts": False,
            "language": "python",
        }
    )
    artifact = parse_code(source, path="mod.py", config=config)
    for fn in artifact.content.functions:
        assert fn.contracts.preconditions == []


def test_module_name_derived_from_path():
    source = "def foo():\n    pass\n"
    config = ParserConfig()
    artifact = parse_code(source, path="mypackage/mymodule.py", config=config)
    node_ids = [f.node_id for f in artifact.content.functions]
    assert "mymodule.foo" in node_ids


def test_empty_source_returns_empty_content():
    config = ParserConfig()
    artifact = parse_code("", path="empty.py", config=config)
    assert artifact.content.functions == []
    assert artifact.content.call_graph.edges == []
