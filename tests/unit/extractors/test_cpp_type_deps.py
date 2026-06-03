"""Unit tests for lib_code_parser.extractors.primitives.cpp_type_deps.extract.

Covers #include import deps (regex on raw_content), member-type deps from
FIELD_DECL cursors, missing-header tolerance (warn-not-error, LNG-05), and
DET-04 sort by (source, target, kind, source_line). No pyright/adapter path.
"""

from __future__ import annotations

import pathlib

import pytest

from lib_code_parser.extractors.primitives.cpp_type_deps import extract
from lib_code_parser.models.infrastructure.config import ParserConfig
from tests.conftest import build_cpp_cav


@pytest.fixture
def config() -> ParserConfig:
    return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _read_fixture(name: str) -> tuple[str, str]:
    path = f"tests/fixtures/cpp/{name}"
    src = pathlib.Path(path).read_text(encoding="utf-8")
    return src, name


def test_payload_assert_rejects_non_tu(config) -> None:
    from lib_code_parser.models.infrastructure.cav import CAV

    bad = CAV(language="cpp", path="x.cpp", payload=object())
    with pytest.raises(AssertionError):
        extract(bad, config)


def test_include_import_deps(config) -> None:
    src, name = _read_fixture("includes.cpp")
    cav = build_cpp_cav(src, name)
    deps = extract(cav, config)
    import_targets = {d.target for d in deps if d.kind == "imports"}
    assert {"local_a.h", "local_b.h", "vector"} <= import_targets


def test_missing_header_still_yields_import_no_raise(config) -> None:
    src, name = _read_fixture("missing_include.cpp")
    cav = build_cpp_cav(src, name)
    # Must NOT raise on the unresolved header (LNG-05 warn-not-error).
    deps = extract(cav, config)
    import_targets = {d.target for d in deps if d.kind == "imports"}
    assert "missing_header.h" in import_targets


def test_member_type_deps(config) -> None:
    src, name = _read_fixture("relations.cpp")
    cav = build_cpp_cav(src, name)
    deps = extract(cav, config)
    # value/pointer/reference members of a known class -> a member type dep.
    member_targets = {d.target for d in deps if d.kind != "imports"}
    assert "Point" in member_targets or "Shape" in member_targets


def test_sorted_by_det04_key(config) -> None:
    src, name = _read_fixture("relations.cpp")
    cav = build_cpp_cav(src, name)
    deps = extract(cav, config)
    keys = [(d.source, d.target, d.kind, d.source_line) for d in deps]
    assert keys == sorted(keys)


def test_no_pyright_adapter_in_source() -> None:
    s = pathlib.Path("lib_code_parser/extractors/primitives/cpp_type_deps.py").read_text(
        encoding="utf-8"
    )
    assert "pyright" not in s.lower()
    assert "adapter" not in s.lower()
