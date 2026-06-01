"""Structural fixtures for DIA-01 class_diagram tests (RESEARCH §Required Test Fixtures).

A class hierarchy exercising every branch of the composition/aggregation/
association decision rule:

- ``class B(A)`` → ``inherits`` edge B → A
- ``x: Engine`` (direct known class) → ``composes`` B → Engine
- ``y: Optional[Engine]`` / ``z: list[Engine]`` (container/optional of known
  class) → ``aggregates`` B → Engine
- ``w: SomeForwardRefUnknown`` (undecidable name) → ``associates`` B → ...
- ``n: int`` / ``s: str`` (builtin/primitive) → NO edge (field, skipped)

These are *source strings*; the extractor parses them via the CAV. No imports of
the named classes are needed at runtime.
"""

from __future__ import annotations

# Class hierarchy fixture: A (base), Engine (known class), B (relationships).
CLASS_HIERARCHY_SOURCE = '''
from typing import Optional


class A:
    pass


class Engine:
    pass


class B(A):
    """Subclass with the full relationship spectrum."""

    x: Engine                       # composes (direct known class)
    y: Optional[Engine]             # aggregates (Optional of known class)
    z: list[Engine]                 # aggregates (container of known class)
    w: SomeForwardRefUnknown        # associates (undecidable / unknown name)
    n: int                          # skip (builtin)
    s: str                          # skip (builtin)
'''

CLASS_HIERARCHY_PATH = "src/shapes.py"


# __init__ self-attribute annotations fixture: relationships declared inside
# __init__ via `self.x: T = ...` rather than class-body AnnAssign.
INIT_ATTRS_SOURCE = """
class Wheel:
    pass


class Car:
    def __init__(self) -> None:
        self.wheel: Wheel = Wheel()      # composes
        self.spare: "Wheel | None" = None  # aggregates (X | None)
"""

INIT_ATTRS_PATH = "src/auto.py"
