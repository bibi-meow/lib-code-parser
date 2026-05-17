# lib-code-parser User Stories

> cicd の sys.1-userstory.md の対応 US から lib-level US を導出する。
> design doc §7 Step 2 参照。

## 対応 cicd US

| cicd US ID | タイトル | 本 lib の関連性 |
|-----------|---------|--------------|
| US-01 | Spec→Code 意味的一致の自動検証 | コードの FunctionNode + contracts を提供することで spec→code 検証の物理側入力となる |
| US-22 | Spec-Code 両端一致レビュー | code→spec 方向の検証に必要な FunctionNode 一覧（node_id + docstring + trace_tags）を提供 |
| US-25 | コード設計妥当性 (Design Quality) レビュー | CallGraph + TypeDep から構造メトリクス（cyclomatic/cohesion/coupling）を計算する素材を提供 |
| US-32 | コードからの物理アーキテクチャ リバース | AST + CallGraph をリバースエンジニアリングの物理アーキ表現として提供 |

---

## US-L-01: Python コードから FunctionNode 一覧を抽出する

**As a** spec-reviewer エンジン（spec_code_verifier / architecture_verifier）
**I want** Python コードファイルを渡したら FunctionNode（関数・メソッド・クラス）の一覧を取得できる
**So that** コード単位ごとに spec との意味的一致（US-01）・undocumented behavior 検出（US-22）が判定できる

**Acceptance Criteria:**
- [ ] `.py` ファイルの bytes を渡すと FunctionNode のリストが返される
- [ ] 各 FunctionNode は node_id（"module.Class.method" 形式）、kind（"function"|"method"|"class"）、params、return_type、docstring、source_range を持つ
- [ ] ネストしたメソッド（クラス内メソッド）も正しく抽出される

**cicd US 参照**: US-01, US-22
**Decision Log**: #2-1

---

## US-L-02: Python コードから CallGraph を生成する

**As a** architecture_verifier
**I want** Python コードファイルから関数間呼び出し関係（CallGraph）を取得できる
**So that** コードの物理アーキテクチャをリバースエンジニアリングし、spec の論理アーキとの構造比較が可能になる（US-32）

**Acceptance Criteria:**
- [ ] CallGraph.nodes に FunctionNode の node_id 一覧が含まれる
- [ ] CallGraph.edges に (caller_node_id, callee_node_id) のペアが含まれる
- [ ] ast.Call ノードを追跡した静的解析で生成される（外部ツール依存なし）

**cicd US 参照**: US-32
**Decision Log**: #2-2

---

## US-L-03: Python コードから型依存グラフ（TypeDep）を生成する

**As a** spec_code_verifier
**I want** Python コードから型間の依存関係（TypeDep）を取得できる
**So that** 型システム上の契約整合性（US-22）を確認できる

**Acceptance Criteria:**
- [ ] TypeDep.source / target / dep_type が返される
- [ ] pyright がインストールされていない環境では空リスト [] で graceful degrade する
- [ ] pyright がある場合は subprocess 経由で呼び出し、JSON 出力を解析する

**cicd US 参照**: US-22, US-25
**Decision Log**: #2-3

---

## US-L-04: Pydantic / dataclass validator から ContractInfo を抽出する

**As a** spec_code_verifier
**I want** Pydantic BaseModel または dataclass の validator 定義から ContractInfo（preconditions / invariants）を抽出できる
**So that** spec に書かれたビジネスルール（制約・不変条件）がコードの validator として実装されているかを照合できる（US-01, §3.7）

**Acceptance Criteria:**
- [ ] `@field_validator` デコレータを持つメソッドが preconditions に含まれる
- [ ] `model_validator(mode="wrap")` / `model_validator(mode="before")` が invariants に含まれる
- [ ] `__post_init__` メソッドの内容が preconditions に含まれる
- [ ] extract_contracts=False の場合は ContractInfo は空で返される

**cicd US 参照**: US-01, US-22
**Decision Log**: #2-4

---

## US-L-05: Trace タグを抽出する

**As a** trace_mapper
**I want** コードのコメント内の "Traces: US-01, FR-02" 形式のタグを TraceTag として抽出できる
**So that** spec ID とコード単位の対応関係をトレーサビリティマッピングに利用できる

**Acceptance Criteria:**
- [ ] `# Traces: US-01` コメントがある場合 TraceTag として抽出される
- [ ] 複数のタグ（Traces: US-01, FR-02）が複数の TraceTag として返される
- [ ] タグなしの場合は空リストが返される

**cicd US 参照**: US-01, US-22
**Decision Log**: #2-5

---

<!-- 追加 US は ## US-L-NN の形式で追加 -->
