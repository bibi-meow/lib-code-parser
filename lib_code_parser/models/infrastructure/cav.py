"""Common AST View (CAV) — single-parse envelope shared by all extractors.

Implements ARC-02, satisfies D-04/D-05.

Traces: ARC-02, SCH-02.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class CAV(BaseModel):
    """Common AST View — single-parse envelope shared by all extractors.

    ``payload`` is intentionally opaque (``object``) so the Python frontend can
    stash ``ast.Module`` and the C++ frontend can stash
    ``clang.cindex.TranslationUnit`` without forcing a typed union on the
    cross-cutting contract.

    Immutability is enforced via ``frozen=True``; ``arbitrary_types_allowed=True``
    is required because ``ast.Module`` is not a Pydantic model.
    """

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
        frozen=True,
    )

    language: Literal["python", "cpp"]
    path: str
    payload: object
