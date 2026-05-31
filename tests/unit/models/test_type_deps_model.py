"""Unit tests for the Phase 2 TypeDep additive fields (plan 02-06 Task 1).

Phase 2 adds two additive, default-bearing fields to TypeDep:
- ``resolved: bool = True`` — pyright reportMissingImports oracle result
- ``source_line: int = 0`` — 1-based source line of the import / annotation

These defaults keep Phase 1 forward-ref usage (CodeContent.type_deps) and the
existing extra="forbid" contract intact (test_primitives_extra_forbid.py still
passes).

Traces: SCH-02, AST-03, DET-03.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lib_code_parser.models.primitives.type_deps import TypeDep


def test_minimal_construction_uses_defaults() -> None:
    """TypeDep with only the 2 required fields gets Phase 1 + Phase 2 defaults."""
    t = TypeDep(source="m", target="os.path")
    assert t.kind == "uses"
    assert t.resolved is True
    assert t.source_line == 0


def test_full_construction_with_phase2_fields() -> None:
    """All Phase 2 fields are settable explicitly."""
    t = TypeDep(
        source="m",
        target="os.path",
        kind="imports",
        resolved=False,
        source_line=5,
    )
    assert t.kind == "imports"
    assert t.resolved is False
    assert t.source_line == 5


def test_extra_field_rejected() -> None:
    """extra="forbid" remains in force after the additive Phase 2 fields."""
    with pytest.raises(ValidationError):
        TypeDep(source="m", target="os", extra_field=1)


def test_model_dump_json_includes_phase2_keys() -> None:
    """Serialized JSON carries both new keys."""
    payload = TypeDep(source="m", target="os").model_dump_json()
    assert '"resolved"' in payload
    assert '"source_line"' in payload
