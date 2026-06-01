"""SPC-01 stdlib-only docstring dialect parser (Google / NumPy / Sphinx).

A small state machine over ``docstring.splitlines()`` that auto-detects the
dialect (byte-stable order Sphinx → NumPy → Google → none) and reduces all three
to ONE normalized ``DocstringSection`` shape, so the SAME function documented in
any of the three styles yields byte-identical output (the strongest SPC-01
determinism proof). Pre/postconditions are derived by a FIXED keyword/regex set
(no NLP, no scoring) and marked ``source_kind="docstring"``.

D-09: NO external library (``docstring_parser`` etc.). Pure stdlib (``re``).

DET-04: output ordering is deterministic — sections follow the canonical
``summary → params (source order) → returns → raises`` layout, identical across
dialects; the heuristic is a fixed keyword set, so the same docstring yields the
same conditions every run.

Implements: SPC-01
Traces: SPC-01, US-01, US-22, D-09.
"""

from __future__ import annotations

import re
from typing import Literal

from lib_code_parser.models.evaluations.spec import DocstringSection, SpecCondition

__all__ = ["parse"]

Dialect = Literal["sphinx", "numpy", "google", "none"]

# ---------------------------------------------------------------------------
# Detection signals (anchored, linear regexes — no catastrophic backtracking).
# ---------------------------------------------------------------------------
_SPHINX_FIELD_RE = re.compile(r"^\s*:(param|type|returns?|raises?|rtype)\b")
_NUMPY_UNDERLINE_RE = re.compile(r"^-{3,}\s*$")
_GOOGLE_HEADER_RE = re.compile(
    r"^(Args|Arguments|Returns|Raises|Yields|Attributes|Note|Examples?):\s*$"
)
_NUMPY_HEADER_RE = re.compile(
    r"^\s*(Parameters|Returns|Raises|Yields|Attributes|Other Parameters)\s*$"
)

# Header → normalized section kind. Param-like headers explode one-per-entry.
_HEADER_KIND: dict[str, str] = {
    "args": "params",
    "arguments": "params",
    "parameters": "params",
    "returns": "returns",
    "raises": "raises",
}

# Fixed precondition keyword set (RESEARCH §pre/post). IN-01: word-boundary
# matching (not raw substring) so benign prose like "cannot none-the-less" or
# "note: none of" does not false-match "not none". The numeric cues (> 0) keep
# their own anchored alternation since \b does not apply cleanly to symbols.
_PRECONDITION_KW_RE = re.compile(
    r"(\bmust be\b|\bnon-negative\b|>\s*0\b|\bnot none\b|\brequired\b)",
    re.IGNORECASE,
)


def _has_precondition_keyword(text: str) -> bool:
    """True iff the text carries a fixed precondition cue (word-boundary)."""
    return _PRECONDITION_KW_RE.search(text) is not None


def _detect_dialect(lines: list[str]) -> Dialect:
    """Detect dialect (byte-stable first-match order Sphinx → NumPy → Google)."""
    # 1. Sphinx — any reST field line.
    for line in lines:
        if _SPHINX_FIELD_RE.match(line):
            return "sphinx"
    # 2. NumPy — a known header immediately followed by a dashed underline.
    for i, line in enumerate(lines[:-1]):
        if _NUMPY_HEADER_RE.match(line) and _NUMPY_UNDERLINE_RE.match(lines[i + 1]):
            return "numpy"
    # 3. Google — a known header line ending in ``:``.
    for line in lines:
        if _GOOGLE_HEADER_RE.match(line):
            return "google"
    return "none"


def _summary(lines: list[str]) -> str:
    """Leading prose before the first blank line / section header.

    CR-05: skip LEADING blank lines first (a triple-quoted docstring whose
    text starts on the second line begins with an empty ``splitlines()``
    entry). Stop at the first blank line AFTER prose has started, or at a
    section header. Previously the very first blank line broke immediately,
    dropping the summary for every dialect.
    """
    collected: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if started:
                break
            continue  # skip leading blank lines
        if _GOOGLE_HEADER_RE.match(stripped) or _NUMPY_HEADER_RE.match(line):
            break
        if _SPHINX_FIELD_RE.match(line):
            break
        started = True
        collected.append(stripped)
    return " ".join(collected).strip()


def _section(kind: str, name: str = "", type_ref: str = "", text: str = "") -> DocstringSection:
    return DocstringSection(kind=kind, name=name, type_ref=type_ref, text=text)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Google parser.
# ---------------------------------------------------------------------------
_GOOGLE_PARAM_RE = re.compile(r"^(\w+)\s*(?:\(([^)]*)\))?\s*:\s*(.*)$")


def _parse_google(lines: list[str]) -> list[DocstringSection]:
    sections: list[DocstringSection] = []
    summary = _summary(lines)
    if summary:
        sections.append(_section("summary", text=summary))

    i = 0
    n = len(lines)
    while i < n:
        header = _GOOGLE_HEADER_RE.match(lines[i].strip())
        if not header:
            i += 1
            continue
        kind = _HEADER_KIND.get(header.group(1).lower())
        i += 1
        # Collect the indented body block until dedent / next header / blank-gap.
        body: list[str] = []
        while i < n:
            line = lines[i]
            if not line.strip():
                # blank line — peek: if next is a header, stop; else keep going.
                i += 1
                if i < n and _GOOGLE_HEADER_RE.match(lines[i].strip()):
                    break
                continue
            if _GOOGLE_HEADER_RE.match(line.strip()) and not line.startswith((" ", "\t")):
                break
            body.append(line)
            i += 1
        if kind == "params":
            for entry_name, entry_type, entry_text in _split_google_params(body):
                sections.append(
                    _section("params", name=entry_name, type_ref=entry_type, text=entry_text)
                )
        elif kind in ("returns", "raises"):
            sections.append(_parse_returns_raises_google(kind, body))
    return sections


def _split_google_params(body: list[str]) -> list[tuple[str, str, str]]:
    """Split a Google Args block into (name, type, desc) — one per parameter.

    WR-04: a parameter description may span multiple indented continuation
    lines; accumulate them into the current entry's text (joined with a single
    space) until the next ``name (type): ...`` header. Previously only the
    first line was kept, dropping multi-line descriptions.
    """
    entries: list[tuple[str, str, str]] = []
    cur_name: str | None = None
    cur_type = ""
    cur_desc: list[str] = []

    def _flush() -> None:
        if cur_name is not None:
            entries.append((cur_name, cur_type, " ".join(cur_desc).strip()))

    for line in body:
        m = _GOOGLE_PARAM_RE.match(line.strip())
        if m:
            _flush()
            cur_name = m.group(1)
            cur_type = (m.group(2) or "").strip()
            cur_desc = [m.group(3).strip()] if m.group(3).strip() else []
        elif cur_name is not None and line.strip():
            # Continuation line of the current parameter's description.
            cur_desc.append(line.strip())
    _flush()
    return entries


def _parse_returns_raises_google(kind: str, body: list[str]) -> DocstringSection:
    text = " ".join(line.strip() for line in body if line.strip()).strip()
    type_ref = ""
    name = ""
    if kind == "returns":
        # "bool: True if ..." → type_ref="bool", text="True if ..."
        m = re.match(r"^(\w[\w\[\], .]*?):\s*(.*)$", text)
        if m:
            type_ref, text = m.group(1).strip(), m.group(2).strip()
    else:  # raises
        # "ValueError: if ..." → name="ValueError", text="if ..."
        m = re.match(r"^(\w[\w.]*?):\s*(.*)$", text)
        if m:
            name, text = m.group(1).strip(), m.group(2).strip()
    return _section(kind, name=name, type_ref=type_ref, text=text)


# ---------------------------------------------------------------------------
# NumPy parser.
# ---------------------------------------------------------------------------
def _parse_numpy(lines: list[str]) -> list[DocstringSection]:
    sections: list[DocstringSection] = []
    summary = _summary(lines)
    if summary:
        sections.append(_section("summary", text=summary))

    i = 0
    n = len(lines)
    while i < n:
        header = _NUMPY_HEADER_RE.match(lines[i])
        if not (header and i + 1 < n and _NUMPY_UNDERLINE_RE.match(lines[i + 1])):
            i += 1
            continue
        kind = _HEADER_KIND.get(header.group(1).lower())
        i += 2  # skip header + underline
        body: list[str] = []
        while i < n:
            line = lines[i]
            is_next_header = (
                i + 1 < n
                and _NUMPY_HEADER_RE.match(line)
                and _NUMPY_UNDERLINE_RE.match(lines[i + 1])
            )
            if is_next_header:
                break
            body.append(line)
            i += 1
        if kind == "params":
            for entry_name, entry_type, entry_text in _split_numpy_params(body):
                sections.append(
                    _section("params", name=entry_name, type_ref=entry_type, text=entry_text)
                )
        elif kind in ("returns", "raises"):
            sections.append(_parse_returns_raises_numpy(kind, body))
    return sections


_NUMPY_NAME_TYPE_RE = re.compile(r"^(\w+)\s*:\s*(.*)$")


def _split_numpy_params(body: list[str]) -> list[tuple[str, str, str]]:
    """Split a NumPy Parameters block: ``name : type`` then indented desc."""
    entries: list[tuple[str, str, str]] = []
    i = 0
    n = len(body)
    while i < n:
        line = body[i]
        m = _NUMPY_NAME_TYPE_RE.match(line.strip())
        if m and not line.startswith((" ", "\t")):
            name, type_ref = m.group(1), m.group(2).strip()
            i += 1
            desc_lines: list[str] = []
            while i < n and (body[i].startswith((" ", "\t")) or not body[i].strip()):
                if body[i].strip():
                    desc_lines.append(body[i].strip())
                i += 1
            entries.append((name, type_ref, " ".join(desc_lines).strip()))
        else:
            i += 1
    return entries


def _parse_returns_raises_numpy(kind: str, body: list[str]) -> DocstringSection:
    # NumPy returns/raises: first non-blank line = type/exception, rest = desc.
    meaningful = [line for line in body if line.strip()]
    type_or_name = meaningful[0].strip() if meaningful else ""
    text = " ".join(line.strip() for line in meaningful[1:]).strip()
    if kind == "returns":
        return _section("returns", type_ref=type_or_name, text=text)
    return _section("raises", name=type_or_name, text=text)


# ---------------------------------------------------------------------------
# Sphinx (reST) parser.
# ---------------------------------------------------------------------------
_SPHINX_PARAM_RE = re.compile(r"^\s*:param\s+(\w+):\s*(.*)$")
_SPHINX_TYPE_RE = re.compile(r"^\s*:type\s+(\w+):\s*(.*)$")
_SPHINX_RETURNS_RE = re.compile(r"^\s*:returns?:\s*(.*)$")
_SPHINX_RTYPE_RE = re.compile(r"^\s*:rtype:\s*(.*)$")
_SPHINX_RAISES_RE = re.compile(r"^\s*:raises?\s+(\w[\w.]*):\s*(.*)$")


def _parse_sphinx(lines: list[str]) -> list[DocstringSection]:
    sections: list[DocstringSection] = []
    summary = _summary(lines)
    if summary:
        sections.append(_section("summary", text=summary))

    param_order: list[str] = []
    param_text: dict[str, str] = {}
    param_type: dict[str, str] = {}
    returns_text = ""
    returns_type = ""
    raises: list[tuple[str, str]] = []

    for line in lines:
        mp = _SPHINX_PARAM_RE.match(line)
        if mp:
            name = mp.group(1)
            if name not in param_text:
                param_order.append(name)
            param_text[name] = mp.group(2).strip()
            continue
        mt = _SPHINX_TYPE_RE.match(line)
        if mt:
            param_type[mt.group(1)] = mt.group(2).strip()
            continue
        mret = _SPHINX_RETURNS_RE.match(line)
        if mret:
            returns_text = mret.group(1).strip()
            continue
        mrt = _SPHINX_RTYPE_RE.match(line)
        if mrt:
            returns_type = mrt.group(1).strip()
            continue
        mr = _SPHINX_RAISES_RE.match(line)
        if mr:
            raises.append((mr.group(1), mr.group(2).strip()))

    for name in param_order:
        sections.append(
            _section("params", name=name, type_ref=param_type.get(name, ""), text=param_text[name])
        )
    if returns_text or returns_type:
        sections.append(_section("returns", type_ref=returns_type, text=returns_text))
    for exc, desc in raises:
        sections.append(_section("raises", name=exc, text=desc))
    return sections


# ---------------------------------------------------------------------------
# Pre/post derivation (fixed-keyword heuristic, byte-stable).
# ---------------------------------------------------------------------------
def _derive_conditions(
    sections: list[DocstringSection],
) -> tuple[list[SpecCondition], list[SpecCondition]]:
    pre: list[SpecCondition] = []
    post: list[SpecCondition] = []
    for sec in sections:
        if sec.kind == "params":
            if _has_precondition_keyword(sec.text):
                pre.append(
                    SpecCondition(
                        kind="precondition",
                        text=f"{sec.name}: {sec.text}".strip(": ").strip(),
                        source_kind="docstring",
                    )
                )
        elif sec.kind == "raises":
            # WR-07: only CONDITIONAL raises (those reading like a
            # precondition-failure mode — "if ...", or a fixed precondition
            # keyword) become preconditions. Unconditional postcondition-failure
            # modes (e.g. "the connection dropped") are NOT preconditions: the
            # caller cannot prevent them by checking an input.
            lowered = sec.text.lower()
            if "if " in lowered or _has_precondition_keyword(sec.text):
                label = f"{sec.name}: {sec.text}".strip(": ").strip()
                pre.append(SpecCondition(kind="precondition", text=label, source_kind="docstring"))
        elif sec.kind == "returns" and (sec.text or sec.type_ref):
            label = f"{sec.type_ref}: {sec.text}".strip(": ").strip()
            post.append(SpecCondition(kind="postcondition", text=label, source_kind="docstring"))
    return pre, post


def parse(
    docstring: str,
) -> tuple[list[DocstringSection], list[SpecCondition], list[SpecCondition]]:
    """Parse a docstring → (sections, preconditions, postconditions).

    The same content in Google/NumPy/Sphinx yields byte-identical sections.
    Empty / unstructured docstrings produce a single ``summary`` section (or
    nothing when blank). Pre/post are a fixed-keyword heuristic, ``source_kind
    ="docstring"``.
    """
    if not docstring or not docstring.strip():
        return [], [], []

    lines = docstring.splitlines()
    dialect = _detect_dialect(lines)

    if dialect == "sphinx":
        sections = _parse_sphinx(lines)
    elif dialect == "numpy":
        sections = _parse_numpy(lines)
    elif dialect == "google":
        sections = _parse_google(lines)
    else:
        summary = _summary(lines) or docstring.strip()
        sections = [_section("summary", text=summary)] if summary else []

    pre, post = _derive_conditions(sections)
    return sections, pre, post
