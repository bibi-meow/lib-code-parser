# lib-code-parser Trace Matrix

> FR（機能要求）→ AT（受入テスト）→ Code（実装）→ Test（単体テスト）のトレーサビリティを管理する。
> design doc §7 Step 15 参照。
> **実装完了後に全 FR が網羅されていることを確認してから push すること。**

---

## Trace Matrix

| FR ID | FR 概要 | Gherkin シナリオ | 受入テストファイル | 実装ファイル | 単体テストファイル | 完了 |
|-------|---------|----------------|-----------------|------------|-----------------|------|
| LIB-FR-01 | [FR の概要] | Feature: [シナリオ名] | tests/test_[name].py::test_[scenario] | [lib_name]/[module].py | tests/test_[module].py::test_[unit] | [ ] |
| LIB-FR-02 | [FR の概要] | Feature: [シナリオ名] | tests/test_[name].py::test_[scenario] | [lib_name]/[module].py | tests/test_[module].py::test_[unit] | [ ] |

---

## カバレッジサマリ

| 指標 | 件数 |
|------|------|
| FR 総数 | N |
| AT（Gherkin シナリオ）総数 | N |
| 実装ファイル総数 | N |
| 単体テスト総数 | N |
| 全 FR 網羅済み | YES / NO |

---

## トレーサビリティ確認チェックリスト

- [ ] 全 FR ID が Trace Matrix に記載されている
- [ ] 各 FR に少なくとも 1 件の Gherkin シナリオが対応している
- [ ] 各 Gherkin シナリオに受入テストファイルのパスが記載されている
- [ ] 各 FR に対応する実装ファイルが記載されている
- [ ] 各 FR に対応する単体テストが記載されている
- [ ] pytest で全テスト PASS が確認されている
- [ ] カバレッジサマリの「全 FR 網羅済み」が YES になっている

**Decision Log**: #15-1（Trace Matrix 完成の確認を記録）

---

<!-- Step 9（scaffold）前にこのファイルのスケルトンを作成し、実装中に逐次更新する -->
<!-- Step 15 でこの Matrix を最終確認してから push する -->
