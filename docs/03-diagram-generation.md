# lib-code-parser Diagram Generation 手法

> input data から diagram を生成するアルゴリズム・実装方針を定義する。
> design doc §7 Step 4 参照。

---

## 本 lib の diagram 生成について

本 lib は視覚的な diagram ファイル（Mermaid/PlantUML）を直接生成しない。

代わりに、後段の `architecture_verifier` が利用する **物理アーキテクチャのグラフデータ**（CallGraph / TypeDep）を生成する。これらは「グラフモデル」として `02-diagram-spec.md` に定義されている。

---

## 生成対象

| グラフ種別 | 生成元 input | 生成手法（概要） |
|-----------|------------|--------------|
| CallGraph | Python ソースコード bytes | Python AST（ast モジュール）で ast.Call ノードを追跡し、(caller, callee) エッジを抽出 |
| TypeDep | Python ソースコード bytes | ast の型アノテーション解析 + オプションで pyright --outputjson |
| FunctionNode リスト | Python ソースコード bytes | ast.walk で FunctionDef / AsyncFunctionDef / ClassDef を収集 |
| ContractInfo | Python ソースコード bytes | ast でデコレータ（@field_validator / model_validator）と __post_init__ を検出 |

---

## アルゴリズム定義

### FunctionNode 抽出アルゴリズム

**決定論性**: D

```
1. input: raw_content (bytes), path (str)
2. パース: ast.parse(raw_content.decode("utf-8")) で AST を生成
3. walk: ast.walk(tree) で FunctionDef / AsyncFunctionDef / ClassDef ノードを収集
4. node_id 構築: モジュール名 + クラス名（ネストを考慮）+ 関数名 を "." で連結
5. params 抽出: node.args.args から (name, annotation) を取得
6. return_type 抽出: node.returns から型文字列を取得
7. source_range: node.lineno / node.end_lineno から SourceRange を生成
8. docstring: ast.get_docstring(node) から取得
9. trace_tags: コメント（ast.Constant ノード / docstring）から "Traces:" パターンを検出
10. 出力: List[FunctionNode]
```

### CallGraph 生成アルゴリズム

**決定論性**: D

```
1. input: AST + FunctionNode リスト（node_id マッピング付き）
2. 現在スコープを管理するスタック（caller スタック）を初期化
3. ast.walk で FunctionDef / AsyncFunctionDef ノードを検出 → caller スタックに push
4. ast.walk で ast.Call ノードを検出
   - func が ast.Name → 単純関数名（同モジュール内の node_id を解決）
   - func が ast.Attribute → "object.method" 形式（クラスメソッド呼び出し）
5. 解決できた (caller, callee) ペアを edges に追加
6. 全 node_id を nodes に追加
7. 出力: CallGraph(nodes=..., edges=...)
```

### TypeDep 生成アルゴリズム

**決定論性**: D（pyright あり）/ D（pyright なし → 空リスト）

```
A. pyright が利用可能な場合:
   1. 一時ファイルに source を書き出す
   2. subprocess: pyright --outputjson <tmpfile>
   3. JSON 出力を解析 → 型依存関係を TypeDep に変換
   4. 一時ファイルを削除
   5. 出力: List[TypeDep]

B. pyright が利用不可の場合:
   1. ast の型アノテーションを解析（ast.AnnAssign / 関数引数の annotation）
   2. Import / ImportFrom ノードから型の import 元を追跡
   3. (source_type → target_type) の依存を TypeDep に変換
   4. 出力: List[TypeDep]（精度は A より低いが graceful degrade）
```

### ContractInfo 抽出アルゴリズム（§3.7 Pydantic / dataclass validator）

**決定論性**: D

```
1. input: ClassDef ノード（FunctionNode 抽出で得たもの）
2. @field_validator デコレータを持つメソッドを検出 → 引数（対象フィールド名）を preconditions に追加
3. @model_validator デコレータを持つメソッドを検出 → mode 引数を確認 → invariants に追加
4. __post_init__ メソッドを検出 → 関数本体の ast.Assert / 比較式を preconditions に追加
5. 出力: ContractInfo(preconditions=[...], invariants=[...])
```

---

## Step 3 Diagram Spec との差異（Step 4 発見分）

| 発見日 | 差異内容 | 02-diagram-spec.md 更新内容 | Decision Log |
|-------|---------|--------------------------|-------------|
| 2026-05-18 | TypeDep の dep_type は "typing" 固定でなく "inherit"（継承）等も含む場合がある | dep_type の説明を「"typing" / "inherit" 等」に修正済 | #4-1 |

**Decision Log**: #4-1（手法選択の判断を記録）
