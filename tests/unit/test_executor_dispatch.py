"""Unit tests for the dispatch-dict-driven CodeParserExecutor (D-03 / D-12).

The executor body walks _dispatch.FRONTENDS / PRIMITIVES — it contains no
primitive-specific extraction logic beyond mapping each primitive output to a
CodeContent slot. These units monkeypatch the dispatch dicts to prove the
walk, the contracts gate, the disabled / C++ early returns, the frontend
selection, and the ContractInfo merger — without invoking real extractors or
pyright.

Traces: ARC-01, ARC-02, D-03, D-12.
"""

from __future__ import annotations

import pytest

from lib_code_parser import _dispatch
from lib_code_parser.executor import CodeParserExecutor
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.callgraph import CallGraph
from lib_code_parser.models.primitives.contracts import (
    ContractEntry,
    ContractInfo,
)
from lib_code_parser.models.primitives.functions import FunctionNode

_PY = b"import os\n"
_PATH = "m.py"


def _config(**kw: object) -> ParserConfig:
    base: dict[str, object] = {
        "artifact_type": "code",
        "executor_lib": "lib_code_parser",
    }
    base.update(kw)
    return ParserConfig(**base)  # type: ignore[arg-type]


def _stub_cav(raw_content: bytes, path: str, config: ParserConfig) -> object:
    """Frontend stub — returns a sentinel object (extractors are mocked too)."""
    return object()


def test_dispatch_walks_all_4_primitives(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _make(name: str, ret: object):
        def _fn(cav: object, config: ParserConfig) -> object:
            calls.append(name)
            return ret

        return _fn

    monkeypatch.setitem(_dispatch.FRONTENDS, "python", _stub_cav)
    monkeypatch.setitem(_dispatch.PRIMITIVES, "functions", _make("functions", []))
    monkeypatch.setitem(_dispatch.PRIMITIVES, "call_graph", _make("call_graph", CallGraph()))
    monkeypatch.setitem(_dispatch.PRIMITIVES, "type_deps", _make("type_deps", []))
    monkeypatch.setitem(_dispatch.PRIMITIVES, "contracts", _make("contracts", {}))

    CodeParserExecutor().execute(_config(), _PY, _PATH)
    assert sorted(calls) == ["call_graph", "contracts", "functions", "type_deps"]


def test_dispatch_skips_contracts_when_extract_contracts_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def _make(name: str, ret: object):
        def _fn(cav: object, config: ParserConfig) -> object:
            calls.append(name)
            return ret

        return _fn

    monkeypatch.setitem(_dispatch.FRONTENDS, "python", _stub_cav)
    monkeypatch.setitem(_dispatch.PRIMITIVES, "functions", _make("functions", []))
    monkeypatch.setitem(_dispatch.PRIMITIVES, "call_graph", _make("call_graph", CallGraph()))
    monkeypatch.setitem(_dispatch.PRIMITIVES, "type_deps", _make("type_deps", []))
    monkeypatch.setitem(_dispatch.PRIMITIVES, "contracts", _make("contracts", {}))

    CodeParserExecutor().execute(_config(extract_contracts=False), _PY, _PATH)
    assert "contracts" not in calls


def test_dispatch_enabled_false_returns_empty_content() -> None:
    art = CodeParserExecutor().execute(_config(enabled=False), _PY, _PATH)
    assert art.content.functions == []
    assert art.content.type_deps == []
    assert art.content.contracts == {}


def test_dispatch_cpp_extension_returns_empty_content() -> None:
    art = CodeParserExecutor().execute(_config(), _PY, "x.cpp")
    assert art.content.functions == []
    assert art.content.type_deps == []


def test_dispatch_frontend_python_called(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[bytes, str]] = []

    def _frontend(raw_content: bytes, path: str, config: ParserConfig) -> object:
        seen.append((raw_content, path))
        return object()

    monkeypatch.setitem(_dispatch.FRONTENDS, "python", _frontend)
    monkeypatch.setitem(_dispatch.PRIMITIVES, "functions", lambda c, cfg: [])
    monkeypatch.setitem(_dispatch.PRIMITIVES, "call_graph", lambda c, cfg: CallGraph())
    monkeypatch.setitem(_dispatch.PRIMITIVES, "type_deps", lambda c, cfg: [])
    monkeypatch.setitem(_dispatch.PRIMITIVES, "contracts", lambda c, cfg: {})

    CodeParserExecutor().execute(_config(), _PY, _PATH)
    assert seen == [(_PY, _PATH)]


def test_dispatch_contract_merger_assigns_to_functionnode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fn = FunctionNode(node_id="m.Foo", kind="class")
    ci = ContractInfo(
        node_id="m.Foo",
        entries=[
            ContractEntry(
                name="val_x",
                source_kind="pydantic_validator",
                kind="precondition",
            )
        ],
    )

    monkeypatch.setitem(_dispatch.FRONTENDS, "python", _stub_cav)
    monkeypatch.setitem(_dispatch.PRIMITIVES, "functions", lambda c, cfg: [fn])
    monkeypatch.setitem(_dispatch.PRIMITIVES, "call_graph", lambda c, cfg: CallGraph())
    monkeypatch.setitem(_dispatch.PRIMITIVES, "type_deps", lambda c, cfg: [])
    monkeypatch.setitem(_dispatch.PRIMITIVES, "contracts", lambda c, cfg: {"m.Foo": ci})

    art = CodeParserExecutor().execute(_config(), _PY, _PATH)
    merged = art.content.functions[0]
    assert merged.contracts.node_id == "m.Foo"
    assert merged.contracts.entries[0].name == "val_x"
