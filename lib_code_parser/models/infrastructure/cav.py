"""Common AST View (CAV) — single-parse envelope shared by all extractors.

Implements ARC-02, satisfies D-04/D-05.

Phase 2 (plan 02-01) adds an additive ``raw_content: bytes`` field so the
type_deps extractor's pyright adapter can write the original bytes to its
internal tmpdir without re-serializing via ``ast.unparse`` (which would drift
line numbers and break pyright diagnostic <-> TypeDep mapping). The default
``b""`` keeps Phase 1 callers backward-compatible — the field is additive, not
breaking.

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

    See module docstring for the Phase 2 ``raw_content`` rationale.
    """

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
        frozen=True,
    )

    language: Literal["python", "cpp"]
    path: str
    payload: object
    raw_content: bytes = b""
