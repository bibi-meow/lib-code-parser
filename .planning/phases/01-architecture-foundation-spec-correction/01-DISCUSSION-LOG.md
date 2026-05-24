# Phase 1: Architecture Foundation + Spec Correction - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-24
**Phase:** 1-Architecture Foundation + Spec Correction
**Areas discussed:** D (DOC-01 spec doc 範囲), B (CAV polymorphism), A (モジュール配置), C (sibling-lib PR タイミング), E (SP-3 spike 判定ルール)

---

## D: DOC-01 spec doc 修正範囲

| Option | Description | Selected |
|--------|-------------|----------|
| surgical edit | `callgraph.py` + "ACL-2" の該当行のみ書き換え (最低限要件のみ) | |
| **full rewrite** | v0.2.0 全方針 (内製 call graph、pyright MIT、libclang、CAV、EdgeKind、5 diagram、function/class spec、Doxygen、Apache-2.0、physical_*/source_* prefix、Traceability) を反映する全面書き直し | ✓ |
| rewrite + 旧版退避 | full rewrite + `frozen/` に旧版を保存 | ✓ (full rewrite に含める) |

**User's choice:** full rewrite + `frozen/2026-05-24-v0.1.0-spec/` 退避
**Notes:**
- 現 spec doc は v0.1.0 時代の文体で書かれており、`callgraph.py` / "ACL-2" / "C++ 将来拡張" / `params: dict[str, object]` 等が随所に散在
- surgical edit では内部論理が崩れる (callgraph.py 削除後に「ACL-2 決定論的ツール」分類根拠が宙吊り等)
- DOC-01 / DOC-03 / DOC-04 / TRC-01 の 4 件が同時にこの doc に依存 → 整合した rewrite 1 回が review コスト低い
- backup-before-major-rewrite ルール準拠で `frozen/` 退避を含める

---

## B: CAV (Common AST View) polymorphism

| Option | Description | Selected |
|--------|-------------|----------|
| **単一 `CAV` + language discriminator + opaque payload (object)** | Pydantic BaseModel 1 個、language で分岐、payload は `object` 型で `ast.Module` / `cindex.TranslationUnit` を保持 | ✓ |
| `PythonCAV` \| `CppCAV` (discriminated union) | typed union、Phase 4 で union 拡張 | |
| `@dataclass(frozen=True)` (Pydantic 捨てる) | Pydantic 規約から外れる、immutability 強化 | |
| `payload: dict[str, Any]` 化 | AST を flatten する独自正規化 | |

**User's choice:** 単一 CAV + opaque payload (私の推薦)、ただし **「兄弟 lib も同様にリファクタするので両方のあるべきを目指せ」** という重要補足を user が追加

**Sub-question: workspace 共通規約のスコープ** (user 補足を受けて Claude が再提示)

| Option | Description | Selected |
|--------|-------------|----------|
| (α) workspace `CONVENTIONS.md` を Phase 1 のスコープに含める | lib-code-parser Phase 1 + workspace doc 1 個作成 | |
| **(β) Phase 1 では lib-code-parser 内に transferable pattern doc だけ書く** | 兄弟 lib の再設計は別タイミング、現タスクを終わらせる優先 | ✓ |
| (γ) workspace `CONVENTIONS.md` を別 lib の作業として隔離 | Phase 1 は純粋維持 | |

**User's choice:** (β)
**Notes (user の重要な指示)**:
- 「兄弟 lib の再設計を行うと現タスクが終わらなくなります」
- 「現 lib の考え方を残してください」 → caller-agnostic / Pydantic v2 / no I/O / 純粋関数を継承
- 「兄弟 lib の状況を踏まえ、変更容易性を確保した IO としてください」 → `NormalizedArtifact` Generic 化、`ParserConfig` field 命名規約、`adapters/base.py` の transferable helper として書く
- 「これにより、兄弟 lib 更新時に再リファクタしましょう」 → workspace 共通規約 / 共通 lib 化 / 再リファクタ phase は Deferred Ideas に記録

**Sub-decision: pattern doc 命名**
- 案 B: `docs/08-common-view-pattern.md` (SDD chain 連番に組み込み、subagent が読み順を理解しやすい) ← 採用

**Sub-decision: `NormalizedArtifact` Generic 化の v0.1.0 互換性**
- v0.1.0 fixture parity test 込みで進める ← 採用 (異議なし、Claude 推薦)

---

## A: モジュール配置レイアウト

| Iteration | Claude 提案 | User Feedback |
|---|---|---|
| 1 | nested layout、`extractors/` flat、`models/` 8 file 分割、suffix 一部省略 (`sequence.py` 等) | 「diagram などの生成単位でファイルを分けるべき。今後拡張するし、その構成のほうがスマート。ただ、model ってなんだっけ？」 |
| 2 | `extractors/{ast,diagram,spec}/` サブフォルダ化、suffix 全付け、`models/` 役割説明 | 「output が core ロジックだから、それを軸にすべき。同じ解析手法を利用する場合はインスタンスを取りに行けばいい」 |
| 3 | 評価単位 7 file を `extractors/` 直下に flat、`primitives/` (5 file) を共有 supplier 化、`_doxygen.py` helper | 「要件ごとに分割してね。この場合、model は論理アーキテクチャと評価するの？」 |
| 4 (最終) | 上記 + `models/` を `infrastructure/` (lib I/O 契約) / `primitives/` (中間データ) / `evaluations/` (論理アーキ比較対象) の 3 分割。論理アーキ比較は **`evaluations/` のみ** | OK |

**User's choice (最終形):**
- 評価単位 7 file を `extractors/` 直下に flat (verifier 比較単位と 1:1)
- `extractors/primitives/` 5 file (共有 supplier、評価単位が pull で取得)
- `models/{infrastructure,primitives,evaluations}/` 3 分割 (要件 = 何の責務かで分割)
- `_dispatch.py` で FRONTENDS / PRIMITIVES / EVALUATIONS の 3 dict 管理
- 拡張点 6 不変条件 (Open-Closed) を `docs/09-extending.md` に明記
- `models/evaluations/` のみが論理アーキ比較対象 (このルールを doc に明記)

**Notes:**
- user 設計原則「**output が core ロジック、解析手法は二次**」を最終構造に反映
- 「機能追加 2 パターン (評価手法追加 / 解析手法追加)」を明示。call graph に何か追加して新 diagram = A+B 同時追加の例
- 拡張時の典型シナリオ: 既存 file touch ゼロで新 primitive + 新評価単位を追加可能 (`_dispatch.py` と `CodeContent` への append のみ)

---

## C: sibling-lib (lib-diagram-parser) PR タイミング

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 1 で PR 出す | DIA-04 を Phase 3 で unblock するため早期に動く | |
| **Phase 1 では出さない、Phase 3 着手時に再評価** | 兄弟 lib に触らない方針 (B-v2 (β) 整合) | ✓ |
| local placeholder + 将来 switch | lib-code-parser 内に独自定義 (SCH-01 違反の可能性) | |

**Sub-decision: Phase 3 着手時の fallback (lib-diagram-parser 未進化の場合)**
- **local extension** (`GraphNode` subclass + `node_type` Literal 拡張) で対応 ← 採用
- SCH-01 の解釈を「直接利用 (subclass 含む)」に拡大 (model duplication は引き続き禁止)
- REQUIREMENTS.md の SCH-01 文言を Phase 1 で微更新

**User's choice:** Phase 1 では PR 出さず、Phase 3 入口で再評価 (私の推薦)
**Notes:**
- "PR = Pull Request" の clarification を user が要求 → Claude が初出時に定義しなかった (explain-before-using-jargon ルール違反、応答内で apology)
- user の (β) 方針 (兄弟 lib に触らない) と整合
- Phase 3 plan-phase で sibling-lib の最新版を確認、`node_type="package"` の有無で対応分岐
- Phase 1 close は sibling-lib に依存しない

---

## E: SP-3 libclang spike 判定ルール

| Option | Description | Selected |
|--------|-------------|----------|
| CI matrix で実機検証 + 4 段階判定 | GitHub Actions `macos-14` (arm64) で Python 3.13/3.14、(a) install / (b) dylib load / (c) ABI / (d) minimal parse の 4 段階 | ✓ |
| user 環境で local 検証 | user が macOS arm64 マシンで実行 | (user が環境なし、不採用) |
| 3 段階判定 (簡素化) | ship-best-effort / partial / defer | |

**Sub-decision: Phase 1 close 条件**
- **Phase 1 close 緩和**: CI workflow setup + 最初の run 1 回 + 暫定 verdict 記録で OK (verdict 結果で Phase 1 close を blocking しない) ← 採用
- Phase 4 入口で verdict 再確認・更新可能

**Sub-decision: 優先度**
- **Phase 1 内で最低優先** ← user 指示
- 他タスク (DOC-01 rewrite / 構造再編 / dispatch 実装等) 完了後に着手

**User's choice:** CI matrix で 4 段階判定 + **優先度最低** + Phase 1 close 緩和
**Notes (user の重要な指示):**
- 「OKですが、優先度最低としてください。課題の環境を持っていません」
- → user は macOS arm64 環境を持っていない。ローカル検証は完全に削除、CI のみで完結させる
- Phase 4 入口で verdict 再確認 / 必要なら追加 spike (Intel macOS / macOS-15) を Deferred Ideas に記録

---

## Claude's Discretion

以下は user が「お任せ」で進めて良い領域:
- ファイル内部の細かい命名 (関数名 / private helper 名 / module docstring の表現) は標準慣習に従う
- 各評価単位 extractor 内部の言語分岐実装パターン (if/elif vs dispatch dict 等) は Phase 2-4 plan-phase で詰める
- `docs/08-common-view-pattern.md` / `docs/09-extending.md` の文章スタイルと細部構成は Claude が判断 (SDD chain 既存ドキュメントの文体に合わせる)
- `.github/workflows/ci.yml` への SP-3 matrix 追加の具体的な YAML 構造は Phase 1 plan で詰める

---

## Deferred Ideas

### Workspace coordination (兄弟 lib 更新時に再評価)

- workspace `spec-reviewer-libs/CONVENTIONS.md` 作成 (兄弟 lib 2+ が同 pattern を採用したタイミング)
- `NormalizedArtifact` / Container の workspace 共通 lib 化検討
- 再リファクタ phase (lib-code-parser ↔ 兄弟 lib の I/O 揃え)

### Sibling-lib coordination (Phase 3 入口で再評価)

- `lib-diagram-parser` `node_type="package"` enum 追加 PR
- local extension 削除 → 直接 import switch (sibling lib に PR merge された後)

### Future evaluation units

- **コードから DDD リバース** (user 提供例): BC / Aggregate / Layer 検出 (拡張点 A+B 同時追加パターンの好例、将来評価単位候補)

### Spike 関連 (Phase 4 入口で再評価)

- Phase 4 入口で SP-3 verdict 再確認
- 追加 spike: Intel macOS (macos-13) / macOS-15 等の matrix

---

## Discussion Sequence (議論進行記録)

1. user が `/gsd:discuss-phase 1` を起動
2. Claude が初期化 → Phase 1 コンテキスト読み込み (PROJECT.md / REQUIREMENTS.md / ROADMAP.md / STATE.md / codebase maps / spec doc) → 5 gray area を提示
3. user が AskUserQuestion multi-select を拒否 → 「対話形式で QA をしてほしい」 → Claude が memory `feedback_qa_dialog_style.md` を更新 (multiSelect も避ける明示)
4. user が **「上位ドキュメントから順に」** 指示 → D → B → A → C → E の順で議論
5. **D 議論**: full rewrite vs surgical edit → full rewrite + frozen 退避で確定 → user 「OK」
6. **B 議論**: 単一 CAV + opaque payload で確定 → user 「OK ただ、兄弟 lib も同様にリファクタするので両方のあるべきを目指せ」補足
7. **B sub-discussion**: workspace 共通規約のスコープ → (β) で確定 (兄弟 lib に触らない、変更容易性確保 IO で進める) → user 「これにより、兄弟 lib 更新時に再リファクタしましょう」
8. **A 議論 (iteration 1)**: extractors/ flat 提案 → user 「diagram などの生成単位でファイルを分けるべき」反対 + 「model ってなんだっけ？」
9. **A 議論 (iteration 2)**: extractors/{ast,diagram,spec}/ サブフォルダ化 + models 説明 → user 「output が core ロジックだから、それを軸にすべき。同じ解析手法はインスタンスを取りに行けばいい」
10. **A 議論 (iteration 3)**: 評価単位 7 file flat + primitives/ supplier 化 → user 「要件ごとに分割してね。model は論理アーキと評価するの？」
11. **A 議論 (iteration 4 = 最終)**: models/{infrastructure,primitives,evaluations}/ 3 分割 + 論理アーキ比較は evaluations/ のみ + DDD リバースを将来例として Deferred 追加 → user 「OK」
12. **拡張点設計の追加**: user 「機能追加 2 パターン (評価手法 / 解析手法)、call graph に何か追加して diagram にするケース」指摘 → Open-Closed 6 不変条件を `docs/09-extending.md` に追加 → user 「具体的な近未来の拡張は予定なし、ただし可能性として DDD リバース」
13. **C 議論**: Phase 1 では PR 出さない、Phase 3 着手時に再評価 → user 「PR は pull req のこと？」 (jargon clarification) → Claude apology + 説明 → user 「OK」
14. **E 議論**: GitHub Actions macos-14 + 4 段階判定 → user 「OK ですが、優先度最低としてください。課題の環境を持っていません」 → Phase 1 close 緩和、ローカル検証削除、CI のみ
15. **5 gray area 全確定**: CONTEXT.md / DISCUSSION-LOG.md 作成許可 → user 「OK」 → 本ファイル作成
