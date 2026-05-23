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
- [ ] ACL-2 統合 — `callgraph.py` を subprocess で呼び出し決定論的コールグラフ取得 (Python)
- [ ] ACL-2 統合 — `pyright` を subprocess で呼び出し型解決済み `TypeDep` 取得 (Python)
- [ ] アンチパターン解消 — `_get_module_name` 4 重複の共通化
- [ ] アンチパターン解消 — AST 4 回再パースを 1 回に集約
- [ ] アンチパターン解消 — `ParserConfig.params: dict[str, object]` を typed field 化

**B. Diagram 抽出 (5 種、`lib-diagram-parser` と同形式の structured graph data + 物理メタデータ):**
- [ ] クラス図抽出 — class 定義 + 継承 + 集約関係
- [ ] シーケンス図抽出 — call graph + 制御フロー
- [ ] コンポーネント図抽出 — module/package boundary + import 依存
- [ ] パッケージ図抽出 — directory 構造 + namespace 階層
- [ ] 状態遷移図抽出 — FSM パターン (enum + transition method) **must-have**
- [ ] 状態遷移図抽出 — 汎用制御フロー由来の状態抽出 **spike (決定論的ルール構築可否を検証)**

**C. Spec 抽出 (`lib-spec-parser` と並列):**
- [ ] 関数仕様抽出 — signature + docstring + pre/post conditions の構造化
- [ ] クラス仕様抽出 — class definition + members + invariants の構造化

**D. 言語サポート:**
- [ ] C++ サポート — `clang.cindex` (libclang Python binding) ベースで A/B/C 全機能を実装

**E. 内部アーキテクチャ:**
- [ ] 疎結合モジュラー設計 — 各 extractor を独立して lib-internal で呼び出し可能に
- [ ] Module 間契約 — Pydantic model のみで依存、直接呼び出しなし
- [ ] アーキ設計 phase を独立 — 実装着手前にアーキを固定

**F. Traceability:**
- [ ] US-01 (spec→code 意味一致) / US-22 (code→spec 意味一致) / US-25 (architecture リバース) / US-32 (物理アーキ比較) を REQUIREMENTS で固定
- [ ] 各 extractor module がどの US を支えるかを明示

### Out of Scope

- **CrossHair による symbolic execution 統合** — spec (lib-code-parser.md §3.7) で "可能" 止まり。今ミルストンの Core Value から外れる
- **LLM 統合** — 本 lib は決定論性が要件 (Layer M bisimulation の基盤)。表現幅ギャップの解釈は verifier 側の責務
- **動的解析 (runtime tracing)** — 静的解析のみ。spec の範疇外
- **自然文 spec 生成** — 構造化データのみで足りる (verifier が比較に使うだけ)
- **汎用制御フロー由来の状態遷移抽出** — spike で決定論的ルール構築不可と判明したら次ミルストンへ
- **pip パッケージ分割** — 今は 1 lib (`spec_reviewer_code_parser`)。内部 module 分離まで。pip パッケージ分割は v0.3.0 以降に実需 (依存サイズ / 配布粒度) が出てから検討
- **OAS / OpenAPI / IDL からのコード生成** — リバースエンジニアリングのみ
- **テストコード解析** — 本 lib はプロダクトコードのみ対象 (`lib-test-parser` 相当は別 lib)

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
- ACL-2 ツール (`callgraph.py`, `pyright`, `clang`) は本 lib 内部から subprocess 経由で呼ばれる

## Constraints

- **Tech stack**: Python 3.11+, Pydantic 2.x, stdlib `ast`, `pyright`, `clang.cindex`, `callgraph.py` (subprocess)
  — spec (lib-code-parser.md §採用する検証手法) と兄弟 libs の整合性
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
| C++ 解析 = `clang.cindex` (libclang) | AST 正確性 + 型解決可 + 決定論性 (tree-sitter-cpp は syntactic のみで型解決不可) | — Pending |
| Python ACL-2 統合 = `callgraph.py` + `pyright` を subprocess で | spec §3.7 / §6.3 指示、決定論性保持、内製 AST より正確 | — Pending |
| 1 pip lib + 内部疎結合 module 設計 (各 extractor が lib-internal で independently callable) | アーキ重視。pip 分割は早期最適化を避ける | — Pending |
| FSM 抽出 = 明示パターン (enum + transition method) のみ must-have、汎用制御フロー由来は spike | 決定論性を崩さない。spike 結果次第で次ミルストンへ送る | — Pending |
| アーキ設計を独立 phase で先に固める (実装着手前) | "アーキが重要" の user 指針。疎結合設計は後付け不可 | — Pending |
| Python と C++ を最初から対象 (段階分けしない) | spec が "もともと Python だけじゃない" 想定で書かれている (user 指示 2026-05-23) | — Pending |

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
*Last updated: 2026-05-23 after initialization*
