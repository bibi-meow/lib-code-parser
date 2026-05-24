"""Wave 0 tests for CAV (Common AST View).

Traces: ARC-02, SCH-02, D-04, D-05.
"""

from __future__ import annotations

import ast

import pytest
from pydantic import ValidationError

from lib_code_parser.models.infrastructure.cav import CAV


def test_cav_constructs_with_python_payload() -> None:
    """CAV accepts an ast.Module payload when language='python'."""
    tree = ast.parse("x = 1")
    cav = CAV(language="python", path="foo.py", payload=tree)
    assert cav.language == "python"
    assert cav.path == "foo.py"
    assert isinstance(cav.payload, ast.Module)


def test_cav_rejects_unknown_language() -> None:
    """CAV.language is a Literal['python', 'cpp']; 'java' must be rejected."""
    with pytest.raises(ValidationError):
        CAV(language="java", path="x.java", payload=None)  # type: ignore[arg-type]


def test_cav_is_frozen() -> None:
    """CAV is frozen=True; field mutation must raise ValidationError."""
    cav = CAV(language="python", path="foo.py", payload=None)
    with pytest.raises(ValidationError):
        cav.language = "cpp"  # type: ignore[misc]


def test_cav_rejects_extra_fields() -> None:
    """CAV is extra='forbid'; unknown kwargs must be rejected."""
    with pytest.raises(ValidationError):
        CAV(  # type: ignore[call-arg]
            language="python",
            path="x",
            payload=None,
            extra="surprise",
        )
