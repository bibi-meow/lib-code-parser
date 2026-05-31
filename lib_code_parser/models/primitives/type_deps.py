"""Primitive type-dependency model — TypeDep.

Traces: SCH-02, AST-03, DET-03. Phase 2 fills via the type_deps extractor.

NOTE: TypeDep.kind is a free-form str at the primitives layer per D-14; the closed
EdgeKind Literal applies only to verifier-facing evaluations/.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TypeDep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    kind: str = "uses"
    # Phase 2 (plan 02-06) additive fields per CONTEXT.md D-07-revised algorithm:
    # - resolved: pyright reportMissingImports diagnostic did NOT fire on the
    #   ast.Import / ast.ImportFrom line -> True; fired -> False. Default True
    #   for v0.1.0 parity (callers ignoring resolution semantics see same shape).
    # - source_line: 1-based source line of the import statement / annotation
    #   for diagnostic <-> TypeDep mapping. Default 0 = "unknown / not tracked".
    resolved: bool = True
    source_line: int = 0
