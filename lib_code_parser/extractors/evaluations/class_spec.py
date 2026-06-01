"""SPC-02 class spec + SPC-04 auxiliary marker aggregation.

The physical-side analog of lib-spec-parser's logical class spec: for each
class this emits a ``ClassSpec(node_id, definition, members, invariants)``.

- ``definition`` — a synthesized ``class Name(Base, ...)`` header summary.
- ``members`` — method names + class-level annotated attribute names, sorted.
- ``invariants`` — the aggregated SPC-04 auxiliary contract markers (D-10,
  detection-only): icontract/deal class-decorator invariants + per-method
  pre/post/ensure/require + PEP-316 ``pre:``/``post:`` docstring keywords. These
  are SUPPLEMENTARY to the Phase 2 ``contracts`` primitive (Pydantic/dataclass
  contracts), which the verifier reads from ``CodeContent.contracts`` directly;
  SPC-04 markers carry their own ``source_kind`` so the verifier can weight them.

Walks the CAV's ``ast.Module`` payload once (Pitfall 5 — no re-parse). The
marker provenance map is built once per module; SPC-04 ``source_kind`` values
come from ``models/evaluations/spec.py`` — the frozen ``primitives/contracts.py``
is NOT touched (invariant #1, anti-Pitfall 6).

DET-04: ClassSpec list sorted by ``node_id``; members sorted by name;
invariants sorted by ``(source_kind, line_no, text)`` → byte-identical across
PYTHONHASHSEED.

Implements: SPC-02, SPC-04
Traces: SPC-02, SPC-04, US-01, US-22
"""

from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name
from lib_code_parser.extractors.evaluations import _markers
from lib_code_parser.models.evaluations.spec import ClassSpec, SpecCondition
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]


def _definition(node: ast.ClassDef) -> str:
    """Synthesize a deterministic ``class Name(Base, ...)`` header summary."""
    bases = [ast.unparse(base) for base in node.bases]
    keywords = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in node.keywords if kw.arg]
    parts = bases + keywords
    if parts:
        return f"class {node.name}({', '.join(parts)})"
    return f"class {node.name}"


def _members(node: ast.ClassDef) -> list[str]:
    """Method names + class-level annotated attribute names (sorted, deduped)."""
    names: set[str] = set()
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(item.name)
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            names.add(item.target.id)
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return sorted(names)


def _set_line(cond: SpecCondition, line_no: int) -> SpecCondition:
    """Return a copy of cond with line_no set (SpecCondition is line-agnostic)."""
    return cond.model_copy(update={"line_no": line_no})


def _invariants(node: ast.ClassDef, aliases: dict[str, tuple[str, str]]) -> list[SpecCondition]:
    """Aggregate SPC-04 markers for a class (class decorators + members)."""
    conditions: list[SpecCondition] = []

    # Class-level decorators (icontract.invariant / deal.inv).
    for cond in _markers.detect_decorator_markers(node.decorator_list, aliases):
        conditions.append(_set_line(cond, node.lineno))

    # Per-method decorators + PEP-316 docstrings.
    for item in node.body:
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for cond in _markers.detect_decorator_markers(item.decorator_list, aliases):
            conditions.append(_set_line(cond, item.lineno))
        docstring = ast.get_docstring(item) or ""
        for cond in _markers.detect_pep316_markers(docstring):
            conditions.append(_set_line(cond, item.lineno))

    # DET-04 sort by (source_kind, line_no, text).
    conditions.sort(key=lambda c: (c.source_kind, c.line_no, c.text))
    return conditions


def extract(cav: CAV, config: ParserConfig) -> list[ClassSpec]:
    """SPC-02/04: emit one ClassSpec per top-level class from cav.

    config is accepted for EvaluationFn signature alignment but not consumed.
    """
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"class_spec extractor requires Python CAV (ast.Module payload), got {type(tree).__name__}"
    )
    module_name = get_module_name(cav.path)
    aliases = _markers.resolve_marker_aliases(tree)

    specs: list[ClassSpec] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        specs.append(
            ClassSpec(
                node_id=f"{module_name}.{node.name}",
                definition=_definition(node),
                members=_members(node),
                invariants=_invariants(node, aliases),
            )
        )

    # DET-04 sort-on-exit by node_id → byte-identical across PYTHONHASHSEED.
    specs.sort(key=lambda s: s.node_id)
    return specs
