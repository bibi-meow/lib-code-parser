# Requirements: lib-code-parser (spec_reviewer_code_parser)

**Defined:** 2026-05-24
**Core Value:** コードから構造化された全アーキ表現 (primitives / diagrams / specs) を、`lib-diagram-parser` が spec から抽出するものと **同形式・最大忠実度・決定論的に** 抽出する。物理↔論理ギャップの解釈は verifier (LLM agent) の責務。

## User Stories

本 lib は spec-reviewer 検証パイプラインの上流 Parser として下記 US を物理側から支える:

- **US-01** (spec → code 意味一致検証): caller が code から抽出した `FunctionNode.contracts` / 関数仕様 / クラス仕様 を `spec_code_verifier` に提供する
- **US-22** (code → spec 意味一致検証): US-01 と対称、code 側を一次資料とする検証で同上を提供する
- **US-25** (architecture リバース): caller が 5 種の diagram (class / sequence / component / package / state) を physical artifact として抽出できる
- **US-32** (物理アーキ比較): caller が `architecture_verifier` に lib-diagram-parser 互換 schema の物理アーキを供給できる

## v1 Requirements

42 件。Apache-2.0 ライセンスで配布する pip パッケージ `spec_reviewer_code_parser` v0.2.0 の責務範囲。

### AST primitives (5)

- [x] **AST-01**: Caller can extract function/method/class nodes (`FunctionNode`) with `kind`, `params`, `return_type`, `docstring`, `trace_tags`, `source_range` from Python source
- [x] **AST-02**: Caller can extract a deterministic `CallGraph` (nodes + caller→callee edges) from Python source via the lib's internal extractor — no GPL deps, no external subprocess
- [x] **AST-03**: Caller can extract type-resolved `TypeDep` list from Python source via `pyright` subprocess wrapper (handles import statements + annotation types)
- [x] **AST-04**: Caller can extract `ContractInfo` distinguishing Pydantic v2 validator decorators (`field_validator` / `model_validator` / `validator`) from `dataclass.__post_init__` blocks (separate `source_kind` discriminator)
- [x] **AST-05**: All AST primitive extractors operate on a single Common AST View (CAV) — file is parsed once per `execute()` call, not four times

### Diagram extractors (7)

- [x] **DIA-01**: Caller can extract class diagram (class nodes + inheritance + composition/aggregation/association edges; composition vs aggregation via type-annotation rule, `association` fallback when undecidable)
- [x] **DIA-02**: Caller can extract sequence diagram with linear call flow from call graph (branch fidelity `alt`/`loop`/`par` is SP-2 spike — falls back to v2 if spike fails)
- [x] **DIA-03**: Caller can extract component diagram (file/module-level component nodes + import-derived dependency edges)
- [x] **DIA-04**: Caller can extract package diagram (directory/namespace hierarchy with **`node_type="package"`** — multiple packages per project supported; sibling lib `lib-diagram-parser` enum gets new value)
- [x] **DIA-05**: Caller can extract state diagram from FSM explicit patterns: (a) library-anchored AST detection for `transitions.Machine(...)` and `python-statemachine.StateMachine`, (b) native `Enum` + transition-method pattern
- [x] **DIA-06**: State diagram extractor performs **return-value substitution analysis** for non-literal state mutations — when `self.state = self._next()` is found, callee's return statements are resolved (intra-class, N-level recursive, cycle-safe); fully-resolved cases emit all edges; unresolvable cases emit placeholder edge with `unresolved=true` attribute
- [x] **DIA-07**: All 5 diagram outputs serialize to `lib-diagram-parser`-compatible `GraphNode` / `GraphEdge` / `GraphModel` / `GuardExpr` schema; physical-only metadata uses optional `physical_*` / `source_*` prefix fields

### Spec extractors (4)

- [x] **SPC-01**: Caller can extract function spec (signature + structured docstring + pre/post conditions) from Python source — supports Sphinx Napoleon / Google / NumPy docstring styles
- [x] **SPC-02**: Caller can extract class spec (class definition + members + invariants) from Python source
- [x] **SPC-03**: Caller can extract function/class spec from C++ source via Doxygen `\pre` / `\post` / `\invariant` markers (Python/C++ symmetric output schema)
- [x] **SPC-04**: Caller can extract auxiliary Python contract markers from `icontract` / `deal` decorators and PEP-316 `pre:` / `post:` docstring keywords (supplementary to Pydantic / dataclass)

### Language support (5)

- [ ] **LNG-01**: Library installs and runs on CPython 3.11, 3.12, 3.13, 3.14 on Linux x86_64 / aarch64 and Windows x86_64 (strong guarantee — CI mandatory matrix)
- [ ] **LNG-02**: Library installs on macOS arm64 + Python 3.13+; runtime operation is observed but not guaranteed in v0.2.0 (CI continue-on-error; full guarantee deferred to v0.3.0)
- [x] **LNG-03**: Library import triggers runtime guard that calls `cindex.Index.create()` once; on dylib load failure raises clear `RuntimeError` with platform-specific install instructions
- [x] **LNG-04**: All AST primitive extractors (AST-01..05) and diagram extractors (DIA-01..07) work on C++ source via `libclang==18.1.1` with output schema parity to Python source
- [x] **LNG-05**: C++ extractors accept caller-supplied compile flags via `ParserConfig.params.compile_args` (default `["-std=c++17"]`, unresolved `#include` directives produce warnings not errors)

### Architecture (5)

- [ ] **ARC-01**: Each extractor module (`ast_extractor`, `callgraph_builder`, `type_dep_builder`, `contract_extractor`, `class_diagram`, `sequence_diagram`, `component_diagram`, `package_diagram`, `state_diagram`, `function_spec`, `class_spec`, `doxygen_extractor`) is lib-internal callable independently — importable and usable without instantiating `CodeParserExecutor`
- [ ] **ARC-02**: Extractor modules communicate only via Pydantic model contracts — no direct cross-module function calls between extractors
- [x] **ARC-03**: All subprocess invocations (`pyright`) live in `lib_code_parser/adapters/` layer; adapter canonicalizes output (sort by composite keys, normalize paths to forward-slash, strip timestamps, force `LC_ALL=C`)
- [ ] **ARC-04**: Module-name derivation is centralized in `lib_code_parser/_paths.py:get_module_name()` — no duplicated `_get_module_name` across extractor files
- [ ] **ARC-05**: `ParserConfig.params: dict[str, object]` is replaced with typed Pydantic fields: `language: Literal["python", "cpp"]`, `extract_contracts: bool`, `compile_args: list[str]`, `python_version: str`

### Determinism (5)

- [ ] **DET-01**: Library output is byte-identical for the same `(raw_content, path, ParserConfig)` tuple across re-runs, machines, and OS — verified by snapshot tests that diff JSON dump of `NormalizedArtifact` between 3 consecutive runs
- [x] **DET-02**: `libclang==18.1.1` exact pin enforced; runtime ABI assertion at import rejects `Config.set_library_file` overrides and verifies the bundled library version via `cindex.Config.library_path`
- [x] **DET-03**: `pyright[nodejs]==1.1.409` exact pin; subprocess invocation sets `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` to prevent npm pyright drift
- [x] **DET-04**: All extractor outputs are sorted by stable composite keys before emission — `FunctionNode` by `node_id`, `CallGraph.edges` lexicographic by `(caller, callee)`, `TypeDep` by `(node_id, type_ref)`
- [ ] **DET-05**: All subprocess calls (`pyright`, future tools) use `capture_output=True`, `encoding="utf-8"`, `env={..., "LC_ALL": "C", "PYTHONHASHSEED": "0"}`, `timeout=60`, and explicit `cwd` (no inherited `os.getcwd()`)

### Schema (4)

- [ ] **SCH-01**: `lib_code_parser` imports `lib-diagram-parser>=0.1.0` `GraphNode` / `GraphEdge` / `GraphModel` / `GuardExpr` models directly via `from lib_diagram_parser import ...` — no model duplication, single source of truth
- [ ] **SCH-02**: Physical-side schema extensions use optional fields with `physical_` or `source_` prefix (e.g., `physical_module: str`, `source_range: SourceRange`) to mark "physical-side only" data invisible to logical-side comparisons
- [ ] **SCH-03**: All Pydantic models defined in this lib use `model_config = ConfigDict(extra="forbid")` to fail loudly on unknown fields and catch silent schema drift
- [ ] **SCH-04**: Cross-lib schema compatibility test (`tests/test_schema_compat.py`) imports both `lib-code-parser` and `lib-diagram-parser` models and asserts structural compatibility on representative `GraphModel` instances; CI gates merges on this test

### Traceability (3)

- [ ] **TRC-01**: Each requirement in this file maps to at least one US (US-01 / US-22 / US-25 / US-32) in the Traceability table below
- [x] **TRC-02**: Each extractor module's module-level docstring declares which REQ-IDs it implements (e.g., `"""Implements AST-01, AST-05."""`)
- [x] **TRC-03**: `TraceTag` extraction (`Traces: REQ-ID, US-NN` regex pattern from docstrings/Doxygen comments) is retained from v0.1.0 and works identically for both Python and C++ source

### Documentation (4)

- [ ] **DOC-01**: `lib-code-parser.md` spec is updated in Phase 1 to (a) remove `callgraph.py` + "ACL-2" references (Lisp theorem prover misidentification), (b) reflect all Key Decisions from PROJECT.md, (c) cite Apache-2.0 license
- [ ] **DOC-02**: `README.md` documents the platform compatibility matrix (OS × Python version × C++ availability) with a clear "strongly supported" / "best-effort" distinction
- [ ] **DOC-03**: `README.md` documents that no GPL-licensed tools are bundled; call graph is internal; pyright is MIT; libclang is Apache-2.0+LLVM exception
- [ ] **DOC-04**: `pyproject.toml` declares `license = "Apache-2.0"`, `license-files = ["LICENSE"]`, and includes `LICENSE` file with patent grant clause

## v2 Requirements

Deferred to v0.3.0+. Tracked but not in v0.2.0 roadmap.

### Diagrams

- **DIA-02-FULL**: Sequence diagram with full branch fidelity (`alt` / `loop` / `par` Mermaid frames) — depends on SP-2 spike result
- **DIA-05-FULL**: General control flow → state diagram extraction (beyond explicit FSM patterns) — depends on SP-1 spike result

### Language

- **LNG-02-FULL**: macOS arm64 + Python 3.13+ full libclang compatibility guarantee (today: continue-on-error CI)
- **LNG-06**: Additional language support (Java / TypeScript / Rust) via dedicated frontend modules

### Distribution

- **DIST-01**: pip package split into multiple distributions (e.g., `spec_reviewer_code_parser_cpp` optional extra with libclang isolated)
- **DIST-02**: External call graph tool integration if a MIT/Apache-licensed deterministic OSS emerges

### Verification (not in this lib)

- **VRF-01**: CrossHair symbolic execution integration (defers to a future `lib-symbolic-verifier` consumer of this lib's `ContractInfo`)

## Out of Scope

Inherits from PROJECT.md §Out of Scope. Listed for traceability:

| Feature | Reason |
|---------|--------|
| LLM 統合 / 自然言語解釈 | 決定論性違反 (Layer M bisimulation 前提) — verifier 側の責務 |
| 動的解析 (runtime tracing) | 静的解析のみ — spec の範疇外 |
| 自然文 spec 生成 | 構造化データで足りる |
| OAS / OpenAPI / IDL からのコード生成 | リバースエンジニアリングのみ |
| テストコード解析 | 別 lib (`lib-test-parser` 相当) の責務 |
| pyan3 / その他 GPL 系 call graph OSS subprocess | GPL viral 回避、内製で代替 (MIT/Apache 決定論的 OSS 不在) |
| `compile_commands.json` 自動探索 | source code reverse のみ、binary/build artifacts に触れない |
| system-installed libclang (`clang` 別 PyPI パッケージ) | 自己完結性失う |
| 汎用制御フロー由来の状態遷移 (rule 構築不可なら) | SP-1 spike 失敗時は v2 |

## Definition of Done (Release Criteria for v0.2.0)

v0.2.0 リリース時に下記が全て満たされていること:

- [ ] 42 件の v1 requirements が全て `[x]` (実装完了 + テスト合格 + commit 済み)
- [ ] CI mandatory matrix (Linux x86_64 / aarch64 + Windows x86_64, Python 3.11/3.12/3.13/3.14) が green
- [ ] CI best-effort matrix (macOS arm64 + Python 3.13/3.14) が観測継続 (落ちても block しない)
- [ ] Snapshot test (DET-01) が 3 連続実行で byte-identical
- [ ] Cross-lib schema compat test (SCH-04) が green
- [ ] v0.1.0 baseline の Validated requirements (PROJECT.md §Validated) を 1 件も regression していない
- [ ] `pyproject.toml` の Apache-2.0 license が正しく宣言され `LICENSE` ファイルが同梱
- [ ] README に platform compat matrix が明記
- [ ] `lib-code-parser.md` spec 修正が commit 済み (DOC-01)
- [ ] `lib-diagram-parser` 側に `node_type="package"` PR が merge 済み (DIA-04 の前提)

## Acceptance Criteria

各 REQ は次のいずれかの観測可能な確認を持つこと:

- 単体テスト (pytest) で input → output が assert される
- snapshot/golden test で出力が固定 fixture と byte-identical
- CI gate で実機の install/import/runtime が成功
- 別 lib 連携テストで cross-lib 互換が成立
- (DOC 系のみ) ファイルが存在 + 内容が記載要件を満たす

詳細な acceptance criteria は Phase 1 で各 REQ について PLAN.md 内に展開される。

## Traceability

| Requirement | Phase | US support | Status |
|-------------|-------|------------|--------|
| AST-01 | Phase 2 | US-01, US-22 | Pending |
| AST-02 | Phase 2 | US-01, US-22, US-25 | Pending |
| AST-03 | Phase 2 | US-01, US-22 | Pending |
| AST-04 | Phase 2 | US-01, US-22 | Pending |
| AST-05 | Phase 2 | US-01, US-22, US-25, US-32 | Pending |
| DIA-01 | Phase 3 | US-25, US-32 | Pending |
| DIA-02 | Phase 3 | US-25, US-32 | Pending |
| DIA-03 | Phase 3 | US-25, US-32 | Pending |
| DIA-04 | Phase 3 | US-25, US-32 | Pending |
| DIA-05 | Phase 3 | US-25, US-32 | Pending |
| DIA-06 | Phase 3 | US-25, US-32 | Pending |
| DIA-07 | Phase 3 | US-25, US-32 | Pending |
| SPC-01 | Phase 3 | US-01, US-22 | Pending |
| SPC-02 | Phase 3 | US-01, US-22 | Pending |
| SPC-03 | Phase 4 | US-01, US-22 | Pending |
| SPC-04 | Phase 3 | US-01, US-22 | Pending |
| LNG-01 | Phase 4 | US-01, US-22, US-25, US-32 | Pending |
| LNG-02 | Phase 4 | US-01, US-22, US-25, US-32 | Pending |
| LNG-03 | Phase 4 | US-01, US-22, US-25, US-32 | Pending |
| LNG-04 | Phase 4 | US-01, US-22, US-25, US-32 | Pending |
| LNG-05 | Phase 4 | US-01, US-22, US-25, US-32 | Pending |
| ARC-01 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| ARC-02 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| ARC-03 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| ARC-04 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| ARC-05 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| DET-01 | Phase 5 | US-01, US-22, US-25, US-32 | Pending |
| DET-02 | Phase 4 | US-01, US-22, US-25, US-32 | Pending |
| DET-03 | Phase 2 | US-01, US-22 | Pending |
| DET-04 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| DET-05 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| SCH-01 | Phase 1 | US-25, US-32 | Pending |
| SCH-02 | Phase 1 | US-25, US-32 | Pending |
| SCH-03 | Phase 1 | US-25, US-32 | Pending |
| SCH-04 | Phase 5 | US-25, US-32 | Pending |
| TRC-01 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| TRC-02 | Phase 2 | US-01, US-22, US-25, US-32 | Pending |
| TRC-03 | Phase 2 | US-01, US-22, US-25, US-32 | Pending |
| DOC-01 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| DOC-02 | Phase 5 | US-01, US-22, US-25, US-32 | Pending |
| DOC-03 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |
| DOC-04 | Phase 1 | US-01, US-22, US-25, US-32 | Pending |

**Coverage:**
- v1 requirements: **42** total
- Mapped to phases: **42** ✓
- Unmapped: **0** ✓

**Phase distribution:**
- Phase 1 (Architecture Foundation + Spec Correction): 14 requirements — ARC-01..05, SCH-01..03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01
- Phase 2 (Python Frontend + AST Primitives + ACL-2 Adapters): 8 requirements — AST-01..05, DET-03, TRC-02, TRC-03
- Phase 3 (Python Diagram + Spec Extractors): 10 requirements — DIA-01..07, SPC-01, SPC-02, SPC-04
- Phase 4 (C++ Frontend + C++ Extractors): 7 requirements — LNG-01..05, SPC-03, DET-02
- Phase 5 (Cross-Cutting Integration + Acceptance): 3 requirements — DET-01, SCH-04, DOC-02

---

*Requirements defined: 2026-05-24*
*Last updated: 2026-05-24 after roadmap creation — Traceability table populated, 42/42 mapped*
