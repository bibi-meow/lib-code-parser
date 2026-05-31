"""Python type dependency extractor (CAV + pyright adapter).

Combines a stdlib ast walk over cav.payload (RESEARCH §7.3 v0.1.0 parity for
import / annotation extraction) with PyrightAdapter (Plan 02-05) to annotate
each TypeDep with resolved=True when pyright did NOT fire a
reportMissingImports diagnostic on the source line, and resolved=False when
it did. This is the CONTEXT.md D-07-revised algorithm — pyright's
--outputjson cannot provide resolved type info (RESEARCH §2.1 empirical),
so pyright is used as a diagnostic-driven resolution oracle.

PyrightAdapter is invoked with cav.raw_content (carried by the Python
Frontend via Plan 02-01). This avoids the ast.unparse round-trip that would
drift line numbers and break the diagnostic <-> TypeDep mapping (Assumption A1).

D-06 fail-loudly: PyrightAdapter RuntimeError propagates; silent empty list
is never returned.

Implements: AST-03, AST-05, DET-03
Traces: AST-03, AST-05, DET-03, US-01, US-22
"""

from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name
from lib_code_parser.adapters.pyright import PyrightAdapter
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.type_deps import TypeDep

__all__ = ["extract"]

_EXCLUDED_NAMES: frozenset[str] = frozenset({"None", "True", "False"})


def _collect_annotation_deps(
    annotation: ast.expr,
    module_name: str,
    source_line: int,
    deps: list[TypeDep],
) -> None:
    """Walk annotation tree and record TypeDep entries with source_line."""
    for sub in ast.walk(annotation):
        if isinstance(sub, ast.Name):
            name = sub.id
            if name and name not in _EXCLUDED_NAMES:
                deps.append(
                    TypeDep(
                        source=module_name,
                        target=name,
                        kind="uses",
                        source_line=source_line,
                    )
                )
        elif isinstance(sub, ast.Attribute):
            # Uppercase-first heuristic for class-like types (v0.1.0 parity)
            if sub.attr and sub.attr[0].isupper():
                deps.append(
                    TypeDep(
                        source=module_name,
                        target=sub.attr,
                        kind="uses",
                        source_line=source_line,
                    )
                )


def extract(cav: CAV, config: ParserConfig) -> list[TypeDep]:
    """AST-03 / AST-05 / DET-03 / DET-04: emit type_deps list from cav.

    Algorithm (RESEARCH §2.3 hybrid):
        1. stdlib ast walk -> raw TypeDeps (v0.1.0 parity + source_line tracking)
        2. PyrightAdapter.analyze(cav.raw_content, cav.path) -> diagnostics
        3. annotate resolved=False for source_line in reportMissingImports range
        4. sort by (source, target, kind, source_line) — DET-04
    """
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"type_deps extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )
    module_name = get_module_name(cav.path)
    raw_deps: list[TypeDep] = []

    # Step 1: ast walk for imports + annotations (v0.1.0 parity + source_line)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                raw_deps.append(
                    TypeDep(
                        source=module_name,
                        target=alias.asname if alias.asname else alias.name,
                        kind="imports",
                        source_line=node.lineno,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            from_module = node.module or ""
            for alias in node.names:
                target = f"{from_module}.{alias.name}" if from_module else alias.name
                raw_deps.append(
                    TypeDep(
                        source=module_name,
                        target=target,
                        kind="imports",
                        source_line=node.lineno,
                    )
                )

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                if arg.annotation:
                    _collect_annotation_deps(
                        arg.annotation,
                        module_name,
                        arg.lineno,
                        raw_deps,
                    )
            if node.returns:
                _collect_annotation_deps(
                    node.returns,
                    module_name,
                    node.returns.lineno,
                    raw_deps,
                )

    # Step 2: pyright diagnostics — fail-loudly per D-06 (RuntimeError propagates)
    adapter = PyrightAdapter(python_version=config.python_version)
    pyright_result = adapter.analyze(cav.raw_content, cav.path)

    # Step 3: annotate resolved flag.
    # pyright range.start.line is 0-based; ast.lineno is 1-based. Normalize
    # to 1-based for comparison.
    unresolved_ranges: list[tuple[int, int]] = [
        (d.start_line + 1, d.end_line + 1)
        for d in pyright_result.diagnostics
        if d.rule == "reportMissingImports"
    ]

    annotated: list[TypeDep] = []
    for dep in raw_deps:
        is_resolved = True
        for start_one_based, end_one_based in unresolved_ranges:
            if start_one_based <= dep.source_line <= end_one_based:
                is_resolved = False
                break
        annotated.append(dep.model_copy(update={"resolved": is_resolved}))

    # Step 4: DET-04 sort by (source, target, kind, source_line)
    annotated.sort(key=lambda d: (d.source, d.target, d.kind, d.source_line))
    return annotated
