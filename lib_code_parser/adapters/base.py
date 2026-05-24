"""Subprocess adapter base class + hardening helper.

All subprocess invocations in this library MUST go through ``run_subprocess()``.
The helper centralizes determinism guarantees (encoding, locale, hash seed,
timeout, cwd) and cross-platform pitfalls (Windows cp1252 decode, Popen
buffer-full deadlock).

The helper is intentionally transferable — sibling libs can copy it verbatim
if they need the same subprocess discipline; no internal state, pure-function
style. The ABC pattern reduces in-lib boilerplate for subclasses (Phase 2
PyrightAdapter and future tool adapters).

Hardening invariants enforced (DET-05, Pitfall 3, Pitfall 13):

1. ``encoding="utf-8"`` — never depend on platform default codec (cp1252 on Windows)
2. ``errors="replace"`` — tolerate stray bytes from external tools without crashing
3. Deterministic env (``LC_ALL=C``, ``LANG=C``, ``PYTHONHASHSEED=0``,
   ``PYTHONIOENCODING=utf-8``) — kill locale + dict/set order non-determinism
4. ``capture_output=True`` (via ``subprocess.run``) — never block on full pipe;
   the low-level ``Popen`` API is forbidden in this module (use ``subprocess.run`` only)
5. ``shell=False`` — argv is always a ``Sequence[str]``; no shell injection
6. Explicit ``timeout`` (default 60.0) + explicit ``cwd`` (required) — never hang;
   never inherit ``os.getcwd()`` silently

Traces: ARC-03, DET-05.
"""

from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from pydantic import BaseModel

__all__ = ["run_subprocess", "SubprocessAdapter"]


# Determinism env (DET-05).
#   LC_ALL=C, LANG=C   — kills locale-dependent text formatting (sort order,
#                        date/time strings, numeric separators)
#   PYTHONHASHSEED=0   — kills set/dict iteration order non-determinism
#   PYTHONIOENCODING=utf-8 — forces UTF-8 on any child Python interpreter
_DETERMINISTIC_ENV: dict[str, str] = {
    "LC_ALL": "C",
    "LANG": "C",
    "PYTHONHASHSEED": "0",
    "PYTHONIOENCODING": "utf-8",
}


def run_subprocess(
    argv: Sequence[str],
    *,
    cwd: str,
    timeout: float = 60.0,
    extra_env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with deterministic hardening.

    Enforces every invariant required by DET-05 and the pitfalls catalog:

    * ``encoding="utf-8"`` (Pitfall 13 — Windows cp1252 default would corrupt
      non-ASCII paths and tool output)
    * ``errors="replace"`` — degrade gracefully on stray bytes; never raise
      ``UnicodeDecodeError`` from the helper itself
    * Deterministic env merged onto a copy of ``os.environ`` (LC_ALL=C,
      LANG=C, PYTHONHASHSEED=0, PYTHONIOENCODING=utf-8) — applied
      unconditionally on every call; caller-supplied ``extra_env`` is layered
      on top last (caller wins for non-deterministic keys it explicitly sets)
    * ``capture_output=True`` (Pitfall 3 — ``Popen`` + ``wait()`` + later
      ``stdout.read()`` deadlocks on full pipe buffer; ``subprocess.run``
      drains both streams concurrently)
    * ``shell=False`` — argv is a ``Sequence[str]``; no shell injection
    * ``timeout`` (default 60.0) — never hang forever
    * ``check=False`` — return the ``CompletedProcess`` even on non-zero exit;
      caller decides what to do (different adapters have different policies)

    This function NEVER calls the low-level ``Popen`` API directly; only
    ``subprocess.run``. Sibling libs may copy this helper verbatim.

    Required keyword args:
        cwd: explicit working directory (no inherited ``os.getcwd()``).

    Optional keyword args:
        timeout: seconds before ``subprocess.TimeoutExpired`` is raised
            (default 60.0).
        extra_env: extra env vars to overlay on top of the deterministic env.

    Returns:
        ``subprocess.CompletedProcess[str]`` — ``stdout``/``stderr`` are
        already-decoded ``str``.

    Raises:
        subprocess.TimeoutExpired: if the child does not exit within
            ``timeout`` seconds.
        OSError: if argv[0] cannot be located / executed.

    Traces: ARC-03, DET-05.
    """
    env: dict[str, str] = dict(os.environ)
    env.update(_DETERMINISTIC_ENV)
    if extra_env is not None:
        env.update(extra_env)
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
        check=False,
    )


class SubprocessAdapter(ABC):
    """Abstract base for any subprocess-based adapter (pyright, future tools).

    Subclasses implement two methods:

    1. ``tool_argv(target_path)`` — build the argv list (always a list/sequence,
       never a single string; ``shell=False`` is enforced by the helper).
    2. ``parse_output(stdout, stderr, returncode)`` — convert raw subprocess
       output into a typed Pydantic ``BaseModel`` (Pitfall 4 — defend against
       schema drift by parsing into a closed model rather than ``dict``).

    The concrete ``execute()`` method drives the run via ``run_subprocess()``
    and delegates to the subclass for argv + output parsing. Subclasses
    therefore never bypass the hardening contract — that is the whole point
    of D-09.

    Traces: ARC-03, DET-05.
    """

    @abstractmethod
    def tool_argv(self, target_path: str) -> Sequence[str]:
        """Return the argv list for invoking the tool against ``target_path``.

        Must be a list / sequence of strings. Never a single string (shell=False).
        """
        ...

    @abstractmethod
    def parse_output(self, stdout: str, stderr: str, returncode: int) -> BaseModel:
        """Parse raw subprocess output into a typed Pydantic model."""
        ...

    def execute(
        self,
        target_path: str,
        *,
        cwd: str,
        timeout: float = 60.0,
        extra_env: Mapping[str, str] | None = None,
    ) -> BaseModel:
        """Template method — fetch argv from subclass, run via hardened helper,
        delegate parse to subclass.
        """
        result = run_subprocess(
            self.tool_argv(target_path),
            cwd=cwd,
            timeout=timeout,
            extra_env=extra_env,
        )
        return self.parse_output(result.stdout, result.stderr, result.returncode)
