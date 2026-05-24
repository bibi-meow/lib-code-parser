# lib-code-parser — v0.2.0 Architecture Specification

**Package:** `spec_reviewer_code_parser` (PyPI 配布名: `lib-code-parser`)
**Version:** 0.2.0 (Phase 1 〜 Phase 5 で段階的に実装、本 spec doc は v0.2.0 target を記述)
**License:** Apache-2.0 (SPDX: `Apache-2.0`) — `LICENSE` 同梱、Section 3 patent grant clause 含む
**Status:** v0.1.0 (commit `cf7e7ec`) を baseline とした v0.2.0 への進化仕様。旧版は `frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md` に保存

---

## §概要

`lib-code-parser` は、Python と C++ のソースコードから **構造化されたアーキテクチャ表現を決定論的に・最大忠実度で・spec 側 (`lib-diagram-parser`) と同形式で** 抽出する pip ライブラリである。
spec-reviewer パイプラインの `spec_code_verifier` (US-01 / US-22) と `architecture_verifier` (US-32) に物理アーキの入力を供給する Parser lib として機能する。物理 (code) と論理 (spec) の表現幅ギャップの解釈は verifier (LLM agent) の責務であり、本 lib は **事実抽出のみ** を担って決定論性を維持する。これが崩れると Layer M bisimulation (構造一致判定) が成立しない。

v0.2.0 で targeted する全方針は以下のとおり:

- **内製 call graph extractor** — AST 静的解析で実装し、外部 OSS には依存しない (pyan3=GPL viral 不採用、PyCG=archived 不採用、code2flow=非決定論 不採用)。本 lib 内の Apache-2.0 コードのみで構成され、**GPL viral を一切持ち込まない**
- **`pyright[nodejs]==1.1.409` subprocess** — Microsoft MIT、`[nodejs]` extra で Node bundled、型解決済み `TypeDep` 取得 (Python)
- **`libclang==18.1.1` in-process ctypes** — Apache-2.0 WITH LLVM-exception、厳密 pin、ABI 整合性を保つため `Config.set_library_file` を禁止。import 時 runtime guard で `cindex.Index.create()` を呼んで dylib load を検証
- **CAV (Common AST View)** — 1 ファイル 1 回 parse の immutable Pydantic envelope。全 extractor が CAV を pull で消費 (`frozen=True`、`arbitrary_types_allowed=True`、`extra="forbid"`)。v0.1.0 の AST 4 回再パース アンチパターンを解消 (ARC-02 / AST-05)
- **EdgeKind closed Literal** — `inherits / implements / composes / aggregates / associates / field_of / param_of / returns / instantiates / calls / transitions_to` の 11 値固定。`uses` / `other` / `misc` 等の catch-all は **不採用** (Pitfall 7)
- **5 種 diagram** — class / sequence / component / package / state を `lib-diagram-parser` 互換 schema (`GraphNode` / `GraphEdge` / `GraphModel` / `GuardExpr`) で抽出
- **2 種 spec** — function spec (Python signature + docstring + pre/post + Doxygen C++) / class spec (members + invariants + Doxygen C++) を Python / C++ 対称に出力
- **Doxygen 契約抽出** — C++ `\pre` / `\post` / `\invariant` を解析し、Python の Pydantic validator / dataclass `__post_init__` と対称な `ContractInfo` を生成
- **icontract / deal / PEP-316** — Python 補助的契約抽出 (Pydantic / dataclass の補完)
- **Apache-2.0 license** — `LICENSE` 同梱 (Section 3 Grant of Patent License 含む)。No GPL bundled
- **`physical_*` / `source_*` prefix** — 物理側のみのメタデータ (`physical_module`, `source_range` 等) は schema 拡張時に optional prefix で識別 (SCH-02)
- **Traceability** — 42 件の v1 requirements を US-01 / US-22 / US-25 / US-32 にマップ。各 extractor module の docstring に `Traces: REQ-ID` 行を埋め込む (TRC-01 / TRC-02 / TRC-03)

旧 v0.1.0 spec doc に存在した「コールグラフ生成には Common Lisp theorem prover 経由の決定論的ツール (該当 PyPI script)」記述は、**実在しない参照** であったため v0.2.0 では削除し、内製 extractor の説明に全面置換した (DOC-01)。

`Traces: ARC-01`
`Traces: ARC-02`

---

## §インターフェース

caller API は単一の orchestrator class `CodeParserExecutor` に集約される:

```python
from lib_code_parser import CodeParserExecutor, ParserConfig, NormalizedArtifact, CodeContent

executor = CodeParserExecutor()
config = ParserConfig(
    enabled=True,
    language="python",
    extract_contracts=True,
    compile_args=["-std=c++17"],   # C++ のみ参照
    python_version="3.11",
)
artifact: NormalizedArtifact[CodeContent] = executor.execute(
    config=config,
    raw_content=b"def foo(): ...",
    path="example.py",
)
```

### `ParserConfig` typed fields (D-08 / ARC-05)

v0.2.0 で `params: dict[str, object]` を廃止し、Pydantic typed fields に migrate する (ARC-05):

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `enabled` | `bool` | `True` | 無効化時は executor が空の `CodeContent` を即返す (gating) |
| `language` | `Literal["python", "cpp"]` | `"python"` | Frontend dispatch key。`_dispatch.FRONTENDS[language]` で CAV builder を選択 |
| `extract_contracts` | `bool` | `True` | False 時は `contracts` 抽出を skip (cost 削減) |
| `compile_args` | `list[str]` | `["-std=c++17"]` | C++ only。`libclang.TranslationUnit.parse(args=...)` に渡す compile flags。未解決 `#include` は warning |
| `python_version` | `str` | `"3.11"` | `pyright` 等の型解決ツールが参照する PEP 561 target version |

**v0.1.0 からの破壊的変更:** `params: dict[str, object]` 経由のフリーフォーマット引数は削除する (ARC-05)。同様に、旧版に存在した tool-script 指定用の dict field は **追加しない** — call graph は内製 extractor が `_dispatch.PRIMITIVES["callgraph"]` から無条件で供給されるため、caller が tool を選ぶ余地は不要。`extra="forbid"` のため未知 field は ValidationError になる (SCH-03)。

### Executor signature

```python
class CodeParserExecutor:
    def execute(
        self,
        config: ParserConfig,
        raw_content: bytes,
        path: str,
    ) -> NormalizedArtifact[CodeContent]:
        ...
```

- **入力 (caller が供給):** 純粋関数の引数のみ。Library は file I/O・network・logging・clock を一切呼ばない (I/O policy)
- **出力:** Pydantic Generic envelope `NormalizedArtifact[CodeContent]` を返す。caller は `artifact.content.functions` 等で AST primitives を取得し、`artifact.content` の他の field で diagram / spec を受け取る (Phase 2-4 で順次充足)
- **Determinism:** 同一 `(raw_content, path, config)` に対して byte-identical な `NormalizedArtifact` を返す (DET-01)

`Traces: ARC-05`

---

## §出力 schema

すべての出力は Pydantic v2 `BaseModel` で、`model_config = ConfigDict(extra="forbid")` を **全 model に必須** とする (SCH-03)。これにより不明 field の混入は ValidationError として早期に検出され、cross-lib schema drift を防ぐ。

### Envelope: `NormalizedArtifact[TContent]` (Pydantic Generic)

```python
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict

TContent = TypeVar("TContent", bound=BaseModel)

class NormalizedArtifact(BaseModel, Generic[TContent]):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    artifact_id: ArtifactId       # path-derived identifier
    artifact_type: str            # "code" / "spec" / "diagram" 等
    content: TContent             # refined per lib (本 lib では CodeContent)
```

Generic 化により caller (verifier 側) は `content` の型を refine できるが、本 lib では常に `CodeContent` を埋める。

### Aggregate: `CodeContent`

`CodeContent` は v0.2.0 で抽出する全 primitives / evaluations の入れ物:

| Field | Type | Source |
|-------|------|--------|
| `functions` | `list[FunctionNode]` | `extractors/primitives/functions.py` (AST-01) |
| `call_graph` | `CallGraph` | `extractors/primitives/callgraph` module (AST-02、内製 extractor) |
| `type_deps` | `list[TypeDep]` | `extractors/primitives/type_deps.py` + `adapters/pyright.py` (AST-03) |
| `contracts` | `dict[str, ContractInfo]` | `extractors/primitives/contracts.py` (AST-04) |

Phase 3 で `class_diagram` / `sequence_diagram` / `component_diagram` / `package_diagram` / `state_diagram` / `function_spec` / `class_spec` の各 evaluation field を optional で追加する (Open-Closed 拡張、`docs/09-extending.md` 参照)。

### Diagram primitives (lib-diagram-parser 互換)

`GraphNode` / `GraphEdge` / `GraphModel` / `GuardExpr` は `lib-diagram-parser>=0.1.0` から直接 import するか、または node_type 拡張のため subclass する (SCH-01)。

```python
EdgeKind = Literal[
    "inherits", "implements",
    "composes", "aggregates", "associates",
    "field_of", "param_of", "returns", "instantiates",
    "calls",
    "transitions_to",
]
```

**EdgeKind は closed Literal で 11 値固定** (SCH-03 / Pitfall 7)。`uses` / `other` / `misc` のような catch-all は採用しない — ambiguity は `associates` で明示的に表現する。新しい edge 種類は Phase 1 close 後は追加不可 (拡張点契約: dispatch dict は append-only だが、Literal 値の拡張は破壊的変更扱い)。

### `physical_*` / `source_*` prefix convention (SCH-02)

物理側 (code) のみで取得可能なメタデータは optional field に `physical_` または `source_` を prefix する:

| Field example | Lives in | Purpose |
|---------------|----------|---------|
| `physical_module: str \| None` | `GraphEdge` | 物理 module 名 (verifier が比較時に無視する) |
| `source_range: SourceRange \| None` | `GraphEdge`, `FunctionNode` | source の line range (debug / IDE 連携用) |

verifier (LLM agent) は prefix を見て「物理側のみのメタデータ」を判別し、論理側 (spec) との bisimulation 比較から除外する。

`Traces: SCH-01`
`Traces: SCH-02`
`Traces: SCH-03`

---

## §採用アルゴリズム

各 capability の実装アルゴリズム / 使用 tool は以下のとおり:

### (a) Python AST = stdlib `ast`

Python frontend は stdlib `ast` モジュールを使い、**1 ファイル 1 回だけ parse して CAV に詰める**。CAV は immutable Pydantic envelope (`frozen=True`、`arbitrary_types_allowed=True`、`extra="forbid"`) で payload に `ast.Module` を保持する。全 primitive extractor (functions / callgraph / type_deps / contracts) は CAV を引数で受け取り pull で消費する。v0.1.0 の「各 extractor が個別に `ast.parse` を呼ぶ」アンチパターンは解消される。

### (b) 内製 call graph extractor (AST 静的解析、GPL viral 回避)

Call graph は **本 lib 内の callgraph extractor module (`extractors/primitives/callgraph`) で内製** する。pyan3 (GPL v2)、PyCG (archived)、code2flow (非決定論) は **すべて不採用** — MIT/Apache の決定論的 call graph OSS が存在しないため、内製 extractor が唯一の選択肢である。内製により license が完全に Apache-2.0 で閉じ、決定論性と schema 完全制御を確保する。

- 旧 v0.1.0 spec doc の「外部 script 経由 call graph 生成」記述は **削除** (実在しない PyPI artifact への参照)
- 旧 v0.1.0 spec doc の「Common Lisp theorem prover 由来の決定論的ツール」記述は **削除** (theorem prover であり call graph tool ではない)
- v0.2.0 で `extractors/primitives/callgraph` module が `CallGraph` (nodes + caller→callee edges) を返す内製実装に置き換える (v0.1.0 の `callgraph_builder` module 拡張)

### (c) Python 型解決 = `pyright[nodejs]==1.1.409` subprocess (MIT license)

`pyright` は Microsoft 製の static type checker (MIT license)。`[nodejs]` extra で Node binary が bundle されるため、user 側に node install を要求しない。本 lib は `adapters/pyright.py` から subprocess invocation し、JSON output (`generalDiagnostics`) を pydantic で正規化して `TypeDep` を生成する (AST-03 / DET-03)。

### (d) C++ AST = `libclang==18.1.1` in-process ctypes

`libclang` は Apache-2.0 WITH LLVM-exception (SPDX: `Apache-2.0 WITH LLVM-exception`)。ctypes ベースの wheel が `py2.py3-none-platform` で配布されているため Python 3.13/3.14 でも pip install できる。Linux / Windows は **強保証** 対象、macOS arm64 + Python 3.13+ は SP-3 spike の結果次第で continue-on-error (LNG-02)。

- **厳密 pin (`==18.1.1`)** — ABI 整合性のため。caller が version override すると bisimulation が破壊される
- **runtime guard** — import 時に `cindex.Index.create()` を呼んで dylib load を検証 (LNG-03)
- **`Config.set_library_file` を禁止** — 別 path から異なる version の libclang を load されると DET-02 が破壊される (DET-02 assertion)
- **`Cursor` / `Type` を libclang module 境界の外に返さない** — lifetime crash (Pitfall 1) を避けるため、即座に Pydantic model に変換する

### (e) Python 契約抽出 = Pydantic v2 validator / dataclass `__post_init__` 区別

`extractors/primitives/contracts.py` は AST decorator inspection で以下を区別する (AST-04):

```python
ContractInfo.source_kind ∈ {
    "pydantic_validator",            # @validator (v1 style)
    "pydantic_field_validator",      # @field_validator (v2 style)
    "pydantic_model_validator",      # @model_validator (v2 style)
    "dataclass_post_init",           # @dataclass の __post_init__ method
}
```

v0.1.0 では unconditional に「Pydantic-style validator」として扱っていたが、v0.2.0 では discriminator 必須 (内部 logic が `__post_init__` を独立 source として扱う必要があるため)。

### (f) C++ 契約抽出 = Doxygen `\pre` / `\post` / `\invariant`

C++ では Python と対称に契約を抽出する (SPC-03)。Doxygen の標準 marker (`\pre`、`\post`、`\invariant`) を libclang の `Cursor.raw_comment` から regex で抜き、`ContractInfo` (`source_kind` 拡張で `doxygen_pre` / `doxygen_post` / `doxygen_invariant`) を生成する。Python と C++ の出力 schema は parity を保つ (verifier の処理を非対称にしないため)。

### (g) subprocess hardening (`adapters/base.py`、DET-05)

すべての subprocess invocation は `adapters/` 層に隔離する (ARC-03)。`extractors/` 層からは subprocess を直接呼ばない。`adapters/base.py` の `SubprocessAdapter` 抽象 base が以下を強制する:

```python
subprocess.run(
    cmd,
    capture_output=True,         # Pitfall 3 (deadlock 回避)
    encoding="utf-8",            # Pitfall 13 (Windows cp1252 回避)
    errors="replace",            # non-UTF-8 byte 混入時の robust 退化
    env={
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONHASHSEED": "0",
        "PYTHONIOENCODING": "utf-8",
    },
    timeout=60,                  # 明示 timeout
    cwd=<explicit>,              # `os.getcwd()` 継承を防ぐ
    shell=False,                 # injection 防止
)
```

これにより determinism (DET-05) と portability を保証する。adapter は subprocess 出力を sort / strip timestamps / normalize paths した上で Pydantic model に変換し、extractor には Pydantic model のみを返す。

### Open-Closed 契約 (拡張点)

`_dispatch.py` の 3 つの dispatch dict (`FRONTENDS` / `PRIMITIVES` / `EVALUATIONS`) は **append-only** とする (D-13)。executor は dict を走査して評価単位を実行 (`for name, fn in EVALUATIONS.items(): result[name] = fn(cav, config)`) するのみで、評価単位を追加しても executor 本体は変更されない。詳細な 6 不変条件は `docs/09-extending.md` を参照。

`Traces: ARC-03`
`Traces: ARC-04`
`Traces: DET-04`
`Traces: DET-05`

---

## §License

### 本 lib 自身

`lib-code-parser` は **Apache-2.0** で配布する (SPDX: `Apache-2.0`)。`LICENSE` ファイル (project root) に Apache License Version 2.0 (January 2004) のフルテキストを同梱し、その **Section 3 — Grant of Patent License** clause (寄与者からの特許グラント) も完全な形で含む。`pyproject.toml` は PEP 639 形式で `license = "Apache-2.0"` + `license-files = ["LICENSE"]` を宣言する (DOC-04、`setuptools>=77.0.3` 必須)。

### Bundled / required dependencies and their licenses

| Dependency | License | SPDX | Invocation pattern | Notes |
|------------|---------|------|--------------------|-------|
| Internal call graph extractor | Apache-2.0 (本 lib の一部) | `Apache-2.0` | In-process (本 lib 内のコード) | **No GPL viral**。pyan3 (GPL v2) は採用拒否、PyCG (archived) は採用拒否、code2flow (非決定論) は採用拒否。本 lib が唯一 deterministic で license clean な選択肢として内製を採用した |
| `pyright` | MIT | `MIT` | Subprocess (`adapters/pyright.py` 経由) | Microsoft が maintain する static type checker。`[nodejs]` extra で Node binary が bundle される (user 側に node install 不要)。`PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` で version pin |
| `libclang` (bundled via PyPI wheel) | Apache 2.0 with LLVM exception | `Apache-2.0 WITH LLVM-exception` | In-process ctypes (`cindex.Index.create()`) | LLVM exception により、コンパイラ produced artifacts の attribution requirement が免除される — これにより GPL v2 compatible になる。本 lib は libclang を ctypes 経由で in-process 呼び出しするのみで、コンパイラとして使うわけではない。`==18.1.1` 厳密 pin |
| `pydantic` | MIT | `MIT` | In-process (model 定義に使用) | v2.13.0 以降、v3.0 未満。runtime dependency |
| `lib-diagram-parser` | (兄弟 lib、Apache-2.0 想定) | (sibling lib に準拠) | In-process import (schema model のみ) | SCH-01 で schema 直接 import (model duplication 禁止)。Phase 3 で正式統合 |

### No GPL bundled の宣言

本 lib は **GPL ライセンスのツールを一切 bundle しない**。Call graph は **内製 (Apache-2.0)**、`pyright` は **MIT**、`libclang` は **Apache-2.0 WITH LLVM-exception** (GPL v2 compatible)。これは DOC-03 として明文化される宣言であり、Phase 5 で `README.md` にも同等の disclosure が反映される。`pyproject.toml` の license declaration と本 §License の記述は単一の source (本研究 §Apache-2.0 pyproject.toml) から派生する。

### LICENSE file の patent grant clause

`LICENSE` ファイルには Apache-2.0 の Section 3 Grant of Patent License clause が完全な形で含まれる:

> Subject to the terms and conditions of this License, each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable (except as stated in this section) patent license to make, have made, use, offer to sell, sell, import, and otherwise transfer the Work, ...

これにより contributor から user への patent rights が明示的に grant され、特許 troll に対する防御線を提供する。

`Traces: DOC-01`
`Traces: DOC-03`
`Traces: DOC-04`

---

## §Traceability

v1 で実装する 42 件の requirements を US-01 / US-22 / US-25 / US-32 にマップする。詳細な mapping table は `docs/99-trace-matrix.md` を参照 (Phase 1 終了時点では本 spec doc の §Traceability が source、Phase 2 以降は trace matrix が source)。

TRC-02 (per-module REQ-ID docstring declaration) と TRC-03 (Python と C++ で同一 regex の trace tag 抽出) は **Phase 2 で実装** する。本 phase (Phase 1) では下記サマリと、本ドキュメント内の `Traces: <REQ-ID>` 行による carrier-side 宣言のみを行う (TRC-01)。

### Phase 1 で完了する 14 件 (Architecture Foundation + Spec Correction)

| Category | REQ-IDs | US support |
|----------|---------|-----------|
| Architecture (ARC) | ARC-01, ARC-02, ARC-03, ARC-04, ARC-05 | US-01, US-22, US-25, US-32 |
| Schema (SCH) | SCH-01, SCH-02, SCH-03 | US-25, US-32 |
| Determinism (DET) | DET-04, DET-05 | US-01, US-22, US-25, US-32 |
| Documentation (DOC) | DOC-01, DOC-03, DOC-04 | US-01, US-22, US-25, US-32 |
| Traceability (TRC) | TRC-01 | US-01, US-22, US-25, US-32 |

### Phase 2-5 で完了する 28 件 (要約)

| Category | REQ count | Phase | US support |
|----------|-----------|-------|-----------|
| AST primitives (AST) | AST-01..05 (5 件) | Phase 2 | US-01, US-22 (一部 US-25, US-32) |
| Determinism (DET) | DET-03 | Phase 2 | US-01, US-22 |
| Traceability (TRC) | TRC-02, TRC-03 | Phase 2 | US-01, US-22, US-25, US-32 |
| Diagram extractors (DIA) | DIA-01..07 (7 件) | Phase 3 | US-25, US-32 |
| Spec extractors (SPC) | SPC-01, SPC-02, SPC-04 (3 件) | Phase 3 | US-01, US-22 |
| Spec extractors (SPC) | SPC-03 | Phase 4 | US-01, US-22 |
| Language support (LNG) | LNG-01..05 (5 件) | Phase 4 | US-01, US-22, US-25, US-32 |
| Determinism (DET) | DET-02 | Phase 4 | US-01, US-22, US-25, US-32 |
| Cross-cutting (DET / SCH / DOC) | DET-01, SCH-04, DOC-02 (3 件) | Phase 5 | All US |

合計 **42 / 42** が phase mapped、unmapped 0 件 (REQUIREMENTS.md §Traceability §Coverage に一致)。

### Phase 1 REQ-ID anchors (TRC-01 carrier)

下記は本 spec doc が Phase 1 で実装する 14 件の REQ を `Traces: <REQ-ID>` 形式で明示する anchor 行である。本 lib の trace tag regex (`Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)`) でそのまま抽出可能。

`Traces: ARC-01`
`Traces: ARC-02`
`Traces: ARC-03`
`Traces: ARC-04`
`Traces: ARC-05`
`Traces: SCH-01`
`Traces: SCH-02`
`Traces: SCH-03`
`Traces: DET-04`
`Traces: DET-05`
`Traces: DOC-01`
`Traces: DOC-03`
`Traces: DOC-04`
`Traces: TRC-01`

---

*Last updated: 2026-05-25 — Phase 1 Plan 01-02 full rewrite, replaces v0.1.0 spec doc (preserved at `frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md`).*
