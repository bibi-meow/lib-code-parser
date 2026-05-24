"""Single source of truth for path → module-name derivation (ARC-04 / DET-04).

Eliminates the v0.1.0 4× duplication of _get_module_name across
ast_extractor.py / callgraph_builder.py / type_dep_builder.py /
contract_extractor.py. Plan 09 patches those 4 v0.1.0 extractors to make
their `_get_module_name` thin shims that re-export from this module.

Traces: ARC-04, DET-04
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["get_module_name"]


def get_module_name(path: str) -> str:
    """Convert file path to module name (stem only)."""
    return Path(path).stem
