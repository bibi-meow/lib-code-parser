"""Call-graph + control-flow fixtures for the DIA-02 sequence_diagram extractor.

RESEARCH §Required Test Fixtures (DIA-02): a call-graph source whose linear
sequence edges (participants ordered deterministically) are the must-have, plus
control-flow constructs (if/for/while/async) that exercise the SP-2 branch
frames (alt/loop/par) which shipped per the SP-2 verdict.

These are *source strings* only; the library parses them via the CAV. Nothing
here is imported as a module.
"""

from __future__ import annotations

# Linear call chain: top-level + method calls, no control flow.
# order_service.OrderService.create_order calls _calculate_total (self-call ->
# bare callee name per v0.1.0 callgraph semantics), process_payment calls a
# top-level helper. Proves participants + calls edges, deterministically sorted.
LINEAR_SOURCE = (
    "class OrderService:\n"
    "    def create_order(self, items):\n"
    "        total = self._calculate_total(items)\n"
    "        return total\n"
    "    def _calculate_total(self, items):\n"
    "        return len(items)\n"
    "def process_payment(amount):\n"
    "    return validate(amount)\n"
)
LINEAR_PATH = "src/order_service.py"

# Branch frames: an `if` (alt), a `for` (loop), a `while` (loop), and an async
# `await` (par) each wrapping a call. Proves the SP-2 branch-frame labels.
BRANCH_SOURCE = (
    "def handler(items):\n"
    "    setup()\n"
    "    if items:\n"
    "        notify()\n"
    "    for it in items:\n"
    "        process(it)\n"
    "    while pending():\n"
    "        retry()\n"
    "async def worker():\n"
    "    async with lock():\n"
    "        await fetch()\n"
)
BRANCH_PATH = "src/handler.py"

# No calls at all → empty edges, nodes are the defined callables only.
NO_CALLS_SOURCE = "def lonely():\n    x = 1\n    return x\n"
NO_CALLS_PATH = "src/lonely.py"
