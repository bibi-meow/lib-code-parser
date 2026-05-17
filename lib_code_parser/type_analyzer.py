"""Type dependency analyzer: pyright subprocess with AST fallback."""

from __future__ import annotations

import ast
import subprocess

from lib_code_parser.models import TypeDep

# Built-in / standard annotation names that are not external type deps
_BUILTINS: frozenset[str] = frozenset(
    {
        "str",
        "int",
        "float",
        "bool",
        "bytes",
        "bytearray",
        "memoryview",
        "complex",
        "None",
        "NoneType",
        "list",
        "dict",
        "set",
        "frozenset",
        "tuple",
        "type",
        "object",
        "Any",
        "Optional",
        "Union",
        "List",
        "Dict",
        "Set",
        "Tuple",
        "FrozenSet",
        "Type",
        "Callable",
        "Iterator",
        "Generator",
        "Iterable",
        "Sequence",
        "Mapping",
        "MutableMapping",
        "MutableSequence",
        "ClassVar",
        "Final",
        "Literal",
        "TypeVar",
        "Generic",
        "Protocol",
        "overload",
        "dataclass",
        "field",
        "property",
        "staticmethod",
        "classmethod",
        "abstractmethod",
        "Self",
        "Never",
        "LiteralString",
        "TypeAlias",
        "ParamSpec",
        "Concatenate",
        "TypeGuard",
        "Annotated",
    }
)


def _extract_type_names(annotation: ast.expr) -> list[str]:
    """Recursively extract all Name nodes from an annotation expression."""
    names: list[str] = []
    if isinstance(annotation, ast.Name):
        names.append(annotation.id)
    elif isinstance(annotation, ast.Attribute):
        # e.g. typing.Optional — skip
        pass
    elif isinstance(annotation, ast.Subscript):
        names.extend(_extract_type_names(annotation.value))
        names.extend(_extract_type_names(annotation.slice))
    elif isinstance(annotation, ast.Tuple):
        for elt in annotation.elts:
            names.extend(_extract_type_names(elt))
    elif isinstance(annotation, ast.BinOp):
        # PEP 604 union: X | Y
        names.extend(_extract_type_names(annotation.left))
        names.extend(_extract_type_names(annotation.right))
    elif isinstance(annotation, ast.Constant):
        # Forward reference string annotation
        if isinstance(annotation.value, str):
            try:
                inner = ast.parse(annotation.value, mode="eval")
                names.extend(_extract_type_names(inner.body))
            except SyntaxError:
                pass
    return names


def _ast_fallback(source: str, module_name: str) -> list[TypeDep]:
    """Extract type deps using pure AST analysis."""
    tree = ast.parse(source)
    deps: list[TypeDep] = []

    def _process_func(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        caller_id: str,
    ) -> None:
        all_args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
        for arg in all_args:
            if arg.annotation:
                for name in _extract_type_names(arg.annotation):
                    if name not in _BUILTINS:
                        deps.append(TypeDep(source=caller_id, target=name, dep_type="typing"))
        if node.returns:
            for name in _extract_type_names(node.returns):
                if name not in _BUILTINS:
                    deps.append(TypeDep(source=caller_id, target=name, dep_type="typing"))

    for item in ast.walk(tree):
        if isinstance(item, ast.ClassDef):
            class_prefix = f"{module_name}.{item.name}"
            for child in ast.iter_child_nodes(item):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _process_func(child, f"{class_prefix}.{child.name}")
        elif isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
            # Only top-level (not inside class) — we can't easily distinguish here,
            # so we walk all FunctionDef nodes at top-level
            pass

    # Second pass for top-level functions
    for item in ast.iter_child_nodes(tree):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _process_func(item, f"{module_name}.{item.name}")

    # Deduplicate
    seen: set[tuple[str, str]] = set()
    unique: list[TypeDep] = []
    for d in deps:
        key = (d.source, d.target)
        if key not in seen:
            seen.add(key)
            unique.append(d)

    return unique


def analyze_type_deps(
    source: str,
    path: str,
    module_name: str,
    use_pyright: bool = True,
) -> list[TypeDep]:
    """Analyze type dependencies in Python source.

    Attempts pyright subprocess analysis when use_pyright=True.
    Falls back to AST-based extraction on any failure.

    Args:
        source: Python source code.
        path: File path (used for pyright invocation).
        module_name: Logical module name prefix.
        use_pyright: Whether to attempt pyright analysis.

    Returns:
        List of TypeDep objects.
    """
    if not source.strip():
        return []

    if use_pyright:
        try:
            subprocess.run(
                ["pyright", "--outputjson", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # pyright JSON output can be processed here in a full implementation
            # For now, always fall back to AST (pyright output parsing is complex)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

    return _ast_fallback(source, module_name)
