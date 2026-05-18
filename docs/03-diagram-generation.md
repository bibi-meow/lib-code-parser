# lib-code-parser Diagram Generation 手法

> input data から diagram を生成するアルゴリズム・実装方針を定義する。
> design doc §7 Step 4 参照。

---

<!-- 本 lib が diagram を扱わない場合:
  ## 適用外宣言
  本 lib は diagram を扱わない。
  理由: [理由]
  → Step 4 完了（02-diagram-spec.md も同様に適用外宣言済みであること）
-->

---

## 生成対象

| diagram 種別 | 生成元 input | 生成手法（概要） |
|------------|------------|--------------|
| [例: SCDL PFD] | [例: spec ファイル] | [例: AST 解析 + グラフ構築] |

---

## アルゴリズム定義

### [diagram 種別] 生成アルゴリズム

**決定論性**: D / N / H

```
1. input: [入力データ形式・スキーマ]
2. パース: [パース手法（AST / regex / 専用パーサ）]
3. 変換: [変換ルール — 入力要素 → ノード / エッジ]
4. 検証: [スキーマ検証 — 02-diagram-spec.md のスキーマ準拠チェック]
5. 出力: [出力形式（NetworkX グラフ / JSON / dataclass）]
```

---

## Step 3 Diagram Spec との差異（Step 4 発見分）

Step 4 の実装方針検討中に 02-diagram-spec.md との差異が見つかった場合はここに記録し、
`02-diagram-spec.md` を即更新する。

| 発見日 | 差異内容 | 02-diagram-spec.md 更新内容 | Decision Log |
|-------|---------|--------------------------|-------------|
|       |         |                           | #4-N        |

**Decision Log**: #4-1（手法選択の判断を記録）
