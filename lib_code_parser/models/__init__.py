"""Parent package marker for the lib_code_parser.models nested layout.

This file is intentionally minimal during Wave 1 (Plans 01-03/04/05 in parallel).
Wave 2 Plan 01-09 will rewrite this file to provide the v0.1.0 backward-compat
re-export surface (FunctionNode, CallGraph, etc.) sourced from the new
infrastructure/ and primitives/ subpackages, and will then delete the legacy
lib_code_parser/models.py file.

During Wave 1 worktrees this file does not re-export the v0.1.0 14-model surface,
so a top-level ``from lib_code_parser import CodeParserExecutor`` will fail until
Wave 2 integration runs. Direct submodule access
(``from lib_code_parser.models.evaluations.graph_base import EdgeKind``) still
goes through ``lib_code_parser/__init__.py`` and therefore inherits the same
constraint — Wave 1 verification of this plan is done via static grep gates and
post-integration pytest in Wave 2.

Traces: ARC-01, D-10.
"""
