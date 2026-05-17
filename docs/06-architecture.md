# lib-code-parser System Architecture

> lib のアーキテクチャを定義する。モジュール構成・DFD・エラー処理を明確にする。
> design doc §7 Step 6 参照。
> **lib は caller を意識しない独立設計とすること（strategy-pattern-lib-impl.md 参照）。**

---

## 目的

Python ソースコード（bytes）を受け取り、AST 解析によって FunctionNode リスト・CallGraph・TypeDep リストを抽出し、`NormalizedArtifact(CodeContent)` として返す。後段の `spec_code_verifier` や `architecture_verifier` が物理アーキテクチャを参照するための入力データを提供する。

## 入力 / 出力

| 種別 | 型 | 説明 |
|------|-----|------|
| 入力 | `bytes` | Python ソースコードの生バイト |
| 入力 | `str` | VCS 上のファイルパス（言語補助判定に使用） |
| 入力 | `ParserConfig` | callgraph_tool / type_tool / extract_contracts / language パラメータ |
| 出力 | `NormalizedArtifact` | artifact_type="code", content=CodeContent |

---

## モジュール構成

```
lib_code_parser/
├── __init__.py              # 公開 API: parse_code() をエクスポート
├── parser.py                # メインエントリポイント: parse_code()
├── ast_extractor.py         # FunctionNode / TraceTag 抽出（ast.walk ベース）
├── callgraph_builder.py     # CallGraph 生成（ast.Call 追跡）
├── type_analyzer.py         # TypeDep 生成（pyright subprocess / ast fallback）
├── contract_extractor.py    # ContractInfo 抽出（§3.7 Pydantic / dataclass validator）
└── models.py                # 共有データクラス定義（FunctionNode / CallGraph / TypeDep 等）
```

| モジュール | 責務 | 決定論性 | FR 対応 |
|-----------|------|---------|---------|
| parser.py | 統合エントリポイント・NormalizedArtifact 組立 | D | LIB-FR-06 |
| ast_extractor.py | FunctionNode / TraceTag の AST 解析抽出 | D | LIB-FR-01, LIB-FR-05 |
| callgraph_builder.py | ast.Call 追跡による CallGraph 生成 | D | LIB-FR-02 |
| type_analyzer.py | pyright subprocess + ast fallback の TypeDep 生成 | D | LIB-FR-03 |
| contract_extractor.py | Pydantic / dataclass validator の ContractInfo 抽出 | D | LIB-FR-04 |
| models.py | 全 dataclass 型定義 | D | 共通 |

---

## DFD (Data Flow Diagram)

```
[raw_content: bytes]
[path: str          ]  ──▶  [プロセス 1: 言語判定・デコード]
[config: ParserConfig]            │
                                  ▼
                         [プロセス 2: ast.parse → AST Tree]
                                  │
                    ┌─────────────┼──────────────┐
                    ▼             ▼              ▼
         [プロセス 3a:   ] [プロセス 3b:  ] [プロセス 3c:    ]
         [FunctionNode  ] [CallGraph     ] [TypeDep        ]
         [TraceTag 抽出 ] [生成          ] [生成            ]
         [ContractInfo  ] [(ast.Call)    ] [(pyright/ast)  ]
                    │             │              │
                    └─────────────┴──────────────┘
                                  │
                                  ▼
                    [プロセス 4: CodeContent 組立]
                                  │
                                  ▼
                    [プロセス 5: NormalizedArtifact 生成]
                                  │
                                  ▼
                    [NormalizedArtifact(CodeContent)]
```

| プロセス | 入力 DF | 出力 DF | 決定論性 |
|---------|---------|---------|---------|
| 1: 言語判定・デコード | raw_content + path | decoded source + language | D |
| 2: ast.parse | decoded source | AST Tree | D |
| 3a: FunctionNode / TraceTag / ContractInfo 抽出 | AST Tree + config | List[FunctionNode] | D |
| 3b: CallGraph 生成 | AST Tree + FunctionNode list | CallGraph | D |
| 3c: TypeDep 生成 | source + config | List[TypeDep] | D |
| 4: CodeContent 組立 | 3a + 3b + 3c | CodeContent | D |
| 5: NormalizedArtifact 生成 | CodeContent + path | NormalizedArtifact | D |

---

## エラー処理

| エラー条件 | 発生モジュール | 処理方針 | 例外型 |
|-----------|-------------|---------|-------|
| SyntaxError（無効な Python）| ast_extractor.py | ValueError を raise（メッセージにパス含む）| `ValueError` |
| UnicodeDecodeError（binary ファイル）| parser.py | ValueError を raise | `ValueError` |
| pyright 実行失敗 / 未インストール | type_analyzer.py | 空リスト [] を返す（graceful degrade） | なし（ログのみ） |
| サポート外の言語（.cpp 等） | parser.py | ValueError を raise（C++ は future scope）| `ValueError` |
| 空ファイル | ast_extractor.py | 空の FunctionNode / CallGraph / TypeDep を返す | なし |

---

## 依存 OSS

| OSS | バージョン | 用途 | ライセンス |
|-----|-----------|------|---------|
| Python 標準 ast | 3.11+ 標準 | AST 解析・CallGraph・ContractInfo | PSF（Python ライセンス） |
| pyright | ^1.1（オプション）| 高精度 TypeDep 生成 | MIT |

**Decision Log**: #6-1（アーキテクチャ選択の判断を記録）

---

<!-- Step 7 Spec 記述時に DFD との差異が見つかった場合は本ファイルを更新する -->
