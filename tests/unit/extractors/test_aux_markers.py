"""Unit tests for the SPC-04 auxiliary contract marker detector (_markers.py).

Detection-only (D-10): icontract/deal are NEVER imported by the library. A
marker is classified only when its name resolves through a real icontract/deal
import OR is the ``pkg.attr`` attribute form (import-provenance, T-03-13). PEP-316
``pre:``/``post:`` docstring keywords are regex-detected. The condition text is
``ast.unparse`` of the lambda only (T-03-14 — no execution).

Traces: SPC-04, D-10, US-01, US-22.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations import _markers
from tests.unit.extractors.fixtures.aux_marker_samples import (
    DEAL_ATTR_SOURCE,
    DEAL_FROM_SOURCE,
    DECOY_PRE_NO_IMPORT_SOURCE,
    DECOY_REQUIRE_SOURCE,
    ICONTRACT_ATTR_SOURCE,
    ICONTRACT_FROM_SOURCE,
    PEP316_SOURCE,
)


def _module(source: str) -> ast.Module:
    return ast.parse(source)


def _classdef(module: ast.Module, name: str) -> ast.ClassDef:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"class {name} not found")


def _method(cls: ast.ClassDef, name: str) -> ast.FunctionDef:
    for item in cls.body:
        if isinstance(item, ast.FunctionDef) and item.name == name:
            return item
    raise AssertionError(f"method {name} not found")


# ---------------------------------------------------------------------------
# Provenance map.
# ---------------------------------------------------------------------------
class TestResolveAliases:
    def test_from_icontract_import(self) -> None:
        aliases = _markers.resolve_marker_aliases(_module(ICONTRACT_FROM_SOURCE))
        assert aliases["require"] == ("icontract", "require")
        assert aliases["invariant"] == ("icontract", "invariant")

    def test_from_deal_import(self) -> None:
        aliases = _markers.resolve_marker_aliases(_module(DEAL_FROM_SOURCE))
        assert aliases["pre"] == ("deal", "pre")
        assert aliases["post"] == ("deal", "post")

    def test_import_pkg_form_yields_no_bare_aliases(self) -> None:
        # `import icontract` makes only the attribute form work, no bare names.
        aliases = _markers.resolve_marker_aliases(_module(ICONTRACT_ATTR_SOURCE))
        assert aliases == {}


# ---------------------------------------------------------------------------
# icontract.
# ---------------------------------------------------------------------------
class TestIcontract:
    def test_attribute_form_require_ensure(self) -> None:
        mod = _module(ICONTRACT_ATTR_SOURCE)
        aliases = _markers.resolve_marker_aliases(mod)
        method = _method(_classdef(mod, "Account"), "deposit")
        conds = _markers.detect_decorator_markers(method.decorator_list, aliases)
        by_sk = {c.source_kind: c for c in conds}
        assert by_sk["icontract_require"].kind == "precondition"
        assert by_sk["icontract_ensure"].kind == "postcondition"
        assert "amount > 0" in by_sk["icontract_require"].text

    def test_class_invariant_attribute_form(self) -> None:
        mod = _module(ICONTRACT_ATTR_SOURCE)
        aliases = _markers.resolve_marker_aliases(mod)
        cls = _classdef(mod, "Account")
        conds = _markers.detect_decorator_markers(cls.decorator_list, aliases)
        assert conds[0].source_kind == "icontract_invariant"
        assert conds[0].kind == "invariant"

    def test_bare_name_via_from_import(self) -> None:
        mod = _module(ICONTRACT_FROM_SOURCE)
        aliases = _markers.resolve_marker_aliases(mod)
        cls = _classdef(mod, "Widget")
        cls_conds = _markers.detect_decorator_markers(cls.decorator_list, aliases)
        assert cls_conds[0].source_kind == "icontract_invariant"
        method = _method(cls, "grow")
        m_conds = _markers.detect_decorator_markers(method.decorator_list, aliases)
        assert m_conds[0].source_kind == "icontract_require"


# ---------------------------------------------------------------------------
# deal.
# ---------------------------------------------------------------------------
class TestDeal:
    def test_attribute_form_pre_post_ensure(self) -> None:
        mod = _module(DEAL_ATTR_SOURCE)
        aliases = _markers.resolve_marker_aliases(mod)
        method = _method(_classdef(mod, "Buffer"), "push")
        conds = _markers.detect_decorator_markers(method.decorator_list, aliases)
        sks = {c.source_kind for c in conds}
        assert sks == {"deal_pre", "deal_post", "deal_ensure"}

    def test_class_inv_attribute_form(self) -> None:
        mod = _module(DEAL_ATTR_SOURCE)
        aliases = _markers.resolve_marker_aliases(mod)
        cls = _classdef(mod, "Buffer")
        conds = _markers.detect_decorator_markers(cls.decorator_list, aliases)
        assert conds[0].source_kind == "deal_inv"
        assert conds[0].kind == "invariant"

    def test_bare_name_via_from_import(self) -> None:
        mod = _module(DEAL_FROM_SOURCE)
        aliases = _markers.resolve_marker_aliases(mod)
        method = _method(_classdef(mod, "Calc"), "half")
        conds = _markers.detect_decorator_markers(method.decorator_list, aliases)
        sks = {c.source_kind for c in conds}
        assert sks == {"deal_pre", "deal_post"}


# ---------------------------------------------------------------------------
# PEP-316 docstring keywords.
# ---------------------------------------------------------------------------
class TestPep316:
    def test_pre_post_keywords(self) -> None:
        mod = _module(PEP316_SOURCE)
        method = _method(_classdef(mod, "Stack"), "pop")
        docstring = ast.get_docstring(method) or ""
        conds = _markers.detect_pep316_markers(docstring)
        by_sk = {c.source_kind: c for c in conds}
        assert by_sk["pep316_pre"].kind == "precondition"
        assert "not self.is_empty()" in by_sk["pep316_pre"].text
        assert by_sk["pep316_post"].kind == "postcondition"
        # post[self]: form is supported.
        assert "len(self)" in by_sk["pep316_post"].text

    def test_no_keywords_empty(self) -> None:
        assert _markers.detect_pep316_markers("Just a normal docstring.") == []

    def test_empty_docstring(self) -> None:
        assert _markers.detect_pep316_markers("") == []


# ---------------------------------------------------------------------------
# False-positive defense (T-03-13).
# ---------------------------------------------------------------------------
class TestFalsePositiveDefense:
    def test_decoy_require_no_import_not_classified(self) -> None:
        mod = _module(DECOY_REQUIRE_SOURCE)
        aliases = _markers.resolve_marker_aliases(mod)
        assert aliases == {}
        method = _method(_classdef(mod, "Service"), "run")
        conds = _markers.detect_decorator_markers(method.decorator_list, aliases)
        assert conds == []

    def test_decoy_bare_pre_no_import_not_classified(self) -> None:
        mod = _module(DECOY_PRE_NO_IMPORT_SOURCE)
        aliases = _markers.resolve_marker_aliases(mod)
        assert aliases == {}
        method = _method(_classdef(mod, "Thing"), "go")
        conds = _markers.detect_decorator_markers(method.decorator_list, aliases)
        assert conds == []


# ---------------------------------------------------------------------------
# Determinism (DET-04 building block).
# ---------------------------------------------------------------------------
class TestDeterminism:
    def test_repeated_runs_byte_identical(self) -> None:
        mod = _module(DEAL_ATTR_SOURCE)
        aliases = _markers.resolve_marker_aliases(mod)
        method = _method(_classdef(mod, "Buffer"), "push")
        first = [
            c.model_dump()
            for c in _markers.detect_decorator_markers(method.decorator_list, aliases)
        ]
        second = [
            c.model_dump()
            for c in _markers.detect_decorator_markers(method.decorator_list, aliases)
        ]
        assert first == second
