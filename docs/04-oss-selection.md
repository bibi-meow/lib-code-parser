# lib-code-parser OSS 選定

> System Architecture に組み込む OSS を評価マトリクスで選定する。
> design doc §7 Step 5 参照。

---

## 選定対象

| 機能 | 必要理由 |
|------|---------|
| Python AST 解析 | FunctionNode 抽出・CallGraph 生成・ContractInfo 抽出のコア処理 |
| コールグラフ生成 | 関数間呼び出し関係の静的解析 |
| 型依存解析 | TypeDep 生成（型アノテーション → 依存グラフ） |

---

## 選定基準

| 基準 | 重み | 説明 |
|------|------|------|
| 機能性 | 0.4 | アルゴリズムの正確性・カバレッジ |
| 性能 | 0.3 | 計算量・実測処理速度 |
| 保守性 | 0.2 | 最終更新・star 数・コミュニティ |
| ライセンス | 0.1 | MIT / Apache 互換 |

---

## 評価マトリクス: Python AST 解析

参照: lib-code-parser.md §採用アルゴリズム / variants-catalog.md §4.3 §3.7

| 候補 | 機能性 (0.4) | 性能 (0.3) | 保守性 (0.2) | ライセンス (0.1) | 合計スコア |
|------|:-----------:|:--------:|:-----------:|:-------------:|:---------:|
| **Python 標準 ast** | 5 | 5 | 5 | 5 | 5.0 |
| tree-sitter-python | 4 | 5 | 4 | 4 | 4.3 |
| astroid (pylint) | 4 | 3 | 5 | 4 | 4.0 |

### 決定

**採用**: Python 標準ライブラリ `ast`
**採用バージョン**: Python 3.11+ 標準（追加インストール不要）
**理由**:
- lib-code-parser.md §採用アルゴリズム に「Python AST 解析: 標準ライブラリ ast モジュール（ast.parse / ast.walk）」と明示されている
- 追加依存なし（pyproject.toml に依存追加不要）
- Python 3.11 で安定しており保守性最高
- tree-sitter は multi-language 対応だが今回は Python のみで不要なオーバーヘッド
**Decision Log**: #5-1

---

## 評価マトリクス: コールグラフ生成

参照: lib-code-parser.md §採用アルゴリズム "callgraph.py（ACL-2 決定論的ツール）"

| 候補 | 機能性 (0.4) | 性能 (0.3) | 保守性 (0.2) | ライセンス (0.1) | 合計スコア |
|------|:-----------:|:--------:|:-----------:|:-------------:|:---------:|
| **ast.Call 内部実装** | 4 | 5 | 5 | 5 | 4.7 |
| PyCG (archived) | 5 | 3 | 1 | 4 | 3.4 |
| pyan3 | 4 | 3 | 3 | 4 | 3.5 |

### 決定

**採用**: ast.Call ベースの内部実装（外部 OSS 依存なし）
**採用バージョン**: Python 3.11+ 標準 ast（追加インストール不要）
**理由**:
- lib-code-parser.md SOT に「callgraph_tool: "internal" — 内部実装のコールグラフ生成（ACL-2 callgraph.py は外部依存のため内部実装）」と明示
- PyCG は archived（保守性スコア 1）で採用不可
- pyan3 は保守性が中程度で外部依存追加のデメリットが勝る
**Decision Log**: #5-2

---

## 評価マトリクス: 型依存解析

参照: lib-code-parser.md §インターフェース "type_tool: pyright"

| 候補 | 機能性 (0.4) | 性能 (0.3) | 保守性 (0.2) | ライセンス (0.1) | 合計スコア |
|------|:-----------:|:--------:|:-----------:|:-------------:|:---------:|
| **pyright** | 5 | 4 | 5 | 4 | 4.7 |
| mypy | 4 | 3 | 5 | 5 | 4.1 |
| ast アノテーション解析（fallback） | 3 | 5 | 5 | 5 | 4.1 |

### 決定

**採用**: pyright（subprocess 経由、optional）+ ast アノテーション fallback
**採用バージョン**: pyright 最新安定版（`^1.1`）
**理由**:
- lib-code-parser.md SOT に「type_tool: "pyright" — 静的型チェッカー（subprocess 経由）」と明示
- インストールされていない環境では graceful degrade（SOT の実装方針より）
- ast アノテーション解析を fallback として実装することで、pyright なしでも基本動作する
**Decision Log**: #5-3

---

## 最終依存関係まとめ

| 用途 | パッケージ | 必須/オプション |
|------|----------|--------------|
| Python AST 解析 | Python 標準 `ast` | 必須（追加不要） |
| CallGraph 生成 | Python 標準 `ast` | 必須（追加不要） |
| 型依存解析（高精度） | `pyright`（subprocess） | オプション（graceful degrade） |
| テスト | `pytest>=8`, `pytest-cov` | dev のみ |
| Lint | `ruff` | dev のみ |
| 型チェック | `pyright` | dev のみ |
