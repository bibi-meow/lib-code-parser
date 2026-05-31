"""Python contract extractor (Pydantic validators + dataclass __post_init__).

Walks the CAV's ast.Module payload once and emits ContractInfo entries with
per-entry source_kind discriminator (D-12 β):

- @validator / @field_validator / @model_validator / @root_validator on a
  class member → ContractEntry with the canonical decorator name (after
  alias resolution) mapped to source_kind via _DECORATOR_TO_SOURCE_KIND
- __post_init__ method (regardless of class-level @dataclass) → ContractEntry
  with source_kind=dataclass_post_init; the verifier no longer sees
  __post_init__ as an unconditional Pydantic concept (AST-04 / SC-3)

Phase 2 fixes two v0.1.0 bugs documented in RESEARCH §3.1:
- C3: aliased imports like `from pydantic import field_validator as fv`
      and `@fv(...)` are now resolved via _resolve_decorator_aliases()
- C4: @root_validator is now recognized and mapped to
      pydantic_model_validator (semantic equivalent per D-11)

Provenance restriction (T-02-19): only decorators whose local name resolves
through the pydantic-scoped import map (or `pydantic.X` attribute form) are
classified, so a same-name decorator from another library is never falsely
emitted into the physical-architecture output.

Implements: AST-04, AST-05
Traces: AST-04, AST-05, US-01, US-22
"""

from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.contracts import (
    ContractEntry,
    ContractInfo,
    ContractKind,
    SourceKind,
)

__all__ = ["extract"]


# D-11 mapping: canonical pydantic decorator name → (source_kind, contract kind)
# - validator / field_validator → precondition (v0.1.0 _PRECONDITION_DECORATORS の意味継承)
# - model_validator / root_validator → invariant (v0.1.0 _INVARIANT_DECORATORS 意味継承)
# - root_validator (v1 deprecated) is semantically equivalent to model_validator (v2)
#   per Pydantic v1→v2 migration guide; collapse to pydantic_model_validator
_DECORATOR_TO_SOURCE_KIND: dict[str, tuple[SourceKind, ContractKind]] = {
    "validator": ("pydantic_validator", "precondition"),
    "field_validator": ("pydantic_field_validator", "precondition"),
    "model_validator": ("pydantic_model_validator", "invariant"),
    "root_validator": ("pydantic_model_validator", "invariant"),
}


def _get_decorator_raw_name(decorator: ast.expr) -> str:
    """Extract the local (possibly-aliased) name from a decorator expression.

    Same semantics as v0.1.0 _get_decorator_name; supports Name / Call(Name) /
    Call(Attribute) / Attribute forms. Returns '' for unsupported forms.
    """
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


def _is_attribute_form(decorator: ast.expr) -> bool:
    """True for `@pydantic.field_validator` / `@pydantic.field_validator(...)` forms.

    Attribute forms carry their pydantic provenance inline (the `pydantic.`
    prefix) and do not depend on an import-alias map.
    """
    target = decorator
    if isinstance(target, ast.Call):
        target = target.func
    return isinstance(target, ast.Attribute)


def _resolve_decorator_aliases(module: ast.Module) -> dict[str, str]:
    """Build {local_name: canonical_pydantic_name} from `from pydantic import ...`.

    Examples:
        from pydantic import field_validator               → {"field_validator": "field_validator"}
        from pydantic import field_validator as fv         → {"fv": "field_validator"}
        from pydantic.deprecated.class_validators import validator → {"validator": "validator"}
        import pydantic                                     → {} (attribute form handled separately)

    Only `from pydantic[.X] import ...` is in scope. Identifiers with the same
    name from other libraries (e.g. `from other_lib import field_validator`) are
    excluded so they are not falsely classified as pydantic contracts (T-02-19).
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "pydantic" or mod.startswith("pydantic."):
                for alias in node.names:
                    local = alias.asname or alias.name
                    aliases[local] = alias.name
    return aliases


def _classify_decorator(
    decorator: ast.expr, aliases: dict[str, str]
) -> tuple[SourceKind, ContractKind, str] | None:
    """Return (source_kind, contract_kind, canonical_name) or None if not a contract.

    A decorator is classified only when its pydantic provenance is established:
    either its local name is in the pydantic-scoped alias map, or it is a
    `pydantic.X` attribute form. Bare names without a pydantic import are
    rejected (T-02-19 false-positive defense).
    """
    raw = _get_decorator_raw_name(decorator)
    if not raw:
        return None

    if raw in aliases:
        canonical = aliases[raw]
    elif _is_attribute_form(decorator):
        # `@pydantic.field_validator` — provenance carried by the attribute prefix.
        canonical = raw
    else:
        # Bare local name with no pydantic import → no provenance, skip.
        return None

    info = _DECORATOR_TO_SOURCE_KIND.get(canonical)
    if info is None:
        return None
    source_kind, contract_kind = info
    return source_kind, contract_kind, canonical


def extract(cav: CAV, config: ParserConfig) -> dict[str, ContractInfo]:
    """AST-04: emit per-class ContractInfo dict from cav.payload (ast.Module).

    config is accepted for signature alignment but not consumed; extraction
    does not depend on per-config flags (the executor in Plan 02-06 applies
    config.extract_contracts to decide whether to invoke this extractor at all).
    """
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"contracts extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )
    module_name = get_module_name(cav.path)
    aliases = _resolve_decorator_aliases(tree)

    result: dict[str, ContractInfo] = {}
    for class_node in tree.body:
        if not isinstance(class_node, ast.ClassDef):
            continue
        class_id = f"{module_name}.{class_node.name}"
        entries: list[ContractEntry] = []

        for item in class_node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # __post_init__ — method-name-only detection (Pitfall 5 + D-11 simplicity)
            if item.name == "__post_init__":
                entries.append(
                    ContractEntry(
                        name="__post_init__",
                        source_kind="dataclass_post_init",
                        kind="precondition",
                        decorator_name="",
                        line_no=item.lineno,
                    )
                )
                continue

            # Decorator scan — first match wins (v0.1.0 parity)
            for decorator in item.decorator_list:
                classified = _classify_decorator(decorator, aliases)
                if classified is None:
                    continue
                source_kind, contract_kind, canonical = classified
                entries.append(
                    ContractEntry(
                        name=item.name,
                        source_kind=source_kind,
                        kind=contract_kind,
                        decorator_name=canonical,
                        line_no=item.lineno,
                    )
                )
                break

        if entries:
            result[class_id] = ContractInfo(node_id=class_id, entries=entries)

    return result
