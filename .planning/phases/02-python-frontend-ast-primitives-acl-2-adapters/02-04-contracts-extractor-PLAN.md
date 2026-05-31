---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 04
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/models/primitives/contracts.py
  - lib_code_parser/extractors/primitives/contracts.py
  - tests/unit/models/test_contracts_model.py
  - tests/unit/extractors/test_contracts_extractor.py
autonomous: true
requirements: [AST-04, AST-05, TRC-02, TRC-03]
must_haves:
  truths:
    - "Caller can write `from lib_code_parser.extractors.primitives.contracts import extract; extract(cav, config)` and gets dict[str, ContractInfo] where each ContractInfo carries per-entry source_kind discriminator (D-12 β)"
    - "ContractInfo model is restructured: new ContractEntry sub-model carries (name, source_kind, kind, decorator_name, line_no) per validator; ContractInfo.entries: list[ContractEntry] is the canonical storage; backward-compat helper properties preconditions / invariants / postconditions return list[str] derived from entries for executor consumption"
    - "Pydantic decorator detection covers all 4 mapping cases per D-11: @validator → pydantic_validator, @field_validator → pydantic_field_validator, @model_validator → pydantic_model_validator, @root_validator → pydantic_model_validator (semantic equivalent, v0.1.0 bug C4 fix)"
    - "Alias import detection works: `from pydantic import field_validator as fv; @fv(...)` resolves to source_kind=pydantic_field_validator (v0.1.0 bug C3 fix; RESEARCH §3.1 C3)"
    - "`__post_init__` is detected by method-name only (no @dataclass class-level check) and tagged source_kind=dataclass_post_init (Pitfall 5 + D-11 simplicity; verifier no longer sees `__post_init__` as unconditional Pydantic concept — ROADMAP Phase 2 SC-3 satisfied)"
    - "Mixed case: same class containing @field_validator + __post_init__ produces ContractInfo with 2 entries differing in source_kind (D-13 自動サポート via D-12 β granularity)"
    - "Module docstring contains 'Implements: AST-04, AST-05' and 'Traces: AST-04, AST-05, US-01, US-22'"
  artifacts:
    - path: "lib_code_parser/models/primitives/contracts.py"
      provides: "Restructured ContractInfo model: ContractEntry sub-model + entries list + backward-compat helper properties"
      contains: "class ContractEntry|class ContractInfo|entries"
    - path: "lib_code_parser/extractors/primitives/contracts.py"
      provides: "Pure-CAV contract extractor (AST-04) with alias resolution + @root_validator support + per-entry source_kind"
      contains: "def extract"
    - path: "tests/unit/models/test_contracts_model.py"
      provides: "ContractInfo/ContractEntry shape + backward-compat helper assertions"
      contains: "def test_contract_entry|def test_contract_info"
    - path: "tests/unit/extractors/test_contracts_extractor.py"
      provides: "Decorator detection unit covering D-11 mapping all 4 cases + alias + mixed + post_init"
      contains: "def test_extract"
  key_links:
    - from: "extractors/primitives/contracts.py::extract"
      to: "_DECORATOR_TO_SOURCE_KIND mapping"
      via: "canonical-name lookup after alias resolution"
      pattern: "_DECORATOR_TO_SOURCE_KIND"
    - from: "extractors/primitives/contracts.py::_resolve_decorator_aliases"
      to: "ast.ImportFrom walk"
      via: "from pydantic import X [as Y] → {Y: X}"
      pattern: "ImportFrom"
---

<objective>
Wave 1 並列の 4 件目。 v0.1.0 `lib_code_parser/contract_extractor.py` の decorator 認識ロジックを拡張・修正して `lib_code_parser/extractors/primitives/contracts.py` に新規実装する。 同時に Phase 1 で生成された `models/primitives/contracts.py` の `ContractInfo` model を D-12 (β) + D-14 を満たす形に restructure する (RESEARCH §3.4 Case A 採用 — `ContractEntry` 新規 + `ContractInfo.entries: list[ContractEntry]` + backward-compat helper `@computed_field` で `preconditions` / `invariants` / `postconditions` を `list[str]` として返す)。

v0.1.0 が持っていた **2 件の実証バグ** (RESEARCH §3.1 C3 / C4) を Phase 2 で修正する:
- **C3 alias 未解決**: `from pydantic import field_validator as fv; @fv(...)` を検出できなかった → Plan 02-04 で `_resolve_decorator_aliases()` を追加し、 ImportFrom AST walk で `pydantic` 由来の alias map を構築、 `_get_decorator_canonical_name()` で alias 解決後に source_kind マッピングを引く
- **C4 `@root_validator` 未認識**: `_PRECONDITION_DECORATORS` / `_INVARIANT_DECORATORS` に未登録だった → Plan 02-04 で `_DECORATOR_TO_SOURCE_KIND` 辞書 (4 値マッピング) に `root_validator` → `pydantic_model_validator` を含める (D-11 semantic equivalent)

`__post_init__` 検出は v0.1.0 と同じく method 名のみで判定 (RESEARCH Pitfall 5 + Assumption A4 — class-level `@dataclass` 文脈を見ない、 D-11 simplicity 優先)、 しかし source_kind は **unconditional Pydantic でなく `dataclass_post_init`** に分離する (AST-04 / ROADMAP SC-3)。

Purpose: ROADMAP Phase 2 success criterion 3 (`source_kind ∈ {pydantic_validator, pydantic_model_validator, pydantic_field_validator, dataclass_post_init}` per validator entry) と SC-4 の contracts extractor isolated 性を成立。 同時に PROJECT.md Core Value (物理側 = 事実の最大忠実度抽出、 verifier 側 = 物理↔論理ギャップの解釈) を contracts レベルで実現する。

Output:
- `lib_code_parser/models/primitives/contracts.py` — Phase 1 model の **breaking restructure** (D-01 clean break が許容)、 `ContractEntry` 新規 + `entries: list[ContractEntry]` + 3 helper computed_field
- `lib_code_parser/extractors/primitives/contracts.py` — 新規 1 ファイル、 `extract(cav, config) -> dict[str, ContractInfo]` + alias resolution + 4-値 mapping
- `tests/unit/models/test_contracts_model.py` — ContractEntry shape + ContractInfo.entries + helper properties unit
- `tests/unit/extractors/test_contracts_extractor.py` — RESEARCH §3.1 C1-C7 7 edge case + 混在 case + isolated 性
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/PROJECT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/REQUIREMENTS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/ROADMAP.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/contract_extractor.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_paths.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/contracts.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/functions.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/cav.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/config.py

<interfaces>
<!-- Phase 1 ContractInfo (BEFORE Plan 02-04 restructure):

class ContractInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node_id: str = ""
    source_kind: Literal[
        "pydantic_validator", "pydantic_model_validator",
        "pydantic_field_validator", "dataclass_post_init",
    ] = "pydantic_validator"
    preconditions: list[str] = []
    invariants: list[str] = []
    postconditions: list[str] = []

This is the v0.1.0 "α" shape (single source_kind per class). Plan 02-04 restructures
to D-12 (β) "per-entry source_kind" via RESEARCH §3.4 Case A.

NOTE on dependent code: FunctionNode (models/primitives/functions.py) has
`contracts: ContractInfo = Field(default_factory=...)`. The default factory
constructs an empty ContractInfo, so the restructure MUST keep ContractInfo()
no-args constructable.

Plan 02-04 AFTER:

class ContractEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str                                   # method name
    source_kind: Literal["pydantic_validator", "pydantic_model_validator",
                         "pydantic_field_validator", "dataclass_post_init"]
    kind: Literal["precondition", "invariant", "postcondition"]
    decorator_name: str = ""                    # canonical name (after alias)
    line_no: int = 0

class ContractInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node_id: str = ""
    entries: list[ContractEntry] = []

    @computed_field
    @property
    def preconditions(self) -> list[str]:
        return [e.name for e in self.entries if e.kind == "precondition"]

    @computed_field
    @property
    def invariants(self) -> list[str]:
        return [e.name for e in self.entries if e.kind == "invariant"]

    @computed_field
    @property
    def postconditions(self) -> list[str]:
        return [e.name for e in self.entries if e.kind == "postcondition"]
-->

<!-- v0.1.0 contract_extractor.py 解像度 (RESEARCH §3.1 で実機検証済 7 件):
- C1 `@validator("x")` simple Name → 検出
- C2 `@pydantic.field_validator("x")` Attribute → 検出 (decorator.attr で field_validator 抽出)
- C3 alias `@fv("x")` with `from pydantic import field_validator as fv` → ✗ 未検出 (v0.1.0 バグ)
- C4 `@root_validator` → ✗ 未認識 (v0.1.0 バグ、 mapping 表にない)
- C5 decorator chain `@field_validator @classmethod` → 検出 (first match で break)
- C6 factory `@validator("x", pre=True)` Call → 検出
- C7 plain class `__post_init__` → 検出するが unconditional Pydantic 扱い (Phase 2 で source_kind=dataclass_post_init に分離)
-->
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Restructure ContractInfo model — add ContractEntry + entries list + backward-compat helper computed_field</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/contracts.py (Phase 1 locked α 形 — 全面置換対象)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/functions.py (FunctionNode.contracts default_factory が ContractInfo() を呼ぶため、 ContractInfo() 引数なし構築の互換性維持が必要)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§3.4 Case A / B / C 比較 — Plan 02-04 は Case A 採用 + Case C 様の computed_field helper を併設)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md (D-12 / D-14 — per-entry source_kind、 既存 model 拡張、 extra="forbid" + required field 維持)
  </read_first>
  <behavior>
    - `ContractInfo()` (引数なし) 構築が成功し、 `entries == []`、 `preconditions == []` / `invariants == []` / `postconditions == []` を返す (FunctionNode.contracts default 互換)
    - `ContractEntry(name="validate_status", source_kind="pydantic_field_validator", kind="precondition")` が成功
    - `ContractEntry(name="x", source_kind="invalid_kind", kind="precondition")` が `ValidationError` を raise (Literal 4 値の closure 維持)
    - `ContractEntry(name="x", source_kind="pydantic_field_validator", kind="unknown")` が `ValidationError` を raise (kind Literal closure)
    - `ContractEntry(extra_field="boom", name="x", source_kind="pydantic_field_validator", kind="precondition")` が `ValidationError` (SCH-02 extra="forbid")
    - `ContractInfo(entries=[ContractEntry(name="validate_status", source_kind="pydantic_field_validator", kind="precondition"), ContractEntry(name="__post_init__", source_kind="dataclass_post_init", kind="precondition")])` の `.preconditions == ["validate_status", "__post_init__"]` (helper property が `kind == "precondition"` の entry を抽出)
    - 同 instance の `.invariants == []`、 `.postconditions == []`
    - `ContractInfo.model_dump_json()` が `entries` を含む JSON を返し、 byte-identical な再構築が可能
    - **computed_field の出力含有性**: Pydantic v2 で `@computed_field` は `model_dump()` / `model_dump_json()` の出力に **含まれる** がdefault。 後方互換性のため、 caller が `ci.model_dump_json()` を見たときに preconditions/invariants/postconditions が key として現れる (executor が `fn.contracts = ci` 後に JSON 出力する際の予測可能性確保) — この挙動は Pydantic v2.13 で標準
    - 既存 Phase 1 `tests/unit/models/test_contracts.py` (Plan 01-04 で確立、 ContractInfo の 4 値 source_kind Literal + extra="forbid" + default 構築の unit) は **breaking 互換性破壊が発生** することを認める (D-01 clean break、 D-12 model restructure 不可避)。 当該既存 unit は本 Task で書き換え or 削除し、 新 unit (`tests/unit/models/test_contracts_model.py`) で置き換える
  </behavior>
  <action>
    Step 1 — `lib_code_parser/models/primitives/contracts.py` の **既存 ContractInfo class を全面置換**。 module docstring と SCH-02 `extra="forbid"` 規約は維持。 RESEARCH §3.4 Case A の skeleton を実装する:

    ```
    """Primitive contract models — ContractEntry + ContractInfo with per-entry source_kind discriminator.

    Per Phase 2 D-12 (β): each ContractInfo carries a list of ContractEntry, and
    each entry has its own source_kind ∈ {pydantic_validator, pydantic_field_validator,
    pydantic_model_validator, dataclass_post_init} per AST-04. This per-entry granularity
    lets verifiers see exactly which validator decorator was used on each method, without
    re-expanding a class-level discriminator (preserves PROJECT.md Core Value: physical-
    side emits the maximum-fidelity facts; the verifier alone interprets the physical↔
    logical gap).

    Phase 2 restructure (D-14): the v0.1.0/Phase-1 class-level discriminator
    (single source_kind + 3 list[str] for preconditions/invariants/postconditions) is
    breaking-replaced by ContractEntry list. Backward-compat is provided via Pydantic v2
    @computed_field helpers (preconditions / invariants / postconditions) so existing
    callers reading `ci.preconditions` continue to get list[str].

    Traces: SCH-02, AST-04, D-12, D-14.
    """

    from __future__ import annotations

    from typing import Literal

    from pydantic import BaseModel, ConfigDict, Field, computed_field


    SourceKind = Literal[
        "pydantic_validator",
        "pydantic_model_validator",
        "pydantic_field_validator",
        "dataclass_post_init",
    ]


    ContractKind = Literal["precondition", "invariant", "postcondition"]


    class ContractEntry(BaseModel):
        """One contract statement (decorator or __post_init__) on a class member.

        - name: method name (e.g. "validate_status", "__post_init__")
        - source_kind: D-11 mapping result after alias resolution
        - kind: precondition / invariant / postcondition bucket (D-12)
        - decorator_name: canonical pydantic decorator name after alias resolution
          (e.g. "field_validator" even if the source said "@fv"); empty for __post_init__
        - line_no: source line of the decorator (1-based)
        """

        model_config = ConfigDict(extra="forbid")

        name: str
        source_kind: SourceKind
        kind: ContractKind
        decorator_name: str = ""
        line_no: int = 0


    class ContractInfo(BaseModel):
        """Per-class contract aggregate with per-entry source_kind discriminator (D-12 β).

        Backward-compat: the v0.1.0 caller pattern ``ci.preconditions / ci.invariants /
        ci.postconditions`` (list[str] of method names) is preserved via @computed_field
        helpers derived from ``entries``. New callers should read ``entries`` directly.
        """

        model_config = ConfigDict(extra="forbid")

        node_id: str = ""
        entries: list[ContractEntry] = Field(default_factory=list)

        @computed_field
        @property
        def preconditions(self) -> list[str]:
            return [e.name for e in self.entries if e.kind == "precondition"]

        @computed_field
        @property
        def invariants(self) -> list[str]:
            return [e.name for e in self.entries if e.kind == "invariant"]

        @computed_field
        @property
        def postconditions(self) -> list[str]:
            return [e.name for e in self.entries if e.kind == "postcondition"]
    ```

    Step 2 — `tests/unit/models/test_contracts_model.py` を新規作成し、 上記 `<behavior>` 7 件の Pydantic shape 検証 + helper property 検証を実装する。 既存 Phase 1 `tests/unit/models/test_contracts.py` (Plan 01-04 の旧 α 形 assertion) は本 Task で **削除** (`git rm`) し、 新 unit `test_contracts_model.py` に置換する (D-01 clean break、 旧 model 形に依存する unit は parity を維持しない)。 削除と同時に新 unit の追加で test 件数バランスを保つ。

    Step 3 — `models/primitives/functions.py` の `FunctionNode.contracts` default factory が引き続き動くことを動的検証する: `FunctionNode(node_id="x", kind="function", source_range=SourceRange(start_line=0, end_line=0))` が成功し、 `.contracts == ContractInfo(entries=[])` であることを Task 2 unit でも assert する (実装 logic 変更なし、 ContractInfo() 引数なし構築の互換性が default factory を救う)。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/models/test_contracts_model.py tests/unit/models/test_functions.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/models/test_contracts_model.py -x -q` exit 0 with 7 件以上 pass
    - `python -c "from lib_code_parser.models.primitives.contracts import ContractEntry, ContractInfo, SourceKind, ContractKind; ci = ContractInfo(); assert ci.entries == [] and ci.preconditions == [] and ci.invariants == [] and ci.postconditions == []"` exit 0
    - `python -c "from lib_code_parser.models.primitives.functions import FunctionNode; from lib_code_parser.models.primitives.contracts import ContractInfo; from lib_code_parser.models.primitives.functions import SourceRange; fn = FunctionNode(node_id='x', kind='function', source_range=SourceRange(start_line=0, end_line=0)); assert isinstance(fn.contracts, ContractInfo)"` exit 0 (FunctionNode default factory 互換)
    - 旧 unit `tests/unit/models/test_contracts.py` が `git rm` 済 (削除済) であること; `[ ! -f tests/unit/models/test_contracts.py ]` で確認
    - Phase 1 model 構造の grep 検出 (旧 `preconditions: list[str] = Field(default_factory=list)` フィールド宣言が消えていること): `grep -c "preconditions: list\[str\] = Field" lib_code_parser/models/primitives/contracts.py` が 0
    - 新 model 構造の grep 検出: `grep -c "class ContractEntry" lib_code_parser/models/primitives/contracts.py` が 1、 `grep -c "entries: list\[ContractEntry\]" lib_code_parser/models/primitives/contracts.py` が 1、 `grep -c "@computed_field" lib_code_parser/models/primitives/contracts.py` >= 3
    - `ruff check lib_code_parser/models/primitives/contracts.py tests/unit/models/test_contracts_model.py` exit 0
    - Phase 1 baseline parity の互換性確認: `pytest tests/parity/ tests/acceptance/ -x -q` の結果が以下の挙動を満たす:
      - `tests/acceptance/test_fr04_contracts.py` は **失敗する可能性が高い** (v0.1.0 model 形に依存しているため)。 これは想定内であり、 Plan 02-07 (Wave 3 closer) で書き換えられる。 本 plan の acceptance では `tests/acceptance/test_fr04_contracts.py` 単体の失敗を許容するが、 それ以外の acceptance + parity test (FR-01/02/03/05/06 + Phase 1 parity 11 件) は依然として pass しなければならない。 本 acceptance では `pytest tests/acceptance/test_fr01_function_extraction.py tests/acceptance/test_fr02_callgraph.py tests/acceptance/test_fr03_type_deps.py tests/acceptance/test_fr05_trace_tags.py tests/acceptance/test_fr06_disabled.py tests/parity/ -x -q` exit 0 を assertion する (test_fr04_contracts.py を意図的に除外)
  </acceptance_criteria>
  <done>ContractInfo model が D-12 (β) restructure 完了。 ContractEntry list + 3 helper computed_field。 FunctionNode default factory 互換性維持。 Phase 1 acceptance test_fr04_contracts.py は失敗するが、 これは Plan 02-07 の書き換え担当範囲 (D-04) であり想定内。</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement extractors/primitives/contracts.py with alias resolution + 4-値 mapping + per-entry source_kind</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/contract_extractor.py (v0.1.0 reference — `_get_decorator_name` ロジックを base、 alias 解決と `@root_validator` を追加)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§3.2 推奨 detection algorithm + §3.3 D-11 mapping 表確認 + §Pitfall 5 `__post_init__` の `@dataclass` 文脈を見ない決定)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md (D-11 mapping 4 値、 D-12 β 集約粒度、 D-13 混在 case 自動サポート)
  </read_first>
  <behavior>
    - `from lib_code_parser.extractors.primitives.contracts import extract` 成功 (isolated import)
    - `extract(cav, config) -> dict[str, ContractInfo]` 返り値 (v0.1.0 と同 signature shape、 戻り値型のみ D-14 で entries 構造に変更)
    - dict key = class node_id (`{module_name}.{class_name}`)、 dict value = ContractInfo
    - **C1 `@validator("x")`** : entries に `ContractEntry(name=method, source_kind="pydantic_validator", kind="precondition", decorator_name="validator")` 1 件
    - **C2 `@pydantic.field_validator("x")`** : entries に `source_kind="pydantic_field_validator", decorator_name="field_validator"` 1 件
    - **C3 alias `@fv("x")` with `from pydantic import field_validator as fv`** (v0.1.0 バグ修正): entries に `source_kind="pydantic_field_validator", decorator_name="field_validator"` 1 件
    - **C4 `@root_validator`** (v0.1.0 バグ修正): entries に `source_kind="pydantic_model_validator", decorator_name="root_validator", kind="invariant"` 1 件 (D-11 mapping、 invariant に格納するのは v0.1.0 logic の `_INVARIANT_DECORATORS` 拡張形)
    - **C5 decorator chain `@field_validator @classmethod`**: entries に 1 件 (first match で break、 v0.1.0 parity)
    - **C6 factory `@validator("x", pre=True)`**: entries に 1 件 (Call form 検出)
    - **C7 `__post_init__`**: entries に `ContractEntry(name="__post_init__", source_kind="dataclass_post_init", kind="precondition", decorator_name="")` 1 件
    - **混在 case (D-13)**: `class Mixed:` 内に `@field_validator + __post_init__` 同居 → 同 `ContractInfo.entries` に 2 件 (source_kind が `pydantic_field_validator` と `dataclass_post_init` で異なる)
    - non-Pydantic alias (`from other_lib import field_validator`) は **検出しない**: alias map 構築時に `from pydantic` か `from pydantic.X` のみを scope に入れる
    - module docstring: `Implements: AST-04, AST-05` + `Traces: AST-04, AST-05, US-01, US-22`
    - `ast.parse` 呼び出しなし、 `_get_module_name` ローカル定義なし
  </behavior>
  <action>
    `lib_code_parser/extractors/primitives/contracts.py` を新規作成。 RESEARCH §3.2 推奨 detection algorithm を template に実装する。

    Module docstring:
    ```
    """Python contract extractor (Pydantic validators + dataclass __post_init__).

    Walks the CAV's ast.Module payload once and emits ContractInfo entries with
    per-entry source_kind discriminator (D-12 β):

    - @validator / @field_validator / @model_validator / @root_validator on a
      class member → ContractEntry with the canonical decorator name (after
      alias resolution) mapped to source_kind via _DECORATOR_TO_SOURCE_KIND
    - __post_init__ method (regardless of class-level @dataclass) → ContractEntry
      with source_kind=dataclass_post_init; the verifier no longer sees
      __post_init__ as an unconditional Pydantic concept (AST-04 / SC-3)

    Phase 2 fixes two v0.1.0 bugs documented in RESEARCH §3.1:
    - C3: aliased imports like `from pydantic import field_validator as fv`
          and `@fv(...)` are now resolved via _resolve_decorator_aliases()
    - C4: @root_validator is now recognized and mapped to
          pydantic_model_validator (semantic equivalent per D-11)

    Implements: AST-04, AST-05
    Traces: AST-04, AST-05, US-01, US-22
    """
    ```

    Imports:
    ```
    from __future__ import annotations

    import ast

    from lib_code_parser._paths import get_module_name
    from lib_code_parser.models.infrastructure.cav import CAV
    from lib_code_parser.models.infrastructure.config import ParserConfig
    from lib_code_parser.models.primitives.contracts import (
        ContractEntry,
        ContractInfo,
        ContractKind,
        SourceKind,
    )

    __all__ = ["extract"]
    ```

    Mapping 表 (D-11 4 値):
    ```
    # D-11 mapping: canonical pydantic decorator name → (source_kind, contract kind)
    # - validator / field_validator → precondition (v0.1.0 _PRECONDITION_DECORATORS の意味継承)
    # - model_validator / root_validator → invariant (v0.1.0 _INVARIANT_DECORATORS 意味継承)
    # - root_validator (v1 deprecated) is semantically equivalent to model_validator (v2)
    #   per Pydantic v1→v2 migration guide; collapse to pydantic_model_validator
    _DECORATOR_TO_SOURCE_KIND: dict[str, tuple[SourceKind, ContractKind]] = {
        "validator": ("pydantic_validator", "precondition"),
        "field_validator": ("pydantic_field_validator", "precondition"),
        "model_validator": ("pydantic_model_validator", "invariant"),
        "root_validator": ("pydantic_model_validator", "invariant"),
    }
    ```

    Helpers — v0.1.0 `_get_decorator_name` を base + RESEARCH §3.2 alias resolver を追加:

    ```
    def _get_decorator_raw_name(decorator: ast.expr) -> str:
        """Extract the local (possibly-aliased) name from a decorator expression.

        Same semantics as v0.1.0 _get_decorator_name; supports Name / Call(Name) /
        Call(Attribute) / Attribute forms. Returns '' for unsupported forms.
        """
        if isinstance(decorator, ast.Name):
            return decorator.id
        if isinstance(decorator, ast.Call):
            func = decorator.func
            if isinstance(func, ast.Name):
                return func.id
            if isinstance(func, ast.Attribute):
                return func.attr
        if isinstance(decorator, ast.Attribute):
            return decorator.attr
        return ""


    def _resolve_decorator_aliases(module: ast.Module) -> dict[str, str]:
        """Build {local_alias_name: canonical_pydantic_name} from `from pydantic import ...` statements.

        Examples:
            from pydantic import field_validator                → {"field_validator": "field_validator"}
            from pydantic import field_validator as fv          → {"fv": "field_validator"}
            from pydantic.deprecated.class_validators import validator → {"validator": "validator"}
            import pydantic                                     → {} (attribute form handled elsewhere)

        Only `from pydantic[.X] import ...` is in scope. Other libraries' identifiers
        with the same name (e.g. `from other_lib import field_validator`) are excluded
        from the alias map so they are not falsely classified as pydantic contracts.
        """
        aliases: dict[str, str] = {}
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == "pydantic" or mod.startswith("pydantic."):
                    for alias in node.names:
                        local = alias.asname or alias.name
                        aliases[local] = alias.name
        return aliases


    def _classify_decorator(
        decorator: ast.expr, aliases: dict[str, str]
    ) -> tuple[SourceKind, ContractKind, str] | None:
        """Return (source_kind, contract_kind, canonical_name) or None if not a contract decorator."""
        raw = _get_decorator_raw_name(decorator)
        canonical = aliases.get(raw, raw)
        info = _DECORATOR_TO_SOURCE_KIND.get(canonical)
        if info is None:
            return None
        source_kind, contract_kind = info
        return source_kind, contract_kind, canonical
    ```

    Main extractor:
    ```
    def extract(cav: CAV, config: ParserConfig) -> dict[str, ContractInfo]:
        """AST-04: emit per-class ContractInfo dict from cav.payload (ast.Module).

        config is accepted for signature alignment but not consumed; extraction
        does not depend on per-config flags (the executor in Plan 02-06 applies
        config.extract_contracts to decide whether to invoke this extractor at all).
        """
        tree = cav.payload  # type: ignore[assignment]
        assert isinstance(tree, ast.Module), (
            f"contracts extractor requires Python CAV (ast.Module payload), "
            f"got {type(tree).__name__}"
        )
        module_name = get_module_name(cav.path)
        aliases = _resolve_decorator_aliases(tree)

        result: dict[str, ContractInfo] = {}
        for class_node in tree.body:
            if not isinstance(class_node, ast.ClassDef):
                continue
            class_id = f"{module_name}.{class_node.name}"
            entries: list[ContractEntry] = []

            for item in class_node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                # __post_init__ — method-name-only detection (Pitfall 5 + D-11 simplicity)
                if item.name == "__post_init__":
                    entries.append(
                        ContractEntry(
                            name="__post_init__",
                            source_kind="dataclass_post_init",
                            kind="precondition",
                            decorator_name="",
                            line_no=item.lineno,
                        )
                    )
                    continue

                # Decorator scan — first match wins (v0.1.0 parity)
                for decorator in item.decorator_list:
                    classified = _classify_decorator(decorator, aliases)
                    if classified is None:
                        continue
                    source_kind, contract_kind, canonical = classified
                    entries.append(
                        ContractEntry(
                            name=item.name,
                            source_kind=source_kind,
                            kind=contract_kind,
                            decorator_name=canonical,
                            line_no=item.lineno,
                        )
                    )
                    break

            if entries:
                result[class_id] = ContractInfo(node_id=class_id, entries=entries)

        return result
    ```

    Wave 0 unit test `tests/unit/extractors/test_contracts_extractor.py` を新規作成。 上記 `<behavior>` の C1-C7 + 混在 case + isolated import = 約 10 件の test を実装する。 fixture は Plan 02-02 / 02-03 と同じ `_build_cav(source, path)` helper を使う。 test 内で `ast.parse` を直接呼ばない。

    Test 一覧:
    1. `test_c1_simple_validator` — `@validator("x")` で source_kind=pydantic_validator
    2. `test_c2_attribute_field_validator` — `@pydantic.field_validator("x")` で pydantic_field_validator
    3. `test_c3_alias_resolution_fixes_v01_bug` — `from pydantic import field_validator as fv; @fv("x")` を pydantic_field_validator として検出 (canonical_name="field_validator")
    4. `test_c4_root_validator_recognized` — `@root_validator` を pydantic_model_validator として検出 (canonical_name="root_validator")
    5. `test_c5_decorator_chain_first_match` — `@field_validator + @classmethod` で 1 entry のみ (first match で break)
    6. `test_c6_factory_call_form` — `@validator("x", pre=True)` で 1 entry
    7. `test_c7_post_init_in_plain_class_gets_dataclass_post_init` — `class PlainClass: def __post_init__(self): pass` で source_kind=dataclass_post_init (unconditional Pydantic でないことを assert — ROADMAP SC-3 invariant)
    8. `test_mixed_validator_and_post_init` (D-13) — 同 class 内に `@field_validator` + `__post_init__` 同居 → entries 2 件で source_kind 別
    9. `test_non_pydantic_alias_not_classified` — `from other_lib import field_validator; @field_validator` は検出しない (alias map scope 制限)
    10. `test_isolated_import_no_executor` — `CodeParserExecutor` 一切 import せず `extract(cav, config)` 直接呼び出し (SC-4)
    11. `test_extract_on_example_source_returns_order_model_contracts` — conftest EXAMPLE_SOURCE で `order_service.OrderModel` の entries に validate_status (precondition) + check_total (invariant) が含まれる (v0.1.0 acceptance test_fr04 semantic parity の core 部分のみ)
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/extractors/test_contracts_extractor.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/extractors/test_contracts_extractor.py -x -q` exit 0 with 11 件 pass
    - `grep -c "ast\.parse" lib_code_parser/extractors/primitives/contracts.py` が 0
    - `grep -c "^def _get_module_name\|^def get_module_name" lib_code_parser/extractors/primitives/contracts.py` が 0
    - `grep -c "from lib_code_parser\._paths import get_module_name" lib_code_parser/extractors/primitives/contracts.py` が 1
    - `grep -c "_DECORATOR_TO_SOURCE_KIND" lib_code_parser/extractors/primitives/contracts.py` >= 2 (定義 + lookup)
    - `grep -c "root_validator" lib_code_parser/extractors/primitives/contracts.py` >= 1 (C4 fix の grep 証跡)
    - `grep -c "_resolve_decorator_aliases" lib_code_parser/extractors/primitives/contracts.py` >= 2 (定義 + 呼び出し、 C3 fix の grep 証跡)
    - `grep -c "dataclass_post_init" lib_code_parser/extractors/primitives/contracts.py` >= 1 (C7 fix の grep 証跡)
    - `grep -c "Implements: AST-04" lib_code_parser/extractors/primitives/contracts.py` = 1
    - `grep -c "Traces: AST-04" lib_code_parser/extractors/primitives/contracts.py` >= 1
    - Plan 02-01 AST-05 parity: `pytest tests/parity/test_ast_05_one_parse.py -x -q` exit 0
    - Phase 1 baseline parity (excluding test_fr04_contracts.py which is intentionally breaking — Plan 02-07 rewrites it): `pytest tests/acceptance/test_fr01_function_extraction.py tests/acceptance/test_fr02_callgraph.py tests/acceptance/test_fr03_type_deps.py tests/acceptance/test_fr05_trace_tags.py tests/acceptance/test_fr06_disabled.py tests/parity/test_v01_v02_compat.py -x -q` exit 0
    - `ruff check lib_code_parser/extractors/primitives/contracts.py tests/unit/extractors/test_contracts_extractor.py` exit 0
  </acceptance_criteria>
  <done>contracts extractor が C3 / C4 v0.1.0 バグ修正 + 4 値 source_kind + per-entry 集約 + D-13 混在 case 自動サポート + dataclass_post_init 分離 を達成。 RESEARCH §3.1 7 fixture と D-13 全パターンが unit でロック。</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| CAV.payload (ast.Module) → ContractInfo emit | payload 形状は Frontend 保証、 isolated call 時は assert で fail loudly |
| alias map (caller-provided source) → decorator classifier | alias map scope を `from pydantic[.X]` に限定して non-pydantic 同名 decorator の誤分類を防ぐ |
| ContractInfo restructure → FunctionNode.contracts default factory | restructure 後も ContractInfo() 引数なし構築が成功することを Pydantic 仕様 + acceptance unit で保証 |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-16 | Tampering | Plan 02-04 model restructure が FunctionNode.contracts default factory を壊す | mitigate | Task 1 acceptance に `FunctionNode(...).contracts == ContractInfo()` 動的検証 |
| T-02-17 | Tampering | AST-05 違反 | mitigate | Task 2 acceptance grep gate + Plan 02-01 parity test |
| T-02-18 | Tampering | ARC-04 違反 (`_get_module_name` ローカル定義) | mitigate | Task 2 acceptance grep gate |
| T-02-19 | Information disclosure | non-pydantic alias の誤分類 (false positive) で関数名が物理アーキ出力に混入 | mitigate | Task 2 で `from pydantic[.X]` 制限 + unit test `test_non_pydantic_alias_not_classified` で fixture 検証 |
| T-02-20 | Tampering | `__post_init__` を Pydantic 扱いし続ける (ROADMAP SC-3 違反) | mitigate | Task 2 で C7 case を `dataclass_post_init` に分離する logic + unit `test_c7_post_init_in_plain_class_gets_dataclass_post_init` で assert |
| T-02-21 | Supply chain | 新規依存なし | accept | stdlib `ast`、 pydantic は Phase 1 declared |
</threat_model>

<verification>
- `pytest tests/unit/models/test_contracts_model.py tests/unit/extractors/test_contracts_extractor.py tests/unit/models/test_functions.py -x -q` exit 0 (約 20 件 pass)
- AST-05 grep gate (Plan 02-01 parity): 0 件 in `lib_code_parser/extractors/`
- ARC-04 no-duplication grep gate: 1 件 (`_paths.py`)
- D-11 4 値 mapping 完全性 grep: validator / field_validator / model_validator / root_validator が全部 mapping 表に存在
- D-12 (β) 構造 grep: `ContractInfo.entries` フィールドあり、 `preconditions: list[str]` field 宣言なし (computed_field のみ)
- Phase 1 baseline (test_fr04_contracts.py を除く 5 acceptance + 11 parity) 維持
- `ruff check lib_code_parser/ tests/unit/` exit 0
</verification>

<success_criteria>
- ROADMAP Phase 2 success criterion 3 (source_kind 4 値 per validator entry) 成立
- ROADMAP Phase 2 success criterion 4 (contracts extractor isolated 性) 成立
- v0.1.0 C3 / C4 2 件のバグが unit でロック修正
- D-13 混在 case (Pydantic + __post_init__ 同居) が D-12 β 集約粒度で自動サポート
- TRC-02 / TRC-03 docstring 規約が contracts.py で確立
</success_criteria>

<output>
Create `.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-04-SUMMARY.md` when done. Include:
1. pytest output (Plan 02-04 contribution + which acceptance tests fail intentionally — test_fr04_contracts.py only)
2. ContractInfo restructure diff (Case A — entries + computed_field helpers; v0.1.0 α 形 field 削除)
3. v0.1.0 C3 / C4 bug fix evidence (unit test names + assertion outputs)
4. AST-05 / ARC-04 / TRC-02 / TRC-03 grep gate results
5. FunctionNode.contracts default factory 互換性確認
</output>
