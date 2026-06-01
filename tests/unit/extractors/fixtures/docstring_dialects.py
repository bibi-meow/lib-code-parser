"""Three-dialect golden fixture for the SPC-01 docstring parser.

The SAME function — same summary, same two parameters (``amount``, ``method``),
same return clause, same raised exception — documented three ways: Google,
NumPy, and Sphinx (reST) Napoleon styles. The strongest SPC-01 determinism
proof is that ``_docstring.parse`` reduces all three to byte-identical
normalized ``DocstringSection`` output (RESEARCH §Required Test Fixtures).

Each docstring shares the SAME normalized content:
- summary: "Process a payment."
- param amount (float): "must be > 0 — the charge amount."
- param method (str): "the payment method; required."
- returns (bool): "True if the charge settled."
- raises (ValueError): "if amount is non-negative."
"""

from __future__ import annotations

GOOGLE_DOCSTRING = """Process a payment.

Args:
    amount (float): must be > 0 — the charge amount.
    method (str): the payment method; required.

Returns:
    bool: True if the charge settled.

Raises:
    ValueError: if amount is non-negative.
"""

NUMPY_DOCSTRING = """Process a payment.

Parameters
----------
amount : float
    must be > 0 — the charge amount.
method : str
    the payment method; required.

Returns
-------
bool
    True if the charge settled.

Raises
------
ValueError
    if amount is non-negative.
"""

SPHINX_DOCSTRING = """Process a payment.

:param amount: must be > 0 — the charge amount.
:type amount: float
:param method: the payment method; required.
:type method: str
:returns: True if the charge settled.
:rtype: bool
:raises ValueError: if amount is non-negative.
"""

# A source module exercising the full execute() path: the SAME function body
# documented in each dialect, plus a no-docstring function (inert FunctionSpec).
THREE_DIALECT_SOURCE = '''
def pay_google(amount: float, method: str) -> bool:
    """Process a payment.

    Args:
        amount (float): must be > 0 — the charge amount.
        method (str): the payment method; required.

    Returns:
        bool: True if the charge settled.

    Raises:
        ValueError: if amount is non-negative.
    """
    return True


def pay_numpy(amount: float, method: str) -> bool:
    """Process a payment.

    Parameters
    ----------
    amount : float
        must be > 0 — the charge amount.
    method : str
        the payment method; required.

    Returns
    -------
    bool
        True if the charge settled.

    Raises
    ------
    ValueError
        if amount is non-negative.
    """
    return True


def pay_sphinx(amount: float, method: str) -> bool:
    """Process a payment.

    :param amount: must be > 0 — the charge amount.
    :type amount: float
    :param method: the payment method; required.
    :type method: str
    :returns: True if the charge settled.
    :rtype: bool
    :raises ValueError: if amount is non-negative.
    """
    return True


def undocumented(x):
    return x
'''

THREE_DIALECT_PATH = "src/payments.py"
