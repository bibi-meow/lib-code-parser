# Phase 2: Python Frontend + AST Primitives + ACL-2 Adapters - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-29
**Phase:** 02-python-frontend-ast-primitives-acl-2-adapters
**Areas discussed:** G-1 (v0.1.0 legacy + ParserConfig stub), G-2 (PyrightAdapter), G-3 (source_kind 粒度)

---

## G-1: v0.1.0 legacy 4 ファイル + ParserConfig stub の処理

| Option | Description | Selected |
|--------|-------------|----------|
| A. Clean break | 4 legacy 削除 + barrel ParserConfig を typed 版に差し替え。v0.1.0 caller `ParserConfig(params={...})` は break。 parity test の JSON byte-identical (stub 経由) を廃止し、shipped v0.1.0 fixture snapshot test に置換 | ✓ |
| B. Hybrid (Claude 推薦) | legacy 4 ファイル削除 + ParserConfig typed graduation、ただし 13 name surface だけは維持 | |
| C. Full backward-compat | barrel stub も legacy も残す、Phase 5 まで dual-path 保守 | |

**User's choice:** A (Clean break)
**Notes:** user 指示「しっかりときれいにしましょう。レガシーは毒です」。Claude 推薦は B (Hybrid) だったが、user がより clean な break を選択した。
v0.2.0 は pre-release internal lib のため、`params={...}` API 破壊は許容される。Phase 1 Plan 09
SUMMARY の「Phase 2 で typed graduation」予告と整合し、PROJECT.md §Constraints「互換性破壊は
Key Decisions に明示する場合のみ」は CONTEXT.md D-02 で明示することで満たす。

実装影響:
- legacy 4 ファイル全削除 (`ast_extractor.py` / `callgraph_builder.py` / `contract_extractor.py` / `type_dep_builder.py`)
- barrel `lib_code_parser.ParserConfig` を typed 版に統一
- `executor.py` を dispatch dict 走査型に rewrite
- parity test 再設計 (name surface + no-duplication は保持、stub parity 廃止、snapshot test 追加)

---

## G-2: AST-03 PyrightAdapter の解析モード・失敗ハンドリング

### G-2-a. 解析モード

| Option | Description | Selected |
|--------|-------------|----------|
| (i) caller passes path on disk | `pyright {path} --outputjson` を直接実行 | |
| (ii) internal tmpdir + write bytes | lib 内部で tmpdir 作成、raw_content 書き出し、pyright 実行、自動 cleanup | ✓ |
| (iii) caller passes project root | pyright が project 全体を resolve | |

### G-2-b. 失敗時セマンティクス

| Option | Description | Selected |
|--------|-------------|----------|
| (i) fail loudly | RuntimeError を上位伝搬 | ✓ |
| (ii) graceful degradation | 空 TypeDep + stderr warning | |

### G-2-c. JSON 正規化範囲

| Option | Description | Selected |
|--------|-------------|----------|
| 必要 subkey のみ抽出 + forward-slash 正規化 + tmpdir prefix strip | sort key (node_id, type_ref)、generalDiagnostics 破棄、具体的 subkey は researcher 領域 | ✓ |

### G-2-d. pyright CLI フラグ・出力解釈

| Option | Description | Selected |
|--------|-------------|----------|
| researcher 領域 | CONTEXT.md には選定基準のみ、RESEARCH.md で gsd-phase-researcher が確定 | ✓ |

**User's choice:** Claude 推薦案を全 4 サブ論点で承認
**Notes:** caller-agnostic I/O 原則 (Phase 1 D-09) を Phase 2 の PyrightAdapter で実装側として実証。
Determinism-first 原則と整合する fail-loudly セマンティクスを採用。 pyright JSON schema の
具体的 mapping は実機検証が必要なため researcher 領域に委ねる。

---

## G-3: AST-04 `source_kind` 判別の粒度

### G-3-a. 旧 Pydantic v1 decorator のマッピング

| Option | Description | Selected |
|--------|-------------|----------|
| `@root_validator` → `pydantic_model_validator` にマップ | semantic equivalent、Literal 4 値維持 | ✓ |
| `@root_validator` を認識しない | v0.2.0 は v2 syntax only | |

### G-3-b. 集約粒度

| Option | Description | Selected |
|--------|-------------|----------|
| (α) ContractInfo 全体に単一 source_kind | class は Pydantic か dataclass のどちらか 1 種類だけ assume | |
| (β) 各 entry に source_kind | 同 class 内に混在 case を表現可能、verifier 責務分離と整合 | ✓ |
| (γ) source_kind 別に分割 | 同 class が 2 種類で 2 ContractInfo emit | |

### G-3-c. 混在 case (Pydantic + `__post_init__` 同居)

| Option | Description | Selected |
|--------|-------------|----------|
| (β) で自動サポート | 別ルール不要 | ✓ |

**User's choice:** Claude 推薦案を全 3 サブ論点で承認
**Notes:**
- ROADMAP success criteria 3 で source_kind 4 値が固定されている前提で、未確定の mapping と
  集約粒度のみを議論
- `@root_validator` の Pydantic v1 → v2 移行は semantic equivalent (model レベルの validator)
  なので `pydantic_model_validator` バケットに集約
- 集約粒度 (β) は verifier (LLM agent) が contract-statement レベルで物理↔論理を比較するという
  Core Value (PROJECT.md) と整合し、物理側は事実の最大忠実度抽出に徹する責務分離を維持する
- AST-04 success criteria 「verifier が `__post_init__` を unconditional Pydantic 扱いしないこと」
  は (β) + 5 entry 単位 mapping (D-11/D-12/D-13) で満たす

---

## Claude's Discretion

- **G-4 (AST-05 単一 parse の hard gate test 戦略)** — 複数戦略 (monkeypatch / grep / structural)
  併用が安価、planner が RESEARCH.md と CONTEXT.md から判断
- **G-5 (AST-02 内製 CallGraph の解像度)** — method/chain/import 解決の表現幅は v0.1.0 parity を
  baseline に planner が研究して継承 or 拡張、ROADMAP success criteria 2「lexicographic by
  (caller, callee)」のみを invariant とする
- **TRC-02 module docstring の REQ-ID 宣言形式** — 既存 `Traces: REQ-ID, US-NN` regex 整合の形式
- **TRC-03 trace tag extraction parity** — v0.1.0 で確立した regex をそのまま保持
- ファイル内部の関数命名 / private helper 名 / module docstring の細部表現
- pyright JSON parse 実装の error path 詳細 (D-06 fail-loudly 枠内)

---

## Deferred Ideas

### Phase 3 入口で再評価
- AST-02 内製 CallGraph の解像度拡張 (G-5)
- `extractors/primitives/auxiliary_contracts.py` (SPC-04) — Phase 3 scope

### Phase 4 入口で再評価
- C++ frontend (`frontends/cpp.py`) + libclang 統合
- DET-02 libclang ABI assertion

### Phase 5 入口で再評価
- DET-01 byte-identical snapshot test 完成形
- SCH-04 cross-lib schema compat test
- DOC-02 README platform compat matrix

### v0.3.0+ (next milestone) で検討
- v0.1.0 caller compat layer の再導入 (もし外部 caller 発生時)

---

## Post-RESEARCH update (2026-05-31)

### D-07-revised: pyright JSON 前提逆転 → ast + diagnostic-driven `resolved` annotation 採用

**Discovered by:** gsd-phase-researcher (Phase 2 RESEARCH §2.1)、 2026-05-31

**Empirical evidence:**
- pyright 1.1.409 `--outputjson` を 3 fixture (clean / bad-imports / reveal_type) で実機 fire
- 公式 docs (microsoft/pyright command-line.md) + basedpyright docs + GitHub issue
  microsoft/pyright#6740 ("outputjson schema is not according to spec") でクロス確認
- 結論: `--outputjson` の output schema は `{version, time, generalDiagnostics[], summary{}}` のみ。
  型解決済み import / annotation データを返す subkey は存在しない。

**Original D-07 assumption (invalidated):**
- 「`--outputjson` のうち TypeDep 生成に必要な subkey のみ抽出」
- 「`generalDiagnostics` は破棄」

**Revised algorithm (CONTEXT.md D-07 に反映、 詳細は RESEARCH.md §2.3):**

```text
def extract_type_deps(cav, config) -> list[TypeDep]:
    # 1. stdlib ast walk で TypeDep raw 抽出 (v0.1.0 type_dep_builder.py の logic 継承)
    raw_deps = _ast_walk_for_type_deps(cav.payload, cav.path)

    # 2. PyrightAdapter を起動して generalDiagnostics を収集
    diagnostics = PyrightAdapter(...).execute(...)

    # 3. 各 raw_dep の source 行に reportMissingImports diagnostic が
    #    発火しているか判定 → resolved flag を annotate
    unresolved = {d.line for d in diagnostics if d.rule == "reportMissingImports"}
    return [dep.model_copy(update={"resolved": dep.source_line not in unresolved})
            for dep in raw_deps]
```

**Why selected:**
- 「`generalDiagnostics` こそが唯一の有用データ」が実機検証で確定
- Layer M bisimulation の決定論性 (Core Value) を維持
- 「`pyright[nodejs]==1.1.409` で完結」 (CONTEXT.md G-2 selection 基準) を破らない

**Sub-contract decisions deferred to planner autonomy (user no-touch per [[feedback_contract_level_review]]):**

- TypeDep model に `resolved` を field 追加 vs `kind` enum 拡張 — planner 判断 (RESEARCH §2.3 推奨は field 追加)
- PyrightAdapter signature が `raw_content: bytes` を CAV 内 / 別引数のどちらで受け取るか — planner 判断 (Phase 1 CAV lock を破らない選択肢が推奨)
- ContractInfo model の D-12 (β) を満たす field 構造 (案 A: ContractEntry list / 案 B: parallel field / 案 C: A + computed shim) — planner 判断 (RESEARCH §3.4 推奨は案 A)
- chain call `a.b().c()` の edge 数、 `__post_init__` 検出条件 — planner 判断 (RESEARCH §4 / §3 で v0.1.0 parity baseline 提示済み)
- AST-05 hard gate test 戦略 (primary/backup 組み合わせ) — planner 判断 (RESEARCH §5.2 推奨は grep + monkeypatch)
- TRC-02 docstring template、 各 extractor の internal helper 命名等 — planner 判断

これら下位 decision は contract 範囲内 (architecture / concept / acceptance criteria に変更なし) のため
planner が RESEARCH.md / CONTEXT.md / docs / 既存コードベースを根拠に自律決定する。

**User approval (2026-05-31):** D-07-revised は contract level の変更として user に surface 済み、 承認済み。
下位 sub-contract decision は agent autonomy に委ねる方針も合意。
