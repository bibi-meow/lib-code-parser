"""Unit tests for the SPC-02/SPC-04 class_spec extractor.

SPC-02: one ClassSpec(node_id, definition, members, invariants) per class.
SPC-04: invariants aggregate auxiliary contract markers (icontract.invariant /
deal.inv class decorators + per-method icontract/deal pre/post/ensure + PEP-316
pre:/post:) — detection-only (D-10), import-provenance defended (T-03-13).

members are sorted by name; invariants sorted by (source_kind, line_no, text)
(DET-04) → byte-identical across PYTHONHASHSEED.

Traces: SPC-02, SPC-04, US-01, US-22.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations import class_spec
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from tests.unit.extractors.fixtures.aux_marker_samples import (
    DEAL_ATTR_SOURCE,
    DECOY_REQUIRE_SOURCE,
    ICONTRACT_ATTR_SOURCE,
)

_CONFIG = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")


def _build_cav(source: str, path: str) -> CAV:
    return CAV(language="python", path=path, payload=ast.parse(source))


def _by_name(specs: list) -> dict:
    return {s.node_id.rsplit(".", 1)[-1]: s for s in specs}


SIMPLE_SOURCE = '''
class Greeter:
    """A greeter (Traces: SPC-02)."""

    name: str
    times: int

    def greet(self, who: str) -> str:
        return f"hi {who}"

    def _private(self) -> None:
        pass
'''


class TestSpc02Definition:
    def test_one_classspec_per_class(self) -> None:
        specs = class_spec.extract(_build_cav(SIMPLE_SOURCE, "g.py"), _CONFIG)
        assert len(specs) == 1
        assert specs[0].node_id == "g.Greeter"

    def test_members_include_methods_and_attrs_sorted(self) -> None:
        specs = class_spec.extract(_build_cav(SIMPLE_SOURCE, "g.py"), _CONFIG)
        members = specs[0].members
        assert set(members) >= {"greet", "_private", "name", "times"}
        assert members == sorted(members)

    def test_definition_carries_class_name(self) -> None:
        specs = class_spec.extract(_build_cav(SIMPLE_SOURCE, "g.py"), _CONFIG)
        assert "Greeter" in specs[0].definition

    def test_no_classes_empty(self) -> None:
        specs = class_spec.extract(_build_cav("def f(): pass\n", "m.py"), _CONFIG)
        assert specs == []


class TestSpc04Icontract:
    def test_class_invariant_and_method_markers(self) -> None:
        specs = class_spec.extract(_build_cav(ICONTRACT_ATTR_SOURCE, "a.py"), _CONFIG)
        account = _by_name(specs)["Account"]
        sks = {c.source_kind for c in account.invariants}
        assert "icontract_invariant" in sks  # class decorator
        assert "icontract_require" in sks  # deposit method
        assert "icontract_ensure" in sks


class TestSpc04Deal:
    def test_class_inv_and_method_markers(self) -> None:
        specs = class_spec.extract(_build_cav(DEAL_ATTR_SOURCE, "b.py"), _CONFIG)
        buffer = _by_name(specs)["Buffer"]
        sks = {c.source_kind for c in buffer.invariants}
        assert "deal_inv" in sks
        assert "deal_pre" in sks
        assert "deal_post" in sks


class TestSpc04FalsePositiveDefense:
    def test_decoy_require_not_aggregated(self) -> None:
        specs = class_spec.extract(_build_cav(DECOY_REQUIRE_SOURCE, "d.py"), _CONFIG)
        service = _by_name(specs)["Service"]
        assert service.invariants == []


class TestSpc04Pep316:
    def test_docstring_pre_post(self) -> None:
        source = '''
class Stack:
    """A stack."""

    def pop(self):
        """Pop.

        pre: not self.is_empty()
        post: len(self) >= 0
        """
        return None
'''
        specs = class_spec.extract(_build_cav(source, "s.py"), _CONFIG)
        sks = {c.source_kind for c in specs[0].invariants}
        assert "pep316_pre" in sks
        assert "pep316_post" in sks


class TestDeterminism:
    def test_invariants_sorted_and_stable(self) -> None:
        cav = _build_cav(DEAL_ATTR_SOURCE, "b.py")
        first = class_spec.extract(cav, _CONFIG)
        second = class_spec.extract(cav, _CONFIG)
        assert [s.model_dump() for s in first] == [s.model_dump() for s in second]
        for spec in first:
            keys = [(c.source_kind, c.line_no, c.text) for c in spec.invariants]
            assert keys == sorted(keys)

    def test_classspecs_sorted_by_node_id(self) -> None:
        specs = class_spec.extract(_build_cav(ICONTRACT_ATTR_SOURCE, "a.py"), _CONFIG)
        node_ids = [s.node_id for s in specs]
        assert node_ids == sorted(node_ids)
