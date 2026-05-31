# lib-code-parser (spec_reviewer_code_parser)

## What This Is

Python (現状) と C++ (新規) のソースコードから、構造化されたアーキテクチャ表現を
**決定論的に・最大忠実度で・spec 側と同形式で** 抽出する pip ライブラリ。
spec-reviewer パイプラインの `spec_code_verifier` (US-01/US-22) と `architecture_verifier`
(US-32) に物理アーキの入力を供給する Parser lib として機能する。

## Core Value

**コードから抽出する全てのアーキ表現が、`lib-diagram-parser` が spec から抽出するものと
同形式で比較可能であること。** 物理 (code) と論理 (spec) の表現幅ギャップの解釈は
verifier (LLM agent) の責務であり、本 lib は事実抽出のみを担って決定論性を維持する。
これが崩れると Layer M bisimulation (構造一致判定) が成立せず、検証パイプライン全体が機能しない。

## Requirements

### Validated

<!-- v0.1.0 で実装済み・shipped (commit cf7e7ec) -->

- ✓ AST ベースの `FunctionNode` 抽出 (class / method / function + params, return_type, docstring, trace_tags, source_range) — v0.1.0
- ✓ AST ベースの `CallGraph` (nodes + caller→callee edges) — v0.1.0
- ✓ AST ベースの `TypeDep` (import 文 + 型アノテーション由来) — v0.1.0
- ✓ Pydantic v2 `ContractInfo` 抽出 (`field_validator` / `validator` / `model_validator` / `__post_init__`) — v0.1.0
- ✓ `ParserConfig` ベースの gating (`enabled` / `params.language` / `params.extract_contracts`) — v0.1.0
- ✓ 純粋関数的設計 (no I/O, no LLM, no network, no clock) — v0.1.0
- ✓ Trace tag 抽出 (`Traces: FR-01, US-03` パターン) — v0.1.0
- ✓ pip 配布可能な単一パッケージレイアウト — v0.1.0

### Active

<!-- v0.2.0 で目指す scope -->

**A. AST primitives 強化:**
- [ ] §3.7 Contract 抽出の精密化: Pydantic validator と dataclass `__post_init__` を区別 (現状 unconditional)
- [ ] 内製 call graph extractor の強化 — 既存 `callgraph_builder.py` を v0.2.0 で拡張 (pyan3 不採用; GPL viral 回避 + 決定論性自明 + schema 完全制御)
- [ ] `pyright` subprocess 統合 — 型解決済み `TypeDep` 取得 (Python)。Microsoft MIT、`[nodejs]` extra で Node bundle
- [ ] アンチパターン解消 — `_get_module_name` 4 重複の共通化
- [ ] アンチパターン解消 — AST 4 回再パースを 1 回に集約 (CAV = Common AST View 化)
- [ ] アンチパターン解消 — `ParserConfig.params: dict[str, object]` を typed field 化
- [ ] spec 修正 — `lib-code-parser.md` の `callgraph.py` + "ACL-2" 表記を削除 (存在しない tool への参照)

**B. Diagram 抽出 (5 種、`lib-diagram-parser` と同形式の structured graph data + 物理メタデータ):**
- [ ] クラス図抽出 — class 定義 + 継承 + 集約関係 (composition vs aggregation は py2puml 流の type-annotation 由来規則 + 不明時は `association` フォールバック)
- [ ] シーケンス図抽出 — call graph + 制御フロー (linear が must-have、branch fidelity (alt/loop/par) は spike SP-2)
- [ ] コンポーネント図抽出 — module/file 境界 + import 依存
- [ ] パッケージ図抽出 — directory 構造 + namespace 階層 (file = package を 1 単位として複数 package 表現)
- [ ] 状態遷移図抽出 — FSM 明示パターン (enum + transition method、library-anchored `transitions` / `python-statemachine` AST 検出) **must-have**
- [ ] 状態遷移図抽出 — 非リテラル state mutation の **return-value substitution 解析** (`self.state = self._next()` を見つけたら `_next()` の return statements を再帰的に解決し、全 return が state literal なら全 edge を emit。N 階層、cycle detection 付き)
- [ ] 状態遷移図抽出 — 汎用制御フロー由来の状態抽出 **spike SP-1 (決定論的ルール構築可否を検証)**
- [ ] **lib-diagram-parser 側 contract 変更**: `node_type="package"` enum 値追加の提案 (sibling lib coordination)

**C. Spec 抽出 (`lib-spec-parser` と並列):**
- [ ] 関数仕様抽出 (Python) — signature + docstring (Google/NumPy/Sphinx Napoleon) + pre/post conditions の構造化
- [ ] クラス仕様抽出 (Python) — class definition + members + invariants の構造化
- [ ] Doxygen 契約抽出 (C++、**TS 昇格**) — `\pre` / `\post` / `\invariant` を解析し contract に変換 (Python/C++ 対称性確保)
- [ ] icontract / deal / PEP-316 (`pre:`/`post:` docstring keywords) スキャン (Python、補助的)

**D. 言語サポート:**
- [ ] Python: stdlib `ast` (現状継続) + `pyright[nodejs]==1.1.409` subprocess (型解決) + 内製 call graph extractor (callgraph_builder.py 拡張)
- [ ] C++: `libclang==18.1.1` 厳密 pin (ctypes ベースなので Python 3.13/3.14 にも pip install 可) + import 時 runtime guard で明確エラー
- [ ] macOS arm64 + Python 3.13+ の libclang 実機動作を Phase 1 で spike (Linux/Windows は強保証、macOS arm64 は CI continue-on-error)
- [ ] C++ compile flags は `ParserConfig.params["compile_args"]` 経由の caller 明示供給のみ (default `-std=c++17`、未解決 include は warning)
- [ ] LLVM org の libclang PyPI 新リリース監視 (出たら version 更新を検討)

**E. 内部アーキテクチャ:**
- [ ] 疎結合モジュラー設計 — 各 extractor を独立して lib-internal で呼び出し可能に
- [ ] Module 間契約 — Pydantic model のみで依存、直接呼び出しなし
- [ ] CAV (Common AST View) — 1 回 parse の Pydantic envelope を各 extractor に渡す。AST 4 回再パースを解消
- [ ] subprocess は `adapters/` 層に隔離 — extractor からは Pydantic model 経由でのみアクセス
- [ ] アーキ設計 phase を独立 — 実装着手前にアーキを固定

**F. Traceability:**
- [ ] US-01 (spec→code 意味一致) / US-22 (code→spec 意味一致) / US-25 (architecture リバース) / US-32 (物理アーキ比較) を REQUIREMENTS で固定
- [ ] 各 extractor module がどの US を支えるかを明示

### Out of Scope

- **CrossHair による symbolic execution 統合** — spec (lib-code-parser.md §3.7) で "可能" 止まり。今ミルストンの Core Value から外れる
- **LLM 統合** — 本 lib は決定論性が要件 (Layer M bisimulation の基盤)。表現幅ギャップの解釈は verifier 側の責務
- **動的解析 (runtime tracing)** — 静的解析のみ。spec の範疇外
- **自然文 spec 生成** — 構造化データのみで足りる (verifier が比較に使うだけ)
- **汎用制御フロー由来の状態遷移抽出** — SP-1 spike で決定論的ルール構築不可と判明したら次ミルストンへ
- **pip パッケージ分割** — 今は 1 lib (`spec_reviewer_code_parser`)。内部 module 分離まで。pip パッケージ分割は v0.3.0 以降に実需 (依存サイズ / 配布粒度) が出てから検討
- **OAS / OpenAPI / IDL からのコード生成** — リバースエンジニアリングのみ
- **テストコード解析** — 本 lib はプロダクトコードのみ対象 (`lib-test-parser` 相当は別 lib)
- **pyan3 / GPL ライセンス系 call graph OSS の subprocess 統合** — GPL viral 回避のため内製 extractor を採用 (MIT/Apache の決定論的 call graph OSS が存在しないため)
- **`compile_commands.json` 自動探索** — source code reverse のみ、binary/build artifacts には触れない。compile flags は caller 明示供給
- **macOS arm64 + Python 3.13+ の libclang 完全動作保証** — Phase 1 spike 結果次第。動作不可なら v0.3.0 に延期 (今ミルストンは Linux/Windows 強保証 + macOS arm64 経過観察)
- **system-installed libclang (`clang` 別 PyPI パッケージ)** — bundled 無しで user 側に libclang.so install を要求するため自己完結性を失う

## Context

**プロジェクト位置づけ:**
- `spec-reviewer-libs/` workspace 配下の 7 lib のうちの 1 つ
- 兄弟 libs: `lib-spec-parser`, `lib-diagram-parser`, `lib-logical-consistency-prover`, `lib-scdl-builder`, `lib-sysml-v2-parser`, `spec-reviewer` (orchestrator)
- 上位プロジェクト `spec-reviewer` で消費される pip 配布物

**Spec ドキュメント:**
- `lib-code-parser.md` (project root) が target behavior を記述
- §3.7 Pydantic / dataclass validator (variants catalog §4.3 Pattern 3 Contract) を採用
- US-01, US-22, US-25, US-32 への対応が明文化されている

**v0.1.0 baseline:**
- commit `cf7e7ec` で AST-only 実装が shipped 済み
- commit `f1a2bda` で codebase map (`.planning/codebase/`) 作成済み
- ARCHITECTURE.md に既知 anti-patterns が列挙済み

**消費先:**
- `spec_code_verifier`: spec から抽出した期待仕様と本 lib の `FunctionNode.contracts` / 関数仕様 / クラス仕様 を比較 (US-01/US-22)
- `architecture_verifier`: spec の埋め込み図 (lib-diagram-parser 経由) と本 lib の diagram 出力を比較 (US-32)
- 外部ツール: `pyright` (subprocess、MIT) と `libclang` (in-process、ctypes、Apache-2.0+LLVM 例外) は本 lib 内部から呼ばれる。call graph は内製 (subprocess 不要)

## Constraints

- **Tech stack**: Python `>=3.11` (上限なし; 3.13/3.14 サポート), Pydantic `>=2.13.0,<3.0`, stdlib `ast`, `pyright[nodejs]==1.1.409` (subprocess), `libclang==18.1.1` (in-process ctypes、厳密 pin)
  — spec と兄弟 libs の整合性。pyan3/ACL-2/callgraph.py は不採用 (spec 表記は Phase 1 で訂正)
- **Determinism**: LLM / network / clock / 動的解析を一切使わない。出力は `(raw_content, path, config)` の純粋関数
  — Layer M bisimulation の前提条件
- **I/O policy**: ライブラリは I/O・ログ出力・設定読込を一切行わない。呼び出し側が bytes + path を渡す
  — caller-agnostic 原則 (兄弟 libs と同じ規約)
- **Distribution**: 単一 pip パッケージ `spec_reviewer_code_parser`
  — リポジトリ作成済み、配布名確定
- **Schema compatibility**: Diagram 出力は `lib-diagram-parser` 互換 schema (物理側追加メタデータは optional フィールドで)
  — verifier が同形式で比較できることが Core Value の前提
- **言語**: Python と C++ を最初から対象。"Python-first, C++-later" の段階分けは取らない
  — user 指示 (2026-05-23 QUESTIONING)
- **アーキ重視**: 実装前にアーキを独立 phase で固定する
  — 内部疎結合 + lib-internal 呼び出し可能性が要件
- **既存資産**: v0.1.0 (commit cf7e7ec) を baseline とし、互換性破壊は Key Decisions に明示する場合のみ

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| pip package 名 = `spec_reviewer_code_parser` | spec (lib-code-parser.md) で指定、リポジトリ作成済み | ✓ Good |
| Output schema = `lib-diagram-parser` ベース + 物理側追加メタデータ (optional フィールド) | verifier が両者を同形式で比較可能。物理は表現幅が広いので拡張余地を残す | — Pending |
| 物理↔論理ギャップの解釈は verifier (LLM agent) の責務、本 lib は事実抽出のみ | lib の決定論性維持 (Layer M bisimulation 前提)。責務分離 | — Pending |
| C++ 解析 = `libclang==18.1.1` 厳密 pin (ctypes ベース、bundled .so/.dll、3.13/3.14 互換性は ctypes 経由) + import 時 runtime guard | AST 正確性 + 型解決可 + 決定論性 (tree-sitter-cpp は syntactic のみ、`clang` 別パッケージは bundled なし)。LLVM org PyPI 引取後の新リリース待ち中 | — Pending |
| Python type 解析 = `pyright[nodejs]==1.1.409` subprocess (Microsoft MIT、Node bundled) | 型解決済み TypeDep、JSON schema 安定 (`generalDiagnostics`)、内製 AST より正確 | — Pending |
| **Call graph = 内製 extractor 拡張** (pyan3 不採用) | MIT/Apache の決定論的 call graph OSS が存在しない (pyan3=GPL v2, code2flow=非決定論, PyCG=archived)。内製なら license 完全クリア + 決定論性自明 + schema 完全制御 | — Pending |
| **spec 修正**: `lib-code-parser.md` の `callgraph.py` + "ACL-2" 表記を削除 | ACL-2 は Common Lisp 定理証明器であり call graph tool ではない。`callgraph.py` も該当 PyPI/GitHub artifact なし (live verified 2026-05-24) | — Pending |
| Python target = `>=3.11` (上限なし、3.13/3.14 サポート) | libclang ctypes ベース wheel が `py2.py3-none-platform` で 3.13+ pip install 可。Linux/Windows は強保証、macOS arm64 + 3.13+ は continue-on-error 経過観察 | — Pending |
| C++ compile flags = `ParserConfig.params["compile_args"]` 明示供給 (default `-std=c++17`、未解決 include は warning) | source code reverse のみ、binary/build artifacts (`compile_commands.json`) は触れない (user 指示 2026-05-24) | — Pending |
| **Doxygen 契約抽出 = Table Stakes 昇格** (C++ `\pre` / `\post` / `\invariant`) | Python は docstring + Pydantic validator から契約抽出するため、C++ も対称に対応しないと verifier の処理が非対称になる (user 指示 2026-05-24) | — Pending |
| **lib-diagram-parser `node_type="package"` 値追加** = sibling lib contract 変更を提案 | file = package を 1 単位として複数 package を表現する必要 (user 指示 2026-05-24)。`attributes.granularity` での区別では不十分 | — Pending |
| **FSM 非リテラル state mutation = return-value substitution 解析** (intra-class、N 階層再帰、cycle detection) | 明示パターンのみ + 検出を諦めるのではなく、`_next()` 等の helper method の return statements を解析することで決定論的に edge 抽出可能 (user 指示 2026-05-24) | — Pending |
| 1 pip lib + 内部疎結合 module 設計 (各 extractor が lib-internal で independently callable) | アーキ重視。pip 分割は早期最適化を避ける | — Pending |
| FSM 抽出 = 明示パターン (enum + transition method) + return-value substitution が must-have、汎用制御フロー由来は SP-1 spike | 決定論性を崩さない。spike 結果次第で次ミルストンへ送る | — Pending |
| アーキ設計を独立 phase で先に固める (実装着手前) | "アーキが重要" の user 指針。疎結合設計は後付け不可 | — Pending |
| Python と C++ を最初から対象 (段階分けしない) | spec が "もともと Python だけじゃない" 想定で書かれている (user 指示 2026-05-23) | — Pending |
| CAV (Common AST View) = 1 回 parse の Pydantic envelope で全 extractor に渡す | v0.1.0 のアンチパターン (AST 4 回再パース) を解消、且つ Frontend/Aspect 層境界を明確化 | — Pending |
| subprocess は `adapters/` 層に隔離 | extractor から subprocess を直接呼ばないことで no-I/O 原則と決定論性を維持。adapter 内で正規化 (タイムスタンプ除去・ソート・パス正規化) | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-31 — Phase 2 complete: Python Frontend (CAV single-parse) + 4 pure-CAV extractors + opt-in pyright adapter + v0.1.0 clean break; 241 tests green*
