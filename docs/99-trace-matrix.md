# lib-code-parser Trace Matrix

> FR（機能要求）→ AT（受入テスト）→ Code（実装）→ Test（単体テスト）のトレーサビリティを管理する。
> design doc §7 Step 15 参照。
> **実装完了後に全 FR が網羅されていることを確認してから push すること。**

---

## Trace Matrix

| FR ID | FR 概要 | Gherkin シナリオ | 受入テストファイル | 実装ファイル | 単体テストファイル | 完了 |
|-------|---------|----------------|-----------------|------------|-----------------|------|
| LIB-FR-01 | [FR の概要] | Feature: [シナリオ名] | tests/test_[name].py::test_[scenario] | [lib_name]/[module].py | tests/test_[module].py::test_[unit] | [ ] |
| LIB-FR-02 | [FR の概要] | Feature: [シナリオ名] | tests/test_[name].py::test_[scenario] | [lib_name]/[module].py | tests/test_[module].py::test_[unit] | [ ] |

---

## カバレッジサマリ

| 指標 | 件数 |
|------|------|
| FR 総数 | N |
| AT（Gherkin シナリオ）総数 | N |
| 実装ファイル総数 | N |
| 単体テスト総数 | N |
| 全 FR 網羅済み | YES / NO |

---

## トレーサビリティ確認チェックリスト

- [ ] 全 FR ID が Trace Matrix に記載されている
- [ ] 各 FR に少なくとも 1 件の Gherkin シナリオが対応している
- [ ] 各 Gherkin シナリオに受入テストファイルのパスが記載されている
- [ ] 各 FR に対応する実装ファイルが記載されている
- [ ] 各 FR に対応する単体テストが記載されている
- [ ] pytest で全テスト PASS が確認されている
- [ ] カバレッジサマリの「全 FR 網羅済み」が YES になっている

**Decision Log**: #15-1（Trace Matrix 完成の確認を記録）

---

<!-- Step 9（scaffold）前にこのファイルのスケルトンを作成し、実装中に逐次更新する -->
<!-- Step 15 でこの Matrix を最終確認してから push する -->

---

## Phase 1 — Architecture Foundation + Spec Correction (TRC-01)

各 Phase 1 要件 (14 件) を、それを支える User Story (US) と Phase 1 内の closure plan に対応づける。
情報源は `.planning/REQUIREMENTS.md` §Traceability の 42 行表 (Phase 1 抜粋)。

| Requirement | US support | Phase 1 closure plan |
|-------------|------------|----------------------|
| ARC-01 | US-01, US-22, US-25, US-32 | Plan 09 (substrate: nested layout enables module-level extractor isolation; full closure in Phase 2 when extractors exist as standalone functions) |
| ARC-02 | US-01, US-22, US-25, US-32 | Plan 03 (CAV envelope) + Plan 09 (model layer wiring) |
| ARC-03 | US-01, US-22, US-25, US-32 | Plan 07 (adapters/base.py SubprocessAdapter ABC + run_subprocess helper) |
| ARC-04 | US-01, US-22, US-25, US-32 | Plan 06 (_paths.py) + Plan 09 (4 extractor shims point to _paths.get_module_name) |
| ARC-05 | US-01, US-22, US-25, US-32 | Plan 03 (typed ParserConfig — params dict removed) |
| SCH-01 | US-25, US-32 | Plan 05 (graph_base.py — Phase 1 self-contained per pre-resolved decision #5; Phase 3 revisits direct-import vs subclass) |
| SCH-02 | US-25, US-32 | Plans 03 / 04 / 05 (extra="forbid" on all 5+8+4 = 17 models) |
| SCH-03 | US-25, US-32 | Plan 05 (EdgeKind closed Literal, 11 values, "uses"/"other"/"misc" rejected) |
| DET-04 | US-01, US-22, US-25, US-32 | Plan 06 (_paths.py) + Plan 09 (grep gate: single def in _paths.py) |
| DET-05 | US-01, US-22, US-25, US-32 | Plan 07 (subprocess hardening helper — all 6 invariants enforced) |
| DOC-01 | US-01, US-22, US-25, US-32 | Plan 02 (spec doc full rewrite — callgraph.py / ACL-2 removed; v0.2.0 6 sections present) |
| DOC-03 | US-01, US-22, US-25, US-32 | Plan 02 (spec doc §License "No GPL bundled" disclosure); README mirror is Phase 5 |
| DOC-04 | US-01, US-22, US-25, US-32 | Plan 01 (LICENSE Apache-2.0 + pyproject.toml SPDX + setuptools>=77.0.3) |
| TRC-01 | US-01, US-22, US-25, US-32 | This row + Plan 02 spec doc §Traceability (14 `Traces:` tags) — closed by Plan 10 |

Phase 2-5 rows will be appended at their respective phase close. Source of truth: `.planning/REQUIREMENTS.md` §Traceability (42 rows mapped to 5 phases as of 2026-05-24).

TRC-02 / TRC-03 closure is a Phase 2 deliverable (per-module REQ-ID docstring declaration + Traces regex).
