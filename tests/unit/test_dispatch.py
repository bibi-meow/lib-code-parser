"""Wave 0 unit tests for lib_code_parser._dispatch (ARC-04, D-12, D-13 #4).

Verifies:
- 3 typed empty dispatch dicts (FRONTENDS / PRIMITIVES / EVALUATIONS)
- Callable type aliases (FrontendFn / PrimitiveFn / EvaluationFn)
- Module docstring documents the append-only invariant (D-13 #4)
- Module docstring forward-references docs/09-extending.md

Traces: ARC-04
"""

from pathlib import Path

import lib_code_parser._dispatch as dispatch_module
from lib_code_parser._dispatch import (
    EVALUATIONS,
    FRONTENDS,
    PRIMITIVES,
    EvaluationFn,
    FrontendFn,
    PrimitiveFn,
)


class TestDispatchDictsPopulated:
    """Phase 2 (plan 02-06) populates FRONTENDS (1) + PRIMITIVES (4).

    EVALUATIONS stays empty after Phase 3 plan 03-01 (foundation only); Plans
    02-06 register the 5 diagrams + 2 specs append-only. The Phase 1 "all dicts
    empty" invariant was retired by plan 02-06's registration deliverable.
    """

    def test_frontends_dict_has_python_entry(self) -> None:
        assert isinstance(FRONTENDS, dict)
        assert "python" in FRONTENDS

    def test_primitives_dict_has_4_entries_in_append_only_order(self) -> None:
        assert isinstance(PRIMITIVES, dict)
        # Insertion order is the append-only registration order (D-12).
        assert list(PRIMITIVES.keys()) == [
            "functions",
            "call_graph",
            "type_deps",
            "contracts",
        ]

    def test_evaluations_registered_append_only(self) -> None:
        # Plan 03-06 registers the FINAL (7th) entry class_spec. All 7
        # EVALUATIONS are now present in canonical registration order — the
        # forward-compatible subsequence assertion graduates to full equality
        # (mirroring test_primitives_dict_has_4_entries_in_append_only_order).
        assert isinstance(EVALUATIONS, dict)
        assert list(EVALUATIONS.keys()) == [
            "class_diagram",
            "sequence_diagram",
            "component_diagram",
            "package_diagram",
            "state_diagram",
            "function_spec",
            "class_spec",
        ]


class TestWR01EvaluationKeyGuard:
    """WR-01: every EVALUATIONS key must correspond to a declared CodeContent
    slot, enforced at import time so a misspelled key fails fast rather than
    surfacing as an opaque Pydantic extra='forbid' error at runtime."""

    def test_every_evaluation_key_is_a_codecontent_field(self) -> None:
        from lib_code_parser.models.infrastructure.artifact import CodeContent

        content_fields = set(CodeContent.model_fields.keys())
        for key in EVALUATIONS:
            assert key in content_fields, f"EVALUATIONS key {key!r} has no CodeContent slot"

    def test_guard_constant_matches_codecontent_fields(self) -> None:
        from lib_code_parser._dispatch import _CONTENT_FIELDS
        from lib_code_parser.models.infrastructure.artifact import CodeContent

        assert _CONTENT_FIELDS == frozenset(CodeContent.model_fields.keys())


class TestDispatchModuleDocstring:
    """Append-only invariant is documentary (D-13 #4, code review gate)."""

    def test_dispatch_module_docstring_mentions_append_only(self) -> None:
        doc = dispatch_module.__doc__ or ""
        assert "append-only" in doc.lower()

    def test_dispatch_module_docstring_mentions_extending(self) -> None:
        # Forward reference to Plan 08's docs/09-extending.md
        doc = dispatch_module.__doc__ or ""
        assert "docs/09-extending.md" in doc


class TestCallableAliasesImportable:
    """Callable type aliases are part of the public surface."""

    def test_callable_aliases_imported(self) -> None:
        # If import at top succeeded, the aliases exist; assert non-None to silence lints
        assert FrontendFn is not None
        assert PrimitiveFn is not None
        assert EvaluationFn is not None


class TestDispatchSourceFile:
    """Source-file invariants (documentary gates per RESEARCH design choices)."""

    @staticmethod
    def _read_source() -> str:
        path = Path(__file__).resolve().parents[2] / "lib_code_parser" / "_dispatch.py"
        return path.read_text(encoding="utf-8")

    def test_no_mappingproxytype(self) -> None:
        # MappingProxyType would block legitimate Phase 2 dict additions
        src = self._read_source()
        assert "MappingProxyType" not in src

    def test_no_protocol(self) -> None:
        # Protocol attracts method-shaped expectations; we use Callable instead
        src = self._read_source()
        assert "Protocol" not in src
