---
phase: 1
slug: architecture-foundation-spec-correction
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (already installed) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ --cov=lib_code_parser` |
| **Estimated runtime** | ~5 seconds (v0.1.0 baseline) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ --cov=lib_code_parser`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

> Populated by planner during Step 8. Each task's `<automated>` block maps here.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

> Populated by planner. Likely includes:
> - `tests/test_models_contracts.py` — Pydantic v2 contract tests for CAV / EdgeKind / ParserConfig
> - `tests/test_paths.py` — single-source `get_module_name()` invariant
> - `tests/test_adapters_base.py` — subprocess hardening contract assertions
> - `tests/test_layout.py` — nested layout import parity (v0.1.0 caller compat)
> - `tests/conftest.py` — shared fixtures (carry over `EXAMPLE_SOURCE`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SP-3 libclang macOS arm64 smoke test (a)(b)(c)(d) | DET-05, SP-3 | macOS arm64 runner only on GitHub Actions; user environment cannot run | Trigger `.github/workflows/ci.yml` SP-3 matrix; record verdict in `.planning/spikes/SP-3-libclang-macos-arm64.md` |
| Spec doc full rewrite correctness (DOC-01) | DOC-01 | Semantic / content review (no `callgraph.py` or "ACL-2" references; v0.2.0 alignment) | Human review of `lib-code-parser.md` against `docs/00-decision-log.md` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
