# Extension Contract (Open-Closed Invariants)

> Phase 2-4 で新 extractor / 新評価単位 / 新 EdgeKind を追加する contributor が読む文書。
> 拡張の Open-Closed 不変条件 6 件 + dispatch dict append-only invariant + EdgeKind の
> MAJOR-version 政策 + dispatch entry 追加手順を規定する。
> SDD chain: 06-architecture.md (構成) → 07-spec.md (API) → 08-common-view-pattern.md (共通 View) → **09-extending.md** (本書)。

---

## 目的

lib-code-parser は v0.2.0 以降も継続的に成長することが計画されている:

- **Phase 2** で Python frontend + 4 primitives + ContractInfo / function spec extractor を追加
- **Phase 3** で 5 diagram (Class / Sequence / Component / Package / State) extractor を追加
- **Phase 4** で C++ frontend (libclang) + C++ Doxygen 契約抽出を追加
- **将来 milestone (v0.3.0+)** で DDD リバース等の新評価単位を追加 (Deferred Ideas)

これらの追加を **既存 code に触れずに行えること** が internal-architecture の必須要件である
(PROJECT.md `## Constraints` § アーキ重視)。 ルールがなければ:

- ad-hoc な追加で `EdgeKind` に `"uses"` / `"other"` / `"misc"` が増殖し、 verifier (LLM agent)
  が物理 ↔ 論理を比較できなくなる (Pitfall 7 — diagram edge semantics ambiguity)
- 既存 primitive を改変して新 extractor を作る誘惑が発生し、 v0.1.0 caller の互換性 (parity)
  が壊れる (Pitfall 6 — cross-lib drift と同根の問題)
- dispatch dict の既存 entry が書き換えられ、 「どの extractor が走ったか」が PR ごとに
  ぶれて Layer M bisimulation の前提が崩れる

本書はこれらの drift を **規範文書として** 防ぐ。 Phase 1 では hook / lint による自動 enforcement
を導入せず、 **code review が enforcement gate** である (pre-resolved Open Question #4)。

---

## 6 つの Open-Closed 不変条件

CONTEXT.md D-13 で確定した 6 つの不変条件を verbatim で再掲する。 contributor は PR を出す
前に、 これらすべてを満たすことを確認する。

### 不変条件 #1: 既存 primitive は変更不可 (新 primitive は別 file)

`lib_code_parser/extractors/primitives/{functions,callgraph,type_deps,contracts}.py` の各
ファイルは v0.2.0 freeze 後は **書き換え不可** とする。 解析手法を追加・改良したい場合は
`lib_code_parser/extractors/primitives/<new_aspect>.py` を新規に作成する。

- ✅ Good: `lib_code_parser/extractors/primitives/class_relations.py` を新規作成して DDD リバースに使う
- ❌ Anti-pattern: `lib_code_parser/extractors/primitives/callgraph.py` の `extract()` 内に DDD 用の追加ロジックを混ぜる

理由: 既存 primitive を変えると、 既存評価単位 (clas_diagram / sequence_diagram / ...) の出力が
意図せず変わり、 v0.1.0 parity test が破壊される。

### 不変条件 #2: 既存評価単位は変更不可 (新評価単位は別 file)

`lib_code_parser/extractors/{class_diagram,sequence_diagram,component_diagram,package_diagram,state_diagram,function_spec,class_spec}.py` は v0.2.0 freeze 後は書き換え不可。 新しい diagram 種別 / 仕様種別を
追加したい場合は新規 file (例: `lib_code_parser/extractors/ddd_context_map.py`) を作成する。

- ✅ Good: `lib_code_parser/extractors/ddd_aggregate.py` を新規作成
- ❌ Anti-pattern: `lib_code_parser/extractors/class_diagram.py` に「DDD モード」フラグを追加して条件分岐

理由: 評価単位 1 つあたり 1 ファイルの 1:1 対応は verifier の比較粒度に直結する。 既存単位の
出力を改変すると Layer M bisimulation の固定点が動く。

### 不変条件 #3: `CodeContent` への追加は optional field で行う (v0.1.0 互換性維持)

`lib_code_parser/models/infrastructure/artifact.py` 内の `CodeContent` model に新 field を
追加する場合は、 **必ず optional (`field_name: SomeType | None = None`) または
default 付き** で追加する。 既存 caller (v0.1.0 形式) が新 field を意識せず構築できる必要がある。

```python
# ✅ Good
class CodeContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    functions: list[FunctionNode] = []
    # ... 既存 field ...
    ddd_relations: list[ClassRelation] | None = None   # v0.3.0+ で追加 (optional)

# ❌ Anti-pattern — required new field
class CodeContent(BaseModel):
    ddd_relations: list[ClassRelation]  # v0.1.0 caller は構築できなくなる
```

理由: 既存 caller (`tests/acceptance/test_fr*.py` 6 件 + 外部 caller) が無修正で v0.2.0 → v0.3.0
を渡れることが parity の定義。 required new field はこれを破る。

### 不変条件 #4: dispatch dict は append-only

`lib_code_parser/_dispatch.py` の 3 dict (`FRONTENDS` / `PRIMITIVES` / `EVALUATIONS`) は
**append-only** である。 既存 entry の値を別の callable に置き換える patch、 および既存 entry を
削除する patch は **禁止**。

- ✅ Good: `PRIMITIVES["ddd_relations"] = extract` を新規追加
- ❌ Anti-pattern: `PRIMITIVES["functions"] = new_extract_v2` で既存 entry を上書き

この invariant の enforcement は **code review に依存する** (Phase 1 では hook / lint 自動
enforcement を ship しない — pre-resolved Open Question #4)。 reviewer は `_dispatch.py` への
patch に対して以下を確認する:

- 追加された行は `DICT["new_key"] = new_fn` の形か (既存 key の上書きでないか)
- 既存行の削除がないか (`git diff` で `-` 行を確認)
- 既存 callable の signature が変わっていないか (extractor 側の breaking change を伴わないか)

### 不変条件 #5: 評価単位は primitives を pull で取得 (push 型注入ではない)

評価単位 extractor (例: `class_diagram.py`) は、 必要な primitive を **直接 import (pull)** して
取得する。 dispatch dict 経由で primitive 結果を受け取る (push) 設計は採用しない。

```python
# ✅ Good: pull
# lib_code_parser/extractors/class_diagram.py
from lib_code_parser.extractors.primitives import callgraph, type_deps


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    cg = callgraph.extract(cav, config)
    tds = type_deps.extract(cav, config)
    return _build_class_diagram(cg, tds)


# ❌ Anti-pattern: push (executor が primitive 結果を引数に渡す)
def extract(cav, config, callgraph_result, type_deps_result): ...
```

理由: pull 型なら評価単位ごとに **必要な primitive だけ** を選んで読み込める。 push 型だと
executor が全 primitive を毎回計算する必要が生じ、 disabled な評価単位の primitive まで無駄に
計算してしまう。

### 不変条件 #6: executor は dispatch dict 走査ロジックのみ (評価単位を増やしても変更しない)

`lib_code_parser/executor.py` 内の `CodeParserExecutor.execute()` は dispatch dict (`FRONTENDS` /
`EVALUATIONS`) を for-loop で走査するロジックだけを持つ。 評価単位を追加しても executor 本体は
変わらない。

```python
# ✅ Good (擬似コード)
def execute(self, config, raw_content, path) -> NormalizedArtifact[CodeContent]:
    cav = FRONTENDS[config.language](raw_content, path, config)
    content = CodeContent()
    for name, fn in EVALUATIONS.items():
        if config.is_enabled(name):
            setattr(content, name, fn(cav, config))
    return NormalizedArtifact(artifact_id=..., artifact_type="code", content=content)


# ❌ Anti-pattern: 評価単位ごとに if 分岐
def execute(self, config, raw_content, path):
    if config.extract_class_diagram:
        ...
    if config.extract_sequence_diagram:
        ...
```

理由: 評価単位を増やすたびに executor を書き換える設計だと、 不変条件 #2 (既存評価単位は変更
不可) が機能しない。 executor が動的に dict を走査する形を維持することで、 Phase 2-4 の
追加が executor.py に **0 行の diff** で済む。

#### 不変条件 #6 への一回限りの改訂 (Phase 4 D-01 — 言語軸の導入)

Phase 4 plan 04-01 (CONTEXT.md D-01) で `PRIMITIVES` / `EVALUATIONS` に **言語次元** を
導入した。 これにともない executor の走査 2 行が以下に **一回だけ** 変わる:

```python
# Phase 2-3: 言語非依存の flat 走査
for name, fn in PRIMITIVES.items(): ...
for name, fn in EVALUATIONS.items(): ...

# Phase 4 D-01 以降: cav.language で index した走査
for name, fn in PRIMITIVES[cav.language].items(): ...
for name, fn in EVALUATIONS[cav.language].items(): ...
```

これは「評価単位を増やすたびに executor が変わる」変更ではない。 **言語軸の導入という
一回限りの構造変更** であり、 これ以降 cpp の extractor / 評価単位を追加しても executor 本体は
再び 0 行 diff である (新しい言語キーの sub-dict に entry を append するだけ)。 したがって
不変条件 #6 の精神 (extractor 追加で executor body が成長しない) は維持される。 この一回限りの
例外は D-01 の load-bearing 構造変更として明示的に許容される。

---

## 論理アーキ比較対象は models/evaluations/ のみ (D-14)

verifier (`spec_code_verifier` / `architecture_verifier` などの LLM agent) が論理アーキ
(spec / 設計書) と比較するのは、 **`lib_code_parser/models/evaluations/` 配下の出力のみ** で
ある (CONTEXT.md D-14)。

- `models/evaluations/` — 5 diagram + 2 spec → 論理アーキと直接比較される
- `models/primitives/` — `FunctionNode` / `CallGraph` / `TypeDep` / `ContractInfo` etc. → 中間データ。 verifier には渡さない
- `models/infrastructure/` — `CAV` / `NormalizedArtifact[TContent]` / `ParserConfig` → I/O 契約。 verifier には渡さない

この layer purity rule の重要な帰結は **`EdgeKind` Literal の適用範囲** である:

- `models/evaluations/graph_base.py` の `GraphEdge.edge_type: EdgeKind` は 11 値の closed Literal
  として strict に固定 (SCH-03)。 ad-hoc 拡張は Pydantic ValidationError で reject される。
- `models/primitives/type_deps.py` の `TypeDep.kind: str` は **free-form `str` のまま** で残す。
  なぜなら primitives は verifier に直接渡されないため、 strict Literal で縛ると言語固有の
  type 種別 (例: C++ の `friend`, Python の `Protocol`) を表現する自由度が失われ、 拡張時に
  「`kind` 値を 1 つ増やすたびに MAJOR version bump が必要」という過剰な制約になってしまう。

つまり EdgeKind の strict 化は **verifier に渡る surface を守るため** であり、 内部中間データ
には適用されない。 この区分を踏み外して `TypeDep.kind` を Literal 化すると、 表現幅 (variability)
を不必要に絞ることになる。

---

## EdgeKind 追加は MAJOR version 案件

`models/evaluations/graph_base.py` の `EdgeKind` は 11 値の closed Literal:

```python
EdgeKind = Literal[
    "inherits", "implements",
    "composes", "aggregates", "associates",
    "field_of", "param_of", "returns", "instantiates",
    "calls", "transitions_to",
]
```

11 値で 5 diagram すべてを MECE にカバーしている (本研究 §EdgeKind Closed Literal の coverage table)。
新しい EdgeKind 値の追加は **ad-hoc patch では一切認められない**。 以下 3 つすべてを満たす必要がある:

1. **issue を立てる**: なぜ既存 11 値のいずれもフィットしないかを明文化する。 既存値:
   `inherits / implements / composes / aggregates / associates / field_of / param_of / returns /
   instantiates / calls / transitions_to` のどれにも該当しないことを具体例で示す。
2. **MAJOR version bump**: lib-code-parser を v0.x.0 → v1.0.0 (または v1.x.0 → v2.0.0) に上げる。
   patch / minor では受け付けない。 schema 互換性に影響するため breaking change として扱う。
3. **sibling lib 協調更新**: lib-diagram-parser と `architecture_verifier` も同時に新 EdgeKind 値を
   理解できるよう更新する。 cross-lib drift (Pitfall 6) を生まないため。

### 禁止される ad-hoc patch

- ❌ `EdgeKind = Literal[..., "uses", "other", "misc"]` のような catch-all 追加
- ❌ "uses" / "other" / "misc" / "ref" / "dep" のような曖昧語の追加

これらは Pitfall 7 (diagram edge semantics ambiguity) を再生産する。 「あいまいだから catch-all を
入れる」という発想自体が間違っており、 catch-all は verifier が物理 ↔ 論理を区別できなくする
原因となる。

### 判定不能の場合の正規 fallback: `"associates"`

composition (`composes`) と aggregation (`aggregates`) の区別が type annotation 情報だけでは
**決定論的に判定不能** な場合がある (例: Python で `field: Logger` と書かれているが、 lifecycle 所有が
コードからは判断できないケース)。 こうしたケースは catch-all を増やすのではなく、
**`"associates"` を explicit fallback として使う** (DIA-01 の規定)。

- `"associates"` は「reference 関係はあるが ownership は undecidable」という **明示的なセマンティクス**
  を持つ enum 値である。 catch-all ではなく、 「決められなかった」ことを伝える正規の選択肢。
- 判定可能なケースで `"associates"` を濫用するのは別の anti-pattern (情報損失) なので、
  decision 規則 (type annotation の `Optional` / `list` 有無 → aggregates、 直接型 → composes) を
  先に適用し、 適用できない場合のみ `"associates"` を選ぶ。

---

## dispatch dict への entry 追加手順

新しい frontend / primitive / evaluation を追加する標準手順を示す。 すべて
**既存 file には触らず、 新 file 追加 + `_dispatch.py` への 1 行追加のみ** で完結する。

### Frontend を追加する (例: 新言語サポート)

```bash
# 1. Frontend 実装を新規作成
$ vim lib_code_parser/frontends/<lang>.py

# build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV
# を export する pure function を書く
```

```python
# 2. lib_code_parser/_dispatch.py に 1 行追加 (append-only)
from lib_code_parser.frontends import <lang> as _<lang>_frontend

FRONTENDS["<lang>"] = _<lang>_frontend.build_cav
```

PR は **frontend 単体** で submit する (primitive / evaluation の追加とは別 PR に分ける)。
review 観点は「signature が `(bytes, str, ParserConfig) -> CAV` であること」「`CAV.language`
discriminator に新言語値を追加した場合 Literal を拡張する」など。

### Primitive を追加する

```bash
# 1. Primitive 実装を新規作成
$ vim lib_code_parser/extractors/primitives/<aspect>.py

# extract(cav: CAV, config: ParserConfig) -> <PrimitiveModel>
# を export する
```

```python
# 2. 対応する model を新規作成
$ vim lib_code_parser/models/primitives/<aspect>.py
# class <PrimitiveModel>(BaseModel):
#     model_config = ConfigDict(extra="forbid")    # SCH-02 必須
#     ...

# 3. _dispatch.py に 1 行追加
from lib_code_parser.extractors.primitives import <aspect> as _<aspect>_primitive

PRIMITIVES["<aspect>"] = _<aspect>_primitive.extract
```

`extra="forbid"` を必ず指定する (SCH-02)。 そうしないと unknown field が silent に流入する。

### Evaluation を追加する

```bash
# 1. Evaluation 実装を新規作成
$ vim lib_code_parser/extractors/<diagram_or_spec>.py

# extract(cav: CAV, config: ParserConfig) -> <EvaluationModel>
# を export する。 必要な primitives は pull で import する (不変条件 #5)
```

```python
# 2. 対応する model を新規作成 (verifier-facing なので strict)
$ vim lib_code_parser/models/evaluations/<name>.py
# class <EvaluationModel>(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     ...

# 3. _dispatch.py に 1 行追加
from lib_code_parser.extractors import <name> as _<name>_eval

EVALUATIONS["<name>"] = _<name>_eval.extract
```

### 新言語の extractor セット追加手順 (Phase 4 D-01 — 言語次元)

Phase 4 plan 04-01 (CONTEXT.md D-01) で `PRIMITIVES` / `EVALUATIONS` は
**`dict[language, dict[name, fn]]`** の入れ子構造になった (`FRONTENDS` は言語キー単独の
flat `dict[language, fn]` のまま — 1 言語 1 frontend なので二重入れ子にしない、 Phase 4 Pitfall 1)。
新しい言語 (例: `cpp`) の extractor セットを追加する手順は、 上の「dispatch dict への entry
追加手順」を言語キー配下で行うだけである:

```python
# 1. その言語の frontend を FRONTENDS に append (上の Frontend 追加手順と同じ)
FRONTENDS["cpp"] = _cpp_frontend.build_cav

# 2. その言語の primitive / evaluation sub-dict に entry を append
#    (plan 04-01 で {"python": {...}, "cpp": {}} の空 sub-dict が既に予約されている)
PRIMITIVES["cpp"]["functions"] = _cpp_functions.extract
EVALUATIONS["cpp"]["class_diagram"] = _cpp_class_diagram.extract
# ... 言語ごとに必要な aspect を登録する
```

スロット名 (`functions` / `class_diagram` / ...) は **言語をまたいで共通** に保つ
(LNG-04 parity: 物理側の出力スロットが言語に依らず同形式であること)。 executor は
`PRIMITIVES[cav.language]` / `EVALUATIONS[cav.language]` を走査するので、 cpp の extractor は
cpp CAV のときだけ走り、 python の extractor は python CAV のときだけ走る。

**不変条件 (言語キーは append-only)**: 既存の言語キー (`"python"`) の **削除・改名は禁止**
である (dispatch dict 全体の append-only 不変条件 #4 を言語次元に拡張したもの)。 新言語の
追加は `PRIMITIVES["<lang>"] = {}` / `EVALUATIONS["<lang>"] = {}` の sub-dict 予約 + その配下への
aspect 登録のみで完結し、 既存言語の entry / 値には一切触れない。

### 禁止操作

- **既存 entry の修正**: `PRIMITIVES["python"]["functions"] = new_extract` のような既存 key への
  代入は禁止 (不変条件 #4 違反)
- **既存 entry の削除**: `del PRIMITIVES["python"]["functions"]` は禁止 (caller の output schema を壊す)
- **既存言語キーの削除・改名**: `del PRIMITIVES["python"]` や `"python"` → 別名への変更は禁止
  (言語キーは append-only)
- **既存 callable の signature 変更**: `extract(cav, config)` を `extract(cav, config, options)` に
  変更するのは breaking change (MAJOR version 案件)

これらの禁止は **code review が enforcement gate** である (Phase 1 では hook / lint 自動
enforcement を ship しない — pre-resolved Open Question #4)。 reviewer は patch 内の `_dispatch.py`
diff が `+` 行のみであることを目視確認する。 hook / lint による自動化は Phase 2+ で必要性が
出てから検討する (現時点では over-engineering)。

---

## 拡張シナリオ例 (DDD リバース)

将来 milestone (v0.3.0+) で「コードから DDD リバース」評価単位を追加する場合のシナリオを
示す (CONTEXT.md `## Deferred Ideas` §Future evaluation units)。 6 不変条件すべてが守られる
ことを確認できる。

### 追加するもの

(a) 新 primitives 3 件:

- `lib_code_parser/extractors/primitives/class_relations.py` — 継承 + 集約 + 依存の関係
- `lib_code_parser/extractors/primitives/naming_patterns.py` — Entity / VO 命名規約検出
- `lib_code_parser/extractors/primitives/module_groups.py` — BC (Bounded Context) 推測

(b) 新評価単位 3 件:

- `lib_code_parser/extractors/ddd_context_map.py` — BC 関係図
- `lib_code_parser/extractors/ddd_aggregate.py` — Aggregate root + 構成 Entity
- `lib_code_parser/extractors/ddd_layer_diagram.py` — Layered Architecture 検出

### 6 不変条件の確認

| 不変条件 | 確認内容 |
|---------|---------|
| #1 既存 primitive 不変 | `extractors/primitives/{functions,callgraph,type_deps,contracts}.py` のいずれも touch しない。 新 3 file のみ追加 |
| #2 既存評価単位不変 | `extractors/{class_diagram,sequence_diagram,...}.py` のいずれも touch しない。 新 3 file のみ追加 |
| #3 CodeContent optional field | `CodeContent` に `ddd_context_map: GraphModel \| None = None` 等を optional で追加 |
| #4 dispatch dict append-only | `_dispatch.py` で `PRIMITIVES["class_relations"] = ...` etc. を 6 行 append。 既存 entry 上書き / 削除なし |
| #5 primitives は pull | `ddd_aggregate.py` 内で `from lib_code_parser.extractors.primitives import class_relations, naming_patterns` で取得 |
| #6 executor 不変 | `executor.py` は 1 行も書き換えない。 走査ロジックが新 3 評価単位を自動的に拾う |

このシナリオで modified file は: 新規 6 file + `_dispatch.py` への 6 行 append + `CodeContent`
への 3 行 optional field 追加 = 計 9 file。 既存評価単位 / 既存 primitive / executor / parser
core / models infrastructure はゼロ touch。 この diff 形状を維持できる限り、 lib-code-parser は
Open-Closed である。

---

## Traceability

- **Traces: ARC-01, ARC-02, ARC-03, ARC-04, ARC-05, SCH-01, SCH-02, SCH-03, DET-04**
  - ARC-01: nested module layout (`models/{infrastructure,primitives,evaluations}/` 3 分割)
  - ARC-02: CAV envelope での single-parse
  - ARC-03: subprocess を `adapters/` に隔離 (拡張手順で adapters の追加にも言及)
  - ARC-04: `_paths.get_module_name()` single source of truth
  - ARC-05: typed `ParserConfig` (`params: dict[str, object]` 廃止)
  - SCH-01: `lib-diagram-parser` model 互換性 (subclass 含む)
  - SCH-02: 全 model に `ConfigDict(extra="forbid")`
  - SCH-03: `EdgeKind` 11 値 closed Literal (本書 §EdgeKind 追加は MAJOR version 案件)
  - DET-04: 単一 source of truth (`_paths` / `_dispatch`)
- Back-links:
  - `lib_code_parser/_dispatch.py` のモジュール docstring が本書 §dispatch dict への entry 追加手順 に
    forward-reference する (Plan 06 で実装)
  - 上流文書: 08-common-view-pattern.md (本書が前提とする envelope pattern)

---

<!-- Decision Log: CONTEXT.md D-13 (6 不変条件) + D-14 (層 purity) + 01-RESEARCH.md §EdgeKind Closed Literal + Pitfall 7 -->
<!-- Pre-resolved Open Question #4: append-only invariant は Phase 1 では code review で enforce、 hook / lint 自動化は ship しない -->
