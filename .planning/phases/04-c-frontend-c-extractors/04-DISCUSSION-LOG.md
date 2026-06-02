# Phase 4: C++ Frontend + C++ Extractors - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 4-C++ Frontend + C++ Extractors
**Areas discussed:** C++ dispatch architecture, C++ schema-parity fidelity boundary, libclang determinism + import guard, Doxygen SourceKind extension

> Discussion format: contract-level only (per project feedback memory — architecture / concept /
> acceptance criteria は user 相談、下位 implementation detail は agent 自律). Presented as
> decision + rationale + 異議受付 in conversational text (no AskUserQuestion popup). User approved
> all 4 decisions in a single "OK".

---

## A. C++ dispatch architecture (locked 契約衝突の解消)

| Option | Description | Selected |
|--------|-------------|----------|
| 言語次元を dispatch に導入 (`dict[language, dict[name, fn]]`) | executor が `cav.language` で extractor セット選択。Python ファイル不変、cpp は新ファイル、parity + determinism 両立 | ✓ |
| 既存 extractor 内に `cav.language` 分岐 | Open-Closed 不変条件 #2 が明示的に禁止する anti-pattern | |
| フラット維持 + cpp slot を別名にし verifier で吸収 | parity (LNG-04) を verifier 側に押し付ける、DET-01 空上書きリスク残る | |
| Frontend normalization (libclang TU → ast 互換 IR) | 非忠実・大規模・C++ 構造を ast.Module で表現不能 → 棄却 | |

**User's choice:** 言語次元導入 (D-01/D-02/D-03)
**Notes:** これは「選択肢提示」ではなく **locked 契約同士の矛盾の報告** として提示。Open-Closed
不変条件 #2/#4 と executor の「フラット 1 名前=1 関数・run-all-registered・name==slot」契約が衝突し、
現行契約のままでは C++ トラックが実装不能であることを示した。言語次元導入は parity と determinism を
最小コストで両立する唯一の遵守可能解。「executor body は増やさない」不変条件を言語軸についてのみ明示改訂。

---

## B. C++ schema-parity の忠実度境界

| Option | Description | Selected |
|--------|-------------|----------|
| struct/class/free fn/method/namespace/include/継承/メンバ型依存 を must-have、template/macro/overload は best-effort | 決定論的に抽出可能な範囲を v0.2.0 必須、文脈依存の完全解決は v0.3.0 候補 | ✓ |
| template も v0.2.0 必須 | 非決定論リスク、SP-1 の「決定論不可なら defer」基準に反する | |

**User's choice:** best-effort 境界 (D-04/D-05)
**Notes:** Core Value (決定論的事実抽出) と整合。未解決 include は diagnostics warning (parse error にしない)。
composition/aggregation は値=composes / ポインタ・参照=aggregates / 解決不能=associates の C++ 対応決定論ルール。

---

## C. libclang determinism + import 時 runtime guard の位置

| Option | Description | Selected |
|--------|-------------|----------|
| libclang を frontends/cpp.py (in-process)、guard は cpp frontend import 時に遅延ロード | Python 専用 caller に libclang ロードを強制しない、no-I/O-at-import 維持 | ✓ |
| LNG-03 を厳密解釈し `import lib_code_parser` で必ず eager に libclang guard 起動 | Python 専用でも毎 import で dylib ロード | |

**User's choice:** in-process + 遅延 guard (D-06/D-07)
**Notes:** adapters/ は subprocess 専用と確定 (libclang は非適用)。determinism は cursor 走査順 + sort-on-exit
+ DET-02 ABI assertion で担保。LNG-03 の「library import」は「C++ frontend module の import」と解釈。

---

## D. Doxygen 契約の SourceKind 拡張方式 (SPC-03)

| Option | Description | Selected |
|--------|-------------|----------|
| SourceKind Literal に Doxygen 値を additive 追加 + 既存 contracts slot 共用 | parity 維持、新 field 不要、EdgeKind additive 政策と同型 | ✓ |
| source_kind 拡張せず別 field を立てる | parity を崩す | |

**User's choice:** additive Literal 拡張 (D-08/D-09)
**Notes:** 単一 `"doxygen"` + 既存 `ContractEntry.kind` で pre/post/invariant 区別が第一候補 (細部 agent 自律)。
既存 4 値の削除・改名は禁止。docs/09 に Literal additive 拡張政策を明記。

---

## Claude's Discretion

- libclang cursor 走査の具体実装、C++ fixture corpus 選定、個別 edge/type 判定ルールの細部
- composition/aggregation の C++ 境界ケース、namespace → module/package マッピング細部
- Doxygen comment parser の実装方式、SourceKind の単一値 vs 3 値の最終選択
- test 戦略 (parity primary/backup)、CI matrix YAML 構造、`_dispatch.py` ネスト化の migration 刻み

## Deferred Ideas

- template/macro 完全展開忠実度 → v0.3.0 候補 (実需が出たタイミング)
- LNG-02-FULL (macOS arm64 完全保証) → v0.3.0 (REQUIREMENTS v2 既記載)
- DET-01 snapshot / SCH-04 cross-lib compat / DOC-02 README matrix → Phase 5 (acceptance phase)
