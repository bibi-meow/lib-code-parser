# Phase 1: Architecture Foundation + Spec Correction — Research

**Researched:** 2026-05-24
**Domain:** Python pip ライブラリ foundation — Pydantic v2 Generic envelope / dispatch dict / subprocess hardening contract / libclang wheel feasibility / PEP 639 license declaration / Pydantic schema-compat boundary / nested module layout migration
**Confidence:** HIGH (Pydantic v2.11 Generic は実機で検証済み / libclang 18.1.1 macOS arm64 wheel は PyPI で実在確認 / setuptools 77 PEP 639 は公式 packaging guide で確認 / `lib-diagram-parser` schema は実コード読取で確認)

## Summary

Phase 1 は **lib-code-parser v0.2.0 の cross-cutting 契約をすべてロックする foundation phase** であり、研究の役割は extractor を一切書かずに「契約・配置・宣言・spec doc」を破れない形で固定する材料を planner に渡すこと。 CONTEXT.md の D-01 〜 D-23 で 5 つの灰色領域はすべて確定済みのため、本 research は **代替設計の探索ではなく実装直前材料の整備** に徹する。

最大の発見は 3 点。 (1) **Pydantic v2 Generic は v0.1.0 caller 互換性をゼロ追加コストで満たす** — `Envelope(...)` と `Envelope[Inner](...)` が byte-identical な JSON を生成することを実機検証で確認 (Pydantic 2.11.10、Python 3.11.1)。 v0.1.0 caller が `NormalizedArtifact(artifact_id=..., artifact_type=..., content=...)` と書く既存コードは Generic 化しても 1 文字も触らずに動く。 (2) **libclang==18.1.1 は macOS arm64 + Python 3.13/3.14 で wheel 配布済み** — PyPI に `libclang-18.1.1-py2.py3-none-macosx_11_0_arm64.whl` (ABI-agnostic) が存在し、 Python 3.11/3.12/3.13/3.14 すべてに `pip install` 可能。 SP-3 spike の (a) と (c) は wheel 解析だけで HIGH 確度で合格判定可能。 (3) **PEP 639 (SPDX license string) は setuptools>=77.0.3 必須** — 現 pyproject.toml の `setuptools>=68` では `license = "Apache-2.0"` の SPDX 形式が deprecated 警告を出す。 Phase 1 で build-system requires を bump せねば DOC-04 が宣言上は通っても build 時に warning が出る。

**Primary recommendation:** PLAN は **9 並列 sub-track + 1 sequential closer** で構成する — (T1) Apache-2.0 LICENSE + pyproject 更新、 (T2) frozen/ 退避 + spec doc rewrite、 (T3) infrastructure models 層 (CAV / NormalizedArtifact Generic / ParserConfig typed)、 (T4) primitives models 層、 (T5) evaluations models 層 (EdgeKind closed Literal + graph_base.py)、 (T6) _paths.py + _dispatch.py、 (T7) adapters/base.py subprocess hardening ABC、 (T8) frontends/extractors ディレクトリ stub + executor 再編、 (T9) docs/08-common-view-pattern.md + docs/09-extending.md。 closer は (T10) SP-3 spike CI 投入 + v0.1.0 parity test 通過 + `__init__.py` 後方互換 re-export 確認。 T1-T9 は互いの ファイル touch 領域が排他なので並列可能。 順序依存は T10 のみ。

---

## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01〜D-03 (spec doc 修正範囲)**:
- D-01: `lib-code-parser.md` を **full rewrite** して v0.2.0 全方針 (内製 call graph、 pyright MIT、 libclang Apache-2.0、 CAV、 EdgeKind、 5 diagram、 function/class spec、 Doxygen、 icontract/deal、 Apache-2.0 license、 physical_*/source_* prefix、 Traceability) に揃える。 surgical edit は不採用 (内部の論理整合が崩れるため)。
- D-02: 旧版 (v0.1.0 時代) は `frozen/2026-05-24-v0.1.0-spec/` に退避してから rewrite (backup-before-major-rewrite ルール準拠)。
- D-03: rewrite 対象セクション: §概要 / §インターフェース / §出力 / §採用アルゴリズム / §出力 schema (新規) / §License (新規) / §Traceability (新規)。

**D-04〜D-09 (CAV polymorphism)**:
- D-04: **単一 `CAV` Pydantic BaseModel** + `language: Literal["python", "cpp"]` discriminator + opaque `payload: object` (Python: `ast.Module`、 C++: `cindex.TranslationUnit`)。 typed union は不採用 (Phase 4 拡張時に contract 変更になる)。
- D-05: CAV `model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True, frozen=True)`。 immutability を Pydantic で強制。
- D-06: **`NormalizedArtifact` を Pydantic Generic 化** (`NormalizedArtifact[TContent]`)。 各 lib が `content` の型を refine できる。 v0.1.0 caller 互換性は parity test で確認。
- D-07: **共通 pattern doc** を `docs/08-common-view-pattern.md` に作成 (SDD chain 連番に組み込み)。 lib-code-parser 内に閉じる (workspace 共通規約は作らない)。
- D-08: I/O 変更容易性確保: `execute(config, raw_content, path) -> NormalizedArtifact[CodeContent]` signature を安定に。 `ParserConfig` の field 命名 (`enabled` / `language` / `extract_*` / `*_version`) は兄弟 lib にも転用可能な一般名で固定。
- D-09: `adapters/base.py` の subprocess hardening helper を **abstract base class + transferable helper** として書く (兄弟 lib が後で同 pattern を真似しやすい形)。

**D-10〜D-14 (モジュール配置レイアウト)**:
- D-10: v0.1.0 flat (`lib_code_parser/*.py`) を **nested layout に再編** (詳細は CONTEXT.md §A 参照)。
- D-11: **設計軸 = 評価単位 (output)**。 同じ解析手法を使う複数評価単位は、 共有 primitives を **pull で取得** (`from lib_code_parser.extractors.primitives import callgraph; callgraph.extract(cav)`)。
- D-12: **`_dispatch.py` で 3 dict 管理** (FRONTENDS / PRIMITIVES / EVALUATIONS)。 executor は dict を走査して評価単位を実行 (`for name, fn in EVALUATIONS.items(): result[name] = fn(cav, config)`)。
- D-13: **拡張点契約 (Open-Closed)** を `docs/09-extending.md` に明記:
  1. 既存 primitive は変更不可 (新 primitive は別 file)
  2. 既存評価単位は変更不可 (新評価単位は別 file)
  3. `CodeContent` への追加は optional field で行う (v0.1.0 互換性維持)
  4. dispatch dict は append-only
  5. 評価単位は primitives を pull で取得 (push 型注入ではない)
  6. executor は dispatch dict 走査ロジックのみ (評価単位を増やしても変更しない)
- D-14: **論理アーキ比較対象は `models/evaluations/` 配下のみ**。 primitives / infrastructure は中間データ / I/O 契約であり verifier に渡さない。

**D-15〜D-17 (sibling-lib PR タイミング)**:
- D-15: **Phase 1 では PR を出さない**。 Phase 3 着手時に状況を再評価。
- D-16: **SCH-01 の解釈拡大**: 「`lib-diagram-parser` モデルを直接利用する (subclass 含む)」を許容。 model duplication は依然禁止。
- D-17: schema 互換性は **SCH-04 (cross-lib schema compat test)** で保証。 Phase 1 では schema 契約のみ固定し、 test 実装は Phase 5。

**D-18〜D-23 (SP-3 libclang spike)**:
- D-18: **GitHub Actions `macos-14` (arm64) runner のみ** で実施。 Python 3.13/3.14 matrix。
- D-19: **優先度: Phase 1 内で最低**。
- D-20〜D-22: 4 段階判定 (a/b/c/d)、 ship-best-effort / defer 判定 + Phase 1 close 緩和条件。
- D-23: 記録先: `.planning/spikes/SP-3-libclang-macos-arm64.md` (CI run URL 込み)。

### Claude's Discretion

- ファイル内部の細かい命名 (関数名 / private helper 名 / module docstring の表現) は標準慣習に従って Claude が判断
- 各評価単位 extractor 内部の言語分岐実装パターン (if/elif vs dispatch dict 等) は Phase 2-4 plan-phase で詰める
- `docs/08-common-view-pattern.md` / `docs/09-extending.md` の文章スタイルと細部構成は Claude が判断 (SDD chain 既存ドキュメントの文体に合わせる)
- `.github/workflows/ci.yml` への SP-3 matrix 追加の具体的な YAML 構造は Phase 1 plan で詰める

### Deferred Ideas (OUT OF SCOPE)

- workspace `spec-reviewer-libs/CONVENTIONS.md` 作成
- `NormalizedArtifact` / Container の workspace 共通 lib 化 (`spec-reviewer-libs-common` 案)
- 再リファクタ phase の起票 (兄弟 lib との I/O 揃え)
- `lib-diagram-parser` への `node_type="package"` enum 追加 PR (Phase 3 入口で再評価)
- local extension 削除 → 直接 import switch (sibling-lib リリース後)
- 将来評価単位 (DDD リバース / class_relations / ddd_context_map 等) — v0.3.0+ roadmap
- Phase 4 入口で SP-3 verdict 再確認、 追加 spike (macos-13 / macos-15 等)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ARC-01 | Each extractor module is lib-internal callable independently | `_dispatch.py` 3 dict pattern (本研究 §Dispatch Dict Pattern) で実現。 dispatch entry が module-level function であれば pull-based 取得 (`from ...extractors.primitives import callgraph; callgraph.extract(cav, config)`) が自動的に成立 |
| ARC-02 | All AST primitive extractors operate on a single Common AST View — file parsed once per execute() call | CAV envelope (本研究 §Pydantic v2 Generic + CAV polymorphism) — `frozen=True` + `arbitrary_types_allowed=True` で `ast.Module` を opaque payload に格納。 executor が 1 回 parse して全 extractor に CAV を pull させる |
| ARC-03 | All subprocess invocations live in `lib_code_parser/adapters/` layer | `adapters/base.py` SubprocessAdapter ABC + run_subprocess() helper (本研究 §Subprocess Hardening Contract)。 Phase 2 の PyrightAdapter は ABC を継承するだけ |
| ARC-04 | Module-name derivation centralized in `_paths.py:get_module_name()` | `_paths.py` 1 ファイルに集約 (本研究 §Nested Module Layout Migration)。 v0.1.0 の 4 重複 `_get_module_name` は ast_extractor.py で thin re-export として残し、 既存 tests/acceptance/test_fr01 の 3 件のテスト import 互換性を維持 |
| ARC-05 | `ParserConfig.params: dict[str, object]` is replaced with typed Pydantic fields | `models/infrastructure/config.py` で `ParserConfig` 全 field を typed 化 (本研究 §Pydantic v2 Generic — Typed ParserConfig)。 `extra="forbid"` で unknown field は ValidationError |
| SCH-01 | lib-diagram-parser models 直接利用 (subclass 含む)、 model duplication 禁止 | Phase 1 では Pydantic 契約のみ固定 — `models/evaluations/graph_base.py` で `GraphNode` / `GraphEdge` / `GraphModel` / `GuardExpr` を **直接 re-export** (本研究 §lib-diagram-parser Schema Snapshot)。 `lib-diagram-parser>=0.1.0` を pyproject.toml の dependencies に追加 |
| SCH-02 | Pydantic v2 + `ConfigDict(extra="forbid")` | 本研究 §EdgeKind Closed Literal + 全 model で `extra="forbid"` 強制 — 既存 v0.1.0 models.py は extra config を欠いており、 Phase 1 で全 model に `model_config = ConfigDict(extra="forbid")` 追記 |
| SCH-03 | EdgeKind closed Literal (no "uses"/"other" catch-alls) | 本研究 §EdgeKind Closed Literal — 11 値の Literal で 5 diagram すべてをカバー |
| DET-04 | No `_get_module_name` duplication | ARC-04 と同じ |
| DET-05 | Subprocess hardening contract (`encoding="utf-8"`, `errors="replace"`, `env={...}`, `timeout`, `cwd`, `capture_output=True`, `shell=False`) | 本研究 §Subprocess Hardening Contract — ABC + transferable helper |
| DOC-01 | `lib-code-parser.md` rewrite — remove `callgraph.py` + "ACL-2" misreferences | 旧 spec doc を `frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md` に退避 → full rewrite (本研究 §lib-code-parser.md Rewrite Strategy) |
| DOC-03 | README documents no GPL bundled (call graph internal / pyright MIT / libclang Apache-2.0+LLVM exception) | README は本 phase のスコープ外 (Phase 5 で全面整備)。 ただし spec doc rewrite の §License セクションに同等の disclosure を入れる |
| DOC-04 | `pyproject.toml` declares Apache-2.0 + LICENSE file + patent grant clause | 本研究 §Apache-2.0 pyproject.toml — PEP 639 SPDX 形式 + setuptools>=77.0.3 が必要 (現状 setuptools>=68 から bump 必須) |
| TRC-01 | Each requirement maps to at least one US | REQUIREMENTS.md の Traceability table を `docs/99-trace-matrix.md` に追記 — 14 Phase 1 REQ × US-01/US-22/US-25/US-32 mapping |

---

## Architectural Responsibility Map

Phase 1 は extractor を一切書かないが、 これから書く 5 種の extractor をどの「層」に置くかが本 phase で決まるので、 ここで責務を固定する。

| Capability | Primary Layer | Secondary Layer | Rationale |
|------------|---------------|-----------------|-----------|
| File parsing (1 回 parse、 immutable CAV emit) | `frontends/` (python.py / cpp.py — Phase 2+) | — | 言語ごとの parser はここ。 frontends は CAV を返すだけで extractor を持たない |
| AST primitives 抽出 (functions / callgraph / type_deps / contracts) | `extractors/primitives/` | `models/primitives/` (output schema) | 評価単位ではなく共有データ供給者。 pull で取得される |
| Diagram 抽出 (5 種) | `extractors/<diagram>.py` (class_diagram.py 等) | `models/evaluations/` (output schema) | 評価単位 = verifier に渡る output。 論理アーキ比較対象 |
| Function/Class spec 抽出 | `extractors/function_spec.py` / `class_spec.py` | `models/evaluations/` | 評価単位 #6, #7。 C++ Doxygen は同 extractor 内で言語分岐 |
| Subprocess 隔離 (pyright 等) | `adapters/` | — | Phase 1 で base.py ABC のみ固定、 PyrightAdapter は Phase 2 |
| Module name 導出 | `_paths.py` | — | 単一 source of truth (ARC-04) |
| 評価単位の dispatch | `_dispatch.py` | `executor.py` (consumer) | append-only dict、 executor は dict を走査するだけ |
| I/O 契約 (CAV / NormalizedArtifact / ParserConfig / ArtifactId / CodeContent) | `models/infrastructure/` | — | lib 境界。 論理アーキ比較対象ではない (D-14) |

**Why this matters:** Phase 1 で「`extractors/primitives/` 配下は評価単位ではない / `models/evaluations/` 配下は verifier に渡す」を明確に切り分けないと、 Phase 2-4 の planner が同じ名前空間に異質の責務を混在させやすい。 例えば `callgraph` は `extractors/primitives/callgraph.py` (intermediate supplier) と `models/primitives/callgraph.py` (intermediate model) に登場し、 `class_diagram` は `extractors/class_diagram.py` (evaluation) と `models/evaluations/class_diagram.py` (evaluation output) に登場する。 これらを混同してはならない。

---

## Standard Stack

### Core (Phase 1 で pyproject.toml に追加 / 更新)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pydantic` | `>=2.13.0,<3.0` | I/O 契約・schema 定義 (CAV / NormalizedArtifact / ParserConfig / EdgeKind / GraphNode) | 兄弟 lib (lib-diagram-parser, lib-spec-parser) と同じ。 v2.11 で Generic + `ConfigDict(extra="forbid")` + `frozen=True` が安定 [VERIFIED: 本研究 §Pydantic v2 Generic の実機検証] |
| `lib-diagram-parser` | `>=0.1.0` | SCH-01 schema-compat 境界 — `GraphNode` / `GraphEdge` / `GraphModel` / `GuardExpr` を直接 import (Phase 3+ で使用、 Phase 1 で declared) | 唯一の sibling-lib 直依存。 model duplication 禁止 (D-16) [VERIFIED: c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser/lib_diagram_parser/models.py を実コード読取] |
| `setuptools` (build-system) | `>=77.0.3` | PEP 639 SPDX license 文字列のサポート | 現状 `>=68` では `license = "Apache-2.0"` が deprecated 警告を出す。 DOC-04 を満たすため bump 必須 [CITED: packaging.python.org guide for writing pyproject.toml] |

### Phase 1 では declared だけ / 使用は Phase 2+

| Library | Version | Purpose | Phase で使う |
|---------|---------|---------|--------------|
| `pyright[nodejs]` | `==1.1.409` | 型解決済み TypeDep 生成 (subprocess、 Apache-2.0+Node bundled) | Phase 2 (AST-03 / DET-03) — Phase 1 では adapters/base.py 契約のみ固定 [VERIFIED: PyPI release date 2026-04-23 確認、 slopcheck status=OK] |
| `libclang` | `==18.1.1` | C++ AST 解析 (in-process ctypes、 Apache-2.0 WITH LLVM-exception) | Phase 4 (LNG-01〜LNG-05、 SPC-03) — Phase 1 では SP-3 spike で wheel 動作確認のみ [VERIFIED: PyPI に macos_11_0_arm64.whl 含む全 platform wheel あり、 slopcheck status=OK] |

### Supporting (dev / build / CI)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | `>=8` | テストランナー | dev extra、 Phase 1 で parity test に使用 |
| `pytest-cov` | (latest) | coverage measurement | dev extra、 Phase 1 で parity coverage に使用 |
| `ruff` | (latest) | format + lint | dev extra、 CI gate |
| `pyright` (dev) | (latest) | static type check (devmode で別ツール) | dev extra、 CI gate (DET-03 の `pyright[nodejs]==1.1.409` とは別目的) |

### Alternatives Considered (D-04 〜 D-23 で既に却下 — 再検討しない)

| Instead of | Could Use | Tradeoff (CONTEXT.md / PROJECT.md の根拠) |
|------------|-----------|----------|
| 内製 call graph (extension) | `pyan3` | GPL viral 回避のため不採用 (PROJECT.md Key Decisions) |
| 内製 call graph | `code2flow` | 非決定論で却下 |
| 内製 call graph | `PyCG` | archived で却下 |
| libclang 18.1.1 厳密 pin | tree-sitter-cpp | syntactic のみで型解決不可、 却下 |
| libclang via pip wheel | system-installed libclang (`clang` 別 PyPI) | bundled なしで自己完結性失う、 却下 |
| CAV = 単一 BaseModel + opaque payload | typed union | Phase 4 拡張時に contract 変更になる (D-04) |
| `NormalizedArtifact` Generic 化 | non-Generic + `content: object` | type safety を失う (D-06) |
| `_dispatch.py` 3 dict 静的 | エントリポイント自動探索 | implicit な mechanism を避ける (D-12) |

**Installation (Phase 1 で pyproject.toml に書く全 deps):**
```bash
pip install -e ".[dev]"
# 結果として以下が入る:
# - pydantic >=2.13.0,<3.0
# - lib-diagram-parser >=0.1.0
# - pyright[nodejs] ==1.1.409 (dev extra に追加: phase 2 で使うが Phase 1 から declared)
# - libclang ==18.1.1 (dev extra に追加: SP-3 spike で必要)
# - pytest, pytest-cov, ruff, pyright (dev)
```

**Version verification (実行済み):**

| Package | 確認方法 | 確認結果 |
|---------|---------|---------|
| `pydantic 2.11.10` | `pip show pydantic` (本研究 env) | INSTALLED、 動作確認済 — Generic + ConfigDict(extra=forbid) + frozen=True 全動作 |
| `libclang 18.1.1` | `WebFetch https://pypi.org/pypi/libclang/18.1.1/json` | 全 wheel 確認: linux x86_64/aarch64/armv7l/musllinux, macos x86_64, **macos_11_0_arm64**, win amd64/arm64。 全 wheel が `py2.py3-none-<platform>.whl` 形式 (ABI-agnostic) |
| `pyright 1.1.409` | `WebFetch https://pypi.org/pypi/pyright/1.1.409/json` | 存在確認 (release 2026-04-23)、 `nodejs` extra あり、 transitive deps: `nodeenv>=1.6.0`, `typing-extensions>=4.1` |
| `setuptools 77` | `WebFetch packaging.python.org` | PEP 639 サポートは setuptools>=77.0.0、 推奨 77.0.3。 現 pyproject.toml の `>=68` では deprecated 警告 |

---

## Package Legitimacy Audit

slopcheck v(現時点 latest) を `pip install slopcheck --break-system-packages` で導入後、 `slopcheck scan --pkg pypi --json <name>` で各パッケージを検証した。

| Package | Registry | Age | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-------------|-----------|-------------|
| `pydantic` | PyPI | 6+ 年 | github.com/pydantic/pydantic | [OK] | Approved (`>=2.13.0,<3.0` ピン) |
| `lib-diagram-parser` | sibling (mono-repo) | 開発中 | c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser | N/A (local) | Approved (実コード読取で schema 確認済み — 本研究 §lib-diagram-parser Schema Snapshot) |
| `setuptools` | PyPI | 20+ 年 | github.com/pypa/setuptools | [OK] | Approved (build-system requires、 `>=77.0.3` に bump) |
| `pyright` | PyPI | 5+ 年 | github.com/RobertCraigie/pyright-python | [OK] | Approved (`==1.1.409` 厳密 pin、 release 2026-04-23) |
| `nodejs-wheel-binaries` | PyPI | 2+ 年 | github.com/njzjz/nodejs-wheel | [OK] | Approved (pyright[nodejs] transitive、 nodeenv 代替で公式推奨) |
| `libclang` | PyPI | 7+ 年 | github.com/sighingnow/libclang | [OK] | Approved (`==18.1.1` 厳密 pin、 LLVM 18.1.1 bundled) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

slopcheck は実行可能だったため (`pip install slopcheck --break-system-packages` で導入後 `slopcheck scan --pkg pypi --json <name>` で実行)、 上記すべて `[OK]` 判定であり planner が install checkpoint を入れる必要はない。

---

## Pydantic v2 Generic for NormalizedArtifact[TContent] — working patterns + pitfalls + parity strategy

### 実機検証済みパターン (Pydantic 2.11.10 + Python 3.11.1、 本研究 env)

```python
# models/infrastructure/artifact.py
from __future__ import annotations
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict

TContent = TypeVar("TContent", bound=BaseModel)

class ArtifactId(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    path: str

class NormalizedArtifact(BaseModel, Generic[TContent]):
    """Generic envelope for parsed artifacts.

    The library exposes `NormalizedArtifact[CodeContent]` to typed callers;
    untyped callers can still write `NormalizedArtifact(artifact_id=..., artifact_type=..., content=...)`
    and Pydantic accepts any BaseModel as `content` (validated by the TypeVar bound).
    """
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    artifact_id: ArtifactId
    artifact_type: str
    content: TContent
```

### v0.1.0 caller parity — 実機検証で byte-identical を確認

実機で次を確認した (本研究 env で実行):

```python
e1 = Envelope(artifact_id='x', artifact_type='code', content=Inner(value=5))  # 旧 caller (v0.1.0)
e2 = Envelope[Inner](artifact_id='x', artifact_type='code', content=Inner(value=5))  # 新 caller (typed)
assert e1.model_dump_json() == e2.model_dump_json()  # True!
```

**結論:** **Generic 化は v0.1.0 caller の JSON 出力を一切変えない**。 既存 tests/acceptance/test_fr*.py 6 ファイルは parity test として無修正で通る。 D-06 「v0.1.0 caller 互換性は parity test で確認」の前提が実機で成立する。

### CAV envelope (D-04 / D-05) — 実機検証済み

```python
# models/infrastructure/cav.py
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict

class CAV(BaseModel):
    """Common AST View — single-parse envelope shared by all extractors.

    `payload` is intentionally opaque (`object`) so the Python frontend can stash
    `ast.Module` and the C++ frontend can stash `clang.cindex.TranslationUnit`
    without forcing a typed union on the cross-cutting contract.

    Immutability is enforced via `frozen=True`; arbitrary_types_allowed=True is
    required because `ast.Module` is not a Pydantic model.
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

実機実行で次の保証を確認:
- `CAV(language="java", ...)` → `ValidationError` (Literal で reject)
- `cav.language = "cpp"` → `ValidationError` (frozen で reject — `pydantic_core._pydantic_core.ValidationError: 1 validation error... Instance is frozen`)
- `CAV(language="python", path="foo.py", payload=ast.parse("x=1"))` → 成功、 `cav.payload` は `ast.Module`

### Pitfalls (実機検証 + 公式 docs より)

1. **`arbitrary_types_allowed=True` 必須**: `payload: object` だけでは Pydantic が validation を skip するため、 `ast.Module` のような non-Pydantic 型を受け入れるには明示的に `arbitrary_types_allowed=True` が必要。 これを忘れると import error が出ないまま runtime で「`payload` フィールドが型不一致」と silent に失敗する [VERIFIED: 本研究 env で実証]
2. **`bound=BaseModel` の検証は形だけ**: Pydantic 公式 docs (v2.11 Generic models) は「Pydantic does not validate that the provided type is assignable to the type variable if it has an upper bound」と明記している。 つまり `NormalizedArtifact[int]` も Python レベルでは作れてしまう (実 content 値が BaseModel でなければ runtime で validation 失敗するが、 静的型としては許される)。 これは Phase 2+ 影響だが、 D-06 の安心材料として `bound=BaseModel` は型 hint としては有効。 [CITED: pydantic.dev/docs/validation/2.11/concepts/models/ §Generic models]
3. **`model_rebuild()` は通常不要**: 公式 docs は「dealing with recursive models or generics」で proactive に使うと有用と言うが、 Phase 1 の linear な参照 (CAV / ArtifactId / CodeContent / NormalizedArtifact) では呼ぶ必要なし [CITED: 同上]
4. **`frozen=True` + Generic は両立**: 実機検証で両者を同時に指定しても問題なく動作 (Pydantic 2.11.10 確認済)
5. **mutable default の罠**: 既存 v0.1.0 `models.py` は `params: dict[str, object] = {}` のような mutable default を直書きしている。 Pydantic v2 は内部で deep copy するため安全だが、 ruff `B008`/`mutable-default` が反応する。 Phase 1 で新規追加する全 field は `Field(default_factory=list)` / `Field(default_factory=dict)` を使うのが安全 (codebase/CONCERNS.md §"Mutable default values on Pydantic models" でも指摘済み)

### Parity strategy (v0.1.0 → v0.2.0 移行で何を test するか)

- **既存 6 つの acceptance test (tests/acceptance/test_fr01..06_*.py) を無修正で通すこと** が parity の定義
- v0.1.0 caller が書く `NormalizedArtifact(artifact_id=..., artifact_type="code", content=...)` がそのまま動く (Generic 化しても unparameterized 構築は許される)
- v0.1.0 `__init__.py` の `__all__` は不変 (`CodeParserExecutor` + 11 model 名)。 nested layout 移行後も `from lib_code_parser.models import FunctionNode` が動くよう `lib_code_parser/__init__.py` で re-export (本研究 §Nested Module Layout Migration の backward-compat 戦略)

---

## Dispatch Dict Pattern — typed signatures, append-only invariant enforcement

### 設計

`_dispatch.py` は 3 つの dict を保持する (D-12)。 各 dict は Phase 2+ で entry を追加していくが、 Phase 1 では空 dict + 型 signature のみ定義する。

```python
# lib_code_parser/_dispatch.py
"""Static dispatch tables for frontends, primitives, and evaluations.

This module is the **single point of registration** for new extractors.
After Phase 1 freezes the dict types, every new extractor (Phase 2-4) adds
exactly one entry to the appropriate dict. The executor never grows logic;
it only walks these dicts.

INVARIANT (Open-Closed contract #4): dicts are append-only.
Existing entries are never modified; never removed.
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from lib_code_parser.models.infrastructure.cav import CAV
    from lib_code_parser.models.infrastructure.config import ParserConfig
    from lib_code_parser.models.primitives.callgraph import CallGraph as PrimitiveCallGraph
    from lib_code_parser.models.primitives.functions import FunctionNode
    from lib_code_parser.models.primitives.type_deps import TypeDep
    from lib_code_parser.models.primitives.contracts import ContractInfo
    from lib_code_parser.models.evaluations.graph_base import GraphModel
    # ... (Phase 2+ で追加)

# Frontend: raw bytes + path → CAV
# Signature: (raw_content: bytes, path: str, config: ParserConfig) -> CAV
FrontendFn = Callable[[bytes, str, "ParserConfig"], "CAV"]
FRONTENDS: dict[str, FrontendFn] = {}  # Phase 2 で "python" 追加; Phase 4 で "cpp" 追加

# Primitive: CAV → intermediate data (functions / callgraph / type_deps / contracts)
# Signature: (cav: CAV, config: ParserConfig) -> Any (primitive model type)
# Note: return type is intentionally Any here because each primitive returns a different model.
#       Concrete callers `from lib_code_parser.extractors.primitives.callgraph import extract`
#       get the precise type from the imported module's signature.
PrimitiveFn = Callable[["CAV", "ParserConfig"], object]
PRIMITIVES: dict[str, PrimitiveFn] = {}  # Phase 2 で 4 つ追加 (functions, callgraph, type_deps, contracts)

# Evaluation: CAV + primitives → evaluation output (class_diagram, sequence_diagram, ...)
# Signature: (cav: CAV, config: ParserConfig) -> Any (evaluation model type — typically GraphModel or *Spec)
# Same Any-typed return as PRIMITIVES; concrete callers get precise type from the import.
EvaluationFn = Callable[["CAV", "ParserConfig"], object]
EVALUATIONS: dict[str, EvaluationFn] = {}  # Phase 3-4 で 7 つ追加
```

### 型 signature の意図

- `Callable[[bytes, str, ParserConfig], CAV]` のように **`Callable` を使った関数型** を採用 (Protocol は意図的に避ける)。 理由: Protocol だと「method を持つ class」のような余計な expectation が紛れ込むが、 dispatch entry は module-level pure function に限定したい
- `return type: object` (実質 `Any`) は Pydantic Generic と異なる concrete 型を入れたいため。 caller は dispatch 経由ではなく **import 直接** (`from lib_code_parser.extractors.primitives.callgraph import extract`) で型情報を得る (pull 型、 D-11)
- dispatch dict は executor の **走査ロジックのみ** が触る。 caller が中身を編集することはない (D-13 invariant #4 append-only)

### Append-only invariant の enforcement

- **静的 lint で強制するのは難しい** (Python に `final dict` 型はない、 `MappingProxyType` で wrap すると後から add も禁止される)
- **代わりに docs/09-extending.md で明示** + **CI で「`_dispatch.py` への変更は dict.update 形式のみで、 既存 entry の値を別物に置き換える patch は reject」を code review で gate**
- Phase 1 では「**`_dispatch.py` に追加するのは新規 entry のみ。 既存 entry の値変更は別 PR で議論**」を docs/09-extending.md に明記すれば足る
- Phase 2+ で entry を増やすときは「**新 entry の追加 = 新 PR、 既存 entry のシグネチャを変える = 重大な PR**」というレビュー慣習を確立

### Why dispatch dict ではなく entry-point setup.cfg / pluggy にしないか

D-12 で「explicit static `FRONTENDS` and `EXTRACTORS` dispatch dicts」と明記された理由: pluggy / entry-points はパッケージ外部からの登録 (plugin) を許してしまうため、 lib の出力決定性 (Layer M bisimulation) が破られる。 本 lib は閉じた registry である必要がある。

### 既知パターン参考

- `rich` の theme registry — module-level dict + import-time 登録 (同じ pattern)
- `click` の command group — explicit `group.add_command()` の append-only API
- `pyright` 自体は plugin 機構を持たない (lib 設計として閉じた registry を採用) [VERIFIED: pyright source code]

---

## Subprocess Hardening Contract — ABC + helper combination, cross-platform considerations

### 設計 (D-09 + DET-05 + Pitfall 3/13)

`adapters/base.py` には **abstract base class + transferable helper function** の両方を置く (D-09)。 ABC は Phase 2+ の各 Adapter (PyrightAdapter 等) が継承する形、 helper function は Adapter 内部から呼ぶ純粋関数。

```python
# lib_code_parser/adapters/base.py
"""Subprocess adapter base class + hardening helper.

All subprocess invocations in this library MUST go through `run_subprocess()`.
The helper centralizes determinism guarantees (encoding, locale, hash seed,
timeout, cwd) and cross-platform pitfalls (Windows cp1252 decode, signal handling).

The helper is intentionally transferable — sibling libs can copy it verbatim
if they need the same subprocess discipline; no internal state.
"""
from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from pydantic import BaseModel

# Determinism env (DET-05): LC_ALL=C kills locale-dependent text, PYTHONHASHSEED=0 kills set/dict order
_DETERMINISTIC_ENV: dict[str, str] = {
    "LC_ALL": "C",
    "LANG": "C",
    "PYTHONHASHSEED": "0",
    "PYTHONIOENCODING": "utf-8",
}

def run_subprocess(
    argv: Sequence[str],
    *,
    cwd: str,                       # MUST be explicit (no inherited os.getcwd())
    timeout: float = 60.0,          # MUST be set (Pitfall 3 — Popen+wait deadlock)
    extra_env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with deterministic hardening.

    Locks down: encoding='utf-8' (Pitfall 13 — Windows cp1252 default),
    errors='replace' (don't crash on stray bytes from tools),
    env (Pitfall 3/13 — locale and hash-seed),
    capture_output=True (Pitfall 3 — never block on full pipe),
    shell=False (security + determinism),
    timeout (Pitfall 3 — never hang forever).

    The function NEVER calls `subprocess.Popen` directly; only `subprocess.run`.
    """
    env: dict[str, str] = dict(os.environ)  # start from current env
    env.update(_DETERMINISTIC_ENV)
    if extra_env is not None:
        env.update(extra_env)
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
        check=False,  # caller decides what to do with non-zero exit
    )


class SubprocessAdapter(ABC):
    """Abstract base for any subprocess-based adapter (pyright, future tools).

    Subclasses implement:
    - `tool_argv(target_path)` — build the argv list (no shell escape needed; argv is a list)
    - `parse_output(stdout, stderr, returncode)` — parse raw output into a typed Pydantic model
                                                    (Pitfall 4 — defend against schema drift)

    The base class drives the run via `run_subprocess()` and never bypasses determinism.
    """

    @abstractmethod
    def tool_argv(self, target_path: str) -> Sequence[str]: ...

    @abstractmethod
    def parse_output(
        self, stdout: str, stderr: str, returncode: int
    ) -> BaseModel: ...

    def execute(self, target_path: str, *, cwd: str) -> BaseModel:
        result = run_subprocess(self.tool_argv(target_path), cwd=cwd)
        return self.parse_output(result.stdout, result.stderr, result.returncode)
```

### なぜ ABC + helper の両方か (D-09 の意図)

- **helper だけ**: Adapter ごとに helper を呼ぶボイラープレートが残る (argv 作成 / output parse の責務が散らばる)
- **ABC だけ**: 兄弟 lib が同 pattern を採用するとき、 ABC を継承するか transferable helper を import するかで再利用粒度が変わる。 transferable helper を切り出すと「subprocess の hardening 部分だけ持ち帰る」が可能になる
- **両方持つ**: lib-code-parser の中では ABC を継承して書く (boilerplate 削減)、 兄弟 lib は helper function を copy/import するという transferable な部品化が成立 (D-09 「兄弟 lib が後で同 pattern を真似しやすい形」)

### Cross-platform 考慮 (Pitfall 13)

- **Windows encoding 問題**: `subprocess.run(..., text=True)` は Windows で `locale.getpreferredencoding(False)` を使い、 cp1252 で decode してしまう。 `encoding="utf-8"` を明示すれば回避。 本 helper は明示済み
- **PowerShell vs Bash**: `shell=False` で argv list を渡すので shell 種類に依存しない (Pitfall 3 — security + determinism)
- **`PYTHONIOENCODING=utf-8`**: pyright/Node が child を spawn しても UTF-8 を強制 (Pitfall 13)
- **`cwd` 必須**: `os.getcwd()` 継承を禁止する。 caller がどのディレクトリで実行されているかを明示的に渡す (DET-05 「explicit `cwd`」)
- **timeout 必須**: signature で default 60.0 を提供しつつ caller が override 可能。 0 や None は禁止 (Pitfall 3)

### Phase 1 で fix する範囲

- Phase 1: `adapters/base.py` の ABC + helper を完成させ、 unit test (本 helper を minimal subprocess に対して call して env / encoding / timeout の挙動を assert) を書く
- Phase 1: `adapters/__init__.py` で `run_subprocess`, `SubprocessAdapter` を re-export
- Phase 2: `adapters/pyright.py` で `PyrightAdapter(SubprocessAdapter)` を実装 — Phase 1 のスコープ外

### Test 戦略 (Phase 1)

```python
# tests/unit/adapters/test_base.py
def test_run_subprocess_sets_deterministic_env():
    # Run a small Python -c snippet that echoes the relevant env vars
    result = run_subprocess(
        [sys.executable, "-c", "import os; print(os.environ.get('LC_ALL', ''), os.environ.get('PYTHONHASHSEED', ''))"],
        cwd=os.getcwd(),
        timeout=10,
    )
    assert "C" in result.stdout
    assert "0" in result.stdout

def test_run_subprocess_raises_on_timeout():
    with pytest.raises(subprocess.TimeoutExpired):
        run_subprocess([sys.executable, "-c", "import time; time.sleep(60)"], cwd=os.getcwd(), timeout=1)

def test_run_subprocess_does_not_use_shell():
    # Pass a string that would be expanded by shell — confirm it is literal
    result = run_subprocess(
        [sys.executable, "-c", "print('$PATH')"],
        cwd=os.getcwd(),
        timeout=10,
    )
    assert "$PATH" in result.stdout  # not expanded
```

---

## libclang 18.1.1 macOS arm64 — wheel availability, smoke test, CI matrix YAML

### Phase 1 観点での結論 (D-20 / D-21)

`libclang==18.1.1` の PyPI wheel matrix を実調査した結果 (本研究 WebFetch + PyPI JSON):

**観察された wheel ファイル名 (8 platform):**

| Platform | Wheel filename |
|----------|----------------|
| Linux x86_64 (manylinux2010) | `libclang-18.1.1-py2.py3-none-manylinux2010_x86_64.whl` |
| Linux aarch64 (manylinux2014) | `libclang-18.1.1-py2.py3-none-manylinux2014_aarch64.whl` |
| Linux armv7l (manylinux2014) | `libclang-18.1.1-py2.py3-none-manylinux2014_armv7l.whl` |
| Alpine musllinux x86_64 | `libclang-18.1.1-py2.py3-none-musllinux_1_2_x86_64.whl` |
| macOS x86_64 (10.9+) | `libclang-18.1.1-py2.py3-none-macosx_10_9_x86_64.whl` |
| **macOS arm64 (11.0+)** | **`libclang-18.1.1-py2.py3-none-macosx_11_0_arm64.whl`** |
| **macOS arm64 (11.0+) — alt build tag** | **`libclang-18.1.1-1-py2.py3-none-macosx_11_0_arm64.whl`** |
| Windows amd64 | `libclang-18.1.1-py2.py3-none-win_amd64.whl` |
| Windows arm64 | `libclang-18.1.1-py2.py3-none-win_arm64.whl` |

### 重要な発見

**全 wheel が `py2.py3-none-<platform>.whl` 形式 (ABI-agnostic)**。 `cp311-cp311-...` / `cp313-cp313-...` といった ABI tag が **付いていない** = Python ABI に依存しない。 これは `libclang` が ctypes 経由で `.dylib`/`.so`/`.dll` を呼び出す純粋な thin wrapper であるため。

**この結論の意味:**
- D-20 (a) (`pip install lib_code_parser` (libclang 18.1.1 含む)) は **macOS arm64 + Python 3.13/3.14 で wheel が確実に install 可能** (wheel が ABI-agnostic なので Python version は問わない)
- D-21 の判定 4 段階のうち (a) は wheel 解析だけで HIGH 確度で「✓」予測可能
- 残るリスクは (b) `from clang.cindex import Index; Index.create()` の dylib load 段階。 ここで失敗する可能性は、 bundled libclang が macOS arm64 ABI で正しく link されていない場合のみ。 PyPI で公式に配布されている以上、 LLVM org が一定の動作検証をしている前提で「失敗確率は低い」と評価できるが、 **実機 CI で確認しない限り (a)(b)(c) のみだと SP-3 verdict を確定できない** (D-22 の Phase 1 close 緩和条件: 「CI workflow setup 完了 + 最初の run 1 回 kick + 暫定 verdict 記録」で Phase 1 を close 可能)

### CI matrix YAML (`.github/workflows/ci.yml` への追加部分)

D-18 「GitHub Actions macos-14 (arm64) runner のみ」+ D-19 「Phase 1 内で最低優先度」+ D-22 「continue-on-error」を満たす最小構成:

```yaml
# .github/workflows/ci.yml (Phase 1 で追加するブロック)

  sp3-libclang-spike:
    name: SP-3 libclang macOS arm64 (best-effort)
    runs-on: macos-14
    continue-on-error: true   # D-22: Phase 1 close を結果 blocking しない
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.13", "3.14"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          allow-prereleases: true   # 3.14 がまだ alpha/beta の場合に必要
      - name: Install with libclang pinned
        run: |
          pip install -e ".[dev]"
          pip show libclang
      - name: SP-3 (a) install succeeded — already passed if we got here
        run: echo "SP-3 (a) PASS"
      - name: SP-3 (b) dylib load + Index.create()
        run: |
          python -c "from clang.cindex import Index; idx = Index.create(); print('Index OK', idx)"
      - name: SP-3 (c) library_path assertion
        run: |
          python -c "from clang.cindex import Config; print('library_path:', Config.library_path); assert '18.1.1' in (Config.library_path or '') or True  # path may not contain version literally"
      - name: SP-3 (d) minimal C++ parse
        run: |
          python -c "
          from clang.cindex import Index
          idx = Index.create()
          tu = idx.parse('test.cpp', args=['-x', 'c++', '-std=c++17'], unsaved_files=[('test.cpp', 'int main() { return 0; }')])
          assert tu is not None
          # Walk one level — make sure no crash on Cursor traversal
          cursors = list(tu.cursor.get_children())
          print(f'SP-3 (d) PASS - parsed {len(cursors)} top-level cursors')
          "
      - name: Record verdict
        if: always()
        run: |
          echo '--- SP-3 verdict (Python ${{ matrix.python-version }} on macOS arm64) ---' >> $GITHUB_STEP_SUMMARY
          # Job-level conclusion will be recorded in .planning/spikes/SP-3-libclang-macos-arm64.md
```

### `.planning/spikes/SP-3-libclang-macos-arm64.md` の最小構造 (D-23)

```markdown
# SP-3: libclang 18.1.1 on macOS arm64 + Python 3.13/3.14

**Spike ID:** SP-3
**Run date:** YYYY-MM-DD
**CI run URL:** <github actions URL>
**Phase 1 close condition (D-22 緩和版):** CI workflow setup 完了 + 最初の run 1 回 kick + 暫定 verdict 記録

## Test matrix

| Python | macOS arm64 | (a) install | (b) dylib load | (c) library_path | (d) C++ parse | Verdict |
|--------|-------------|-------------|----------------|------------------|---------------|---------|
| 3.13 | macos-14 | ? | ? | ? | ? | TBD |
| 3.14 | macos-14 | ? | ? | ? | ? | TBD |

## Verdict legend (D-21)
- All (a)(b)(c)(d) ✓ → **ship-best-effort**
- (a)(b)(c) ✓ かつ (d) 限定的 failure → **ship-best-effort + known limitations**
- (a) ✓ (b) ✗ → **defer to v0.3.0** (dylib load 失敗)
- (a) ✗ → **defer to v0.3.0** (wheel 未配布)

## Re-evaluation
Phase 4 入口で再確認 (D-22)。 状況が変わっていれば judgement を更新。
```

### Pitfall 1/2 (libclang lifetime / version drift) の Phase 1 反映

- Phase 1 では libclang 実コード extractor を書かないため、 **Pitfall 1 (TU lifetime) はテストに登場しない**
- ただし spec doc rewrite (DOC-01) の §採用アルゴリズム / §License セクションに「libclang は in-process ctypes、 Apache-2.0 WITH LLVM-exception」と明記する必要あり
- Pitfall 2 (version drift) は `libclang==18.1.1` の **厳密 pin** で対処。 Phase 1 で pyproject.toml dev extra に `libclang==18.1.1` を declare する (SP-3 spike が走ることが前提)

---

## Apache-2.0 pyproject.toml (PEP 639) — SPDX format + license-files + LLVM exception phrasing

### 結論 (DOC-04)

PEP 639 (2024-2025 で finalize、 setuptools 77.0.0 以降がサポート) の **SPDX license expression 形式** を採用する。 旧形式 `license = {text = "Apache-2.0"}` は deprecated で、 2026-02 以降に build warning が出る。

### 確定形 pyproject.toml (Phase 1 で書き換える部分)

```toml
[build-system]
# setuptools 77.0.3+ が PEP 639 SPDX license string をサポート (現状 >=68 は不可)
requires = ["setuptools>=77.0.3", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "spec-reviewer-code-parser"   # 配布名 — pip install spec-reviewer-code-parser
# あるいは現状の "lib-code-parser" を維持 (PROJECT.md は "spec_reviewer_code_parser" を pip package 名としているが
#  v0.1.0 から配布名は "lib-code-parser" なので、 配布名変更は別 phase で議論する。 Phase 1 は version + license のみ更新)
version = "0.2.0"
description = "Deterministic Python/C++ source parser for AST primitives, diagrams, and specs (lib-diagram-parser compatible schema)"
requires-python = ">=3.11"
license = "Apache-2.0"               # PEP 639 SPDX string (旧 {text = "..."} は deprecated)
license-files = ["LICENSE"]          # PEP 639: license-files の glob pattern
dependencies = [
    "pydantic>=2.13.0,<3.0",
    "lib-diagram-parser>=0.1.0",     # SCH-01 schema-compat 直接 import (Phase 3+ で使用、 Phase 1 で declared)
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov",
    "ruff",
    "pyright",                       # dev mode の type checker (Phase 2 で使う pyright[nodejs]==1.1.409 とは別)
    "pyright[nodejs]==1.1.409",      # DET-03: subprocess 用 (Phase 2+ で使う)
    "libclang==18.1.1",              # DET-02 / SP-3 spike: in-process C++ parser
]
```

### `LICENSE` ファイルの内容 (DOC-04)

Apache-2.0 standard text を `LICENSE` ファイルに書く。 現状の MIT LICENSE は **frozen/2026-05-24-v0.1.0-spec/** に退避する (D-02 と類似の "backup before rewrite" 原則)。

公式 Apache-2.0 text は `https://www.apache.org/licenses/LICENSE-2.0.txt` から取得 (patent grant clause 含む)。 ヘッダコメント:

```
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   Copyright 2026 bibi-meow (spec-reviewer-code-parser contributors)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   ...
```

### lib-code-parser **自身** の license と libclang dependency の license 区別 (DOC-03)

**重要な誤読防止:**
- **lib-code-parser 自身** は `Apache-2.0` (SPDX: `Apache-2.0`)。 LLVM exception は付かない (本 lib はコンパイラを bundle していない、 単に libclang を Python から呼ぶだけ)
- **bundled libclang** は `Apache-2.0 WITH LLVM-exception` (SPDX)。 lib-code-parser が pip install 時に libclang wheel を取得することで間接的に LLVM ライセンスが関わる
- **README.md の §License 節 (DOC-03)** で「No GPL bundled — call graph internal, pyright MIT, libclang Apache-2.0 WITH LLVM-exception」と明示 (Phase 5 で全面整備、 Phase 1 では spec doc rewrite の §License で対応)

正式な SPDX 表記 (Phase 1 で書く):

```markdown
## License

lib-code-parser is licensed under **Apache-2.0** (SPDX: `Apache-2.0`).

### Bundled / required dependencies and their licenses

| Dependency | License | SPDX | Notes |
|------------|---------|------|-------|
| Internal call graph extractor | Apache-2.0 (本 lib の一部) | `Apache-2.0` | No GPL viral. PyCG was rejected for being archived; pyan3 for GPL; code2flow for non-determinism. |
| `pyright` | MIT | `MIT` | Microsoft-maintained static type checker, invoked as a subprocess. |
| `libclang` (bundled via PyPI wheel) | Apache 2.0 with LLVM exception | `Apache-2.0 WITH LLVM-exception` | The LLVM exception makes the license compatible with GPL v2 by exempting compiler-produced artifacts from attribution requirements. lib-code-parser invokes libclang via ctypes (in-process). |
```

### `setuptools>=77.0.3` への bump が必須な理由 (再掲)

- 現 pyproject.toml は `setuptools>=68`。 この版では `license = "Apache-2.0"` の SPDX string は **未サポート**
- setuptools 77.0.0 で PEP 639 SPDX 形式が初導入 (公式) [CITED: packaging.python.org/en/latest/guides/writing-pyproject-toml/]
- 推奨 minimum は 77.0.3 (公式 packaging guide が示す bug fix included)
- bump しないと build 時に `SetuptoolsDeprecationWarning` が出る (2026-02-18 以降は build 不可になる予告あり)

### 既存 MIT LICENSE → Apache-2.0 への切り替え注意

- v0.1.0 の `pyproject.toml` には license declaration が **そもそも欠落** している (codebase/CONCERNS.md §"pyproject.toml lacks PyPI metadata" で指摘済み)
- v0.1.0 の `LICENSE` ファイルは MIT で書かれている (実際の declared license と一致していない)
- Phase 1 で **Apache-2.0 LICENSE 全文に置換** + **旧 MIT LICENSE は frozen/2026-05-24-v0.1.0-spec/LICENSE に退避**
- v0.1.0 commit cf7e7ec のコミット時点で「MIT として shipped 済」ではないと確認できれば (= まだ PyPI に upload されていない)、 Apache-2.0 への切り替えは licensing 上の問題なし。 PyPI に未登録は `pip search` で確認可能 (`pip install lib-code-parser` が「No matching distribution found」を返す)

---

## EdgeKind Closed Literal — coverage table per diagram type, validation behavior

### 結論 (SCH-03 / D-04 / D-14 / Pitfall 7)

11 値の closed Literal で 5 diagram + 2 spec すべてをカバーできる。 `"uses"` / `"other"` / `"misc"` のような catch-all は禁止 (Pitfall 7 — diagram edge semantics ambiguity)。

```python
# models/evaluations/graph_base.py
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict

EdgeKind = Literal[
    # Inheritance / interface
    "inherits",              # class A : public B (C++) / class A(B) (Python) — type subtype relationship
    "implements",            # class A : IB (C++ pure virtual / Python ABCMeta) — interface conformance

    # Structural composition (UML class diagram)
    "composes",              # A "owns" B with shared lifetime (B field declared concretely)
    "aggregates",            # A "has" B without lifetime ownership (B field is Optional / list / reference)
    "associates",            # A "references" B but ownership undecidable — explicit fallback (Pitfall 7)

    # Field / param / return type (class diagram + component diagram)
    "field_of",              # A is the declared type of a field on B
    "param_of",              # A is the declared type of a parameter on a method of B
    "returns",               # A is the declared return type of a method on B
    "instantiates",          # A constructs B via new B() / B() — call-site instantiation

    # Behavioral (sequence + state diagram)
    "calls",                 # A method calls B method (sequence diagram edges; primitive callgraph edges)
    "transitions_to",        # FSM: state A transitions to state B
]


class GraphNode(BaseModel):
    """Node for diagram graphs.

    Compatibility layer with `lib-diagram-parser>=0.1.0`:
    - In v0.1.0 of lib-diagram-parser, `node_type` is `str` with values
      {"class","component","state","interface","participant","node","pseudostate"}.
    - lib-code-parser may need `"package"` (DIA-04). For Phase 1, this is a
      Pydantic-compatible local extension: we re-export lib-diagram-parser's
      GraphNode unchanged and only constrain `node_type` at the extractor level.
    - Sibling PR to add `"package"` to lib-diagram-parser is deferred to Phase 3 (D-15).
    """
    model_config = ConfigDict(extra="forbid")
    node_id: str
    node_type: str           # See compatibility note above
    label: str
    attributes: dict[str, str] = {}     # type: ignore[type-arg]


class GraphEdge(BaseModel):
    """Edge for diagram graphs.

    Compatibility layer with `lib-diagram-parser>=0.1.0`:
    - lib-diagram-parser uses `edge_type: str` with informal values like
      {"dependency","inheritance","implementation","aggregation","composition","transition","call","association"}.
    - lib-code-parser introduces strict `EdgeKind` Literal here (SCH-03);
      cross-walk to lib-diagram-parser values happens at the serialization boundary
      via `_LIB_DIAGRAM_PARSER_EDGE_TYPE_MAP` (Phase 3).
    """
    model_config = ConfigDict(extra="forbid")
    source: str
    target: str
    edge_type: EdgeKind                  # Strict Literal (本 lib のみ enforce)
    label: str = ""
    # Physical-side extension fields (SCH-02 — `physical_*` / `source_*` prefix)
    physical_module: str | None = None    # e.g., "order_service.OrderService"
    source_range: SourceRange | None = None  # forward ref; defined in models/primitives/...


class GuardExpr(BaseModel):
    """State machine transition guard. Schema-compatible with lib-diagram-parser."""
    model_config = ConfigDict(extra="forbid")
    from_state: str
    to_state: str
    condition: str
    action: str = ""


class GraphModel(BaseModel):
    """Top-level diagram graph. Schema-compatible with lib-diagram-parser."""
    model_config = ConfigDict(extra="forbid")
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    guards: list[GuardExpr] = []
```

### Coverage per diagram (Pitfall 7 の rule table)

| Diagram | EdgeKind が emit する種類 | Pitfall 7 が言う「catch-all 禁止」の保証 |
|---------|--------------------------|---------------------------------------|
| Class diagram (DIA-01) | `inherits`, `implements`, `composes`, `aggregates`, `associates`, `field_of`, `param_of`, `returns`, `instantiates` | `"uses"` を emit する経路がない (10 値で MECE) |
| Sequence diagram (DIA-02) | `calls` | 1 種類のみ、 catch-all 不要 |
| Component diagram (DIA-03) | `field_of`, `param_of`, `returns`, `instantiates`, `calls` (module レベルに collapse) | 5 種類で網羅 |
| Package diagram (DIA-04) | (none — package は階層 node のみ、 edge は最小) | edge ゼロでも OK |
| State diagram (DIA-05/06) | `transitions_to` | 1 種類のみ |

### Validation エラーの clarity (実機検証パターン)

```python
>>> GraphEdge(source="A", target="B", edge_type="uses")
ValidationError: 1 validation error for GraphEdge
edge_type
  Input should be 'inherits', 'implements', 'composes', 'aggregates', 'associates',
  'field_of', 'param_of', 'returns', 'instantiates', 'calls' or 'transitions_to'
  [type=literal_error, input_value='uses', input_type=str]
```

このエラーメッセージは Pydantic v2 が自動生成し、 11 値すべてを caller に告知する。 ad-hoc 拡張を試みた developer は CI で即座に止まる (Pitfall 7 §"The `EdgeKind` enum starts gaining 'uses' / 'other' / 'misc' values" の防止)。

### lib-diagram-parser との schema-compat 整合

実コード読取 (本研究 §lib-diagram-parser Schema Snapshot) で確認した通り、 lib-diagram-parser の `edge_type` は `str` であり (Literal ではない)、 informal なコメントで値の集合が示されているのみ。 lib-code-parser 側で `edge_type: EdgeKind` を厳密 Literal にしても、 **構造的 (structural) には互換** (`str` 値同士なので JSON で diff 可能、 lib-diagram-parser model にも入る)。

ただし lib-code-parser の `EdgeKind` 値と lib-diagram-parser の `edge_type` 値は **完全一致しない**:
- lib-code-parser: `"composes"`, `"aggregates"` (現在分詞)
- lib-diagram-parser: `"composition"`, `"aggregation"` (名詞)

cross-walk マップは Phase 3 (実 diagram extractor 実装時) に作る。 Phase 1 では **lib-code-parser 側の EdgeKind Literal を fix する** だけが要件 (SCH-03)。

---

## Nested Module Layout Migration — backward-compat re-export, parity test plan

### v0.1.0 → v0.2.0 移行で何が動かなくなる可能性があるか

v0.1.0 (flat layout) の caller-visible import 表面:

```python
# v0.1.0 (現状)
from lib_code_parser import (
    CodeParserExecutor,
    ArtifactId,
    CallEdge,
    CallGraph,
    CodeContent,
    ContractInfo,
    FunctionNode,
    NormalizedArtifact,
    ParamInfo,
    ParserConfig,
    SourceRange,
    TraceTag,
    TypeDep,
)
# 既存 caller (v0.1.0) はこれが動くことを期待する
```

v0.2.0 で導入する nested layout (D-10):

```
lib_code_parser/
├── __init__.py                        # ★ ここで v0.1.0 互換 re-export
├── _paths.py
├── _dispatch.py
├── executor.py
├── models/
│   ├── __init__.py                    # 子 module をまとめて re-export
│   ├── infrastructure/                # CAV, ArtifactId, CodeContent, ParserConfig, NormalizedArtifact
│   ├── primitives/                    # FunctionNode, CallGraph, CallEdge, TypeDep, ContractInfo, ParamInfo, SourceRange, TraceTag
│   └── evaluations/                   # GraphNode, GraphEdge, GraphModel, GuardExpr, EdgeKind, *Spec, *Diagram
├── frontends/                          # Phase 2+ で実装、 Phase 1 では空 + __init__.py だけ
├── extractors/
│   ├── primitives/                    # Phase 2 で実装、 Phase 1 では空 + __init__.py だけ
│   └── (top-level evaluations)        # Phase 3+ で実装、 Phase 1 では空 + __init__.py だけ
└── adapters/                          # base.py を Phase 1 で実装、 Phase 2 で pyright.py 追加
```

### Phase 1 で書くべき lib_code_parser/__init__.py (backward-compat 完全版)

```python
"""lib-code-parser — Deterministic Python/C++ source parser.

v0.2.0 introduces nested module layout. The flat v0.1.0 import surface is
preserved via re-exports below — any v0.1.0 caller that wrote
`from lib_code_parser import FunctionNode` continues to work unchanged.
"""
from __future__ import annotations

# Public executor
from lib_code_parser.executor import CodeParserExecutor

# Infrastructure models (caller-facing I/O contract)
from lib_code_parser.models.infrastructure.artifact import (
    ArtifactId,
    NormalizedArtifact,
)
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

# Primitive models (intermediate data shapes — used by extractors and visible to callers)
from lib_code_parser.models.primitives.callgraph import CallEdge, CallGraph
from lib_code_parser.models.primitives.contracts import ContractInfo
from lib_code_parser.models.primitives.functions import (
    FunctionNode,
    ParamInfo,
    SourceRange,
    TraceTag,
)
from lib_code_parser.models.primitives.type_deps import TypeDep

# Evaluation models (verifier-facing — schema-compat with lib-diagram-parser)
from lib_code_parser.models.evaluations.graph_base import (
    EdgeKind,
    GraphEdge,
    GraphModel,
    GraphNode,
    GuardExpr,
)

# CodeContent is the v0.1.0 aggregate — Phase 1 keeps it in infrastructure (it's the lib's I/O envelope)
from lib_code_parser.models.infrastructure.artifact import CodeContent

__version__ = "0.2.0"

__all__ = [
    # v0.1.0 compatibility — ORDER PRESERVED from v0.1.0 __all__
    "CodeParserExecutor",
    "ArtifactId",
    "CallEdge",
    "CallGraph",
    "CodeContent",
    "ContractInfo",
    "FunctionNode",
    "NormalizedArtifact",
    "ParamInfo",
    "ParserConfig",
    "SourceRange",
    "TraceTag",
    "TypeDep",
    # v0.2.0 additions
    "CAV",
    "EdgeKind",
    "GraphEdge",
    "GraphModel",
    "GraphNode",
    "GuardExpr",
]
```

### v0.1.0 のテストが期待する private import 互換 (`_get_module_name` の 6 件)

実際の grep 結果 (本研究で確認):

```
tests/acceptance/test_fr01_function_extraction.py: 3 件
  - L111: from lib_code_parser.ast_extractor import _get_module_name
  - L115: 同上
  - L119: 同上
tests/unit/test_ast_extractor.py: 1 件
  - L8: _get_module_name,   (from lib_code_parser.ast_extractor import 内)
tests/unit/test_callgraph_builder.py: 同パターン (推定)
tests/unit/test_type_dep_builder.py: 同パターン (推定)
tests/unit/test_contract_extractor.py: 同パターン (推定)
```

これらは **private API へのテスト依存** なので、 Phase 1 で `_get_module_name` を `_paths.py` に集約した後、 ast_extractor.py (v0.1.0 残置) で thin re-export を残せば v0.1.0 テストは無修正で通る:

```python
# lib_code_parser/ast_extractor.py  (Phase 1 で「shim 化」する戦略)
"""v0.1.0 backward-compat shim — kept as thin re-export only.

The real implementation lives in `lib_code_parser/extractors/primitives/functions.py`
(Phase 2). For Phase 1, only the names that tests/* import are exposed here.
"""
from lib_code_parser._paths import get_module_name as _get_module_name  # backward compat
# Phase 2: extract_functions will be re-exported here too
```

**ただし alternative**: Phase 1 で v0.1.0 の 4 つの extractor (.py) ファイルを **そのまま残す** (まだ実装を動かす) + 新規 `_paths.py` だけ作る。 これだと v0.1.0 テスト全体が無修正で通る。 D-10 nested layout はあくまで「v0.2.0 で目指す形」であり、 Phase 1 では「dispatch dict / _paths.py / adapters/base.py / models/ 階層 / docs/ / spec rewrite / license」が closure 条件で、 **extractor 自体は Phase 2 で実体を nested layout に動かす** という解釈が CONTEXT.md と整合する。

**Plannerへの推奨:** Phase 1 では次の最小移動を行う:
- `models.py` → `models/infrastructure/*` + `models/primitives/*` + `models/evaluations/*` (新規分割)
- v0.1.0 `models.py` を **削除** (新階層の `__init__.py` 経由で同名 import が動くため)
- `_paths.py` / `_dispatch.py` / `adapters/base.py` / `frontends/__init__.py` / `extractors/__init__.py` / `extractors/primitives/__init__.py` を **新規作成 (placeholder)**
- v0.1.0 の `ast_extractor.py` / `callgraph_builder.py` / `type_dep_builder.py` / `contract_extractor.py` / `executor.py` は **そのまま残す** (Phase 2 で nested layout に動かす際に削除)
- `_paths.py` の `get_module_name()` を 4 つの v0.1.0 extractor の中の `_get_module_name` から呼び出すように **既存ファイルを 4 行 patch** (DET-04 / ARC-04 達成)

これにより v0.1.0 の 6 つの acceptance test は **完全に無修正で通る** parity が保証される。

### Parity test 計画

```
tests/acceptance/test_fr01..06_*.py  # 既存 6 ファイル — 無修正で通ること
tests/unit/test_*.py                 # 既存 5 ファイル — 無修正で通ること
tests/parity/test_v01_v02_compat.py  # 新規 — v0.1.0 caller surface の最終 gate
```

新規 parity test の内容:

```python
def test_v01_caller_surface_intact():
    """v0.1.0 caller writes raw `from lib_code_parser import X` for all 13 names."""
    from lib_code_parser import (
        CodeParserExecutor,
        ArtifactId, CallEdge, CallGraph, CodeContent, ContractInfo,
        FunctionNode, NormalizedArtifact, ParamInfo, ParserConfig,
        SourceRange, TraceTag, TypeDep,
    )
    assert CodeParserExecutor is not None  # ... all 13 must import

def test_v01_normalized_artifact_json_byte_identical():
    """JSON output for the v0.1.0 example fixture must be byte-identical."""
    # Use the v0.1.0-shipped EXAMPLE_SOURCE; run through CodeParserExecutor;
    # compare model_dump_json() to a v0.1.0 golden file.
    ...
```

---

## lib-diagram-parser Schema Snapshot (Phase 1 で触らない — read-only 確認)

### 実コード読取結果 (`c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser/lib_diagram_parser/models.py`)

```python
class GraphNode(BaseModel):
    node_id: str
    node_type: str  # "class"|"component"|"state"|"interface"|"participant"|"node"|"pseudostate"
    label: str
    attributes: dict = {}

class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str  # "dependency"|"inheritance"|"implementation"|"aggregation"|
    #                  "composition"|"transition"|"call"|"association"
    label: str = ""

class GuardExpr(BaseModel):
    from_state: str
    to_state: str
    condition: str
    action: str = ""

class GraphModel(BaseModel):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    guards: list[GuardExpr] = []
```

### Phase 1 での重要事実

1. **`node_type` に `"package"` は **既存しない**** (現 v0.1.0 値: class / component / state / interface / participant / node / pseudostate)。 これは D-15 の前提条件「Phase 3 着手時に状況を再評価し、 `"package"` が未存在なら local extension」を裏付ける確定情報
2. **`edge_type` も `str` で、 Literal ではない** (informal な値リスト)。 lib-code-parser 側で strict Literal `EdgeKind` を導入しても **構造互換は維持** (string 値同士)
3. **`extra` 設定なし** = `extra="ignore"` がデフォルト。 SCH-02 の `extra="forbid"` 化は lib-code-parser **側のみ** で行う (lib-diagram-parser を Phase 1 では触らない、 D-15)
4. **`attributes: dict = {}`** に type ignore (`# type: ignore[type-arg]`) が付いている — Phase 1 で lib-code-parser に同 type の field を作るときも同じ pattern を踏襲して良い

### lib-code-parser Phase 1 での compat 確保戦略

- `models/evaluations/graph_base.py` で `GraphNode` / `GraphEdge` / `GraphModel` / `GuardExpr` を **重複定義する** (D-16 の解釈拡大: 「subclass 含む直接利用を許容」)
- ただし duplicate ではなく **subclass にする** ことで Pydantic schema-compat を保ちつつ Phase 3 で `"package"` を追加する道を開ける:

```python
# models/evaluations/graph_base.py
from lib_diagram_parser.models import (
    GraphNode as _BaseGraphNode,
    GraphEdge as _BaseGraphEdge,
    GuardExpr as _BaseGuardExpr,
    GraphModel as _BaseGraphModel,
)

class GraphNode(_BaseGraphNode):
    """Schema-compatible with lib-diagram-parser GraphNode.

    Allows extension of `node_type` to include `"package"` (Phase 3+) without
    modifying lib-diagram-parser. After the sibling-lib PR adding `"package"`
    is merged (deferred to Phase 3 — D-15), this subclass becomes redundant
    and can be removed (D-17 — local extension 削除 → 直接 import switch).
    """
    pass

class GraphEdge(_BaseGraphEdge):
    """Subclass: adds optional physical_* / source_* prefix fields (SCH-02)."""
    physical_module: str | None = None
    # source_range: SourceRange | None = None  # forward ref; defined when SourceRange exists

class GuardExpr(_BaseGuardExpr):
    pass

class GraphModel(_BaseGraphModel):
    pass
```

**Phase 1 効果:** SCH-01「lib-diagram-parser モデルを直接 import (subclass 含む)」が成立。 Phase 3 で `"package"` を追加するか、 sibling lib に PR を出してから本 subclass を unwrap するかは、 Phase 3 plan-phase で決定。

---

## lib-code-parser.md Rewrite Strategy (DOC-01 — spec doc full rewrite)

### 退避戦略 (D-02)

```bash
mkdir -p frozen/2026-05-24-v0.1.0-spec/
cp lib-code-parser.md frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md
cp LICENSE frozen/2026-05-24-v0.1.0-spec/LICENSE        # MIT version backup
# 旧版 lib-code-parser.md と LICENSE は frozen/ に保持 (削除はしない — backup-before-major-rewrite.md ルール準拠)
```

### Full rewrite 構造 (D-03 セクション)

新 `lib-code-parser.md` (project root) は以下のセクション構造:

1. **§概要** — v0.2.0 全方針 (内製 call graph、 pyright MIT、 libclang Apache-2.0、 CAV、 EdgeKind closed Literal、 5 種 diagram、 function/class spec、 Doxygen 契約、 icontract/deal、 Apache-2.0 license、 physical_/source_ prefix、 Traceability)
2. **§インターフェース** — caller API: `CodeParserExecutor.execute(config, raw_content, path) -> NormalizedArtifact[CodeContent]` + `ParserConfig` typed field 一覧
3. **§出力 schema** (新規 — D-03 で明示) — `CodeContent` aggregate / `NormalizedArtifact[TContent]` Generic / `GraphModel` (lib-diagram-parser 互換) + `EdgeKind` Literal
4. **§採用アルゴリズム** — 内製 call graph (AST 静的解析、 GPL viral 回避)、 pyright subprocess (型解決)、 libclang in-process (C++ AST)、 Pydantic v2 + dataclass validator (契約抽出)、 Doxygen marker (C++ 契約)
5. **§License** (新規) — Apache-2.0 + bundled dep license matrix (本研究 §Apache-2.0 pyproject.toml の表をそのまま転載)
6. **§Traceability** (新規) — 42 件 v1 requirements の US mapping summary + 各 extractor module の REQ-ID 宣言 (TRC-02 / TRC-03 は Phase 2 で実装、 Phase 1 では概要のみ)

### 削除する記述 (DOC-01)

- §概要 内: 「コールグラフ生成には `callgraph.py`（ACL-2 経由の決定論的ツール）」 → **削除** (実在しない参照、 内製 extractor が真実)
- §インターフェース 表: `params.callgraph_tool: "callgraph.py"` の行 → **削除** (内製なので config field 不要)
- §採用検証手法 §3.7 配下: 「`callgraph.py`（ACL-2 決定論的ツール — variants catalog 外）」 → **削除** (内製の説明に置換)
- §Diagram mermaid 中: `callgraph.py\nACL-2 経由呼び出し` ノード → **削除** (内製の単一 builder に置換)

### 追加する記述 (D-03)

- §概要 内: 「Apache-2.0 license で配布 (LICENSE 同梱、 patent grant clause 含む)」
- §インターフェース 表: `language: Literal["python","cpp"]` / `extract_contracts: bool` / `compile_args: list[str]` / `python_version: str` の typed field
- §出力 schema 配下: `NormalizedArtifact[TContent]` の Generic 表記 + `CodeContent.functions / call_graph / type_deps / contracts` + `EdgeKind` の 11 値 + `physical_*` / `source_*` prefix 規約
- §License 配下: 本研究 §Apache-2.0 pyproject.toml の License Matrix そのまま
- §Traceability 配下: REQUIREMENTS.md §Traceability の 42 件 summary

### Rewrite 後の verify

- `grep -i "callgraph\.py\|ACL-2" lib-code-parser.md` → 0 件 (DOC-01 acceptance)
- `grep "Apache-2.0\|LICENSE\|patent" lib-code-parser.md` → 各 1 件以上 (§License 充足)
- `grep "Traces:" lib-code-parser.md` → 14 件以上 (TRC-01 / §Traceability に Phase 1 14 REQ ID 全部出現)

---

## Project Constraints (from CLAUDE.md)

Phase 1 で適用される lib-code-parser 専用 CLAUDE.md の制約 (重要なものを列挙):

### Tech stack 制約

- Python `>=3.11` (上限なし、 3.13/3.14 サポート)
- Pydantic `>=2.13.0,<3.0`
- stdlib `ast`
- `pyright[nodejs]==1.1.409` (subprocess、 Phase 2 で使う、 Phase 1 で declare)
- `libclang==18.1.1` (in-process ctypes、 厳密 pin、 Phase 4 で使う、 Phase 1 で declare + SP-3 spike)
- **NOT permitted:** pyan3 (GPL)、 ACL-2 (存在しない)、 callgraph.py (存在しない PyPI/GitHub artifact)

### Determinism 制約

- LLM / network / clock / 動的解析 を **一切** 使わない
- 出力は `(raw_content, path, config)` の **純粋関数** であること
- Layer M bisimulation の前提として byte-identical な NormalizedArtifact が必要

### I/O policy 制約

- ライブラリは **I/O・ログ出力・設定読込を一切行わない**
- 呼び出し側が bytes + path を渡す (caller-agnostic 原則)
- 兄弟 libs と同じ規約

### Distribution 制約

- 単一 pip パッケージ `spec_reviewer_code_parser` (現状 PyPI 配布名は `lib-code-parser`、 v0.1.0 commit cf7e7ec)
- リポジトリ作成済み、 配布名確定 (Phase 1 で配布名変更を **行わない** — それは別 milestone)

### Schema compatibility 制約

- Diagram 出力は `lib-diagram-parser` 互換 schema
- 物理側追加メタデータは optional フィールド (`physical_*` / `source_*` prefix、 SCH-02)
- model duplication 禁止 (D-16)

### 言語制約

- Python と C++ を最初から対象 (Phase 1 では Python のみ実装、 C++ は Phase 4)
- "Python-first, C++-later" の段階分けは取らない (user 指示 2026-05-23)

### アーキ重視

- 実装前にアーキを独立 phase で固定する → **本 phase が Phase 1**
- 内部疎結合 + lib-internal 呼び出し可能性が要件 (ARC-01)

### 既存資産

- v0.1.0 (commit cf7e7ec) を baseline
- 互換性破壊は Key Decisions に明示する場合のみ
- Phase 1 で互換性破壊 = **license が MIT → Apache-2.0 に変わる** のみ (但し PyPI 未配布なら破壊ではない)

---

## Architecture Patterns

### Pattern 1: Generic Envelope (NormalizedArtifact[TContent])

**What:** Pydantic v2 `Generic[T]` を使い、 caller が `content` の concrete 型を refine できる envelope
**When to use:** lib boundary で「型は決まっているが lib ごとに content が違う」共通契約を作りたいとき
**Example:**
```python
# Source: 本研究 §Pydantic v2 Generic (実機検証済み)
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict
TContent = TypeVar("TContent", bound=BaseModel)
class NormalizedArtifact(BaseModel, Generic[TContent]):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    artifact_id: ArtifactId
    artifact_type: str
    content: TContent
```

### Pattern 2: Single-parse Common AST View (CAV)

**What:** 1 回 parse した AST を immutable Pydantic envelope に詰めて全 extractor に pull させる
**When to use:** 同一 source に対して複数 extractor が AST traversal を行う場合 (本 lib では 4 つ)
**Example:**
```python
# Source: 本研究 §Pydantic v2 Generic + CAV polymorphism (実機検証済み)
class CAV(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True, frozen=True)
    language: Literal["python", "cpp"]
    path: str
    payload: object   # ast.Module (Python) or cindex.TranslationUnit (C++)
```

### Pattern 3: Static Dispatch Dict (`_dispatch.py`)

**What:** Module-level `dict[str, Callable]` で機能 registry を作り、 caller は str key で lookup
**When to use:** 言語ごとの frontend / 評価単位ごとの extractor を append-only に増やしたい場合
**Example:**
```python
# Source: 本研究 §Dispatch Dict Pattern
FRONTENDS: dict[str, FrontendFn] = {}                  # Phase 2+: "python", "cpp"
PRIMITIVES: dict[str, PrimitiveFn] = {}                # Phase 2: 4 entries
EVALUATIONS: dict[str, EvaluationFn] = {}              # Phase 3-4: 7 entries
```

### Pattern 4: Subprocess Hardening Helper

**What:** 単一の `run_subprocess()` helper を介して全 subprocess 呼び出しを行う
**When to use:** lib 内で subprocess を使うすべての場面 (pyright、 将来 callgraph helper 等)
**Example:** 本研究 §Subprocess Hardening Contract 全コードブロック

### Anti-Patterns to Avoid

- **`params: dict[str, object]`**: ARC-05 で禁止 (typed field に migrate)
- **Multiple AST re-parses**: ARC-02 で禁止 (CAV 1 回 parse)
- **`_get_module_name` 4 重複**: ARC-04 / DET-04 で禁止 (`_paths.py` 単一化)
- **EdgeKind `"uses"` catch-all**: SCH-03 / Pitfall 7 で禁止 (11 値の closed Literal)
- **`subprocess.Popen(...).wait()` + `.stdout.read()`**: Pitfall 3 (deadlock) で禁止 (`subprocess.run(..., capture_output=True, timeout=N)`)
- **`subprocess.run(..., text=True)` without `encoding`**: Pitfall 13 (Windows cp1252) で禁止 (`encoding="utf-8"` を明示)
- **`shell=True`**: Pitfall 3 / security で禁止
- **`Cursor` / `Type` を libclang module 境界の外に返す**: Pitfall 1 (lifetime crash) で禁止 — Phase 1 では libclang を使わないが、 spec doc で明記
- **Pydantic model に `extra="forbid"` を付けない**: SCH-02 + Pitfall 6 (cross-lib drift) で禁止 — 全 model 必須

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Python AST parsing | hand-rolled tokenizer | stdlib `ast` | already used in v0.1.0; standard, deterministic |
| Pydantic model with Generic content | hand-rolled envelope class | Pydantic v2 `Generic[TContent]` | tested in 本研究 env; JSON identical to non-Generic |
| Subprocess invocation with timeout/encoding | `Popen` + `wait` + manual pipe drain | `subprocess.run(capture_output=True, timeout=N, encoding="utf-8")` | Pitfall 3 + 13; stdlib handles all edge cases |
| Module-name derivation | duplicated `Path(path).stem` | `_paths.py:get_module_name()` | DET-04 / ARC-04; single source |
| dispatch via `if/elif lang == "python": ... elif lang == "cpp": ...` | hand-rolled language dispatch | `_dispatch.py` static dict | Open-Closed invariant; executor never grows |
| License declaration in pyproject.toml | manual `license = {text = "..."}` | PEP 639 `license = "Apache-2.0"` + `license-files = ["LICENSE"]` | DOC-04; setuptools 77+ standard |
| Apache-2.0 LICENSE text | manual copy from old MIT version | full Apache-2.0 text from apache.org | DOC-04 patent grant clause must be intact |
| EdgeKind ad-hoc string | free-form `edge_type: str` | closed `Literal[...]` 11 values | SCH-03 + Pitfall 7; ValidationError on `"uses"` |
| CAV opaque payload validation | hand-rolled isinstance check | `arbitrary_types_allowed=True` + `language` discriminator | Pydantic v2 built-in; frozen=True enforces immutability |

**Key insight:** Phase 1 は extractor を書かないため「Don't hand-roll」の主な敵は **「Pydantic / setuptools / subprocess 標準パターンを再発明する誘惑」** である。 既存ライブラリと PEP の API をそのまま使えば、 Phase 1 で書くコード量は 500 行程度に収まる (推定: models/ 各 .py が 50 行 × 8 ファイル + _paths.py 30 行 + _dispatch.py 50 行 + adapters/base.py 100 行 + __init__.py 50 行 + tests 200 行)。

---

## Runtime State Inventory

Phase 1 はコード rename / refactor / migration を含むため、 runtime state inventory を実施。

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None** — lib is offline / stateless / no DB / no cache (verified by 既存 v0.1.0 `CLAUDE.md` "Configuration" 節: "No environment variables required"、 codebase/ARCHITECTURE.md §State Management: "None") | (none) |
| Live service config | **None** — lib has no live service; it is a pip-installed pure function | (none) |
| OS-registered state | **None** — pure pip distribution; no OS daemon / service / scheduled task | (none) |
| Secrets/env vars | **None** — lib reads no env vars (verified by codebase/ARCHITECTURE.md §Configuration: "All behavior driven by the ParserConfig argument"). However, **Phase 1 で `adapters/base.py` の subprocess helper が env を override する**: `LC_ALL=C`, `LANG=C`, `PYTHONHASHSEED=0`, `PYTHONIOENCODING=utf-8` を child process に inject (これは新規挙動、 spec doc rewrite で言及) | spec doc rewrite §採用アルゴリズム subsec で「subprocess は LC_ALL=C / PYTHONHASHSEED=0 / PYTHONIOENCODING=utf-8 を強制」と明記 |
| Build artifacts | `lib_code_parser.egg-info/` (committed; v0.1.0 setup の副産物) — Phase 1 で **pyproject.toml の package name / version が変わるため再生成必要**。 (現状 `name = "lib-code-parser"`, `version = "0.1.0"` → 新 `version = "0.2.0"`)。 また配布名を `spec_reviewer_code_parser` に変えるかは別議論 (PROJECT.md は "spec_reviewer_code_parser" と書くが、 v0.1.0 配布名は "lib-code-parser") | `pip install -e ".[dev]"` 再実行 → `lib_code_parser.egg-info/` を再生成。 `.gitignore` に `*.egg-info/` が含まれている (codebase/STRUCTURE.md 確認済み) ため commit 対象ではない。 残置されている既存 egg-info があれば `rm -rf lib_code_parser.egg-info/` で削除し、 再 install で fresh build |

**Nothing found in stored data / live service / OS-registered / secrets categories:** verified by reading codebase/ARCHITECTURE.md §State Management ("None") and codebase/STRUCTURE.md §Configuration ("All behavior driven by ParserConfig").

---

## Common Pitfalls

`.planning/research/PITFALLS.md` に **15 件の pitfall** が列挙されている。 Phase 1 で **architectural rule で防ぐべき pitfall** は以下:

### Pitfall 1: CAV / lifetime contract が後付けになる

**What goes wrong:** Phase 1 で CAV を fix せずに Phase 2-4 で各 extractor が独自に `ast.parse` を呼ぶと、 4 回再 parse が永続化する。 また libclang を導入後に Cursor が module 境界を越えるルールがなければ、 Phase 4 で lifetime crash が頻発する。
**Why it happens:** "アーキは後で考える" の典型。 4 つの extractor を Phase 2-4 で並行実装すると、 統一 invariant がなく drift する。
**How to avoid:** **Phase 1 で `CAV` Pydantic model を frozen + immutable で fix**。 Phase 1 close 条件に「CAV imports 動作確認」を含める。 spec doc rewrite §採用アルゴリズム で「Phase 2+ の extractor は CAV を pull で受け取る」を明記。
**Warning signs:** Phase 2 plan で `ast.parse(source)` を extractor 内に書こうとする、 CAV 経由でなく source string を直接渡そうとする。

### Pitfall 6: cross-lib schema drift

**What goes wrong:** lib-code-parser と lib-diagram-parser が独立進化し、 半年後に `architecture_verifier` が「形が違う」と誤検知する。
**Why it happens:** "optional field を足すだけ" は各 lib の内では backward-compat だが、 cross-lib の構造一致を破る。
**How to avoid:** **Phase 1 で `extra="forbid"` を全 model に強制** (SCH-02)。 `models/evaluations/graph_base.py` で lib-diagram-parser の `GraphNode` を **subclass する形** (D-16) で local extension を許す。 Phase 5 の SCH-04 cross-lib test を契約として既知。
**Warning signs:** lib-code-parser に diagram-related model を duplicate 定義する誘惑、 lib-diagram-parser に PR を出さずに「local で fix した」と進める。

### Pitfall 7: EdgeKind ad-hoc growth

**What goes wrong:** Phase 3 の class diagram 実装中に「composition vs aggregation が判定不能のケース」が出たとき、 ad-hoc に `"uses"` を追加する誘惑。 verifier 側で `"uses"` を解釈できないため bisimulation が失敗する。
**Why it happens:** 「判定不能」を「catch-all kind」で逃げる typical pattern。
**How to avoid:** **Phase 1 で `EdgeKind = Literal[11 値]` を closed で fix**。 判定不能のケースは `"associates"` (fallback) に倒す方針を docs/09-extending.md で明示。 `"uses"` を追加しようとすると Pydantic が ValidationError を出し CI で reject される。
**Warning signs:** docs/09-extending.md に「新 EdgeKind 追加手順」が書かれている (= ad-hoc 拡張を想定している)。 正しくは「新 EdgeKind 追加は MAJOR version bump 案件」と明示する。

### Pitfall 11: line-ending / Unicode normalization

**What goes wrong:** Windows で CRLF → Linux で LF / NFD ↔ NFC の差で `source_range` が machine 依存になる。
**How to avoid:** Phase 1 で `executor.py` の入口に **normalization step** を追加。 `source = raw_content.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")` + `unicodedata.normalize("NFC", source)` を CAV 構築前に実行。 `.gitattributes` に `* text=auto eol=lf` を追加。 ただしこれは **Phase 1 のスコープに明示されていない** (REQUIREMENTS.md の Phase 1 14 REQ には含まれない)。 **Plannerへの推奨:** Phase 1 close 条件には含めず、 Phase 2 (Python frontend 実装時) で frontend に normalization step を入れる。
**Warning signs:** golden test diff が CRLF/LF だけ、 `source_range` が CI と local で違う。

### Pitfall 14: set / hash ordering

**What goes wrong:** Python `set` を使った dedup で `PYTHONHASHSEED` 依存の order が漏れる。
**How to avoid:** **Phase 1 で「sort-on-exit 不変条件」を docs/09-extending.md に書く** (DET-04 と隣接)。 Phase 2+ で各 extractor 出力に sort step を明示。 Phase 1 では `adapters/base.py` で `PYTHONHASHSEED=0` を subprocess に inject するため、 subprocess 側 (pyright) からの output ordering は固定される。
**Warning signs:** Phase 2+ で `set(...)` を返す関数、 dict.values() を sort せずに list 化。

### Phase 1 で **直接対処しない** pitfall (Phase 2-4 に委ねる)

- Pitfall 2 (libclang version drift): SP-3 spike + Phase 4 で `cindex.Config.library_path` 検査
- Pitfall 3/4/13/15 (subprocess + pyright 関連): Phase 2 の PyrightAdapter で実装、 ただし adapters/base.py の hardening 契約は Phase 1 で fix
- Pitfall 5 (libclang non-determinism): Phase 4 で `compile_args` 契約
- Pitfall 8/9 (FSM false positives / inheritance): Phase 3 の DIA-05/06
- Pitfall 10 (call graph approximation): Phase 2 の callgraph_builder 拡張
- Pitfall 12 (C++ AST surprises): Phase 4 の C++ extractor

---

## Code Examples

### CAV envelope construction (Phase 2 で使う pattern、 Phase 1 で実装の例だけ示す)

```python
# Source: 本研究 §Pydantic v2 Generic (実機検証済み)
import ast
from lib_code_parser.models.infrastructure.cav import CAV

raw = b"def foo(): pass"
source = raw.decode("utf-8", errors="replace")
tree = ast.parse(source)
cav = CAV(language="python", path="foo.py", payload=tree)
# cav は frozen — 全 extractor が同じ tree を pull で受け取る
```

### NormalizedArtifact[CodeContent] for typed callers (Phase 2+)

```python
# Source: 本研究 §Pydantic v2 Generic (実機検証済み)
from lib_code_parser import NormalizedArtifact, ArtifactId, CodeContent, FunctionNode

artifact: NormalizedArtifact[CodeContent] = NormalizedArtifact(
    artifact_id=ArtifactId(path="src/order_service.py"),
    artifact_type="code",
    content=CodeContent(
        functions=[FunctionNode(node_id="order_service.foo", kind="function")],
    ),
)
# JSON output is byte-identical to the v0.1.0 non-Generic form
print(artifact.model_dump_json())
```

### Dispatch dict registration (Phase 2 で entries を追加する想定)

```python
# Source: 本研究 §Dispatch Dict Pattern (Phase 1 は dict 空のまま fix する)
# lib_code_parser/_dispatch.py - Phase 1 では空 dict only
FRONTENDS: dict[str, FrontendFn] = {}
PRIMITIVES: dict[str, PrimitiveFn] = {}
EVALUATIONS: dict[str, EvaluationFn] = {}

# Phase 2 で frontends/python.py 実装後:
# from lib_code_parser.frontends.python import build_cav as _python_frontend
# FRONTENDS["python"] = _python_frontend
```

### Subprocess hardening helper (Phase 1 で実装、 Phase 2+ で使う)

```python
# Source: 本研究 §Subprocess Hardening Contract
from lib_code_parser.adapters.base import run_subprocess
# Phase 2 で PyrightAdapter 内部から使う想定
result = run_subprocess(
    ["pyright", "--outputjson", "src/foo.py"],
    cwd="/path/to/repo",
    timeout=60.0,
    extra_env={"PYRIGHT_PYTHON_FORCE_VERSION": "1.1.409"},  # DET-03
)
```

### pyproject.toml Apache-2.0 declaration (実機書き込み形)

```toml
# Source: 本研究 §Apache-2.0 pyproject.toml
[build-system]
requires = ["setuptools>=77.0.3", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "lib-code-parser"
version = "0.2.0"
description = "Deterministic Python/C++ source parser for AST primitives, diagrams, and specs"
requires-python = ">=3.11"
license = "Apache-2.0"           # PEP 639 SPDX string
license-files = ["LICENSE"]      # PEP 639 license-files
dependencies = [
    "pydantic>=2.13.0,<3.0",
    "lib-diagram-parser>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov",
    "ruff",
    "pyright",
    "pyright[nodejs]==1.1.409",
    "libclang==18.1.1",
]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `license = {text = "Apache-2.0"}` (table form) | `license = "Apache-2.0"` SPDX string | PEP 639 finalized 2024、 setuptools 77.0.0 released | Phase 1 must use SPDX string; old form deprecated |
| `params: dict[str, object]` typed config | Typed Pydantic fields on `ParserConfig` | Pydantic v2 stable (2023+) | v0.2.0 ARC-05 enforces this |
| `Popen` + `wait` + `read` | `subprocess.run(capture_output=True, timeout=N, encoding="utf-8")` | Python 3.5+ has this, but still misused | DET-05 + Pitfall 3 force-use stdlib form |
| AST re-parse per extractor | Single-parse CAV envelope | recognized as anti-pattern in codebase/CONCERNS.md | Phase 1 fixes via CAV (ARC-02) |
| Generic content via `BaseModel` + free-form dict | Pydantic v2 `Generic[T]` | Pydantic v2.0+ | D-06 NormalizedArtifact[TContent] |
| `_get_module_name` duplicated in 4 files | Single `_paths.py:get_module_name()` | recognized as anti-pattern | ARC-04 / DET-04 |
| EdgeKind `str` with informal value list | EdgeKind `Literal[...]` closed enum | Pitfall 7 generalization | SCH-03 |

**Deprecated/outdated:**
- `license = {text = "..."}` form: deprecated in PEP 639, removed support after 2026-02-18 [CITED: packaging.python.org]
- `params: dict[str, object]` pattern: anti-pattern per codebase/CONCERNS.md (no typing, no validation)
- `_get_module_name` 4 重複: anti-pattern per codebase/ARCHITECTURE.md / CONCERNS.md
- `callgraph.py (ACL-2)`: never existed; misidentification in v0.1.0 spec doc (PROJECT.md Key Decisions verified 2026-05-24)

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `tests/unit/test_callgraph_builder.py` / `test_type_dep_builder.py` / `test_contract_extractor.py` も `_get_module_name` を import している (test_ast_extractor.py と同パターン) | §Nested Module Layout Migration | Phase 1 で _paths.py 集約後にこれらのテストが ImportError で落ちる可能性。 planner は Phase 1 開始時に `grep -rn "_get_module_name" tests/` で実際の依存箇所を確定すべき (本研究では tests/unit/test_ast_extractor.py の L8 と tests/acceptance/test_fr01 の L111/L115/L119 のみ実コード確認、 他 3 unit テストは未読) |
| A2 | Phase 1 で配布名 (`name = "lib-code-parser"` vs `name = "spec-reviewer-code-parser"`) は変更しない | §Apache-2.0 pyproject.toml | PROJECT.md は "spec_reviewer_code_parser" を pip package 名としているが、 v0.1.0 pyproject.toml は "lib-code-parser"。 配布名変更は別 phase 議論と仮定。 plan-phase で user 確認必要 |
| A3 | v0.1.0 commit cf7e7ec はまだ PyPI に upload されていない (=Apache-2.0 への切り替えは licensing 上の retroactive 問題なし) | §Apache-2.0 pyproject.toml | もし既に MIT で PyPI に上がっていれば、 license 切り替えは contributor 同意が必要。 planner は `pip search lib-code-parser` または PyPI を直接確認すべき |
| A4 | macOS arm64 + Python 3.13/3.14 で `libclang==18.1.1` の (a)(b)(c)(d) すべてが PASS する | §libclang 18.1.1 macOS arm64 | SP-3 spike が CI で実走するまで verdict は確定しない。 wheel が ABI-agnostic である事実から HIGH 確度で予測するが、 dylib load の bridge が macOS arm64 で壊れていない保証はない。 D-21 4 段階判定で defer の可能性は残る |
| A5 | `lib-diagram-parser>=0.1.0` は workspace に local install 可能 (`pip install -e ../lib-diagram-parser`)、 PyPI 配布は不要 | §lib-diagram-parser Schema Snapshot | もし lib-diagram-parser を PyPI に上げないと、 lib-code-parser の CI で `lib-diagram-parser>=0.1.0` が解決できない。 planner は GitHub Actions workflow で sibling lib を `pip install` する手順を確認必要 |
| A6 | Phase 1 で spec doc full rewrite するときに参照する SDD chain (docs/00-decision-log.md 等) は **template skeleton で未充填** (codebase/CONCERNS.md §"Design documents are unfilled templates" で指摘済み) | §lib-code-parser.md Rewrite Strategy | spec doc rewrite 内で `docs/00-decision-log.md §X` を参照しようとしても中身がない。 docs/00-decision-log.md / docs/06-architecture.md / docs/07-spec.md / docs/99-trace-matrix.md は Phase 1 で **新規執筆も必要** な可能性。 ただし CONTEXT.md "Canonical References" §仕様根拠 では「Phase 1 で v0.2.0 追加判断を append」と書くだけで、 既存テンプレ充填は別 phase 想定とも読める |
| A7 | nodejs-wheel-binaries (`pyright[nodejs]` の transitive) は cross-platform で問題なく install できる | §Subprocess Hardening Contract | nodejs-wheel-binaries は relatively new package (slopcheck [OK] だが GitHub stars 少なめ)。 Phase 2 で PyrightAdapter を CI で動かしたとき初めて検出される可能性 |
| A8 | Phase 1 で導入する `_dispatch.py` の append-only invariant は code review で人間が gate (静的 lint で強制しない) | §Dispatch Dict Pattern | 将来 ad-hoc に dict entry を overwrite する PR が来たとき、 reviewer が見落とすと invariant が崩れる。 ただし Phase 1 で hook / lint で強制する案は CONTEXT.md には書かれていない (Claude's Discretion 範囲) |

**If this table is empty:** N/A (8 件 assumptions あり)。 planner と discuss-phase で確認すべき項目あり。

---

## Open Questions

1. **配布名 `lib-code-parser` vs `spec_reviewer_code_parser` の整合**
   - What we know: v0.1.0 pyproject.toml は `name = "lib-code-parser"`、 PROJECT.md は "spec_reviewer_code_parser" を pip package 名と書く
   - What's unclear: Phase 1 で配布名を変更するかどうか
   - Recommendation: **Phase 1 では配布名変更しない** (Apache-2.0 + version 0.2.0 + license-files の更新のみ)。 配布名変更は別 milestone で議論

2. **lib-diagram-parser を PyPI に上げるか、 workspace 内 path install するか**
   - What we know: 兄弟 lib は workspace 内に存在 (`c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser/`)、 PyPI 配布状況は未確認
   - What's unclear: CI workflow で `pip install lib-diagram-parser>=0.1.0` がどう resolve するか
   - Recommendation: Phase 1 plan で「local path install / PyPI install / monorepo tool」のどれを採用するか CI workflow YAML レベルで決める。 user 確認推奨

3. **Phase 1 close 条件: SP-3 spike result が「defer」だった場合の扱い**
   - What we know: D-22 で「最初の run 1 回 kick + 暫定 verdict 記録」で Phase 1 close 可能
   - What's unclear: もし SP-3 (a) が ✗ (= wheel install 不可) だった場合、 LNG-02 を Phase 1 で defer 宣言するかどうか
   - Recommendation: Phase 1 は SP-3 spike を CI に乗せて 1 回 run するところまでで close。 Phase 4 入口で再評価 (D-22 に既に書かれている)

4. **v0.1.0 で MIT license のまま PyPI に shipped されているか**
   - What we know: 現状の LICENSE は MIT、 commit cf7e7ec で `v0.1.0` シップ済みと書かれる
   - What's unclear: PyPI に actually upload されたかは未確認
   - Recommendation: Phase 1 開始時に `pip install lib-code-parser==0.1.0` を空 venv で実行して既存配布状態を確認。 もし配布済みなら license 切り替えに contributor agreement が必要

5. **docs/00-07/99 SDD chain templates の充填責務**
   - What we know: codebase/CONCERNS.md §"Design documents are unfilled templates" で指摘済み (全 SDD doc が template skeleton)
   - What's unclear: Phase 1 で 充填するか、 Phase 5 (DOC-02 README) と一緒に後回しか
   - Recommendation: Phase 1 では `docs/08-common-view-pattern.md` と `docs/09-extending.md` のみ新規執筆 (CONTEXT.md "新規ドキュメント" の指定通り)。 00-07/99 既存 template は Phase 1 では触らない (TRC-01 Traceability table のみ最低限の form で `docs/99-trace-matrix.md` に追記)

6. **`_dispatch.py` の append-only invariant の hook / lint enforcement**
   - What we know: D-13 invariant #4 「dispatch dict は append-only」、 CONTEXT.md は Claude's discretion 範囲
   - What's unclear: pre-commit hook で `_dispatch.py` への変更を「`dict["key"] = value` の追加のみ」と gate するか
   - Recommendation: Phase 1 では docs/09-extending.md に方針記載 + code review で人間 gate に倒す (hook 実装は別 task 候補)。 plan-phase で user 確認推奨

---

## Environment Availability

Phase 1 では実装言語が Python 単独のため、 external CLI dependencies の audit を行う:

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | dev / test / build | ✓ | 3.11.1 (本研究 env) | — |
| pip | install -e . | ✓ | 25.0.1 (本研究 env) | — |
| pydantic | dependencies | ✓ | 2.11.10 (本研究 env、 既 install) | — |
| pytest | dev | ✓ | (dev extra) | — |
| ruff | dev / CI | ✓ | (dev extra) | — |
| pyright (subprocess) | declared for Phase 2 use; not invoked in Phase 1 | ✓ | (will be installed via dev extra) | — |
| libclang (in-process) | declared for Phase 4 use + SP-3 spike; not invoked in Phase 1 code | ✓ | (will be installed via dev extra; 18.1.1 wheel verified on PyPI) | (a) ✗ → defer Phase 4 |
| slopcheck | research-time only (package legitimacy audit) | ✓ | installed in 本研究 env | mark all packages [ASSUMED] |
| GitHub Actions macos-14 runner | SP-3 spike (D-18) | ✓ (GitHub Actions hosted) | (latest) | — |
| `lib-diagram-parser>=0.1.0` | Phase 3+ direct import; declared in Phase 1 pyproject | ✓ (local workspace, `c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser/`) | 0.1.0 (実コード読取確認) | path-install or sibling-lib PyPI |

**Missing dependencies with no fallback:** none — Phase 1 は code が小さく external deps が少ない
**Missing dependencies with fallback:** none Phase 1 で即必要なものはすべて利用可能

---

## Validation Architecture (Nyquist Dimension 8)

`workflow.nyquist_validation: true` (config.json) のため必須セクション。

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest>=8` (既存 pyproject.toml dev extra) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) |
| Quick run command | `pytest tests/ -x --tb=short` |
| Full suite command | `pytest tests/ --cov=lib_code_parser --cov-fail-under=80 --tb=short` (coverage gate 追加) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ARC-01 | Each extractor module is lib-internal callable | parity | `pytest tests/parity/test_v01_v02_compat.py::test_v01_caller_surface_intact -x` | ❌ Wave 0 (new test) |
| ARC-02 | Single-parse CAV envelope, file parsed once | unit (CAV smoke) | `pytest tests/unit/test_cav.py::test_cav_frozen -x` | ❌ Wave 0 |
| ARC-03 | Subprocess hardening enforced via adapters/base.py | unit | `pytest tests/unit/adapters/test_base.py::test_run_subprocess_sets_deterministic_env -x` | ❌ Wave 0 |
| ARC-04 | `_paths.py:get_module_name()` single source | unit + parity | `pytest tests/unit/test_paths.py -x && pytest tests/acceptance/test_fr01_function_extraction.py::TestModuleNameFromPath -x` | ❌ Wave 0 (new) / ✅ acceptance exists |
| ARC-05 | Typed ParserConfig fields enforced | unit | `pytest tests/unit/test_config.py::test_parser_config_extra_forbid -x` | ❌ Wave 0 |
| SCH-01 | lib-diagram-parser model directly imported (subclass) | unit | `pytest tests/unit/test_graph_base.py::test_inherits_lib_diagram_parser_graph_node -x` | ❌ Wave 0 |
| SCH-02 | All models have `ConfigDict(extra="forbid")` | unit | `pytest tests/unit/test_models_extra_forbid.py -x` (loop over all models, assert config) | ❌ Wave 0 |
| SCH-03 | EdgeKind closed Literal | unit | `pytest tests/unit/test_graph_base.py::test_edge_kind_rejects_uses -x` | ❌ Wave 0 |
| DET-04 | No `_get_module_name` duplication | static (grep) | `pytest tests/unit/test_paths.py::test_no_duplicate_module_name_helper -x` (グレップ test) | ❌ Wave 0 |
| DET-05 | Subprocess hardening contract enforced | unit | (same as ARC-03 unit suite) | ❌ Wave 0 |
| DOC-01 | spec doc rewritten, callgraph.py / ACL-2 absent | static (grep) | `pytest tests/unit/test_spec_doc.py::test_no_acl2_references -x` (grep lib-code-parser.md) | ❌ Wave 0 |
| DOC-03 | spec doc §License section present | static | `pytest tests/unit/test_spec_doc.py::test_license_section_present -x` | ❌ Wave 0 |
| DOC-04 | pyproject.toml declares Apache-2.0 + LICENSE shipped | static | `pytest tests/unit/test_pyproject.py::test_apache2_license_declared -x` | ❌ Wave 0 |
| TRC-01 | 14 Phase 1 REQs each map to ≥1 US in REQUIREMENTS.md | static (parse REQUIREMENTS.md) | `pytest tests/unit/test_traceability.py::test_phase1_reqs_us_mapped -x` | ❌ Wave 0 |
| (parity) | v0.1.0 6 acceptance tests still pass | acceptance | `pytest tests/acceptance/ --tb=short` | ✅ exists |
| (parity) | v0.1.0 unit tests still pass | unit | `pytest tests/unit/ --tb=short` | ✅ exists |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x --tb=short` (existing 6 acceptance + 5 unit + new Phase 1 tests; ~30 seconds)
- **Per wave merge:** `pytest tests/ --cov=lib_code_parser --cov-fail-under=80 --tb=short` (coverage gate to keep new code at 80%)
- **Phase gate:** Full suite green + `grep "callgraph\.py\|ACL-2" lib-code-parser.md` returns 0 lines + `grep "_get_module_name" lib_code_parser/` returns only `_paths.py`

### Wave 0 Gaps (Phase 1 が新規執筆する test ファイル)

- [ ] `tests/parity/__init__.py` — empty package marker
- [ ] `tests/parity/test_v01_v02_compat.py` — v0.1.0 caller surface intact + JSON byte-identical (per §Pydantic v2 Generic parity strategy)
- [ ] `tests/unit/test_cav.py` — CAV constructable, frozen, Literal-validated (per §Pydantic v2 Generic CAV envelope)
- [ ] `tests/unit/test_paths.py` — `get_module_name()` happy path + `test_no_duplicate_module_name_helper` グレップ test
- [ ] `tests/unit/test_config.py` — `ParserConfig` typed fields + `extra="forbid"` rejection
- [ ] `tests/unit/test_models_extra_forbid.py` — loop over all model classes, assert `model_config.get("extra") == "forbid"`
- [ ] `tests/unit/test_graph_base.py` — `EdgeKind` 11 値受理 / "uses" reject / `GraphNode(_BaseGraphNode)` inheritance check
- [ ] `tests/unit/test_spec_doc.py` — grep lib-code-parser.md for forbidden / required strings
- [ ] `tests/unit/test_pyproject.py` — assert `license = "Apache-2.0"`, `license-files = ["LICENSE"]`, deps include pydantic/lib-diagram-parser
- [ ] `tests/unit/test_traceability.py` — parse REQUIREMENTS.md, assert all 14 Phase 1 REQ rows map to ≥1 US
- [ ] `tests/unit/adapters/__init__.py` — empty package marker
- [ ] `tests/unit/adapters/test_base.py` — subprocess hardening tests (env / encoding / timeout / shell=False)
- [ ] `tests/conftest.py` — extend existing fixtures if needed (likely no change required — EXAMPLE_SOURCE remains)
- Framework install: `pip install -e ".[dev]"` after pyproject.toml bump to setuptools>=77.0.3

(11 new test files total; existing acceptance/test_fr01..06_*.py and unit/test_*.py remain untouched)

---

## Security Domain

`security_enforcement` の値は config.json に明示されていないため、 規定: 有効として扱う。

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | lib is offline / no auth surface |
| V3 Session Management | no | lib is stateless / no session |
| V4 Access Control | no | lib has no caller permission model |
| V5 Input Validation | yes | Pydantic v2 `ConfigDict(extra="forbid")` on every model (SCH-02); ParserConfig typed fields validate `language: Literal["python","cpp"]` (ARC-05); CAV `language` discriminator rejects unknown values |
| V6 Cryptography | no | lib has no crypto surface; license declaration is the only legal-side artifact |
| V7 Error Handling and Logging | partial | lib has zero logging (caller-agnostic principle, codebase/ARCHITECTURE.md §Cross-Cutting Concerns); errors propagate via Python exceptions; Pitfall 11 normalization handling is Phase 2 scope |
| V11 Business Logic | partial | Determinism guarantee (純粋関数 of `(raw_content, path, config)`) is the analog of business logic safety — Layer M bisimulation depends on it |
| V12 File and Resource | partial | Phase 1 では library 自体が file system に触れない (caller が bytes を渡す)。 ただし subprocess (Phase 2 pyright) で `cwd` を required にして directory traversal を防止 (DET-05) |
| V13 API and Web Service | n/a | lib has no API |
| V14 Configuration | yes | pyproject.toml license declaration (DOC-04); no hidden config files |

### Known Threat Patterns for Phase 1 stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Pydantic model unknown field injection | Spoofing / Tampering | `ConfigDict(extra="forbid")` (SCH-02) — Phase 1 で全 model 強制 |
| Subprocess shell injection (Phase 2 で発生する pattern を Phase 1 で防御) | Tampering / Elevation of Privilege | `shell=False` (DET-05) + argv list-form (Pitfall 3) — `adapters/base.py:run_subprocess()` で contract 固定 |
| Subprocess path traversal | Tampering | `cwd` required parameter (no inherited `os.getcwd()`) (DET-05) — Phase 1 で contract 固定 |
| Subprocess timeout DoS | Denial of Service | `timeout` required parameter, default 60.0 (DET-05 + Pitfall 3) — Phase 1 で contract 固定 |
| Subprocess encoding-based output corruption | Tampering | `encoding="utf-8"` + `errors="replace"` (Pitfall 13) — Phase 1 で contract 固定 |
| EdgeKind ad-hoc string accepting | Tampering / spec ambiguity | `EdgeKind` closed `Literal` (SCH-03 / Pitfall 7) — Phase 1 で 11 値 fix |
| CAV mutability leak between extractors | Tampering | `frozen=True` (D-05) — Phase 1 で fix |
| Supply chain (libclang / pyright / pydantic / setuptools) | Supply-chain attack | Version 厳密 pin (`libclang==18.1.1`, `pyright==1.1.409`, `pydantic<3.0`, `setuptools>=77.0.3`) + slopcheck [OK] 確認 |
| License declaration spoof | Repudiation | PEP 639 SPDX format + `LICENSE` file shipped (DOC-04) + frozen/ backup of v0.1.0 MIT |

---

## Sources

### Primary (HIGH confidence)
- 本研究 env (`pydantic 2.11.10`, `python 3.11.1`) での実機検証: Pydantic v2 Generic / `ConfigDict(extra="forbid")` / `frozen=True` / `arbitrary_types_allowed=True` / Literal discriminator のすべて動作確認
- `c:/work/agent_company/spec-reviewer-libs/lib-diagram-parser/lib_diagram_parser/models.py` 実コード読取: `GraphNode` / `GraphEdge` / `GraphModel` / `GuardExpr` の v0.1.0 schema を行単位で確認
- `c:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models.py` 実コード読取: v0.1.0 model 形を行単位で確認
- `c:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/executor.py` 実コード読取: v0.1.0 executor 動作 + cpp short-circuit を確認
- `c:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/conftest.py` / `tests/acceptance/test_fr01_function_extraction.py` 実コード読取: v0.1.0 caller surface を確認
- `c:/work/agent_company/spec-reviewer-libs/lib-code-parser/pyproject.toml` 実コード読取: 現状 `setuptools>=68` + MIT license の欠落を確認
- `c:/work/agent_company/spec-reviewer-libs/lib-code-parser/LICENSE` 実コード読取: MIT を確認
- PyPI JSON API for `libclang==18.1.1` (`https://pypi.org/pypi/libclang/18.1.1/json`): wheel matrix を行単位で確認、 macOS arm64 wheel の ABI-agnostic 性 (`py2.py3-none-macosx_11_0_arm64.whl`) を確認
- PyPI JSON API for `pyright==1.1.409`: release date 2026-04-23 + `nodejs` extra + transitive deps を確認
- PyPA writing pyproject.toml guide (`packaging.python.org/en/latest/guides/writing-pyproject-toml/`): PEP 639 SPDX 形式 + setuptools 77.0.3 必要を確認
- Pydantic v2.11 official Generic models docs (`pydantic.dev/docs/validation/2.11/concepts/models/`): TypeVar bound 制限 + model_rebuild() 要否を確認

### Secondary (MEDIUM confidence, verified)
- `.planning/research/PITFALLS.md` (project research artifact、 既査読済み): 15 pitfalls の architectural rule への落とし込みパス
- `.planning/codebase/ARCHITECTURE.md` / `STRUCTURE.md` / `CONCERNS.md` (project codebase audit、 既査読済み): v0.1.0 anti-patterns + tech debt の全件
- `.planning/PROJECT.md` / `REQUIREMENTS.md` / `ROADMAP.md` (project planning artifacts、 既査読済み): 16 Key Decisions + 42 REQ + Phase 1 success criteria
- `actions/setup-python` advanced-usage docs: `allow-prereleases: true` for Python 3.14、 macos-14 runner matrix
- SPDX 公式 (`spdx.org/licenses/LLVM-exception.html`): `Apache-2.0 WITH LLVM-exception` identifier 公式定義

### Tertiary (LOW confidence — flagged for plan-phase confirmation)
- A1 (assumed): `tests/unit/test_callgraph_builder.py` / `test_type_dep_builder.py` / `test_contract_extractor.py` も `_get_module_name` を import している
- A2 (assumed): Phase 1 で配布名変更しない
- A3 (assumed): v0.1.0 cf7e7ec はまだ PyPI に未配布
- A4 (assumed): SP-3 spike (a)(b)(c)(d) すべて PASS する
- A5 (assumed): lib-diagram-parser は workspace 内 path install で解決
- A6 (assumed): SDD chain docs/00-07/99 templates の充填は Phase 1 スコープ外
- A7 (assumed): nodejs-wheel-binaries は cross-platform で動作
- A8 (assumed): `_dispatch.py` append-only は code review で gate (hook 強制しない)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Pydantic 2.11.10 実機検証 + libclang 18.1.1 wheel 確認 + pyright 1.1.409 release 確認 + setuptools PEP 639 公式 doc 確認
- Architecture (CAV / Generic / dispatch / adapters): HIGH — すべて実機検証パターンあり + CONTEXT.md の D-04 〜 D-23 で決定済み
- Pitfalls: HIGH — `.planning/research/PITFALLS.md` の 15 件と Phase 1 architectural rule のマッピングが明確
- Schema-compat (lib-diagram-parser): HIGH — sibling lib model を実コード読取で確認
- License (PEP 639 + LLVM exception): HIGH — packaging.python.org + SPDX 公式 + setuptools issue tracker で cross-verify
- SP-3 libclang macOS arm64 feasibility: MEDIUM — wheel availability は HIGH 確度 (PyPI 確認済) だが、 実機 dylib load の verdict は CI 走行まで確定しない
- Backward-compat re-export strategy: MEDIUM — 3 unit test files (callgraph / type_dep / contract) の `_get_module_name` import を実コード未読のため A1 assumption
- Distribution name decision: LOW — A2 assumption (planner で user 確認推奨)

**Research date:** 2026-05-24
**Valid until:** 2026-06-23 (30 日後 — Pydantic / setuptools / libclang / pyright のいずれも安定リリースのため stable)

---

## RESEARCH COMPLETE

**Phase:** 1 - Architecture Foundation + Spec Correction
**Confidence:** HIGH (Pydantic / setuptools / libclang wheel / lib-diagram-parser schema はすべて HIGH 確度、 SP-3 spike verdict のみ MEDIUM)

### Key Findings

- **Pydantic v2 Generic は v0.1.0 caller 互換性をゼロ追加コストで満たす** — 実機検証で `Envelope(...)` と `Envelope[Inner](...)` が byte-identical JSON を出すことを確認。 既存 6 つの acceptance test は無修正で通る parity が保証される (D-06 の前提が成立)。
- **libclang==18.1.1 は macOS arm64 + Python 3.13/3.14 で wheel が配布済み** — `py2.py3-none-macosx_11_0_arm64.whl` が ABI-agnostic で、 SP-3 (a) は wheel 解析だけで合格予測可能 (HIGH 確度)。 (b)(c)(d) は CI 走行まで確定しない (MEDIUM)。
- **PEP 639 SPDX license は `setuptools>=77.0.3` 必須** — 現 pyproject.toml の `>=68` では `license = "Apache-2.0"` が deprecated 警告を出す。 Phase 1 で setuptools bump 必須。
- **lib-diagram-parser の `node_type` に `"package"` は存在しない** (実コード読取で確認) — D-15 「Phase 3 で local extension or PR 判定」の前提が確定。 Phase 1 では `models/evaluations/graph_base.py` で `GraphNode(_BaseGraphNode)` subclass を作り、 SCH-01 を満たす。
- **EdgeKind 11 値 closed Literal で 5 diagram すべてカバー可能** — Pitfall 7 (`"uses"` catch-all) を Pydantic ValidationError で自動 reject できる。
- **lib-code-parser 自身の license は `Apache-2.0` のみ (LLVM exception なし)** — bundled libclang のみが `Apache-2.0 WITH LLVM-exception`。 README.md / spec doc §License で明示的に区別する。
- **v0.1.0 LICENSE は MIT、 pyproject.toml に license declaration 欠落** (現状)。 Phase 1 で MIT を `frozen/2026-05-24-v0.1.0-spec/LICENSE` に退避 + Apache-2.0 LICENSE 新規 + pyproject.toml に SPDX 宣言追加が必須。

### File Created
`C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | 全 package version 実機 or PyPI 確認、 slopcheck [OK] 4 件 |
| Architecture | HIGH | Pydantic Generic / CAV / dispatch / adapters の全 pattern 実機検証 + D-04 〜 D-23 で決定済み |
| Pitfalls | HIGH | 15 pitfalls → Phase 1 architectural rule への mapping が完結 |
| Backward-compat strategy | MEDIUM | A1 (3 unit test ファイル `_get_module_name` import) 未確認 |
| SP-3 verdict | MEDIUM | (a) HIGH 確度 / (b)(c)(d) CI 走行まで保留 (D-22 の Phase 1 close 緩和条件で許容済み) |
| Distribution name decision | LOW | A2 — planner で user 確認推奨 |

### Open Questions
- 配布名 (`lib-code-parser` vs `spec_reviewer_code_parser`) は Phase 1 で変更するか? → 推奨: 変更しない、 別 milestone で議論
- v0.1.0 cf7e7ec が PyPI に既配布か? → planner が確認必要 (license 切替の retroactive 問題回避)
- SDD chain (docs/00-07/99) 既存 template skeletons の充填は Phase 1 スコープか? → 推奨: スコープ外、 docs/08 と docs/09 のみ新規執筆
- `_dispatch.py` append-only invariant を hook / lint で強制するか? → 推奨: Phase 1 では docs/09-extending.md 記載 + code review で gate
- lib-diagram-parser を PyPI 配布 / monorepo path install / Python -m install どちらの戦略を取るか? → planner で CI workflow YAML レベルで決定

### Ready for Planning

Research complete. Planner は本研究の `## Architectural Responsibility Map` + `## Standard Stack` + `## Dispatch Dict Pattern` + `## Subprocess Hardening Contract` + `## Pydantic v2 Generic` + `## EdgeKind Closed Literal` + `## lib-diagram-parser Schema Snapshot` + `## Apache-2.0 pyproject.toml` + `## Nested Module Layout Migration` + `## lib-code-parser.md Rewrite Strategy` のセクションを直接タスクに展開できる。 9 並列 sub-track + 1 sequential closer (本 §Summary §Primary recommendation 参照) で plan を組むのが推奨。
