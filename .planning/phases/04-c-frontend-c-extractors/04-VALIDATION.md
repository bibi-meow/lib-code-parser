---
phase: 4
slug: c-frontend-c-extractors
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-02
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 04-RESEARCH.md §Validation Architecture; per-task map filled by planner.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) |
| **Quick run command** | `pytest tests/unit -x -q` |
| **Full suite command** | `pytest --tb=short` |
| **Estimated runtime** | ~30 seconds (local; CI matrix separate) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit -x -q`
- **After every plan wave:** Run `pytest --tb=short` (full suite; existing Python tests must NOT regress — invariant #1/#2 guard)
- **Before `/gsd:verify-work`:** Full suite green + CI mandatory matrix green
- **Max feedback latency:** ~30 seconds (local)

---

## Per-Task Verification Map

> Planner fills exact Task IDs against plans. Requirement→test mapping below is the source of truth for coverage.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| LNG-03 | import-time guard raises clear RuntimeError on ABI/load/override failure | unit | `pytest tests/unit/frontends/test_cpp_guard.py -x` | ❌ W0 | ⬜ pending |
| DET-02 | `version("libclang")=="18.1.1"`; `set_library_file` override rejected | unit | `pytest tests/unit/frontends/test_cpp_guard.py::test_abi_pin -x` | ❌ W0 | ⬜ pending |
| LNG-04 | cpp `NormalizedArtifact` has identical Pydantic shape to Python (structural assertion) | parity | `pytest tests/parity/test_cpp_python_schema_parity.py -x` | ❌ W0 | ⬜ pending |
| LNG-05 | missing `#include` → diagnostics warning, never raises; cursor tree still built | unit | `pytest tests/unit/frontends/test_cpp_frontend.py::test_missing_include_warns -x` | ❌ W0 | ⬜ pending |
| LNG-04 (class) | inheritance(multiple) + composes/aggregates/associates from C++ fixture | acceptance | `pytest tests/acceptance/test_cpp_class_diagram.py -x` | ❌ W0 | ⬜ pending |
| SPC-03 | `\pre`/`\post`/`\invariant` → ContractInfo same schema as Python | acceptance | `pytest tests/acceptance/test_cpp_doxygen_contracts.py -x` | ❌ W0 | ⬜ pending |
| SPC-03 (TRC) | `Traces:` extraction identical for Python docstring + C++ Doxygen | parity | `pytest tests/parity/test_trc03_cpp_parity.py -x` | ❌ W0 | ⬜ pending |
| LNG-04 (determinism) | cpp output byte-identical across 3 runs (per-extractor; full-pipeline DET-01 is Phase 5) | unit | `pytest tests/unit/frontends/test_cpp_determinism.py -x` | ❌ W0 | ⬜ pending |
| LNG-01 / LNG-02 | pip install + import succeeds across mandatory CI matrix (Linux x86_64/aarch64 + Windows x86_64 × Py 3.11–3.14) | ci | `.github/workflows/ci.yml` matrix all-green | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — add `build_cpp_cav(source, path)` helper (mirror of Python CAV builder) so cpp extractor tests share one CAV builder
- [ ] `tests/fixtures/cpp/` — C++ fixture corpus (inheritance/multiple-inheritance, composition/aggregation/association members, namespace, includes, Doxygen contracts, `Traces:` tags, a "looks like FSM but isn't" negative fixture)
- [ ] `tests/unit/frontends/test_cpp_guard.py` — LNG-03/DET-02 guard tests
- [ ] `tests/parity/test_cpp_python_schema_parity.py` — LNG-04 structural parity
- [ ] `tests/unit/test_dispatch.py` — extend to assert nested-dict shape + per-language slot guard (existing file)
- [ ] Framework install: already present (`libclang==18.1.1` in dev extras) — no new install

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| macOS arm64 best-effort matrix observed | LNG-02 (best-effort) | macOS arm64 runner is `continue-on-error: true`; green is observed, not gated | Inspect CI run: best-effort job present and not blocking phase gate |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (plan-checker confirmed every task carries an automated verify)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (test infra in 04-02; guard/frontend tests created in the plans that consume them)
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

> `wave_0_complete` stays `false` until execution actually runs Wave 0 — the strategy is compliant, the work is not yet done.

**Approval:** approved 2026-06-03 (plan-checker VERIFICATION PASSED)
