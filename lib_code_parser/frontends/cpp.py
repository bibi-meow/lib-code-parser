"""C++ Frontend — libclang parse the source exactly once and emit a CAV envelope.

This is the SINGLE site in lib_code_parser/extractors/ + frontends/ that calls
libclang (``clang.cindex.Index.create().parse(...)``) for the C++ language path
(the AST-05 analog for C++). All cpp primitive/evaluation extractors consume the
parsed ``clang.cindex.TranslationUnit`` carried on ``cav.payload`` and never
re-parse. The raw bytes are carried on the CAV envelope (``cav.raw_content``) so
the component-diagram ``#include`` regex has the original source to scan.

libclang is loaded IN-PROCESS via ctypes here (D-06): the subprocess hardening in
the subprocess-only layer is NOT applied — that layer stays subprocess-only and this
module never imports or calls anything from it.

The D-07 runtime guard (``_ensure_libclang_ready``) runs ONCE at first parse via a
lazy ``_READY`` flag, so Python-only caller paths that never import this module never
load libclang (no-I/O-at-import preserved for the pure-Python path).

Unlike the Python frontend (whose ``config`` argument is accepted only for signature
parity), this frontend DOES consume ``config.compile_args`` — the caller-supplied
``-I``/``-std`` flags are forwarded to the libclang parse (LNG-05).

Implements: AST-05 (C++ analog), LNG-03, LNG-05, DET-02
Traces: AST-05, ARC-02, LNG-03, LNG-05, DET-02
"""

from __future__ import annotations

import importlib.metadata
import os
import sys

from clang.cindex import Index, TranslationUnit

from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["build_cav"]

_READY = False
_EXPECTED_VERSION = "18.1.1"


def _platform_install_hint() -> str:
    """Return a platform-specific install hint for a libclang load failure."""
    if sys.platform == "darwin":
        return (
            "macOS: install Xcode Command Line Tools (xcode-select --install) and "
            "confirm the arm64 libclang wheel is installed."
        )
    if sys.platform.startswith("win"):
        return (
            "Windows: ensure the MSVC runtime redistributable is installed; "
            "reinstall 'libclang==18.1.1'."
        )
    return (
        "Linux: the bundled libclang wheel should self-contain the shared lib; "
        "reinstall 'libclang==18.1.1' (match glibc/musl)."
    )


def _ensure_libclang_ready() -> None:
    """Run the D-07 libclang runtime guard once (idempotent via the _READY flag).

    Three jobs (LNG-03 / DET-02):
      1. DET-02 ABI pin: assert ``importlib.metadata.version("libclang") == "18.1.1"``.
         NEVER FFI-poke the libclang version function for the version
         (Pitfall 2 — that segfaults; stay on the metadata/high-level binding).
      2. LNG-03 override rejection: reject any caller ``Config.set_library_file(...)``
         (``Config.library_file is not None``) and assert ``Config.library_path``
         resolves into the bundled ``clang/native/`` directory.
      3. LNG-03 smoke test: ``Index.create()`` once; a dylib load failure raises a
         clear ``RuntimeError`` with the platform-specific install hint.
    """
    global _READY
    if _READY:
        return
    # DET-02: pinned ABI assertion via metadata (safe — never FFI-poke the version).
    ver = importlib.metadata.version("libclang")
    if ver != _EXPECTED_VERSION:
        raise RuntimeError(
            f"libclang ABI pin violated: expected {_EXPECTED_VERSION}, got {ver} (DET-02)."
        )
    from clang.cindex import Config

    # LNG-03: reject caller override of the bundled library.
    if Config.library_file is not None:
        raise RuntimeError(
            "Config.set_library_file override is rejected: the pinned bundled "
            f"libclang=={_EXPECTED_VERSION} must be used (DET-02 / LNG-03)."
        )
    lib_path = Config.library_path
    if not lib_path or "native" not in os.path.normpath(lib_path).split(os.sep):
        # The bundled wheel resolves library_path to .../clang/native/ (verified live).
        raise RuntimeError(
            f"libclang not resolving to the bundled wheel (library_path={lib_path!r}). "
            f"{_platform_install_hint()}"
        )
    try:
        Index.create()  # dylib load smoke test (LNG-03)
    except Exception as exc:  # dylib failed to load
        raise RuntimeError(f"libclang failed to load: {exc}. {_platform_install_hint()}") from exc
    _READY = True


def build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV:
    """Parse raw_content exactly once via libclang and wrap in a CAV envelope.

    AST-05 (C++ analog) single-parse invariant: this is the ONLY libclang parse
    call site for the C++ language path. cpp extractors consume ``cav.payload``
    (the already-parsed ``clang.cindex.TranslationUnit``) and never re-parse.

    LNG-05: parses with ``["-x", "c++", *config.compile_args]`` (compile_args
    defaults to ``["-std=c++17"]``) and ``PARSE_INCOMPLETE`` so an unresolved
    ``#include`` surfaces as a diagnostic warning carried on the TranslationUnit,
    NEVER as a raised exception. This function never inspects ``tu.diagnostics``
    to raise.
    """
    _ensure_libclang_ready()
    source = raw_content.decode("utf-8", errors="replace")
    args = ["-x", "c++", *config.compile_args]
    tu = Index.create().parse(
        path,
        args=args,
        unsaved_files=[(path, source)],
        options=TranslationUnit.PARSE_INCOMPLETE,
    )
    return CAV(
        language="cpp",
        path=path,
        payload=tu,
        raw_content=raw_content,
    )
