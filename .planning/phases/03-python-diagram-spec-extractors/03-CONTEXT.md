# Phase 3: Python Diagram + Spec Extractors - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 で確立した CAV (Common AST View) + aspect models (FunctionNode / CallGraph /
TypeDep / ContractInfo) の上に、**評価単位 extractor (5 diagrams + 2 specs)** を実装する phase。
Phase 1 で固定した `models/evaluations/graph_base.py` (GraphNode / GraphEdge / GraphModel /
GuardExpr / 閉じた EdgeKind) と Open-Closed 6 不変条件を消費し、以下を実装する:

- **`extractors/evaluations/class_diagram.py`** (DIA-01) — class 定義 + 継承 +
  composition/aggregation/association edges。composition vs aggregation は型注釈由来規則
  (ROADMAP SC1 で確定)、不明時 `association` フォールバック
- **`extractors/evaluations/sequence_diagram.py`** (DIA-02) — call graph 由来の linear
  sequence (must-have)。branch fidelity (alt/loop/par) は SP-2 spike 依存
- **`extractors/evaluations/component_diagram.py`** (DIA-03) — file/module 境界 +
  import 由来依存エッジ
- **`extractors/evaluations/package_diagram.py`** (DIA-04) — directory/namespace 階層、
  `node_type="package"`、複数 package 表現
- **`extractors/evaluations/state_diagram.py`** (DIA-05/06) — FSM 明示パターン
  (`transitions.Machine` / `python-statemachine.StateMachine` / native Enum + transition
  method) + return-value substitution 解析 (intra-class N 階層再帰・cycle detection・
  `unresolved=true` placeholder)。コア挙動は ROADMAP SC3/SC4 で確定
- **`extractors/evaluations/function_spec.py`** (SPC-01) — signature + structured docstring
  (Google / NumPy / Sphinx Napoleon) + pre/post conditions
- **`extractors/evaluations/class_spec.py`** (SPC-02) — class definition + members + invariants
- **補助 contract マーカー** (SPC-04) — icontract / deal decorator + PEP-316
  (`pre:` / `post:` docstring keyword) の **検出** (それらの lib を import しない)
- **SP-1 spike** (汎用制御フロー → state、決定論的ルール構築可否) と
  **SP-2 spike** (sequence branch fidelity) を各 plan の最初の deliverable として実行
- **DIA-07**: 5 diagram 全出力が `graph_base.py` の GraphNode / GraphEdge / GraphModel /
  GuardExpr schema に validate (physical-only metadata は `physical_*` / `source_*` prefix)

**スコープに含まれる Requirements (10 件):** DIA-01, DIA-02, DIA-03, DIA-04, DIA-05, DIA-06,
DIA-07, SPC-01, SPC-02, SPC-04

**スコープに含まれないもの:**
- C++ Frontend (`frontends/cpp.py`) + libclang 統合 + C++ 上での diagram/spec 抽出 → Phase 4
- SPC-03 (Doxygen `\pre`/`\post`/`\invariant` 契約抽出) → Phase 4 (REQUIREMENTS Traceability)
- DET-01 byte-identical snapshot 完成形 / SCH-04 cross-lib schema compat test → Phase 5
- DOC-02 README platform compat matrix → Phase 5
- AST primitives (Phase 2 で完了)

</domain>

<decisions>
## Implementation Decisions

### ⚠ Contract-level finding: EdgeKind が DIA-03/DIA-04 を表現できない (要 Phase 1 locked-decision 更新)

スカウトで Phase 1 locked の `EdgeKind` closed Literal と Phase 3 要件の間に実在の矛盾を検出。
user 承認済み (2026-06-01 "OK")。

- **D-01:** `models/evaluations/graph_base.py` の `EdgeKind` (閉じた 11 値) には
  **import 依存を表す値が存在しない** (`inherits/implements/composes/aggregates/associates/
  field_of/param_of/returns/instantiates/calls/transitions_to`)。DIA-03 component diagram は
  「import 由来依存エッジ」が要件だが、自然な値 `dependency`/`depends` は **Phase 1 が Pitfall 7 で
  catch-all として明示的に禁止** (`uses/other/misc/depends` を forbid)。
  → **`EdgeKind` に明示セマンティック値 `imports` を追加** (module A imports module B、
  catch-all ではなく明示セマンティック — `associates` が "undecidable fallback だが explicit semantic"
  であるのと同じ哲学)。package diagram の containment 表現が必要なら **`contains` も同様に追加** を
  planner が DIA-04 設計時に判断 (containment を node 入れ子/attributes で表現できるなら追加不要)。
  これは Phase 1 locked closed Literal の **append-only 更新** であり、Open-Closed 不変条件
  (dispatch dict は append-only) と同じ精神。既存 11 値は不変。

### GA-1: スキーマ整合戦略 (SCH-01 / DIA-07 / EdgeKind)

- **D-02:** **自己完結スキーマ (graph_base.py) を維持** する。SCH-01 の字面 (「`lib-diagram-parser`
  の model を直接 import」) は採らない。理由: 兄弟 lib `lib-diagram-parser/lib_diagram_parser/models.py`
  の GraphNode/GraphEdge/GraphModel は `extra="forbid"` 無し・`physical_*` field 無し・閉じた
  Literal 無しの緩いスキーマで、直接 import すると Phase 1 で確立した厳格スキーマ
  (`extra="forbid"` / 閉じた EdgeKind / `physical_module`) を失う。Phase 1 は意図的に自己完結を
  選び「direct-import vs subclass は Phase 3 で再評価 (D-15/D-17)」と先送りしていた。本 D-02 で
  **自己完結維持** に確定。cross-lib 構造互換は SCH-04 (Phase 5) の構造互換テストで担保する。
- **D-03:** **物理↔論理の語彙ギャップは verifier の責務**。兄弟 lib の `edge_type` 語彙
  (`dependency/inheritance/implementation/aggregation/composition/transition/call/association`、
  plain str) と本 lib `EdgeKind` (`inherits/composes/calls/transitions_to/...`) は字面が異なるが、
  本 lib は **厳格・自己完結な語彙を維持** し、`inherits` vs `inheritance` のようなギャップ解釈は
  verifier (LLM agent) が担う (PROJECT.md Core Value「表現幅ギャップの解釈は verifier 責務」と整合)。
  本 lib 側で兄弟 lib 語彙へ rename はしない。
- **D-04:** **DIA-07 schema 適合は `graph_base.py` 基準**。5 diagram 全出力が GraphNode /
  GraphEdge / GraphModel / GuardExpr に validate。physical-only metadata は `physical_*` /
  `source_*` prefix の optional field (SCH-02)。`GraphNode.node_type` は plain str のまま
  (`"class"/"component"/"package"/"state"` 等を値として emit、Literal 化しない — Phase 1 D-15 通り)。

### GA-2: 兄弟 lib lib-diagram-parser 協調の scope/sequencing (DIA-04)

- **D-05:** 兄弟 lib `lib-diagram-parser` の `node_type` は **plain `str`** (enum/Literal ではない)。
  よって `node_type="package"` 追加は **兄弟 lib のコード変更不要** (str は任意値を受理)。
  ROADMAP/REQUIREMENTS の「enum 値追加 PR (`lib-diagram-parser>=0.1.x`)」という枠組みは
  実体と乖離しており、実際は **docstring/コメントの語彙整合のみ**。
- **D-06:** Phase 3 では **本 lib 側で `node_type="package"` を emit** し package diagram を完結実装する。
  兄弟 lib へは `node_type` コメントに `"package"` を追記する **軽量ドキュメント PR** のみ提出
  (任意・非ブロッキング)。**DIA-04 を「PR merge 待ち」でブロックしない** — 実装は本 lib 側で完結可能。
  cross-lib 構造互換の検証は SCH-04 (Phase 5)。

### GA-3: SP-1 / SP-2 spike の ship-vs-defer 基準 (v0.2.0 / v0.3.0 線、acceptance scope)

- **D-07:** **must-have は v0.2.0 確定**: DIA-02 linear sequence (call graph 由来) と
  DIA-05 FSM 明示パターン (`transitions.Machine` / `python-statemachine` / native Enum) +
  DIA-06 return-value substitution 解析。これらは spike 結果に依存しない。
- **D-08:** **spike 依存部分の ship-vs-defer は決定論性で判定**:
  - **SP-2** (sequence branch fidelity: alt/loop/par Mermaid frame): 各 plan の最初の deliverable
    として spike を実行。決定論的に AST から branch を抽出できれば **ship**、できなければ
    **DIA-02-FULL として v0.3.0 へ defer** し `.planning/spikes/SP-2-sequence-branch-fidelity.md` に
    verdict を記録。
  - **SP-1** (汎用制御フロー → state、明示 FSM パターンを超える抽出): 同様に spike 実行。
    決定論的ルールが構築可能なら **ship**、不可能なら **DIA-05-FULL として v0.3.0 へ defer** し
    `.planning/spikes/SP-1-general-control-flow-state.md` に verdict を記録。
  - 判定基準は「**決定論的ルールが構築可能か**」のみ (LLM/heuristic に頼らず、`(raw_content, path,
    config)` の純粋関数として byte-identical を保てるか)。Layer M bisimulation の前提を崩さない。
  - user 承認済み (2026-06-01): acceptance scope だが「決定論性で defer 判定」方針で合意。

### GA-4: spec 抽出の docstring パーサ — 依存追加 vs 内製 (SPC-01/02/04、Tech stack = contract)

- **D-09:** **外部依存を追加せず stdlib のみで内製**。Google / NumPy / Sphinx Napoleon の
  docstring section 解析 (`Args:` / `Parameters` / `:param:` 等) は `ast.get_docstring()` +
  内製パーサで実装。理由: Constraints (決定論性 / no-GPL / caller-agnostic / 最小依存) と整合。
  `docstring_parser` 等の外部 lib を追加すると Tech stack constraint が変わり、決定論性も外部依存に
  委ねることになる。
- **D-10:** **SPC-04 は検出のみ**。icontract / deal の decorator と PEP-316 (`pre:`/`post:`
  docstring keyword) は **AST/正規表現で検出** し contract entry を生成するが、`icontract`/`deal`
  本体を import/実行しない (Pydantic / dataclass は Phase 2 で済、SPC-04 は補助的検出の追加)。

### Claude's Discretion (Phase 3 planner / researcher が既存根拠から自律判断 — user ノータッチ)

contract level の変更が必要になった場合のみ surface する (それ以外は RESEARCH.md / CONTEXT.md /
REQUIREMENTS.md / docs / 既存 `lib_code_parser/` convention を base に決定):

- **`EdgeKind` 追加値の最終形** (`imports` のみ / `contains` も / 各値の正確な semantic 記述) —
  D-01 の方針内で planner が DIA-03/DIA-04 設計時に確定 (containment を node 入れ子で表現できるなら
  `contains` 不要)
- **各 diagram extractor の signature / module 配置** — `extractors/evaluations/` 配下、
  Phase 2 の `def extract(cav: CAV, config: ParserConfig) -> <Pydantic>` pattern を継承
- **DIA-01 の composition/aggregation 判定の AST 実装細部** (型注釈の解析方法、`Optional[X]`/
  `list[X]` の unwrap) — ROADMAP SC1 規則の実装
- **DIA-02 sequence の participant 解決 / self-call 表現 / chain call 分解** — Phase 2 callgraph の
  表現を継承 (Phase 2 deferred の「CallGraph 解像度拡張」を Phase 3 入口で再評価)
- **DIA-05/06 の FSM AST 検出パターン詳細** (`transitions.Machine(states=..., transitions=...)` の
  引数解析、`python-statemachine` の State/transition クラス属性解析、native Enum の transition
  method 検出条件、return-value substitution の callee 解決アルゴリズムと cycle detection 実装) —
  ROADMAP SC3/SC4 規則の実装
- **docstring section パーサの内部実装** (Google/NumPy/Sphinx の dialect 判定、section 名 mapping、
  pre/post condition の抽出ヒューリスティック) — D-09 の枠内
- **spec model の field 構造** (`FunctionSpec` / `ClassSpec` の docstring_sections / preconditions /
  postconditions / members / invariants の Pydantic shape) — `models/evaluations/` 配下に新設、
  `extra="forbid"` 必須、physical metadata は `physical_*`/`source_*` prefix
- **SP-1 / SP-2 spike の実験設計** (fixture 選定、決定論性検証方法)
- **sort key / DET-04 整合の具体的 composite key 構成**
- **test 戦略** (negative case fixture `class Color(Enum): RED,GREEN,BLUE → 0 FSM` の assert 方法、
  diagram 出力の golden fixture 設計)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (researcher / planner / executor) MUST read these before planning or implementing.**

### Phase 3 直接根拠

- `.planning/PROJECT.md` — Core Value (物理↔論理ギャップ解釈は verifier 責務)、16 Key Decisions
  (特に FSM return-value substitution / composition-vs-aggregation / node_type=package /
  lib-diagram-parser coordination)、Constraints (Determinism / I/O policy / Schema compatibility /
  最小依存)
- `.planning/REQUIREMENTS.md` — 本 Phase 10 件 (DIA-01..07, SPC-01, SPC-02, SPC-04) +
  Traceability 表 (SPC-03 は Phase 4、DIA-02-FULL/DIA-05-FULL は v2) + Acceptance Criteria
- `.planning/ROADMAP.md` §Phase 3 — 5 success criteria (class diagram composition/aggregation 規則 /
  linear sequence + component + package(node_type=package) / FSM 明示パターン + negative case /
  return-value substitution N 階層 + SP-1 verdict / FunctionSpec+ClassSpec+補助マーカー +
  全 5 diagram の GraphNode/GraphEdge/GraphModel schema 適合)
- `lib-code-parser.md` (project root、Phase 1 で full rewrite 済み) — v0.2.0 全方針の現行 spec

### スキーマ contract (Phase 3 が必ず守る / 更新する)

- `lib_code_parser/models/evaluations/graph_base.py` — **本 Phase の中心 contract**。
  GraphNode / GraphEdge / GraphModel / GuardExpr + 閉じた `EdgeKind` (11 値)。
  **D-01 で `imports` (必要なら `contains`) を append-only 追加**。docstring に D-15/D-17
  (Phase 3 で direct-import vs subclass 再評価) の記載あり → D-02 で「自己完結維持」に確定。
- `c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser/lib_diagram_parser/models.py` —
  兄弟 lib スキーマ (read-only 参照)。GraphNode.node_type / GraphEdge.edge_type は **plain str**
  (enum ではない)、`extra="forbid"` 無し。D-03 (語彙ギャップは verifier 責務) / D-05 (node_type=package
  はコード変更不要) の根拠。SCH-04 (Phase 5) で構造互換を直接 import テスト。
- `docs/09-extending.md` — Open-Closed 6 不変条件 (#2 既存評価単位変更不可 / #3 CodeContent 追加は
  optional field / #4 dispatch dict は append-only / #5 評価単位は primitives を pull)。Phase 3 の
  5 diagram + 2 spec は #4 (EVALUATIONS dict 登録) + #5 (CAV/primitives を pull) に従う

### Phase 1 / Phase 2 carry-forward (Phase 3 が依存する locked decisions)

- `.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md` — D-14 (論理アーキ
  比較対象 = `models/evaluations/` 配下のみ)、D-15/D-17 (graph schema 自己完結 + Phase 3 再評価)、
  Open-Closed 6 不変条件、CAV / dispatch / SubprocessAdapter
- `.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md` — Phase 2
  decisions (CAV consumer pattern、`def extract(cav, config)` signature、contracts.py source_kind)。
  特に `<deferred>` の「AST-02 CallGraph 解像度拡張は Phase 3 (DIA-02) 入口で再評価」「SPC-04 は
  Phase 3 scope」
- `lib_code_parser/_dispatch.py` — `EVALUATIONS` dict (Phase 3 で 5 diagram + 2 spec entry を登録)
- `lib_code_parser/frontends/python.py` — CAV 生成 (Phase 3 評価単位の入力)
- `lib_code_parser/models/primitives/callgraph.py` — `CallGraph` (DIA-02 sequence / DIA-03
  component が pull)
- `lib_code_parser/models/primitives/functions.py` — `FunctionNode` (DIA-01 class / SPC-01/02 spec
  が pull)
- `lib_code_parser/models/primitives/type_deps.py` — `TypeDep` (DIA-03 component import 依存が pull)
- `lib_code_parser/models/primitives/contracts.py` — `ContractInfo` + source_kind (SPC-04 補助
  マーカーが拡張)
- `lib_code_parser/executor.py` — dispatch dict 走査型 (Phase 3 で EVALUATIONS 走査を追加、
  executor 本体は不変が Open-Closed 不変条件 #6)

### Spike 記録先 (Phase 3 で生成)

- `.planning/spikes/SP-1-general-control-flow-state.md` — SP-1 verdict (ship / v0.3.0 defer)
- `.planning/spikes/SP-2-sequence-branch-fidelity.md` — SP-2 verdict (ship / v0.3.0 defer)
- `.planning/spikes/SP-3-libclang-macos-arm64.md` — Phase 1 で記録済み (Phase 3 は参照のみ、Phase 4 入口)

### コードベース現状

- `.planning/codebase/ARCHITECTURE.md` / `CONCERNS.md` / `STRUCTURE.md` — v0.1.0/Phase 完了時点の
  記録 (Phase 3 着手前に Phase 2 完了状態を反映した refresh は planner 判断)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`lib_code_parser/models/evaluations/graph_base.py`** — DIA-07 の出力 schema 一式。Phase 3 の
  5 diagram は全てこの GraphNode/GraphEdge/GraphModel/GuardExpr を emit。D-01 で EdgeKind を
  append-only 拡張
- **`lib_code_parser/models/primitives/*.py`** — Phase 2 で確立した CallGraph / FunctionNode /
  TypeDep / ContractInfo。各 diagram/spec extractor がこれらを **pull** (Open-Closed #5、評価単位は
  primitives を再利用、直接 AST を再走査しない)
- **`lib_code_parser/extractors/primitives/*.py`** — Phase 2 の `def extract(cav, config)` pattern。
  Phase 3 `extractors/evaluations/*.py` は同 signature 慣習を継承
- **v0.1.0 `_PRECONDITION_DECORATORS` / `_INVARIANT_DECORATORS` frozenset 定数** (Phase 2
  contracts.py に移植済み) — SPC-04 の icontract/deal/PEP-316 検出パターンの拡張ベース

### Established Patterns

- **CAV single-parse**: Phase 3 評価単位も CAV (1 回 parse の Pydantic envelope) を consume。
  AST 再パース禁止 (Phase 1/2 で確立した anti-pattern 解消を維持)
- **pure-function + Pydantic contract**: 各 extractor は `(cav, config) → Pydantic` の純粋関数、
  module 間は Pydantic model のみで依存 (ARC-01/ARC-02)
- **`model_config = ConfigDict(extra="forbid")`**: Phase 3 で新設する spec model
  (`FunctionSpec`/`ClassSpec`) も必須 (SCH-03)
- **physical-side extension prefix**: physical-only metadata は `physical_*` / `source_*` prefix の
  optional field (SCH-02、verifier は physical_ prefix を論理比較時に無視)
- **DET-04 sort-on-exit**: 全 diagram/spec 出力は stable composite key で sort 後 emit
- **dispatch dict 走査 + EVALUATIONS append-only**: Phase 3 で `EVALUATIONS` に 5 diagram + 2 spec を
  登録、executor 本体は不変 (Open-Closed #4/#6)

### Integration Points

- **`_dispatch.py` の `EVALUATIONS` dict**: Phase 3 で 7 entry (class_diagram / sequence_diagram /
  component_diagram / package_diagram / state_diagram / function_spec / class_spec) を登録
- **`models/evaluations/graph_base.py` の `EdgeKind`**: D-01 で `imports` (必要なら `contains`) を
  append-only 追加。既存 11 値は不変
- **兄弟 lib `lib-diagram-parser`**: D-06 の軽量ドキュメント PR (node_type コメントに "package" 追記)
  以外は read-only。SCH-04 直接 import テストは Phase 5

</code_context>

<specifics>
## Specific Ideas

- **「contract レベルのみ user 相談、下位 detail は agent 自律」** (user 運用方針): Phase 3 では
  EdgeKind 更新 (D-01)・スキーマ整合戦略 (GA-1)・兄弟 lib 協調 (GA-2)・spike defer 基準 (GA-3)・
  Tech stack への依存追加可否 (GA-4) のみ user 承認を取り、model field/signature/private helper/
  test 戦略/AST 実装細部は planner/researcher 自律判断とした (2026-06-01 全 GA を "OK" 承認)
- **「EdgeKind の append-only 拡張は Open-Closed 精神と整合」** (D-01 議論): `dependency`/`depends` は
  Pitfall 7 で catch-all 禁止だが、`imports` は明示セマンティック (module A imports module B) なので
  `associates` (undecidable fallback だが explicit semantic) と同じ哲学で追加可
- **「自己完結スキーマ維持 + verifier が語彙ギャップ吸収」** (GA-1/D-02/D-03): SCH-01 の字面
  (直接 import) より Phase 1 の厳格スキーマ (extra=forbid / physical_* / 閉じた EdgeKind) を優先。
  Core Value「ギャップ解釈は verifier 責務」と整合
- **「node_type は plain str なので package 追加にコード変更不要」** (GA-2/D-05): ROADMAP の
  「enum 値追加 PR」枠組みは実体と乖離、軽量ドキュメント PR で十分・非ブロッキング

</specifics>

<deferred>
## Deferred Ideas

### Phase 4 入口で再評価
- **SPC-03 Doxygen 契約抽出** (`\pre`/`\post`/`\invariant`) — C++ 対称性、REQUIREMENTS Traceability
  で Phase 4
- **C++ 上での 5 diagram + 2 spec 抽出** (LNG-04 schema parity) — Phase 4

### Phase 5 入口で再評価
- **SCH-04 cross-lib schema compat test** — `lib-diagram-parser` を直接 import して構造互換を assert。
  D-02 (自己完結維持) を Phase 5 で検証。Phase 3 の軽量ドキュメント PR (D-06) 状況も合わせて確認
- **DET-01 byte-identical snapshot 完成形** — Phase 3 で追加する 5 diagram + 2 spec を含めた全体
  snapshot として Phase 5 で完成
- **DOC-02 README platform compat matrix** — Phase 5

### v0.3.0+ (spike verdict 次第で defer)
- **DIA-02-FULL** sequence branch fidelity (alt/loop/par) — SP-2 spike が「決定論的構築不可」なら defer
- **DIA-05-FULL** 汎用制御フロー → state diagram — SP-1 spike が「決定論的構築不可」なら defer

### 兄弟 lib coordination (任意・非ブロッキング)
- **`lib-diagram-parser` node_type ドキュメント PR** — `"package"` をコメント語彙に追記する軽量 PR
  (D-06)。Phase 3 実装をブロックしない

</deferred>

---

*Phase: 3-Python Diagram + Spec Extractors*
*Context gathered: 2026-06-01*
