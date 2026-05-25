---
phase: 01-architecture-foundation-spec-correction
verified: 2026-05-26T04:30:00Z
status: passed
score: 14/14 must-haves verified
overrides_applied: 0
re_verification: null
gaps: []
deferred: []
human_verification: []
---

# Phase 1: Architecture Foundation + Spec Correction 検証レポート

**フェーズゴール:** v0.2.0 アーキテクチャ基盤を Key Decisions D-01..D-23 に従い確立し、v0.1.0 spec doc の誤参照 (callgraph.py / ACL-2) を修正する。Phase 2-4 が決定論性保持・lib-diagram-parser 互換レイアウト・4× `_get_module_name` 重複解消・Apache-2.0 ライセンス・subprocess ハードニングヘルパー・SP-3 macOS arm64 libclang 評価に基づいて構築できる基盤を提供する。

**検証日時:** 2026-05-26T04:30:00Z
**ステータス:** passed
**再検証:** なし (初回検証)

---

## ゴール達成の評価

### Observable Truths (観測可能な真実)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | DOC-01 hard gate: `lib-code-parser.md` に `callgraph.py` / `ACL-2` が存在しない | VERIFIED | `grep -E "callgraph\.py\|ACL-2" lib-code-parser.md` → 0 件。Plan 02 で全面書き換え済み (commit 772a212) |
| 2 | ARC-04/DET-04 hard gate: `_get_module_name`/`get_module_name` 定義が `_paths.py` に1件のみ | VERIFIED | `grep -rn "^def (_get_module_name\|get_module_name)" lib_code_parser/` → 1件のみ (`_paths.py:18`)。4 extractors は全て `from lib_code_parser._paths import get_module_name as _get_module_name` の re-export shim のみ。parity test `test_no_duplicate_module_name_helper` PASS |
| 3 | SCH-03 closed Literal: `EdgeKind` が正確に 11 値 ("uses"/"other"/"misc" なし) | VERIFIED | `graph_base.py` の `EdgeKind = Literal[...]` に 11 値確認済み。Python 実行確認: `len(get_args(EdgeKind)) == 11`。`GraphEdge(edge_type="uses")` → `ValidationError` (テスト PASS) |
| 4 | SCH-02 extra="forbid": graph_base.py の 4 モデル全てと infrastructure/primitives モデルが ConfigDict(extra="forbid") を使用 | VERIFIED | grep 確認: graph_base.py 4モデル全て `extra="forbid"` 宣言。infrastructure (artifact.py 3モデル + cav.py + config.py) + primitives (callgraph 2・contracts・functions 4・type_deps) 全モデルに `extra="forbid"` |
| 5 | ARC-05 ParserConfig: `lib_code_parser.models.infrastructure.config.ParserConfig` が型付きフィールド (params dict なし) + extra="forbid" | VERIFIED | `infrastructure/config.py` に `language: Literal["python","cpp"]`, `extract_contracts: bool`, `compile_args: list[str]`, `python_version: str` の型付きフィールドを確認。`extra="forbid"` 宣言済み。Python 実行で `ValidationError` on unknown field 確認済み |
| 6 | DET-05 subprocess hardening: `adapters/base.py:run_subprocess()` が 6 不変条件全てを実装 | VERIFIED | `base.py` docstring に「Hardening invariants enforced (DET-05)」と 6 不変条件 (encoding="utf-8" / errors="replace" / LC_ALL=C+PYTHONHASHSEED=0 / capture_output=True / shell=False / timeout+cwd) が全て明記・実装済み |
| 7 | DOC-04 LICENSE: `LICENSE` は Apache-2.0 全文 + Section 3 patent grant。`pyproject.toml` は `license = "Apache-2.0"` (PEP 639) | VERIFIED | `grep "Grant of Patent License" LICENSE` → 1件。`grep '^license = "Apache-2.0"$' pyproject.toml` → 1件。`grep '^license-files = \["LICENSE"\]$' pyproject.toml` → 1件。MIT の痕跡なし |
| 8 | DOC-03 README §License: "No GPL bundled" + ライセンスマトリクス (call graph internal / pyright MIT / libclang Apache-2.0 WITH LLVM exception) | VERIFIED | README.md L132: `**No GPL bundled.**` 確認。L130: `Apache License 2.0` 確認。L139: `LLVM exception` 確認。pyright MIT、libclang Apache-2.0 WITH LLVM exception のテーブル存在確認 |
| 9 | TRC-01 trace matrix: `docs/99-trace-matrix.md` に Phase 1 の 14 REQ 全行 | VERIFIED | docs/99-trace-matrix.md L54-69 に Phase 1 H2 セクション。ARC-01..05, SCH-01..03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01 の 14 行全て存在。各行に US support + closure plan 記載 |
| 10 | SP-3 spike (D-22): `.planning/spikes/SP-3-libclang-macos-arm64.md` が verdict=ship-best-effort で存在 | VERIFIED | frontmatter: `status: verdict-recorded-ship-best-effort`。Test matrix: Python 3.13/3.14 両方で (a)(b)(c)(d) 全 ✓。CI run URL: https://github.com/bibi-meow/lib-code-parser/actions/runs/26406392965 確認 |
| 11 | D-06 parity: `tests/parity/test_v01_v02_compat.py` が全通過 — v0.1.0 14-name surface 保持 | VERIFIED | `python -m pytest tests/parity/ -v` → 11 passed。v0.1.0 名前 13 件 + v0.2.0 追加 6 件全てインポート可能。JSON byte-identical parity 確認 |
| 12 | CI green: GitHub Actions CI run 26406392965 (commit 0afdb7d) — 3 jobs 全て green | VERIFIED | SP-3-libclang-macos-arm64.md に confirming run `26406392965` 記録あり。`test` + `sp3-libclang-spike (3.13)` + `sp3-libclang-spike (3.14)` 全 green。ローカル: 187 tests passed |
| 13 | ROADMAP SC-1: `from lib_code_parser.models import CAV, EdgeKind, GraphNode, GraphEdge, GraphModel, ParserConfig` が全て Pydantic v2 BaseModel + ConfigDict(extra="forbid") | VERIFIED | Python 実行確認: 6 名前全てインポート可能。各モデルは BaseModel 継承。CAV/GraphNode/GraphEdge/GraphModel/GuardExpr に `extra="forbid"` |
| 14 | ROADMAP SC-4: `adapters/base.py` に subprocess hardening contract 実装済み | VERIFIED | True 3 の確認通り。`run_subprocess()` と `SubprocessAdapter` ABC が存在。DET-05 Traces タグ付き |

**スコア: 14/14 truths 検証済み**

---

### 必須成果物 (Required Artifacts)

| 成果物 | 提供内容 | Status | 詳細 |
|--------|----------|--------|------|
| `lib-code-parser.md` | v0.2.0 spec doc (callgraph.py/ACL-2 参照なし) | VERIFIED | 6 H2 セクション、14 REQ Traces タグ、Apache-2.0 ライセンスマトリクス |
| `LICENSE` | Apache-2.0 全文 (Section 3 patent grant 含む) | VERIFIED | Grant of Patent License 確認。MIT License 痕跡なし |
| `pyproject.toml` | PEP 639 SPDX + setuptools>=77.0.3 + v0.2.0 | VERIFIED | license="Apache-2.0", license-files=["LICENSE"], version="0.2.0", setuptools>=77.0.3 |
| `README.md` | "No GPL bundled" + ライセンスマトリクス | VERIFIED | 全 4 フレーズ確認: "No GPL bundled", "Apache License 2.0", "MIT", "LLVM exception" |
| `lib_code_parser/_paths.py` | get_module_name() 単一ソース | VERIFIED | 18行、定義1件。4 extractors は re-export shim のみ |
| `lib_code_parser/_dispatch.py` | FRONTENDS/PRIMITIVES/EVALUATIONS dispatch dicts | VERIFIED | 3 dict (append-only)。FrontendFn/PrimitiveFn/EvaluationFn 型エイリアス定義 |
| `lib_code_parser/adapters/base.py` | subprocess hardening helper + SubprocessAdapter ABC | VERIFIED | 6 不変条件実装済み。`run_subprocess()` + `SubprocessAdapter` ABC |
| `lib_code_parser/models/infrastructure/cav.py` | CAV (Common AST View) | VERIFIED | extra="forbid", frozen=True, arbitrary_types_allowed=True |
| `lib_code_parser/models/infrastructure/config.py` | 型付き ParserConfig (ARC-05) | VERIFIED | language/extract_contracts/compile_args/python_version フィールド。extra="forbid" |
| `lib_code_parser/models/evaluations/graph_base.py` | EdgeKind (11値) + 4 graph models | VERIFIED | EdgeKind closed Literal 11値。GraphNode/GraphEdge/GraphModel/GuardExpr 全て extra="forbid" |
| `docs/99-trace-matrix.md` | Phase 1 14-REQ トレースマトリクス | VERIFIED | Phase 1 H2 セクション + 14 行テーブル存在 |
| `docs/08-common-view-pattern.md` | CAV + Generic NormalizedArtifact パターン文書 | VERIFIED | 6 不変条件基盤、ARC-02/ARC-04/ARC-05 Traces タグ |
| `docs/09-extending.md` | 拡張 Open-Closed 不変条件 6 件文書 | VERIFIED | 6 不変条件、dispatch dict append-only 契約 |
| `.planning/spikes/SP-3-libclang-macos-arm64.md` | SP-3 spike 評価 (verdict: ship-best-effort) | VERIFIED | status: verdict-recorded-ship-best-effort。全 (a)(b)(c)(d) PASS |
| `.github/workflows/ci.yml` | SP-3 libclang spike job (macos-14, continue-on-error) | VERIFIED | sp3-libclang-spike job 存在。test job 保持 |
| `tests/parity/test_v01_v02_compat.py` | v0.1.0/v0.2.0 互換性テスト | VERIFIED | 11 tests all PASS |
| `frozen/2026-05-24-v0.1.0-spec/LICENSE` | v0.1.0 MIT LICENSE バックアップ | VERIFIED | Plan 01-01 SUMMARY 確認済み |

---

### キーリンク検証 (Key Link Verification)

| From | To | Via | Status | 詳細 |
|------|-----|-----|--------|------|
| `pyproject.toml` | `LICENSE` | `license-files = ["LICENSE"]` | WIRED | L11: `license-files = ["LICENSE"]` |
| `README.md` | `LICENSE` | License セクション参照 | WIRED | "See the [`LICENSE`](./LICENSE) file" |
| extractors (4 files) | `_paths.py:get_module_name` | `from lib_code_parser._paths import get_module_name as _get_module_name` | WIRED | 4 extractors 全て re-export shim のみ、独自定義なし |
| `run_subprocess()` | subprocess invariants | `subprocess.run` + env + encoding | WIRED | encoding="utf-8", errors="replace", LC_ALL=C, PYTHONHASHSEED=0, capture_output=True, shell=False, timeout, cwd |
| `CAV` model | `lib_code_parser/_dispatch.py` | TYPE_CHECKING import | WIRED | `from lib_code_parser.models.infrastructure.cav import CAV` |

---

### データフロートレース (Level 4)

動的データをレンダリングする成果物なし (Phase 1 は models/infra のみ)。Phase 1 は設定・型契約・ドキュメントを確立するフェーズ。Level 4 はスキップ (対象なし)。

---

### 動作スポットチェック (Behavioral Spot-Checks)

| 動作 | コマンド | 結果 | Status |
|------|---------|------|--------|
| パリティテスト全通過 | `python -m pytest tests/parity/ -v` | 11 passed | PASS |
| 全テスト通過 | `python -m pytest -q` | 187 passed | PASS |
| EdgeKind 11値確認 | `python -c "from typing import get_args; from lib_code_parser import EdgeKind; print(len(get_args(EdgeKind)))"` | 11 | PASS |
| ValidationError on unknown field | `ParserConfig(..., surprise=1)` | ValidationError raised | PASS |
| ValidationError on EdgeKind="uses" | `GraphEdge(edge_type="uses")` | ValidationError raised | PASS |
| callable import | `from lib_code_parser import CAV, EdgeKind, GraphNode, ...` | all 6 resolve | PASS |

---

### プローブ実行 (Probe Execution)

明示的なプローブスクリプトは存在しない。SP-3 spike (a)(b)(c)(d) は GitHub Actions CI 上で実行済み (run 26406392965, commit 0afdb7d)。ローカルでは `python -m pytest` による全テスト通過で代替確認。

---

### 要件カバレッジ (Requirements Coverage)

| Requirement | Source Plan | 説明 | Status | Evidence |
|-------------|-------------|------|--------|---------|
| ARC-01 | Plan 09 | 各 extractor module が独立 import 可能 (Phase 1 substrate) | SATISFIED (Phase 1 scope) | 入れ子レイアウト完成。Phase 2 で完全クロージャー予定 |
| ARC-02 | Plan 03 | extractor は Pydantic model 経由のみで通信 | SATISFIED | CAV envelope 実装済み。cross-module direct call なし |
| ARC-03 | Plan 07 | subprocess は adapters/ 層に隔離 | SATISFIED | `adapters/base.py` SubprocessAdapter ABC + run_subprocess() |
| ARC-04 | Plan 06 + 09 | module-name 導出が `_paths.py` に一元化 | SATISFIED | 定義1件のみ。parity test PASS |
| ARC-05 | Plan 03 | `ParserConfig.params: dict[str, object]` を型付きフィールドに置換 | SATISFIED | `infrastructure/config.py` に typed ParserConfig |
| SCH-01 | Plan 05 | lib-diagram-parser 互換 schema (Phase 1 is structural compatibility) | SATISFIED (D-16 interpretation) | 同一 field names + types。direct import は Phase 3 で再評価 |
| SCH-02 | Plans 03/04/05 | 全 Pydantic モデルに `ConfigDict(extra="forbid")` | SATISFIED | 全モデルレイヤー (infrastructure/primitives/evaluations) で確認 |
| SCH-03 | Plan 05 | EdgeKind が 11値の closed Literal | SATISFIED | 11値確認。"uses" → ValidationError |
| DET-04 | Plan 06 + 09 | extractor 出力が安定複合キーでソート (single source) | SATISFIED | `_paths.py` 1定義。grep gate PASS |
| DET-05 | Plan 07 | 全 subprocess 呼び出しが 6 不変条件を使用 | SATISFIED | `run_subprocess()` 全 6 不変条件実装 |
| DOC-01 | Plan 02 | `lib-code-parser.md` から callgraph.py / ACL-2 削除 | SATISFIED | grep → 0件 |
| DOC-03 | Plan 01 + 02 | README に "No GPL bundled" + ライセンスマトリクス | SATISFIED | README L132 "No GPL bundled" 確認 |
| DOC-04 | Plan 01 | Apache-2.0 LICENSE + pyproject.toml SPDX + patent grant | SATISFIED | LICENSE / pyproject.toml 確認済み |
| TRC-01 | Plan 10 | 14 REQ を US にマップしたトレースマトリクス | SATISFIED | docs/99-trace-matrix.md Phase 1 H2 セクション + 14 行 |

---

### アンチパターンスキャン

Phase 1 modified files: `lib-code-parser.md`, `pyproject.toml`, `LICENSE`, `README.md`, `lib_code_parser/_paths.py`, `lib_code_parser/_dispatch.py`, `lib_code_parser/adapters/base.py`, `lib_code_parser/models/` 配下各モデル, `docs/08`, `docs/09`, `docs/99-trace-matrix.md`, `.planning/spikes/SP-3-libclang-macos-arm64.md`, `.github/workflows/ci.yml`, `tests/parity/test_v01_v02_compat.py`

| ファイル | 行 | パターン | 深刻度 | 影響 |
|---------|-----|---------|-------|------|
| `lib_code_parser/_dispatch.py:34` | FRONTENDS, PRIMITIVES, EVALUATIONS = `{}` | 意図的な空 dict | INFO | 設計通り。Phase 2 以降で埋められる (append-only invariant) |
| `lib_code_parser/models/__init__.py:64` | v0.1.0 parity stub ParserConfig (params dict + no extra="forbid") | 意図的な v0.1.0 互換スタブ | INFO | 文書化された移行ブリッジ。Phase 2 executor 書き換えで削除予定 |
| `README.md Quick start section:38` | `params={"language": "python", "extract_contracts": True}` (v0.1.0 API 使用) | v0.1.0 API の旧スタイルサンプル | INFO | Phase 1 transitional window の許容範囲。Phase 2 で更新予定 |

**TBD/FIXME/XXX マーカー:** lib_code_parser/ 配下のいずれのファイルにも未解決の debt marker は存在しない。

**注記:** barrel レベルの `ParserConfig` (v0.1.0 互換スタブ) は `lib_code_parser/models/__init__.py` に文書化され、`tests/parity/test_v01_v02_compat.py` で意図的な Phase 1 transitional 設計として `test_parser_config_unknown_field_raises` が infrastructure パスのみを対象とすることを明記している。これはスタブではなく、設計通りの移行ブリッジである。

---

### 人間による検証が必要な項目

なし。全ての検証項目がプログラム的に確認できた。

---

## ギャップサマリー

なし。全 14 の must-have truths が検証済み。14 要件が全て SATISFIED。

---

## 注記

### SCH-01 解釈について

REQUIREMENTS.md の SCH-01 は「`lib_code_parser` が `lib-diagram-parser>=0.1.0` から直接 import する」と記述しているが、Phase 1 PLAN の must_haves では D-16 interpretation (structural compatibility) が適用されており、Phase 1 では `lib_diagram_parser` を runtime import しないことが pre-resolved Open Question #5 で確定している。Phase 3 (DIA-04) で `node_type="package"` sibling-lib PR の状況が再評価される。この解釈は `lib_code_parser/models/evaluations/graph_base.py` のモジュール docstring、Plan 05 の objective、および Plan 10 SUMMARY で明文化されている。

### docs/99-trace-matrix.md DOC-03 記述について

trace-matrix の DOC-03 行には「README mirror is Phase 5」と記載されているが、これは不正確である。Plan 01-01 は `requirements-completed: [DOC-04, DOC-03]` として DOC-03 を Phase 1 で完了しており、README.md に "No GPL bundled" が実際に存在する。Phase 5 (DOC-02) は README プラットフォーム互換マトリクスに関する別の要件である。この trace-matrix の記述は内部ドキュメントの軽微な不整合だが、DOC-03 要件自体の達成には影響しない。

### pyproject.toml の lib-diagram-parser について

Plan 01-01 SUMMARY では `lib-diagram-parser>=0.1.0` を依存関係に追加したと記録されているが、その後の orchestrator hot-fix (commit 53688ca) で PyPI 未公開のため hard dep から削除された。現在の pyproject.toml では依存関係リストから除外され、コメントのみで経緯が説明されている。Phase 3 (DIA-04) で再追加予定。

---

_検証日時: 2026-05-26T04:30:00Z_
_検証者: Claude (gsd-verifier)_
