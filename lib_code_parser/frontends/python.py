"""Python Frontend — ast.parse() the source exactly once and emit CAV envelope.

This is the SINGLE site in lib_code_parser/extractors/ + frontends/ that
calls ast.parse(). All primitive extractors consume cav.payload (already-
parsed ast.Module) and never re-parse. The raw bytes are carried on the
CAV envelope (cav.raw_content) so the type_deps extractor's PyrightAdapter
can write them to its tmpdir without an ast.unparse() round-trip
(which would drift line numbers).

Implements: AST-05
Traces: AST-05, ARC-02
"""

from __future__ import annotations

import ast

from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["build_cav"]


def build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV:
    """Parse raw_content exactly once into ast.Module and wrap in a CAV envelope.

    AST-05 single-parse invariant: this is the ONLY ast.parse() call site for
    the Python language path. Primitive extractors (functions / callgraph /
    type_deps / contracts) consume cav.payload and never re-parse.

    The ``config`` argument is part of the FrontendFn dispatch contract
    (``_dispatch.FrontendFn``) and is accepted for signature parity; the Python
    parse does not depend on any ParserConfig field.
    """
    source = raw_content.decode("utf-8", errors="replace")
    module = ast.parse(source, filename=path)
    return CAV(
        language="python",
        path=path,
        payload=module,
        raw_content=raw_content,
    )
