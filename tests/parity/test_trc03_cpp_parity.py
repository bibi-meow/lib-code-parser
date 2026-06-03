"""TRC-03 parity: byte-identical Traces: extraction for Python and C++.

Feeds the SAME ``Traces: REQ-9, US-3`` tag text through:
- the Python docstring path (``functions._extract_trace_tags``), and
- the C++ Doxygen path (``_cpp_cursor.extract_trace_tags``, the verbatim regex
  reused by the cpp extractors),

and asserts the resulting ``TraceTag.refs`` lists are equal — demonstrating the
regex produces identical output for a Python docstring and a C++ Doxygen comment
(D-09). A second case drives the tag through the LIVE cpp extractor path (a
Doxygen comment on a real decl) to prove parity end-to-end, not just at the
shared helper.

Traces: TRC-03, LNG-04.
"""

from __future__ import annotations

from lib_code_parser import _cpp_cursor
from lib_code_parser.extractors.primitives import cpp_functions, functions
from lib_code_parser.models.infrastructure.config import ParserConfig
from tests.conftest import build_cpp_cav

_TAG_TEXT = "Traces: REQ-9, US-3"


def test_helper_byte_identical() -> None:
    """The Python and C++ trace-tag helpers yield identical TraceTag.refs."""
    py_tags = functions._extract_trace_tags(_TAG_TEXT)
    cpp_tags = _cpp_cursor.extract_trace_tags(_TAG_TEXT)
    assert [t.refs for t in py_tags] == [t.refs for t in cpp_tags]
    assert [t.refs for t in cpp_tags] == [["REQ-9", "US-3"]]


def test_regex_literal_byte_identical() -> None:
    """The compiled regex pattern is the SAME literal (D-09 byte-identity)."""
    assert functions._TRACE_TAGS_RE.pattern == _cpp_cursor._TRACE_TAGS_RE.pattern


def test_live_cpp_path_matches_python() -> None:
    """End-to-end: a C++ Doxygen comment carrying the tag extracts the same refs.

    The reference is the Python docstring path; the C++ side runs the real
    cpp_functions extractor over a decl whose Doxygen comment carries the same
    ``Traces:`` line.
    """
    py_refs = [t.refs for t in functions._extract_trace_tags(_TAG_TEXT)]

    src = f"/**\n * Compute.\n *\n * {_TAG_TEXT}\n */\nint compute(int x) {{ return x; }}\n"
    cav = build_cpp_cav(src, "c.cpp")
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser", language="cpp")
    nodes = cpp_functions.extract(cav, config)
    compute = next(n for n in nodes if n.node_id == "compute")
    cpp_refs = [t.refs for t in compute.trace_tags]

    assert cpp_refs == py_refs == [["REQ-9", "US-3"]]
