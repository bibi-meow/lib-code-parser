"""Static dispatch tables for frontends, primitives, and evaluations.

This module is the single point of registration for new extractors. After
Phase 1 freezes the dict types, every new extractor in Phase 2-4 adds exactly
one entry to the appropriate dict. The executor never grows logic; it only
walks these dicts.

INVARIANT (Open-Closed contract #4): dicts are append-only. Existing entries
are never modified or removed. See docs/09-extending.md for the full
6-invariant Open-Closed contract.

Traces: ARC-04
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from lib_code_parser.models.infrastructure.cav import CAV
    from lib_code_parser.models.infrastructure.config import ParserConfig

# Type aliases for the dispatch signatures.
# FrontendFn: (raw_content, path, config) -> CAV (Common AST View)
FrontendFn = Callable[[bytes, str, "ParserConfig"], "CAV"]

# PrimitiveFn: (cav, config) -> primitive model instance (concrete type per primitive)
PrimitiveFn = Callable[["CAV", "ParserConfig"], object]

# EvaluationFn: (cav, config) -> evaluation model instance (concrete type per evaluation)
EvaluationFn = Callable[["CAV", "ParserConfig"], object]

# Phase 2 will add: 'python' (stdlib ast); Phase 4 will add: 'cpp' (libclang adapter).
FRONTENDS: dict[str, FrontendFn] = {}

# Phase 2 will add 4 entries: functions, call_graph, type_deps, contracts.
PRIMITIVES: dict[str, PrimitiveFn] = {}

# Phase 3 will add 5 diagrams + 2 specs (7 entries total).
EVALUATIONS: dict[str, EvaluationFn] = {}

__all__ = [
    "FrontendFn",
    "PrimitiveFn",
    "EvaluationFn",
    "FRONTENDS",
    "PRIMITIVES",
    "EVALUATIONS",
]
