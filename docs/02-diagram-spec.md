# lib-code-parser Diagram Spec

> 本 lib が生成・参照する diagram の仕様。必ず正規ドキュメントを Read して引用すること。
> **学習データ推定禁止**: LLM の記憶から推定するのではなく正規仕様を Read して根拠を残す。
> design doc §7 Step 3 参照。

---

## 本 lib の diagram 扱いについて

本 lib は「視覚的な diagram ファイル」(Mermaid/PlantUML/SCDL) を生成・解析しない。

ただし、本 lib が出力する **CallGraph** および **TypeDep** は、後段の `architecture_verifier` が物理アーキテクチャを表現する「グラフデータ構造」として機能する。これらは diagram の **内部表現（グラフモデル）** に相当する。

**引用根拠**: `cicd/doc/sys/lib/lib-code-parser.md` §概要:
> 「これらは SD-01 の ArchitectureStrategy が spec 由来の論理アーキテクチャ（SpecContent.embedded_diagrams から導出）と比較する物理アーキテクチャの実体となる」

**引用根拠**: `cicd/doc/sys/user-stories/sys.1-userstory.md` US-32 AC:
> 「AST + コールグラフ（callgraph.py 連携）から物理アーキテクチャ図が生成される」

---

## 本 lib が扱う内部グラフ表現

| グラフ種別 | データ型 | 用途 |
|-----------|---------|------|
| CallGraph | `CallGraph(nodes, edges)` | 関数間呼び出し関係。物理アーキテクチャの有向グラフ |
| TypeDep | `List[TypeDep(source, target, dep_type)]` | 型間の依存関係 |

---

## ノード型（CallGraph.nodes）

| ノード型 | 型 | 説明 | 正規仕様引用 |
|---------|-----|------|------------|
| FunctionNode.node_id | `str` | "module.ClassName.method_name" 形式の完全修飾名 | lib-code-parser.md §インターフェース FunctionNode.node_id |

## エッジ型（CallGraph.edges）

| エッジ型 | 型 | 方向 | 正規仕様引用 |
|---------|-----|------|------------|
| 呼び出し関係 | `Tuple[str, str]` | (caller_node_id → callee_node_id) | lib-code-parser.md §インターフェース CallGraph.edges |

## TypeDep スキーマ

| フィールド | 型 | 説明 | 正規仕様引用 |
|-----------|-----|------|------------|
| source | `str` | 依存元の型名（完全修飾名） | 共有型定義 TypeDep |
| target | `str` | 依存先の型名（完全修飾名） | 共有型定義 TypeDep |
| dep_type | `str` | 依存種別（"typing" / "inherit" 等）| 共有型定義 TypeDep |

---

## 正規ドキュメント引用根拠

| ドキュメント名 | パス | 参照章節 | 引用目的 |
|-------------|------|---------|---------|
| lib-code-parser.md | cicd/doc/sys/lib/lib-code-parser.md | §概要, §インターフェース | CallGraph/TypeDep の仕様確認 |
| sys.1-userstory.md | cicd/doc/sys/user-stories/sys.1-userstory.md | US-32 AC | 物理アーキテクチャとの関係 |
| 共有型定義 | agent_company プロンプト内 | TypeDep dataclass | フィールド仕様 |

**Decision Log**: #3-1

---

<!-- Step 4 Diagram Generation 時にズレが発見されたら本ファイルを更新する（フィードバックループ）-->
