# Phase 4: C++ Frontend + C++ Extractors - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 で固定した **CAV 境界の裏で C++ トラックを立ち上げる** phase。libclang ベースの
C++ Frontend を実装し、C++ AST primitives (functions / call graph / type info / includes)・
5 種 diagram・Doxygen 駆動の契約抽出を、**Python トラックと schema parity (同一 Pydantic shape)**
で出力する。加えて platform CI matrix (mandatory: Linux x86_64/aarch64 + Windows x86_64 ×
Python 3.11–3.14 / best-effort: macOS arm64 × Python 3.13/3.14) を立ち上げる。

スコープに含まれる Requirements: **LNG-01, LNG-02, LNG-03, LNG-04, LNG-05, SPC-03, DET-02** (7 件)

スコープに含まれないもの:
- Cross-cutting acceptance test (snapshot DET-01 / cross-lib schema compat SCH-04 / README compat
  matrix DOC-02) — Phase 5
- Python トラックの拡張 (Phase 2/3 で完了済み)
- template/macro 完全展開・overload 完全解決の完全忠実度 — best-effort (下記 D-04、完全版は v0.3.0 候補)
- 汎用制御フロー由来 state (SP-1 DEFER 済み) / sequence branch full (SP-2 は SHIP 済み、C++ にも適用)

**前提 (prior phase からの carry-forward — 再質問しない):**
- CAV は `language: Literal["python","cpp"]` + opaque `payload` で既に C++ 対応済み (Phase 1 D-04)
- レイアウト上 `frontends/cpp.py` + `extractors/` の配置は確定済み (Phase 1 D-10)
- **SP-3 verdict = ship-best-effort** (libclang 18.1.1 が macOS arm64 × Python 3.13/3.14 で
  全 4 ステップ PASS、再 spike 不要) — `.planning/spikes/SP-3-libclang-macos-arm64.md`

</domain>

<decisions>
## Implementation Decisions

### A: C++ extractor の dispatch 方式 (locked 契約衝突の解消)

**背景 (発見した契約衝突):** Open-Closed 不変条件 #2 (既存評価単位は変更不可、言語フラグ条件分岐は
anti-pattern) / #4 (dispatch dict append-only、既存 entry の callable 差し替え禁止) と、executor の
「フラット 1 名前=1 関数・全 entry 無条件実行 (run-all-registered #6)・name == CodeContent slot 名」
契約が衝突する。C++ extractor を別ファイル別 entry で足すと (1) CodeContent slot 不在、(2) Python CAV
に対しても cpp extractor が走り Python 結果を空上書きし DET-01 byte-identical と LNG-04 parity を破る。
既存ファイル内 `cav.language` 分岐は不変条件 #2 が禁止。→ **現行契約のままでは C++ トラック実装不能。**

- **D-01:** dispatch に **言語次元を 1 度だけ導入**する。`FRONTENDS` / `PRIMITIVES` / `EVALUATIONS` を
  `dict[language, dict[name, fn]]` 形にネストし、executor は `cav.language` で extractor セットを選択
  (`for name, fn in EVALUATIONS[cav.language].items()`)。
- **D-02:** これにより (1) 既存 Python extractor ファイルは一切不変 (不変条件 #1/#2 完全遵守、C++ は
  全て新ファイル)、(2) cpp extractor は cpp CAV にのみ走り DET-01 を守る、(3) 言語次元内では依然
  append-only (将来 Java は `["java"]` 追加のみ)、(4) 出力 slot 名は両言語共通 (`class_diagram` 等) で
  LNG-04 parity を自然に満たす。
- **D-03:** Phase 1 の「executor body は増やさない」不変条件を **言語軸についてのみ明示的に改訂**する
  (executor 1 行 + `_dispatch.py` ネスト化の 1 回限りの構造変更)。`docs/09-extending.md` に言語次元の
  追加手順と「言語キーは append-only」invariant を追記する。

### B: C++ schema-parity の忠実度境界 (v0.2.0 must-have vs v0.3.0 defer)

- **D-04:** v0.2.0 must-have = **struct / class / free function / method / namespace / include /
  継承 (多重含む) / メンバ型依存**。composition vs aggregation は **値メンバ = composes /
  ポインタ・参照 = aggregates / 解決不能 = associates** の決定論ルール (Python 規則の C++ 対応版)。
- **D-05:** **template / macro 展開・overload 解決の完全性は best-effort**。未解決 `#include` は
  `diagnostics` warning とし parse error にしない (SC#3 準拠、LNG-05)。完全忠実度 (template 完全
  instantiation 等) は v0.3.0 候補として明記 (下記 Deferred)。
- **根拠:** Core Value は決定論的事実抽出。template/macro 完全解決は libclang でも文脈依存で
  非決定論リスクがあり、SP-1 の「決定論ルール構築不可なら次ミルストン」基準と整合。

### C: libclang の determinism 契約と import 時 runtime guard の位置

- **D-06:** libclang は **`frontends/cpp.py` (in-process ctypes) に置き、`adapters/` には入れない**。
  `adapters/` は subprocess 専用と確定。libclang の determinism は subprocess env hardening ではなく
  **決定論的 cursor 走査順 + sort-on-exit (DET-04 と同型) + DET-02 ABI assertion** で担保する。
- **D-07:** runtime guard (`cindex.Index.create()` 一回 + bundled libclang 18.1.1 の ABI 検証 +
  `Config.set_library_file` override 拒否、LNG-03/DET-02) は **C++ frontend module の import 時に
  1 回だけ**実行する遅延ロードとし、Python 専用 caller のパスからは libclang をロードしない
  (no-I/O-at-import 維持)。LNG-03 の「library import triggers guard」は「C++ frontend module の
  import」と解釈する。SC#2 の `import lib_code_parser` ガード要件は cpp frontend を含む実行パスで
  満たす (必要なら `__init__.py` から cpp frontend を import して eager 起動も許容 — 実装時に確定)。

### D: Doxygen 契約の SourceKind 拡張方式 (SPC-03)

- **D-08:** `models/primitives/contracts.py` の `SourceKind` Literal に **Doxygen 用の値を additive に
  追加**する (単一 `"doxygen"` + 既存 `ContractEntry.kind` で pre/post/invariant を区別する案を第一候補。
  細部は agent 自律)。既存 4 値の削除・改名は禁止。`docs/09-extending.md` に「Literal の追記は
  additive 拡張として許容、既存値の削除・改名は禁止」を EdgeKind MAJOR 政策と同様に明記する。
- **D-09:** C++ Doxygen 契約は既存 `CodeContent.contracts` slot を共用し新 field を立てない
  (parity 維持)。`\pre` / `\post` / `\invariant` を `ContractInfo` / `ContractEntry` の同 schema で出す。
  `Traces: REQ-ID, US-NN` の trace tag 抽出が Python docstring と C++ Doxygen comment で同一動作する
  こと (TRC-03 parity) を test で確認する。

### Claude's Discretion (下位 implementation detail — user ノータッチ)

- libclang cursor 走査の具体実装パターン、C++ fixture corpus の選定、個別 edge/type 判定ルールの細部
- composition/aggregation の C++ 判定の境界ケース解釈、namespace → module/package へのマッピング細部
- Doxygen comment parser の実装方式 (regex / libclang comment API)、`SourceKind` の単一値 vs 3 値の最終選択
- test 戦略 (parity test の primary/backup 構成)、CI matrix YAML の具体構造
- `_dispatch.py` ネスト化の具体的な型エイリアス・migration の刻み方 (既存 Python entry の移送手順)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (researcher / planner / executor) MUST read these before planning or implementing.**

### Phase 4 直接根拠

- `.planning/ROADMAP.md` §Phase 4 — Goal + 4 success criteria (pip install matrix / import ABI guard /
  schema parity / Doxygen contract parity)
- `.planning/REQUIREMENTS.md` — Phase 4 の 7 requirements (LNG-01..05, SPC-03, DET-02) + Definition of Done
- `.planning/PROJECT.md` — Core Value / Key Decisions (libclang 18.1.1 pin / compile_args 明示供給 /
  Doxygen TS 昇格 / macOS best-effort) / Constraints
- `.planning/spikes/SP-3-libclang-macos-arm64.md` — SP-3 verdict = ship-best-effort (libclang 18.1.1 が
  macOS arm64 × Python 3.13/3.14 で全 4 ステップ PASS。Phase 4 入口での再確認は完了扱い)

### 衝突解消の根拠 (決定 A)

- `docs/09-extending.md` — 6 Open-Closed 不変条件 (#1 既存 primitive 不変 / #2 既存評価単位不変 /
  #4 dispatch append-only / #6 run-all-registered)。Phase 4 で言語次元の追加手順 + 「言語キー append-only」
  invariant を追記する対象
- `lib_code_parser/_dispatch.py` — フラット 3 dict (FRONTENDS/PRIMITIVES/EVALUATIONS) → 言語ネスト化対象
- `lib_code_parser/executor.py` — dispatch walk (D-03 で `cav.language` 選択を 1 行追加する対象)

### 既存契約 (C++ extractor が遵守すべき shape)

- `lib_code_parser/models/infrastructure/cav.py` — CAV envelope (`language` discriminator + opaque payload、
  C++ payload = `clang.cindex.TranslationUnit`)
- `lib_code_parser/models/infrastructure/config.py` — ParserConfig (`compile_args` default `["-std=c++17"]`、
  `language`、LNG-05 の caller 供給 flag)
- `lib_code_parser/models/primitives/contracts.py` — SourceKind / ContractEntry / ContractInfo (D-08 拡張対象)
- `lib_code_parser/models/evaluations/graph_base.py` — GraphNode/Edge/Model/EdgeKind (C++ diagram の出力 schema)
- `lib_code_parser/frontends/python.py` — Python frontend (C++ frontend `frontends/cpp.py` の対称参照モデル)
- `lib_code_parser/extractors/primitives/functions.py` / `extractors/evaluations/class_diagram.py` —
  Python extractor の実装パターン (C++ 対応版を別ファイルで書く際の参照)
- `lib_code_parser/adapters/base.py` — subprocess hardening (libclang は in-process のため**非適用**、
  D-06 の「adapters/ は subprocess 専用」確認用)

### 前 phase の決定文脈

- `.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md` — D-04 (CAV polymorphism)、
  D-10 (nested layout)、D-13 (6 不変条件)、D-18..D-23 (SP-3 spike ルール)
- `.planning/codebase/ARCHITECTURE.md` / `STRUCTURE.md` / `CONVENTIONS.md` — v0.1.0 baseline 構造と規約

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontends/python.py` `build_cav()`: C++ frontend `frontends/cpp.py` の対称テンプレート (1 parse/file →
  CAV envelope、`raw_content` carry)。libclang 版は `cindex.TranslationUnit` を payload に積む
- `extractors/primitives/*.py` / `extractors/evaluations/*.py`: 各 extractor の `extract(cav, config)`
  signature + sort-on-exit (DET-04) + `assert isinstance(cav.payload, ...)` の言語ガードパターンを C++ 版でも踏襲
- `adapters/base.py` `run_subprocess()`: subprocess hardening helper — **libclang には使わない** (in-process)
- `tests/` の Python parity/fixture 構造: C++ fixture + parity test の対称構成の雛形

### Established Patterns
- **言語ガード**: 現行 extractor は `assert isinstance(cav.payload, ast.Module)` で Python 専用。D-01 の
  言語ネスト dispatch により、cpp extractor は cpp payload を前提に `assert isinstance(..., cindex.TranslationUnit)`
  を書ける (Python CAV に走らないことが保証される)
- **sort-on-exit (DET-04)**: 全 extractor が node/edge を安定 composite key でソートして emit → libclang の
  cursor 走査順非決定性も同 pattern で吸収
- **EdgeKind closed Literal + additive 拡張政策**: SourceKind の Doxygen 値追加 (D-08) も同政策に従う

### Integration Points
- `_dispatch.py`: 言語ネスト化 (D-01) の中心。既存 Python entry を `["python"]` 下に移送し、`["cpp"]` に
  C++ frontend/primitives/evaluations を append。registration-time guard (slot 名検証) を言語ごとに拡張
- `executor.py`: `cav.language` で extractor セット選択 (D-03、1 行構造変更)
- `pyproject.toml`: `libclang==18.1.1` 厳密 pin は Phase 1 で宣言済み。Phase 4 で CI matrix を mandatory に昇格
- `.github/workflows/ci.yml`: SP-3 best-effort matrix を Phase 1 で setup 済み → Phase 4 で mandatory matrix
  (Linux x86_64/aarch64 + Windows x86_64 × Python 3.11–3.14) を完成

</code_context>

<specifics>
## Specific Ideas

- **「現行契約のままでは実装不能」という発見を起点に設計する** (user 承認): 決定 A は user に選ばせた
  選択肢ではなく、locked 契約同士の矛盾の報告。言語次元導入は parity (LNG-04) と determinism (DET-01) を
  最小コストで両立する唯一の遵守可能解として user が承認した。
- **libclang は in-process、subprocess hardening は非適用** (決定 C): adapters/ 層の役割を「subprocess 専用」と
  明確化。in-process C ライブラリの determinism は cursor 走査順 + sort-on-exit + ABI guard で担保する。
- **Python/C++ 対称性が Doxygen 昇格の理由** (PROJECT.md Key Decision): C++ も `\pre`/`\post`/`\invariant` を
  Python と同 schema で出さないと verifier の処理が非対称になる。slot 共用 + SourceKind additive 拡張で対称化。

</specifics>

<deferred>
## Deferred Ideas

### v0.3.0 候補 (Phase 4 best-effort の完全版)

- **template / macro 完全展開忠実度**: v0.2.0 は best-effort (D-05)。完全な template instantiation /
  マクロ展開解析は決定論性検証を経て v0.3.0 候補。**Triggering**: 実需 (verifier が template-heavy C++ で
  parity 不足を報告) が出たタイミング
- **LNG-02-FULL (macOS arm64 完全保証)**: v0.2.0 は continue-on-error の best-effort CI。完全保証は v0.3.0
  (REQUIREMENTS.md v2 に既記載)

### Phase 5 へ送る cross-cutting acceptance

- **DET-01 snapshot test (Python + C++ 両 fixture の byte-identical 3-run)** / **SCH-04 cross-lib schema
  compat test** / **DOC-02 README platform compat matrix**: Phase 5 (acceptance phase) で実装。Phase 4 は
  各 extractor の単体 parity まで

None beyond the above — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-C++ Frontend + C++ Extractors*
*Context gathered: 2026-06-02*
