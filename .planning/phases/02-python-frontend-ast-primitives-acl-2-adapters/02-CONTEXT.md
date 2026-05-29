# Phase 2: Python Frontend + AST Primitives + ACL-2 Adapters - Context

**Gathered:** 2026-05-29
**Status:** Ready for planning

<domain>
## Phase Boundary

v0.2.0 の **Python 物理アーキ抽出 path を end-to-end で稼働させる phase**。
Phase 1 で固定した foundation (CAV envelope / typed ParserConfig / `_dispatch.py` 空 dict /
`adapters/base.py` subprocess hardening) を消費し、以下を実装する:

- **`frontends/python.py`** — `raw_content: bytes` を `ast.parse()` で **1 回だけ** 解析し、
  `CAV(language="python", path=..., payload=ast.Module)` を返す Python Frontend (AST-05)
- **`extractors/primitives/functions.py`** (AST-01) — CAV consumer、`FunctionNode` list 生成
- **`extractors/primitives/callgraph.py`** (AST-02) — CAV consumer、内製 caller→callee `CallGraph` 生成
  (GPL deps なし / 外部 subprocess なし)
- **`extractors/primitives/type_deps.py`** (AST-03) — CAV を基準 + `adapters/pyright.py` の
  PyrightAdapter 経由で `pyright[nodejs]==1.1.409` から型解決済み `TypeDep` list を取得
- **`extractors/primitives/contracts.py`** (AST-04) — CAV consumer、
  `source_kind ∈ {pydantic_validator, pydantic_field_validator, pydantic_model_validator, dataclass_post_init}`
  を **各 contract entry 単位で discriminator** として付与
- **`adapters/pyright.py`** — `SubprocessAdapter` ABC の subclass、PyrightAdapter 実装、
  determinism env + canonicalization (sort / forward-slash 正規化 / tmpdir prefix strip)
- **`executor.py` rewrite** — Plan 09 deviation の予告どおり、`FRONTENDS` / `PRIMITIVES` dict 走査型に
  書き換え。barrel `lib_code_parser.ParserConfig` を typed 版 (`models.infrastructure.config.ParserConfig`)
  に統一 (stub 廃止)
- **v0.1.0 legacy 4 ファイル削除** — `ast_extractor.py` / `callgraph_builder.py` /
  `contract_extractor.py` / `type_dep_builder.py` を全削除 (clean break)
- **parity test 再設計** — name surface 13 names + `_get_module_name` no-duplication gate は **保持**、
  JSON byte-identical (stub 経由) は **廃止**、shipped v0.1.0 fixture snapshot test に置換

**スコープに含まれる Requirements (8 件):** AST-01, AST-02, AST-03, AST-04, AST-05, DET-03, TRC-02, TRC-03

**スコープに含まれないもの:**
- C++ Frontend (`frontends/cpp.py`) と libclang 統合 → Phase 4
- 評価単位 extractor (5 diagrams + 2 specs) → Phase 3
- README platform compat matrix (DOC-02) → Phase 5
- Cross-lib schema compat test (SCH-04) と byte-identical snapshot test 完成形 (DET-01) → Phase 5
- 兄弟 lib (`lib-diagram-parser` 等) への変更

</domain>

<decisions>
## Implementation Decisions

### G-1: v0.1.0 legacy 4 ファイル + ParserConfig stub の処理

- **D-01:** **Clean break** 方針を採用 (user 指示: 「しっかりときれいに、レガシーは毒」)。Phase 2 完了時点で:
  - `lib_code_parser/ast_extractor.py` / `callgraph_builder.py` / `contract_extractor.py` /
    `type_dep_builder.py` を **全削除**
  - barrel `lib_code_parser.ParserConfig` (v0.1.0 stub、`params: dict[str, object]` 形式) を
    **typed 版 (`lib_code_parser.models.infrastructure.config.ParserConfig`) に差し替え**
  - barrel ParserConfig の single source of truth を typed 版に集約 (legacy stub 廃止)
- **D-02:** v0.1.0 caller の `ParserConfig(artifact_type=..., executor_lib=..., params={"language": ..., "extract_contracts": ...})`
  形式は **明示的 break**。代わりに typed fields (`language: Literal["python","cpp"]`,
  `extract_contracts: bool`, `compile_args: list[str]`, `python_version: str`) を使う。
  Rationale: v0.2.0 は internal lib の minor bump、PROJECT.md §Constraints の「互換性破壊は
  Key Decisions に明示する場合のみ」要件を本 D-02 で満たす。
- **D-03:** **`executor.py` rewrite**: `_dispatch.py` の `FRONTENDS` / `PRIMITIVES` dict 走査型に
  書き換え。executor は dict を for-loop し、frontend で CAV 生成 → primitives を順に走査して
  `CodeContent` を組み立てる。executor 本体に新 extractor 追加時の修正は発生しない (Open-Closed
  invariant #6)。
- **D-04:** **parity test 再設計** (`tests/parity/test_v01_v02_compat.py`):
  - **保持**: name surface 13 names の importability gate (Phase 3 以降の symbol drift 検出として
    実用価値あり)
  - **保持**: `_get_module_name` no-duplication hard gate (Phase 1 で確立、Phase 2 以降も
    accidental 重複を検出)
  - **廃止**: stub 経由の JSON byte-identical parity (Plan 09 D-06 で確立した parity stub assertion)
    — typed ParserConfig 経由に変わるため stub assertion は無意味化
  - **新規**: **shipped v0.1.0 fixture snapshot test** — Phase 1 で記録された v0.1.0 baseline 出力
    (commit cf7e7ec 時点の `tests/conftest.py` `EXAMPLE_SOURCE` を typed ParserConfig 経由で実行した
    結果) を JSON snapshot として fix し、Phase 2 以降の output drift を検出する

### G-2: AST-03 PyrightAdapter の解析モード・失敗ハンドリング

- **D-05:** **解析モード = internal tmpdir + write bytes** (caller-agnostic I/O 維持)。
  PyrightAdapter は `tempfile.TemporaryDirectory()` で context manager 風 tmpdir を作成、
  `raw_content` を `{tmpdir}/{module_name}.py` に書き出し、pyright をその tmpdir を cwd として
  起動する。 lib の caller-visible I/O は維持 (caller は bytes と path 文字列だけを渡し、
  caller の file system 状態には依存しない)。
- **D-06:** **失敗時セマンティクス = fail loudly (RuntimeError)** — pyright 未インストール /
  startup 失敗 / timeout (60s 既定、DET-05) / JSON parse 失敗 のいずれも `RuntimeError` を
  上位に伝搬する。silent empty (空 `TypeDep` 化) は **採用しない**。
  Rationale: `pyright[nodejs]==1.1.409` は本 lib の install dependency なので未インストールは
  caller 環境問題。silent 化は DET-01 byte-identical の前提を環境状態に依存させてしまい、
  Layer M bisimulation の前提が崩れる。
- **D-07:** **JSON 正規化原則**:
  - `pyright --outputjson` 出力のうち **`TypeDep` 生成に必要な subkey のみ抽出**
    (`generalDiagnostics` は破棄)
  - file path は **forward-slash 正規化** (`pathlib.PurePosixPath` 等で `\` → `/`)
  - tmpdir prefix を strip して caller が渡した `path` 文字列のみを `TypeDep.path` に出力
  - sort key は `(node_id, type_ref)` (DET-04 と整合)
  - **具体的な pyright JSON subkey 名・抽出 algorithm は researcher 領域** (Phase 2 RESEARCH.md で
    `gsd-phase-researcher` が pyright 1.1.409 の `--outputjson` schema を実機検証し、
    `TypeDep` への mapping を確定する)
- **D-08:** **pyright CLI フラグ・サブコマンド選定は researcher 領域** — `--outputjson` /
  `--verifytypes` / `--ignoreexternal` 等のうち、import 文 + 型注釈の type 解決済み一覧を
  最も忠実に返す組み合わせは RESEARCH.md で確定。CONTEXT.md には選定基準 (型解決済み /
  決定論的 / 既存 `pyright[nodejs]==1.1.409` で完結) のみ記載。
- **D-09:** **DET-03 強制**: `PyrightAdapter` は subprocess env に
  `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` を必ず付加し、pyright wrapper script が npm 経由の
  drift を起こさないようにする (PROJECT.md Key Decision より)。

### G-3: AST-04 `source_kind` 判別の粒度

- **D-10:** **ROADMAP success criteria 3 で 4 値 Literal が固定** (`pydantic_validator` /
  `pydantic_field_validator` / `pydantic_model_validator` / `dataclass_post_init`)。
  Phase 2 では 5 値目を追加せず、既存 4 値への mapping のみ確定する。
- **D-11:** **Pydantic decorator → source_kind mapping 表**:

  | 検出対象 decorator | source_kind |
  |------------------|-------------|
  | `@validator` (Pydantic v1 + v2 deprecated alias) | `pydantic_validator` |
  | `@field_validator` (Pydantic v2 explicit) | `pydantic_field_validator` |
  | `@model_validator` (Pydantic v2 explicit) | `pydantic_model_validator` |
  | `@root_validator` (Pydantic v1 deprecated、v2 で `@model_validator` に統合) | `pydantic_model_validator` ← **semantic equivalent としてマップ** |
  | `__post_init__` (stdlib dataclass + Pydantic dataclass の両方) | `dataclass_post_init` |

  Rationale: `@root_validator` は Pydantic v1 で `@model_validator` の前身。`pydantic_model_validator`
  バケットに集約することで Literal 4 値を維持しつつ legacy codebase も検出可能。
- **D-12:** **集約粒度 = (β) 各 contract entry に `source_kind` 付与** — `ContractInfo` は
  class 単位で 1 entry (v0.1.0 通り)、内部に validator-list を保持し、各 entry が
  `(source_kind, body_excerpt, line_no, decorator_name)` を持つ。
  Rationale: verifier (spec_code_verifier) は contract-statement レベルで比較するため、
  ContractInfo 内で source_kind を集約してしまうと verifier 側が再展開する必要が生じ、
  「verifier 側で物理↔論理ギャップを解釈する」という Core Value (PROJECT.md) の責務分離を
  破壊する。物理側 (本 lib) は **事実の最大忠実度抽出** が責務。
- **D-13:** **混在 case 自動サポート** — Pydantic dataclass + `__post_init__` 同居 case、
  または通常 class で `@field_validator` + 手動 `__post_init__` 同居 case は、D-12 (β) 採用により
  別 rule なしで表現可能 (同 `ContractInfo` 内に複数 entry を異なる source_kind で並存)。
  AST-04 success criteria 「verifier が `__post_init__` を unconditional Pydantic 扱いしないこと」
  は D-11 + D-12 の組み合わせで満たす。
- **D-14:** **`models/primitives/contracts.py` 既存 model 拡張** — Phase 1 で生成済みの
  `ContractInfo` Pydantic model に、各 entry が `source_kind: Literal[...]` を持つよう
  field 追加 (extra="forbid" 維持、Optional ではなく required)。具体的な field 名・list 構造は
  Phase 2 planner が `models/primitives/contracts.py` の Phase 1 出力を読んで決定。

### Claude's Discretion (Phase 2 planner / researcher が決定)

- **AST-02 内製 CallGraph の解像度** (G-5、議論外): method 呼び出し表現 (`self.foo()` → `Class.foo`
  vs `self.foo`)、chain call (`a.b().c()`) の edge 分解、intra-file vs cross-import resolution の
  境界。 ROADMAP success criteria 2 の「lexicographic by (caller, callee)」だけを invariant とし、
  v0.1.0 `callgraph_builder.py` の表現 (parity baseline) を Phase 2 planner が研究して継承 or 拡張する
- **AST-05 「1 回 parse」の hard gate test 戦略** (G-4、議論外): (i) `monkeypatch ast.parse` の
  call count assertion / (ii) `grep -c "ast\.parse" lib_code_parser/extractors/` 静的 gate /
  (iii) extractor signature が `cav.payload` のみ受け取る構造制約 — 複数併用も安価、planner が
  RESEARCH.md と CONTEXT.md を読んで test 戦略を確定
- **TRC-02 module docstring の REQ-ID 宣言形式**: 既存 `Traces: REQ-ID, US-NN` regex に整合する形で
  各 extractor module の docstring 冒頭に `Implements: AST-NN` 等を記載。具体的な docstring
  template は planner 判断
- **TRC-03 trace tag extraction parity**: v0.1.0 で確立した `Traces:\s*([A-Z]+-\d+...)` regex は
  そのまま保持。新規 extractor module でも同 regex で抽出されることを test で確認
- ファイル内部の関数命名 / private helper 名 / module docstring の細部表現は標準慣習 + 既存
  `lib_code_parser/` の convention に従って planner が判断
- pyright JSON parse 実装の error path (例えば JSON schema validation の Pydantic model 化など) は
  D-06 fail-loudly の枠内で planner が判断

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (researcher / planner / executor) MUST read these before planning or implementing.**

### Phase 2 直接根拠

- `.planning/PROJECT.md` — Core Value、16 Key Decisions、Constraints (Tech stack /
  Determinism / I/O policy / 言語 / アーキ重視 / 既存資産)
- `.planning/REQUIREMENTS.md` — 42 件全体および本 Phase 8 件 (AST-01..05, DET-03, TRC-02, TRC-03)
  と Traceability 表 / Definition of Done / Acceptance Criteria
- `.planning/ROADMAP.md` §Phase 2 — 4 success criteria
  (single `ast.parse()` per file / internal callgraph + pyright TypeDep / `source_kind` 4 値 /
   各 extractor の isolated import-and-call)
- `lib-code-parser.md` (project root、Phase 1 で full rewrite 済み) — v0.2.0 全方針
  (CAV / EdgeKind / pyright MIT / Apache-2.0 / Traceability) の現行 spec

### Phase 1 carry-forward (Phase 2 が依存する locked decisions)

- `.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md` — Phase 1
  CONTEXT.md (D-01..D-23、特に D-04/D-05 CAV、D-08 execute signature、D-10/D-11/D-12 nested
  layout + pull-based primitives + dispatch dict 走査、D-09 SubprocessAdapter ABC、D-13
  Open-Closed 6 不変条件、D-14 論理アーキ比較対象 = `models/evaluations/` 配下のみ)
- `.planning/phases/01-architecture-foundation-spec-correction/01-VERIFICATION.md` — Phase 1
  14/14 truths verified passed (commit 0afdb7d)
- `.planning/phases/01-architecture-foundation-spec-correction/01-09-SUMMARY.md` — Plan 09 deviation
  記録 (barrel ParserConfig stub の Phase 2 graduation 予告 + name surface 13 names parity gate
  仕様 + JSON byte-identical parity stub の Phase 2 廃止予告)
- `.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md` — Phase 1 research
  (pyright 1.1.409 PyPI verify、libclang wheel verify、Pydantic v2 Generic 検証)
- `.planning/spikes/SP-3-libclang-macos-arm64.md` — SP-3 verdict (Phase 2 は libclang を触らないので
  reference のみ、Phase 4 入口で再評価)

### 既存コードベース (Phase 1 終了時点の locked layout)

- `lib_code_parser/_paths.py` — `get_module_name()` single source (ARC-04 / DET-04、
  Phase 2 でも引き続き SoT)
- `lib_code_parser/_dispatch.py` — `FRONTENDS` / `PRIMITIVES` / `EVALUATIONS` 空 dict
  (Phase 2 で `FRONTENDS["python"]` + `PRIMITIVES["functions"]` + `PRIMITIVES["call_graph"]` +
   `PRIMITIVES["type_deps"]` + `PRIMITIVES["contracts"]` の 5 entry を登録)
- `lib_code_parser/adapters/base.py` — `SubprocessAdapter` ABC + `run_subprocess()` helper
  (DET-05 6 不変条件、Phase 2 PyrightAdapter が subclass)
- `lib_code_parser/models/infrastructure/cav.py` — `CAV(language, path, payload)` Pydantic model
  (Phase 2 frontends/python.py が `payload=ast.Module` 形式で生成)
- `lib_code_parser/models/infrastructure/config.py` — typed `ParserConfig` (ARC-05、Phase 2 で
  barrel に graduation)
- `lib_code_parser/models/infrastructure/artifact.py` — `ArtifactId` / `NormalizedArtifact` /
  `CodeContent` (Phase 2 で executor 出力に使用、Generic 化済み D-06)
- `lib_code_parser/models/primitives/functions.py` — `FunctionNode` / `ParamInfo` / `SourceRange`
  / `TraceTag` (Phase 2 AST-01 が emit)
- `lib_code_parser/models/primitives/callgraph.py` — `CallEdge` / `CallGraph` (Phase 2 AST-02 が
  emit、edge sort key は DET-04 で固定済み)
- `lib_code_parser/models/primitives/type_deps.py` — `TypeDep` (Phase 2 AST-03 が emit)
- `lib_code_parser/models/primitives/contracts.py` — `ContractInfo` (Phase 2 AST-04 で `source_kind`
  discriminator 追加、D-12/D-14 参照)
- `tests/parity/test_v01_v02_compat.py` — Phase 1 で確立、Phase 2 で D-04 のとおり再設計
- `tests/conftest.py` `EXAMPLE_SOURCE` fixture — Phase 2 snapshot test の入力 fixture
- `tests/acceptance/test_fr0N_*.py` (v0.1.0) — Phase 2 で typed ParserConfig 経由に書き換え、
  v0.1.0 baseline 出力との parity を保証

### 拡張点契約 (Phase 2 が必ず守る)

- `docs/09-extending.md` — Open-Closed 6 不変条件 (#1 既存 primitive 変更不可 / #2 既存評価単位
  変更不可 / #3 `CodeContent` 追加は optional field / #4 dispatch dict は append-only / #5
  評価単位は primitives を pull / #6 executor は dispatch 走査のみ)。 Phase 2 では特に #4
  (新規 PRIMITIVES entry 追加) と #6 (executor rewrite で dispatch 走査固定) を満たす

### コードベース現状 (Phase 1 完了時点のスナップショット)

- `.planning/codebase/ARCHITECTURE.md` (analysis_date: 2026-05-23、**Phase 1 前**) — v0.1.0 の
  flat layout 記録。Phase 2 着手前に Phase 1 完了状態を反映した最新 STRUCTURE は不要
  (Phase 2 で実装後に refresh する想定)
- `.planning/codebase/CONCERNS.md` — v0.1.0 anti-patterns (Phase 1 で `_get_module_name` 重複と
  AST 4 回再パース と `params: dict` を全て解消済み)。 Phase 2 で再導入しないことを self-check

### 兄弟 lib (read-only — Phase 2 では触らない)

- `c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser/` — Phase 3 入口で再評価。
  Phase 2 は AST primitives のみで diagram は扱わないため interaction なし

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`lib_code_parser/ast_extractor.py`** (v0.1.0): pure-function AST walk、`FunctionNode` 生成
  ロジック → **Phase 2 で `extractors/primitives/functions.py` に書き換え** (CAV consumption に
  signature 変更)。実装本体は Phase 2 で write して legacy は削除 (D-01)
- **`lib_code_parser/callgraph_builder.py`** (v0.1.0): pure-function call graph 構築 →
  同様に `extractors/primitives/callgraph.py` に書き換え
- **`lib_code_parser/contract_extractor.py`** (v0.1.0): `_PRECONDITION_DECORATORS` /
  `_INVARIANT_DECORATORS` frozenset 定数 + decorator 認識 logic → `extractors/primitives/contracts.py`
  で `source_kind` discriminator 追加版に書き換え (D-11/D-12)
- **`lib_code_parser/type_dep_builder.py`** (v0.1.0): import 文 + 型アノテーション解析 → Phase 2 は
  pyright subprocess に切り替えるため、v0.1.0 の logic は **parity baseline として参照のみ**
  (Phase 2 では pyright 出力経由で `TypeDep` を組み立てる、internal AST walk は使わない)
- **`tests/acceptance/test_fr*.py`** (v0.1.0): 6 acceptance tests → Phase 2 で typed ParserConfig
  経由に signature 修正、v0.1.0 fixture parity gate として継続使用

### Established Patterns

- **caller-agnostic I/O 原則**: Phase 2 で **強化** — PyrightAdapter は internal tmpdir で
  subprocess 入力を扱い、caller-visible I/O はゼロを維持 (D-05)
- **Pydantic v2 `model_config = ConfigDict(extra="forbid")`**: 全 model 必須 (SCH-03、Phase 1 で
  enforced)。Phase 2 で追加する model field (`ContractInfo` への `source_kind` 拡張等) も
  extra="forbid" の制約下
- **pure-function extractors + Pydantic model contracts**: Phase 1 D-11/D-12 で確定。Phase 2 の
  4 primitive extractor は `def extract(cav: CAV, config: ParserConfig) -> <Pydantic>` signature
- **dispatch dict 走査型 executor**: Phase 1 D-12 で確定、Phase 2 D-03 で実装
- **subprocess hardening helper (`run_subprocess`)**: Phase 1 で abstract、Phase 2 PyrightAdapter は
  subclass で hardening を継承 (DET-05 を新規実装しない)
- **DET-04 sort key**: 全 extractor 出力は `(node_id, ...)` 等の stable composite key で sort 後 emit。
  pyright 出力も `(node_id, type_ref)` で sort (D-07)
- **discriminator-based union**: 既存 `FunctionNode.kind ∈ {"function", "method", "class"}`
  pattern → Phase 2 で `ContractInfo` entry の `source_kind ∈ Literal[4 values]` に同型適用 (D-12)

### Integration Points

- **`__init__.py`** (Phase 1 完了時点で `__version__ = "0.2.0"`, 13 v0.1.0 names + 6 v0.2.0 names
  export): Phase 2 で legacy 4 ファイル削除に伴い、`from lib_code_parser.ast_extractor import ...`
  等の old internal path が消える。public API surface (13 + 6 names) は **維持** (D-04 name surface
  gate)
- **`pyproject.toml`**: Phase 1 で `pyright[nodejs]==1.1.409` を install dep に追加済み。Phase 2 で
  実装が稼働する (DET-03)。`libclang==18.1.1` は dev extra のまま (Phase 4 で graduation)
- **`tests/parity/test_v01_v02_compat.py`**: Phase 1 で 11 tests 確立。Phase 2 で D-04 のとおり
  再設計 (name surface + no-duplication は保持、stub 経由 JSON parity は廃止、snapshot test 追加)
- **`_dispatch.py`** registrations: Phase 2 で 1 frontend (python) + 4 primitives (functions /
  call_graph / type_deps / contracts) の合計 5 entry を登録。executor は dict 走査のみ
- **既知 anti-patterns** (Phase 1 で全解消、Phase 2 で再導入しない self-check 対象):
  - `_get_module_name` 重複 (Phase 2 の新 extractor も `from lib_code_parser._paths import
    get_module_name` を使う)
  - AST 4 回再パース (Phase 2 では frontends/python.py が 1 回 parse、4 primitives は CAV 経由のみ)
  - `params: dict[str, object]` (Phase 2 で typed ParserConfig に完全 graduation、D-01)

</code_context>

<specifics>
## Specific Ideas

- **「しっかりときれいに、レガシーは毒」** (user 指示、G-1 議論): Phase 2 完了時点で v0.1.0
  legacy ファイルと ParserConfig stub を全削除。dual-path 保守を許さない、clean break を選択。
  rationale はチャットで議論済み (B Hybrid 推薦に対し A Clean break を採用)
- **「caller-agnostic I/O 原則を PyrightAdapter でも維持する」** (G-2 議論): tmpdir + bytes 書き出し
  方式を採用し、(i) caller passes path on disk と (iii) caller passes project root は不採用。
  Phase 1 D-09 の SubprocessAdapter 設計思想を Phase 2 で実装側として実証
- **「fail loudly」原則** (G-2 議論): pyright 未インストール / startup 失敗 / timeout は
  RuntimeError 伝搬。 silent empty は DET-01 byte-identical の前提を環境状態に依存させるため不採用
- **「verifier 責務分離 = 物理側は事実の最大忠実度抽出」** (G-3 議論): ContractInfo 内で
  source_kind を集約してしまうと verifier 側が再展開する必要が生じ、Core Value の責務分離を
  破壊する。各 contract entry に source_kind を付与する (β) を採用
- **「ROADMAP 4 値 Literal を維持しつつ legacy decorator も検出可能」** (G-3 議論): `@root_validator`
  (v1 deprecated) を `pydantic_model_validator` バケットに semantic equivalent としてマップ。
  5 値目を追加しない

</specifics>

<deferred>
## Deferred Ideas

### Phase 3 入口で再評価
- **AST-02 内製 CallGraph の解像度拡張** (G-5): method 呼び出し / chain call / import 解決の
  表現幅。Phase 2 では v0.1.0 parity 優先で実装し、Phase 3 (DIA-02 sequence diagram) 着手時に
  call graph 表現力の不足が露呈すれば拡張を検討
- **`extractors/primitives/auxiliary_contracts.py` (SPC-04)** — icontract / deal / PEP-316 サポート
  は Phase 3 scope (REQUIREMENTS.md Traceability 表より)。Phase 2 では contracts.py に Pydantic +
  dataclass のみ実装

### Phase 4 入口で再評価
- **C++ frontend (`frontends/cpp.py`) + libclang 統合** — SP-3 verdict は ship-best-effort、Phase 4
  入口で再確認
- **DET-02 libclang ABI assertion** — Phase 4 scope

### Phase 5 入口で再評価
- **DET-01 byte-identical snapshot test 完成形** — Phase 2 で導入する v0.1.0 fixture snapshot
  test (D-04) を、Phase 3-4 の追加 extractor も含めた全体 snapshot として完成させる
- **SCH-04 cross-lib schema compat test** — Phase 5 scope (lib-diagram-parser との直接 import が
  必要、Phase 3 で sibling-lib coordination 状況が確定してから)
- **DOC-02 README platform compat matrix** — Phase 5 scope

### v0.3.0+ (next milestone) で検討
- **v0.1.0 caller compat layer の再導入** — もし v0.2.0 release 後に dict-style ParserConfig
  caller が外部に発生したら、deprecation shim を追加することを検討 (現時点では内部 baseline
  のみのため不要)

</deferred>

---

*Phase: 2-Python Frontend + AST Primitives + ACL-2 Adapters*
*Context gathered: 2026-05-29*
