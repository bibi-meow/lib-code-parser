---
phase: 2
slug: python-frontend-ast-primitives-acl-2-adapters
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-31
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from RESEARCH.md §Validation Architecture (`02-RESEARCH.md` lines 900–945).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest >=8` (declared in `pyproject.toml` `[project.optional-dependencies].dev`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) |
| **Quick run command** | `pytest tests/parity tests/acceptance -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | Quick ~5–15s, full ~30–60s (includes pyright subprocess fixtures) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/parity -x -q` (all hard gates, fastest signal)
- **After every plan wave:** Run `pytest tests/ -v` (full suite including acceptance + adapter unit tests)
- **Before `/gsd:verify-work`:** Full suite must be green; v0.1.0 fixture snapshot diff = 0 bytes
- **Max feedback latency:** 30 seconds (quick gate)

---

## Per-Task Verification Map

> Plans not yet written; rows filled by gsd-planner using this map as contract.
> Each plan task must declare `<automated>` verify command matching one of the cells below.

| Req ID | Behavior | Test Type | Automated Command | File Exists | Source |
|--------|----------|-----------|-------------------|-------------|--------|
| AST-01 | `FunctionNode` 抽出 (class/method/function + params/return_type/docstring/trace_tags/source_range) | acceptance | `pytest tests/acceptance/test_fr01_function_extraction.py -x` | ✅ (要 typed ParserConfig 書換) | RESEARCH §7.1 |
| AST-02 | `CallGraph` emit + `(caller, callee)` lexicographic sort | acceptance + unit | `pytest tests/acceptance/test_fr02_callgraph.py tests/unit/test_callgraph_sort.py -x` | ✅ + ❌ W0 | RESEARCH §4 / §7.2 |
| AST-03 | TypeDep + pyright `resolved` annotation | acceptance + adapter unit | `pytest tests/acceptance/test_fr03_type_deps.py tests/unit/test_pyright_adapter.py -x` | ✅ + ❌ W0 | RESEARCH §2 / §7.3 |
| AST-04 | `ContractInfo` per-entry `source_kind` 4 値 + Pydantic alias 解決 + `@root_validator` 認識 | acceptance | `pytest tests/acceptance/test_fr04_contracts.py -x` | ✅ (要全面書換) | RESEARCH §3 / §7.4 |
| AST-05 | 1 parse per `execute()` call (Frontend single source) | parity (static grep + dynamic monkeypatch) | `pytest tests/parity/test_ast_05_one_parse.py -x` | ❌ W0 | RESEARCH §5 |
| DET-03 | `PYRIGHT_PYTHON_FORCE_VERSION=1.1.409` env injection | adapter unit | `pytest tests/unit/test_pyright_adapter.py::test_det_03_env_var_set -x` | ❌ W0 | RESEARCH §2.4 |
| TRC-02 | Extractor docstring 内 `Implements: AST-NN` 宣言 | parity (static grep) | `pytest tests/parity/test_trc_02_docstring.py -x` | ❌ W0 | RESEARCH §6 |
| TRC-03 | `Traces:` regex 動作の v0.1.0 parity | acceptance | `pytest tests/acceptance/test_fr05_trace_tags.py -x` | ✅ (要書換) | RESEARCH §6.4 / §7.5 |

*Status (per task): ⬜ pending · ✅ green · ❌ red · ⚠️ flaky — gsd-executor が `<state>` で更新*

---

## Wave 0 Requirements

- [ ] `tests/parity/test_ast_05_one_parse.py` — AST-05 grep static gate + monkeypatch dynamic gate (RESEARCH §5.2)
- [ ] `tests/parity/test_trc_02_docstring.py` — extractor module docstring `Implements: AST-NN` static gate (RESEARCH §6)
- [ ] `tests/parity/test_snapshot_v01_fixture.py` — D-04 shipped v0.1.0 fixture snapshot test (RESEARCH §7.6)
- [ ] `tests/parity/fixtures/v01_snapshot.json` — Phase 2 emit 出力を fix した snapshot file (commit 順序: Phase 2 全 extractor 実装後)
- [ ] `tests/unit/test_pyright_adapter.py` — PyrightAdapter unit (mock subprocess、 env var assertion、 JSON parse error path、 timeout path) (RESEARCH §2)
- [ ] `tests/unit/test_callgraph_sort.py` — AST-02 `(caller, callee)` sort 動作の unit test (RESEARCH §4.2)

*Wave 0 = Phase 2 開始時に既存していない test fixture / harness。 Planner が Wave 1 着手前に整備する。*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| (none — Phase 2 はすべて自動検証可能) | — | — | — |

*All Phase 2 behaviors have automated verification (pytest + subprocess fixture). Manual smoke test なし。*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references in Per-Task Verification Map (6 W0 files)
- [ ] No watch-mode flags (`pytest --watch`、 `pytest-watcher` 等は使用しない)
- [ ] Feedback latency < 30s for quick gate (`pytest tests/parity -x -q`)
- [ ] `nyquist_compliant: true` set in frontmatter (after gsd-plan-checker pass)

**Approval:** pending (planner が PLAN.md 完成後に gsd-plan-checker による Nyquist gate を pass させ、 ここを `approved YYYY-MM-DD` に更新する)
