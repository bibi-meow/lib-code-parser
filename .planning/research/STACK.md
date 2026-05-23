# Stack Research

**Domain:** Deterministic static code analysis library (Python + C++) producing architecture graphs schema-compatible with `lib-diagram-parser`
**Researched:** 2026-05-24
**Confidence:** HIGH (libclang, pyright, pylint/pyreverse, pydantic verified against PyPI + official docs; pyan3 verified against the 2026 revived PyPI package; spec-referenced `callgraph.py` / "ACL-2" investigated and refuted with sources)

---

## Executive Summary

The v0.1.0 baseline (AST-only) is sound but two spec references in `lib-code-parser.md` are **incorrect and block implementation**:

1. **"ACL-2"** — the spec uses this to mean "determinstic tooling layer," but **ACL2 is a Lisp theorem prover** (`https://www.cs.utexas.edu/~moore/acl2/`). It has nothing to do with Python call graphs. The term needs to be dropped or redefined in the spec before implementation starts.
2. **`callgraph.py`** — no PyPI package and no GitHub project matches this name as a deterministic Python static-call-graph tool. The closest matches are stale or non-deterministic. **Recommended replacement: `pyan3` v2.6.0** (revived in 2026, GPL v2, active maintenance, deterministic when input files are pre-sorted).

The rest of the stack is straightforward and well-established (libclang for C++, pyright for type resolution, pyreverse for class/package diagrams, pydantic v2 for the data model). The non-obvious design choices are all about **determinism preservation** — version pinning, subprocess wrapping, sort order, and locale control.

A license decision is required up front: `pyan3` is GPL v2. To keep `spec_reviewer_code_parser` permissively licensed, expose pyan3 only through an optional extra `[callgraph]` so users opt into the GPL surface.

---

## Recommended Stack

### Core Technologies (additions to v0.1.0 baseline)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `libclang` | `==18.1.1` (exact pin) | C++ AST via `clang.cindex`; provides type resolution, inheritance, templates | Only library that gives full C++ semantic resolution from Python. Ships prebuilt LLVM binary inside the wheel (no system LLVM needed). ABI is incompatible across versions — must be pinned exactly. tree-sitter-cpp is purely syntactic and cannot resolve types. |
| `pyright[nodejs]` | `==1.1.409` (exact pin) | Python static type resolution; produces `--outputjson` with fully-qualified types | Microsoft's reference type checker for Python. `--outputjson` is a stable contract. The `[nodejs]` extra bundles a private Node.js so determinism doesn't depend on the user's `node` version (or whether `node` exists at all). Pinning the version is critical because npm pyright auto-updates on every invocation otherwise. |
| `pyan3` | `==2.6.0` (exact pin, **optional extra `[callgraph]`**) | Python static call graph (caller→callee edges) | The only actively-maintained Python call-graph tool as of 2026. Revived from PyAn after PyCG was archived. Deterministic **only** when input file order is controlled (sort lexicographically before passing). Output is DOT — must be parsed by us into our `GraphEdge` schema. **GPL v2** — kept behind optional extra to keep core distribution permissive. |
| `pylint` | `>=3.3.0,<4.0` | Bundles `pyreverse` — class & package diagram extractor (Mermaid format since pylint 3.2) | `pyreverse` is the de-facto Python class-diagram tool; output formats include Mermaid (`-o mermaid`), DOT, PlantUML. Class + package diagrams without a separate dependency. Stable since 2003, ships with pylint. |
| `pydantic` | `>=2.13.0,<3.0` | Data model for `GraphNode`/`GraphEdge`/`GraphModel`/`GuardExpr` and `FunctionNode`/`CallGraph`/`TypeDep`/`ContractInfo`/`NormalizedArtifact` | Bump from v0.1.0's `>=2.0` floor to `>=2.13.0,<3.0` — 2.13 is the current stable line; `<3.0` cap avoids the future v3 breakage. Already in the dependency tree. |
| `lib-diagram-parser` | `>=0.1.0` | Direct import of `GraphNode`, `GraphEdge`, `GraphModel`, `GuardExpr` from `lib_diagram_parser.models` | Schema compatibility is the **Core Value** of this lib. Importing the sibling lib's pydantic models guarantees byte-for-byte schema match instead of duplicating definitions and risking drift. Verified — `lib_diagram_parser/models.py` contains all four exports as plain pydantic v2 `BaseModel` subclasses. |

### FSM Detection Targets (extraction targets — NOT runtime dependencies)

These libraries are **detected in user code by AST pattern matching**, not imported by us:

| Library | Detection Pattern | Status |
|---------|-------------------|--------|
| `transitions` v0.9.4 (MIT) | `Machine(model=..., states=[...], transitions=[...])` constructor call | Must-have — most common FSM library in Python |
| `python-statemachine` v3.1.2 (MIT) | `class X(StateMachine): foo = State(); bar = foo.to(baz) \| baz.to(foo)` chained `\|` operator | Must-have — second most common |
| Native `Enum` + transition methods | `class State(Enum): A=1; B=2` plus methods that mutate `self.state` between Enum values | Must-have — explicit pattern, vendor-agnostic |

If we ever needed to detect more (e.g., `statemachine`, `automat`), add new AST visitors — never add the FSM libraries as runtime dependencies.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydot` | `>=3.0` | Parse pyan3 DOT output into our schema | Only needed in the call-graph extractor; could be replaced by a small hand-written DOT parser if we want to avoid the dep |
| Python stdlib `ast` | (CPython 3.11+) | Primary Python parsing (already in v0.1.0) | Everything except call graph and type resolution |
| Python stdlib `subprocess` | (CPython 3.11+) | Invoking pyright / pyan3 / pyreverse | All external tool calls; **never** use `shell=True`; always pass list args |
| Python stdlib `tempfile` | (CPython 3.11+) | Write raw_content bytes to disk for subprocess tools that need file paths | pyright + pyan3 + pyreverse all require file paths, not stdin |
| Python stdlib `pathlib` | (CPython 3.11+) | Path normalization (forward-slash, lex sort) | All extractors |

### Development Tools (no change from v0.1.0 baseline)

| Tool | Purpose | Notes |
|------|---------|-------|
| `pytest` `>=8` | Test runner | Already in v0.1.0 |
| `pytest-cov` | Coverage | Already in v0.1.0 |
| `ruff` | Linter + formatter | Already in v0.1.0; `target-version = "py311"` |
| `pyright` (dev) | Type-check our own code | Same binary as the runtime tool; pin separately under `[dev]` |
| `setuptools >=68` + `wheel` | PEP 517 build | Already in v0.1.0 |

---

## Subprocess Wrapping Patterns

All external tools must be invoked through deterministic wrappers. Concrete patterns:

### pyright

```python
import json, subprocess, os
from pathlib import Path

def run_pyright(file_paths: list[Path], python_version: str = "3.11") -> dict:
    env = {**os.environ, "LC_ALL": "C", "PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409"}
    proc = subprocess.run(
        ["pyright", "--outputjson", "--pythonversion", python_version, *map(str, sorted(file_paths))],
        capture_output=True, text=True, env=env, check=False,
    )
    # pyright exits non-zero when type errors exist — that's fine, we only need the JSON
    return json.loads(proc.stdout)
```

Key points: `--outputjson` (stable schema), `--pythonversion` explicit (stubs differ across versions), lex-sorted file paths, `LC_ALL=C` to defeat localized messages, env-pin of pyright version.

### pyan3

```python
import subprocess, os
from pathlib import Path

def run_pyan3(file_paths: list[Path], out_dot: Path) -> None:
    env = {**os.environ, "LC_ALL": "C"}
    subprocess.run(
        ["pyan3", *map(str, sorted(file_paths)), "--dot", "--no-defines", "--colored=False"],
        stdout=out_dot.open("wb"), env=env, check=True,
    )
```

Key points: file paths **must be sorted lexicographically** — pyan3 emits edges in input order, and unsorted input produces a different DOT byte-for-byte. After parsing DOT, also sort nodes and edges before constructing `GraphModel`.

### libclang (in-process, not subprocess)

```python
from clang import cindex

def parse_cpp(raw_content: bytes, path: str, cpp_std: str = "c++17",
              include_paths: list[str] | None = None) -> cindex.TranslationUnit:
    # NEVER call cindex.Config.set_library_file — rely on the pinned libclang wheel's bundled binary
    idx = cindex.Index.create()  # fresh Index per call — no global state
    args = [f"-std={cpp_std}", "-x", "c++"]
    for inc in (include_paths or []):
        args.extend(["-I", inc])
    tu = idx.parse(path, args=args, unsaved_files=[(path, raw_content)])
    if tu is None:
        raise RuntimeError(f"libclang failed to parse {path}")
    return tu
```

Key points: in-process call (no subprocess), fresh `Index` per call (no global state), explicit `-std=` (defaults differ by platform), explicit `-x c++` (so `.h` files are parsed as C++, not C), use `unsaved_files` to feed raw bytes without touching disk.

### pyreverse

```python
import subprocess, os
from pathlib import Path

def run_pyreverse(file_paths: list[Path], out_dir: Path, project: str) -> Path:
    env = {**os.environ, "LC_ALL": "C"}
    subprocess.run(
        ["pyreverse", "-o", "mermaid", "-d", str(out_dir), "-p", project,
         *map(str, sorted(file_paths))],
        env=env, check=True,
    )
    return out_dir / f"classes_{project}.mmd"
```

Key points: explicit `-d` for output dir (otherwise pyreverse writes to `pwd`), explicit `-p` for project name (otherwise auto-generated from first arg = nondeterministic across invocations), sorted file paths.

---

## Determinism Analysis

This is the spine of the Core Value. Every external tool introduces at least one determinism risk:

| Risk | Cause | Mitigation |
|------|-------|------------|
| libclang version drift | ABI incompatibility across LLVM versions; bundled binary changes between wheel versions | Exact pin `libclang==18.1.1`; runtime assert `cindex.__version__`; **forbid** `Config.set_library_file()` (would let users substitute a different libclang) |
| libclang missing compile args | Default `-std=` differs per platform; missing `-I` paths cause unresolved types | Force `cpp_std` and `include_paths` from `ParserConfig.params`; default `cpp_std = "c++17"`; document that callers must supply include paths |
| pyright version drift | npm `pyright` auto-updates to latest on each invocation if user runs CLI directly | Pin via `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` env var + use the `pyright[nodejs]` extra so the bundled Node.js is used (not user's) |
| pyright Python version mismatch | Type stubs vary by Python target — same code yields different `TypeDep` for py3.10 vs py3.12 | Always pass `--pythonversion` explicitly; default to the caller's `ParserConfig.params["python_version"]` or `"3.11"` |
| pyan3 file order non-determinism | Output edges emitted in input file order | Sort `file_paths` lexicographically before passing to pyan3; after parsing DOT, also sort the resulting nodes and edges lists |
| pyreverse temp file naming | Output filename depends on `-p` flag; default project name is generated from first arg = pwd-dependent | Always pass explicit `-d output_dir` and `-p project_name` flags |
| CPython version differences | `ast` module's node shapes change subtly between minor versions (e.g., `ast.Constant` consolidation) | Keep `requires-python = ">=3.11"`; test matrix should cover 3.11 / 3.12 (3.13+ blocked by libclang wheel availability — see Version Compatibility) |
| OS path separators | Windows `\` vs POSIX `/` in module/file paths leaks into `node_id` strings | Normalize all paths to forward-slash before constructing `node_id` strings; canonical form: `"module/submodule.ClassName.method"` |
| Environment locale | LLVM/clang/pyright emit localized error messages when `LANG=ja_JP.UTF-8` etc., which appear in our error paths | Set `LC_ALL=C` in subprocess env for **all** external tool invocations |

---

## Alternatives Considered

| Recommended | Alternative | Why Rejected (and when to revisit) |
|-------------|-------------|-------------------------------------|
| `pyan3` v2.6.0 | `PyCG` (Vitalis et al., archived 2023) | Archived upstream — no fixes, no Python 3.12+ support, no roadmap. Revisit only if a maintained fork appears. |
| `pyan3` v2.6.0 | `code2flow` | Non-deterministic edge ordering; output format changes between versions; primarily designed for visualization, not programmatic consumption. |
| `pyan3` v2.6.0 | `JARVIS` (Salis, 2021 paper) | No PyPI package; research artifact only. Would require vendoring. |
| `libclang` 18.1.1 | `tree-sitter-cpp` | Purely syntactic — no type resolution, no template instantiation, no inheritance lookup. Architecture extraction needs semantic info. Revisit if we ever need only syntax (e.g., quick "find all class names"). |
| `libclang` 18.1.1 | Raw clang CLI (`clang -Xclang -ast-dump`) | Output format is unstable and human-oriented; would require fragile parsing. Python bindings (`clang.cindex`) give us a proper API. |
| `pyright` | `mypy` with `--output json` | mypy's JSON output schema is **not stable** across versions and is documented as such. pyright's `--outputjson` is the reference schema. Revisit if mypy ships a stability guarantee. |
| `pyright[nodejs]` | npm-installed `pyright` | Without `[nodejs]` extra, falls back to user's `node` — version drift, may not exist in sandboxed environments. |
| `pyreverse` (in pylint) | `py2puml`, `pylint-pyreverse` (standalone) | pyreverse ships **with pylint** (one less dep), is the original tool, and is the most stable. Standalone forks lag behind. |
| Direct schema duplication | Re-import from `lib-diagram-parser` | Duplicating `GraphNode`/`GraphEdge`/`GraphModel`/`GuardExpr` invites drift. The cost of a sibling-lib dependency is far less than the cost of schema divergence (which would break Layer M bisimulation). |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `tree-sitter-cpp` (for our use case) | Syntactic only — no type resolution, inheritance lookup, or template instantiation; cannot produce semantic graph edges | `libclang` 18.1.1 via `clang.cindex` |
| `PyCG` (archived 2023) | No active maintenance, no Python 3.12+ support, security/correctness fixes will never land | `pyan3` 2.6.0 |
| `code2flow` | Non-deterministic edge order; visualization-first tool; breaks our deterministic output contract | `pyan3` 2.6.0 |
| `pyright` without `[nodejs]` extra | Falls back to user's Node.js — version drift, may be absent | `pyright[nodejs]==1.1.409` |
| `libclang` without exact version pin | ABI incompatibility between LLVM versions silently changes AST node shapes and field availability | Exact pin `libclang==18.1.1` |
| `libclang` without explicit `-std=` flag | Default C++ standard varies by platform and clang build; same source produces different ASTs | Always pass `cpp_std` from `ParserConfig.params`; default `"c++17"` |
| `mypy --output json` | JSON output schema is unstable across mypy releases (documented as such) | `pyright --outputjson` (stable contract) |
| `transitions` / `python-statemachine` as **runtime** dependencies | We extract FSMs from user code; importing these libraries makes our parser depend on whatever the user uses | Detect AST patterns instead — never `import transitions` in our code |
| In-process libclang `Index` as a module-level global | `cindex.Index` holds caches and parser state; reusing across calls makes output depend on call order | Create a fresh `Index` per `execute()` call |
| The spec term "ACL-2" as a Python tooling reference | ACL2 is a Lisp theorem prover (`https://www.cs.utexas.edu/~moore/acl2/`) — nothing to do with Python call graphs; appears to be a spec authoring error | Drop the term entirely; replace with concrete tool names (pyan3, pyright, libclang) |
| The spec reference `callgraph.py` as a literal tool to call | No PyPI/GitHub project matches as a deterministic call-graph tool; the spec reference cannot be implemented as written | Replace with `pyan3` invocation (with the determinism mitigations above) |

---

## Stack Patterns by Variant

**If extracting Python:**
- Use `ast` (stdlib) for FunctionNode + Pydantic validators + FSM detection
- Use `pyan3` subprocess for CallGraph
- Use `pyright[nodejs]` subprocess for TypeDep
- Use `pyreverse` subprocess for class & package diagrams

**If extracting C++:**
- Use `libclang` in-process for everything (FunctionNode + CallGraph + TypeDep + class structure)
- libclang's `Cursor.get_children()` traversal yields all of FunctionNode, call relations (via `CursorKind.CALL_EXPR`), and type dependencies in one pass
- No subprocess wrapping needed — `clang.cindex` is a Python binding

**If the caller doesn't install the `[callgraph]` extra:**
- `CodeParserExecutor` should detect pyan3 absence (`importlib.util.find_spec("pyan")`) and emit `CallGraph(nodes=[], edges=[])` with a single `warnings` entry on `NormalizedArtifact` rather than raising
- This preserves the lib's "pure function" contract while making the GPL surface opt-in

**If the caller wants schema-only output (no external tools):**
- v0.1.0 baseline already covers this — `extract_contracts=False` plus the AST-only path
- v0.2.0 should keep this path working as a degraded mode for environments that can't install pyright/pyan3 (e.g., sandboxed CI)

---

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `libclang==18.1.1` | CPython 3.7 – 3.12 only | PyPI wheels are not published for 3.13+ as of 2026-05. **Caps our `requires-python` ceiling at 3.12.** If we want 3.13+ later, either wait for a new libclang release or fall back to subprocess `clang` CLI for 3.13+ users. |
| `pyright[nodejs]==1.1.409` | CPython 3.8+ | Wheels broad; the `[nodejs]` extra bundles its own Node.js so no system requirement. |
| `pyan3==2.6.0` | CPython 3.8+ | Requires `pydot>=1.4`, which we also use; no conflict. |
| `pylint>=3.3.0,<4.0` (pyreverse) | CPython 3.9+ | pyreverse Mermaid output requires pylint **>=3.2** — our `>=3.3.0` floor is safely above that. |
| `pydantic>=2.13.0,<3.0` | CPython 3.8+ | v2.13 is current stable; v3.0 is the breakage line. |
| `lib-diagram-parser>=0.1.0` | pydantic 2.x | Sibling lib; its `models.py` uses plain pydantic v2 `BaseModel` — verified compatible. |

**Bottom line on Python target:** Stay at `requires-python = ">=3.11,<3.13"`. The 3.13 ceiling is forced by libclang wheels. (v0.1.0 had `>=3.11` open-ended — needs tightening.)

---

## Roadmap Implications

**Phase 1 (Architecture) must include:**
1. **Spec correction commit** — fix `lib-code-parser.md` to drop "ACL-2" (factually wrong) and replace `callgraph.py` with `pyan3`. This is a prerequisite for implementation; otherwise downstream specs and tests will inherit the error.
2. **License decision** — confirm pyan3 GPL v2 via optional extra `[callgraph]` is acceptable, or accept GPL v2 for the whole package. (See Open Questions.)
3. **Subprocess wrapper module design** — single `lib_code_parser/external/` package holding `pyright_wrapper.py`, `pyan3_wrapper.py`, `pyreverse_wrapper.py`, each enforcing the determinism mitigations listed above. Wrappers are the only place where subprocess calls live.
4. **Determinism test harness** — golden-output tests that run each extractor twice on the same input and byte-compare the resulting `GraphModel`. This catches every determinism regression at CI time.

**Phase 2 (Implementation) order (recommended):**
1. `pyright` integration first — easiest (JSON output), no license concerns, immediately benefits TypeDep extraction
2. `pyreverse` next — class & package diagrams, no license concerns, Mermaid output is parseable
3. `pyan3` third — behind `[callgraph]` extra, requires DOT parsing; gated by license decision
4. `libclang` last — biggest new surface (in-process, fresh Index discipline, compile-arg passing); independent from the Python path so can run in parallel with steps 1–3

**Schema compatibility — confirmed:**
- Read `lib_diagram_parser/models.py` (lib-diagram-parser repo) — `GraphNode`, `GraphEdge`, `GraphModel`, `GuardExpr` are plain pydantic v2 `BaseModel` subclasses
- Direct import is safe and is the right approach (no schema duplication)
- New physical-side metadata should be added as **optional** fields on subclasses or extension models, never by modifying the imported types

---

## Open Questions for Orchestrator

1. **`callgraph.py` replacement** — Is `pyan3` v2.6.0 acceptable as the spec-referenced call-graph tool? If yes, spec needs a correction commit before Phase 1.
2. **License for `spec_reviewer_code_parser`** — Is pyan3's GPL v2 acceptable behind an optional extra `[callgraph]`, or do we need to find a permissively-licensed alternative (which would mean writing our own AST-based call-graph extractor)?
3. **Python target version** — Stay at `>=3.11`? Note that libclang wheels are unavailable for 3.13+, so the effective range is `>=3.11,<3.13`.
4. **C++ build flag source** — Should `cpp_std` / `include_paths` come only from `ParserConfig.params`, or should the executor auto-discover from a `compile_commands.json` if present in the project root? The latter is the standard libclang pattern but adds I/O (violating the lib's "no I/O" rule).

---

## Sources

- **PyPI: libclang** — `https://pypi.org/project/libclang/` (version 18.1.1, wheel matrix CPython 3.7–3.12) — HIGH
- **PyPI: pyright** — `https://pypi.org/project/pyright/` (version 1.1.409, `[nodejs]` extra documented) — HIGH
- **PyPI: pyan3** — `https://pypi.org/project/pyan3/` (version 2.6.0, GPL v2, revived 2026) — HIGH
- **PyPI: pylint** — `https://pypi.org/project/pylint/` (>=3.2 for Mermaid output in pyreverse) — HIGH
- **PyPI: pydantic** — `https://pypi.org/project/pydantic/` (v2.13 current stable line) — HIGH
- **PyPI: transitions** — `https://pypi.org/project/transitions/` (v0.9.4, MIT) — HIGH
- **PyPI: python-statemachine** — `https://pypi.org/project/python-statemachine/` (v3.1.2, MIT) — HIGH
- **Microsoft pyright docs** — command-line options including `--outputjson` and `--pythonversion` — HIGH
- **pylint pyreverse docs** — `https://pylint.pycqa.org/en/latest/pyreverse.html` (Mermaid `-o` output, `-d` and `-p` flags) — HIGH
- **LLVM clang Python bindings docs** — `https://libclang.readthedocs.io/` (`cindex.Index`, `Config`, `unsaved_files`) — HIGH
- **lib-diagram-parser source** — `lib_diagram_parser/models.py` (direct file read, confirmed GraphNode/GraphEdge/GraphModel/GuardExpr are pydantic v2 BaseModel) — HIGH
- **ACL2 official site** — `https://www.cs.utexas.edu/~moore/acl2/` (confirms ACL2 is a Lisp theorem prover, not a Python tool) — HIGH; spec's use of "ACL-2" is incorrect
- **PyCG repository status** — archived 2023, no active fork (verified GitHub) — HIGH (negative finding)
- **GitHub + PyPI search for `callgraph.py`** — no matching deterministic Python call-graph tool — HIGH (negative finding)

---

*Stack research for: lib-code-parser v0.2.0 (deterministic static code analysis for Python + C++)*
*Researched: 2026-05-24*
