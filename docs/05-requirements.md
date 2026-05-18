# lib-code-parser Requirements

> cicd の lib-*.md から lib-level の機能要求（FR）を導出する。
> design doc §7 Step 5 参照。
> **Gherkin 形式で受入テスト（AT）を記述すること。**

---

## 対応 cicd lib 設計

| 設計ドキュメント | パス |
|---------------|------|
| lib-*.md | cicd/doc/sys/lib/[path]/lib-[name].md |

---

## 機能要求一覧

| FR ID | 説明 | 決定論性 | Decision Log |
|-------|------|---------|-------------|
| LIB-FR-01 | [要求の説明] | D / N / H | #5-1 |

---

## LIB-FR-01: [タイトル]

**概要**: [FR の詳細説明]

**入力**: [入力データ形式]
**出力**: [出力データ形式]
**決定論性**: D / N / H

### Gherkin 受入テスト

```gherkin
Feature: [FR-01 の機能名]
  [背景・文脈の説明]

  Scenario: [正常系シナリオ名]
    Given [前提条件]
    When [実行アクション]
    Then [期待される結果]

  Scenario: [異常系シナリオ名]
    Given [前提条件]
    When [異常な入力]
    Then [期待されるエラーハンドリング]
```

**AT ファイル**: `tests/test_[機能名].py`
**Decision Log**: #5-1

---

<!-- 追加 FR は ## LIB-FR-NN の形式で追加 -->
<!-- 各 FR に必ず Gherkin シナリオを 1 件以上付ける -->
