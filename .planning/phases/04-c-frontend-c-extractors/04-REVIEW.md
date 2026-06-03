---
phase: 04-c-frontend-c-extractors
reviewed: 2026-06-04T00:00:00Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - lib_code_parser/_dispatch.py
  - lib_code_parser/executor.py
  - lib_code_parser/_cpp_cursor.py
  - lib_code_parser/frontends/cpp.py
  - lib_code_parser/models/primitives/contracts.py
  - lib_code_parser/extractors/primitives/cpp_functions.py
  - lib_code_parser/extractors/primitives/cpp_callgraph.py
  - lib_code_parser/extractors/primitives/cpp_type_deps.py
  - lib_code_parser/extractors/primitives/cpp_contracts.py
  - lib_code_parser/extractors/evaluations/cpp_class_diagram.py
  - lib_code_parser/extractors/evaluations/cpp_component_diagram.py
  - lib_code_parser/extractors/evaluations/cpp_sequence_diagram.py
  - lib_code_parser/extractors/evaluations/cpp_package_diagram.py
  - lib_code_parser/extractors/evaluations/cpp_state_diagram.py
  - .github/workflows/ci.yml
  - tests/conftest.py
  - tests/unit/frontends/test_cpp_guard.py
  - tests/parity/test_cpp_python_schema_parity.py
  - tests/parity/test_trc03_cpp_parity.py
findings:
  critical: 2
  blocker: 2
  warning: 6
  info: 4
  total: 12
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-06-04
**Depth:** standard
**Files Reviewed:** 19
**Status:** issues_found

## Summary

This phase wires the C++ language path into the dispatch-driven executor: a libclang
frontend (`frontends/cpp.py`), a shared cursor-walk helper (`_cpp_cursor.py`), four cpp
primitives, five cpp evaluations, an additive `SourceKind="doxygen"` model value, and a
CI matrix. The Open-Closed dispatch registration, the additive-only model change, and the
schema-parity intent are all structurally sound, and most extractors correctly sort-on-exit
(DET-04). The libclang ABI guard correctly uses `importlib.metadata` and never FFI-pokes the
version.

However, the review surfaces two correctness defects that break the deterministic contract on
realistic inputs, two defects that undermine the guard/CI guarantees the phase claims to enforce,
and several robustness gaps. The two BLOCKER items concern non-determinism that survives the
sort-on-exit (USR-fallback ids depending on traversal, and unsorted free-function emission via the
dedup map), plus a guard-test that does not actually exercise the rejection path it claims. The
CI macOS step and the `_in_main_file` path-identity assumption are WARNING-level robustness gaps.

## Critical Issues

### CR-01: `qualified_node_id` USR fallback discards the namespace chain, breaking schema parity for anonymous decls

**File:** `lib_code_parser/_cpp_cursor.py:82-93`
**Issue:** When `cursor.spelling` is empty (anonymous struct/union/namespace), the function
returns `cursor.get_usr()` and **throws away the already-computed `parts` chain**. A USR is a
mangled string like `c:@S@...` — a completely different id namespace from the dotted
`a.b.Class` ids every other code path produces and merges against. The executor's contract
merger (`executor.py:106-108`) and every `node_id`-keyed dedup (`cpp_functions.by_id`,
`cpp_contracts.seen`) compare these ids for equality. An anonymous decl that should merge a
Doxygen `\pre` from `cpp_contracts` into its `FunctionNode.contracts` will silently fail to
merge because the two extractors can derive *different* USRs for related cursors (declaration
vs out-of-line definition do not always share a USR for anonymous entities). The Core Value
("code-side ids comparable with spec-side ids") is violated for any anonymous aggregate.
**Fix:** Anonymous decls should still be qualified by their enclosing chain and a stable
synthetic segment, not collapse to a raw USR. For example:
```python
own = cursor.spelling
if not own:
    # stable synthetic segment within the parent chain; keep dotted-id namespace
    own = f"<anonymous@{cursor.location.line}:{cursor.location.column}>"
parts.append(own)
return ".".join(parts)
```
If the USR is genuinely required as a last resort, append it as a chain segment
(`parts.append(cursor.get_usr())`) rather than returning it bare, so the id stays in the dotted
namespace and the parent context is preserved.

### CR-02: `_in_main_file` relies on byte-exact `file.name == path`, silently dropping ALL decls when the caller passes a normalized/absolute path

**File:** `lib_code_parser/_cpp_cursor.py:46-54` (consumed by every cpp extractor)
**Issue:** `f.name == path` is an exact string compare. libclang's `location.file.name` echoes
the spelling it was given, but it can normalize separators (e.g. on Windows, mixed `/` and `\`),
collapse `./` prefixes, or differ when the caller passes an absolute path while `path` was
relative. The `unsaved_files` key and the `parse()` first argument are both `path` here, so the
test fixtures (relative `relations.cpp`) pass — but a real caller in the spec-reviewer pipeline
passing `src/foo.cpp` vs `./src/foo.cpp`, or an absolute path with backslashes on Windows, will
make `f.name != path` for *every* cursor. The result is not a crash but a **silent empty
extraction**: zero functions, zero edges, zero contracts, while `execute()` returns a
well-formed empty `NormalizedArtifact`. A verifier downstream then sees "no architecture" and
mis-concludes the code is empty. Silent wrong-empty output is worse than a raise.
**Fix:** Compare on a normalized basis and guard against the empty-result footgun:
```python
import os
def _in_main_file(cursor: Cursor, path: str) -> bool:
    f = cursor.location.file
    if f is None:
        return False
    return os.path.normcase(os.path.normpath(f.name)) == os.path.normcase(os.path.normpath(path))
```
Additionally consider asserting (in the frontend, once) that at least the main-file cursor
matches, so a path-identity mismatch fails loudly instead of producing silent empty content.

## Blockers

### BL-01: `test_rejects_set_library_file_override` cannot exercise the rejection path — the guard is asserted by a test that passes vacuously

**File:** `tests/unit/frontends/test_cpp_guard.py:44-49` (guard at `frontends/cpp.py:86-90`)
**Issue:** The test `monkeypatch.setattr(clang.cindex.Config, "library_file", "/some/override")`.
But `clang.cindex.Config.library_file` is a **plain class attribute set by
`Config.set_library_file()`**; `monkeypatch.setattr` on the class attribute does change it, so
the test may pass — but the test is fragile and, more importantly, the *production* rejection it
claims to protect runs `_ensure_libclang_ready()` which first executes
`importlib.metadata.version("libclang")` and the real version check, then imports
`from clang.cindex import Config` and reads `Config.library_file`. On a machine where libclang is
already initialized (e.g. a prior test called `Index.create()` and set `_READY`/loaded the
library), `Config.library_file` semantics interact with the global libclang load state. The test
resets `cpp._READY = False` but does NOT reset `Config.library_file` after the test, leaking the
`/some/override` value into subsequent tests in the same process; the next test that calls
`_ensure_libclang_ready()` (`test_happy_path_sets_ready`) can then spuriously hit the
override-rejection branch depending on collection order. There is no teardown.
**Fix:** Use `monkeypatch` (auto-reverts) consistently and assert the leak cannot escape; verify
ordering independence:
```python
def test_rejects_set_library_file_override(monkeypatch):
    from clang.cindex import Config
    monkeypatch.setattr(Config, "library_file", "/some/override/libclang.so", raising=False)
    monkeypatch.setattr(cpp, "_READY", False)   # use monkeypatch so it auto-reverts
    with pytest.raises(RuntimeError, match="override is rejected"):
        cpp._ensure_libclang_ready()
```
Replace the manual `_reset_ready()` global mutation with `monkeypatch.setattr(cpp, "_READY", False)`
in all three tests so no global state leaks across tests.

### BL-02: ABI-pin guard order lets a bad `library_file` override or a load failure go unreported when `_READY` is already True

**File:** `lib_code_parser/frontends/cpp.py:74-102`
**Issue:** The guard short-circuits on `if _READY: return` (line 75-76). `_READY` is a
module-global set to `True` after the first successful parse. The override-rejection
(`Config.library_file is not None`) and the bundled-path assertion only run on the *first*
invocation. If any caller (or test) calls `set_library_file()` **after** the first successful
parse, every subsequent `build_cav` silently uses the overridden library with no re-check — the
LNG-03/DET-02 guarantee ("the pinned bundled libclang must be used") is only enforced once per
process, not per parse. Because libclang's `Config` is process-global and `Index.create()` binds
to whatever library is loaded, this is a real determinism/ABI hole, not theoretical.
**Fix:** The version pin and override rejection are cheap; run the override/path checks on every
call (not gated by `_READY`), and gate only the one-time `Index.create()` smoke test:
```python
def _ensure_libclang_ready() -> None:
    ver = importlib.metadata.version("libclang")
    if ver != _EXPECTED_VERSION:
        raise RuntimeError(...)
    from clang.cindex import Config
    if Config.library_file is not None:
        raise RuntimeError("Config.set_library_file override is rejected ...")
    # library_path assertion here too ...
    global _READY
    if _READY:
        return
    try:
        Index.create()
    except Exception as exc:
        raise RuntimeError(...) from exc
    _READY = True
```

## Warnings

### WR-01: macOS best-effort job runs `pytest` without a step-level guard; a hang/timeout in libclang load can stall the whole workflow despite `continue-on-error`

**File:** `.github/workflows/ci.yml:60-97`
**Issue:** `continue-on-error: true` at the job level correctly makes macOS non-gating for *failures*.
However, the smoke steps and `pytest` step have no `timeout-minutes`. `continue-on-error` does not
bound wall-clock; a libclang dylib load that hangs (a known failure mode on arm64 macOS wheels)
will run until the GitHub default 6-hour job timeout, consuming runner minutes and delaying the
overall workflow conclusion. The mandatory matrix has the same gap but there a hang would (correctly)
fail the gate eventually.
**Fix:** Add `timeout-minutes: 15` (or similar) to the `macos-arm64-best-effort` job and to the
mandatory `test` job so a hung libclang load fails fast rather than burning the default 6h budget.

### WR-02: `compile_args` is forwarded into libclang unvalidated — a caller-supplied flag is arbitrary process input to a native parser

**File:** `lib_code_parser/frontends/cpp.py:120-126` (`config.compile_args`)
**Issue:** `args = ["-x", "c++", *config.compile_args]` forwards caller flags verbatim to
`Index.parse`. While not a shell injection (no shell is invoked), libclang accepts flags such as
`-include <path>`, `-I <dir>` that cause it to **open files on disk**, and `-D` macros that change
the parse. This punctures the "pure function of `(raw_content, path, config)`" determinism claim:
two callers with identical bytes/path but a `-include /etc/...` flag get different output, and the
parse now performs filesystem I/O that the library's no-I/O charter says it does not. The default
`["-std=c++17"]` is fine; the risk is the open extension point.
**Fix:** Document explicitly that `compile_args` may cause libclang to read the filesystem
(breaking the no-I/O guarantee), and consider rejecting flags that take file paths
(`-include`, `-I`, `-isystem`) unless the caller opts in, or at minimum validate that
`compile_args` entries are from an allowlist of determinism-safe flags (`-std=`, `-D`, `-f...`).

### WR-03: `field_relation` strips `class `/`struct ` only, leaving qualified/template spellings unstripped — target ids drift

**File:** `lib_code_parser/_cpp_cursor.py:110-115`
**Issue:** `base = target.replace("class ", "").replace("struct ", "").split("::")[-1].strip(" *&")`.
This handles `class Foo` and `ns::Foo`, but a template member like `std::vector<Widget>` yields
`base = "vector<Widget>"` (the `split("::")[-1]` keeps `vector<Widget>` after the last `::`), and a
`const Foo&` yields `Foo` only if `const ` is also stripped — it is not, so a `const Foo &` pointee
spelling can leave `const Foo` as the base, never matching `known_classes`, so it falls to
`associates` instead of `aggregates`. The classification silently degrades on the most common C++
member shapes (const refs, templated owners).
**Fix:** Normalize the type spelling more robustly before the final segment split:
strip leading cv-qualifiers (`const `, `volatile `) and consider extracting the template base
(`vector<Widget>` → either `vector` or the inner `Widget`, per the intended D-04 rule). At minimum
strip `const `/`volatile ` so `const Foo&` resolves to `Foo`.

### WR-04: `cpp_callgraph._collect_callees` walks the whole subtree, double-counting calls in nested lambdas/local classes

**File:** `lib_code_parser/extractors/primitives/cpp_callgraph.py:45-51, 83-86`
**Issue:** `_collect_callees` does `cursor.walk_preorder()` over the entire function body, including
any nested lambda bodies or local class method bodies. Those nested callables are themselves visited
by the outer `walk_preorder` in `extract` (lines 70-86) and, if they have a `COMPOUND_STMT`, become
their own caller node too — so a call inside a lambda is attributed BOTH to the enclosing function
(via `_collect_callees`) AND to the lambda. This produces duplicate/over-counted edges relative to
the Python sibling, which flattens nested function bodies to the enclosing node but does NOT also
emit the nested function as a separate caller. The `seen_callers` guard only prevents re-counting
the *same node_id*, not the lambda-vs-enclosing double attribution.
**Fix:** Either (a) skip descending into nested callable bodies in `_collect_callees` (stop at the
first nested `CXX_METHOD`/`FUNCTION_DECL`/`LAMBDA_EXPR` boundary), matching the Python "flatten to
enclosing top-level/method" rule, or (b) explicitly document that lambdas are separate caller nodes
and ensure the Python sibling and parity tests agree. As written the two languages diverge.

### WR-05: `cpp_type_deps` uses `cursor.location.line` for member `source_line` but `_source_range`/contracts use `extent.start.line` — inconsistent line provenance

**File:** `lib_code_parser/extractors/primitives/cpp_type_deps.py:108` vs `cpp_functions.py:52-54`, `cpp_contracts.py:116`
**Issue:** The member-type `TypeDep.source_line` is `cursor.location.line` (the location of the
field's *name token*), whereas functions/contracts use `cursor.extent.start.line` (the start of the
whole decl). For a multi-line field declaration these differ. This is not wrong per se, but it is
an undocumented inconsistency that makes the DET-04 sort key `(source, target, kind, source_line)`
order by a different line basis than the sibling extractors, and complicates verifier diffing
against spec-side line provenance. Pick one basis library-wide.
**Fix:** Use `cursor.extent.start.line` for the member `source_line` for consistency with the other
cpp extractors, or document the deliberate difference in the module docstring.

### WR-06: `_DOXY_RE` lacks `re.MULTILINE` and captures a `condition` it then discards — but also matches mid-line `@pre` inside prose

**File:** `lib_code_parser/extractors/primitives/cpp_contracts.py:54, 119`
**Issue:** `_DOXY_RE = re.compile(r"[\\@](pre|post|invariant)\b[ \t]*(.*)", re.IGNORECASE)`. The
`\b` after the keyword guards trailing word chars, but there is no leading boundary: a comment line
like `// see foo@predicate` does not match (`pre` followed by `d` fails `\b`), good — but
`The @pre below` *does* match, treating prose mentioning `@pre` as a real precondition. Doxygen
commands must be the first non-whitespace token on a line (or after `*`). Without anchoring, any
prose `@pre`/`\post` in a docstring is falsely emitted as a contract entry. The captured
`_condition` group is discarded (`for marker, _condition in ...`), so the text is parsed but unused
— dead capture.
**Fix:** Anchor the command to start-of-line-after-optional-`*`/whitespace and add `re.MULTILINE`:
```python
_DOXY_RE = re.compile(r"^[ \t]*\*?[ \t]*[\\@](pre|post|invariant)\b[ \t]*(.*)$",
                      re.IGNORECASE | re.MULTILINE)
```
If the condition text is genuinely unused, drop the `(.*)` capture group entirely to make the
intent clear.

## Info

### IN-01: `_dispatch.py` import-time CodeContent-slot guard does not cover PRIMITIVES keys

**File:** `lib_code_parser/_dispatch.py:180-187`
**Issue:** The fail-fast guard (WR-01 comment) validates that every `EVALUATIONS` key maps to a
`CodeContent` field, but the executor `setattr`s only evaluation results by name. Primitive results
are assigned by an explicit `if/elif` chain in the executor (`executor.py:95-102`), so a misspelled
PRIMITIVES key (e.g. `"call_grph"`) is silently ignored — the `elif` chain has no `else`, so an
unknown primitive name runs the extractor and discards the result with no error. Consider an
analogous import-time assertion that every PRIMITIVES key is in a known set `{functions, call_graph,
type_deps, contracts}`.
**Fix:** Add `_KNOWN_PRIMITIVES = frozenset({...})` and assert each registered key is a member at
import time, mirroring the EVALUATIONS guard.

### IN-02: `.h` files are always parsed as `-x c++`, mis-handling C headers

**File:** `lib_code_parser/executor.py:29, 71-73` and `frontends/cpp.py:120`
**Issue:** `_CPP_EXTENSIONS` includes `.c` and `.h`. A `.c` (C, not C++) or a C-only `.h` is forced
through `-x c++`, which can change overload/name-mangling and reject valid C constructs (`restrict`,
implicit int). Determinism is preserved but fidelity is not. This matches the documented design
("Python and C++ from the start") but the C-vs-C++ ambiguity for `.h`/`.c` is undocumented.
**Fix:** Document that `.c`/`.h` are parsed as C++; if C fidelity matters, route `.c` to `-x c`.

### IN-03: `cpp_state_diagram` is a hardcoded empty extractor — dead computation kept only for "structural parity"

**File:** `lib_code_parser/extractors/evaluations/cpp_state_diagram.py:42-68`
**Issue:** The extractor asserts the payload type, then sorts three always-empty lists and returns
an empty `GraphModel`. The sort calls are no-ops. This is intentional per A1/D-05, but the function
performs a TU type-assert and three pointless sorts; a reader may mistake it for an unfinished stub.
**Fix:** Keep the behavior but tighten the comment to state unambiguously that this is a deliberate
v0.2.0 empty-shape contract (the docstring does say so; the sort no-ops could be dropped or replaced
with a single `return GraphModel()` plus a comment).

### IN-04: `_EXPECTED_VERSION` is duplicated from `pyproject.toml` with no single source of truth

**File:** `lib_code_parser/frontends/cpp.py:40` vs `pyproject.toml:28`
**Issue:** The ABI pin `"18.1.1"` is hardcoded in two places. A future bump to the pyproject pin
without updating `_EXPECTED_VERSION` makes the runtime guard reject the very wheel the package
installs, or vice versa. Currently consistent (verified), but drift-prone.
**Fix:** Read the expected version from `importlib.metadata` of the installed package's declared
requirement, or add a test asserting `frontends.cpp._EXPECTED_VERSION` equals the pin parsed from
`pyproject.toml` so drift fails CI.

---

_Reviewed: 2026-06-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
