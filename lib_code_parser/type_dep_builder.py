"""Type dependency extractor from Python AST (imports + annotations)."""

from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name as _get_module_name
from lib_code_parser.models import TypeDep

# ARC-04 / DET-04: single source of truth for path -> module-name; thin shim
# preserves the v0.1.0 private symbol export for test backward-compat.


def build_type_deps(source: str, path: str) -> list[TypeDep]:
    """Extract TypeDep from import statements and type annotations."""
    tree = ast.parse(source)
    module_name = _get_module_name(path)
    deps: list[TypeDep] = []

    # Import statements
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps.append(
                    TypeDep(
                        source=module_name,
                        target=alias.asname if alias.asname else alias.name,
                        kind="imports",
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            from_module = node.module or ""
            for alias in node.names:
                target = f"{from_module}.{alias.name}" if from_module else alias.name
                deps.append(
                    TypeDep(
                        source=module_name,
                        target=target,
                        kind="imports",
                    )
                )

    # Type annotations in function parameters and return types
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Parameter annotations
            for arg in node.args.args:
                if arg.annotation:
                    _collect_annotation_deps(arg.annotation, module_name, deps)
            # Return annotation
            if node.returns:
                _collect_annotation_deps(node.returns, module_name, deps)

    return deps


def _collect_annotation_deps(annotation: ast.expr, module_name: str, deps: list[TypeDep]) -> None:
    """Recursively collect type names from annotation AST nodes."""
    # Walk the annotation tree to find Name nodes (type names)
    for sub in ast.walk(annotation):
        if isinstance(sub, ast.Name):
            # Only collect names starting with uppercase (class types) or builtins
            name = sub.id
            if name and name not in ("None", "True", "False"):
                deps.append(TypeDep(source=module_name, target=name, kind="uses"))
        elif isinstance(sub, ast.Attribute):
            # e.g. "OrderModel" from "models.OrderModel"
            if sub.attr and sub.attr[0].isupper():
                deps.append(TypeDep(source=module_name, target=sub.attr, kind="uses"))
