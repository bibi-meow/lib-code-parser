# lib-code-parser Trace Matrix

> FR（機能要求）→ AT（受入テスト）→ Code（実装）→ Test（単体テスト）のトレーサビリティを管理する。
> design doc §7 Step 15 参照。
> **実装完了後に全 FR が網羅されていることを確認してから push すること。**

---

## Trace Matrix

| FR ID | FR 概要 | Acceptance Scenario | AT ファイル | 実装ファイル | 単体テストファイル | 完了 |
|-------|---------|---------------------|------------|-------------|------------------|------|
| LIB-FR-01 | Python コードから FunctionNode 一覧を抽出する | 単純関数・クラス/メソッド・空ファイル | tests/test_fr01_ast_extractor.py | lib_code_parser/ast_extractor.py | tests/test_fr01_ast_extractor.py (7 tests) | [x] |
| LIB-FR-02 | CallGraph を生成する | 呼び出しあり/なし・メソッド呼び出し・外部呼び出し除外 | tests/test_fr02_callgraph.py | lib_code_parser/callgraph_builder.py | tests/test_fr02_callgraph.py (5 tests) | [x] |
| LIB-FR-03 | TypeDep リスト（pyright なし環境での ast fallback） | 戻り値型・引数型・組み込み型除外・pyright未インストール時 | tests/test_fr03_type_analyzer.py | lib_code_parser/type_analyzer.py | tests/test_fr03_type_analyzer.py (6 tests) | [x] |
| LIB-FR-04 | ContractInfo 抽出（Pydantic / dataclass validator） | field_validator・__post_init__・extract_contracts=False | tests/test_fr04_contract_extractor.py | lib_code_parser/contract_extractor.py | tests/test_fr04_contract_extractor.py (5 tests) | [x] |
| LIB-FR-05 | TraceTag 抽出 | 単一タグ・複数タグ・タグなし・関数内タグ | tests/test_fr05_trace_extractor.py | lib_code_parser/trace_extractor.py | tests/test_fr05_trace_extractor.py (6 tests) | [x] |
| LIB-FR-06 | NormalizedArtifact 統合 | 正常ファイル・関数抽出・CallGraph・TraceTag・SyntaxError | tests/test_fr06_parser.py | lib_code_parser/parser.py | tests/test_fr06_parser.py (8 tests) | [x] |
| LIB-NFR-01 | pyright がない環境でも graceful degrade | pyright 未インストール時に空リスト/ast fallback で正常動作 | tests/test_fr03_type_analyzer.py::test_pyright_true_no_exception_when_unavailable | lib_code_parser/type_analyzer.py | tests/test_fr03_type_analyzer.py | [x] |
| LIB-NFR-02 | extract_contracts=False の場合は ContractInfo を空で返す | config.params["extract_contracts"]=False で preconditions 空 | tests/test_fr04_contract_extractor.py::test_extract_contracts_false_returns_empty, tests/test_fr06_parser.py::test_extract_contracts_false | lib_code_parser/contract_extractor.py, lib_code_parser/parser.py | tests/test_fr04_contract_extractor.py, tests/test_fr06_parser.py | [x] |

---

## カバレッジサマリ

| 指標 | 件数 |
|------|------|
| FR 総数 | 6 (LIB-FR-01〜06) |
| NFR 総数 | 2 (LIB-NFR-01〜02) |
| 実装ファイル総数 | 7 (models, parser, ast_extractor, callgraph_builder, type_analyzer, contract_extractor, trace_extractor) |
| 単体テストファイル総数 | 6 |
| 単体テスト合計件数 | 37 |
| pytest 全 PASS | YES (37/37) |
| ruff check | CLEAN |
| ruff format | CLEAN |
| pyright | 0 errors, 0 warnings |
| 全 FR 網羅済み | YES |

---

## トレーサビリティ確認チェックリスト

- [x] 全 FR ID が Trace Matrix に記載されている
- [x] 各 FR に少なくとも 1 件の Acceptance シナリオが対応している
- [x] 各シナリオに受入テストファイルのパスが記載されている
- [x] 各 FR に対応する実装ファイルが記載されている
- [x] 各 FR に対応する単体テストが記載されている
- [x] pytest で全テスト PASS が確認されている（37/37）
- [x] カバレッジサマリの「全 FR 網羅済み」が YES になっている

**Decision Log**: #15-1（2026-05-18 Trace Matrix 完成確認 — 37 tests passed, ruff + pyright clean, GitHub public）

---

<!-- Step 15 で確認済み (2026-05-18) -->
