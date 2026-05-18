# lib-code-parser API Spec

> lib の公開 API を定義する。dataclass / TypedDict で型を明示し、pseudocode でアルゴリズムを示す。
> design doc §7 Step 7 参照。
> **API signature は 06-architecture.md の DFD と一致させること。**

---

## 公開 API 一覧

| 関数 / クラス | 入力型 | 出力型 | 決定論性 |
|-------------|-------|-------|---------|
| `[function_name]` | `[InputType]` | `[OutputType]` | D / N / H |

---

## 型定義

```python
# dataclass / TypedDict 形式で定義
# 05-requirements.md の LIB-FR-NN と対応させること

from dataclasses import dataclass
from typing import Any

@dataclass
class [InputType]:
    """[説明]"""
    [field_name]: [type]  # [説明]

@dataclass
class [OutputType]:
    """[説明]"""
    [field_name]: [type]  # [説明]
    verdict: str          # "PASS" | "FAIL" — 決定論的根拠から導出
    evidence: list[str]   # 根拠リスト（LLM 可）
    explanation: str      # 自然言語説明（LLM 可）
```

---

## API signature

```python
def [function_name](
    input: [InputType],
    *,
    [optional_param]: [type] = [default],
) -> [OutputType]:
    """
    [関数の説明]

    Args:
        input: [説明]
        [optional_param]: [説明]

    Returns:
        [OutputType]: [説明]

    Raises:
        ValueError: [エラー条件]
        RuntimeError: [エラー条件]

    Traces: LIB-FR-01
    Decision Log: #7-1
    """
    ...
```

---

## Pseudocode

```
function [function_name](input):
  1. [入力検証]: input のスキーマを検証する → ValidationError
  2. [前処理]: [処理内容] → [中間データ]
  3. [コア処理]: [決定論的アルゴリズム] → verdict
     - 決定論性: D — [理由]
     - ※ LLM を使う場合は Decision Log #7-N に非決定論性の根拠を記録
  4. [後処理]: evidence / explanation を生成する → OutputType
  5. return OutputType(verdict=verdict, evidence=..., explanation=...)
```

**Decision Log**: #7-1（API 設計の判断を記録）

---

<!-- 実装開始（Step 9）前にこの spec が 06-architecture.md と一致していることを確認すること -->
<!-- 差異があれば先に 06-architecture.md を更新する -->
