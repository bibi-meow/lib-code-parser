"""DET-04 per-extractor determinism: cpp diagram output is byte-identical x3.

Runs each cpp diagram extractor (and the full cpp ``execute``) THREE times on the
same fixture bytes + ParserConfig and asserts all three ``model_dump_json()``
outputs are byte-identical. This proves the DET-04 sort-on-exit tail in every cpp
diagram absorbs libclang's nondeterministic cursor-traversal order (RESEARCH
Pitfall 5) so a fresh parse never reorders nodes/edges.

Each run rebuilds the CAV from scratch (a fresh libclang parse), so this exercises
real parse-to-output determinism, not just re-serialization of one model.

NOTE: the full-pipeline 3-fresh-subprocess DET-01 snapshot (separate OS processes,
fresh PYTHONHASHSEED) is Phase 5 scope, not this test; here we prove per-extractor
and single-process full-execute byte-identity.

Traces: DET-04, LNG-04.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lib_code_parser import CodeParserExecutor, ParserConfig
from lib_code_parser.extractors.evaluations import (
    cpp_class_diagram,
    cpp_component_diagram,
    cpp_package_diagram,
    cpp_sequence_diagram,
    cpp_state_diagram,
)
from tests.conftest import build_cpp_cav

_FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "cpp"


def _config() -> ParserConfig:
    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser", language="cpp")


def _runs(extract_fn, fixture_name: str, n: int = 3) -> list[str]:
    """Build a fresh CAV and run the extractor n times; return JSON dumps."""
    src = (_FIXTURES / fixture_name).read_text(encoding="utf-8")
    dumps: list[str] = []
    for _ in range(n):
        cav = build_cpp_cav(src, fixture_name)
        dumps.append(extract_fn(cav, _config()).model_dump_json())
    return dumps


@pytest.mark.parametrize(
    ("extract_fn", "fixture_name"),
    [
        (cpp_class_diagram.extract, "inheritance.cpp"),
        (cpp_class_diagram.extract, "relations.cpp"),
        (cpp_component_diagram.extract, "includes.cpp"),
        (cpp_sequence_diagram.extract, "doxygen_contracts.cpp"),
        (cpp_package_diagram.extract, "namespaces.cpp"),
        (cpp_state_diagram.extract, "not_a_state_machine.cpp"),
    ],
)
def test_per_extractor_byte_identical_three_runs(extract_fn, fixture_name: str) -> None:
    dumps = _runs(extract_fn, fixture_name)
    assert dumps[0] == dumps[1] == dumps[2]


def test_full_cpp_execute_byte_identical_three_runs() -> None:
    """The full cpp pipeline output is byte-identical across 3 fresh executes."""
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    raw = (_FIXTURES / "relations.cpp").read_bytes()
    dumps = [
        CodeParserExecutor().execute(config, raw, "relations.cpp").model_dump_json()
        for _ in range(3)
    ]
    assert dumps[0] == dumps[1] == dumps[2]
