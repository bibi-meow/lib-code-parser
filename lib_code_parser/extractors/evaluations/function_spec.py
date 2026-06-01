"""SPC-01 function spec extractor (signature + normalized docstring + pre/post).

The physical-side analog of lib-spec-parser's logical function spec: for each
function/method this emits a ``FunctionSpec`` carrying the synthesized signature,
the dialect-normalized ``docstring_sections`` (via the stdlib-only
``_docstring`` parser), and the fixed-keyword-derived pre/postconditions
(``source_kind="docstring"``). Functions without a docstring still emit an inert
``FunctionSpec`` (empty sections) so the verifier always sees the signature.

Pulls the Phase 2 ``functions`` primitive for signatures (no re-walk of the
AST for shape); the raw docstring already lives on each ``FunctionNode``.

D-09: docstring parsing is stdlib-only (no external library).
DET-04: output sorted by ``node_id`` on exit → byte-identical across
PYTHONHASHSEED.

Implements: SPC-01
Traces: SPC-01, US-01, US-22.
"""

from __future__ import annotations

import ast

from lib_code_parser.extractors.evaluations import _docstring
from lib_code_parser.extractors.primitives import functions
from lib_code_parser.models.evaluations.spec import FunctionSpec
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.functions import FunctionNode

__all__ = ["extract"]


def _signature(node: FunctionNode) -> str:
    """Synthesize a deterministic ``name(params) -> return`` signature string."""
    name = node.node_id.rsplit(".", 1)[-1]
    parts: list[str] = []
    for param in node.params:
        if param.type_annotation:
            parts.append(f"{param.name}: {param.type_annotation}")
        else:
            parts.append(param.name)
    sig = f"{name}({', '.join(parts)})"
    if node.return_type:
        sig += f" -> {node.return_type}"
    return sig


def extract(cav: CAV, config: ParserConfig) -> list[FunctionSpec]:
    """SPC-01: emit one FunctionSpec per function/method from cav.

    Functions/methods (not class nodes) get a synthesized signature and their
    docstring normalized via ``_docstring.parse``; undocumented members emit an
    inert FunctionSpec (empty sections) so the signature is still visible.
    """
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"function_spec extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )

    specs: list[FunctionSpec] = []
    for node in functions.extract(cav, config):
        # SPC-01 is function/method scoped; class nodes are SPC-02 (class_spec).
        if node.kind == "class":
            continue
        sections, pre, post = _docstring.parse(node.docstring)
        specs.append(
            FunctionSpec(
                node_id=node.node_id,
                signature=_signature(node),
                docstring_sections=sections,
                preconditions=pre,
                postconditions=post,
                source_range=node.source_range,
            )
        )

    # DET-04 sort-on-exit by node_id → byte-identical across PYTHONHASHSEED.
    specs.sort(key=lambda s: s.node_id)
    return specs
