"""SP spike probe tests (deterministic-rule constructibility experiments).

Each spike test is a self-contained determinism probe used by the Phase 3
plans' first-deliverable spikes (D-08): it proves (or disproves) that a pure
``(source) -> structured output`` rule is byte-identical across repeated runs,
which is the SOLE ship-vs-defer criterion (no LLM/heuristic). The verdict is
recorded in ``.planning/spikes/SP-N-*.md``.
"""
