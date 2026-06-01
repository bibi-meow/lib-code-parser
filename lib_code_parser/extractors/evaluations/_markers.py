"""SPC-04 auxiliary contract marker detector (icontract / deal / PEP-316).

DETECTION-ONLY (D-10): icontract and deal are NEVER imported or executed by the
library. Markers are recognized by their AST decorator shape with the Phase 2
``contracts.py`` import-provenance restriction (T-03-13): a decorator is
classified only when its local name resolves through a real ``icontract``/``deal``
import OR is the ``pkg.attr`` attribute form. A user's own ``def require()`` /
bare ``@pre`` with no marker-library import is therefore NOT flagged.

The condition ``text`` is ``ast.unparse`` of the decorator's first argument
(the lambda) only — the lambda is never evaluated (T-03-14). PEP-316 ``pre:`` /
``post:`` docstring keywords are detected via two anchored regexes.

The SPC-04 ``source_kind`` values come from ``models/evaluations/spec.py``
(SpecConditionSourceKind); the frozen ``primitives/contracts.py`` SourceKind
Literal is NOT touched (invariant #1, anti-Pitfall 6).

Implements: SPC-04
Traces: SPC-04, D-10, US-01, US-22
"""

from __future__ import annotations

import ast
import re

from lib_code_parser.models.evaluations.spec import SpecCondition, SpecConditionSourceKind

__all__ = [
    "resolve_marker_aliases",
    "detect_decorator_markers",
    "detect_pep316_markers",
]

# Marker table (RESEARCH §Code Examples lines 575-583): (pkg, attr) -> (kind, source_kind).
_MARKER_TABLE: dict[tuple[str, str], tuple[str, SpecConditionSourceKind]] = {
    ("icontract", "require"): ("precondition", "icontract_require"),
    ("icontract", "ensure"): ("postcondition", "icontract_ensure"),
    ("icontract", "invariant"): ("invariant", "icontract_invariant"),
    ("deal", "pre"): ("precondition", "deal_pre"),
    ("deal", "post"): ("postcondition", "deal_post"),
    ("deal", "ensure"): ("postcondition", "deal_ensure"),
    ("deal", "inv"): ("invariant", "deal_inv"),
}

# The marker packages we DETECT (never import — D-10).
_TARGET_PACKAGES = ("icontract", "deal")

# PEP-316 docstring keyword regexes (anchored, linear — no catastrophic backtracking).
# `post[old]:` / `post[self]:` qualified forms are allowed per PEP-316.
_PEP316_PRE_RE = re.compile(r"^\s*pre:\s*(.+)$")
_PEP316_POST_RE = re.compile(r"^\s*post(?:\[\w+\])?:\s*(.+)$")


def resolve_marker_aliases(module: ast.Module) -> dict[str, tuple[str, str]]:
    """Build {local_name: (package, canonical_attr)} from a marker-pkg ImportFrom.

    For a `from <pkg> require` style statement (where <pkg> is a target marker
    package), each imported name maps to its (package, canonical_attr):
        `<pkg>=icontract`, name `require`           -> {"require": ("icontract", "require")}
        `<pkg>=icontract`, name `require` as `req`  -> {"req": ("icontract", "require")}
        `<pkg>=deal`, names `pre`, `post`           -> two entries keyed by local name
        a plain `<pkg>` module import               -> {} (attribute form handled separately)

    Only ImportFrom statements whose root package is a target marker package are
    in scope. Same-name identifiers from other libraries are excluded so they
    are not falsely classified (T-03-13).
    """
    aliases: dict[str, tuple[str, str]] = {}
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            pkg = mod.split(".", 1)[0]
            if pkg in _TARGET_PACKAGES:
                for alias in node.names:
                    local = alias.asname or alias.name
                    aliases[local] = (pkg, alias.name)
    return aliases


def _attribute_provenance(decorator: ast.expr) -> tuple[str, str] | None:
    """Return (package, attr) for a `@pkg.attr(...)` / `@pkg.attr` attribute form.

    The provenance is carried inline by the ``pkg.`` prefix, so no import-alias
    map is needed. Returns None for non-attribute forms or non-target packages.
    """
    target = decorator
    if isinstance(target, ast.Call):
        target = target.func
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
        pkg = target.value.id
        if pkg in _TARGET_PACKAGES:
            return pkg, target.attr
    return None


def _bare_name(decorator: ast.expr) -> str:
    """Return the bare local name for a `@name(...)` / `@name` form, else ''."""
    target = decorator
    if isinstance(target, ast.Call):
        target = target.func
    if isinstance(target, ast.Name):
        return target.id
    return ""


def _condition_text(decorator: ast.expr) -> str:
    """ast.unparse the decorator's first positional arg (the lambda), if present.

    The lambda is unparsed only — never evaluated (T-03-14, D-10).
    """
    if isinstance(decorator, ast.Call) and decorator.args:
        return ast.unparse(decorator.args[0])
    return ""


def _classify(decorator: ast.expr, aliases: dict[str, tuple[str, str]]) -> tuple[str, str] | None:
    """Return (package, canonical_attr) if the decorator is a marker, else None.

    Provenance order: attribute form (`@pkg.attr`) first (inline provenance),
    then bare name resolved through the import-alias map. A bare name with no
    target-library import has no provenance and is rejected (T-03-13).
    """
    attr_prov = _attribute_provenance(decorator)
    if attr_prov is not None:
        return attr_prov
    bare = _bare_name(decorator)
    if bare and bare in aliases:
        return aliases[bare]
    return None


def detect_decorator_markers(
    decorators: list[ast.expr], aliases: dict[str, tuple[str, str]]
) -> list[SpecCondition]:
    """Detect icontract/deal markers on a decorator list (class or function).

    For each decorator whose provenance resolves to a target marker, emit a
    SpecCondition with the table-driven kind/source_kind and the unparsed lambda
    as ``text``. Order follows the decorator-list source order (decorators are
    visited top-to-bottom); the caller applies DET-04 sort-on-exit.
    """
    conditions: list[SpecCondition] = []
    for decorator in decorators:
        prov = _classify(decorator, aliases)
        if prov is None:
            continue
        info = _MARKER_TABLE.get(prov)
        if info is None:
            continue
        kind, source_kind = info
        conditions.append(
            SpecCondition(
                kind=kind,  # type: ignore[arg-type]
                text=_condition_text(decorator),
                source_kind=source_kind,
            )
        )
    return conditions


def detect_pep316_markers(docstring: str) -> list[SpecCondition]:
    """Detect PEP-316 ``pre:`` / ``post[...]:`` docstring keywords.

    Anchored regexes over each docstring line. ``pre:`` → precondition
    (source_kind=pep316_pre); ``post:``/``post[x]:`` → postcondition
    (source_kind=pep316_post). Returns [] for an empty/keyword-free docstring.
    """
    if not docstring:
        return []
    conditions: list[SpecCondition] = []
    for line in docstring.splitlines():
        mpre = _PEP316_PRE_RE.match(line)
        if mpre:
            conditions.append(
                SpecCondition(
                    kind="precondition",
                    text=mpre.group(1).strip(),
                    source_kind="pep316_pre",
                )
            )
            continue
        mpost = _PEP316_POST_RE.match(line)
        if mpost:
            conditions.append(
                SpecCondition(
                    kind="postcondition",
                    text=mpost.group(1).strip(),
                    source_kind="pep316_post",
                )
            )
    return conditions
