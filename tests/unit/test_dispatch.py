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
    """Phase 2 populates FRONTENDS (1) + PRIMITIVES (4) + Phase 3 EVALUATIONS (7).

    Phase 4 plan 04-01 (D-01) nests PRIMITIVES/EVALUATIONS into
    dict[language, dict[name, fn]]: the Python entries move under ["python"]
    (values byte-unchanged) and an empty ["cpp"] sub-dict reserves the cpp slot.
    FRONTENDS stays flat dict[language, fn] (one frontend per language; Pitfall 1
    — never double-nested).
    """

    def test_frontends_dict_has_python_entry(self) -> None:
        assert isinstance(FRONTENDS, dict)
        assert "python" in FRONTENDS

    def test_primitives_dict_has_4_entries_in_append_only_order(self) -> None:
        # Phase 4 D-01: PRIMITIVES is now nested dict[language, dict[name, fn]].
        # The 4 Python primitives live under ["python"] in append-only order
        # (D-12); the empty ["cpp"] sub-dict is the reserved slot for later
        # Phase 4 plans (no cpp callables register in plan 04-01).
        assert isinstance(PRIMITIVES, dict)
        assert list(PRIMITIVES["python"].keys()) == [
            "functions",
            "call_graph",
            "type_deps",
            "contracts",
        ]
        assert "cpp" in PRIMITIVES

    def test_evaluations_registered_append_only(self) -> None:
        # Plan 03-06 registers the FINAL (7th) entry class_spec. All 7
        # EVALUATIONS are present under ["python"] in canonical registration
        # order. Phase 4 D-01 nests EVALUATIONS as dict[language, dict[name, fn]];
        # the empty ["cpp"] sub-dict is the reserved cpp slot (no cpp evaluations
        # register in plan 04-01).
        assert isinstance(EVALUATIONS, dict)
        assert list(EVALUATIONS["python"].keys()) == [
            "class_diagram",
            "sequence_diagram",
            "component_diagram",
            "package_diagram",
            "state_diagram",
            "function_spec",
            "class_spec",
        ]
        assert "cpp" in EVALUATIONS


class TestWR01EvaluationKeyGuard:
    """WR-01: every EVALUATIONS key must correspond to a declared CodeContent
    slot, enforced at import time so a misspelled key fails fast rather than
    surfacing as an opaque Pydantic extra='forbid' error at runtime."""

    def test_every_evaluation_key_is_a_codecontent_field(self) -> None:
        from lib_code_parser.models.infrastructure.artifact import CodeContent

        content_fields = set(CodeContent.model_fields.keys())
        # Phase 4 D-01: EVALUATIONS is nested per-language; iterate both dims.
        for lang in EVALUATIONS:
            for key in EVALUATIONS[lang]:
                assert (
                    key in content_fields
                ), f"EVALUATIONS[{lang!r}] key {key!r} has no CodeContent slot"

    def test_guard_constant_matches_codecontent_fields(self) -> None:
        from lib_code_parser._dispatch import _CONTENT_FIELDS
        from lib_code_parser.models.infrastructure.artifact import CodeContent

        assert _CONTENT_FIELDS == frozenset(CodeContent.model_fields.keys())

    def test_per_language_slot_guard_rejects_bad_cpp_key(self) -> None:
        # Phase 4 D-01: the import-time guard iterates EVERY language dim, so a
        # future cpp evaluation registered under a name with no CodeContent slot
        # must fail fast (T-04-01 fail-loud). Simulate the guard body over a
        # nested EVALUATIONS containing a bogus cpp key.
        from lib_code_parser._dispatch import _CONTENT_FIELDS

        evaluations_with_bad_cpp = {
            "python": {"class_diagram": object()},
            "cpp": {"not_a_codecontent_slot": object()},
        }
        offenders = [
            (lang, key)
            for lang in evaluations_with_bad_cpp
            for key in evaluations_with_bad_cpp[lang]
            if key not in _CONTENT_FIELDS
        ]
        assert offenders == [("cpp", "not_a_codecontent_slot")]

    def test_real_dispatch_passes_per_language_guard(self) -> None:
        # The live nested dispatch must satisfy the guard for both language dims
        # at import time (cpp sub-dicts are empty, so they trivially pass).
        from lib_code_parser._dispatch import _CONTENT_FIELDS

        for lang in EVALUATIONS:
            for key in EVALUATIONS[lang]:
                assert key in _CONTENT_FIELDS


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
