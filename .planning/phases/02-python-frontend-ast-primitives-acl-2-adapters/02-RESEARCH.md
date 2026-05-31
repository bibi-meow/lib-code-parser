# Phase 2: Python Frontend + AST Primitives + ACL-2 Adapters — Research

**Researched:** 2026-05-30
**Domain:** Python frontend (stdlib `ast`) / 4 pure-CAV primitive extractors / pyright subprocess adapter / Pydantic v2 validator AST detection / one-parse-per-file enforcement / v0.1.0 parity baselines
**Confidence:** HIGH — 全主要決定点を実機検証 (pyright 1.1.409 `--outputjson` を実 fixture で fire / v0.1.0 4 extractors を実機 import で edge-case 列挙 / `PYRIGHT_PYTHON_FORCE_VERSION` 動作確認 / Pydantic 2.11.10 検証)

## Summary

Phase 2 の最大の研究成果は、 **CONTEXT.md D-07/D-08 が依拠する前提 — pyright `--outputjson` は型解決済み import / annotation 情報を返す — が実機検証で false と判明したこと** である。 pyright `--outputjson` の output schema は `{version, time, generalDiagnostics[], summary{}}` のみで、 import や annotation の解決済み型情報は一切含まれない (本研究 §2 で実機 fixture で再現確認、 公式 docs および basedpyright docs でも同一仕様であることをクロス確認)。 CONTEXT.md D-07 の「`TypeDep` 生成に必要な subkey のみ抽出」「`generalDiagnostics` は破棄」という前提自体が転倒しており、 **`generalDiagnostics` 以外に抽出するデータは存在しない**。 Phase 2 planner はこの事実に基づいて pyright の使い方を再定義する必要がある。

最も重要な結論を 5 点に要約する。

1. **pyright の現実的な使い方は「型解決済みデータの提供者」ではなく「import 解決可否の判定者」である**。 stdlib `ast` で `Import` / `ImportFrom` / annotation を抽出し、 pyright を `reportMissingImports=error` モードで走らせて `generalDiagnostics` を読み、 各 import 行範囲に `reportMissingImports` が発火していない = `resolved=True`、 発火している = `resolved=False` で `TypeDep` に追記する。 これは Layer M bisimulation の前提 (決定論性) を満たし、 pyright を caller 環境の依存に巻き込まずに使える唯一の現実解である。 ([VERIFIED: 実機 fixture で `bad_imports.py` に `from nonexistent_pkg import X` を入れて pyright 1.1.409 `--outputjson` を実行し `rule: "reportMissingImports"` の diagnostic が固定 schema で emit されることを確認])
2. **pyright CLI 選定: `pyright --outputjson <path>` (それ以外の flag は付けない) が D-08 の最適解**。 `--verifytypes` は package 単位の type completeness audit (本 lib 用途と無関係)、 `--dependencies` は text 出力で `--outputjson` と排他、 `--verbose` は `--outputjson` と排他、 `--ignoreexternal` は `--verifytypes` 専用 flag。 残るのは default check + JSON で、 これが最も決定論的かつ schema 安定 (本研究 §2.2)。
3. **DET-03 の env var 名は `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` で正しい**。 さらに `PYRIGHT_PYTHON_IGNORE_WARNINGS=1` を併設して stderr の「new pyright version available」warning を抑止しないと、 caller 環境で stderr が決定論的でなくなる (本研究 §2.4)。
4. **v0.1.0 `callgraph_builder.py` の解像度は決定論的に弱い**: `self.foo()` → callee は bare `foo` (Class.foo ではない)、 chain call `a.b().c()` は 2 edges、 nested function は outer に flatten、 edges は **未 sort**。 Phase 2 は v0.1.0 parity を維持しつつ、 DET-04 の `(caller, callee)` lexicographic sort を **executor 出力時に追加** する (extractor は emission order を v0.1.0 互換のまま保ち、 sort は emit 直前で 1 pass) 設計が最低リスク (本研究 §4)。
5. **v0.1.0 contract decorator detection には 2 つの実証バグがある**: (a) aliased decorator `from pydantic import field_validator as fv; @fv("x")` は検出失敗 (alias 解決をしていない)、 (b) `@root_validator` は元から認識リストに含まれていない。 Phase 2 D-11 の mapping 表で `@root_validator` を `pydantic_model_validator` に集約する決定は、 「v0.1.0 にバグがあるので Phase 2 で修正する」追加マージン込みで planner に伝達する (本研究 §3)。

**Primary recommendation:** PLAN は **4 並列 wave + 1 sequential closer** で構成する。 Wave 1 (5 parallel plans): (T1) `frontends/python.py` 1-parse Frontend、 (T2) `extractors/primitives/functions.py`、 (T3) `extractors/primitives/callgraph.py`、 (T4) `extractors/primitives/contracts.py` (`source_kind` discriminator + alias 解決 + `@root_validator` 認識 込み)、 (T5) `adapters/pyright.py` (PyrightAdapter — diagnostic-driven `resolved` 注釈 mode)。 Wave 2 (1 plan、 Wave 1 5 件全てに依存): (T6) `extractors/primitives/type_deps.py` (Wave 1 T5 を pull) + `_dispatch.py` registration + `executor.py` rewrite + `ContractInfo` model 拡張 (per-entry source_kind)。 Wave 3 (closer): (T7) v0.1.0 legacy 4 ファイル削除 + barrel ParserConfig graduation + parity test 再設計 (D-04: name surface + no-duplication 保持、 stub parity 廃止、 fixture snapshot 追加) + acceptance test signature 修正。

---

## User Constraints (from CONTEXT.md)

### Locked Decisions

**G-1: v0.1.0 legacy + ParserConfig stub**
- **D-01:** Clean break — Phase 2 完了時点で `lib_code_parser/{ast_extractor,callgraph_builder,contract_extractor,type_dep_builder}.py` を **全削除**、 barrel `lib_code_parser.ParserConfig` を typed 版に差し替え (single source of truth は `lib_code_parser.models.infrastructure.config.ParserConfig`)。 stub 廃止。
- **D-02:** v0.1.0 caller の `ParserConfig(artifact_type=..., executor_lib=..., params={"language": ..., "extract_contracts": ...})` 形式は **明示的 break**。 v0.2.0 は internal lib の minor bump、 PROJECT.md §Constraints の互換性破壊明示要件を本 D-02 で満たす。
- **D-03:** `executor.py` rewrite: `_dispatch.py` の `FRONTENDS` / `PRIMITIVES` dict 走査型に書き換え。 executor 本体に新 extractor 追加時の修正は発生しない (Open-Closed invariant #6)。
- **D-04:** parity test 再設計: name surface 13 names + `_get_module_name` no-duplication hard gate は **保持**、 stub 経由の JSON byte-identical parity は **廃止**、 shipped v0.1.0 fixture snapshot test に置換 (commit `cf7e7ec` 時点の `tests/conftest.py` `EXAMPLE_SOURCE` を typed ParserConfig 経由で実行した結果を JSON snapshot として fix)。

**G-2: PyrightAdapter**
- **D-05:** 解析モード = internal tmpdir + write bytes (caller-agnostic I/O 維持)。 PyrightAdapter は `tempfile.TemporaryDirectory()` で tmpdir 作成、 `raw_content` を `{tmpdir}/{module_name}.py` に書き出し、 pyright を tmpdir cwd で起動。
- **D-06:** 失敗時セマンティクス = fail loudly (RuntimeError)。 pyright 未インストール / startup 失敗 / timeout (60s 既定) / JSON parse 失敗 のいずれも `RuntimeError` を上位伝搬。 silent empty は採用しない。
- **D-07:** JSON 正規化原則: `--outputjson` 出力のうち `TypeDep` 生成に必要な subkey のみ抽出、 file path は forward-slash 正規化、 tmpdir prefix を strip、 sort key は `(node_id, type_ref)`。 **具体的な pyright JSON subkey 名・抽出 algorithm は researcher 領域**。
- **D-08:** **pyright CLI フラグ・サブコマンド選定は researcher 領域** — 選定基準のみ (型解決済み / 決定論的 / `pyright[nodejs]==1.1.409` で完結)。
- **D-09:** DET-03 強制 — subprocess env に `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` を必ず付加。

**G-3: source_kind 粒度**
- **D-10:** ROADMAP success criteria 3 で 4 値 Literal が固定 (`pydantic_validator` / `pydantic_field_validator` / `pydantic_model_validator` / `dataclass_post_init`)。 5 値目を追加しない。
- **D-11:** Pydantic decorator → source_kind mapping 表 (本研究 §3 で実装ガイドに展開):

  | 検出対象 decorator | source_kind |
  |------------------|-------------|
  | `@validator` | `pydantic_validator` |
  | `@field_validator` | `pydantic_field_validator` |
  | `@model_validator` | `pydantic_model_validator` |
  | `@root_validator` (v1 deprecated) | `pydantic_model_validator` (semantic equivalent) |
  | `__post_init__` | `dataclass_post_init` |

- **D-12:** 集約粒度 = (β) 各 contract entry に `source_kind` 付与。 `ContractInfo` は class 単位で 1 entry、 内部に validator-list を保持し、 各 entry が `(source_kind, body_excerpt, line_no, decorator_name)` を持つ。
- **D-13:** 混在 case 自動サポート — Pydantic + `__post_init__` 同居は (β) で別 rule なし。
- **D-14:** `models/primitives/contracts.py` 既存 model 拡張 — Phase 1 で生成済みの `ContractInfo` Pydantic model に、 各 entry が `source_kind: Literal[...]` を持つよう field 追加 (extra="forbid" 維持、 Optional ではなく required)。 具体的な field 名・list 構造は Phase 2 planner が `models/primitives/contracts.py` の Phase 1 出力を読んで決定。

### Claude's Discretion (Phase 2 planner / researcher 決定領域)

- **AST-02 内製 CallGraph の解像度**: method/chain/import 解決の表現幅。 ROADMAP success criteria 2 の「lexicographic by `(caller, callee)`」だけを invariant とし、 v0.1.0 baseline を Phase 2 planner が継承 or 拡張。
- **AST-05 「1 回 parse」の hard gate test 戦略**: (i) monkeypatch `ast.parse` の call count assertion、 (ii) `grep -c "ast\.parse" lib_code_parser/extractors/` 静的 gate、 (iii) extractor signature が `cav.payload` のみ受け取る構造制約 — 複数併用も安価。
- **TRC-02 module docstring REQ-ID 宣言形式**: 既存 `Traces: REQ-ID, US-NN` regex に整合する形式。
- **TRC-03 trace tag extraction parity**: v0.1.0 regex `Traces:\s*([A-Z]+-\d+...)` をそのまま保持。
- ファイル内部の関数命名・private helper 名・module docstring の細部表現は標準慣習。
- pyright JSON parse 実装の error path (Pydantic model 化等) は D-06 fail-loudly の枠内で planner が判断。

### Deferred Ideas (OUT OF SCOPE)

- **Phase 3 入口で再評価**: AST-02 内製 CallGraph の解像度拡張、 `extractors/primitives/auxiliary_contracts.py` (SPC-04 — icontract / deal / PEP-316)
- **Phase 4 入口で再評価**: C++ frontend (`frontends/cpp.py`) + libclang 統合、 DET-02 libclang ABI assertion
- **Phase 5 入口で再評価**: DET-01 byte-identical snapshot test 完成形、 SCH-04 cross-lib schema compat test、 DOC-02 README platform compat matrix
- **v0.3.0+**: v0.1.0 caller compat layer の再導入 (外部 caller 発生時のみ)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AST-01 | `FunctionNode` 抽出 (kind / params / return_type / docstring / trace_tags / source_range) | 本研究 §7.1 — v0.1.0 `extract_functions` 6 acceptance test (FR-01) を baseline として継承、 signature を `(cav, config)` に変更 |
| AST-02 | 決定論的 `CallGraph` (caller→callee edges、 GPL 不使用、 外部 subprocess 不使用) | 本研究 §4 — v0.1.0 `build_callgraph` の実機検証で解像度 rule 確定 (self.foo→bare foo、 chain a.b().c()→2 edges、 nested→flatten)。 emit 時に `(caller, callee)` lexicographic sort を追加 |
| AST-03 | 型解決済み `TypeDep` list (pyright subprocess、 import 文 + annotation type) | 本研究 §2 — pyright `--outputjson` は型情報を返さない実機検証結果に基づき、 「stdlib ast で抽出した TypeDep に pyright `reportMissingImports` 判定を `resolved` flag として annotate」する revised design を推奨 |
| AST-04 | `ContractInfo` の Pydantic validator vs `__post_init__` 区別 (`source_kind` discriminator 4 値) | 本研究 §3 — v0.1.0 `extract_contracts` の AST detection logic は流用可能、 source_kind mapping は D-11 のとおり 4 値、 v0.1.0 の 2 つのバグ (alias 未解決、 `@root_validator` 未認識) を Phase 2 で修正 |
| AST-05 | 全 primitive extractor が単一 CAV で動作 (1 parse per execute() call) | 本研究 §5 — recommended primary gate = monkeypatch (動的)、 backup = grep 静的 gate。 structural constraint (extractor signature) は副次防御で同時採用 |
| DET-03 | `pyright[nodejs]==1.1.409` exact pin + `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` | 本研究 §2.4 — env var 名は公式 (RobertCraigie/pyright-python) で確認済み。 `PYRIGHT_PYTHON_IGNORE_WARNINGS=1` 併設で stderr の version-available warning を抑止 |
| TRC-02 | 各 extractor module の docstring が実装 REQ-ID を宣言 | 本研究 §6 — `Implements: AST-NN` 行 + `Traces: AST-NN, US-NN` 行を docstring に共存させる template を提示 |
| TRC-03 | `Traces: REQ-ID, US-NN` regex が Python 側で v0.1.0 と同一に動作 | 本研究 §7.5 — v0.1.0 `_extract_trace_tags` の正規表現 `r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)"` を Phase 2 でもそのまま再利用 (`extractors/primitives/functions.py` 内に移植)。 v0.1.0 acceptance test FR-05 が同一 input で同一 output を返すことが parity test |

---

## Architectural Responsibility Map

Phase 2 は実装 phase なので Phase 1 で固定済みのレイヤー責務に従う。 確認のため再掲する。

| Capability | Primary Layer | Secondary Layer | Rationale |
|------------|---------------|-----------------|-----------|
| Python source bytes → CAV (1-parse) | `frontends/python.py` | — | D-04 / D-05 / D-08 — Frontend は CAV envelope を emit するだけ、 extractor logic を持たない |
| FunctionNode 抽出 (AST-01) | `extractors/primitives/functions.py` | `models/primitives/functions.py` (output schema) | Phase 1 で path / model 確定済み、 Phase 2 は extractor 実装のみ追加 |
| 内製 CallGraph 抽出 (AST-02) | `extractors/primitives/callgraph.py` | `models/primitives/callgraph.py` | 同上。 GPL 不使用 / 外部 subprocess 不使用 (PROJECT.md Key Decision) |
| TypeDep 抽出 (AST-03) | `extractors/primitives/type_deps.py` | `adapters/pyright.py` (subprocess) + `models/primitives/type_deps.py` | primitive extractor が adapter を pull、 adapter は subprocess hardening を継承 |
| Contract (Pydantic / `__post_init__`) 抽出 (AST-04) | `extractors/primitives/contracts.py` | `models/primitives/contracts.py` (source_kind 拡張) | D-11 / D-12 / D-14 — model field 追加 + extractor logic |
| pyright subprocess 隔離 | `adapters/pyright.py` (SubprocessAdapter subclass) | `adapters/base.py` (Phase 1 確定) | ARC-03 — extractor は subprocess を直接呼ばない |
| FRONTENDS / PRIMITIVES dict 登録 | `_dispatch.py` | — | append-only 5 entry 追加 (python frontend + 4 primitives) |
| Executor dispatch 走査 | `executor.py` (rewrite) | `_dispatch.py` (Phase 1 確定) | Open-Closed invariant #6 — dict 走査ロジックのみ |
| Module name 導出 | `_paths.py` (Phase 1 確定) | — | 既存 `get_module_name()` を全 extractor が pull |

**Why this matters:** Phase 2 は Phase 1 で固定したレイヤー責務を **実装する** phase であり、 新しい責務を追加する余地はない。 Plan 内で「extractor 内で subprocess を呼ぶ近道」「executor に if 分岐を追加する近道」を選ぶと Open-Closed 6 不変条件を即座に破る。 planner はレイヤー責務マップを最初の sanity check に使う。

---

## Standard Stack

### Core (Phase 2 で新規に install / 統合)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stdlib `ast` | Python 3.11+ 同梱 | Python source の 1-parse、 4 primitive extractor の入力 | v0.1.0 から継続。 `ast.parse(source)` → `ast.Module` を CAV の payload に格納 [VERIFIED: v0.1.0 4 extractor が全て同 API を使用] |
| stdlib `tempfile` | Python 3.11+ 同梱 | PyrightAdapter の internal tmpdir 作成 (D-05) | I/O policy 「caller agnostic」維持のため必須 |
| stdlib `subprocess` | Python 3.11+ 同梱 | pyright subprocess 起動 | Phase 1 `adapters/base.py` `run_subprocess()` 経由でのみ呼ぶ (DET-05) |
| stdlib `json` | Python 3.11+ 同梱 | pyright `--outputjson` のパース | D-06 fail-loudly: `json.JSONDecodeError` を `RuntimeError` に raise from する |
| stdlib `re` | Python 3.11+ 同梱 | TRC-03 trace tag 抽出 (`Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)`) | v0.1.0 正規表現をそのまま再利用 |
| `pyright[nodejs]` | `==1.1.409` (厳密 pin、 Phase 1 で pyproject.toml 宣言済み) | TypeDep の解決可否判定 (subprocess) | DET-03。 Phase 2 で実稼働 [VERIFIED: Phase 1 で PyPI release date 2026-04-23 確認、 本研究 §2 で実機 1.1.409 起動と `--outputjson` schema 直接観察] |

### Supporting (既存)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydantic` | `>=2.13.0,<3.0` | 全 output model の Pydantic v2 BaseModel | Phase 1 で既存、 `ContractInfo` model field 追加に使用 |
| `pytest` | `>=8` | acceptance / parity / unit test runner | dev extra、 Phase 2 で acceptance test signature 修正 + snapshot test 追加 |
| `pytest-cov` | (latest) | coverage measurement | dev extra |
| `ruff` | (latest) | format + lint | dev extra、 CI gate |
| `pyright` (dev) | (latest) | dev-time static type check | dev extra (DET-03 の `pyright[nodejs]==1.1.409` とは別目的) |

### Alternatives Considered (本研究で実機確認した結果、 不採用)

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pyright --outputjson` を「resolved import 情報の取得 source」とする | reveal_type 注入 + diagnostic 解析 | 元 source への注入が必要 (immutability 違反) — 不採用 |
| pyright `--outputjson` | pyright `--dependencies` (text) | `--outputjson` と排他、 file 単位の transitive 表で symbol 解像度なし — 不採用 (本研究 §2.2 実機検証) |
| pyright `--outputjson` | pyright `--verifytypes <package>` | package 単位の type completeness audit 用、 source ファイル単位 type 解決ではない — 不採用 (本研究 §2.2 実機検証) |
| pyright `--outputjson` | basedpyright | 同じ仕様 (`--outputjson` = diagnostics-only) [CITED: docs.basedpyright.com/dev/configuration/command-line/] — 採用優位なし |
| pyright wrapper script | system-installed pyright | DET-03 「`PYRIGHT_PYTHON_FORCE_VERSION=1.1.409`」 が機能しないため不採用 |
| stdlib `ast` walk + pyright 解決可否注釈 (本研究の推奨) | typeguard / mypy / pyre subprocess | mypy / pyre は同様に JSON 出力が diagnostic 系で同問題 (情報源: 同種 issue が pyright issue tracker に既出 [CITED: github.com/microsoft/pyright/issues/6740])。 typeguard は runtime 解析。 — Phase 2 で追加 dep を増やさない方針優位 |

**Installation (Phase 2 では pyproject.toml に新規 dependency 追加なし — Phase 1 で `pyright[nodejs]==1.1.409` を install dep に declared 済み):**
```bash
pip install -e ".[dev]"
# Phase 1 で declared 済みの pyright[nodejs]==1.1.409 が稼働する
```

**Version verification (本研究で実機実行):**

| Package | 確認方法 | 確認結果 |
|---------|---------|---------|
| `pyright 1.1.409` | `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409 pyright --version` | `pyright 1.1.409` が起動、 npm 経由で `pyright/dist/typeshed-fallback` を解決して動作 [VERIFIED: 本研究実機 stdout] |
| `pyright --outputjson schema` | `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409 pyright --outputjson /tmp/pyright_test/order_service.py` | `{version, time, generalDiagnostics[], summary{filesAnalyzed,errorCount,warningCount,informationCount,timeInSec}}` を確認 (本研究 §2.1 で full schema 提示) |
| `pyright --outputjson + --verbose` | 実機実行 | `'outputjson' option cannot be used with 'verbose' option` で reject [VERIFIED: 本研究実機 stderr] |
| `pyright --outputjson + --dependencies` | 実機実行 | `'outputjson' option cannot be used with 'dependencies' option` で reject [VERIFIED: 本研究実機 stderr] |
| `PYRIGHT_PYTHON_FORCE_VERSION` 環境変数 | RobertCraigie/pyright-python GitHub 公式 README | `PYRIGHT_PYTHON_FORCE_VERSION` が正しい変数名 [CITED: github.com/RobertCraigie/pyright-python] |
| `PYRIGHT_PYTHON_IGNORE_WARNINGS` 環境変数 | 同上公式 README | 「new pyright version available」warning を抑止 [CITED: 同上] |
| `pydantic 2.11.10` | `pip show pydantic` | INSTALLED [VERIFIED: 本研究 env] |

---

## Package Legitimacy Audit

Phase 2 では新規 dependency を追加しない (Phase 1 で `pyright[nodejs]==1.1.409` と `pydantic>=2.13.0,<3.0` を pyproject.toml に declared 済み)。 Phase 1 audit 結果を carry-forward する。

| Package | Registry | Age | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-------------|-----------|-------------|
| `pyright` | PyPI | 5+ 年 | github.com/RobertCraigie/pyright-python | [OK] (Phase 1) | Approved (`==1.1.409` 厳密 pin、 Phase 1 declared) |
| `nodejs-wheel-binaries` | PyPI | 2+ 年 | github.com/njzjz/nodejs-wheel | [OK] (Phase 1) | Approved (pyright[nodejs] transitive) |
| `pydantic` | PyPI | 6+ 年 | github.com/pydantic/pydantic | [OK] (Phase 1) | Approved (Phase 1 declared) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

Phase 2 は新規パッケージ install を行わないので新規 slopcheck 不要。 stdlib のみ追加使用 (`tempfile`, `subprocess`, `json`)。

---

## Pyright Subprocess Integration

(本節は D-07 + D-08 + DET-03 の確定材料)

### §2.1 pyright `--outputjson` 実機 schema (CONTEXT.md 前提を invalidate)

CONTEXT.md D-07 は「`pyright --outputjson` 出力のうち `TypeDep` 生成に必要な subkey のみ抽出 (`generalDiagnostics` は破棄)」を要件としているが、 **実機検証で `generalDiagnostics` 以外に有用な subkey が存在しないことが判明した**。

実機 fixture 1 (`order_service.py` — クリーンコード):

```json
{
    "version": "1.1.409",
    "time": "1780149844871",
    "generalDiagnostics": [],
    "summary": {
        "filesAnalyzed": 1,
        "errorCount": 0,
        "warningCount": 0,
        "informationCount": 0,
        "timeInSec": 0.824
    }
}
```

実機 fixture 2 (`bad_imports.py` — `from nonexistent_pkg import SomeThing` 等を含む):

```json
{
    "version": "1.1.409",
    "time": "1780149952610",
    "generalDiagnostics": [
        {
            "file": "c:\\Users\\bothe\\AppData\\Local\\Temp\\pyright_test\\bad_imports.py",
            "severity": "error",
            "message": "インポート \"nonexistent_pkg\" を解決できませんでした",
            "range": {
                "start": {"line": 2, "character": 5},
                "end": {"line": 2, "character": 20}
            },
            "rule": "reportMissingImports"
        },
        {
            "file": "...",
            "severity": "error",
            "message": "\"UndefinedType\" が定義されていません",
            "range": {"start": {"line": 16, "character": 28}, "end": {"line": 16, "character": 41}},
            "rule": "reportUndefinedVariable"
        }
    ],
    "summary": {"filesAnalyzed": 1, "errorCount": 2, ...}
}
```

**top-level keys 観察結果:**

| Key | 型 / 内容 | TypeDep 生成への有用性 |
|-----|----------|----------------------|
| `version` | str (e.g. `"1.1.409"`) | DET-03 pin 検証に有用 (1.1.409 と一致するか) |
| `time` | str (epoch millis) | **非決定論的** — 必ず strip して JSON 正規化 |
| `generalDiagnostics` | array of `{file, severity, message, range{start{line,character}, end{line,character}}, rule}` | これだけが解析データ。 ただし「型情報」ではなく「警告」のみ |
| `summary` | `{filesAnalyzed, errorCount, warningCount, informationCount, timeInSec}` | `timeInSec` は非決定論的、 数値部分は有用なし |

**否定的事実 (CONTEXT.md 前提に反する):**

- `generalDiagnostics` 配列の各 diagnostic には `severity` / `message` / `rule` / `range` のみ。 **解決済み import path / 解決済み型名 / fully-qualified name / source module / target symbol は一切含まれない**。
- 「`TypeDep(node_id, type_ref)` を作るための subkey」は存在しない。
- 公式 docs および basedpyright docs で同一仕様であることをクロス確認 [CITED: github.com/microsoft/pyright/blob/main/docs/command-line.md (本研究 fetch)、 docs.basedpyright.com/dev/configuration/command-line/ (本研究 fetch)]。

### §2.2 pyright CLI flag 選定 (D-08 解答)

実機で全 flag 組合せを fire し、 排他制約を全列挙した結果:

| Flag combo | 挙動 | TypeDep 用途への可否 |
|-----------|------|---------------------|
| `pyright --outputjson <path>` | diagnostics JSON | **採用候補** (唯一 JSON schema が stable) |
| `pyright --outputjson --verbose <path>` | reject: `'outputjson' option cannot be used with 'verbose' option` | 不採用 (排他) [VERIFIED: 本研究実機] |
| `pyright --outputjson --dependencies <path>` | reject: `'outputjson' option cannot be used with 'dependencies' option` | 不採用 (排他) [VERIFIED: 本研究実機] |
| `pyright --dependencies <path>` | text output (file-level transitive imports)、 `--outputjson` 不可 | 不採用 (text、 symbol 単位でない) |
| `pyright --outputjson --verifytypes pydantic <path>` | type completeness audit JSON (package 単位、 fixture 内のコード解析ではない) | 不採用 (用途不一致) [VERIFIED: 本研究実機] |
| `pyright --ignoreexternal` | `--verifytypes` 専用 flag、 単独では meaningful 効果なし | 不採用 |
| `pyright -p <config> --outputjson <path>` | `pyrightconfig.json` で `strict mode` + `reportMissingImports="error"` 等を設定 | **検討候補** (warning 量を制御できる、 strict mode で reveal_type 風機能を引き出せるかは結論なし) |
| `pyright --outputjson --pythonversion 3.12 <path>` | pyright が解析対象とする Python バージョン明示 | **採用候補** (`ParserConfig.python_version` を渡せる) |
| `pyright --outputjson --skipunannotated <path>` | annotation のない関数を skip | 不採用 (解析対象を間引くと TypeDep が漏れる) |

**§2.2 結論 (D-08 解答):**

```
pyright \
  --outputjson \
  --pythonversion <ParserConfig.python_version> \
  -p <tmpdir>/pyrightconfig.json \
  <tmpdir>/<module_name>.py
```

- `--outputjson` — 唯一の JSON-stable mode
- `--pythonversion` — `ParserConfig.python_version` を伝達 (default `"3.12"`)
- `-p <pyrightconfig.json>` — adapter が tmpdir に `{"reportMissingImports": "error", "reportMissingTypeArgument": "warning"}` を書き出し、 警告レベルを caller 環境から独立化する (PyrightAdapter 内部でも別途 pyrightconfig.json を書く決定論)

`-p` flag は **caller 環境の `pyproject.toml` / `pyrightconfig.json` を pyright が auto-load しないように上書きする** という副次目的が重要 (Phase 2 実機検証で pyright が project root の `pyproject.toml` を自動 detect していたため、 caller 環境依存を排除する必要)。

### §2.3 推奨 TypeDep 生成 algorithm (本研究の中心提案)

CONTEXT.md D-07 の「pyright JSON → TypeDep 直接 mapping」は実機検証で **不可能** と判明した。 代替案として、 **stdlib `ast` で TypeDep を抽出し、 pyright を `resolved` flag の判定者として使う** 設計を planner に推奨する。 これは Layer M bisimulation の決定論性と「pyright[nodejs]==1.1.409 で完結」の両方を満たす。

**Algorithm (擬似コード):**

```python
def extract(cav: CAV, config: ParserConfig) -> list[TypeDep]:
    # Step 1: stdlib ast で TypeDep raw 抽出 (v0.1.0 type_dep_builder.py と同じ logic)
    module = cav.payload  # ast.Module
    raw_deps = _ast_walk_for_type_deps(module, cav.path)
    # raw_deps: [TypeDep(source="<module>", target="<symbol>", kind="imports"/"uses"), ...]

    # Step 2: pyright を起動して generalDiagnostics を収集
    from lib_code_parser.adapters.pyright import PyrightAdapter
    adapter = PyrightAdapter(python_version=config.python_version)
    diagnostics = adapter.execute(cav.path, raw_content=_serialize_cav_payload(cav))
    # diagnostics: list[PyrightDiagnostic(file, severity, message, line, character, rule)]

    # Step 3: 各 raw_dep に resolved flag を annotate
    # 解析した source 行 (= import 文の line) に reportMissingImports diagnostic が
    # 発火していないなら、 その import は pyright が解決成功とみなしている。
    unresolved_lines = {
        d.range_start_line for d in diagnostics if d.rule == "reportMissingImports"
    }
    result = []
    for dep in raw_deps:
        result.append(dep.model_copy(update={
            "resolved": dep.source_line not in unresolved_lines
        }))

    # Step 4: DET-04 sort key で固定 sort
    result.sort(key=lambda d: (d.source, d.target, d.kind))
    return result
```

(注: `TypeDep` model に `resolved: bool` field を追加するか、 `kind` の値域を `Literal["imports_resolved", "imports_unresolved", "uses"]` に拡張するかは planner 判断。 `TypeDep` model は現状 `source: str / target: str / kind: str` で `kind` は free-form str なので、 D-14 同様 model field 追加が現実解。 ContractInfo と同様の model 拡張パターンに揃える。)

**D-07 「subkey 抽出」要件への準拠:**

| D-07 要件 | 解釈 / 実装 |
|----------|------------|
| `--outputjson` の `TypeDep` 生成に必要な subkey のみ抽出 | `generalDiagnostics[].file`、 `generalDiagnostics[].rule`、 `generalDiagnostics[].range.start.line` の 3 つを抽出。 残り (severity, message, character offset, end position) は破棄 |
| `generalDiagnostics` は破棄 | **本研究で invalidate** — `generalDiagnostics` こそが唯一の有用データ、 「破棄」できない |
| file path は forward-slash 正規化 | `pathlib.PurePosixPath(file_path.replace("\\", "/"))` で実機の Windows path (`c:\\Users\\...`) を `c:/Users/...` に変換 |
| tmpdir prefix を strip | tmpdir path を文字列 prefix で startswith 判定 → strip して caller が渡した `path` 文字列に置換 |
| sort key は `(node_id, type_ref)` | TypeDep の `node_id` は `source` 相当、 `type_ref` は `target` 相当。 `(source, target, kind)` で sort |
| `generalDiagnostics` 外には何もない | (本研究の指摘) |

**file path 抽出のための tmpdir handling:**

```python
def _normalize_file_path(diagnostic_file: str, tmpdir: str, caller_path: str) -> str:
    # Step A: forward-slash normalize
    normalized = diagnostic_file.replace("\\", "/")
    # Step B: tmpdir prefix を caller_path に置換
    tmpdir_normalized = tmpdir.replace("\\", "/")
    if normalized.startswith(tmpdir_normalized):
        # tmpdir/{module_name}.py → caller の path
        return caller_path
    return normalized
```

### §2.4 DET-03 env var (env injection sanity check)

`PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` が正しい変数名であることを RobertCraigie/pyright-python 公式 README で確認した [CITED: github.com/RobertCraigie/pyright-python]。 加えて、 本研究実機で:

- `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409 pyright --version` → `pyright 1.1.409` を出力 (動作確認)
- `pyright --version` (env なし) → `pyright 1.1.408` (現 install version) を出力
- env なしでも stderr に `WARNING: there is a new pyright version available (v1.1.408 -> v1.1.409). Please install the new version or set PYRIGHT_PYTHON_FORCE_VERSION to 'latest'` が出る

**DET-03 に必要な full env (PyrightAdapter `extra_env`):**

```python
extra_env = {
    "PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409",        # DET-03 必須
    "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1",            # stderr の version warning を抑止 (決定論的 stderr)
}
```

`PYRIGHT_PYTHON_IGNORE_WARNINGS=1` を併設しないと、 caller 環境で新 pyright がリリースされた瞬間 stderr に warning が混入し、 stderr が決定論的でなくなる (DET-01 byte-identical の前提を環境状態に依存させる)。 これは Phase 2 で defensive に追加すべき。

**Phase 1 `adapters/base.py` の `_DETERMINISTIC_ENV` との関係:**

```python
# adapters/base.py (Phase 1 既存) には既に下記が設定済み
_DETERMINISTIC_ENV: dict[str, str] = {
    "LC_ALL": "C",
    "LANG": "C",
    "PYTHONHASHSEED": "0",
    "PYTHONIOENCODING": "utf-8",
}

# PyrightAdapter は extra_env で pyright 固有を上層に重ねる
extra_env = {
    "PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409",
    "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1",
}
result = run_subprocess(argv, cwd=tmpdir, timeout=60.0, extra_env=extra_env)
```

caller が `extra_env` で別の `PYRIGHT_PYTHON_*` を上書きする余地は閉じる (PyrightAdapter は固定で上記 2 値を hard-code し、 上位からの override を許さない設計を推奨)。

---

## Pydantic Validator AST Detection

(本節は D-11 の確認 + v0.1.0 の実証バグ 2 件の修正方針)

### §3.1 v0.1.0 `contract_extractor.py` の実証検証 (本研究実機)

v0.1.0 の `_get_decorator_name` 関数を fixture で fire し、 6 edge case を実機で確認した。

| Case | 入力 source | v0.1.0 検出 | 期待 (Phase 2) |
|------|------------|------------|----------------|
| **C1: 単純 Name** `@validator("x")` | `from pydantic import validator` | ✓ 検出 → `vfx` precondition、 source_kind 未設定 | ✓ 検出 → source_kind=`pydantic_validator` |
| **C2: 属性 Attribute** `@pydantic.field_validator("x")` | `import pydantic` | ✓ 検出 (decorator.attr fallback で `field_validator` 名抽出) | ✓ 検出 → source_kind=`pydantic_field_validator` |
| **C3: Alias import** `@fv("x")` | `from pydantic import field_validator as fv` | ✗ **未検出** (alias 解決していない、 v0.1.0 のバグ) | ✓ 検出すべき → source_kind=`pydantic_field_validator` |
| **C4: `@root_validator`** | `from pydantic import root_validator` | ✗ **未検出** (`_PRECONDITION_DECORATORS` / `_INVARIANT_DECORATORS` に未登録、 v0.1.0 のバグ) | ✓ 検出 → source_kind=`pydantic_model_validator` (D-11 semantic equivalent) |
| **C5: decorator chain** `@field_validator @classmethod` | 標準 Pydantic v2 idiom | ✓ 検出 (decorator_list を順次走査、 first match で break) | ✓ 同等動作 |
| **C6: factory call** `@validator("x", pre=True)` | 標準 Pydantic idiom | ✓ 検出 (decorator が `ast.Call` の場合 `func.id` を取得) | ✓ 同等動作 |
| **C7: `__post_init__` in any class** | 非 dataclass class でも | ✓ 検出するが unconditional に Pydantic 扱い (v0.1.0 のバグ) | ✓ 検出 → source_kind=`dataclass_post_init` (AST-04 で明示区別) |

実機 fixture 出力 (本研究実機):

```python
# Test 1 (C3): @fv("x") -- 未検出
{}

# Test 2 (C2): @pydantic.field_validator("x") -- 検出
{'m.Foo': ContractInfo(node_id='', source_kind='pydantic_validator', preconditions=['vfx'], invariants=[], postconditions=[])}

# Test 3 (C4): @root_validator -- 未検出
{}

# Test 4 (C5): @field_validator @classmethod -- 検出
{'m.Foo': ContractInfo(node_id='', source_kind='pydantic_validator', preconditions=['vfx'], invariants=[], postconditions=[])}

# Test 5 (C6): @validator("x", pre=True) -- 検出
{'m.Foo': ContractInfo(node_id='', source_kind='pydantic_validator', preconditions=['vfx'], invariants=[], postconditions=[])}

# Test 6 (C7): non-dataclass __post_init__ -- 検出 (unconditional)
{'m.PlainClass': ContractInfo(node_id='', source_kind='pydantic_validator', preconditions=['__post_init__'], invariants=[], postconditions=[])}
```

### §3.2 Phase 2 推奨 decorator detection algorithm

v0.1.0 の `_get_decorator_name(decorator)` を流用しつつ、 (a) alias 解決 (C3) と (b) `@root_validator` 認識 (C4) を追加。 さらに source_kind を decorator base name から直接 derive する。

```python
# 推奨: extractors/primitives/contracts.py 内
_DECORATOR_TO_SOURCE_KIND: dict[str, str] = {
    "validator": "pydantic_validator",
    "field_validator": "pydantic_field_validator",
    "model_validator": "pydantic_model_validator",
    "root_validator": "pydantic_model_validator",  # D-11 semantic equivalent
}


def _resolve_decorator_aliases(module: ast.Module) -> dict[str, str]:
    """Build {local_alias: canonical_name} mapping from import statements.

    例: `from pydantic import field_validator as fv` → {"fv": "field_validator"}
    例: `from pydantic import field_validator` → {"field_validator": "field_validator"}
    例: `import pydantic` → {} (attribute access は detect logic 側で対応)
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            # `from pydantic import X as Y` の場合のみ alias を貼る
            # (本 lib は pydantic 由来でない同名 decorator を無視するため
            #  `from pydantic import ...` でガードする)
            if node.module == "pydantic" or (node.module or "").startswith("pydantic."):
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    aliases[local_name] = alias.name  # alias name → canonical name
    return aliases


def _get_decorator_canonical_name(
    decorator: ast.expr,
    aliases: dict[str, str],
) -> str:
    """Return the canonical pydantic decorator name (after alias resolution), or ''."""
    raw_name = _get_decorator_name(decorator)  # v0.1.0 logic 流用
    return aliases.get(raw_name, raw_name)


def _detect_post_init(item: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return item.name == "__post_init__"
```

**Phase 2 で `__post_init__` を unconditional Pydantic 扱いせずに `dataclass_post_init` source_kind に分離する** ことで AST-04 success criteria 「verifier が `__post_init__` を unconditional Pydantic 扱いしないこと」を満たす (D-13)。

### §3.3 D-11 mapping 表の確認 (本研究の支持)

CONTEXT.md D-11 の mapping 表は Pydantic v2 公式 docs と整合する [CITED: pydantic.dev/docs/validation/latest/concepts/validators/]:

- `@field_validator` / `@model_validator` は Pydantic v2 active decorator (本研究 WebFetch で確認、 factory 形式 `@field_validator('field')` が standard)
- `@validator` / `@root_validator` は v1 deprecated alias (公式 docs では v2 docs に明示なし = deprecated)
- `@root_validator` を `@model_validator` バケットに集約することは Pydantic v1→v2 migration guide の semantic でも整合 (v1 root_validator は v2 model_validator の前身)

decorator chain `@field_validator @classmethod` (C5) は Pydantic v2 標準 idiom であり、 v0.1.0 logic はすでに対応している (decorator_list を順次走査、 マッチした時点で break)。 Phase 2 でも同 logic を保持。

### §3.4 D-12 集約粒度 (β) と D-14 model 拡張の planner ガイド

D-12 (β) 「各 contract entry に source_kind 付与」 + D-14 「`ContractInfo` 既存 model 拡張」を実装するには、 Phase 1 で確定済みの `models/primitives/contracts.py` の現状を base にして field 構造を再設計する必要がある。

**Phase 1 完了時点の `ContractInfo` (本研究実機読取):**

```python
class ContractInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node_id: str = ""
    source_kind: Literal[
        "pydantic_validator",
        "pydantic_model_validator",
        "pydantic_field_validator",
        "dataclass_post_init",
    ] = "pydantic_validator"
    preconditions: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
```

Phase 1 model は **class 単位で 1 つの source_kind を持つ** 構造 (D-12 α 寄り)。 D-12 (β) 「**各 contract entry に source_kind**」を実装するには、 model 構造を「class 単位の `ContractInfo` が複数の `ContractEntry` を保持する」形に変更する必要がある。

**planner への提案 (Phase 2 で D-14 を満たす model 拡張案):**

```python
# 提案案 A: ContractEntry を新規追加、 ContractInfo に list[ContractEntry] を持たせる
class ContractEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str  # 関数名 (e.g., "validate_status" / "__post_init__")
    source_kind: Literal[
        "pydantic_validator",
        "pydantic_model_validator",
        "pydantic_field_validator",
        "dataclass_post_init",
    ]
    kind: Literal["precondition", "invariant", "postcondition"]  # 既存 3 list 構造の代替
    decorator_name: str = ""  # canonical name (alias 解決後)
    line_no: int = 0  # SourceRange 同等
    body_excerpt: str = ""  # CONTEXT.md D-12 言及の "body_excerpt"


class ContractInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node_id: str = ""
    entries: list[ContractEntry] = Field(default_factory=list)
    # (legacy: preconditions / invariants / postconditions list は廃止)

    @computed_field  # 後方互換 helper (optional)
    @property
    def preconditions(self) -> list[str]:
        return [e.name for e in self.entries if e.kind == "precondition"]
    # ... 同様 invariants / postconditions
```

これは breaking change (Phase 1 model の 3 list 構造を破壊する) なので、 Phase 2 D-01 / D-02 「clean break」の枠内で許容される。

ただし planner は次の 2 案も比較検討してから決定する:

- **案 B**: 既存 `preconditions` / `invariants` / `postconditions` を `list[str]` のままにし、 並列に `entries: list[ContractEntry]` を追加 (リダンダント、 SCH-02 `extra="forbid"` 下でも model field 追加なので問題なし)。 「(β) 各 entry に source_kind」を満たしつつ後方互換も保つ。
- **案 C**: 案 A を採用し、 `@computed_field` で後方互換 helper を提供 (callers が `ci.preconditions` を読めば list[str] が返る)。 ただし Phase 2 D-01 clean break 方針なら helper 不要。

**Phase 2 planner は 3 案の比較を `02-DISCUSSION-LOG.md` に追加してから最終決定すること** を推奨する (CONTEXT.md D-14 は「具体的 field 名・list 構造は Phase 2 planner が決定」と委譲している)。

---

## Internal CallGraph Resolution Rules

(本節は AST-02 Claude's Discretion #1 — 解像度 rule の v0.1.0 baseline + Phase 2 推奨)

### §4.1 v0.1.0 `callgraph_builder.py` の実機解像度 (本研究)

7 fixture を v0.1.0 `build_callgraph` で fire した実機結果:

| Case | source | v0.1.0 emit | 解像度 rule |
|------|--------|------------|-------------|
| **CG1: `self.foo()`** in method | `class Foo: def bar(self): self.baz()` | `(m.Foo.bar, baz)` | callee は **bare `baz`** (Class.baz でも self.baz でもない) — `_get_call_name` が `func.attr` を返すため |
| **CG2: chain `a.b().c()`** | `def outer(): a.b().c()` | `(m.outer, c)`, `(m.outer, b)` | **2 edges 発火** — `ast.walk` が Call ノードを 2 つ訪問するため (`a.b()` と `.c()`) |
| **CG3: imported call `helper()`** | `from other import helper; def outer(): helper(); other.helper()` | `(m.outer, helper)` × 2 | **重複 edge** が emit される (dedup なし)。 cross-module resolution **なし** — `helper` も `other.helper` も同じ `helper` に解決 |
| **CG4: nested function** | `def outer(): def inner(): leaf(); inner()` | nodes=`['m.outer']`、 edges=`(m.outer, leaf), (m.outer, inner)` | **nested function を node に登録しない** (top-level/method のみ)、 callee は **outer に flatten** |
| **CG5: @staticmethod / @classmethod** | `class Foo: @staticmethod def smethod(): ...` | nodes=`['m.Foo', 'm.Foo.smethod', 'm.Foo.cmethod']` | decorator 無視 (FunctionDef として扱う)、 nodes 登録は normal method と同じ |
| **CG6: edge order** | `def b(): z(); a(); m()` | edges=`(m.b, z), (m.b, a), (m.b, m)` | **emission order = AST 出現順、 未 sort** |
| **CG7: deep attribute `a.b.c.d()`** | `def outer(): a.b.c.d()` | `(m.outer, d)` | 1 edge — innermost Call (`.d()`) のみ、 中間 attribute access は Call ノードでないため walk 対象外 |

**重要な発見:**

- **DET-04 違反**: v0.1.0 emission は `(caller, callee)` lexicographic sort されていない。 Phase 2 で sort を追加する必要がある (ROADMAP success criteria 2 invariant)。
- **重複 edge 許容**: CG3 同様、 同じ `(caller, callee)` ペアが複数回 emit される。 sort 後に dedup するかは planner 判断。
- **node 重複防止**: `CallGraph.nodes` は `list(dict.fromkeys(nodes))` で挿入順保持 + 重複除去 (v0.1.0 既存 behavior)。

### §4.2 Phase 2 推奨 (v0.1.0 parity + DET-04 sort 追加)

ROADMAP success criteria 2 が要求するのは「`(caller, callee)` lexicographic sort」のみで、 解像度の表現幅は規定なし。 **最低リスク戦略 = v0.1.0 解像度を完全継承 + emit 時に sort を追加** を推奨する:

```python
# extractors/primitives/callgraph.py 推奨実装の骨子
def extract(cav: CAV, config: ParserConfig) -> CallGraph:
    module = cav.payload  # ast.Module
    module_name = get_module_name(cav.path)
    nodes: list[str] = []
    edges: list[CallEdge] = []

    # ===== v0.1.0 logic そのまま継承 =====
    for top_node in module.body:
        if isinstance(top_node, ast.ClassDef):
            class_id = f"{module_name}.{top_node.name}"
            nodes.append(class_id)
            for item in top_node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_id = f"{module_name}.{top_node.name}.{item.name}"
                    nodes.append(method_id)
                    for callee in _collect_calls(item.body):  # v0.1.0 walk logic
                        edges.append(CallEdge(caller=method_id, callee=callee))

    for top_node in module.body:
        if isinstance(top_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_id = f"{module_name}.{top_node.name}"
            nodes.append(func_id)
            for callee in _collect_calls(top_node.body):
                edges.append(CallEdge(caller=func_id, callee=callee))

    # ===== Phase 2 で追加する DET-04 sort =====
    edges.sort(key=lambda e: (e.caller, e.callee))
    # (planner 判断: dedup するなら `edges = list({(e.caller, e.callee) for e in edges})` 後に再構築)

    return CallGraph(nodes=list(dict.fromkeys(nodes)), edges=edges)
```

### §4.3 解像度拡張 (Phase 3 入口で再評価、 Phase 2 では deferred)

Phase 3 の DIA-02 (sequence diagram) が「`self.foo()` を `Class.foo` に resolve できる」call graph を要求すれば、 v0.1.0 解像度では足りない。 ただし CONTEXT.md は「v0.1.0 parity 優先で実装し、 Phase 3 (DIA-02 sequence diagram) 着手時に call graph 表現力の不足が露呈すれば拡張を検討」と明示しており、 Phase 2 では **v0.1.0 解像度を継承する** ことが planner の安全策。

将来拡張する場合の候補 (Phase 3 issue として deferred):

1. **`self.foo()` → `Class.foo` 解決**: 当該 method の enclosing class 名を持って bare name を補完する。 AST walk 時に enclosing class context を track すれば実装可能。
2. **import 文経由の cross-module resolution**: `from other import helper; helper()` → `(caller, other.helper)`。 import alias table を引き、 bare name → fully-qualified name に解決。
3. **chain call の edge 分解 rule の固定**: v0.1.0 は 2 edges を emit するが、 「`a.b().c()` で `c` は `a.b()` の結果に対する method 呼び出し」という意味論を捉えるには 1 edge `(caller, c)` のみが正しい解釈とも言える。 ROADMAP 上は規定なし。

これら 3 候補は Phase 3 で「sequence diagram から逆算した必要性」を起点に planner が再評価する (Phase 2 では扱わない)。

---

## AST-05 One-Parse Enforcement Strategy

(本節は AST-05 Claude's Discretion #2 — hard gate test の primary + backup 選定)

### §5.1 3 候補の比較

| 候補 | 戦略 | 検出能力 | 偽陰性 / 偽陽性 | コスト |
|------|------|---------|---------------|--------|
| **(i) monkeypatch `ast.parse`** | test 内で `monkeypatch.setattr("ast.parse", spy)` → executor 実行 → `assert spy.call_count == 1` | 動的・実行時。 extractor が `ast.parse` を呼ぶ瞬間を catch | 偽陰性: monkeypatch 適用範囲外で parse された場合 (`compile()` 経由など)。 偽陽性: rare | 中 (test 1 件) |
| **(ii) grep 静的 gate** | `subprocess.run(["grep", "-rn", "ast\\.parse", "lib_code_parser/extractors/"])` → empty を assert | 静的・コード走査。 `ast.parse(` 文字列の出現を禁止 | 偽陰性: `from ast import parse` などの alias 使用。 偽陽性: comment / docstring 内に `ast.parse` 文字列 | 低 (test 1 件、 既存 `test_no_duplicate_module_name_helper` と同形式) |
| **(iii) 構造制約 (extractor signature)** | extractor signature が `def extract(cav: CAV, config: ParserConfig)` のみ。 `cav.payload` を pull するのみで `ast.parse` を呼ぶ余地なし | 静的・型システム由来 (実装慣習) | 偽陰性: signature 内で `import ast; ast.parse(...)` を呼べば破れる。 偽陽性: なし | 0 (test なし、 architecture が保証) |

### §5.2 推奨組み合わせ

**Primary = (ii) grep 静的 gate**、 **Backup = (i) monkeypatch 動的 gate** を併用、 **Foundation = (iii) 構造制約**

理由:
- (ii) は **既存 `test_no_duplicate_module_name_helper` と同形式** (Phase 1 parity test に組み込まれている `subprocess.run(["grep", ...])` pattern を再利用)。 メンテナンスコスト最小、 PR 時に diff で見える、 結果が deterministic。
- (i) は test 実行時に発火するので「現実のデモ」として強い証拠。 (ii) の偽陰性 (alias 利用) を catch する。
- (iii) は test 不要だが、 docs/09-extending.md (Phase 1) に追記すべき。 「`extractors/primitives/*.py` は `ast.parse` を import / call してはならない、 reason: AST-05 invariant」を docs 上で enforce。

実装 sketch:

```python
# tests/parity/test_ast_05_one_parse.py (Phase 2 新規追加)

# Primary: (ii) static grep
def test_no_ast_parse_in_extractors() -> None:
    """AST-05 hard gate: no extractor module calls ast.parse — the Frontend owns it."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    extractors = repo_root / "lib_code_parser" / "extractors"
    result = subprocess.run(
        ["grep", "-rn", "-E", r"ast\.parse\(|from ast import parse",
         str(extractors), "--include=*.py"],
        check=False, capture_output=True, text=True,
    )
    matches = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(matches) == 0, (
        f"AST-05 violation — ast.parse must not appear in extractors/. "
        f"Frontends/python.py is the single parse site. Found:\n" + "\n".join(matches)
    )


# Backup: (i) dynamic monkeypatch
def test_single_parse_per_execute(monkeypatch: pytest.MonkeyPatch) -> None:
    """AST-05 hard gate (dynamic): executor invokes ast.parse exactly once per execute()."""
    import ast
    from lib_code_parser import CodeParserExecutor
    from lib_code_parser.models.infrastructure.config import ParserConfig

    real_parse = ast.parse
    call_count = 0
    def spy(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return real_parse(*args, **kwargs)
    monkeypatch.setattr(ast, "parse", spy)

    exe = CodeParserExecutor()
    exe.execute(
        ParserConfig(artifact_type="code", executor_lib="lib_code_parser", language="python"),
        b"class Foo:\n    def bar(self): pass\n",
        "foo.py",
    )
    assert call_count == 1, (
        f"AST-05 violation: ast.parse called {call_count} times per execute(); "
        f"expected 1. Frontend should own the single parse."
    )
```

(注: (i) は `ast.parse` を直接 monkeypatch する。 frontends/python.py が `from ast import parse; parse(source)` の形で呼ぶ場合は monkeypatch が外れるリスクあるが、 (ii) の grep がそれを catch する。 両方併用で防御深度を確保。)

---

## TRC-02 Docstring Template

(本節は TRC-02 Claude's Discretion — module docstring の REQ-ID 宣言形式)

### §6.1 既存 v0.1.0 docstring との整合性

v0.1.0 `ast_extractor.py` module-level docstring (本研究実機読取):

```python
"""AST-based function/class/method extractor for Python source code."""
```

REQ-ID 宣言なし — TRC-02 充足のため Phase 2 で追加する。

Phase 1 で生成済みの primitive model docstring (本研究実機読取、 例:):

```python
# models/primitives/contracts.py
"""Primitive contract model — ContractInfo with source_kind discriminator per AST-04.

Distinguishes Pydantic validator decorators from dataclass ``__post_init__`` per
D-04 substrate.

Traces: SCH-02, AST-04.
"""
```

Phase 1 既に `Traces: REQ-ID` 行を docstring 末尾に置く慣習が確立されており、 TRC-03 regex `Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)` で抽出可能。

### §6.2 推奨 template

TRC-02 の「実装 REQ-ID 宣言」と TRC-03 の「Traces: 行抽出」を分離する形式を推奨:

```python
"""<one-line module purpose>.

<optional: longer description if needed>

Implements: AST-NN[, AST-MM]
Traces: AST-NN, US-NN[, ...]
"""
```

**`Implements:`** 行は TRC-02 専用 (人間と plan-checker が読む)、 **`Traces:`** 行は TRC-03 専用 (regex 抽出 target)。 両者を分けることで:
- TRC-03 regex (v0.1.0 から不変) は `Traces:` 行のみ拾う
- TRC-02 plan-checker は `Implements:` 行を grep で確認
- 同じ REQ-ID が両方に出現するのは OK (重複情報、 異なる用途)

### §6.3 4 extractor の docstring 例

```python
# extractors/primitives/functions.py
"""Python AST → FunctionNode extractor (pure CAV consumer).

Walks the CAV's ast.Module payload once and emits FunctionNode entries for
each class, method, and top-level function with kind/params/return_type/
docstring/trace_tags/source_range populated.

Implements: AST-01, AST-05
Traces: AST-01, AST-05, US-01, US-22
"""

# extractors/primitives/callgraph.py
"""Python internal call graph extractor (pure CAV consumer, no GPL deps, no subprocess).

Walks the CAV's ast.Module payload once and emits (caller, callee) edges
sorted lexicographically by (caller, callee) per DET-04.

Implements: AST-02, AST-05, DET-04
Traces: AST-02, AST-05, DET-04, US-01, US-22, US-25
"""

# extractors/primitives/type_deps.py
"""Python type dependency extractor (CAV + pyright adapter).

Combines stdlib ast walk over the CAV's ast.Module payload with pyright
subprocess (via PyrightAdapter) to annotate each TypeDep with resolved=True
when pyright did not flag the import as missing.

Implements: AST-03, AST-05, DET-03
Traces: AST-03, AST-05, DET-03, US-01, US-22
"""

# extractors/primitives/contracts.py
"""Python contract extractor (Pydantic validators + dataclass __post_init__).

Walks the CAV's ast.Module payload once and emits ContractInfo entries with
source_kind discriminator (pydantic_validator / pydantic_field_validator /
pydantic_model_validator / dataclass_post_init).

Implements: AST-04, AST-05
Traces: AST-04, AST-05, US-01, US-22
"""

# frontends/python.py
"""Python Frontend — ast.parse() the source exactly once and emit CAV envelope.

This is the SINGLE site in lib_code_parser/extractors/ + frontends/ that
calls ast.parse(). All primitive extractors consume cav.payload (already-
parsed ast.Module) and never re-parse.

Implements: AST-05
Traces: AST-05, ARC-02
"""

# adapters/pyright.py
"""Pyright subprocess adapter (Pydantic-validated JSON parser + canonicalizer).

Writes raw_content to internal tmpdir, runs pyright --outputjson with
PYRIGHT_PYTHON_FORCE_VERSION=1.1.409 + PYRIGHT_PYTHON_IGNORE_WARNINGS=1
extra_env, parses generalDiagnostics into a typed Pydantic model. Fail-loudly
on subprocess failure / timeout / JSON parse error per D-06.

Implements: AST-03, DET-03
Traces: AST-03, DET-03, ARC-03, DET-05
"""
```

### §6.4 TRC-03 trace tag extraction parity

v0.1.0 `_extract_trace_tags` 正規表現 (本研究実機読取):

```python
pattern = re.compile(r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)", re.MULTILINE)
```

これを **Phase 2 `extractors/primitives/functions.py` 内に同一文字列で移植** する (1 文字も変えない、 verbatim copy)。 parity test として v0.1.0 acceptance test FR-05 (`tests/acceptance/test_fr05_trace_tags.py`) を typed ParserConfig 経由で fire し、 同じ `EXAMPLE_SOURCE` で同じ `TraceTag` 出力が得られることを確認する (TRC-03 success criteria)。

---

## v0.1.0 Parity Baselines

(本節は §7 = 各 primitive extractor の v0.1.0 baseline 行動と Phase 2 の差分)

### §7.1 AST-01 `extract_functions` parity

| 観点 | v0.1.0 emit | Phase 2 推奨 emit | 差分 |
|------|-------------|-------------------|------|
| node_id format | `<module_name>.<name>` (class)、 `<module_name>.<class>.<method>` (method)、 `<module_name>.<func>` (top-level) | 同 | なし |
| `kind` discriminator | `"class"` / `"method"` / `"function"` | 同 | なし |
| `params` (`ParamInfo`) | `args.args` から `skip_self_cls=True` (method) / `False` (top-level) で抽出 | 同 | なし |
| `return_type` | `_extract_annotation(node.returns)` → `ast.unparse` 結果 | 同 | なし |
| `docstring` | `ast.get_docstring(node) or ""` | 同 | なし |
| `trace_tags` | `_extract_trace_tags(docstring)` で正規表現抽出 | 同 (TRC-03 parity) | なし |
| `source_range` | `start_line=node.lineno, end_line=node.end_lineno or node.lineno` | 同 | なし |
| **emit order** | 1st pass: classes + methods、 2nd pass: top-level functions、 同 pass 内は AST 出現順 | 同 (planner 判断: DET-04 sort 候補だが v0.1.0 parity 維持なら未 sort、 ROADMAP success criteria 1 は sort 規定なし) | 要確認 |
| **`signature`** | `extract_functions(source: str, path: str) -> list[FunctionNode]` | `def extract(cav: CAV, config: ParserConfig) -> list[FunctionNode]` | **breaking change** (D-01 clean break で許容) |

acceptance test `tests/acceptance/test_fr01_function_extraction.py` (v0.1.0、 6 + 6 + 5 = 17 assertion) を Phase 2 で typed ParserConfig + CAV 経由に書き換える。 ROADMAP success criteria 1 と D-04 fixture snapshot test の base.

### §7.2 AST-02 `build_callgraph` parity

§4 でカバー済み。 v0.1.0 解像度を継承 + DET-04 sort を emit 時に追加。

`tests/acceptance/test_fr02_callgraph.py` (v0.1.0、 5 + 2 + 2 = 9 assertion) を Phase 2 で書き換え。 注意: `test_create_order_calls_calculate_total` は `(caller, "_calculate_total")` を assert しており、 sort 追加後も該当 edge は存在し続けるため pass する (sort は edge を消さない)。

### §7.3 AST-03 `build_type_deps` parity (algorithm shift あり)

v0.1.0 は **internal AST walk のみ** で TypeDep を抽出。 Phase 2 は **stdlib ast walk + pyright resolved annotation** に変更 (本研究 §2.3 で詳細)。 これは algorithm shift であり parity の意味が変わる。

| 観点 | v0.1.0 emit | Phase 2 推奨 emit | 差分 |
|------|-------------|-------------------|------|
| Import statements | `ast.Import` → `TypeDep(source=module_name, target=alias.asname or alias.name, kind="imports")` | 同 + `resolved=True/False` flag | flag 追加 |
| `from X import Y` | `ast.ImportFrom` → `TypeDep(source=module_name, target=f"{from_module}.{Y}", kind="imports")` | 同 + `resolved=True/False` flag | flag 追加 |
| Type annotation | `ast.Name` / `ast.Attribute` walk → `TypeDep(source=module_name, target=name, kind="uses")` | 同 (uppercase-first heuristic 込み) | なし (v0.1.0 と同 walk logic) |
| Excluded names | `"None"`, `"True"`, `"False"` を除外 | 同 | なし |
| **`signature`** | `build_type_deps(source: str, path: str) -> list[TypeDep]` | `def extract(cav: CAV, config: ParserConfig) -> list[TypeDep]` | breaking change |
| **emit order** | AST walk order、 未 sort | DET-04 `(source, target, kind)` sort | sort 追加 |
| **新 field `resolved`** | なし | `bool` field (TypeDep model に追加要) | model 拡張 |

acceptance test `tests/acceptance/test_fr03_type_deps.py` (v0.1.0、 3 + 2 + 3 = 8 assertion) は基本 logic を維持するため pass する。 ただし `resolved` 検証は新 test を追加 (本研究 §7.6)。

### §7.4 AST-04 `extract_contracts` parity (model 拡張あり)

§3 でカバー済み。 v0.1.0 logic を base に (a) alias 解決 (C3 fix)、 (b) `@root_validator` 認識 (C4 fix)、 (c) `__post_init__` を `dataclass_post_init` source_kind に分離 (C7 修正)、 (d) D-12 (β) 集約粒度に基づく model 拡張、 を実装。

acceptance test `tests/acceptance/test_fr04_contracts.py` (v0.1.0、 4 + 1 + 3 = 8 assertion) は v0.1.0 model 前提なので Phase 2 model 変更後は **全面書き換え必要** (D-12 model 構造変更による)。 D-04 fixture snapshot test として置換。

### §7.5 TRC-03 trace tag parity (§6.4 と同)

`_extract_trace_tags` 正規表現を `extractors/primitives/functions.py` に verbatim 移植。 v0.1.0 acceptance test `tests/acceptance/test_fr05_trace_tags.py` で同一 output 確認。

### §7.6 Test fixture matrix (Phase 2 planner ガイド)

| Test | v0.1.0 status | Phase 2 action |
|------|--------------|---------------|
| `tests/conftest.py` `EXAMPLE_SOURCE` | 既存、 60 行 Python サンプル | **保持**、 D-04 snapshot test の入力に使用 |
| `tests/acceptance/test_fr01_function_extraction.py` | v0.1.0 import `from lib_code_parser.ast_extractor import extract_functions` | **書き換え** — `from lib_code_parser.extractors.primitives.functions import extract` に変更、 CAV 経由 |
| `tests/acceptance/test_fr02_callgraph.py` | 同様 | **書き換え** — sort 追加に伴う edge order assertion は順序非依存 (set 比較) を確認 |
| `tests/acceptance/test_fr03_type_deps.py` | 同様 | **書き換え** + `resolved` field assertion 追加 |
| `tests/acceptance/test_fr04_contracts.py` | 同様 | **全面書き換え** — D-12 model 変更で旧 assertion pattern が無効化 |
| `tests/acceptance/test_fr05_trace_tags.py` | 同様 | **書き換え** + 新 `Traces:` 行 module docstring に追加 |
| `tests/acceptance/test_fr06_disabled.py` | `enabled=False` 検証 | **書き換え** — typed ParserConfig 経由 |
| `tests/parity/test_v01_v02_compat.py` (Phase 1) | 11 test pass、 stub parity 含む | **再設計** — name surface 13 + no-duplication gate 保持、 stub JSON parity 廃止、 snapshot test 追加 (D-04) |
| `tests/parity/test_ast_05_one_parse.py` (新規) | — | **新規追加** (本研究 §5.2 で sketch 提示) |
| `tests/parity/test_snapshot_v01_fixture.py` (新規、 D-04) | — | **新規追加** — `EXAMPLE_SOURCE` を typed ParserConfig で実行した output JSON を fixture file (`tests/parity/fixtures/v01_snapshot.json`) と byte-identical 比較 |

---

## Validation Architecture

> `workflow.nyquist_validation` キーが `.planning/config.json` に存在しない場合は enabled として扱う。 本研究では `.planning/config.json` は存在しないので enabled と仮定。

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest >=8` ([VERIFIED: pyproject.toml `[project.optional-dependencies].dev`]) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) |
| Quick run command | `pytest tests/parity tests/acceptance -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AST-01 | FunctionNode 抽出 (class/method/function + params/return_type/docstring/trace_tags/source_range) | acceptance | `pytest tests/acceptance/test_fr01_function_extraction.py -x` | ✅ (要書換) |
| AST-02 | CallGraph emit、 `(caller, callee)` sort | acceptance + new unit | `pytest tests/acceptance/test_fr02_callgraph.py -x` + new unit test for sort assertion | ✅ + ❌ |
| AST-03 | TypeDep 抽出 + pyright resolved annotation | acceptance + adapter unit | `pytest tests/acceptance/test_fr03_type_deps.py tests/unit/test_pyright_adapter.py -x` | ✅ + ❌ |
| AST-04 | ContractInfo + source_kind 4 値 | acceptance | `pytest tests/acceptance/test_fr04_contracts.py -x` | ✅ (要全面書換) |
| AST-05 | 1 parse per execute() | parity (static + dynamic) | `pytest tests/parity/test_ast_05_one_parse.py -x` | ❌ (新規) |
| DET-03 | `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` 強制 | adapter unit | `pytest tests/unit/test_pyright_adapter.py::test_det_03_env_var_set -x` | ❌ (新規) |
| TRC-02 | extractor docstring に `Implements: AST-NN` 記載 | parity (static grep) | `pytest tests/parity/test_trc_02_docstring.py -x` | ❌ (新規) |
| TRC-03 | `Traces:` regex 動作 parity | acceptance | `pytest tests/acceptance/test_fr05_trace_tags.py -x` | ✅ (要書換) |

### Sampling Rate

- **Per task commit:** `pytest tests/parity -x -q` (高速、 全 hard gate)
- **Per wave merge:** `pytest tests/ -v` (full suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/parity/test_ast_05_one_parse.py` — AST-05 monkeypatch + grep dual gate
- [ ] `tests/parity/test_trc_02_docstring.py` — extractor module docstring `Implements: AST-NN` static gate
- [ ] `tests/parity/test_snapshot_v01_fixture.py` — D-04 shipped v0.1.0 fixture snapshot
- [ ] `tests/parity/fixtures/v01_snapshot.json` — Phase 2 emit 出力を fix した snapshot (Phase 2 実装後に commit)
- [ ] `tests/unit/test_pyright_adapter.py` — PyrightAdapter unit test (mock subprocess、 env var assertion、 JSON parse error path、 timeout path)
- [ ] `tests/unit/test_callgraph_sort.py` — AST-02 sort 動作の unit test
- [ ] `tests/parity/test_v01_v02_compat.py` — Phase 1 既存を再設計 (D-04 のとおり stub JSON parity 廃止 + snapshot test 追加)
- [ ] `tests/acceptance/test_fr0[1-6]_*.py` — 6 既存 acceptance を typed ParserConfig + CAV 経由に書き換え

---

## Security Domain

> `security_enforcement` キーが `.planning/config.json` に存在しない場合は enabled として扱う。 該当 key は存在しないので enabled と仮定。

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | 該当なし — 本 lib は無 I/O / 無 network / 無認証 (PROJECT.md §Constraints) |
| V3 Session Management | no | 同上 |
| V4 Access Control | no | 同上 |
| V5 Input Validation | **yes** | Pydantic v2 `model_config = ConfigDict(extra="forbid")` (SCH-02、 Phase 1 で全 model 適用済み) — Phase 2 で追加する `ContractEntry` 等にも extra="forbid" 必須 |
| V6 Cryptography | no | 該当なし — 暗号化処理なし |
| V12 File Handling | **yes** | `tempfile.TemporaryDirectory()` の自動 cleanup を確認 — context manager で必ず `__exit__` を呼ぶ。 Phase 1 `run_subprocess` の `cwd` 明示要件と合わせて、 PyrightAdapter が tmpdir 内で完結することを保証 |

### Known Threat Patterns for Python AST + subprocess stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Subprocess argv injection (pyright CLI に caller 由来文字列を流す) | Tampering | argv は `Sequence[str]` のみ (Phase 1 `run_subprocess` で `shell=False` enforced)、 caller-supplied `python_version` は `Literal[…]` で reject (典型: `--pythonversion "3.12; rm -rf /"` のような string injection を Pydantic Literal で防ぐ) |
| Subprocess timeout 無視 → hang | DoS | `run_subprocess(timeout=60.0)` 強制 (Phase 1 DET-05)、 Phase 2 で PyrightAdapter が override しないこと |
| Subprocess stdout buffer 満杯 → deadlock | DoS | `subprocess.run(capture_output=True)` を使用 (Phase 1 で Pitfall 3 として明示) |
| tmpdir 残骸 (cleanup 失敗) | Information disclosure (extraordinary) | `tempfile.TemporaryDirectory()` の context manager で `__exit__` 保証、 例外時も cleanup |
| Path traversal via caller-supplied `path` | Tampering | `path` は metadata のみ (TypeDep / FunctionNode の `node_id` derivation)、 file system に書き出さない。 PyrightAdapter は tmpdir 内で完結するため caller `path` を file system に解釈しない |
| Pickle / arbitrary code execution from JSON | RCE | `json.loads` のみ、 `pickle` / `marshal` / `eval` 一切使用しない |
| Pydantic ValidationError → uncaught exception | DoS via crash | D-06 fail-loudly 原則で `RuntimeError` に raise from、 caller が catch する責務 |

---

## Common Pitfalls

### Pitfall 1: pyright `--outputjson` の schema 誤解に基づく実装

**何が起きるか:** D-07 の前提通り「`generalDiagnostics` を破棄して型解決済み subkey を読み込む」 logic を書くと、 抽出するデータが 0 件で TypeDep が常に空になる。
**根本原因:** pyright `--outputjson` は diagnostics-only という事実が CONTEXT.md 段階で確認されていなかった。
**回避策:** 本研究 §2.3 の revised algorithm (stdlib ast walk + pyright resolved annotation) を採用する。
**早期警告:** Wave 1 T5 (PyrightAdapter unit test) で実 pyright を起動して JSON schema を再確認する test を最初に書く。 fixture に明らかな unresolved import を入れて `rule: "reportMissingImports"` の diagnostic が出ることを assert する。

### Pitfall 2: pyright wrapper の version drift (caller 環境依存)

**何が起きるか:** `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` を設定し忘れると、 caller 環境の `~/.cache/pyright-python/` 内に install された別 version (typically `latest`) が起動し、 stderr に `WARNING: there is a new pyright version available` が混入、 stdout の JSON schema も 1.1.410+ で field 追加される可能性がある。 DET-01 byte-identical の前提が壊れる。
**根本原因:** pyright-python は npm 経由で pyright を install するため、 wrapper script が pyright 本体の version を選ぶ。
**回避策:** PyrightAdapter の `extra_env` に `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` と `PYRIGHT_PYTHON_IGNORE_WARNINGS=1` を **必ず両方** 設定する (本研究 §2.4)。 PyrightAdapter unit test で `extra_env` が `subprocess.run` に正しく伝達されることを assert する。
**早期警告:** PyrightAdapter unit test で `subprocess.run` を mock し、 渡された `env` dict に上記 2 key が存在することを assert。

### Pitfall 3: tmpdir 内で pyright が caller 環境の `pyproject.toml` を auto-load

**何が起きるか:** pyright は cwd から上に向けて `pyproject.toml` を再帰探索し、 `[tool.pyright]` section を自動 load する。 本研究実機検証で、 tmpdir 配下で起動した pyright が `c:\work\agent_company\spec-reviewer-libs\lib-code-parser\pyproject.toml` を auto-load していることを確認した (verbose mode の "Loading pyproject.toml file at..." メッセージで判明)。 これにより caller 環境の pyright 設定が解析結果に混入し、 DET-01 byte-identical が壊れる。
**根本原因:** pyright の標準動作。
**回避策:** PyrightAdapter が tmpdir に `pyrightconfig.json` を書き出し、 `-p <tmpdir>/pyrightconfig.json` で明示指定する。 これで pyright は上位 `pyproject.toml` を探索しなくなる。 `pyrightconfig.json` 内容は固定 (`{"include": ["."], "reportMissingImports": "error", "reportMissingTypeArgument": "warning"}`)。
**早期警告:** PyrightAdapter unit test で「caller 環境に `pyproject.toml` がある状態でも tmpdir 内 fixture の解析結果が変わらない」ことを assert。

### Pitfall 4: chain call `a.b().c()` で意味論的に正しい edge 数 (Claude's Discretion #1)

**何が起きるか:** v0.1.0 は 2 edges (`(caller, c)`, `(caller, b)`) を emit。 Phase 3 sequence diagram が「`c` の前提として `b` が呼ばれた」ことを正しく rendering できるかは不明。
**根本原因:** AST walk が Call ノードを順次訪問するため、 chain 内の各 Call が独立 edge として扱われる。
**回避策:** Phase 2 では **v0.1.0 と同じ 2 edges 動作を保持** する (CONTEXT.md の Claude's Discretion 範囲、 ROADMAP success criteria 2 は edge 数を規定せず sort のみ規定)。 Phase 3 DIA-02 着手時に「sequence diagram で chain を正しく描画できるか」を判断、 必要に応じて Phase 3 で解像度拡張を別 issue として起票。
**早期警告:** v0.1.0 acceptance test FR-02 `TestCallGraphEdges` が chain call を含む fixture を持たないため、 Phase 2 で planner が「chain call の edge 数」を明示する unit test を新規追加する (`test_chain_call_emits_two_edges` 等)。 これにより future readers が現状動作を理解できる。

### Pitfall 5: `__post_init__` の dataclass 判定の精度

**何が起きるか:** Phase 2 D-11 「`__post_init__` → `dataclass_post_init`」は class-level `@dataclass` decorator の有無を見るべきかどうか規定なし。 v0.1.0 は unconditional に `__post_init__` を検出 (本研究 §3.1 C7)。 Phase 2 で `@dataclass` を見なければ「plain class の `__post_init__`」も `dataclass_post_init` になる。
**根本原因:** D-11 の mapping 表が decorator name 単位の判定で、 class 文脈を見ない。
**回避策:** Phase 2 では v0.1.0 と同じく **class-level decorator は見ず、 method 名のみで判定** する (D-11 simplicity 優先)。 `@dataclass` を見ない理由: (a) dataclass alias (`from dataclasses import dataclass as dc`) を解決する complexity と (b) 非 dataclass の `__post_init__` は実コードでは稀である (false positive 許容)。 D-13 の混在 case 自動サポート意図とも整合 (同 class 内に `@field_validator` と `__post_init__` 同居)。
**早期警告:** planner が 02-DISCUSSION-LOG.md に「`@dataclass` 文脈判定を入れるか」を明示し、 入れない場合の rationale を記録する。

### Pitfall 6: pyright subprocess の cold start cost が CI で問題

**何が起きるか:** pyright 1.1.409 の初回起動は本研究実機で 0.8-1.1 sec (node + typeshed load 含む)。 CI で 100+ ファイルを並列解析すると累積で長時間化。
**根本原因:** pyright は file-level でなく project-level analyzer であり、 起動コストが高い。
**回避策:** Phase 2 では「ファイルごとに PyrightAdapter を 1 回起動」を許容 (lib API は file-level)。 Phase 5 で caller (spec-reviewer pipeline) が batch して呼ぶ最適化を検討。 D-06 timeout 60s は十分なマージン。
**早期警告:** PyrightAdapter unit test で 60s timeout が正しく `subprocess.TimeoutExpired` → `RuntimeError` に raise from されることを assert。

### Pitfall 7: v0.1.0 acceptance test 書き換え時の signature mismatch

**何が起きるか:** v0.1.0 acceptance test は `extract_functions(source, path)` を直接呼ぶ。 Phase 2 で `extract(cav, config)` に変わるため、 test 内で CAV を作る必要がある。 「ast.parse を test 内で呼ぶ」 必要があり、 これは AST-05 hard gate (本研究 §5) と混乱を招く可能性がある。
**根本原因:** signature change による test side-effect。
**回避策:** test 内で `from lib_code_parser.frontends.python import build_cav` を import し、 `cav = build_cav(source.encode(), path, config)` 形で CAV を作る (Frontend を test fixture として使う)。 これにより test 内で直接 `ast.parse` を呼ばない、 AST-05 hard gate の意図と整合。
**早期警告:** Phase 2 planner が acceptance test 書き換え時に「`ast.parse` を test 内で直接呼んでいないか」を grep で確認する PR checklist 項目を入れる。

---

## Code Examples

verified pattern を Context7 / 公式 docs / 本研究実機で confirm したもののみ:

### §例 1: `frontends/python.py` — 1-parse Frontend (推奨実装)

```python
# Source: 本研究 — Phase 1 `_dispatch.FrontendFn` signature + CAV model
"""Python Frontend — ast.parse() the source exactly once and emit CAV envelope.

This is the SINGLE site in lib_code_parser/extractors/ + frontends/ that
calls ast.parse(). All primitive extractors consume cav.payload (already-
parsed ast.Module) and never re-parse.

Implements: AST-05
Traces: AST-05, ARC-02
"""
from __future__ import annotations

import ast

from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["build_cav"]


def build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV:
    """Parse raw_content exactly once into ast.Module and wrap in CAV envelope."""
    source = raw_content.decode("utf-8", errors="replace")
    module = ast.parse(source, filename=path)
    return CAV(language="python", path=path, payload=module)
```

### §例 2: `adapters/pyright.py` — PyrightAdapter (推奨実装の骨子)

```python
# Source: 本研究 §2 + Phase 1 SubprocessAdapter ABC
"""Pyright subprocess adapter."""
from __future__ import annotations

import json
import tempfile
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field

from lib_code_parser._paths import get_module_name
from lib_code_parser.adapters.base import SubprocessAdapter, run_subprocess


class PyrightDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file: str
    severity: str
    message: str
    rule: str = ""
    start_line: int
    end_line: int = 0


class PyrightOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    diagnostics: list[PyrightDiagnostic] = Field(default_factory=list)


_PYRIGHT_DET_ENV = {
    "PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409",
    "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1",
}


class PyrightAdapter(SubprocessAdapter):
    def __init__(self, python_version: str = "3.12") -> None:
        self.python_version = python_version

    def analyze(self, raw_content: bytes, path: str) -> PyrightOutput:
        """Write raw_content to tmpdir, run pyright, return parsed PyrightOutput."""
        module_name = get_module_name(path)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target = tmpdir_path / f"{module_name}.py"
            target.write_bytes(raw_content)
            config_path = tmpdir_path / "pyrightconfig.json"
            config_path.write_text(json.dumps({
                "include": ["."],
                "reportMissingImports": "error",
            }))

            argv = self.tool_argv(str(target))
            result = run_subprocess(
                argv, cwd=tmpdir, timeout=60.0, extra_env=_PYRIGHT_DET_ENV,
            )
            # Caller path に tmpdir prefix を置換するため tmpdir を覚えておく
            return self.parse_output(
                stdout=result.stdout, stderr=result.stderr,
                returncode=result.returncode, tmpdir=tmpdir, caller_path=path,
            )

    def tool_argv(self, target_path: str) -> Sequence[str]:
        return [
            "pyright",
            "--outputjson",
            "--pythonversion", self.python_version,
            "-p", str(Path(target_path).parent / "pyrightconfig.json"),
            target_path,
        ]

    def parse_output(
        self, stdout: str, stderr: str, returncode: int,
        tmpdir: str = "", caller_path: str = "",
    ) -> PyrightOutput:
        # D-06 fail-loudly
        if returncode not in (0, 1):  # 0 = clean, 1 = errors found (both valid)
            raise RuntimeError(
                f"pyright exited with code {returncode}: stderr={stderr[:500]}"
            )
        try:
            raw = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"pyright JSON parse failed: {e}; stdout={stdout[:500]}") from e

        diagnostics: list[PyrightDiagnostic] = []
        tmpdir_fwd = tmpdir.replace("\\", "/") if tmpdir else ""
        for d in raw.get("generalDiagnostics", []):
            file_path = d["file"].replace("\\", "/")
            if tmpdir_fwd and file_path.startswith(tmpdir_fwd):
                file_path = caller_path  # caller path に置換
            diagnostics.append(PyrightDiagnostic(
                file=file_path,
                severity=d.get("severity", ""),
                message=d.get("message", ""),
                rule=d.get("rule", ""),
                start_line=d["range"]["start"]["line"],
                end_line=d["range"]["end"]["line"],
            ))
        return PyrightOutput(version=raw["version"], diagnostics=diagnostics)
```

(注: 上記は骨子。 D-06 fail-loudly の error path、 PyrightOutput model field、 `execute` template method override は planner が詳細化する。)

### §例 3: `extractors/primitives/type_deps.py` — TypeDep + resolved annotation

```python
# Source: 本研究 §2.3 推奨 algorithm
"""Python type dependency extractor (CAV + pyright adapter).

Implements: AST-03, AST-05, DET-03
Traces: AST-03, AST-05, DET-03, US-01, US-22
"""
from __future__ import annotations

import ast

from lib_code_parser._paths import get_module_name
from lib_code_parser.adapters.pyright import PyrightAdapter
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig
from lib_code_parser.models.primitives.type_deps import TypeDep


def extract(cav: CAV, config: ParserConfig) -> list[TypeDep]:
    """Extract TypeDep list with pyright-resolved annotation.

    1. Walk ast.Module for Import / ImportFrom / type annotation type names.
    2. Run pyright via PyrightAdapter, get reportMissingImports diagnostics.
    3. Annotate each TypeDep with resolved=True if no missing-import dx hit.
    4. Sort by (source, target, kind) per DET-04.
    """
    module: ast.Module = cav.payload  # type: ignore[assignment]
    module_name = get_module_name(cav.path)
    raw_deps: list[TypeDep] = []
    line_for_dep: dict[int, list[int]] = {}  # dep idx -> [line numbers]

    # Step 1: ast walk for imports + annotations (v0.1.0 logic 流用)
    # ... (詳細は v0.1.0 type_dep_builder.py 流用、 line number を覚える)

    # Step 2: PyrightAdapter で diagnostics 取得
    raw_content = ast.unparse(module).encode("utf-8")
    # NOTE: ast.unparse は AST の再シリアライズ、 line 番号が source と一致しない可能性あり
    # production では cav に raw_content を carry させるか、 cav.payload を再 dump する設計を planner 判断
    adapter = PyrightAdapter(python_version=config.python_version)
    pyright_result = adapter.analyze(raw_content, cav.path)

    # Step 3: unresolved import 行を集合化
    unresolved_lines: set[int] = {
        d.start_line for d in pyright_result.diagnostics
        if d.rule == "reportMissingImports"
    }
    # Step 4: 各 raw_dep に resolved annotation + sort
    result = [
        d.model_copy(update={"resolved": d.line not in unresolved_lines})
        for d in raw_deps
    ]
    result.sort(key=lambda d: (d.source, d.target, d.kind))
    return result
```

(注: `raw_content` の生成方法 — `ast.unparse(cav.payload)` か、 CAV に元 `raw_content` を carry させるか — は planner 判断。 `ast.unparse` は AST round-trip だが空行 / コメント / docstring 修正で line number が変わる可能性あり、 これが pyright diagnostic の line number と乖離するリスク。 **より安全な設計: CAV model に `raw_content: bytes` field を追加する** (Phase 1 CAV model 変更が必要、 D-04 lock 違反)。 planner はこれを 02-DISCUSSION-LOG.md で再議論すべき。)

---

## State of the Art

| Old Approach (v0.1.0) | Current Approach (Phase 2 推奨) | When Changed | Impact |
|------------------------|--------------------------------|--------------|--------|
| Internal AST walk for type_deps | stdlib ast walk + pyright `reportMissingImports` resolved annotation | Phase 2 | TypeDep に新 `resolved` field 追加、 v0.1.0 acceptance test pass 継続 |
| 4 extractors × `ast.parse()` (4 回再パース) | Frontend が 1 回 parse → CAV envelope → 4 extractor が cav.payload pull | Phase 1 で設計、 Phase 2 で実装 | パフォーマンス線形改善、 AST-05 invariant 達成 |
| `ContractInfo(preconditions/invariants/postconditions: list[str])` class-level 1 source_kind | `ContractInfo` with per-entry `source_kind` + `ContractEntry` list (D-12 β) | Phase 2 | verifier が contract-statement レベルで物理↔論理比較可能、 PROJECT.md Core Value (責務分離) 達成 |
| `params: dict[str, object]` (v0.1.0 ParserConfig stub) | typed Pydantic fields (`language`, `extract_contracts`, `compile_args`, `python_version`) | Phase 1 で typed 版作成、 Phase 2 で barrel graduation | ARC-05 達成、 caller-side type safety |
| `_get_module_name` 4 重複 | `_paths.py` single source | Phase 1 | ARC-04 / DET-04 達成、 既存 `tests/parity/test_v01_v02_compat.py::test_no_duplicate_module_name_helper` で gate |
| flat layout (`lib_code_parser/*.py`) | nested layout (`models/{infrastructure,primitives,evaluations}/`, `frontends/`, `extractors/primitives/`, `adapters/`) | Phase 1 | ARC-01 達成、 Open-Closed invariant 適用基盤 |

**Deprecated / outdated:**

- v0.1.0 `lib_code_parser/{ast_extractor,callgraph_builder,contract_extractor,type_dep_builder}.py` 4 ファイル — Phase 2 D-01 で **削除**
- v0.1.0 `lib_code_parser/executor.py` の if/elif 分岐 — Phase 2 D-03 で dispatch dict 走査型に **rewrite**
- v0.1.0 barrel `lib_code_parser.ParserConfig` の `params: dict[str, object]` stub — Phase 2 D-01 で typed 版に **graduation**
- v0.1.0 acceptance test の `from lib_code_parser.ast_extractor import extract_functions` 等の import path — Phase 2 で typed ParserConfig + CAV 経由に書き換え

---

## Assumptions Log

本研究の全てのテクニカル claim は実機検証または公式 docs から citation 済み。 `[ASSUMED]` タグの claim は下記のみ:

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `ast.unparse(cav.payload)` で生成した bytes を pyright に渡しても元 source と等価な diagnostic line number が返る | §2.3 algorithm sketch、 §Code Examples §例 3 | line number 乖離で `resolved` flag が誤判定。 **回避策**: CAV model に `raw_content: bytes` を carry させるか (Phase 1 model 変更が必要)、 frontends/python.py が CAV 作成時に raw_content を保持する 別 path を planner が議論。 02-DISCUSSION-LOG.md で要再議論 |
| A2 | Phase 1 既存 `ContractInfo` model (class-level 1 source_kind) を D-12 (β) に拡張する案 A (`ContractEntry` 新規) が SCH-02 `extra="forbid"` 下で問題なく動く | §3.4 model 拡張案 A | 案 B / C との比較で planner が最終決定する余地あり |
| A3 | pyright 1.1.409 が CI 環境 (Linux x86_64 / Windows x86_64) で同 JSON schema を emit する | §2 全体 | 本研究は Windows x86_64 のみで実機検証、 Linux で reflective 差異がないことは公式 docs 経由 [CITED: pyright cross-platform] |
| A4 | `__post_init__` を class-level `@dataclass` decorator 有無を見ずに method 名のみで判定する (D-11 simplicity 優先) | Pitfall 5 | 非 dataclass の `__post_init__` が `dataclass_post_init` source_kind に分類される false positive 許容。 planner が 02-DISCUSSION-LOG.md で明示決定 |

**If this table contains items:** 上記 4 claim は Phase 2 planning で再確認 / 02-DISCUSSION-LOG.md に追記して user 承認を取ること。

---

## Open Questions

1. **CAV に `raw_content: bytes` を carry させるべきか (A1 関連)**
   - 何が分かっているか: `ast.unparse(module)` は AST→source の re-serialize だが、 空行 / コメント / docstring 形式が変わるため line number が元 source と乖離する可能性がある。
   - 何が不明か: pyright が line number based diagnostics を返すため、 type_deps extractor が「diagnostic line ↔ TypeDep line」 mapping を正確に保つには元 source の line 番号が必要。 Phase 1 CAV model は `payload: object` のみで raw_content を持たない。
   - 推奨: planner が 02-DISCUSSION-LOG.md で「CAV に `raw_content: bytes` field 追加」 vs 「PyrightAdapter が raw_content を別経路で受け取る (例: type_deps extractor が cav とは別に raw_content を受け取る signature)」を比較し決定。 後者の方が Phase 1 lock 違反を回避できる。

2. **AST-04 `__post_init__` 検出で class-level `@dataclass` decorator を見るか (A4 関連)**
   - 何が分かっているか: v0.1.0 は class context を見ず unconditional に `__post_init__` を Pydantic 扱い。
   - 何が不明か: D-11 mapping 表は decorator name 単位で「`__post_init__` → `dataclass_post_init`」と規定するが、 plain class の `__post_init__` をどう扱うかは規定なし。
   - 推奨: planner が 02-DISCUSSION-LOG.md で「class-level `@dataclass` / `@pydantic.dataclasses.dataclass` の有無を見るか / 見ないか」を明示。 simplicity 優先なら見ない方向。

3. **AST-02 chain call `a.b().c()` の edge 数 (Pitfall 4 関連)**
   - 何が分かっているか: v0.1.0 は 2 edges (`(caller, c), (caller, b)`) emit。 ROADMAP success criteria 2 は edge 数規定なし。
   - 何が不明か: Phase 3 DIA-02 が chain call をどう描画するかの仕様。
   - 推奨: Phase 2 では v0.1.0 動作を継承、 Phase 3 入口で再評価 (CONTEXT.md G-5 deferred と整合)。 ただし新規 unit test (`test_chain_call_emits_two_edges`) を Phase 2 で追加して future readers が動作を理解できるようにする。

4. **TypeDep model に `resolved` field を追加するか、 `kind` を enum 化するか**
   - 何が分かっているか: 本研究 §2.3 が pyright resolved annotation を `TypeDep` に notation する設計を推奨。
   - 何が不明か: model 変更の具体 (新 field 追加 vs 既存 `kind` 拡張)。
   - 推奨: 新 field `resolved: bool = False` を追加 (planner 判断、 SCH-02 `extra="forbid"` 下で互換)。 `kind` は v0.1.0 で `"imports"` / `"uses"` の 2 値、 これに `"imports_resolved"` 等を加えると Pydantic Literal 化が必要だが、 既存 docs/09-extending.md の「TypeDep.kind は free-form str」原則と衝突する。 model 拡張は単純 boolean が望ましい。

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | 全 phase 実装 | ✓ | 3.11.1 | — |
| `pyright` (Python wrapper) | DET-03 / AST-03 | ✓ | 1.1.408 install済 (`PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` で 1.1.409 強制動作確認) | — |
| `pyright[nodejs]` 内 Node.js | pyright wrapper の依存 | ✓ | nodeenv 経由で自動 install | — |
| `pydantic` | 全 model | ✓ | 2.11.10 | — |
| `tempfile` (stdlib) | PyrightAdapter tmpdir | ✓ | Python 3.11+ 同梱 | — |
| `subprocess` (stdlib) | PyrightAdapter | ✓ | Python 3.11+ 同梱 | — |
| `json` (stdlib) | pyright JSON parse | ✓ | Python 3.11+ 同梱 | — |
| `ast` (stdlib) | Frontend + 3 primitives | ✓ | Python 3.11+ 同梱 | — |
| `re` (stdlib) | TRC-03 regex | ✓ | Python 3.11+ 同梱 | — |
| `pytest` | test runner | ✓ | `pip show pytest` で確認可能 (Phase 1 で declared) | — |
| `grep` (CLI、 test infrastructure) | `tests/parity/test_v01_v02_compat.py::test_no_duplicate_module_name_helper` + AST-05 static gate | ✓ (Windows: Git Bash / WSL 経由で利用、 Phase 1 既存 test で動作実証済) | — | Python 内で `pathlib.Path.glob` + 文字列 search に置換可能 (Phase 2 で planner が確認) |

**Missing dependencies with no fallback:** なし
**Missing dependencies with fallback:** `grep` は Windows 環境では Git Bash 経由 — Phase 1 既存 test が同じ形式 (`subprocess.run(["grep", ...])`) で機能していることを確認しているので Phase 2 でも問題なし。 CI 環境では Linux runner で問題なし。

---

## Sources

### Primary (HIGH confidence)

- 本研究実機検証 (Windows 11 x86_64、 Python 3.11.1、 Pydantic 2.11.10、 pyright 1.1.408 + `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409`)
  - `pyright --outputjson` schema を 3 fixture で確認 (`order_service.py`、 `bad_imports.py`、 `strict_typing.py`)
  - `pyright --outputjson + --verbose / --dependencies / --verifytypes` の排他性確認
  - v0.1.0 `lib_code_parser/{ast_extractor,callgraph_builder,contract_extractor,type_dep_builder}.py` を 7 + 6 + 7 = 20 fixture で fire し解像度 rule を全列挙
- Phase 1 既存コードベース (本研究実機読取): `models/{infrastructure,primitives}/*.py`, `_dispatch.py`, `_paths.py`, `adapters/base.py`, `tests/parity/test_v01_v02_compat.py`, `tests/conftest.py`, `docs/09-extending.md`
- `.planning/PROJECT.md` Constraints + Key Decisions (16 件、 v0.1.0 baseline + Phase 1 完了反映済)
- `.planning/REQUIREMENTS.md` (42 件、 Phase 2 で 8 件カバー)
- `.planning/ROADMAP.md` §Phase 2 (4 success criteria)
- `.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md` (14 locked decisions D-01..D-14)
- `.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md` (Phase 1 確定済 research — Pydantic Generic / dispatch dict / subprocess hardening)

### Secondary (MEDIUM confidence — WebFetch で公式 docs 確認)

- pyright 公式 docs `command-line.md` (本研究 WebFetch、 raw.githubusercontent.com 経由) — `--outputjson` schema、 全 CLI flag、 「JSON does not include resolved imports/types」明示 [CITED]
- basedpyright docs `command-line.md` (本研究 WebFetch、 docs.basedpyright.com) — pyright と同 schema 確認、 「No, basedpyright does not offer a CLI flag specifically designed to emit resolved import types or annotation types」明示 [CITED]
- RobertCraigie/pyright-python 公式 README (本研究 WebFetch、 github.com) — `PYRIGHT_PYTHON_FORCE_VERSION` + `PYRIGHT_PYTHON_IGNORE_WARNINGS` 含む env var 列挙 [CITED]
- Pydantic v2 公式 docs `concepts/validators/` (本研究 WebFetch、 pydantic.dev) — field_validator / model_validator が active、 validator / root_validator が deprecated 確認 [CITED]
- GitHub issue: `microsoft/pyright/issues/6740` (本研究 WebSearch 経由) — 「`--outputjson` schema is not according to spec」 同種 issue 既出、 公式が schema を限定的にしか document していない確認 [CITED]

### Tertiary (LOW confidence — 不採用、 参照のみ)

- 訓練データの pyright JSON 関連知識 — 本研究実機で false と判明したため不採用 (CONTEXT.md D-07 仮定の元ネタもこの class と推定)

---

## Metadata

**Confidence breakdown:**

- Pyright Subprocess Integration (§2): **HIGH** — pyright 1.1.409 を本 env で実機動作確認、 schema を 3 fixture で観察、 公式 docs + basedpyright docs + GitHub issue でクロス確認
- Pydantic Validator AST Detection (§3): **HIGH** — v0.1.0 contract_extractor.py を 6 edge case で本機実機 fire、 Pydantic v2 公式 docs で decorator 表確認
- Internal CallGraph Resolution Rules (§4): **HIGH** — v0.1.0 callgraph_builder.py を 7 fixture で本機実機 fire、 解像度 rule を全列挙
- AST-05 One-Parse Enforcement (§5): **HIGH** — Phase 1 既存 `test_no_duplicate_module_name_helper` の grep pattern を再利用、 monkeypatch は標準 pytest 機能
- TRC-02 Docstring Template (§6): **MEDIUM** — Phase 1 既存 model docstring の `Traces:` 行を模倣、 `Implements:` 行は本研究の提案 (TRC-02 で REQ-ID 宣言要件のみ規定、 形式は未指定)
- v0.1.0 Parity Baselines (§7): **HIGH** — v0.1.0 4 extractor の全 logic を実機 fire で確認、 acceptance test FR-01..06 を読み込み挙動を全列挙
- Standard Stack / Package Audit: **HIGH** — Phase 1 で確定済み、 Phase 2 で新規 install なし

**Research date:** 2026-05-30
**Valid until:** Phase 2 実装完了まで (pyright 1.1.410+ がリリースされた場合は DET-03 pin 維持の影響なし。 pydantic 2.12+ は SCH-02 `extra="forbid"` 互換性継続を Phase 5 で再確認)

---

## RESEARCH COMPLETE

**Phase:** 2 - Python Frontend + AST Primitives + ACL-2 Adapters
**Confidence:** HIGH

### Key Findings

- pyright `--outputjson` は型解決済み import/annotation 情報を返さない (CONTEXT.md D-07 前提を実機 invalidate)。 代替 design = stdlib ast walk + pyright `reportMissingImports` を `resolved` flag に annotate (本研究 §2.3)
- D-08 pyright CLI 選定確定: `pyright --outputjson --pythonversion <ver> -p <tmpdir>/pyrightconfig.json <path>` (本研究 §2.2)
- DET-03 env: `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` + `PYRIGHT_PYTHON_IGNORE_WARNINGS=1` 必須 (本研究 §2.4 で実機確認 + 公式 README citation)
- v0.1.0 callgraph 解像度を 7 fixture で全列挙: `self.foo()`→bare、 chain `a.b().c()`→2 edges、 nested function→outer flatten、 edges 未 sort。 Phase 2 は v0.1.0 parity 継承 + DET-04 sort 追加 (本研究 §4)
- v0.1.0 contract_extractor に実証バグ 2 件: (a) alias import `as fv` 未解決、 (b) `@root_validator` 未認識。 Phase 2 D-11 mapping で同時修正 (本研究 §3)
- AST-05 hard gate 推奨: primary = grep 静的 gate (Phase 1 `test_no_duplicate_module_name_helper` と同形式)、 backup = monkeypatch `ast.parse` call_count (本研究 §5)
- D-12 (β) per-entry source_kind は `ContractEntry` 新規追加 + `ContractInfo.entries: list[ContractEntry]` 構造を推奨。 案 A / B / C 比較を planner が 02-DISCUSSION-LOG.md で再議論 (本研究 §3.4)

### File Created

`c:\work\agent_company\spec-reviewer-libs\lib-code-parser\.planning\phases\02-python-frontend-ast-primitives-acl-2-adapters\02-RESEARCH.md`

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| pyright integration | HIGH | 実機 fixture × 3、 公式 docs + basedpyright + GitHub issue クロス確認 |
| Pydantic validator AST | HIGH | v0.1.0 を 6 fixture で実機 fire、 公式 docs 確認 |
| CallGraph parity | HIGH | v0.1.0 を 7 fixture で実機 fire、 解像度 rule 全列挙 |
| AST-05 hard gate | HIGH | Phase 1 既存 test pattern を再利用 |
| Standard stack | HIGH | Phase 1 確定済、 Phase 2 で新規追加なし |
| TRC-02 docstring template | MEDIUM | TRC-02 REQ は形式未指定、 本研究の提案を planner が承認 / 修正できる |

### Open Questions (Planner が判断)

1. CAV に `raw_content: bytes` を carry させるか (Phase 1 model 変更を許容するか)
2. `__post_init__` 検出で class-level `@dataclass` decorator を見るか
3. AST-02 chain call の edge 数を v0.1.0 と同じ 2 edges のまま Phase 2 で固定するか
4. TypeDep model に `resolved` field を追加するか、 `kind` を enum 化するか

### Ready for Planning

研究完了。 planner は本 RESEARCH.md + CONTEXT.md + Phase 1 carry-forward を読んで Wave 構成 (本研究 Summary §Primary recommendation 提示済) と各 plan task に進める。 重要警告: **CONTEXT.md D-07 「pyright JSON から型解決済み subkey 抽出」は実機検証で不可能と判明したため、 02-DISCUSSION-LOG.md に「D-07 を本研究 §2.3 の revised algorithm で再解釈する」旨を追記してから plan 着手すべき** (user 承認を取るか、 planner 判断で revised algorithm に進むかは planner の判断領域)。
