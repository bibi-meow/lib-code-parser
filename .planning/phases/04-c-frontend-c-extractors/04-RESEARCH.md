# Phase 4: C++ Frontend + C++ Extractors - Research

**Researched:** 2026-06-02
**Domain:** libclang (clang.cindex) C++ static analysis, schema-parity extraction, multi-platform CI, in-process ABI guarding
**Confidence:** HIGH (libclang API + wheel availability + cursor behavior empirically verified live in this environment; dispatch migration verified against actual codebase)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**A: C++ extractor dispatch (resolves locked-contract collision)**
- **D-01:** Introduce a language dimension into dispatch **once**. Nest `FRONTENDS` / `PRIMITIVES` / `EVALUATIONS` into `dict[language, dict[name, fn]]`; executor selects the extractor set via `cav.language` (`for name, fn in EVALUATIONS[cav.language].items()`).
- **D-02:** This guarantees (1) existing Python extractor files are byte-unchanged (invariants #1/#2; C++ is all new files), (2) cpp extractors run only on cpp CAV (preserves DET-01), (3) within a language dimension dispatch is still append-only (future Java = add `["java"]`), (4) output slot names are common across languages (`class_diagram` etc.) so LNG-04 parity is natural.
- **D-03:** Explicitly revise the Phase-1 "executor body does not grow" invariant **for the language axis only** (executor 1 line + `_dispatch.py` one-time nesting). Add the language-dimension procedure and "language keys are append-only" invariant to `docs/09-extending.md`.

**B: C++ schema-parity fidelity boundary (v0.2.0 must-have vs v0.3.0 defer)**
- **D-04:** v0.2.0 must-have = **struct / class / free function / method / namespace / include / inheritance (incl. multiple) / member type deps**. composition vs aggregation = **value member = composes / pointer·reference = aggregates / unresolvable = associates** (deterministic rule, C++ analog of the Python rule).
- **D-05:** **template / macro expansion + overload resolution completeness is best-effort.** Unresolved `#include` → `diagnostics` warning, never a parse error (SC#3, LNG-05). Full fidelity (complete template instantiation etc.) is a v0.3.0 candidate.

**C: libclang determinism contract + import-time runtime guard location**
- **D-06:** libclang lives in **`frontends/cpp.py` (in-process ctypes), NOT in `adapters/`**. `adapters/` is subprocess-only. libclang determinism is guaranteed by **deterministic cursor traversal order + sort-on-exit (same as DET-04) + DET-02 ABI assertion** — NOT subprocess env hardening.
- **D-07:** runtime guard (`cindex.Index.create()` once + bundled libclang 18.1.1 ABI verification + reject `Config.set_library_file` override; LNG-03/DET-02) runs **once at C++ frontend module import time** (lazy load); Python-only caller paths never load libclang (no-I/O-at-import preserved). LNG-03's "library import triggers guard" = "C++ frontend module import." SC#2 `import lib_code_parser` guard requirement is met on the execution path that includes the cpp frontend (eager-import from `__init__.py` is allowed if needed — decided at implementation time).

**D: Doxygen contract SourceKind extension (SPC-03)**
- **D-08:** Add Doxygen value(s) **additively** to the `SourceKind` Literal in `models/primitives/contracts.py` (first candidate: single `"doxygen"` + reuse `ContractEntry.kind` for pre/post/invariant; details = agent autonomy). Deleting/renaming the existing 4 values is forbidden. Add to `docs/09-extending.md`: "additive Literal extension allowed; deletion/rename forbidden" (same policy as EdgeKind MAJOR).
- **D-09:** C++ Doxygen contracts reuse the existing `CodeContent.contracts` slot — no new field (parity). Emit `\pre`/`\post`/`\invariant` in the same `ContractInfo`/`ContractEntry` schema. Verify in test that `Traces: REQ-ID, US-NN` tag extraction behaves identically for Python docstrings and C++ Doxygen comments (TRC-03 parity).

### Claude's Discretion (lower-level implementation — user does not touch)
- libclang cursor traversal implementation pattern, C++ fixture corpus selection, individual edge/type decision-rule details
- composition/aggregation C++ boundary-case interpretation, namespace → module/package mapping details
- Doxygen comment parser method (regex / libclang comment API), final `SourceKind` single-value vs 3-value choice
- test strategy (parity test primary/backup composition), CI matrix YAML concrete structure
- `_dispatch.py` nesting concrete type aliases + migration increments (existing Python entry migration procedure)

### Deferred Ideas (OUT OF SCOPE)
- **template/macro full-expansion fidelity** → v0.3.0 (triggering: verifier reports parity gaps on template-heavy C++)
- **LNG-02-FULL (macOS arm64 full guarantee)** → v0.3.0 (v0.2.0 stays continue-on-error best-effort)
- **DET-01 snapshot test / SCH-04 cross-lib schema compat / DOC-02 README compat matrix** → Phase 5. Phase 4 delivers per-extractor unit parity only.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LNG-01 | pip install + run on CPython 3.11–3.14 on Linux x86_64/aarch64 + Windows x86_64 (mandatory CI matrix all-green) | §Standard Stack (wheel availability verified for all platforms), §CI Matrix Bring-Up |
| LNG-02 | pip install on macOS arm64 + Python 3.13+; runtime observed not guaranteed (continue-on-error) | §CI Matrix Bring-Up (best-effort job), SP-3 verdict = ship-best-effort |
| LNG-03 | `import` triggers runtime guard calling `cindex.Index.create()` once; dylib load failure → clear `RuntimeError` w/ platform-specific install instructions | §libclang Runtime Guard (D-07), §Code Examples (guard skeleton) |
| LNG-04 | All AST primitives + diagram extractors work on C++ via libclang==18.1.1 with output schema parity to Python | §C++ AST → Schema-Parity Primitives, §All 5 Diagram Extractors, §Architectural Responsibility Map |
| LNG-05 | C++ extractors accept caller-supplied `compile_args` (default `["-std=c++17"]`); unresolved `#include` → warnings not errors | §libclang Parse Contract (empirically verified: missing include = sev-4 diagnostic, parse still completes) |
| SPC-03 | Extract C++ function/class spec via Doxygen `\pre`/`\post`/`\invariant` (Python/C++ symmetric schema) | §Doxygen Contract Extraction (regex-on-raw_comment verified), §SourceKind extension (D-08) |
| DET-02 | `libclang==18.1.1` exact pin enforced; runtime ABI assertion at import rejects `Config.set_library_file` override + verifies bundled version via `cindex.Config.library_path` | §libclang Runtime Guard, §Common Pitfalls (Pitfall 2: never FFI-poke version) |
</phase_requirements>

## Summary

Phase 4 brings up the C++ track behind the CAV boundary locked in Phase 1. The single highest-leverage discovery from the prior `/gsd:discuss-phase` session — already locked as Decision A — is that the **flat dispatch contract is structurally incapable of hosting a second language without violating Open-Closed invariants #1/#2/#4 or breaking DET-01/LNG-04**. The resolution (D-01/02/03) is to nest the three dispatch dicts once into `dict[language, dict[name, fn]]`. This is a one-time structural change touching exactly two files (`_dispatch.py` nest + `executor.py` one-line `cav.language` selection) and zero existing extractor files.

Every load-bearing technical assumption was **verified live in this environment** against the actually-installed `libclang==18.1.1`: the wheel ships for all required platforms (manylinux2010_x86_64, manylinux2014_aarch64, win_amd64, macosx_11_0_arm64, plus musllinux/win_arm64); `clang.cindex` exposes every API the plan needs (`Config.library_path`, `Cursor.raw_comment`, `CXX_BASE_SPECIFIER`, `FIELD_DECL.type.kind`, `get_usr()`, `diagnostics`); a missing `#include` produces a severity-4 diagnostic **but the cursor tree is still fully built** (so LNG-05 "warn not error" is mechanically achievable); and the deterministic composition/aggregation rule maps cleanly onto `TypeKind.POINTER`/`LVALUEREFERENCE` (aggregates) vs `ELABORATED`/record value (composes). Two real segfaults were triggered in testing by poking libclang's FFI function signatures directly — documented as Pitfall 2, with `importlib.metadata.version("libclang")` (verified to return `"18.1.1"` cleanly) as the safe DET-02 assertion.

**Primary recommendation:** Nest the dispatch dicts (D-01) as the first plan; build `frontends/cpp.py` with the lazy import-time guard (D-07) using `importlib.metadata` for the ABI assertion (NOT FFI); write all C++ extractors as new files emitting the existing Pydantic shapes with `get_usr()`-derived stable `node_id`s and DET-04 sort-on-exit; extract Doxygen contracts via regex on `Cursor.raw_comment` (the structured comment API is not reliably exposed in the bindings); and graduate the CI matrix to mandatory Linux x86_64/aarch64 + Windows x86_64 × Python 3.11–3.14 with macOS arm64 staying `continue-on-error: true`.

## Architectural Responsibility Map

This is a single pure-Python library (no client/server/DB tiers). "Tier" here = the layered module architecture locked in Phase 1. The map below sanity-checks that each Phase-4 capability lands in the correct layer.

| Capability | Primary Layer | Secondary Layer | Rationale |
|------------|---------------|-----------------|-----------|
| C++ parse → CAV | `frontends/cpp.py` | — | Single-parse site (mirrors `frontends/python.py`); libclang lives here per D-06 (in-process, NOT adapters/) |
| libclang ABI guard / dylib load | `frontends/cpp.py` (module-import time) | `__init__.py` (optional eager trigger) | D-07: lazy at cpp-frontend import; Python-only path never loads libclang (no-I/O-at-import) |
| C++ AST primitives (functions/callgraph/type_deps/contracts) | `extractors/primitives/cpp_*.py` (new files) | `models/primitives/*` (unchanged shapes) | Invariant #1: new files only; reuse existing Pydantic models for LNG-04 parity |
| C++ 5 diagrams | `extractors/evaluations/cpp_*.py` (new files) | `models/evaluations/graph_base.py` (unchanged) | Invariant #2: new files only; same `GraphNode/GraphEdge/GraphModel` slots |
| Doxygen contract extraction | `extractors/primitives/cpp_contracts.py` (new) | `models/primitives/contracts.py` (additive `SourceKind` value, D-08) | D-09: reuse `CodeContent.contracts` slot; additive Literal only |
| Language dimension dispatch | `_dispatch.py` (one-time nest) + `executor.py` (1 line) | `docs/09-extending.md` (invariant doc) | D-01/D-03: the ONLY existing files Phase 4 modifies |
| Platform CI matrix | `.github/workflows/ci.yml` | `pyproject.toml` (libclang already pinned) | LNG-01/02: graduate SP-3 best-effort job to mandatory matrix |

**Misassignment guard:** No extractor should branch on `cav.language` internally (invariant #2 anti-pattern). Language selection happens once, at the executor's dict-of-dicts walk. A cpp extractor `assert isinstance(cav.payload, clang.cindex.TranslationUnit)` is the correct language guard — it documents the precondition the nested dispatch already enforces.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `libclang` | `==18.1.1` (exact pin) | C++ parsing via `clang.cindex` Python bindings + bundled native libclang shared lib | [CITED: PROJECT.md Key Decision] The only PyPI package that ships a self-contained static-linked libclang for all target platforms without a system LLVM install. Pinned for ABI/output determinism (DET-02). `[VERIFIED: PyPI registry — pip index versions libclang shows 18.1.1 is latest; importlib.metadata.version('libclang')=='18.1.1' in this env]` |
| stdlib `clang.cindex` | (ships in libclang wheel) | `Index`, `TranslationUnit`, `Cursor`, `CursorKind`, `TypeKind`, `Config`, `Diagnostic` | [VERIFIED: live import in this env] All required API surface confirmed present (see §libclang API Surface) |
| stdlib `re` | — | Doxygen `\pre`/`\post`/`\invariant` + `Traces:` regex on `raw_comment` | [VERIFIED: codebase] Same TRC-03 regex already used in `extractors/primitives/functions.py` |
| stdlib `importlib.metadata` | — | DET-02 ABI version assertion (`version("libclang") == "18.1.1"`) | [VERIFIED: live — returns "18.1.1" cleanly without FFI risk] |
| `pydantic` | `>=2.13.0,<3.0` | Output models (reused unchanged — LNG-04 parity) | [VERIFIED: pyproject.toml] Already the project's model layer |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | `>=8` | parity / determinism / guard tests | Already the project test runner |
| `pytest-cov`, `ruff`, `pyright` | (dev extras) | lint / format / typecheck | CI gates (already present in `ci.yml`) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `libclang` (sighingnow) | `clang` PyPI package | [CITED: REQUIREMENTS.md Out of Scope] `clang` requires a system-installed libclang → loses self-containment. **Forbidden** by project constraints. |
| in-process ctypes | libclang via subprocess | D-06 locked: subprocess hardening is for `adapters/` only; libclang is in-process. The segfault risk (Pitfall 2) is mitigated by never poking FFI, not by isolation. |
| `Cursor` structured comment API (`FullComment`) | regex on `raw_comment` | [VERIFIED: live — `brief_comment` returns `''`; full structured comment AST is not reliably exposed in the Python bindings] Regex on `raw_comment` is the deterministic, binding-stable choice. |

**Installation:**
```bash
pip install "libclang==18.1.1"   # already declared in pyproject.toml [project.optional-dependencies] dev
```

**Version verification (performed this session):**
```
pip index versions libclang  →  libclang (18.1.1)  Available: 18.1.1, 17.0.6, ...  INSTALLED: 18.1.1  LATEST: 18.1.1
importlib.metadata.version("libclang")  →  "18.1.1"
```

## Package Legitimacy Audit

> slopcheck could not be installed in this sandbox (no network for pip install of slopcheck). Per the graceful-degradation rule, packages are tagged `[ASSUMED]` for slopcheck status. However, `libclang` is **already a locked, pinned project dependency** (PROJECT.md Key Decision, pyproject.toml, Phase-1 SP-3 spike) — it is NOT a new package introduced by this research, so the slopsquatting risk is nil. It was verified via PyPI registry (correct ecosystem) and live import.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `libclang` | PyPI | 9.x (1.x since 2019; 18.1.1 published 2024) | ~10M+/mo (clang bindings, widely used) | github.com/sighingnow/libclang | [ASSUMED — slopcheck unavailable; mitigated: pre-locked project dep, verified via PyPI + live import] | Approved (already pinned) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*Phase 4 introduces **no new** third-party packages — `libclang==18.1.1` was already locked in Phase 1. No `checkpoint:human-verify` gate is needed for a dependency the user already approved and pinned; the planner may treat it as a confirmed decision.*

## Architecture Patterns

### System Architecture Diagram

```
                      execute(config, raw_content, path)
                                   │
                          config.enabled? ──no──► empty CodeContent
                                   │ yes
                  language = config.language; if suffix∈{.cpp,.cc,.c,.h,.hpp} → "cpp"
                                   │
                  ┌────────────────┴─────────────────┐
                  │  D-01 nested dispatch selection    │
                  │  FRONTENDS[language] (one fn)       │
                  └────────────────┬─────────────────┘
                                   │
            language=="python"     │     language=="cpp"
            frontends.python ◄──────┴──────► frontends.cpp
            ast.parse() once              [import-time guard fired once: D-07]
                  │                        Index.create(); TU.from_source(unsaved_files)
                  ▼                              │  (compile_args from config; LNG-05)
            CAV(payload=ast.Module)         CAV(payload=TranslationUnit)
                  │                              │   diagnostics carried for LNG-05 warnings
                  └────────────────┬─────────────┘
                                   ▼
                  for name, fn in PRIMITIVES[language].items():
                     fn(cav, config) → functions / call_graph / type_deps / contracts
                                   │
                  ContractInfo merger → FunctionNode.contracts (existing logic)
                                   │
                  for name, fn in EVALUATIONS[language].items():
                     fn(cav, config) → setattr(content, name, GraphModel/spec)
                                   │  (5 diagrams + 2 specs; cpp set is schema-parity new files)
                                   ▼
                  NormalizedArtifact[CodeContent]  (byte-identical shape across languages → LNG-04)
```

The diagram's key property for LNG-04: both language paths terminate in the **same `CodeContent` slots** (`functions`, `class_diagram`, `contracts`, …). Parity is structural, not coincidental — the slot names are the dict keys, common across language dimensions (D-02).

### Recommended Project Structure (new files only — invariants #1/#2)
```
lib_code_parser/
├── frontends/
│   └── cpp.py                          # NEW: build_cav() via libclang + D-07 guard
├── extractors/
│   ├── primitives/
│   │   ├── cpp_functions.py            # NEW: FunctionNode from cursors
│   │   ├── cpp_callgraph.py            # NEW: CallGraph from CALL_EXPR
│   │   ├── cpp_type_deps.py            # NEW: TypeDep from #include + member types
│   │   └── cpp_contracts.py            # NEW: Doxygen ContractInfo (SPC-03)
│   └── evaluations/
│       ├── cpp_class_diagram.py        # NEW: inheritance + composes/aggregates/associates
│       ├── cpp_sequence_diagram.py     # NEW: from cpp callgraph
│       ├── cpp_component_diagram.py    # NEW: from #include deps
│       ├── cpp_package_diagram.py      # NEW: namespace/path → packages
│       └── cpp_state_diagram.py        # NEW: explicit FSM (best-effort; likely minimal)
├── _cpp_cursor.py                      # NEW (optional): shared cursor-walk helpers (USR id, main-file filter, sort keys)
├── _dispatch.py                        # MODIFIED ONCE: nest into dict[lang, dict[name, fn]] (D-01)
└── executor.py                         # MODIFIED ONE LINE: select [cav.language] (D-03)
```

### Pattern 1: Nested language dispatch (D-01) — the one-time structural change
**What:** Convert `FRONTENDS: dict[str, FrontendFn]` → `dict[str, dict[str, FrontendFn]]` keyed by language. Migrate existing Python entries under `["python"]`; add `["cpp"]` entries. Executor walks `PRIMITIVES[cav.language]` / `EVALUATIONS[cav.language]`.
**When to use:** Once, in the first Phase-4 plan, before any cpp extractor is written (everything else depends on the nested shape existing).
**Migration shape (verified against current `_dispatch.py`):**
```python
# BEFORE (current):  PRIMITIVES["functions"] = _extract_functions
# AFTER (D-01):
FRONTENDS:   dict[str, dict[str, FrontendFn]]   = {"python": {}, "cpp": {}}
PRIMITIVES:  dict[str, dict[str, PrimitiveFn]]  = {"python": {}, "cpp": {}}
EVALUATIONS: dict[str, dict[str, EvaluationFn]] = {"python": {}, "cpp": {}}

# existing Python registrations move under ["python"] (values byte-unchanged):
PRIMITIVES["python"]["functions"]  = _extract_functions
EVALUATIONS["python"]["class_diagram"] = _extract_class_diagram   # ... etc.

# new cpp registrations:
FRONTENDS["cpp"]["build_cav"]      = _build_cav_cpp   # or no name; FRONTENDS is keyed by language only — see note
PRIMITIVES["cpp"]["functions"]     = _extract_cpp_functions
EVALUATIONS["cpp"]["class_diagram"] = _extract_cpp_class_diagram   # ... etc.
```
**Note on FRONTENDS shape:** FRONTENDS is already keyed by language (`FRONTENDS["python"] = build_cav`). It does NOT need a second nesting level — one frontend per language. Keep `FRONTENDS: dict[str, FrontendFn]` and add `FRONTENDS["cpp"] = _build_cav_cpp`. Only `PRIMITIVES` and `EVALUATIONS` (which are keyed by aspect-name) gain the language dimension. **This asymmetry is a real planning detail** — the executor already does `FRONTENDS[language]` correctly today (executor.py L83); only the primitive/evaluation walks (L91, L121) change to `PRIMITIVES[cav.language].items()` / `EVALUATIONS[cav.language].items()`.

**Registration-time slot guard (extend per D-01):** the current import-time guard (`_dispatch.py` L106-112) asserts every EVALUATIONS key has a matching `CodeContent` field. Extend it to iterate over both language dimensions: `for lang in EVALUATIONS: for key in EVALUATIONS[lang]: assert key in _CONTENT_FIELDS`. The slot names are shared, so cpp keys validate against the same `CodeContent` fields (this is exactly what makes LNG-04 parity automatic).

### Pattern 2: C++ frontend = single-parse CAV (mirror of `frontends/python.py`)
**What:** `build_cav(raw_content, path, config) -> CAV` parses once via libclang, stashes the `TranslationUnit` as `cav.payload`, carries `raw_content`, sets `language="cpp"`.
**When to use:** the sole libclang parse site (AST-05 single-parse invariant, C++ side).
**Example (verified API):**
```python
# Source: live-verified clang.cindex API in this env + frontends/python.py mirror
from clang.cindex import Index, TranslationUnit

def build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV:
    _ensure_libclang_ready()                      # D-07 guard (idempotent; real work once)
    source = raw_content.decode("utf-8", errors="replace")
    args = ["-x", "c++", *config.compile_args]    # default compile_args = ["-std=c++17"] (LNG-05)
    index = Index.create()
    tu = index.parse(
        path, args=args,
        unsaved_files=[(path, source)],           # in-memory parse — no disk I/O (caller-agnostic)
        options=TranslationUnit.PARSE_INCOMPLETE, # tolerate missing includes → still build cursor tree
    )
    # LNG-05: surface unresolved-include + other diagnostics as warnings, never raise.
    # Carry them onto CAV (additive field) or recompute in extractors from tu.diagnostics.
    return CAV(language="cpp", path=path, payload=tu, raw_content=raw_content)
```
**Empirical confirmation:** with a missing `#include "missing_header.h"`, `tu.diagnostics` contained one `severity=4` (fatal) entry `"'missing_header.h' file not found"` **yet the full cursor tree for the rest of the file was still produced** — structs, classes, methods, bases all present. So "warn not error" (LNG-05) is achievable by simply not raising on diagnostics.

### Pattern 3: Deterministic cursor walk + main-file filter + USR node_id
**What:** Walk `tu.cursor.get_children()` recursively; **filter to the main file** (`cursor.location.file.name == path`) to drop builtin/header decls; derive `node_id` from `get_usr()` or a dotted namespace path; sort all output by composite key on exit (DET-04).
**When to use:** every cpp extractor.
**Critical determinism detail (verified):** Do **NOT** pass `PARSE_DETAILED_PROCESSING_RECORD` — it floods the cursor tree with ~hundreds of builtin `MACRO_DEFINITION` cursors (`__llvm__`, `__clang__`, …). The default parse produces a clean tree. Always filter children by `location.file` to exclude anything from system/builtin locations.

### Anti-Patterns to Avoid
- **Branching on `cav.language` inside an extractor** — violates invariant #2. Language is selected once in the executor; each cpp extractor asserts its payload type.
- **Using `PARSE_DETAILED_PROCESSING_RECORD`** — pollutes output with builtin macros; breaks parity and bloats diagrams.
- **Poking `conf.lib.<fn>.restype`** to read versions — caused a hard segfault twice in this session (Pitfall 2). Use `importlib.metadata`.
- **Relying on cursor traversal order for output order** — always sort-on-exit by stable composite keys (the Python extractors all do this; cpp must too).
- **Raising on diagnostics** — LNG-05 requires unresolved includes to be warnings.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| C++ parsing | A C++ tokenizer/parser | `libclang` (`clang.cindex`) | C++ grammar is undecidable to hand-parse; libclang is the reference frontend |
| Composition vs aggregation detection | String-matching `*`/`&` in raw source | `FIELD_DECL.type.kind ∈ {POINTER, LVALUEREFERENCE}` | [VERIFIED live] libclang resolves typedefs/references/elaborated types correctly; source-string matching breaks on `using`/`typedef` |
| Stable cross-run node IDs | Hand-built mangled names | `Cursor.get_usr()` (e.g. `c:@N@geo@S@Shape`) | [VERIFIED live] USR is libclang's deterministic, position-independent symbol ID |
| libclang version assertion | FFI call to `clang_getClangVersion` | `importlib.metadata.version("libclang")` | [VERIFIED live] FFI poke segfaults; metadata returns `"18.1.1"` safely |
| Doxygen comment parsing | Full Doxygen XML pipeline | `re` on `Cursor.raw_comment` | [VERIFIED live] `raw_comment` returns the full `/** ... */` block incl. `\pre`/`@pre`; structured API (`brief_comment`) returns `''` |
| Multi-platform native lib bundling | Vendoring LLVM per-OS | `libclang` wheels (one per platform) | [VERIFIED: PyPI] wheels exist for all target platforms |

**Key insight:** libclang's `clang.cindex` already gives semantically-resolved, deterministic facts (USRs, resolved type kinds, base specifiers, diagnostics). The entire C++ track is a *translation* from cursor facts to the existing Pydantic shapes — never a re-implementation of C++ understanding. The determinism risk is not in libclang's analysis (it is deterministic) but in (a) traversal order — solved by sort-on-exit, and (b) FFI misuse — solved by staying on the high-level binding.

## libclang API Surface (verified present in this env)

| API | Confirmed | Use |
|-----|-----------|-----|
| `Index.create()` | ✓ | LNG-03 guard + per-parse index |
| `index.parse(path, args, unsaved_files, options)` / `TranslationUnit.from_source` | ✓ | in-memory parse from bytes (caller-agnostic) |
| `TranslationUnit.PARSE_INCOMPLETE` | ✓ | tolerate missing includes (LNG-05) |
| `tu.diagnostics` (iterable of `Diagnostic`; `.severity`, `.spelling`, `.category_name`) | ✓ | unresolved-include warnings (LNG-05) |
| `Config.library_path` (= bundled `clang/native/`) | ✓ | DET-02 path verification + reject override |
| `Config.set_library_file` / `Config.library_file` | ✓ | the override surface to **reject** (LNG-03) |
| `Cursor.kind` (`CursorKind.STRUCT_DECL`, `CLASS_DECL`, `CXX_METHOD`, `FUNCTION_DECL`, `FIELD_DECL`, `NAMESPACE`, `CXX_BASE_SPECIFIER`, `CALL_EXPR`, `MEMBER_REF_EXPR`, `PARM_DECL`, `INCLUSION_DIRECTIVE`) | ✓ | structural extraction |
| `Cursor.spelling`, `.displayname`, `.get_usr()`, `.location.file`, `.extent`, `.access_specifier`, `.is_definition()` | ✓ | node ids, ranges, main-file filter, visibility |
| `Cursor.type.kind` (`TypeKind.POINTER`, `LVALUEREFERENCE`, `ELABORATED`, `RECORD`, `INT`, …) + `.type.spelling` | ✓ | composes/aggregates rule |
| `Cursor.raw_comment`, `.brief_comment` | ✓ (`raw_comment` full; `brief_comment` empty) | Doxygen contract regex |
| `cursor.walk_preorder()`, `.get_children()` | ✓ | traversal |

## C++ AST → Schema-Parity Primitives (LNG-04 / D-04)

| Capability | Cursor source | Output (existing Pydantic shape) | Determinism rule |
|------------|---------------|----------------------------------|------------------|
| free function | `FUNCTION_DECL` (main file) | `FunctionNode(kind="function", params, return_type, ...)` | node_id = namespace-qualified name or USR |
| class/struct | `CLASS_DECL` / `STRUCT_DECL` | `FunctionNode(kind="class")` (mirrors Python class node) | node_id qualified |
| method | `CXX_METHOD` under class | `FunctionNode(kind="method")` | node_id = `Class.method`; params from `PARM_DECL` |
| namespace → module/package | `NAMESPACE` | dotted prefix for node_ids; package diagram nodes | namespace nesting → `a.b.c` (analog of Python module path) |
| inheritance (incl. multiple) | `CXX_BASE_SPECIFIER` children of class | `GraphEdge(edge_type="inherits")` per base | [VERIFIED: both bases of `class Circle : public Shape, public Point` captured] |
| member type dep | `FIELD_DECL.type` | `TypeDep` / class-diagram edge | see composes/aggregates below |
| `#include` | `INCLUSION_DIRECTIVE` (or diagnostics for missing) | `TypeDep(kind="imports")` → component diagram | sort by target |
| call | `CALL_EXPR` / `MEMBER_REF_EXPR` in method body | `CallEdge(caller, callee)` | callee = `spelling`; sort lex by (caller, callee) |

**Composition / aggregation / association rule (D-04, verified):**
```
FIELD_DECL.type.kind == POINTER          → aggregates   (Shape* parent)     [has-a, no lifetime]
FIELD_DECL.type.kind == LVALUEREFERENCE  → aggregates   (Point& ref)        [has-a, no lifetime]
FIELD_DECL value record (ELABORATED/RECORD of a known class) → composes     (Point center)      [owns, shared lifetime]
type unresolved / unknown-class / template-dependent          → associates  [undecidable fallback — never a catch-all]
builtin primitive (int/double/…)                              → no edge      (plain field)
```
This is the exact C++ analog of the Python `class_diagram.py` rule (`Optional`/`list` → aggregates; direct class → composes; unknown → associates). "Known class" resolution = the class is declared in the main file (a `CLASS_DECL`/`STRUCT_DECL` cursor); else `associates`. **Empirically confirmed** against the live fixture: `Point center` → `ELABORATED` (composes), `Shape* parent` → `POINTER` (aggregates), `Point& ref` → `LVALUEREFERENCE` (aggregates).

## All 5 Diagram Extractors on C++ CAV

Each cpp evaluation extractor produces the SAME `GraphModel` shape as its Python sibling, into the same `CodeContent` slot:

| Diagram | Python source pattern | C++ cursor equivalent |
|---------|----------------------|------------------------|
| class_diagram (DIA-01) | ClassDef bases + attr annotations | `CLASS_DECL`/`STRUCT_DECL` + `CXX_BASE_SPECIFIER` (inherits) + `FIELD_DECL.type.kind` (composes/aggregates/associates) |
| sequence_diagram (DIA-02) | callgraph CallEdges → `calls` edges; enclosing stmt → frame label | cpp callgraph (`CALL_EXPR`); frame fidelity is best-effort (D-05) — linear `calls` edges are the must-have |
| component_diagram (DIA-03) | `kind=="imports"` TypeDeps → `imports` edges | `#include` directives → `imports` edges; modules = files/translation units |
| package_diagram (DIA-04) | path directory chain → `package` nodes | **namespace** nesting → `package` nodes (primary), path chain as secondary; `attributes={"parent_package": ...}` |
| state_diagram (DIA-05/06) | explicit FSM families (transitions/statemachine/Enum) | C++ has no direct analog of those Python libs; **likely emits empty GraphModel** for v0.2.0 (best-effort, D-05) unless a deterministic C++ FSM idiom is identified. Parity = "same empty shape," which is valid. |

**Planning note on state_diagram:** The Python FSM detection (DIA-05) is library-anchored (`transitions.Machine`, `python-statemachine`). There is no portable, deterministic C++ FSM idiom that maps to those families. The honest, parity-correct behavior is to emit an empty `GraphModel` (zero state nodes) for C++ — exactly as `Color(Enum)` emits zero FSMs on the Python side. This must be **explicitly documented and fixture-asserted** (a C++ fixture with state-machine-looking code asserts zero state nodes), not silently skipped. Confirm with the user/planner whether any C++ FSM idiom is in scope — `[ASSUMED]` empty-output is correct.

## Doxygen Contract Extraction (SPC-03 / D-08 / D-09)

**Method (verified):** regex over `Cursor.raw_comment`. The full comment block is returned including both backslash (`\pre`) and at-sign (`@pre`) Doxygen forms. `brief_comment` returns `''` and the structured `FullComment` AST is not reliably exposed in the Python bindings → **regex is the deterministic choice**.

**Verified live:** for a `/** ... */` block above `int f(int x)`, `raw_comment` returned the literal block containing `@pre x > 0`, `@post r >= 0`, `\invariant state ok`, and `Traces: REQ-9, US-3` — all on one cursor.

**Comment-to-cursor association caveat (planning detail):** `raw_comment` attaches to the *nearest following declaration cursor*. In the namespace fixture, the namespace's leading comment attached to the `NAMESPACE` cursor, not the inner struct. The extractor must read `raw_comment` on the specific decl cursor (function/method/class) it is emitting a contract for — do not assume the comment lands where authored relative to nested decls.

**Marker extraction regex (extend the existing TRC-03 pattern):**
```python
# Both \pre and @pre forms; capture the condition text to end of line.
_DOXY_RE = re.compile(r"[\\@](pre|post|invariant)\b[ \t]*(.*)", re.IGNORECASE)
# TRC-03 trace tags — VERBATIM reuse from functions.py so Python/C++ are byte-identical:
_TRACE_TAGS_RE = re.compile(r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)", re.MULTILINE)
```

**SourceKind extension (D-08):** add additive value(s) to `models/primitives/contracts.py`:
```python
SourceKind = Literal[
    "pydantic_validator", "pydantic_model_validator",
    "pydantic_field_validator", "dataclass_post_init",
    "doxygen",                       # ADDITIVE — D-08 first candidate (single value)
]
```
- `\pre`  → `ContractEntry(source_kind="doxygen", kind="precondition")`
- `\post` → `ContractEntry(source_kind="doxygen", kind="postcondition")`
- `\invariant` → `ContractEntry(source_kind="doxygen", kind="invariant")`

The existing `ContractKind` Literal already has `precondition`/`invariant`/`postcondition` — `\post` maps to `postcondition` cleanly. Reuse `CodeContent.contracts` slot (D-09); no new field. Document in `docs/09-extending.md` that additive `SourceKind` values are allowed (deletion/rename forbidden) — same policy already written for `EdgeKind`.

**Single-value vs 3-value (Claude's discretion):** single `"doxygen"` + `ContractEntry.kind` discrimination is the recommended first candidate — it keeps the Python/C++ schemas symmetric (both use one `source_kind` per provenance family) and avoids a value explosion. Three values (`doxygen_pre`/`doxygen_post`/`doxygen_invariant`) would duplicate information already in `ContractEntry.kind`. Recommend single value.

## libclang Runtime Guard (LNG-03 / DET-02 / D-07)

**Location:** module-level lazy init in `frontends/cpp.py`, run once. Python-only callers never import this module, so libclang never loads on the pure-Python path (no-I/O-at-import preserved).

**Three jobs (all verified mechanically achievable):**
1. **Load + smoke test:** `Index.create()` once; on failure raise `RuntimeError` with platform-specific install instructions.
2. **ABI pin assertion (DET-02):** `importlib.metadata.version("libclang") == "18.1.1"` (NOT FFI — Pitfall 2). Also verify `Config.library_path` points into the bundled `clang/native/` dir (confirms the bundled wheel lib is in use, not a system override).
3. **Reject override (LNG-03):** if a caller has called `Config.set_library_file(...)` (i.e. `Config.library_file` is non-`None` / not the bundled path), raise — the pinned bundled ABI must be the one in use. (`Config.library_file` is `None` by default in this env when the bundled lib is used.)

**Skeleton (see §Code Examples).** Platform-specific messages: macOS → "install Xcode Command Line Tools / verify arm64 wheel"; Linux → "ensure libclang shared lib loads (the bundled wheel should suffice; check glibc/musl variant)"; Windows → "ensure the MSVC runtime redistributable is installed."

## Code Examples

### libclang import-time runtime guard (LNG-03 / DET-02)
```python
# Source: composed from live-verified clang.cindex API + REQUIREMENTS LNG-03/DET-02
from __future__ import annotations
import importlib.metadata, os, sys

_READY = False
_EXPECTED_VERSION = "18.1.1"

def _platform_install_hint() -> str:
    if sys.platform == "darwin":
        return "macOS: install Xcode Command Line Tools (xcode-select --install) and confirm the arm64 libclang wheel is installed."
    if sys.platform.startswith("win"):
        return "Windows: ensure the MSVC runtime redistributable is installed; reinstall 'libclang==18.1.1'."
    return "Linux: the bundled libclang wheel should self-contain the shared lib; reinstall 'libclang==18.1.1' (match glibc/musl)."

def _ensure_libclang_ready() -> None:
    global _READY
    if _READY:
        return
    # DET-02: pinned ABI assertion via metadata (safe — never FFI-poke version).
    ver = importlib.metadata.version("libclang")
    if ver != _EXPECTED_VERSION:
        raise RuntimeError(f"libclang ABI pin violated: expected {_EXPECTED_VERSION}, got {ver}.")
    from clang.cindex import Config, Index
    # LNG-03: reject caller override of the bundled library.
    if Config.library_file is not None:
        raise RuntimeError(
            "Config.set_library_file override is rejected: the pinned bundled "
            f"libclang=={_EXPECTED_VERSION} must be used (DET-02)."
        )
    lib_path = Config.library_path
    if not lib_path or "native" not in os.path.normpath(lib_path).split(os.sep):
        # bundled wheel resolves library_path to .../clang/native/ (verified live)
        raise RuntimeError(f"libclang not resolving to the bundled wheel (library_path={lib_path!r}). {_platform_install_hint()}")
    try:
        Index.create()   # dylib load smoke test (LNG-03)
    except Exception as exc:  # dylib failed to load
        raise RuntimeError(f"libclang failed to load: {exc}. {_platform_install_hint()}") from exc
    _READY = True
```

### Deterministic main-file cursor walk with USR node_id (verified)
```python
# Source: live-verified clang.cindex traversal in this env
from clang.cindex import CursorKind, TypeKind

def _in_main_file(cursor, path: str) -> bool:
    f = cursor.location.file
    return f is not None and f.name == path

def _field_relation(field_cursor, known_classes: set[str]) -> tuple[str, str] | None:
    t = field_cursor.type
    target = t.get_pointee().spelling if t.kind in (TypeKind.POINTER, TypeKind.LVALUEREFERENCE) else t.spelling
    base = target.replace("class ", "").replace("struct ", "").split("::")[-1].strip(" *&")
    if t.kind in (TypeKind.POINTER, TypeKind.LVALUEREFERENCE):
        return ("aggregates", base) if base in known_classes else ("associates", base)
    if t.kind in (TypeKind.ELABORATED, TypeKind.RECORD):
        return ("composes", base) if base in known_classes else ("associates", base)
    return None   # primitive → no edge
```
*(`get_pointee()` is the canonical way to unwrap a pointer/reference target type — use it rather than string-stripping `*`/`&` where possible.)*

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| System-installed libclang + `clang` PyPI binding | self-contained `libclang` wheel (sighingnow) | stable since ~2019 | No LLVM toolchain needed in CI; one pinned wheel per platform |
| `PARSE_DETAILED_PROCESSING_RECORD` for "complete" parse | default parse + main-file filter | — | avoids builtin-macro pollution; deterministic small tree |
| structured comment API | regex on `raw_comment` | bindings limitation | `brief_comment`/`FullComment` unreliable in Python bindings |

**Deprecated/outdated:**
- `clang.cindex.TranslationUnit.from_source` vs `Index.create().parse(...)` — both work and are equivalent; either is fine (verified `from_source` present). Prefer `Index.create().parse(...)` for explicit options control.

## Validation Architecture

> nyquist_validation is not disabled in config (no `.planning/config.json` workflow override found that sets it false — treat as enabled).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest>=8` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) |
| Quick run command | `pytest tests/unit -x -q` |
| Full suite command | `pytest --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LNG-03 | import-time guard raises clear RuntimeError on ABI/load/override failure | unit | `pytest tests/unit/frontends/test_cpp_guard.py -x` | ❌ Wave 0 |
| DET-02 | `version("libclang")=="18.1.1"`; `set_library_file` override rejected | unit | `pytest tests/unit/frontends/test_cpp_guard.py::test_abi_pin -x` | ❌ Wave 0 |
| LNG-04 | cpp `NormalizedArtifact` has identical Pydantic shape to Python (structural assertion) | parity | `pytest tests/parity/test_cpp_python_schema_parity.py -x` | ❌ Wave 0 |
| LNG-05 | missing `#include` → diagnostics warning, never raises; cursor tree still built | unit | `pytest tests/unit/frontends/test_cpp_frontend.py::test_missing_include_warns -x` | ❌ Wave 0 |
| LNG-04 (class) | inheritance(multiple) + composes/aggregates/associates from C++ fixture | acceptance | `pytest tests/acceptance/test_cpp_class_diagram.py -x` | ❌ Wave 0 |
| SPC-03 | `\pre`/`\post`/`\invariant` → ContractInfo same schema as Python | acceptance | `pytest tests/acceptance/test_cpp_doxygen_contracts.py -x` | ❌ Wave 0 |
| TRC-03 | `Traces:` extraction identical for Python docstring + C++ Doxygen | parity | `pytest tests/parity/test_trc03_cpp_parity.py -x` | ❌ Wave 0 |
| LNG-04 (determinism) | cpp output byte-identical across 3 runs (per-extractor, not full snapshot — that's Phase 5) | unit | `pytest tests/unit/frontends/test_cpp_determinism.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit -x -q`
- **Per wave merge:** `pytest --tb=short` (full suite; existing Python tests must NOT regress — invariant #1/#2 guard)
- **Phase gate:** full suite green + CI mandatory matrix green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` — add `build_cpp_cav(source, path)` helper (mirror of `build_python_cav`) so cpp extractor tests share one CAV builder
- [ ] `tests/fixtures/cpp/` — C++ fixture corpus (inheritance/multiple-inheritance, composition/aggregation/association members, namespace, includes, Doxygen contracts, Traces tags, a "looks like FSM but isn't" negative fixture)
- [ ] `tests/unit/frontends/test_cpp_guard.py` — LNG-03/DET-02 guard tests
- [ ] `tests/parity/test_cpp_python_schema_parity.py` — LNG-04 structural parity
- [ ] `tests/unit/test_dispatch.py` — extend to assert nested-dict shape + per-language slot guard (existing file)
- [ ] Framework install: already present (`libclang==18.1.1` in dev extras) — no new install

*(Determinism note: per-extractor 3-run byte-identity is a Phase-4 unit concern; the cross-cutting full-pipeline DET-01 snapshot is Phase 5 per CONTEXT.md Deferred.)*

## Security Domain

> `security_enforcement` config not found; treating as enabled. This is a deterministic, offline, no-network, no-eval static-analysis library — the threat surface is narrow but real (it parses untrusted source).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | library has no auth |
| V3 Session Management | no | stateless library |
| V4 Access Control | no | no access control surface |
| V5 Input Validation | yes | untrusted C++ source is parsed; never `eval`'d. Pydantic `extra="forbid"` on all models. libclang parses, never executes. `unsaved_files` keeps input in-memory (no temp-file write of attacker content to predictable paths). |
| V6 Cryptography | no | no crypto |

### Known Threat Patterns for libclang static parsing
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious/huge C++ input causing libclang OOM/hang | Denial of Service | libclang parses statically (no codegen); caller controls input size. Consider documenting that callers bound input. (No subprocess timeout applies — in-process.) |
| `#include` of attacker-controlled system paths | Tampering / Info disclosure | `compile_args` `-I` dirs are **caller-supplied** (LNG-05); the library never auto-discovers `compile_commands.json` (explicitly out of scope per REQUIREMENTS). Unresolved includes → warning, not a file-read attempt beyond the given `-I` set. |
| FFI memory-safety (segfault) | DoS / integrity | **Pitfall 2** — never manipulate `conf.lib` function signatures; stay on the high-level binding. Segfault reproduced twice this session by poking FFI. |
| Pinned-ABI bypass via `Config.set_library_file` | Tampering | LNG-03 guard rejects the override (DET-02). |

## Common Pitfalls

### Pitfall 1: FRONTENDS over-nesting
**What goes wrong:** Nesting `FRONTENDS` into `dict[lang, dict[name, fn]]` like PRIMITIVES/EVALUATIONS, then `FRONTENDS[language]` returns a dict instead of a function.
**Why it happens:** D-01 says "nest the three dicts" but FRONTENDS is already keyed by language (one frontend per language).
**How to avoid:** Only `PRIMITIVES` and `EVALUATIONS` gain the language dimension. `FRONTENDS` stays `dict[str, FrontendFn]` and just adds `["cpp"]`. The executor already does `FRONTENDS[language]` correctly today.
**Warning signs:** `TypeError: 'dict' object is not callable` at `frontend(raw_content, path, config)`.

### Pitfall 2: libclang FFI version-poke segfault (DET-02 implementation trap)
**What goes wrong:** Reading the libclang version by setting `conf.lib.clang_getClangVersion.restype` and calling it → **hard segfault** (reproduced twice this session, exit 139).
**Why it happens:** Mutating the cached `conf.lib` ctypes function prototype corrupts libclang's binding state.
**How to avoid:** Use `importlib.metadata.version("libclang")` for the DET-02 assertion (verified returns `"18.1.1"` cleanly). Never touch `conf.lib.*.restype`.
**Warning signs:** segfault / `Segmentation fault` during version checks.

### Pitfall 3: Builtin-macro cursor pollution
**What goes wrong:** Output contains hundreds of `__llvm__`, `__clang__`, `__cpp_*` `MACRO_DEFINITION` cursors; diagrams/primitives are huge and non-parity.
**Why it happens:** `PARSE_DETAILED_PROCESSING_RECORD` option, or not filtering by `cursor.location.file`.
**How to avoid:** Default parse (no detailed processing record) + filter every walk by `_in_main_file(cursor, path)`.
**Warning signs:** function/symbol counts in the hundreds for a tiny file.

### Pitfall 4: Comment-to-cursor misassociation
**What goes wrong:** A class's Doxygen `\pre` block is read off the wrong cursor (e.g. the enclosing namespace) and attributed to the wrong node.
**Why it happens:** `raw_comment` attaches to the nearest following decl; with nesting, the authored position and the cursor that owns the comment can differ.
**How to avoid:** Read `raw_comment` on the exact decl cursor being emitted; do not infer from textual proximity.
**Warning signs:** contracts attached to namespaces or the first inner decl instead of the intended function.

### Pitfall 5: Non-deterministic output ordering
**What goes wrong:** cpp output differs run-to-run (breaks LNG-04 parity and future DET-01).
**Why it happens:** Emitting in cursor-traversal order without sorting.
**How to avoid:** sort-on-exit by stable composite key (same as every Python extractor: nodes by `node_id`, edges by `(source, target, edge_type, label)`).
**Warning signs:** 3-run byte-identity test fails.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `libclang` (clang.cindex) | C++ frontend (LNG-03/04/05, DET-02) | ✓ | 18.1.1 | — (hard requirement; pinned) |
| bundled native libclang lib | dylib load | ✓ | `clang/native/libclang.dll` present | — |
| `pytest` | all tests | ✓ (dev extra) | >=8 | — |
| C++ compiler / system LLVM | NOT required | n/a | n/a | wheel is self-contained — no system LLVM needed |
| Linux aarch64 CI runner | LNG-01 mandatory matrix | depends on GitHub Actions runner availability | — | see CI note below |

**Missing dependencies with no fallback:** none on this dev machine (Windows x86_64, libclang 18.1.1 installed and working).

**CI note (planning input):** GitHub-hosted Linux **arm64** runners (`ubuntu-24.04-arm` / `ubuntu-22.04-arm`) are generally available for public repos. The plan should use a native arm64 runner label if available; QEMU emulation (`docker/setup-qemu-action` + a manylinux2014_aarch64 container) is the fallback if a native arm64 runner is not usable. **This is an `[ASSUMED]` runner-availability detail** — the planner/executor must confirm the current GitHub Actions arm64 runner label at implementation time. The libclang `manylinux2014_aarch64` wheel exists `[VERIFIED: PyPI]`, so the dependency side is solved regardless of runner mechanism.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | C++ state_diagram emits an empty GraphModel for v0.2.0 (no portable deterministic C++ FSM idiom maps to the Python FSM families) | §All 5 Diagram Extractors | If a C++ FSM idiom IS expected, DIA-05 parity would be incomplete; confirm scope with planner. Parity-as-empty-shape is defensible but should be fixture-asserted + documented. |
| A2 | GitHub Actions native Linux arm64 runner is available (else QEMU + manylinux container) | §Environment Availability, §CI Matrix | Wrong runner label → CI matrix job fails to provision; mitigated by QEMU fallback. Confirm current runner label at implementation. |
| A3 | slopcheck unavailable → libclang tagged ASSUMED for slop status (mitigated: pre-locked dep, PyPI+import verified) | §Package Legitimacy Audit | None practically — libclang is a user-approved pinned dependency, not a new package. |
| A4 | Single `SourceKind="doxygen"` value (vs 3 values) is the right D-08 choice | §Doxygen Contract Extraction | Low — both are additive and reversible; recommended single value keeps Python/C++ symmetric. Agent discretion per CONTEXT.md. |
| A5 | `Config.library_file is None` when the bundled wheel lib is used (so non-None = override to reject) | §Runtime Guard | If the bundled wheel sets `library_file` itself on some platform, the override check needs to compare against the bundled path instead. Verify the guard on each CI platform. |

**These assumptions need confirmation before becoming locked decisions** — A1 (state diagram scope) and A2 (CI runner) are the highest-impact.

## Open Questions

1. **C++ state_diagram scope (A1)**
   - What we know: Python DIA-05 detects 3 library-anchored FSM families; C++ has no portable analog.
   - What's unclear: whether any C++ FSM idiom (e.g. an enum + switch-on-state pattern) is in v0.2.0 scope, or empty-output is accepted.
   - Recommendation: emit empty `GraphModel`, fixture-assert zero state nodes, document as best-effort (D-05). Flag to planner for explicit confirmation.

2. **Linux arm64 CI runner mechanism (A2)**
   - What we know: libclang manylinux2014_aarch64 wheel exists; GitHub offers arm64 runners.
   - What's unclear: exact current runner label / whether native or QEMU is required.
   - Recommendation: plan a native-arm64 job first; keep QEMU + manylinux container as a documented fallback path.

3. **`#include` directive cursors vs diagnostics for the component diagram**
   - What we know: missing includes appear in `tu.diagnostics`; present includes appear as `INCLUSION_DIRECTIVE` cursors (only with detailed-processing record, which we avoid) OR can be parsed from the source text deterministically.
   - What's unclear: best deterministic source for `#include` edges without the macro-polluting parse flag.
   - Recommendation: parse `#include` lines from `raw_content` via regex (deterministic, no flag) for the component diagram's import edges; cross-check unresolved ones against diagnostics for the LNG-05 warning. Agent discretion.

## Sources

### Primary (HIGH confidence)
- Live `clang.cindex` API + parse behavior verified in this environment (libclang==18.1.1): cursor kinds, `raw_comment`, `Config.library_path`, `FIELD_DECL.type.kind`, `CXX_BASE_SPECIFIER`, `get_usr()`, diagnostics on missing include, `importlib.metadata.version("libclang")`, FFI segfault reproduction
- `pip index versions libclang` — 18.1.1 latest+installed
- PyPI JSON API (`/pypi/libclang/18.1.1/json`) — wheel platform tags: macosx_10_9_x86_64, macosx_11_0_arm64, manylinux2010_x86_64, manylinux2014_aarch64, manylinux2014_armv7l, musllinux_1_2_x86_64, win_amd64, win_arm64
- Codebase: `_dispatch.py`, `executor.py`, `frontends/python.py`, all `models/*`, `extractors/primitives/*`, `extractors/evaluations/*`, `adapters/base.py`, `docs/09-extending.md`, `.github/workflows/ci.yml`, `pyproject.toml`, `tests/`
- `.planning/`: CONTEXT.md (D-01..D-09), REQUIREMENTS.md (LNG-01..05, SPC-03, DET-02), ROADMAP.md §Phase 4, SP-3 spike (verdict ship-best-effort)

### Secondary (MEDIUM confidence)
- WebSearch (libclang PyPI wheels) — corroborates win_arm64 + manylinux2014_aarch64 availability: https://pypi.org/project/libclang/ , https://github.com/sighingnow/libclang

### Tertiary (LOW confidence)
- GitHub Actions arm64 runner label availability (A2) — not verified this session; planner must confirm current label

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — libclang pinned + all platform wheels + full API surface verified live
- Architecture (dispatch nesting + cpp extractors): HIGH — verified against actual codebase; the FRONTENDS-asymmetry pitfall caught
- Pitfalls: HIGH — Pitfalls 1–5 each grounded in live behavior (segfault, macro pollution, comment association all reproduced/observed)
- CI matrix: MEDIUM — wheel side HIGH (verified), runner-label side LOW (A2 assumption)
- State diagram C++ parity: MEDIUM — empty-output recommendation is defensible but scope (A1) needs planner confirmation

**Research date:** 2026-06-02
**Valid until:** 2026-07-02 (stable — libclang pinned exact; revisit if GitHub Actions arm64 runner labels change)
