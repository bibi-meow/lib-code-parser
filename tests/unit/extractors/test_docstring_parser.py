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


class TestWR07RaisesClassification:
    """WR-07: only `raises` clauses that read like conditional/precondition
    failures (contain 'if'/precondition keywords) become preconditions;
    unconditional postcondition-failure modes (e.g. network errors) do not."""

    def test_conditional_raise_is_precondition(self) -> None:
        doc = "Do thing.\n\nRaises:\n    ValueError: if x is negative\n"
        _, pre, _ = parse(doc)
        assert any("ValueError" in c.text for c in pre)
        assert all(c.kind == "precondition" for c in pre)

    def test_unconditional_raise_not_precondition(self) -> None:
        # A bare RuntimeError with no conditional cue is NOT a precondition.
        doc = "Do thing.\n\nRaises:\n    RuntimeError: the connection dropped\n"
        _, pre, _ = parse(doc)
        assert not any("RuntimeError" in c.text for c in pre)


class TestIN01PreconditionWordBoundary:
    """IN-01: precondition keyword matching uses word boundaries so benign
    prose substrings don't trigger false-positive preconditions."""

    def test_substring_not_none_does_not_false_match(self) -> None:
        # "cannot none-the-less" contains the substring "not none" but is NOT a
        # 'not none' precondition; word-boundary matching must reject it.
        doc = "Do thing.\n\nArgs:\n    x (int): this cannot none-the-less be passed\n"
        _, pre, _ = parse(doc)
        assert not any("x:" in c.text for c in pre)

    def test_genuine_not_none_still_matches(self) -> None:
        doc = "Do thing.\n\nArgs:\n    x (int): must be not none for the call\n"
        _, pre, _ = parse(doc)
        assert any("x:" in c.text for c in pre)


class TestWR04GoogleMultiLineParam:
    """WR-04: Google param descriptions spanning multiple (indented)
    continuation lines must be captured in full, not truncated to the first
    line. NumPy already accumulates continuations; Google must match."""

    def test_continuation_lines_joined_into_description(self) -> None:
        doc = (
            "Summary.\n\nArgs:\n    x (int): This is a long\n        description spanning lines.\n"
        )
        sections, _, _ = parse(doc)
        params = [s for s in sections if s.kind == "params"]
        assert len(params) == 1
        assert params[0].name == "x"
        assert params[0].text == "This is a long description spanning lines."


class TestCR05LeadingBlankSummary:
    """CR-05: a docstring whose prose begins after a leading blank line must
    still produce a summary section in every dialect (previously dropped)."""

    def test_google_leading_blank_keeps_summary(self) -> None:
        doc = "\nThis function does X.\n\nArgs:\n    x: value\n"
        sections, _, _ = parse(doc)
        summaries = [s for s in sections if s.kind == "summary"]
        assert len(summaries) == 1
        assert summaries[0].text == "This function does X."

    def test_numpy_leading_blank_keeps_summary(self) -> None:
        doc = "\nThis function does X.\n\nParameters\n----------\nx : int\n    value\n"
        sections, _, _ = parse(doc)
        summaries = [s for s in sections if s.kind == "summary"]
        assert len(summaries) == 1
        assert summaries[0].text == "This function does X."


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
