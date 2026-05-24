# Common View Pattern (CAV + Generic NormalizedArtifact)

> v0.2.0 で導入する cross-cutting envelope pattern を記述する。
> 兄弟 lib (lib-spec-parser / lib-diagram-parser / 他) が後で同 pattern を採用する際の参照モデルでもある。
> SDD chain: 06-architecture.md (構成) → 07-spec.md (API) → **08-common-view-pattern.md** (本書) → 09-extending.md (拡張点)。

---

## 目的

v0.1.0 の `lib_code_parser/*.py` は 4 つの extractor (`ast_extractor` / `callgraph_builder` /
`type_dep_builder` / `contract_extractor`) がそれぞれ独立に `ast.parse(source)` を呼び、
1 ファイルあたり **AST を 4 回再パース** していた (`.planning/codebase/CONCERNS.md` で
anti-pattern として明示)。 同じ source を 4 回パースするのは決定論性に影響しないが、
(a) パフォーマンスが線形劣化する、 (b) 「parse 結果が同一であること」を黙示的に仮定して
いるため将来の C++ 拡張で破綻する、 という二重の問題があった。

加えて、 Python `ast.Module` と C++ `clang.cindex.TranslationUnit` は **互いに型・API が
完全に異なる** 異種データである。 これを extractor 側で個別に if/elif 分岐させると、
extractor の数だけ言語分岐が増殖し、 cross-cutting な variability surface が膨らむ。

本 pattern の目的は次の 3 点である:

1. **single-parse**: Frontend が言語ごとに 1 回だけ parse し、 全 extractor は同じ AST を共有する。
2. **opaque payload**: extractor は `ast.Module` / `TranslationUnit` を直接見ず、 共通 envelope
   (CAV) 経由で受け取る。 typed union (`PythonCAV | CppCAV`) は採用せず、 `payload: object` の
   opaque 型で保持し、 言語分岐は **extractor 内部の責務** とする。
3. **transferable I/O contract**: 兄弟 lib が同 pattern を採用しやすいよう、 envelope 型と
   I/O signature を一般名で固定する。

---

## CAV (Common AST View) 定義

CAV は単一の Pydantic v2 BaseModel で、 言語識別子 (Literal discriminator) + 不透明 payload を
保持する。

```python
# lib_code_parser/models/infrastructure/cav.py
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict


class CAV(BaseModel):
    """Common AST View — single-parse envelope shared by all extractors.

    `payload` is intentionally opaque (`object`) so the Python frontend can
    store `ast.Module` and the C++ frontend can store
    `clang.cindex.TranslationUnit` without forcing a typed union on the
    cross-cutting contract.
    """

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
        frozen=True,
    )
    language: Literal["python", "cpp"]
    path: str
    payload: object
```

`ConfigDict` の 3 flag はそれぞれ次の役割を持つ:

| flag | 役割 | 根拠 |
|------|------|------|
| `extra="forbid"` | unknown field 注入を `ValidationError` で reject する | SCH-02 — schema drift 防止 (兄弟 lib との JSON 互換境界が侵蝕されないため) |
| `arbitrary_types_allowed=True` | `ast.Module` / `cindex.TranslationUnit` のような非 Pydantic 型を `payload` に格納可能にする | これがないと Pydantic は payload の validation を silently skip し、 runtime で型不一致が発生する |
| `frozen=True` | CAV インスタンス生成後の field 書き換えを禁止する | 全 extractor が同一 CAV を読み取り専用で共有するための immutability 保証。 1 つの extractor が変異させた場合の race-like 不具合を排除 |

---

## NormalizedArtifact[TContent] Generic 化

v0.1.0 の `NormalizedArtifact` は `content: CodeContent` と固定型で書かれていた。 v0.2.0 は
Pydantic v2 Generic で `NormalizedArtifact[TContent]` に汎用化し、 「`content` の型を caller 側で
refine 可能」にする。

```python
# lib_code_parser/models/infrastructure/artifact.py
from __future__ import annotations
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict


TContent = TypeVar("TContent", bound=BaseModel)


class ArtifactId(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    path: str


class NormalizedArtifact(BaseModel, Generic[TContent]):
    """Generic envelope for parsed artifacts."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    artifact_id: ArtifactId
    artifact_type: str
    content: TContent
```

この設計は v0.1.0 caller の書き方をそのまま生かす:

```python
# 旧 caller (v0.1.0 形式) — そのまま動く
e1 = NormalizedArtifact(
    artifact_id=ArtifactId(path="x.py"),
    artifact_type="code",
    content=CodeContent(...),
)

# 新 caller (typed 形式) — 型推論が refined される
e2: NormalizedArtifact[CodeContent] = NormalizedArtifact[CodeContent](
    artifact_id=ArtifactId(path="x.py"),
    artifact_type="code",
    content=CodeContent(...),
)

# 重要: e1 と e2 は model_dump_json() で byte-identical な JSON を生成する
assert e1.model_dump_json() == e2.model_dump_json()
```

このことは実機検証で確認済みである (`.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md`
§Pydantic v2 Generic for NormalizedArtifact[TContent])。 既存 acceptance test
(`tests/acceptance/test_fr*.py`) は parity test として無修正で通る。

---

## I/O variability — caller-agnostic 原則

本 lib は I/O・ログ出力・設定読込・clock 参照・network アクセスを **一切行わない**
(PROJECT.md `## Constraints` で固定された契約)。 公開 API は次の 1 つの形に集約される:

```python
def execute(
    config: ParserConfig,
    raw_content: bytes,
    path: str,
) -> NormalizedArtifact[CodeContent]: ...
```

呼び出し側 (caller) の責務:

- ファイル読み込み (`Path.read_bytes()`) は caller 側で行う。 lib は `bytes` で受け取るのみ。
- ログ・進捗報告 / metrics は caller 側で実装する。 lib 側に logger は存在しない。
- 環境変数・設定ファイルは caller が読み込んで `ParserConfig` に詰める。 lib 側で
  `os.environ` を参照しない。

この caller-agnostic 原則は 4 つの帰結を持つ:

1. **決定論性**: 出力は `(config, raw_content, path)` の純粋関数。 同じ入力に対して同じ出力。
2. **テスト容易性**: バイト列を直接渡せるので I/O を mock する必要がない。
3. **副作用ゼロ**: lib 呼び出しが他システムの状態を変えない (file open / network も含めて)。
4. **兄弟 lib との互換性**: 7 lib (lib-spec-parser / lib-diagram-parser / lib-scdl-builder / ...) すべてが
   同じ caller-agnostic 契約を採用しており、 verifier (上位 orchestrator) が統一的に呼び出せる。

なお subprocess (pyright / Doxygen / 他) は **adapters/ 層内部に隔離** されており、 extractor
からは Pydantic model 経由でのみアクセスする (06-architecture.md / 09-extending.md 参照)。
subprocess 自体は I/O だが、 「lib 出力が決定論的である」ことに変わりはない (adapters 層で
正規化済み)。

---

## 兄弟 lib 採用ガイド

将来 `lib-spec-parser` / `lib-diagram-parser` / 他兄弟 lib が同 pattern を採用したくなった
場合の最小レシピを示す。 ただし **Phase 1 ではこのレシピを兄弟 lib に適用しない** —
workspace 共通規約 (`spec-reviewer-libs/CONVENTIONS.md`) は `.planning/phases/01-.../01-CONTEXT.md`
`## Deferred Ideas` に保留されており、 「兄弟 lib のうち 2 個以上が同 pattern を採用し
始めたタイミング」で起票する。

### 採用 4 ステップ

1. **`TContent` TypeVar 定義**: `TContent = TypeVar("TContent", bound=BaseModel)` を `models/` 配下に置く。
2. **`NormalizedArtifact[TContent]` 宣言**: Pydantic v2 Generic で envelope を作る:
   ```python
   class NormalizedArtifact(BaseModel, Generic[TContent]):
       model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
       artifact_id: ArtifactId
       artifact_type: str
       content: TContent
   ```
   `extra="forbid"` を必ず有効にする (schema drift 防止)。
3. **byte-identical JSON parity を保つ**: 既存 caller (Generic 未使用) と新 caller
   (Generic 使用) で `model_dump_json()` の出力が byte-identical であることを test で固定する。
   これは Pydantic v2 の Generic 実装が unparameterized 構築を許容するため、 ゼロ追加コストで
   満たせる (本書 §NormalizedArtifact[TContent] Generic 化 の検証結果)。
4. **subprocess hardening helper の copy/re-use**: lib-code-parser の
   `lib_code_parser/adapters/base.py:run_subprocess()` は **transferable helper** として
   設計されており、 内部 state を持たない pure function である。 兄弟 lib は同 helper を
   verbatim でコピー (または将来 workspace 共通 lib として import) して subprocess の
   determinism (locale / hash seed / encoding / timeout / cwd) を統一できる。

### Phase 1 で **shipped されないもの**

- workspace 共通 lib (`spec-reviewer-libs-common`) としての切り出し — Deferred
- workspace `CONVENTIONS.md` の作成 — Deferred
- 兄弟 lib の I/O 揃え PR — Deferred (兄弟 lib が独自に v0.2.0 級進化を始めたタイミングで coordinate)

これらは「兄弟 lib のうち 2 個以上が同 pattern を採用し始めた」段階で起票する
(`.planning/phases/01-.../01-CONTEXT.md` `## Deferred Ideas` §Workspace coordination)。

---

## Traceability

- **Traces: ARC-02, ARC-04, ARC-05**
  - ARC-02: All AST primitive extractors operate on a single Common AST View — file parsed once per execute() call
  - ARC-04: Single source of truth for module name resolution (`_paths.get_module_name`) — CAV.path はその source
  - ARC-05: `ParserConfig.params: dict[str, object]` is replaced with typed Pydantic fields — caller-agnostic I/O 契約と一体
- Forward references:
  - `docs/09-extending.md` — 拡張点契約 (6 不変条件) で CAV / NormalizedArtifact の immutability を不変条件として明文化
  - `lib-code-parser.md` §採用アルゴリズム — v0.2.0 spec doc rewrite (Plan 02) が本書を forward-reference する

---

<!-- Decision Log: CONTEXT.md D-04, D-05, D-06, D-07, D-08, D-09 -->
