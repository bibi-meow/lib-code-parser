---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
verified: 2026-05-31T00:00:00Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
human_verification:
  - test: "CR-01 の resolve_imports ゲートなし設計がプロジェクト制約と整合するか人間判断を要求する"
    expected: "AST-03 要件の定義と PROJECT.md の決定論性制約が CR-01 に記された懸念を明示的に許容しているか確認"
    why_human: "CR-01 は設計上の意図的トレードオフとして記録された (D-06 fail-loudly + CONTEXT.md §G-2) が、PROJECT.md の 'LLM/network/clock/動的解析を一切使わない' という決定論性ハード制約との整合性は人間が最終判断すべき境界線にある"
    resolution: "RESOLVED — ユーザーが Option B を承認し、plan 02-08 で resolve_imports ゲートを実装。デフォルト execute() 経路は pyright/subprocess なしの純粋関数に復帰。opt-in (resolve_imports=True) のみ pyright-hybrid。241 passed / ruff clean。"
---

> **CR-01 RESOLVED (2026-05-31, plan 02-08):** 本レポートの唯一の human-needed 項目
> (CR-01) は gap closure 済み。`ParserConfig.resolve_imports: bool = False` を
> additive field として追加し、`type_deps.extract()` のデフォルト経路を
> pyright/subprocess なしの AST-only 純粋経路 (`resolved=True` 既定) に変更した。
> これにより `execute()` は PROJECT.md HARD constraint「出力は
> `(raw_content, path, config)` の純粋関数」に復帰した。pyright-hybrid 解決
> オラクル (D-06 fail-loudly) は `resolve_imports=True` の明示 opt-in 経路でのみ
> 起動する。フルスイート 241 passed / 0 failed / 0 skipped、ruff clean。詳細は
> `02-08-cr01-resolve-imports-gate-SUMMARY.md` を参照。ステータスを human_needed
> → passed に更新。

# フェーズ 2: Python Frontend + AST Primitives + ACL-2 Adapters 検証レポート

**フェーズ目標:** Python Frontend (ファイルを 1 回だけパースして不変の Common AST View = CAV を出力) を実装し、4 つの pure-CAV aspect extractor (functions / internal call graph / type deps / contracts with Pydantic-validator vs. `__post_init__` 判別) と `pyright[nodejs]==1.1.409` サブプロセスアダプターを `adapters/` に構築する。v0.1.0 互換の `NormalizedArtifact` を新ロックアーキテクチャ (v0.1.0 呼び出し元にリグレッションなし) で提供し、pyright 解決済み TypeDep と明示的な Pydantic/dataclass contract 判別を追加する。

**検証日時:** 2026-05-31
**ステータス:** human_needed
**再検証:** なし (初回検証)

---

## ゴール達成の評価

### 観測可能な真実 (Observable Truths)

| # | 真実 | ステータス | 根拠 |
|---|------|-----------|------|
| 1 | Python Frontend が 1 ファイル 1 回の `ast.parse()` を保証し、`build_cav()` が正しい CAV を返す | ✓ VERIFIED | `lib_code_parser/frontends/python.py:36` に `ast.parse` が 1 回のみ。`test_ast_05_one_parse.py` (4件) が grep static gate + monkeypatch dynamic gate で確認済み |
| 2 | 4 つの pure-CAV extractor (functions/callgraph/contracts/type_deps) が `cav.payload` を消費し `ast.parse()` を呼ばない | ✓ VERIFIED | `grep -rn "ast.parse(" lib_code_parser/extractors/` → 0 件。parity test `test_no_ast_parse_in_extractors_directory` が PASS |
| 3 | type_deps extractor が pyright `reportMissingImports` 診断を使って `resolved` flag を注釈付与する | ✓ VERIFIED | `lib_code_parser/extractors/primitives/type_deps.py:129-153` 実装確認。`os` → `resolved=True`、`nonexistent_xyz_lib` → `resolved=False` で動作確認済み |
| 4 | ContractInfo が Pydantic validator と `__post_init__` を `source_kind` で明確に判別する | ✓ VERIFIED | `contracts.py:50-55` の `_DECORATOR_TO_SOURCE_KIND` マッピング確認。`__post_init__` → `dataclass_post_init`、`field_validator` → `pydantic_field_validator` で動作確認済み |
| 5 | v0.1.0 互換: `NormalizedArtifact` が dispatch-driven executor から返り、旧 4 ファイルは削除済み | ✓ VERIFIED | `ls lib_code_parser/*.py` → 4 ファイル (`__init__.py`, `_dispatch.py`, `_paths.py`, `executor.py`) のみ。旧 legacy 4 ファイルは削除確認済み |
| 6 | DET-03: `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` が subprocess env に設定されている | ✓ VERIFIED | `adapters/pyright.py:49` に `_PYRIGHT_DET_ENV = {"PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409", ...}` 確認済み |
| 7 | TRC-02: 全 extractor module に `Implements: AST-NN` 形式の docstring 行がある | ✓ VERIFIED | `parity/test_trc_02_docstring.py` (3件) PASS。functions / callgraph / contracts / type_deps / frontends/python / adapters/pyright の全 6 モジュールで確認済み |
| 8 | TRC-03: `Traces: REQ-ID` 行が全 extractor module に存在し、`_extract_trace_tags` の verbatim regex が v0.1.0 と byte-identical | ✓ VERIFIED | 同テスト + functions.py:33 の regex が v0.1.0 と同一確認済み。実際の `Traces: FR-01, FR-02` 抽出も動作確認 |

**スコア:** 8/8 真実が VERIFIED

---

### 必須アーティファクト

| アーティファクト | 提供内容 | ステータス | 詳細 |
|----------------|---------|-----------|------|
| `lib_code_parser/frontends/python.py` | Python Frontend — 1 回 parse、CAV envelope 発行 | ✓ VERIFIED (L1-3) | `def build_cav` 存在、`ast.parse` 1 回のみ、barrel (`frontends/__init__.py`) 経由でも import 可能 |
| `lib_code_parser/models/infrastructure/cav.py` | `raw_content: bytes` additive field 追加の CAV モデル | ✓ VERIFIED (L1-3) | `frozen=True`, `extra="forbid"`, `arbitrary_types_allowed=True` 維持。`raw_content: bytes = b""` が追加 (後方互換) |
| `lib_code_parser/extractors/primitives/functions.py` | Pure-CAV FunctionNode extractor (AST-01) | ✓ VERIFIED (L1-3) | `def extract` 存在、`cav.payload` 消費、`_paths.get_module_name` import で ARC-04 準拠 |
| `lib_code_parser/extractors/primitives/callgraph.py` | Pure-CAV CallGraph extractor (AST-02) | ✓ VERIFIED (L1-3) | `def extract` 存在、エッジが `(caller, callee)` lex ソート (DET-04) |
| `lib_code_parser/extractors/primitives/contracts.py` | ContractInfo extractor with source_kind discrimination (AST-04) | ✓ VERIFIED (L1-3) | `def extract` 存在、`_DECORATOR_TO_SOURCE_KIND` mapping、`__post_init__` → `dataclass_post_init` 判別確認 |
| `lib_code_parser/extractors/primitives/type_deps.py` | TypeDep extractor + pyright resolved 注釈 (AST-03) | ✓ VERIFIED (L1-3) | `def extract` 存在、`PyrightAdapter` 呼び出し、`resolved` flag 注釈確認済み |
| `lib_code_parser/adapters/pyright.py` | PyrightAdapter — DET-03 env + D-06 fail-loudly + D-07 canonicalization | ✓ VERIFIED (L1-3) | `class PyrightAdapter` 存在、`PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` 設定確認、tmpdir 書き込み + pyrightconfig.json 生成確認 |
| `lib_code_parser/_dispatch.py` | FRONTENDS + PRIMITIVES dispatch dict | ✓ VERIFIED (L1-3) | `FRONTENDS["python"] = build_cav`、`PRIMITIVES` に 4 エントリ登録確認 |
| `lib_code_parser/executor.py` | Dispatch-dict-driven executor (D-03 rewrite) | ✓ VERIFIED (L1-3) | `FRONTENDS[language]` + `PRIMITIVES.items()` walk 確認。contracts merge logic (v0.1.0 parity) 確認 |
| `tests/parity/test_ast_05_one_parse.py` | AST-05 static grep gate + monkeypatch dynamic gate | ✓ VERIFIED | 4 件 PASS |
| `tests/parity/test_trc_02_docstring.py` | TRC-02/TRC-03 docstring grep gate | ✓ VERIFIED | 3 件 PASS |
| `tests/parity/test_snapshot_v01_fixture.py` + `fixtures/v01_snapshot.json` | D-04 v0.1.0 fixture snapshot (byte-identical comparison) | ✓ VERIFIED | 2 件 PASS (pyright インストール済み環境で実行確認) |

---

### キーリンク検証

| From | To | Via | ステータス | 詳細 |
|------|----|----|-----------|------|
| `frontends/python.py::build_cav` | `ast.parse` | 単一の直接呼び出し | ✓ WIRED | L36 の 1 箇所のみ (AST body 解析で確認) |
| `frontends/python.py::build_cav` | `CAV(language="python", ...)` | CAV コンストラクタ (`raw_content` carry) | ✓ WIRED | L37-42 確認 |
| `extractors/primitives/functions.py::extract` | `cav.payload` (ast.Module) | re-parse なし、直接消費 | ✓ WIRED | L83 `tree = cav.payload` 確認 |
| `extractors/primitives/functions.py::extract` | `lib_code_parser._paths.get_module_name` | ARC-04 single source import | ✓ WIRED | L20 `from lib_code_parser._paths import get_module_name` 確認 |
| `extractors/primitives/type_deps.py::extract` | `PyrightAdapter.analyze(cav.raw_content, cav.path)` | diagnostic-driven resolved 注釈 | ✓ WIRED | L131 確認 |
| `PyrightAdapter._PYRIGHT_DET_ENV` | `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` | `extra_env` で `run_subprocess` に渡す | ✓ WIRED | L199-204 確認 |
| `PyrightAdapter.analyze` | `tempfile.TemporaryDirectory()` + bytes 書き込み | D-05 caller-agnostic I/O | ✓ WIRED | L190-195 確認 |
| `executor.py` | `_dispatch.FRONTENDS / _dispatch.PRIMITIVES` | D-03 dispatch dict walk | ✓ WIRED | L17 import、L74-94 walk 確認 |

---

### データフロートレース (Level 4)

| アーティファクト | データ変数 | データソース | 実データを生成するか | ステータス |
|----------------|----------|------------|-------------------|-----------|
| `executor.py::execute` | `functions, call_graph, type_deps, contracts_dict` | `PRIMITIVES.items()` walk → 各 extractor(cav, config) | はい | ✓ FLOWING |
| `type_deps.py::extract` | `raw_deps` (TypeDep list) | `ast.walk(tree)` over `cav.payload` | はい | ✓ FLOWING |
| `type_deps.py::extract` | `resolved` flag | `PyrightAdapter.analyze(cav.raw_content, cav.path)` → `reportMissingImports` diagnostic | はい (pyright 利用時) | ✓ FLOWING |
| `contracts.py::extract` | `entries` (ContractEntry list) | `ast.walk(module)` で decorator 検出 | はい | ✓ FLOWING |

---

### 動作スポットチェック (Behavioral Spot-Checks)

| 動作 | コマンド / 確認方法 | 結果 | ステータス |
|------|------------------|------|-----------|
| `build_cav` が ast.Module payload の CAV を返す | Python インライン確認 | `language=python, path=foo.py, payload=Module` | ✓ PASS |
| 4 extractor が isolated 呼び出し可能 | Python インライン確認 | functions=3, callgraph=nodes/edges, contracts=1 class | ✓ PASS |
| `__post_init__` が `dataclass_post_init` に分類される | Python インライン確認 | `source_kind='dataclass_post_init'` 確認 | ✓ PASS |
| pyright 経由で `resolved=False` が設定される | Python インライン確認 | `nonexistent_xyz_lib → resolved=False` 確認 | ✓ PASS |
| DET-04: TypeDep が (source, target, kind, source_line) でソートされる | Python インライン確認 | ソート順アサーション PASS | ✓ PASS |
| `NormalizedArtifact` が dispatch-driven executor から返る | Python インライン確認 | `NormalizedArtifact[CodeContent]` 返却確認 | ✓ PASS |
| 旧 dict-style `ParserConfig(params={...})` が `ValidationError` を raise する | Python インライン確認 | `ValidationError` 確認 (D-02 explicit break) | ✓ PASS |
| `ruff check` が全ファイルで clean | `ruff check lib_code_parser/ tests/` | exit 0 | ✓ PASS |
| フルテストスイート | `python -m pytest -q` | 235 passed, 0 failed, 0 skipped (86s) | ✓ PASS |

---

### 要件カバレッジ

| 要件 ID | 計画 | 説明 | ステータス | 根拠 |
|--------|------|------|-----------|------|
| **AST-01** | 02-02, 02-07 | FunctionNode 抽出 (kind/params/return_type/docstring/trace_tags/source_range) | ✓ SATISFIED | `functions.py::extract` 実装、acceptance test `test_fr01` 全件 PASS |
| **AST-02** | 02-03, 02-07 | 決定論的 CallGraph (GPL 依存なし、内部サブプロセスなし) | ✓ SATISFIED | `callgraph.py::extract` 実装。`lib_code_parser/adapters/` のみ subprocess。acceptance test `test_fr02` PASS |
| **AST-03** | 02-05, 02-06, 02-07 | pyright 経由の型解決済み TypeDep | ✓ SATISFIED | `type_deps.py::extract` + `PyrightAdapter` 実装。`os` → resolved=True, `nonexistent_xyz_lib` → resolved=False 確認 |
| **AST-04** | 02-04, 02-07 | ContractInfo で Pydantic validator vs `__post_init__` を `source_kind` で判別 | ✓ SATISFIED | `contracts.py::extract` 実装。`_DECORATOR_TO_SOURCE_KIND` mapping + `__post_init__` 判別確認 |
| **AST-05** | 02-01, 02-07 | 全 primitive extractor が 1 ファイル 1 回 parse (CAV) で動作 | ✓ SATISFIED | `test_ast_05_one_parse.py` 4 件 PASS (grep static gate + monkeypatch dynamic gate) |
| **DET-03** | 02-05, 02-06 | `pyright[nodejs]==1.1.409` 厳密 pin; subprocess env に `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` | ✓ SATISFIED | `_PYRIGHT_DET_ENV` 確認済み。`test_det_03_env_var_set` PASS |
| **TRC-02** | 02-01, 02-07 | 各 extractor module の docstring に `Implements: REQ-ID` 宣言 | ✓ SATISFIED | `test_trc_02_docstring.py::test_all_extractor_modules_declare_implements_req_id` PASS |
| **TRC-03** | 02-01, 02-07 | TraceTag 抽出 (`Traces: REQ-ID` regex) が v0.1.0 と verbatim parity | ✓ SATISFIED | `_TRACE_TAGS_RE` regex が v0.1.0 と同一。実際の tag 抽出動作確認済み |

**要件カバレッジ:** 8/8 (フェーズ 2 割り当て要件をすべて充足)

---

### アンチパターン検出

| ファイル | 行 | パターン | 重大度 | 影響 |
|--------|-----|---------|-------|------|
| `extractors/primitives/functions.py:84` | 84-87 | `assert isinstance(tree, ast.Module)` — `-O` 実行で無効化される | ⚠️ Warning (WR-04) | `-O` フラグ下での型検証失落。ライブラリコードでの assert 使用は推奨されない |
| `extractors/primitives/callgraph.py:66` | 66-69 | 同上 | ⚠️ Warning (WR-04) | 同上 |
| `extractors/primitives/contracts.py:151` | 151-154 | 同上 | ⚠️ Warning (WR-04) | 同上 |
| `extractors/primitives/type_deps.py:79` | 79-82 | 同上 | ⚠️ Warning (WR-04) | 同上 |
| `extractors/primitives/type_deps.py:69-153` | - | pyright subprocess が常時起動。`resolve_imports` opt-in ゲートなし (CR-01) | ⚠️ Warning — 設計上の意図的トレードオフ | pyright 未インストール環境では `type_deps.extract` が `RuntimeError` を送出する (D-06 fail-loudly として設計認知済み) |
| `models/primitives/contracts.py` | 65-83 | `@computed_field` + `extra="forbid"` で `model_dump()` → `model_validate()` round-trip が破綻 (WR-01) | ⚠️ Warning | verifier が ContractInfo JSON を `model_validate` で復元しようとすると失敗する潜在的スキーマ契約の破壊 |
| `adapters/pyright.py:128-143` | - | `parse_output` ABC の signature と非互換 (WR-05) | ⚠️ Warning | `adapter.execute()` を誤って呼ぶと tmpdir パスが漏洩する Liskov 置換違反リスク |
| `models/__init__.py` | 1 | docstring の名称数が実体と不整合 (IN-03) | ℹ️ Info | 保守者の誤認リスク |

**TBD/FIXME/XXX マーカー:** ソースファイルにはなし。

---

### CR-01 についての評価: 設計トレードオフか、それとも要件違反か

**評価結果: 設計上の意図的なトレードオフ — ただし人間の最終判断を要求**

**証拠 (トレードオフとして認識されている根拠):**
1. CONTEXT.md D-06 は「fail loudly (RuntimeError)」を**明示的なキー決定**として記録している。pyright 未インストール = caller 環境問題であり、silent empty 化は決定論性を破ると記されている。
2. CONTEXT.md D-07-revised は pyright 統合の採用 algorithm を `stdlib ast walk + pyright diagnostics` ハイブリッドと明示している。
3. REQUIREMENTS.md AST-03 は「pyright subprocess wrapper で型解決済み TypeDep を取得」と明記しており、pyright の使用は要件として承認されている。
4. PROJECT.md の制約は「LLM / network / clock / 動的解析を一切使わない」だが、`pyright` は静的型チェッカー (subprocess) であり「動的解析」には該当しない解釈の余地がある。

**CR-01 が懸念する点:**
- `resolve_imports` のような opt-in フラグがなく、pyright を常時起動する (type_deps を無効化する手段がない)
- pyright 未インストール環境ではライブラリ全体が機能しない
- 「(raw_content, path, config) の純粋関数」というハード制約との完全な整合性が論争的

**人間の判断が必要な理由:**
この設計は CONTEXT.md D-06 と D-07 で意識的に選択されたが、PROJECT.md の「純粋関数性」ハード制約と `resolve_imports=False` デフォルトの欠如の間には曖昧さが残る。CR-01 の Fix (resolve_imports フラグ追加) を受け入れるか、現状の設計を承認するかは、ユーザーの判断が必要。

---

### 人間の検証が必要な項目

#### 1. CR-01: `resolve_imports` ゲートなし設計の承認

**テスト:** PROJECT.md の決定論性ハード制約 (「出力は `(raw_content, path, config)` の純粋関数」) と CONTEXT.md D-06 の「fail loudly」設計を照らし合わせ、現状の type_deps が常時 pyright を呼ぶ実装を承認するか判断する。

**期待:** 以下のいずれかの決定:
- (A) 現状承認: pyright は静的解析ツールであり `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` で固定されているため「条件付き決定論」として受け入れる。CR-01 は Warning 止まり。
- (B) Fix 実施: ParserConfig に `resolve_imports: bool = False` を追加し、フラグ未設定時は AST-only 純粋関数経路で返す (CR-01 の推奨 Fix)。

**人間が必要な理由:** CONTEXT.md D-06/D-07 は意識的な設計判断だが、「pyright 未インストール環境では type_deps.extract が RuntimeError を送出する」現実は PROJECT.md のハード制約との整合性を技術的に検証できない。これはポリシー的な判断。

---

## ギャップの要約

技術的な実装は**フルグリーン** (235 passed, 0 failed, 0 skipped) であり、8 つの必須真実はすべて VERIFIED されている。レポジトリに TBD/FIXME/XXX マーカーはない。

**即時 BLOCKER なし。**

コードレビュー (02-REVIEW.md) で検出された 6 件の Warning (WR-01 〜 WR-06) はいずれも Phase 2 ゴール要件 (AST-01..05, DET-03, TRC-02, TRC-03) を技術的にブロックしていない。ただし以下の 2 件は Phase 3 以降での消費者リスクがある:

- **WR-01** (`ContractInfo.model_dump()` → `model_validate()` round-trip 破壊) — verifier が ContractInfo JSON を復元しようとすると失敗。Phase 3 の diagram/spec extractor 実装前に対処を推奨。
- **WR-05** (`PyrightAdapter.parse_output` Liskov 置換違反) — `adapter.execute()` を誤って呼ぶと tmpdir パスが漏洩。Phase 3 以降での誤用リスク。

**CR-01 は人間判断を必要とする**: 現状設計の承認または `resolve_imports` フラグ追加の選択。

---

_検証日時: 2026-05-31_
_検証者: Claude (gsd-verifier)_
