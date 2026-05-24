"""Adapters — subprocess-isolated tool wrappers (ARC-03).

Phase 1 ships only the base helper + ABC; Phase 2 adds PyrightAdapter.
All subprocess invocations in this library MUST go through ``run_subprocess()``
or a subclass of ``SubprocessAdapter``.

Traces: ARC-03, DET-05.
"""

from __future__ import annotations

from lib_code_parser.adapters.base import SubprocessAdapter, run_subprocess

__all__ = ["run_subprocess", "SubprocessAdapter"]
