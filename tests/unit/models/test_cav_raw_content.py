"""Wave 0 tests for the additive CAV.raw_content field (Phase 2 plan 02-01).

These tests prove that adding ``raw_content: bytes = b""`` to the CAV model:
  - is additive (Phase 1 3-field construction still works, defaults to b""),
  - carries bytes verbatim when supplied,
  - does not break the D-05 frozen invariant.

Pydantic v2 lax mode coerces ``str`` -> ``bytes`` at field validation, so a
strict "reject str" test is not possible without ``strict=True`` on the field;
the existing CAV model keeps lax validation, so test #3 asserts the documented
lax-coercion behavior (str is accepted and coerced) instead.

Traces: ARC-02, SCH-02, D-04, D-05.
"""

from __future__ import annotations

import ast

import pytest
from pydantic import ValidationError

from lib_code_parser.models.infrastructure.cav import CAV


def test_cav_constructs_without_raw_content_for_backcompat() -> None:
    """Phase 1 3-field construction still works; raw_content defaults to b""."""
    cav = CAV(language="python", path="x.py", payload=ast.parse(""))
    assert cav.raw_content == b""


def test_cav_carries_raw_content_when_supplied() -> None:
    """raw_content is carried verbatim when explicitly supplied."""
    cav = CAV(
        language="python",
        path="x.py",
        payload=ast.parse(""),
        raw_content=b"def f(): pass",
    )
    assert cav.raw_content == b"def f(): pass"


def test_cav_raw_content_accepts_bytes_only() -> None:
    """Pydantic v2 lax mode coerces str -> bytes for the raw_content field.

    The CAV model intentionally keeps lax validation (no ``strict=True``), so a
    str value is coerced to bytes rather than rejected. This test documents the
    actual behavior so future readers do not expect a ValidationError here.
    """
    cav = CAV(
        language="python",
        path="x.py",
        payload=ast.parse(""),
        raw_content="not bytes",  # type: ignore[arg-type]
    )
    assert cav.raw_content == b"not bytes"


def test_cav_remains_frozen_after_raw_content_add() -> None:
    """D-05 frozen invariant: assigning raw_content must raise ValidationError."""
    cav = CAV(language="python", path="x.py", payload=ast.parse(""))
    with pytest.raises(ValidationError):
        cav.raw_content = b"x"  # type: ignore[misc]
