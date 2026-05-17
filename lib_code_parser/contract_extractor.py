"""Contract information extractor for Pydantic/dataclass validators."""

from __future__ import annotations

import ast

from lib_code_parser.models import ContractInfo

# Decorator names that signal field validators
_VALIDATOR_DECORATORS: frozenset[str] = frozenset(
    {"validator", "field_validator", "root_validator", "model_validator"}
)


def _decorator_name(decorator: ast.expr) -> str | None:
    """Extract the simple name from a decorator expression."""
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    return None


def _decorator_args(decorator: ast.expr) -> list[str]:
    """Extract string arguments from a decorator call."""
    if isinstance(decorator, ast.Call):
        args: list[str] = []
        for arg in decorator.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                args.append(arg.value)
        return args
    return []


def _extract_conditions_from_body(body: list[ast.stmt]) -> list[str]:
    """Extract condition strings from if/assert statements in a function body."""
    conditions: list[str] = []
    for stmt in body:
        if isinstance(stmt, ast.If):
            conditions.append(ast.unparse(stmt.test))
        elif isinstance(stmt, ast.Assert):
            conditions.append(ast.unparse(stmt.test))
    return conditions


def extract_contract_info(
    class_node: ast.ClassDef,
    extract_contracts: bool = True,
) -> ContractInfo:
    """Extract contract information from a class definition.

    Looks for:
    - @field_validator / @validator decorators → preconditions
    - __post_init__ conditions → preconditions

    Args:
        class_node: AST ClassDef node to analyze.
        extract_contracts: If False, return empty ContractInfo.

    Returns:
        ContractInfo with preconditions and invariants.
    """
    if not extract_contracts:
        return ContractInfo()

    preconditions: list[str] = []
    invariants: list[str] = []

    for child in ast.iter_child_nodes(class_node):
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # __post_init__ — extract conditions from body
        if child.name == "__post_init__":
            conditions = _extract_conditions_from_body(child.body)
            preconditions.extend(conditions)
            continue

        # Check decorators for validator patterns
        for decorator in child.decorator_list:
            dec_name = _decorator_name(decorator)
            if dec_name in _VALIDATOR_DECORATORS:
                field_names = _decorator_args(decorator)
                if field_names:
                    preconditions.extend(field_names)
                else:
                    # No args — record the method name as a precondition indicator
                    preconditions.append(child.name)
                break

    return ContractInfo(preconditions=preconditions, invariants=invariants)
