"""Frontends — language-specific CAV producers (1 parse per file).

Phase 2 ships ``build_cav`` for Python via ``lib_code_parser.frontends.python``;
Phase 4 will add the C++ adapter. Each Frontend is the single ast.parse() /
libclang TranslationUnit creation site for its language. AST-05 invariant
is enforced by ``tests/parity/test_ast_05_one_parse.py``.

Implements: AST-05
Traces: AST-05, ARC-02
"""

from lib_code_parser.frontends.python import build_cav

__all__ = ["build_cav"]
