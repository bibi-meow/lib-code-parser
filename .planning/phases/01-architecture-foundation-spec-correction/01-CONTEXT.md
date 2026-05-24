# Phase 1: Architecture Foundation + Spec Correction - Context

**Gathered:** 2026-05-24
**Status:** Ready for planning

<domain>
## Phase Boundary

lib-code-parser v0.2.0 の **cross-cutting 契約をすべてロックする foundation phase**。
extractor コードを書く前に、以下を不変契約として固定する:

- **CAV** (Common AST View) envelope の型と immutability
- **EdgeKind** taxonomy (closed Literal enum)
- **schema 互換境界** (`lib-diagram-parser` との contract、SCH-01/02/03)
- **subprocess hardening 契約** (`adapters/base.py`、DET-05)
- **dispatch table** (`_dispatch.py` で FRONTENDS / PRIMITIVES / EVALUATIONS の 3 dict)
- **`_paths.py:get_module_name()`** single source of truth (ARC-04 / DET-04)
- **typed `ParserConfig`** (`params: dict[str, object]` 廃止、ARC-05)
- **モジュール配置** (nested layout、`extractors/` 直下に評価単位 flat)
- **拡張点契約** (Open-Closed 6 不変条件、`docs/09-extending.md`)
- **Apache-2.0 license** 宣言 + `LICENSE` 同梱 (DOC-04)
- **spec doc `lib-code-parser.md` full rewrite** (DOC-01/DOC-03、`callgraph.py` + "ACL-2" 誤参照を削除 + v0.2.0 全方針反映)
- **SP-3 spike** (libclang `==18.1.1` の macOS arm64 + Python 3.13/3.14 feasibility)

スコープに含まれる Requirements: **ARC-01..05, SCH-01..03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01** (14 件)

スコープに含まれないもの:
- 各 extractor の **実装** (Phase 2-4 で実装)
- 兄弟 lib (lib-diagram-parser 等) への変更 (兄弟 lib 更新時に再リファクタする方針)
- workspace 共通規約 (`spec-reviewer-libs/CONVENTIONS.md`) の作成

</domain>

<decisions>
## Implementation Decisions

### D: DOC-01 spec doc 修正範囲

- **D-01:** `lib-code-parser.md` を **full rewrite** して v0.2.0 全方針 (内製 call graph、pyright MIT、libclang Apache-2.0、CAV、EdgeKind、5 diagram、function/class spec、Doxygen、icontract/deal、Apache-2.0 license、physical_*/source_* prefix、Traceability) に揃える。surgical edit は不採用 (内部の論理整合が崩れるため)。
- **D-02:** 旧版 (v0.1.0 時代) は `frozen/2026-05-24-v0.1.0-spec/` に退避してから rewrite (backup-before-major-rewrite ルール準拠)。
- **D-03:** rewrite 対象セクション: §概要 / §インターフェース / §出力 / §採用アルゴリズム / §出力 schema (新規) / §License (新規) / §Traceability (新規)。

### B: CAV (Common AST View) polymorphism

- **D-04:** **単一 `CAV` Pydantic BaseModel** + `language: Literal["python", "cpp"]` discriminator + opaque `payload: object` (Python: `ast.Module`、C++: `cindex.TranslationUnit`)。typed union は不採用 (Phase 4 拡張時に contract 変更になる)。
- **D-05:** CAV `model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True, frozen=True)`。immutability を Pydantic で強制。
- **D-06:** **`NormalizedArtifact` を Pydantic Generic 化** (`NormalizedArtifact[TContent]`)。各 lib が `content` の型を refine できる。v0.1.0 caller 互換性は parity test で確認。
- **D-07:** **共通 pattern doc** を `docs/08-common-view-pattern.md` に作成 (SDD chain 連番に組み込み)。lib-code-parser 内に閉じる (workspace 共通規約は作らない)。
- **D-08:** I/O 変更容易性確保: `execute(config, raw_content, path) -> NormalizedArtifact[CodeContent]` signature を安定に。`ParserConfig` の field 命名 (`enabled` / `language` / `extract_*` / `*_version`) は兄弟 lib にも転用可能な一般名で固定。
- **D-09:** `adapters/base.py` の subprocess hardening helper を **abstract base class + transferable helper** として書く (兄弟 lib が後で同 pattern を真似しやすい形)。

### A: モジュール配置レイアウト

- **D-10:** v0.1.0 flat (`lib_code_parser/*.py`) を **nested layout に再編**:
  ```
  lib_code_parser/
  ├── __init__.py
  ├── _paths.py                          # get_module_name() (ARC-04)
  ├── _dispatch.py                       # 3 dict (FRONTENDS / PRIMITIVES / EVALUATIONS)
  ├── executor.py
  ├── models/                            # 3 分割 (要件で分割)
  │   ├── infrastructure/                # 論理アーキ比較なし: lib I/O 契約
  │   │   ├── cav.py
  │   │   ├── artifact.py                # NormalizedArtifact[TContent], ArtifactId, CodeContent
  │   │   └── config.py
  │   ├── primitives/                    # 論理アーキ比較なし: AST 中間データ
  │   │   ├── functions.py
  │   │   ├── callgraph.py
  │   │   ├── type_deps.py
  │   │   └── contracts.py
  │   └── evaluations/                   # 論理アーキ比較対象 (verifier 直行)
  │       ├── graph_base.py              # GraphNode/Edge/Model/GuardExpr/EdgeKind (lib-diagram-parser 互換)
  │       ├── class_diagram.py
  │       ├── sequence_diagram.py
  │       ├── component_diagram.py
  │       ├── package_diagram.py
  │       ├── state_diagram.py
  │       ├── function_spec.py
  │       └── class_spec.py
  ├── frontends/                         # CAV を作る (1 parse/file)
  │   ├── python.py                      # Phase 2
  │   └── cpp.py                         # Phase 4
  ├── extractors/
  │   ├── primitives/                    # 共有 supplier ("インスタンスを取りに行く" 先)
  │   │   ├── functions.py               # AST-01
  │   │   ├── callgraph.py               # AST-02
  │   │   ├── type_deps.py               # AST-03
  │   │   ├── contracts.py               # AST-04 (Pydantic / dataclass)
  │   │   └── auxiliary_contracts.py     # SPC-04 (icontract / deal / PEP-316)
  │   ├── class_diagram.py               # 評価単位 #1 (DIA-01)
  │   ├── sequence_diagram.py            # 評価単位 #2 (DIA-02)
  │   ├── component_diagram.py           # 評価単位 #3 (DIA-03)
  │   ├── package_diagram.py             # 評価単位 #4 (DIA-04)
  │   ├── state_diagram.py               # 評価単位 #5 (DIA-05, DIA-06)
  │   ├── function_spec.py               # 評価単位 #6 (SPC-01 + C++ Doxygen 内包)
  │   ├── class_spec.py                  # 評価単位 #7 (SPC-02 + C++ Doxygen 内包)
  │   └── _doxygen.py                    # SPC-03 helper
  └── adapters/                          # subprocess 隔離
      ├── base.py                        # SubprocessAdapter abstract + hardening helper
      └── pyright.py                     # PyrightAdapter (Phase 2)
  ```
- **D-11:** **設計軸 = 評価単位 (output)**。同じ解析手法を使う複数評価単位は、共有 primitives を **pull で取得** (`from lib_code_parser.extractors.primitives import callgraph; callgraph.extract(cav)`)。
- **D-12:** **`_dispatch.py` で 3 dict 管理** (FRONTENDS / PRIMITIVES / EVALUATIONS)。executor は dict を走査して評価単位を実行 (`for name, fn in EVALUATIONS.items(): result[name] = fn(cav, config)`)。
- **D-13:** **拡張点契約 (Open-Closed)** を `docs/09-extending.md` に明記:
  1. 既存 primitive は変更不可 (新 primitive は別 file)
  2. 既存評価単位は変更不可 (新評価単位は別 file)
  3. `CodeContent` への追加は optional field で行う (v0.1.0 互換性維持)
  4. dispatch dict は append-only
  5. 評価単位は primitives を pull で取得 (push 型注入ではない)
  6. executor は dispatch dict 走査ロジックのみ (評価単位を増やしても変更しない)
- **D-14:** **論理アーキ比較対象は `models/evaluations/` 配下のみ**。primitives / infrastructure は中間データ / I/O 契約であり verifier に渡さない。このルールを `docs/09-extending.md` に明記。

### C: sibling-lib (lib-diagram-parser) PR タイミング

- **D-15:** **Phase 1 では PR を出さない**。Phase 3 着手時に状況を再評価:
  - lib-diagram-parser に `node_type="package"` 既存 → 直接 import (SCH-01 そのまま満足)
  - 未存在 → lib-code-parser 内に **local extension** (`models/evaluations/graph_base.py` で `GraphNode` を subclass + `node_type` Literal を拡張) で対応
- **D-16:** **SCH-01 の解釈拡大**: 「`lib-diagram-parser` モデルを直接利用する (subclass 含む)」を許容。model duplication は依然禁止。`.planning/REQUIREMENTS.md` の SCH-01 文言を Phase 1 で微更新。
- **D-17:** schema 互換性は **SCH-04 (cross-lib schema compat test)** で保証。Phase 1 では schema 契約のみ固定し、test 実装は Phase 5。

### E: SP-3 libclang spike 判定ルール

- **D-18:** **GitHub Actions `macos-14` (arm64) runner のみ**で実施。Python 3.13/3.14 matrix。user は対象環境を持っていないためローカル検証は行わない。
- **D-19:** **優先度: Phase 1 内で最低**。他タスク (DOC-01 rewrite / 構造再編 / dispatch 実装等) 完了後に着手。
- **D-20:** **テスト内容** (Phase 1 時点で確認可能なもの):
  - (a) `pip install lib_code_parser` (libclang 18.1.1 含む)
  - (b) `from clang.cindex import Index; Index.create()` (dylib load + ABI 一致)
  - (c) `cindex.Config.library_path` で `18.1.1` 確認 (DET-02 assertion)
  - (d) minimal C++ fixture (`"int main() { return 0; }"`) の `index.parse()`
- **D-21:** **判定ルール (4 段階)**:
  - (a)(b)(c)(d) 全 ✓ → **ship-best-effort**
  - (a)(b)(c) ✓ かつ (d) 限定的 failure → **ship-best-effort + 既知制限を README に open issue**
  - (a) ✓ (b) ✗ → **defer to v0.3.0** (dylib load 失敗 = ABI 不整合)
  - (a) ✗ → **defer to v0.3.0** (wheel 未配布)
- **D-22:** **Phase 1 close 条件 (緩和)**: CI workflow setup 完了 + 最初の run 1 回 kick + 暫定 verdict 記録。Phase 4 入口で verdict 再確認・更新可能 (= Phase 1 close を結果 blocking しない)。
- **D-23:** 記録先: `.planning/spikes/SP-3-libclang-macos-arm64.md` (CI run URL 込み)。

### Claude's Discretion

- ファイル内部の細かい命名 (関数名 / private helper 名 / module docstring の表現) は標準慣習に従って Claude が判断
- 各評価単位 extractor 内部の言語分岐実装パターン (if/elif vs dispatch dict 等) は Phase 2-4 plan-phase で詰める
- `docs/08-common-view-pattern.md` / `docs/09-extending.md` の文章スタイルと細部構成は Claude が判断 (SDD chain 既存ドキュメントの文体に合わせる)
- `.github/workflows/ci.yml` への SP-3 matrix 追加の具体的な YAML 構造は Phase 1 plan で詰める

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (researcher / planner / executor) MUST read these before planning or implementing.**

### Phase 1 直接根拠

- `.planning/PROJECT.md` — Core Value、16 Key Decisions、Constraints (Tech stack / Determinism / I/O policy / Distribution / Schema compatibility / 言語 / アーキ重視 / 既存資産)
- `.planning/REQUIREMENTS.md` — 14 件の Phase 1 requirements (ARC-01..05, SCH-01..03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01) と Definition of Done
- `.planning/ROADMAP.md` §Phase 1 — 5 success criteria (CAV/EdgeKind/ParserConfig/dispatch/`_paths.py`/`adapters/base.py`/spec doc/Apache-2.0/SP-3)
- `lib-code-parser.md` (project root) — **本 Phase で full rewrite される対象**。旧版は v0.1.0 baseline (commit cf7e7ec)

### 仕様根拠 (rewrite 後の参照ドキュメント)

- `docs/00-decision-log.md` — 既存設計判断 (v0.1.0)、Phase 1 で v0.2.0 追加判断を append
- `docs/06-architecture.md` — 既存アーキ説明、Phase 1 で nested layout 反映に rewrite
- `docs/07-spec.md` — 既存 API spec、Phase 1 で `NormalizedArtifact` Generic 化等を反映
- `docs/99-trace-matrix.md` — FR → AT → Code → Test traceability、Phase 1 で 14 件の Phase 1 REQ を反映

### 新規ドキュメント (Phase 1 で作成)

- `docs/08-common-view-pattern.md` — Common View pattern (CAV / Generic NormalizedArtifact / I/O 変更容易性) の transferable 記述。兄弟 lib が将来採用する際の参照モデル
- `docs/09-extending.md` — 拡張点契約 (6 不変条件) + 拡張シナリオ例 (DDD リバース / Annotated Call Graph + Data Flow Diagram 等)
- `.planning/spikes/SP-3-libclang-macos-arm64.md` — SP-3 spike 結果記録 (verdict + evidence + known limitations)
- `LICENSE` — Apache-2.0 license file (patent grant clause 含む、DOC-04)

### コードベース現状

- `.planning/codebase/ARCHITECTURE.md` — v0.1.0 アーキ (4 extractor + 1 executor + 1 models flat layout)
- `.planning/codebase/STRUCTURE.md` — v0.1.0 ディレクトリ構造、Where to Add New Code ガイド
- `.planning/codebase/CONCERNS.md` — 既知 anti-patterns (`_get_module_name` 4 重複、AST 4 回再パース、`params: dict[str, object]`)
- `.planning/codebase/CONVENTIONS.md` — 既存命名規約、Pydantic v2 model 規約

### 兄弟 lib (read-only — Phase 1 では触らない)

- `c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser/` — schema 互換境界の対向 lib。Phase 3 で `node_type="package"` enum 追加 PR を出すか、または local extension で迂回するかを再評価
- `c:/work/agent_company/spec-reviewer-libs/lib-spec-parser/` — 兄弟 Parser、I/O pattern 比較の参考
- `c:/work/agent_company/spec-reviewer-libs/` workspace — 共通規約は不在 (確認済み、2026-05-24)

### 既存研究成果

- `.planning/research/SUMMARY.md` — domain research synthesis
- `.planning/research/ARCHITECTURE.md` — Hexagonal / Clean Architecture pattern 検討
- `.planning/research/FEATURES.md` — 機能 catalog
- `.planning/research/PITFALLS.md` — 既知 pitfalls (CAV lock / EdgeKind ad-hoc / schema drift / Unicode normalization / sort-on-exit / spec misidentification の 6 件が Phase 1 の対象)
- `.planning/research/STACK.md` — tech stack 決定根拠

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`lib_code_parser/models.py`** (v0.1.0): 14 Pydantic models (FunctionNode / ParamInfo / SourceRange / TraceTag / CallEdge / CallGraph / TypeDep / ContractInfo / CodeContent / ArtifactId / NormalizedArtifact / ParserConfig) — Phase 1 で `models/{infrastructure,primitives,evaluations}/` に分割移動
- **`lib_code_parser/executor.py`** (v0.1.0): `CodeParserExecutor.execute()` orchestration — Phase 1 で dispatch dict 走査型に再編 (D-12)
- **`lib_code_parser/ast_extractor.py`** + 3 extractor (v0.1.0): pure-function AST walk — Phase 2 で `extractors/primitives/` 配下に移動・拡張 (CAV consumption に書き換え)
- **`tests/acceptance/test_fr*.py`** (v0.1.0): 6 acceptance tests — Phase 1 で v0.1.0 fixture parity test として転用 (`NormalizedArtifact` Generic 化が破壊しないことの確認)
- **`tests/conftest.py`** `EXAMPLE_SOURCE` fixture — そのまま継続使用

### Established Patterns

- **caller-agnostic I/O** (no I/O、no logging、no config 読込): Phase 1 で **強化** (subprocess も `adapters/` に隔離、ARC-03)
- **Pydantic v2 BaseModel 規約**: Phase 1 で **強化** (`extra="forbid"` 全 model 必須、SCH-03)
- **stateless pure-function extractors**: Phase 1 で **継承** (CAV を引数で受け取る形に変換)
- **discriminator-based union**: 既存 `FunctionNode.kind ∈ {"function", "method", "class"}` パターン → Phase 1 で `ContractInfo.source_kind` discriminator 追加 (D-04 と同型)
- **frozenset 定数**: 既存 `_CPP_EXTENSIONS` / `_PRECONDITION_DECORATORS` / `_INVARIANT_DECORATORS` → Phase 1 で `_paths.py` / `_dispatch.py` に移動・整理

### Integration Points

- **`__init__.py`**: public API surface 維持。v0.1.0 caller が `from lib_code_parser import CodeParserExecutor, NormalizedArtifact, FunctionNode, ...` を書けることを保証 (`__all__` 不変)
- **`pyproject.toml`**: Apache-2.0 license declaration + `LICENSE` file + dependency 追加 (`pyright[nodejs]==1.1.409`, `libclang==18.1.1`)
- **`.github/workflows/ci.yml`**: 現状 Ubuntu + Python 3.11 のみ → Phase 1 で SP-3 best-effort matrix (macos-14 + 3.13/3.14, continue-on-error) を追加。mandatory matrix (Linux x86_64/aarch64 + Windows x86_64 + Python 3.11..3.14) は Phase 4 で完成
- **既知 anti-patterns の解消** (Phase 1 で全て解決):
  - `_get_module_name` 4 重複 → `_paths.py` 単一化 (D-12, ARC-04)
  - AST 4 回再パース → CAV (Frontend が 1 回 parse) (D-04, ARC-02 / AST-05)
  - `params: dict[str, object]` → typed `ParserConfig` (D-08, ARC-05)

</code_context>

<specifics>
## Specific Ideas

- **「output が core ロジック」設計原則** (user 指摘): extractor の軸は評価単位 (verifier に渡す output)、解析手法ではない。同じ解析手法を使う複数評価単位は primitives でインスタンスを取得する (pull 型)。
- **「現 lib の考え方を残しつつ、兄弟 lib も後で同 pattern を採用しやすい変更容易性確保 I/O」** (user 指摘): `NormalizedArtifact` Generic 化、`ParserConfig` field 命名規約、`adapters/base.py` の transferable helper は、兄弟 lib が将来採用する際の参照モデルになる形で設計する。ただし兄弟 lib のコードには Phase 1 では触らない。
- **「兄弟 lib 更新時に再リファクタ」** (user 指示): workspace 共通規約 / sibling-lib PR / 兄弟 lib の I/O 揃えは Phase 1 では行わず、兄弟 lib が独自に v0.2.0 級進化を始めたタイミングで再度 coordinate する (Deferred Ideas 参照)。
- **「論理アーキ比較対象は何か」明示要求** (user 質問): `models/evaluations/` 配下のみが論理アーキと比較される (verifier に直行)。infrastructure (CAV / NormalizedArtifact / ParserConfig) と primitives (FunctionNode / CallGraph 等) は比較対象ではない (= 中間データ / I/O 契約)。
- **「DDD リバース」を将来評価単位候補として例示** (user 提供): 拡張点設計 (A + B 同時追加パターン) の好例。Phase 1 設計の拡張耐性を検証する材料。

</specifics>

<deferred>
## Deferred Ideas

### Workspace coordination (兄弟 lib 更新時に再評価)

- **workspace `spec-reviewer-libs/CONVENTIONS.md` 作成**: Common View pattern (CAV / Generic NormalizedArtifact / subprocess hardening / sort invariants 等) を 7 lib 共通規約として制定。**Triggering 条件**: 兄弟 lib のうち 2 個以上が同 pattern を採用し始めたタイミング
- **`NormalizedArtifact` / Container の workspace 共通 lib 化**: 例 `spec-reviewer-libs-common` lib として切り出し、7 lib が import する形にする。**Triggering**: 上記 CONVENTIONS.md 制定と同時
- **再リファクタ phase の起票**: lib-code-parser ↔ 兄弟 lib の I/O 揃え。**Triggering**: 兄弟 lib v0.2.0 級進化が並走し始めたタイミング

### Sibling-lib coordination (Phase 3 入口で再評価)

- **`lib-diagram-parser` に `node_type="package"` enum 追加 PR**: Phase 1 では出さず、Phase 3 (DIA-04) 着手時に状況再評価。**Triggering**: Phase 3 plan-phase で lib-diagram-parser 最新版に `"package"` 未存在の場合に判断
- **local extension 削除 → 直接 import switch**: 上記 PR が merge された後に、lib-code-parser 内の `GraphNode` subclass extension を削除。**Triggering**: sibling lib に `node_type="package"` 追加版がリリースされたタイミング

### Future evaluation units (将来評価単位の候補)

- **コードから DDD リバース** (拡張点 A+B 同時追加の好例):
  - (a) 新 primitives: `class_relations.py` (継承+集約+依存)、`naming_patterns.py` (Entity/VO 命名規約検出)、`module_groups.py` (BC 推測)
  - (b) 新評価単位: `ddd_context_map.py` (BC 関係図)、`ddd_aggregate.py` (Aggregate root+構成 Entity)、`ddd_layer_diagram.py` (Layered Architecture 検出)
  - **Triggering**: 別 milestone (v0.3.0+) の roadmap に組み込み

### Spike 関連 (Phase 4 入口で再評価)

- **Phase 4 入口で SP-3 verdict 再確認**: Phase 1 で記録した暫定 verdict を Phase 4 plan-phase 時に再評価。状況が変わっていれば judgement を更新
- **追加 spike**: Intel macOS (macos-13) / macOS-15 等の matrix を必要に応じて追加。**Triggering**: SP-3 verdict が defer または ship-best-effort の場合、Phase 4 plan-phase で評価

</deferred>

---

*Phase: 1-Architecture Foundation + Spec Correction*
*Context gathered: 2026-05-24*
