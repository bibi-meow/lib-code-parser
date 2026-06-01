---
phase: 3
slug: python-diagram-spec-extractors
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-01
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `03-RESEARCH.md` § Validation Architecture. The planner refines the
> Per-Task Verification Map once PLAN.md task IDs exist.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8 (+ pytest-cov) — already in `[project.optional-dependencies] dev` |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths = ["tests"]`) |
| **Quick run command** | `python -m pytest tests/unit -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~15 seconds (pure in-process AST, no I/O) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/unit -q`
- **After every plan wave:** Run `python -m pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

> Placeholder rows keyed by requirement; the planner replaces `{plan}`/`{task}` once
> PLAN.md task IDs are assigned. Threat Ref column is "—" (pure library, no runtime
> attack surface — see Security gate note in `03-RESEARCH.md`).

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-{p}-{t} | {p} | 0 | SP-2 verdict | — | N/A | unit | `python -m pytest tests/spikes/test_sp2_branch_fidelity.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 0 | SP-1 verdict | — | N/A | unit | `python -m pytest tests/spikes/test_sp1_control_flow_state.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | DIA-01 | — | N/A | unit | `python -m pytest tests/acceptance/test_dia01_class_diagram.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | DIA-07 | — | N/A | unit | `python -m pytest tests/unit/test_graph_schema.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | DIA-02 | — | N/A | unit | `python -m pytest tests/acceptance/test_dia02_sequence_diagram.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | DIA-03 | — | N/A | unit | `python -m pytest tests/acceptance/test_dia03_component_diagram.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | DIA-04 | — | N/A | unit | `python -m pytest tests/acceptance/test_dia04_package_diagram.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | DIA-05 | — | N/A | unit | `python -m pytest tests/acceptance/test_dia05_state_fsm.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | DIA-06 | — | N/A | unit | `python -m pytest tests/acceptance/test_dia06_return_substitution.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | SPC-01 | — | N/A | unit | `python -m pytest tests/acceptance/test_spc01_function_spec.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | SPC-02 | — | N/A | unit | `python -m pytest tests/acceptance/test_spc02_class_spec.py -q` | ❌ W0 | ⬜ pending |
| 3-{p}-{t} | {p} | 1 | SPC-04 | — | N/A | unit | `python -m pytest tests/acceptance/test_spc04_contract_markers.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/spikes/test_sp2_branch_fidelity.py` — SP-2 determinism probe fixtures (alt/loop/par)
- [ ] `tests/spikes/test_sp1_control_flow_state.py` — SP-1 determinism probe fixtures
- [ ] `tests/acceptance/` — golden-diagram + positive/negative FSM fixtures (incl. `class Color(Enum): RED,GREEN,BLUE` → 0 FSM negative case)
- [ ] `tests/fixtures/` — Python source samples per dialect (Google / NumPy / Sphinx docstrings; transitions / python-statemachine / native-Enum FSMs)
- [ ] `tests/conftest.py` — shared `ParserConfig` + CAV builder fixtures (extend existing)

*Framework already installed — no install task needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SP-1/SP-2 ship-vs-defer verdict text | SP-1, SP-2 | Verdict is a human-readable determinism judgement recorded in `.planning/spikes/*.md` | Reviewer confirms each spike file states ship OR v0.3.0-defer with deterministic-rule rationale |
| sibling-lib `node_type="package"` doc PR | DIA-04 | External repo PR, non-blocking (D-06) | Confirm lightweight comment PR drafted against `lib-diagram-parser`; not required to merge for phase pass |

*All in-library extraction behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
