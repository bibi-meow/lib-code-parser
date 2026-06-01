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
# ruff: noqa: E402 -- Phase 2 registration imports live at module bottom by
# design (append-only Open-Closed invariant #4); they are placed AFTER the
# dispatch-dict declarations, which E402 would otherwise flag.

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

# Phase 2 adds: 'python' (stdlib ast); Phase 4 will add: 'cpp' (libclang adapter).
FRONTENDS: dict[str, FrontendFn] = {}

# Phase 2 adds 4 entries: functions, call_graph, type_deps, contracts.
PRIMITIVES: dict[str, PrimitiveFn] = {}

# Phase 3 will add 5 diagrams + 2 specs (7 entries total).
EVALUATIONS: dict[str, EvaluationFn] = {}

# Phase 2 (plan 02-06) registrations — append-only per Open-Closed invariant #4.
# ============================================================================
# NOTE: these imports are at module bottom (not top) intentionally — register
# AFTER the empty dict declarations to make the append-only contract explicit.
# Phase 3 will append diagram + spec entries to EVALUATIONS similarly.
from lib_code_parser.extractors.primitives.callgraph import extract as _extract_callgraph
from lib_code_parser.extractors.primitives.contracts import extract as _extract_contracts
from lib_code_parser.extractors.primitives.functions import extract as _extract_functions
from lib_code_parser.extractors.primitives.type_deps import extract as _extract_type_deps
from lib_code_parser.frontends.python import build_cav as _build_cav_python

FRONTENDS["python"] = _build_cav_python
PRIMITIVES["functions"] = _extract_functions
PRIMITIVES["call_graph"] = _extract_callgraph
PRIMITIVES["type_deps"] = _extract_type_deps
PRIMITIVES["contracts"] = _extract_contracts

# Phase 3 (plan 03-02) EVALUATIONS registrations — append-only, canonical order
# (class_diagram, sequence_diagram, component_diagram, package_diagram, ...).
# sequence_diagram (Plan 03-03) and the FSM/spec entries register later; the
# append-only test asserts subset-in-canonical-order, not contiguity. The dict
# keys are kept in canonical order, so class_diagram is registered first (#1).
from lib_code_parser.extractors.evaluations.class_diagram import (  # noqa: E402
    extract as _extract_class_diagram,
)
from lib_code_parser.extractors.evaluations.component_diagram import (  # noqa: E402
    extract as _extract_component_diagram,
)
from lib_code_parser.extractors.evaluations.package_diagram import (  # noqa: E402
    extract as _extract_package_diagram,
)
from lib_code_parser.extractors.evaluations.sequence_diagram import (  # noqa: E402
    extract as _extract_sequence_diagram,
)

EVALUATIONS["class_diagram"] = _extract_class_diagram
EVALUATIONS["sequence_diagram"] = _extract_sequence_diagram
EVALUATIONS["component_diagram"] = _extract_component_diagram
EVALUATIONS["package_diagram"] = _extract_package_diagram

__all__ = [
    "FrontendFn",
    "PrimitiveFn",
    "EvaluationFn",
    "FRONTENDS",
    "PRIMITIVES",
    "EVALUATIONS",
]
