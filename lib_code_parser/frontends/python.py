"""Python Frontend — ast.parse() the source exactly once and emit CAV envelope.

This is the SINGLE site in lib_code_parser/extractors/ + frontends/ that
calls ast.parse(). All primitive extractors consume cav.payload (already-
parsed ast.Module) and never re-parse.

Implements: AST-05
Traces: AST-05, ARC-02
"""

from __future__ import annotations

import ast

from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["build_cav"]


def build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV:
    """Parse raw_content exactly once into ast.Module and wrap in CAV envelope."""
    source = raw_content.decode("utf-8", errors="replace")
    module = ast.parse(source, filename=path)
    return CAV(language="python", path=path, payload=module)
