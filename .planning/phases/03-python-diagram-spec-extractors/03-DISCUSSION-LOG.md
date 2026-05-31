# Phase 3: Python Diagram + Spec Extractors - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-01
**Phase:** 3-Python Diagram + Spec Extractors
**Areas discussed:** Schema reconciliation (GA-1), Sibling-lib coordination (GA-2), SP-1/SP-2 ship-vs-defer (GA-3), Docstring parser dependency (GA-4) + contract-conflict finding (EdgeKind)

> 運用方針: user は contract レベル (architecture / concept / acceptance criteria / locked decision の
> 更新破壊) のみレビュー。下位 implementation detail は agent 自律判断 ([[feedback-contract-level-review]])。
> Q&A は AskUserQuestion multi-popup を使わず 1 メッセージで「決定 + 根拠 + 異議受付」を提示
> ([[feedback-qa-dialog-style]])。

---

## Contract-conflict finding: EdgeKind が DIA-03/DIA-04 を表現できない

| Option | Description | Selected |
|--------|-------------|----------|
| `dependency`/`depends` を追加 | 兄弟 lib 語彙に合わせる。だが Phase 1 Pitfall 7 が catch-all として明示禁止 | |
| `imports` (明示セマンティック値) を append-only 追加 | catch-all ではなく "module A imports module B" の明示 semantic。`associates` と同哲学 | ✓ |
| EdgeKind を緩い str に戻す | Phase 1 の閉じた Literal (SCH-03 enforcement) を破壊 | |

**User's choice:** "OK" (推奨 = `imports` append-only 追加を承認)
**Notes:** package containment 用 `contains` の要否は DIA-04 設計時に planner 判断 (node 入れ子で表現できるなら不要)。既存 11 値は不変。

---

## GA-1: スキーマ整合戦略 (SCH-01 / DIA-07)

| Option | Description | Selected |
|--------|-------------|----------|
| 直接 import (SCH-01 字面) | `from lib_diagram_parser import GraphNode...`。だが兄弟 lib は extra=forbid 無し/physical_* 無し/閉じた Literal 無しで厳格スキーマを失う | |
| 自己完結スキーマ維持 (graph_base.py) + SCH-04 構造互換テスト | Phase 1 の厳格スキーマを保持。語彙ギャップは verifier 責務 | ✓ |
| subclass | 兄弟 lib を継承して拡張。緩い基底に依存 | |

**User's choice:** "OK" (推奨 = 自己完結維持 + verifier が語彙ギャップ吸収)
**Notes:** Phase 1 D-15/D-17 で先送りされた「direct-import vs subclass」を本 Phase で「自己完結維持」に確定。Core Value「物理↔論理ギャップ解釈は verifier 責務」と整合。

---

## GA-2: 兄弟 lib lib-diagram-parser 協調 (DIA-04)

| Option | Description | Selected |
|--------|-------------|----------|
| enum 値追加 PR を merge 待ち (ROADMAP 字面) | DIA-04 を PR merge までブロック | |
| 本 lib 側で package emit + 軽量ドキュメント PR (非ブロッキング) | node_type は plain str ゆえコード変更不要。実装は本 lib で完結 | ✓ |

**User's choice:** "OK" (推奨 = 本 lib 側完結 + 軽量ドキュメント PR、非ブロッキング)
**Notes:** 兄弟 lib `node_type` は plain str (enum ではない) と実機確認。ROADMAP の「enum 値追加 PR」枠組みは実体と乖離。

---

## GA-3: SP-1 / SP-2 spike の ship-vs-defer 基準 (acceptance scope)

| Option | Description | Selected |
|--------|-------------|----------|
| 事前に全 ship 確定 | spike 結果を無視して branch fidelity / 汎用制御フローを v0.2.0 に固定 | |
| 決定論性で defer 判定 (spike verdict 駆動) | 決定論的ルール構築可なら ship、不可なら v0.3.0 (DIA-02-FULL/DIA-05-FULL) へ defer | ✓ |
| 事前に全 defer 確定 | spike を実行せず v0.3.0 に送る | |

**User's choice:** "OK" (推奨 = 決定論性で defer 判定。must-have の linear sequence + FSM 明示パターンは v0.2.0 確定)
**Notes:** acceptance scope だが「決定論性 = Layer M bisimulation の前提」を判定基準とすることで合意。verdict は SP-1/SP-2 spike doc に記録。

---

## GA-4: spec 抽出の docstring パーサ (Tech stack = contract)

| Option | Description | Selected |
|--------|-------------|----------|
| 外部 lib 依存 (`docstring_parser` 等) | 実装は楽だが Tech stack constraint 変更 + 決定論性を外部に委ねる | |
| stdlib のみで内製 | 決定論性 / no-GPL / caller-agnostic / 最小依存と整合 | ✓ |

**User's choice:** "OK" (推奨 = stdlib 内製。icontract/deal/PEP-316 は検出のみで本体 import しない)
**Notes:** Google/NumPy/Sphinx Napoleon の section 解析は `ast.get_docstring()` + 内製パーサ。

---

## Claude's Discretion

planner / researcher が既存根拠 (RESEARCH/CONTEXT/REQUIREMENTS/docs/既存 convention) から自律判断:
- EdgeKind 追加値の最終形 (`imports` のみ / `contains` も)
- 各 diagram/spec extractor の signature / module 配置 / model field 構造
- DIA-01 composition/aggregation の AST 実装、DIA-02 sequence の participant/chain call 表現
- DIA-05/06 の FSM AST 検出パターン詳細・return-value substitution アルゴリズム
- docstring section パーサ内部実装、spec model の Pydantic shape
- SP-1/SP-2 spike の実験設計、sort key 構成、test 戦略 (negative case fixture 含む)

## Deferred Ideas

- Phase 4: SPC-03 Doxygen 契約抽出、C++ 上での diagram/spec 抽出 (LNG-04)
- Phase 5: SCH-04 cross-lib compat test、DET-01 snapshot 完成形、DOC-02 README matrix
- v0.3.0+: DIA-02-FULL (sequence branch fidelity)、DIA-05-FULL (汎用制御フロー → state) — spike verdict 次第
- 兄弟 lib: `lib-diagram-parser` node_type ドキュメント PR (非ブロッキング)
