# Phase 4: C++ Frontend + C++ Extractors - Pattern Map

**Mapped:** 2026-06-02
**Files analyzed:** 23 (11 new source + 6 modified + ~6 new test artifacts)
**Analogs found:** 22 / 23 (every new file has a Python sibling; CI matrix has a partial in-repo analog)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| **NEW** `lib_code_parser/frontends/cpp.py` | frontend | transform (bytes→CAV) | `lib_code_parser/frontends/python.py` | exact (role+flow) |
| **NEW** `lib_code_parser/extractors/primitives/cpp_functions.py` | primitive extractor | transform (CAV→list[FunctionNode]) | `extractors/primitives/functions.py` | exact |
| **NEW** `lib_code_parser/extractors/primitives/cpp_callgraph.py` | primitive extractor | transform (CAV→CallGraph) | `extractors/primitives/callgraph.py` | exact |
| **NEW** `lib_code_parser/extractors/primitives/cpp_type_deps.py` | primitive extractor | transform (CAV→list[TypeDep]) | `extractors/primitives/type_deps.py` | role-match (no pyright path) |
| **NEW** `lib_code_parser/extractors/primitives/cpp_contracts.py` | primitive extractor | transform (CAV→dict[str,ContractInfo]) | `extractors/primitives/contracts.py` | exact |
| **NEW** `lib_code_parser/extractors/evaluations/cpp_class_diagram.py` | evaluation extractor | transform (CAV→GraphModel) | `extractors/evaluations/class_diagram.py` | exact |
| **NEW** `lib_code_parser/extractors/evaluations/cpp_sequence_diagram.py` | evaluation extractor | transform (CAV→GraphModel) | `extractors/evaluations/component_diagram.py` (pull-a-primitive pattern) | role-match |
| **NEW** `lib_code_parser/extractors/evaluations/cpp_component_diagram.py` | evaluation extractor | transform (CAV→GraphModel) | `extractors/evaluations/component_diagram.py` | exact |
| **NEW** `lib_code_parser/extractors/evaluations/cpp_package_diagram.py` | evaluation extractor | transform (CAV→GraphModel) | `extractors/evaluations/package_diagram.py` | exact |
| **NEW** `lib_code_parser/extractors/evaluations/cpp_state_diagram.py` | evaluation extractor | transform (CAV→GraphModel, likely empty) | `extractors/evaluations/state_diagram.py` | role-match (empty-output for C++) |
| **NEW** `lib_code_parser/_cpp_cursor.py` (optional) | utility | helper (cursor walk / USR id / sort keys) | `lib_code_parser/_paths.py` (single-source helper idiom) + `class_diagram.py:_field_relation` analog in RESEARCH | partial |
| **MODIFY** `lib_code_parser/_dispatch.py` | config/registry | event-driven (registration) | self (existing flat registration) | self-evolution |
| **MODIFY** `lib_code_parser/executor.py` | orchestrator | request-response (walk) | self (existing PRIMITIVES/EVALUATIONS walk) | self-evolution |
| **MODIFY** `lib_code_parser/models/primitives/contracts.py` | model | n/a (additive Literal) | self (`SourceKind` Literal) | self-evolution |
| **MODIFY** `.github/workflows/ci.yml` | config (CI) | batch (matrix) | self (`sp3-libclang-spike` job) | partial |
| **MODIFY** `docs/09-extending.md` | doc | n/a | self (§EdgeKind MAJOR policy) | self-evolution |
| **NEW** `tests/conftest.py` add `build_cpp_cav` | test fixture | n/a | `tests/conftest.py:build_python_cav` | exact |
| **NEW** `tests/fixtures/cpp/*` | test fixture corpus | n/a | `tests/unit/extractors/fixtures/*.py` | role-match |
| **NEW** `tests/unit/frontends/test_cpp_guard.py` | test (unit) | n/a | `tests/unit/frontends/test_python_frontend.py` | role-match |
| **NEW** `tests/unit/frontends/test_cpp_frontend.py` | test (unit) | n/a | `tests/unit/frontends/test_python_frontend.py` | exact |
| **MODIFY** `tests/unit/test_dispatch.py` | test (unit) | n/a | self (existing nested-shape assertions) | self-evolution |
| **NEW** `tests/parity/test_cpp_python_schema_parity.py` | test (parity) | n/a | `tests/parity/test_v01_v02_compat.py` | role-match |
| **NEW** `tests/acceptance/test_cpp_class_diagram.py`, `test_cpp_doxygen_contracts.py` | test (acceptance) | n/a | `tests/acceptance/test_dia01_class_diagram.py` | exact |

---

## Pattern Assignments

### `lib_code_parser/frontends/cpp.py` (frontend, bytes→CAV transform)

**Analog:** `lib_code_parser/frontends/python.py` (whole file, 43 lines — exact structural twin)

**Module + imports + signature pattern** (`python.py` lines 14-24, 35-42) — mirror this shape exactly, swapping `ast` for libclang:
```python
from __future__ import annotations
import ast  # → cpp.py: from clang.cindex import Index, TranslationUnit (lazy/guarded)
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
__all__ = ["build_cav"]

def build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV:
    source = raw_content.decode("utf-8", errors="replace")   # ← copy verbatim (decode policy)
    module = ast.parse(source, filename=path)                # ← cpp: index.parse(...) (single parse site)
    return CAV(language="python", path=path, payload=module, raw_content=raw_content)
```

**What the C++ version changes** (per D-06/D-07 + RESEARCH Pattern 2, lines 217-233):
- `language="cpp"`, `payload=tu` (the `TranslationUnit`)
- Keep `raw_content` carry verbatim (the C++ component diagram regex-scans `raw_content` for `#include` lines per RESEARCH Open Question 3)
- Keep `decode("utf-8", errors="replace")` verbatim — identical decode policy to Python frontend
- Prepend `_ensure_libclang_ready()` (the D-07 guard, see Shared Patterns below)
- `args = ["-x", "c++", *config.compile_args]`; `options=TranslationUnit.PARSE_INCOMPLETE`; `unsaved_files=[(path, source)]` (in-memory, no disk I/O — caller-agnostic)

**The single-parse invariant comment** (`python.py` lines 27-29 in docstring): this is "the ONLY ast.parse() call site for the Python language path." cpp.py docstring must mirror: "the ONLY libclang parse site for the C++ language path" (AST-05 analog).

**Config-arg-for-signature-parity note** (`python.py` lines 31-33): Python frontend documents that `config` is accepted for FrontendFn dispatch parity. C++ frontend genuinely **uses** `config.compile_args` (LNG-05), so this note inverts — document that compile_args is consumed.

---

### `lib_code_parser/extractors/primitives/cpp_functions.py` (primitive, CAV→list[FunctionNode])

**Analog:** `lib_code_parser/extractors/primitives/functions.py`

**Signature + language-guard pattern** (`functions.py` lines 73, 81-84) — the load-bearing guard that the nested dispatch (D-01) makes safe:
```python
def extract(cav: CAV, config: ParserConfig) -> list[FunctionNode]:
    tree = cav.payload  # ast.Module — declared opaque in CAV
    assert isinstance(tree, ast.Module), (
        f"functions extractor requires Python CAV (ast.Module payload), got {type(tree).__name__}"
    )
```
**C++ version** asserts `isinstance(cav.payload, clang.cindex.TranslationUnit)` with the symmetric message. RESEARCH line 78 confirms this is the correct language guard — it documents the precondition the nested dispatch already enforces. **Do NOT branch on `cav.language` inside the extractor** (invariant #2 anti-pattern, RESEARCH line 243).

**TRC-03 trace-tag regex — copy VERBATIM** (`functions.py` lines 32, 42-48). This regex MUST be byte-identical between Python and C++ so TRC-03 parity (D-09) holds:
```python
_TRACE_TAGS_RE = re.compile(r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)", re.MULTILINE)

def _extract_trace_tags(docstring: str) -> list[TraceTag]:
    tags: list[TraceTag] = []
    for m in _TRACE_TAGS_RE.finditer(docstring):
        refs = [r.strip() for r in m.group(1).split(",")]
        tags.append(TraceTag(tag="Traces", refs=refs))
    return tags
```
C++ feeds `cursor.raw_comment` into the SAME function (RESEARCH lines 327-328 mandates verbatim reuse). Best implemented as a shared helper in `_cpp_cursor.py` importing the identical pattern, or re-declaring the identical literal.

**Two-pass emit + node_id construction** (`functions.py` lines 88-136): Python builds `node_id` as `f"{module_name}.{node.name}"` / `f"{module_name}.{Class}.{method}"`. C++ analog: namespace-qualified name (`a.b.Class.method`) or `cursor.get_usr()` (RESEARCH lines 282-289). FunctionNode `kind` discriminator (`"class"`/`"method"`/`"function"`) maps directly: `CLASS_DECL`/`STRUCT_DECL`→`"class"`, `CXX_METHOD`→`"method"`, `FUNCTION_DECL`→`"function"`.

**Emits the SAME `FunctionNode`/`ParamInfo`/`SourceRange`/`TraceTag` models** (`functions.py` lines 23-28 import block) — no model changes (LNG-04 parity, invariant #1).

---

### `lib_code_parser/extractors/primitives/cpp_callgraph.py` (primitive, CAV→CallGraph)

**Analog:** `lib_code_parser/extractors/primitives/callgraph.py`

**Sort-on-exit pattern (DET-04)** (`callgraph.py` lines 93-96) — the determinism core that absorbs libclang's nondeterministic cursor traversal order:
```python
# DET-04 / ROADMAP Phase 2 SC-2: edge sort by (caller, callee) lex
edges.sort(key=lambda e: (e.caller, e.callee))
return CallGraph(nodes=list(dict.fromkeys(nodes)), edges=edges)
```
C++ collects `CallEdge(caller=method_id, callee=spelling)` from `CALL_EXPR`/`MEMBER_REF_EXPR` cursors, then applies the IDENTICAL sort key (RESEARCH line 289). `dict.fromkeys` for ordered node dedup is copied verbatim.

**Guard + emits same `CallEdge`/`CallGraph` models** (`callgraph.py` lines 29, 66-68): mirror the assert; reuse models unchanged.

---

### `lib_code_parser/extractors/primitives/cpp_type_deps.py` (primitive, CAV→list[TypeDep])

**Analog:** `lib_code_parser/extractors/primitives/type_deps.py` (role-match — the pyright/`resolve_imports` opt-in path does NOT apply to C++)

**Use only the DEFAULT pure path** (`type_deps.py` lines 143-145) — the C++ extractor has no pyright equivalent:
```python
if not config.resolve_imports:
    raw_deps.sort(key=lambda d: (d.source, d.target, d.kind, d.source_line))
    return raw_deps
```
C++ emits `TypeDep(source=module, target=..., kind="imports"|"uses", source_line=...)` from `#include` directives + `FIELD_DECL.type` member deps. **Skip the entire pyright/PyrightAdapter branch** (`type_deps.py` lines 147-171) — it is Python-only and subprocess-based (D-06 says libclang is in-process; adapters/ is subprocess-only).

**`TypeDep.kind` is free-form `str`** (per `docs/09-extending.md` lines 170-178) — C++ may emit language-specific kinds without a MAJOR bump. The sort key `(source, target, kind, source_line)` is copied verbatim for DET-04.

---

### `lib_code_parser/extractors/primitives/cpp_contracts.py` (primitive, CAV→dict[str,ContractInfo])

**Analog:** `lib_code_parser/extractors/primitives/contracts.py`

**Per-class ContractInfo aggregation shape** (`contracts.py` lines 143, 157-201) — mirror the dict-keyed-by-class-id return and the `ContractEntry` construction:
```python
def extract(cav: CAV, config: ParserConfig) -> dict[str, ContractInfo]:
    ...
    result: dict[str, ContractInfo] = {}
    for class_node in ...:
        class_id = f"{module_name}.{class_node.name}"
        entries: list[ContractEntry] = []
        ...
        entries.append(ContractEntry(
            name=item.name, source_kind=source_kind, kind=contract_kind,
            decorator_name=canonical, line_no=item.lineno,
        ))
        if entries:
            result[class_id] = ContractInfo(node_id=class_id, entries=entries)
    return result
```

**C++ Doxygen mapping** (RESEARCH lines 326-345, D-08/D-09):
- Read `cursor.raw_comment` on the **exact decl cursor** being emitted (Pitfall 4 — comment misassociation; do not infer from textual proximity)
- `_DOXY_RE = re.compile(r"[\\@](pre|post|invariant)\b[ \t]*(.*)", re.IGNORECASE)` (both `\pre` and `@pre` forms)
- `\pre` → `ContractEntry(source_kind="doxygen", kind="precondition")`
- `\post` → `ContractEntry(source_kind="doxygen", kind="postcondition")`
- `\invariant` → `ContractEntry(source_kind="doxygen", kind="invariant")`
- Reuse the verbatim `_TRACE_TAGS_RE` (TRC-03 parity, D-09)

The Python decorator-alias provenance machinery (`contracts.py` lines 50-140) does NOT carry over — C++ provenance is the Doxygen marker itself. The OUTPUT shape (`ContractEntry`/`ContractInfo`) is identical.

---

### `lib_code_parser/extractors/evaluations/cpp_class_diagram.py` (evaluation, CAV→GraphModel)

**Analog:** `lib_code_parser/extractors/evaluations/class_diagram.py`

**Sort-on-exit + GraphModel assembly (DET-04)** (`class_diagram.py` lines 359-366) — the exact pattern every cpp diagram extractor must end with:
```python
node_ids = list(dict.fromkeys(node_ids))
nodes = [GraphNode(node_id=nid, node_type="class", label=nid) for nid in node_ids]
# DET-04 sort-on-exit with stable composite keys.
nodes.sort(key=lambda n: n.node_id)
edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))
return GraphModel(nodes=nodes, edges=edges)
```

**Inheritance + relationship edge emission** (`class_diagram.py` lines 346-357):
```python
for base in class_node.bases:
    base_name = _name_of(base)
    if base_name and base_name != "object":
        edges.append(GraphEdge(source=class_name, target=base_name, edge_type="inherits"))
```
C++: `CXX_BASE_SPECIFIER` children → `inherits` edge per base (RESEARCH line 286, multiple inheritance verified). `edge_type` values stay in this lib's own vocabulary (`inherits`/`composes`/`aggregates`/`associates`) — NOT renamed to sibling spelling (`class_diagram.py` docstring lines 15-18, D-03).

**Composition/aggregation decision rule** — the C++ analog of `_classify_annotation` (`class_diagram.py` lines 138-172). RESEARCH lines 291-299, 411-419 gives the verified C++ mapping:
```
FIELD_DECL.type.kind == POINTER/LVALUEREFERENCE  → aggregates  (use get_pointee().spelling)
FIELD_DECL value record (ELABORATED/RECORD of known class) → composes
unresolved / unknown-class / template-dependent  → associates  (explicit fallback, NEVER catch-all)
builtin primitive (int/double/...)               → no edge
```
"Known class" = declared in main file (`CLASS_DECL`/`STRUCT_DECL` cursor), mirroring Python's `_collect_known_classes` (lines 97-121). `"associates"` is the canonical undecidable fallback (`docs/09-extending.md` lines 215-226) — never emit `"uses"`/`"other"`.

---

### `lib_code_parser/extractors/evaluations/cpp_component_diagram.py` (evaluation, CAV→GraphModel)

**Analog:** `lib_code_parser/extractors/evaluations/component_diagram.py` (exact)

**Pull-a-primitive pattern (invariant #5)** (`component_diagram.py` lines 27, 51-64) — evaluation extractors import the primitive they need directly:
```python
from lib_code_parser.extractors.primitives import type_deps
...
tds = type_deps.extract(cav, config)
import_deps = [td for td in tds if td.kind == "imports"]
node_ids: list[str] = [module_name]
for td in import_deps:
    node_ids.append(td.target)
node_ids = list(dict.fromkeys(node_ids))
nodes = [GraphNode(node_id=nid, node_type="component", label=nid) for nid in node_ids]
edges = [GraphEdge(source=td.source, target=td.target, edge_type="imports") for td in import_deps]
```
C++ pulls `cpp_type_deps` (its OWN new primitive — invariant #5 pull, not the Python one). Per RESEARCH Open Question 3, the `#include` edge source is best a deterministic regex over `cav.raw_content` (no `PARSE_DETAILED_PROCESSING_RECORD` flag — Pitfall 3). Same `node_type="component"` slot, same DET-04 sort.

---

### `lib_code_parser/extractors/evaluations/cpp_sequence_diagram.py` (evaluation, CAV→GraphModel)

**Analog:** `extractors/evaluations/component_diagram.py` (pull-primitive structure) + `class_diagram.py` (sort tail)

Pull `cpp_callgraph`, emit linear `calls` edges (the must-have per RESEARCH line 308; frame fidelity is best-effort D-05). Same GraphModel sort tail.

---

### `lib_code_parser/extractors/evaluations/cpp_package_diagram.py` (evaluation, CAV→GraphModel)

**Analog:** `extractors/evaluations/package_diagram.py`

**Containment-via-attributes pattern** (`package_diagram.py` lines 75-92):
```python
nodes.append(GraphNode(
    node_id=pkg_id, node_type="package", label=pkg_id.rsplit(".", 1)[-1],
    attributes={"parent_package": parent} if parent else {},
))
nodes.sort(key=lambda n: n.node_id)
return GraphModel(nodes=nodes)
```
C++ primary source = **namespace nesting** → `package` nodes (RESEARCH line 310), path chain secondary. `attributes={"parent_package": ...}` carries containment (no `contains` edge — same as Python). Same `node_type="package"`, same DET-04 sort.

---

### `lib_code_parser/extractors/evaluations/cpp_state_diagram.py` (evaluation, CAV→GraphModel — likely empty)

**Analog:** `extractors/evaluations/state_diagram.py` (role-match — Python detects 3 library-anchored FSM families; C++ has no portable analog)

**Parity-as-empty-shape** (RESEARCH lines 311-313, Open Question 1 / Assumption A1): emit an **empty `GraphModel`** for v0.2.0 (zero state nodes), exactly as a Python `Color(Enum)` with no transitions yields zero FSMs (`state_diagram.py` docstring lines 18-21). This MUST be **fixture-asserted** (a "looks-like-FSM-but-isn't" C++ fixture asserts zero state nodes) and documented as best-effort — not silently skipped. **PLANNER ACTION:** confirm with user whether any C++ FSM idiom is in v0.2.0 scope; `[ASSUMED]` empty-output is correct. Still ends with the DET-04 sort tail (`state_diagram.py` lines 109-114) even when empty.

---

### `lib_code_parser/_dispatch.py` (MODIFY — the one-time D-01 nesting)

**Analog:** self. Current flat registration (`_dispatch.py` lines 37-43, 56-97).

**Nest ONLY `PRIMITIVES` and `EVALUATIONS`** (RESEARCH Pitfall 1, lines 496-500 — `FRONTENDS` is already language-keyed, do NOT double-nest it):
```python
# BEFORE: PRIMITIVES: dict[str, PrimitiveFn] = {}
# AFTER (D-01):
FRONTENDS:   dict[str, FrontendFn]              = {}                    # unchanged shape — add ["cpp"]
PRIMITIVES:  dict[str, dict[str, PrimitiveFn]]  = {"python": {}, "cpp": {}}
EVALUATIONS: dict[str, dict[str, EvaluationFn]] = {"python": {}, "cpp": {}}
```
Migrate existing Python registrations (`_dispatch.py` lines 56-97) under `["python"]` with values byte-unchanged:
```python
FRONTENDS["python"] = _build_cav_python
PRIMITIVES["python"]["functions"] = _extract_functions   # etc. (4 entries)
EVALUATIONS["python"]["class_diagram"] = _extract_class_diagram   # etc. (7 entries)
```

**Registration-time slot guard — extend to iterate both language dims** (`_dispatch.py` lines 106-112, RESEARCH line 211):
```python
# BEFORE:
for _eval_key in EVALUATIONS:
    if _eval_key not in _CONTENT_FIELDS: raise AssertionError(...)
# AFTER:
for _lang in EVALUATIONS:
    for _eval_key in EVALUATIONS[_lang]:
        if _eval_key not in _CONTENT_FIELDS: raise AssertionError(...)
```
Slot names are shared across languages, so cpp keys validate against the same `CodeContent` fields — this is exactly what makes LNG-04 parity automatic (D-02).

**Append-only idiom** (`_dispatch.py` lines 45-54, docstring lines 8-11): bottom-of-module imports + `DICT[key] = fn` assignment, never overwriting an existing key. C++ entries are appends within the language sub-dict (future Java = add `["java"]`).

---

### `lib_code_parser/executor.py` (MODIFY — D-03 one-line-per-walk language selection)

**Analog:** self. The PRIMITIVES/EVALUATIONS walks (`executor.py` lines 91, 121).

**Frontend selection already correct** (`executor.py` lines 70-84): `language = config.language`; suffix→cpp override; `FRONTENDS[language]`. This stays as-is (RESEARCH line 209 — executor already does `FRONTENDS[language]` correctly today).

**Change the two walks to index by `cav.language`** (D-03, the ONLY executor body change):
```python
# BEFORE (line 91):  for name, primitive_fn in PRIMITIVES.items():
# AFTER:             for name, primitive_fn in PRIMITIVES[cav.language].items():
# BEFORE (line 121): for name, eval_fn in EVALUATIONS.items():
# AFTER:             for name, eval_fn in EVALUATIONS[cav.language].items():
```
The contracts-gating (`executor.py` lines 92-93) and ContractInfo merger (lines 104-108) are language-agnostic and unchanged — they key on the shared `"contracts"`/`"functions"` slot names. `_CPP_EXTENSIONS` (line 29) already exists.

---

### `lib_code_parser/models/primitives/contracts.py` (MODIFY — additive SourceKind, D-08)

**Analog:** self. The `SourceKind` Literal (`contracts.py` lines 26-31).

**Additive extension — append `"doxygen"`, delete/rename nothing** (RESEARCH lines 333-338):
```python
SourceKind = Literal[
    "pydantic_validator",
    "pydantic_model_validator",
    "pydantic_field_validator",
    "dataclass_post_init",
    "doxygen",                       # ADDITIVE — D-08 (single value; kind discriminates pre/post/invariant)
]
```
`ContractKind` (line 34) already has `precondition`/`invariant`/`postcondition` — `\post`→`postcondition` maps cleanly, no `ContractKind` change. Single-value `"doxygen"` is recommended over 3 values (keeps Python/C++ symmetric; RESEARCH lines 345, A4).

---

### `.github/workflows/ci.yml` (MODIFY — mandatory CI matrix)

**Analog:** self. The `sp3-libclang-spike` job (`ci.yml` lines 23-64) — copy its structure (checkout → setup-python with `allow-prereleases` → `pip install -e ".[dev]"` → libclang smoke steps).

**Graduate to mandatory matrix** (LNG-01/02, RESEARCH §CI Matrix):
- Mandatory (no `continue-on-error`): Linux x86_64/aarch64 + Windows x86_64 × Python 3.11–3.14
- Keep macOS arm64 × 3.13/3.14 with `continue-on-error: true` (LNG-02 best-effort — the existing `sp3-libclang-spike` job is the seed)
- Reuse the verified smoke steps already in the spike job (lines 43-58): `Index.create()`, `Config.library_path` assertion, minimal C++ parse
- **PLANNER ACTION (Assumption A2):** confirm current GitHub Actions Linux arm64 runner label (`ubuntu-24.04-arm`) vs QEMU + `manylinux2014_aarch64` fallback

---

### `docs/09-extending.md` (MODIFY — language dimension + invariant doc)

**Analog:** self. The §"EdgeKind 追加は MAJOR version 案件" section (`09-extending.md` lines 182-226) is the policy template for the additive-Literal note.

**Add per D-03/D-08:**
1. Language-dimension dispatch procedure + "language keys are append-only" invariant (mirror the §"dispatch dict への entry 追加手順" lines 230-315, adding a "新言語の extractor セット追加" subsection)
2. Revise invariant #6 (`09-extending.md` lines 126-153) to note the **one-time** executor `cav.language` indexing change (D-03 explicitly revises "executor body does not grow" for the language axis only)
3. Additive-`SourceKind` policy note: "Literal の追記は additive 拡張として許容、既存値の削除・改名は禁止" — same wording as the EdgeKind MAJOR policy (lines 184-213)

---

### Test files

**`tests/conftest.py` — add `build_cpp_cav`** (analog: `build_python_cav`, `conftest.py` lines 13-21):
```python
def build_python_cav(source: str, path: str) -> CAV:
    return CAV(language="python", path=path, payload=ast.parse(source))
```
C++ analog: `build_cpp_cav(source, path)` parses via libclang (guarded) and stashes the `TranslationUnit` — mirror image so cpp extractor tests share ONE CAV builder (RESEARCH Wave-0 gap, line 464).

**`tests/unit/frontends/test_cpp_frontend.py`** (analog: `test_python_frontend.py`, exact): mirror the seven behaviors — language discriminator, payload type, raw_content carry, utf-8 replace decode, single-parse gate, path carry. Add `test_missing_include_warns` (LNG-05: diagnostics warning, cursor tree still built — RESEARCH line 452).

**`tests/unit/frontends/test_cpp_guard.py`** (analog: `test_python_frontend.py:test_build_cav_propagates_syntax_error` pattern, lines 62-65): assert `RuntimeError` on ABI mismatch / `set_library_file` override / dylib load failure (LNG-03/DET-02).

**`tests/acceptance/test_cpp_class_diagram.py` + `test_cpp_doxygen_contracts.py`** (analog: `test_dia01_class_diagram.py`, exact): drive the public `CodeParserExecutor.execute()` surface, read `result.content.class_diagram` / `.contracts`. Assert edge spectrum `{inherits, composes, aggregates, associates}` and `"uses" not in kinds` (lines 35-49). Use `.cpp`/`.h` path so the executor suffix-override selects the cpp track.

**`tests/parity/test_cpp_python_schema_parity.py`** (analog: `test_v01_v02_compat.py`, role-match): structural assertion that the cpp `NormalizedArtifact` has identical Pydantic shape (same `CodeContent` slots) as Python (LNG-04).

**`tests/unit/test_dispatch.py` — MODIFY** (self-evolution, lines 37-61): the existing `test_primitives_dict_has_4_entries_in_append_only_order` / `test_evaluations_registered_append_only` assert flat key lists. Update to assert the nested shape: `list(PRIMITIVES["python"].keys()) == [...]` + `"cpp" in PRIMITIVES` + extend the WR-01 slot guard test (lines 69-80) to iterate both language dims.

---

## Shared Patterns

### Language guard (assert payload type)
**Source:** every primitive/evaluation extractor, e.g. `extractors/primitives/functions.py` lines 81-84
**Apply to:** ALL cpp primitive + evaluation extractors
```python
assert isinstance(cav.payload, clang.cindex.TranslationUnit), (
    f"<name> extractor requires C++ CAV (TranslationUnit payload), got {type(cav.payload).__name__}"
)
```
This documents the precondition the nested dispatch (D-01) enforces. NEVER branch on `cav.language` inside an extractor (invariant #2 anti-pattern).

### Sort-on-exit (DET-04)
**Source:** `extractors/evaluations/class_diagram.py` lines 362-364; `extractors/primitives/callgraph.py` lines 93-94
**Apply to:** ALL cpp extractors (absorbs libclang's nondeterministic cursor traversal order)
```python
nodes.sort(key=lambda n: n.node_id)
edges.sort(key=lambda e: (e.source, e.target, e.edge_type, e.label))
# CallGraph: edges.sort(key=lambda e: (e.caller, e.callee))
# guards:    guards.sort(key=lambda g: (g.from_state, g.to_state, g.condition, g.action))
```
Ordered dedup via `list(dict.fromkeys(...))` before sorting (verbatim idiom).

### libclang import-time runtime guard (D-07 / LNG-03 / DET-02)
**Source:** new (no Python analog — Python frontend has no native dep). RESEARCH §Code Examples lines 361-400 is the verified skeleton.
**Apply to:** `frontends/cpp.py` module-level lazy init, called first thing in `build_cav`
- DET-02 ABI assertion via `importlib.metadata.version("libclang") == "18.1.1"` — **NEVER FFI-poke** `conf.lib.*.restype` (Pitfall 2 — hard segfault reproduced twice)
- Reject `Config.set_library_file` override (LNG-03); verify `Config.library_path` resolves into bundled `clang/native/`
- `Index.create()` once as a dylib smoke test; on failure raise `RuntimeError` with platform-specific install hint
- Idempotent (`_READY` flag) — runs real work once; Python-only callers never import this module (no-I/O-at-import preserved)

### TRC-03 trace-tag regex (parity-critical — copy verbatim)
**Source:** `extractors/primitives/functions.py` line 32
**Apply to:** `cpp_functions.py` + `cpp_contracts.py` (fed by `cursor.raw_comment` instead of docstring)
```python
_TRACE_TAGS_RE = re.compile(r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)", re.MULTILINE)
```
Must be byte-identical so `Traces: REQ-ID, US-NN` extraction behaves the same for Python docstrings and C++ Doxygen comments (TRC-03 parity, D-09). Recommend a shared helper in `_cpp_cursor.py`.

### Model reuse (LNG-04 parity — invariant #1)
**Source:** `models/primitives/{functions,callgraph,type_deps,contracts}.py`, `models/evaluations/graph_base.py`
**Apply to:** ALL cpp extractors — emit the EXISTING Pydantic shapes unchanged (`FunctionNode`, `CallEdge`/`CallGraph`, `TypeDep`, `ContractInfo`/`ContractEntry`, `GraphNode`/`GraphEdge`/`GraphModel`). The ONLY model touch in Phase 4 is the additive `SourceKind="doxygen"` value (D-08). Output slot names (`class_diagram`, `contracts`, …) are shared across languages — structural parity, not coincidental.

### "associates" undecidable fallback (never catch-all)
**Source:** `docs/09-extending.md` lines 215-226; `class_diagram.py:_classify_name` line 135
**Apply to:** `cpp_class_diagram.py`, `cpp_type_deps.py`
Use `"associates"` for type relations that are decidable-as-reference-but-undecidable-as-ownership (template-dependent, unresolved, unknown class). NEVER add `"uses"`/`"other"`/`"misc"` (EdgeKind is a closed 11-value Literal; new values are a MAJOR-version + sibling-coordination case).

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| libclang runtime guard logic in `frontends/cpp.py` | guard | n/a | No native-dependency guard exists in the Python track (pure stdlib `ast`). Use RESEARCH §Code Examples skeleton (lines 361-400) — verified live, not a codebase analog. |
| `cpp_state_diagram.py` detection body | evaluation | n/a | Python FSM detection is library-anchored (`transitions`, `python-statemachine`, `Enum`); no portable deterministic C++ FSM idiom exists. The OUTPUT (empty `GraphModel`) has an analog; the detection body has none. PLANNER must confirm scope (Assumption A1). |

**Partial-analog note:** `.github/workflows/ci.yml` mandatory matrix and the Linux arm64 runner mechanism (Assumption A2) have only the in-repo `sp3-libclang-spike` job as a seed; the multi-platform/Python-version matrix structure is new YAML (agent discretion per CONTEXT.md).

---

## Metadata

**Analog search scope:** `lib_code_parser/frontends/`, `lib_code_parser/extractors/primitives/`, `lib_code_parser/extractors/evaluations/`, `lib_code_parser/models/`, `lib_code_parser/_dispatch.py`, `lib_code_parser/executor.py`, `tests/{conftest,unit/frontends,unit,parity,acceptance}/`, `docs/09-extending.md`, `.github/workflows/ci.yml`
**Files scanned (read in full):** python.py, _dispatch.py, executor.py, functions.py, class_diagram.py, contracts.py (extractor), contracts.py (model), cav.py, callgraph.py, component_diagram.py, state_diagram.py, config.py, type_deps.py, package_diagram.py, 09-extending.md, conftest.py, test_python_frontend.py, test_dispatch.py, ci.yml, test_dia01_class_diagram.py, test_v01_v02_compat.py (partial)
**Pattern extraction date:** 2026-06-02
```
