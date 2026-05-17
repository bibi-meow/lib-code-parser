# lib-code-parser Decision Log

> 全工程の意思決定を時系列で記録する。第三者がトレース可能にする目的。
> design doc §7 Step 0 参照。

---

## 決定 #0-1（Step 0: プロジェクト初期化）

- **What**: lib-code-parser を実装対象として確定
- **Options considered**: SOT ドキュメント（lib-code-parser.md）記載の仕様通り実装する
- **Decision**: Python AST モジュールベースの内部実装を採用し、pyright は subprocess 経由のオプション連携とする
- **Rationale**: SOT に "callgraph_tool: internal" と明示されており、ACL-2 callgraph.py は外部依存のため内部実装が必須。pyright はインストール有無で graceful degrade する
- **Determinism**: D
- **Reviewable by**: SOT lib-code-parser.md の params.callgraph_tool: "internal" 記述を確認
- **Traces from**: lib-code-parser SOT ドキュメント（agent_company プロンプト内）
- **Traces to**: Step 5 OSS 選定、Step 8 Spec

---

## 決定 #0-2（Step 0: 実装スコープ）

- **What**: C++ 対応を今回のスコープ外とする
- **Options considered**: A) Python のみ実装、B) Python + C++ 同時実装
- **Decision**: A) Python のみ実装
- **Rationale**: SOT の実装方針に「C++ 対応は scope 外: Decision Log に将来拡張として記録し、Python のみ実装」と明示
- **Determinism**: D
- **Reviewable by**: SOT の「実装方針」セクション参照
- **Traces from**: SOT の language: "python" | "cpp" 記述と実装方針
- **Traces to**: Step 6 Requirements（LIB-FR-04 language config）、Step 8 Spec

---

## 決定 #2-1（Step 2: US スコープ確定）

- **What**: lib-code-parser の lib-level US を US-L-01〜05 の 5 件に確定
- **Options considered**: cicd US（US-01/22/25/32）を直接参照する方式 vs lib-level US を独立定義する方式
- **Decision**: cicd US から導出した lib-level US-L-01〜05 を定義（各 US に cicd US 参照を明示）
- **Rationale**: lib は caller を意識しない独立設計（strategy-pattern-lib-impl.md）だが、traceability のために cicd US との対応を明示する
- **Determinism**: N（US 定義はドメイン知識に依存）
- **Reviewable by**: 01-user-stories.md の対応 US 表と cicd sys.1-userstory.md の記述を照合
- **Traces from**: cicd/doc/sys/user-stories/sys.1-userstory.md §5.1/§5.5, lib-code-parser.md §対応 US
- **Traces to**: Step 6 Requirements（LIB-FR-01〜05）

---

## 決定 #3-1（Step 3: Diagram Spec — CallGraph / TypeDep をグラフモデルとして定義）

- **What**: 本 lib は視覚的 diagram を生成しないが、CallGraph / TypeDep を「物理アーキテクチャのグラフデータ」として定義した
- **Options considered**: A) diagram を扱わない（適用外宣言）、B) CallGraph/TypeDep を内部グラフモデルとして定義
- **Decision**: B）CallGraph/TypeDep を diagram-spec §グラフ表現として定義
- **Rationale**: US-32 AC「AST + コールグラフから物理アーキテクチャ図が生成される」という用途から、グラフデータは diagram の内部表現に相当する。引用根拠を lib-code-parser.md と US-32 から確認済み
- **Determinism**: D
- **Reviewable by**: 02-diagram-spec.md の引用根拠 vs cicd ドキュメント
- **Traces from**: lib-code-parser.md §概要, sys.1-userstory.md US-32 AC
- **Traces to**: Step 7 Architecture（グラフデータ構造の設計）

---

## 決定 #4-1（Step 4: TypeDep の dep_type 値域）

- **What**: TypeDep.dep_type は "typing" 固定でなく "inherit"（継承）等も含む
- **Options considered**: A) "typing" のみ、B) "typing" / "inherit" / "import" 等複数値
- **Decision**: B）dep_type は str 型（値域: "typing", "inherit", "import" 等）
- **Rationale**: ast 解析で ClassDef の bases（継承元）も型依存として抽出できるため。02-diagram-spec.md を修正済み
- **Determinism**: D
- **Reviewable by**: 02-diagram-spec.md の TypeDep スキーマ
- **Traces from**: Step 3 02-diagram-spec.md 初版（dep_type: "typing" と記載）
- **Traces to**: Step 8 Spec（TypeDep.dep_type の型定義）

---

<!-- 各工程で判断が生じるたびに ## 決定 #N-M エントリを追記する -->
<!-- N = 工程番号（0-15）、M = その工程内の連番 -->
