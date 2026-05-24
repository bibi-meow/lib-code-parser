"""Contract extractor: Pydantic validators -> ContractInfo per class."""

from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name as _get_module_name
from lib_code_parser.models import ContractInfo

# ARC-04 / DET-04: single source of truth for path -> module-name; thin shim
# preserves the v0.1.0 private symbol export for test backward-compat.

_PRECONDITION_DECORATORS = frozenset({"field_validator", "validator"})
_INVARIANT_DECORATORS = frozenset({"model_validator"})


def _get_decorator_name(decorator: ast.expr) -> str:
    """Extract the base name from a decorator (Name or Call)."""
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    return ""


def extract_contracts(source: str, path: str) -> dict[str, ContractInfo]:
    """Extract ContractInfo per class from Pydantic/dataclass validators.

    Returns a dict mapping class node_id -> ContractInfo.
    Only classes that have at least one validator are included.
    """
    tree = ast.parse(source)
    module_name = _get_module_name(path)
    contracts: dict[str, ContractInfo] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        class_id = f"{module_name}.{node.name}"
        preconditions: list[str] = []
        invariants: list[str] = []

        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # __post_init__ counts as precondition
            if item.name == "__post_init__":
                preconditions.append("__post_init__")
                continue

            for decorator in item.decorator_list:
                dec_name = _get_decorator_name(decorator)
                if dec_name in _PRECONDITION_DECORATORS:
                    preconditions.append(item.name)
                    break
                if dec_name in _INVARIANT_DECORATORS:
                    invariants.append(item.name)
                    break

        if preconditions or invariants:
            contracts[class_id] = ContractInfo(
                preconditions=preconditions,
                invariants=invariants,
            )

    return contracts
