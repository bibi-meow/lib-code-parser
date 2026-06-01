"""SPC-04 auxiliary contract marker fixtures (icontract / deal / PEP-316).

Each sample is a Python source string with a known marker family. The decoy
sample defines a USER's own ``require`` with NO icontract import — the
false-positive defense (T-03-13) requires it to NOT be classified.

Used by tests/unit/extractors/test_aux_markers.py and the SPC-04 acceptance
test. Detection is import-provenance based: a marker is classified only when
its name resolves through a real icontract/deal import (or the ``pkg.attr``
attribute form). icontract/deal are NEVER imported by the library (D-10).
"""

from __future__ import annotations

# --- icontract: attribute form (@icontract.require) ------------------------
ICONTRACT_ATTR_SOURCE = '''
import icontract


@icontract.invariant(lambda self: self.balance >= 0)
class Account:
    """An account."""

    @icontract.require(lambda amount: amount > 0)
    @icontract.ensure(lambda result: result >= 0)
    def deposit(self, amount):
        return self.balance + amount
'''

# --- icontract: bare name via `from icontract import ...` -------------------
ICONTRACT_FROM_SOURCE = """
from icontract import require, ensure, invariant


@invariant(lambda self: self.x > 0)
class Widget:
    @require(lambda n: n > 0)
    def grow(self, n):
        return n
"""

# --- deal: attribute + bare forms ------------------------------------------
DEAL_ATTR_SOURCE = """
import deal


@deal.inv(lambda self: self.size >= 0)
class Buffer:
    @deal.pre(lambda n: n > 0)
    @deal.post(lambda result: result >= 0)
    @deal.ensure(lambda _: True)
    def push(self, n):
        return n
"""

DEAL_FROM_SOURCE = """
from deal import pre, post


class Calc:
    @pre(lambda x: x > 0)
    @post(lambda result: result >= 0)
    def half(self, x):
        return x / 2
"""

# --- PEP-316 docstring pre:/post: keywords ---------------------------------
PEP316_SOURCE = '''
class Stack:
    def pop(self):
        """Remove and return the top item.

        pre: not self.is_empty()
        post[self]: len(self) == len(__old__.self) - 1
        """
        return self._items.pop()
'''

# --- DECOY: user's own require() with NO icontract import (T-03-13) ---------
# A bare `@require(...)` whose name is NOT imported from icontract/deal must
# NOT be classified — otherwise the user's own helper leaks into the output.
DECOY_REQUIRE_SOURCE = '''
def require(predicate):
    """A user's own decorator that happens to be named require."""
    def wrap(fn):
        return fn
    return wrap


class Service:
    @require(lambda x: x > 0)
    def run(self, x):
        return x
'''

# --- DECOY: bare @pre with no deal import ----------------------------------
DECOY_PRE_NO_IMPORT_SOURCE = """
class Thing:
    @pre(lambda x: x > 0)
    def go(self, x):
        return x
"""
