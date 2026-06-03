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
# FRONTENDS is keyed by language ONLY — never double-nested (Phase 4 Pitfall 1).
# There is exactly one frontend per language, so a flat dict[language, fn] is the
# correct shape; PRIMITIVES/EVALUATIONS below carry the per-language extractor sets.
FRONTENDS: dict[str, FrontendFn] = {}

# Phase 4 D-01: PRIMITIVES/EVALUATIONS gain the language dimension. They are
# nested dict[language, dict[name, fn]] so cpp extractors run ONLY on cpp CAV and
# python extractors run ONLY on python CAV (LNG-04 parity: slot names stay common
# across languages). The Phase 2 python entries move under ["python"] with their
# values byte-unchanged (Open-Closed invariants #1/#2). The empty ["cpp"] sub-dicts
# are the only cpp presence in THIS plan; cpp callables register in later Phase 4 plans.
# Language keys are append-only (existing language keys are never removed or renamed).

# Phase 2 adds 4 entries under ["python"]: functions, call_graph, type_deps, contracts.
PRIMITIVES: dict[str, dict[str, PrimitiveFn]] = {"python": {}, "cpp": {}}

# Phase 3 adds 5 diagrams + 2 specs (7 entries total) under ["python"].
EVALUATIONS: dict[str, dict[str, EvaluationFn]] = {"python": {}, "cpp": {}}

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
PRIMITIVES["python"]["functions"] = _extract_functions
PRIMITIVES["python"]["call_graph"] = _extract_callgraph
PRIMITIVES["python"]["type_deps"] = _extract_type_deps
PRIMITIVES["python"]["contracts"] = _extract_contracts

# Phase 4 (plan 04-03) cpp frontend registration — append-only, flat FRONTENDS
# keyed by language (NOT nested — Phase 4 Pitfall 1). One frontend per language;
# FRONTENDS["python"] above is never overwritten. cpp PRIMITIVES/EVALUATIONS
# entries land in their own later Phase 4 plans, not here.
from lib_code_parser.frontends.cpp import build_cav as _build_cav_cpp  # noqa: E402

FRONTENDS["cpp"] = _build_cav_cpp

# Phase 4 (plan 04-04) cpp PRIMITIVES registrations — append-only into the
# reserved ["cpp"] sub-dict (D-01). Common slot spelling shared with python
# ("functions"/"call_graph"/"type_deps") so LNG-04 parity is automatic.
from lib_code_parser.extractors.primitives.cpp_callgraph import (  # noqa: E402
    extract as _extract_cpp_callgraph,
)
from lib_code_parser.extractors.primitives.cpp_functions import (  # noqa: E402
    extract as _extract_cpp_functions,
)
from lib_code_parser.extractors.primitives.cpp_type_deps import (  # noqa: E402
    extract as _extract_cpp_type_deps,
)

PRIMITIVES["cpp"]["functions"] = _extract_cpp_functions
PRIMITIVES["cpp"]["call_graph"] = _extract_cpp_callgraph
PRIMITIVES["cpp"]["type_deps"] = _extract_cpp_type_deps

# Phase 4 (plan 04-05) cpp Doxygen contracts (SPC-03) — append-only into the
# reserved ["cpp"] sub-dict, sharing the common "contracts" slot spelling with
# python so the executor's config.extract_contracts gate applies uniformly (D-09).
from lib_code_parser.extractors.primitives.cpp_contracts import (  # noqa: E402
    extract as _extract_cpp_contracts,
)

PRIMITIVES["cpp"]["contracts"] = _extract_cpp_contracts

# Phase 3 (plan 03-02) EVALUATIONS registrations — append-only, canonical order
# (class_diagram, sequence_diagram, component_diagram, package_diagram, ...).
# sequence_diagram (Plan 03-03) and the FSM/spec entries register later; the
# append-only test asserts subset-in-canonical-order, not contiguity. The dict
# keys are kept in canonical order, so class_diagram is registered first (#1).
from lib_code_parser.extractors.evaluations.class_diagram import (  # noqa: E402
    extract as _extract_class_diagram,
)
from lib_code_parser.extractors.evaluations.class_spec import (  # noqa: E402
    extract as _extract_class_spec,
)
from lib_code_parser.extractors.evaluations.component_diagram import (  # noqa: E402
    extract as _extract_component_diagram,
)
from lib_code_parser.extractors.evaluations.function_spec import (  # noqa: E402
    extract as _extract_function_spec,
)
from lib_code_parser.extractors.evaluations.package_diagram import (  # noqa: E402
    extract as _extract_package_diagram,
)
from lib_code_parser.extractors.evaluations.sequence_diagram import (  # noqa: E402
    extract as _extract_sequence_diagram,
)
from lib_code_parser.extractors.evaluations.state_diagram import (  # noqa: E402
    extract as _extract_state_diagram,
)

EVALUATIONS["python"]["class_diagram"] = _extract_class_diagram
EVALUATIONS["python"]["sequence_diagram"] = _extract_sequence_diagram
EVALUATIONS["python"]["component_diagram"] = _extract_component_diagram
EVALUATIONS["python"]["package_diagram"] = _extract_package_diagram
EVALUATIONS["python"]["state_diagram"] = _extract_state_diagram
# Plan 03-05: SPC-01 function_spec at canonical position #6 (append-only).
EVALUATIONS["python"]["function_spec"] = _extract_function_spec
# Plan 03-06: SPC-02/04 class_spec at canonical position #7 — the FINAL entry.
EVALUATIONS["python"]["class_spec"] = _extract_class_spec

# WR-01: registration-time guard. The executor assigns each evaluation result
# into the same-named CodeContent slot via setattr; a misspelled EVALUATIONS
# key would otherwise surface only at runtime as an opaque Pydantic
# extra="forbid" error. Assert at import time that every key has a declared
# CodeContent field so a typo fails fast and clearly.
from lib_code_parser.models.infrastructure.artifact import CodeContent  # noqa: E402

_CONTENT_FIELDS = frozenset(CodeContent.model_fields.keys())
for _lang in EVALUATIONS:
    for _eval_key in EVALUATIONS[_lang]:
        if _eval_key not in _CONTENT_FIELDS:
            raise AssertionError(
                f"EVALUATIONS[{_lang!r}] key {_eval_key!r} has no matching CodeContent slot; "
                f"declared slots: {sorted(_CONTENT_FIELDS)}"
            )

__all__ = [
    "FrontendFn",
    "PrimitiveFn",
    "EvaluationFn",
    "FRONTENDS",
    "PRIMITIVES",
    "EVALUATIONS",
]
