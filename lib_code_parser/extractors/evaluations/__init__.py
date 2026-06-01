"""Evaluations extractors — Phase 3 implements the 5 diagrams + 2 specs.

Each evaluation is a pure ``def extract(cav, config)`` that transforms the
single-parse CAV (or pulls Phase 2 primitives) into a verifier-facing
GraphModel / FunctionSpec / ClassSpec. Registered append-only in
lib_code_parser._dispatch.EVALUATIONS; the executor walks that dict.
"""
