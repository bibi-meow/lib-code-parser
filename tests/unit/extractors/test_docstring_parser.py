"""Unit tests for the SPC-01 stdlib-only docstring dialect parser (_docstring).

The strongest determinism proof (RESEARCH §Required Test Fixtures): the SAME
function documented Google/NumPy/Sphinx yields byte-identical normalized
``DocstringSection`` output. Also asserts the fixed-keyword pre/post heuristic
and the byte-stable dialect-detection order (Sphinx → NumPy → Google → none).

Traces: SPC-01, D-09.
"""

from __future__ import annotations

from lib_code_parser.extractors.evaluations._docstring import (
    _detect_dialect,
    parse,
)
from tests.unit.extractors.fixtures.docstring_dialects import (
    GOOGLE_DOCSTRING,
    NUMPY_DOCSTRING,
    SPHINX_DOCSTRING,
)


class TestDialectDetection:
    """Byte-stable detection order: Sphinx → NumPy → Google → none."""

    def test_google_detected(self) -> None:
        assert _detect_dialect(GOOGLE_DOCSTRING.splitlines()) == "google"

    def test_numpy_detected(self) -> None:
        assert _detect_dialect(NUMPY_DOCSTRING.splitlines()) == "numpy"

    def test_sphinx_detected(self) -> None:
        assert _detect_dialect(SPHINX_DOCSTRING.splitlines()) == "sphinx"

    def test_no_section_is_none(self) -> None:
        assert _detect_dialect("Just a one-line summary.".splitlines()) == "none"

    def test_sphinx_wins_over_google_when_both_present(self) -> None:
        # A docstring that has BOTH a Sphinx field and a Google header — Sphinx
        # must win (first in the byte-stable order).
        mixed = "Summary.\n\nArgs:\n    x: a thing.\n\n:returns: the result.\n"
        assert _detect_dialect(mixed.splitlines()) == "sphinx"


class TestThreeDialectEquivalence:
    """The same content in 3 dialects → identical normalized sections."""

    def test_three_dialects_yield_identical_sections(self) -> None:
        g_sections, _, _ = parse(GOOGLE_DOCSTRING)
        n_sections, _, _ = parse(NUMPY_DOCSTRING)
        s_sections, _, _ = parse(SPHINX_DOCSTRING)

        g = [s.model_dump() for s in g_sections]
        n = [s.model_dump() for s in n_sections]
        s = [s.model_dump() for s in s_sections]

        assert g == n, f"Google vs NumPy differ:\n{g}\n{n}"
        assert g == s, f"Google vs Sphinx differ:\n{g}\n{s}"

    def test_sections_contain_summary_two_params_returns_raises(self) -> None:
        sections, _, _ = parse(GOOGLE_DOCSTRING)
        kinds = [s.kind for s in sections]
        assert "summary" in kinds
        assert kinds.count("params") == 2
        assert "returns" in kinds
        assert "raises" in kinds

    def test_param_sections_carry_name_and_type(self) -> None:
        sections, _, _ = parse(NUMPY_DOCSTRING)
        params = {s.name: s for s in sections if s.kind == "params"}
        assert set(params) == {"amount", "method"}
        assert params["amount"].type_ref == "float"
        assert params["method"].type_ref == "str"

    def test_summary_is_leading_prose(self) -> None:
        sections, _, _ = parse(SPHINX_DOCSTRING)
        summaries = [s.text for s in sections if s.kind == "summary"]
        assert summaries == ["Process a payment."]


class TestPrePostHeuristic:
    """Fixed-keyword/regex byte-stable pre/post derivation."""

    def test_precondition_from_must_be_keyword(self) -> None:
        _, pre, _ = parse(GOOGLE_DOCSTRING)
        # "amount ... must be > 0" and "non-negative" are precondition keywords.
        texts = " ".join(c.text for c in pre)
        assert "amount" in texts
        assert all(c.kind == "precondition" for c in pre)
        assert all(c.source_kind == "docstring" for c in pre)

    def test_raises_becomes_documented_precondition(self) -> None:
        _, pre, _ = parse(GOOGLE_DOCSTRING)
        # Raises: → a documented precondition (the ValueError clause).
        assert any("ValueError" in c.text or "non-negative" in c.text for c in pre)

    def test_postcondition_from_returns(self) -> None:
        _, _, post = parse(GOOGLE_DOCSTRING)
        assert post, "Returns: clause should yield a postcondition"
        assert all(c.kind == "postcondition" for c in post)
        assert all(c.source_kind == "docstring" for c in post)

    def test_pre_post_identical_across_dialects(self) -> None:
        gp = [c.model_dump() for c in parse(GOOGLE_DOCSTRING)[1]]
        np_ = [c.model_dump() for c in parse(NUMPY_DOCSTRING)[1]]
        sp = [c.model_dump() for c in parse(SPHINX_DOCSTRING)[1]]
        assert gp == np_ == sp

        gpo = [c.model_dump() for c in parse(GOOGLE_DOCSTRING)[2]]
        npo = [c.model_dump() for c in parse(NUMPY_DOCSTRING)[2]]
        spo = [c.model_dump() for c in parse(SPHINX_DOCSTRING)[2]]
        assert gpo == npo == spo


class TestEdgeCases:
    """Empty / unstructured docstrings."""

    def test_empty_docstring_yields_no_sections(self) -> None:
        sections, pre, post = parse("")
        assert sections == []
        assert pre == []
        assert post == []

    def test_unstructured_docstring_is_summary(self) -> None:
        sections, _, _ = parse("Just a plain description with no sections.")
        assert len(sections) == 1
        assert sections[0].kind == "summary"
        assert sections[0].text == "Just a plain description with no sections."

    def test_byte_stable_repeated_runs(self) -> None:
        first = [s.model_dump() for s in parse(GOOGLE_DOCSTRING)[0]]
        for _ in range(5):
            assert [s.model_dump() for s in parse(GOOGLE_DOCSTRING)[0]] == first
