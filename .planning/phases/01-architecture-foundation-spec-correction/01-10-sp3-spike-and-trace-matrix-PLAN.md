---
phase: 01-architecture-foundation-spec-correction
plan: 10
type: execute
wave: 3
depends_on: [01-09]
files_modified:
  - .github/workflows/ci.yml
  - .planning/spikes/SP-3-libclang-macos-arm64.md
  - docs/99-trace-matrix.md
autonomous: false
requirements: [TRC-01]
user_setup:
  - service: github-actions
    why: "SP-3 CI workflow must be kicked once on GitHub Actions macos-14 runner to record a provisional verdict per D-22"
    env_vars: []
    dashboard_config:
      - task: "Push the Phase 1 commit; observe the first sp3-libclang-spike job run on GitHub Actions"
        location: "GitHub Actions tab of the repository — sp3-libclang-spike job under the CI workflow"
must_haves:
  truths:
    - ".github/workflows/ci.yml has a new sp3-libclang-spike job on macos-14 runner with python 3.13/3.14 matrix and continue-on-error: true"
    - ".planning/spikes/SP-3-libclang-macos-arm64.md exists with the 4-step verdict template (a/b/c/d) per D-21 and a provisional verdict slot for first-run results"
    - "docs/99-trace-matrix.md includes a Phase 1 14-row matrix mapping each Phase 1 REQ-ID to its US support (per TRC-01)"
    - "Existing CI workflow (Linux Python 3.11) preserved and continues to gate PR merges; sp3-libclang-spike does NOT block merges (continue-on-error)"
  artifacts:
    - path: ".github/workflows/ci.yml"
      provides: "Existing test job + new sp3-libclang-spike best-effort job"
      contains: "sp3-libclang-spike|macos-14|continue-on-error: true"
    - path: ".planning/spikes/SP-3-libclang-macos-arm64.md"
      provides: "Spike record + verdict legend per D-21"
      contains: "ship-best-effort|defer to v0.3.0"
    - path: "docs/99-trace-matrix.md"
      provides: "Phase 1 14-REQ × US-IDs traceability matrix"
      contains: "ARC-01|TRC-01|US-01"
  key_links:
    - from: ".github/workflows/ci.yml sp3-libclang-spike job"
      to: ".planning/spikes/SP-3-libclang-macos-arm64.md"
      via: "CI run URL recorded in spike doc"
      pattern: "CI run URL"
    - from: "docs/99-trace-matrix.md"
      to: "REQUIREMENTS.md §Traceability"
      via: "Phase 1 14 REQ rows mirroring the source table"
      pattern: "ARC-01|TRC-01"
---

<objective>
Wave 3 sequential closer that fulfills the remaining ROADMAP §Phase 1 Success Criterion 5 deliverable (SP-3 spike) AND closes TRC-01 by populating `docs/99-trace-matrix.md` with the 14 Phase 1 requirement rows. Per D-22 (Phase 1 close 緩和条件), the spike completes by:
1. Setting up the CI workflow (`.github/workflows/ci.yml`) with the new `sp3-libclang-spike` job (macos-14 runner, python 3.13/3.14 matrix, continue-on-error: true)
2. Recording an initial verdict scaffold at `.planning/spikes/SP-3-libclang-macos-arm64.md` (the actual ✓/✗ cells get filled after the first CI run kicks; Phase 4 will re-evaluate)
3. Updating `docs/99-trace-matrix.md` with the 14 Phase 1 REQ-IDs → US mapping (TRC-01 final closure)

Per D-22 explicit rule: this plan does NOT block Phase 1 close on the spike RESULT — only on the workflow being set up + first run kicked + verdict slot present in the spike doc. Phase 4 entry point re-evaluates the verdict.

Per pre-resolved Open Question #5, this plan does NOT add a `pip install lib-diagram-parser` step to the CI workflow (Phase 1 graph_base.py is self-contained). Phase 3 will revisit CI dependency wiring when DIA-04 actually needs lib-diagram-parser at runtime.

Purpose: Closes the final ROADMAP §Phase 1 Success Criterion (SP-3 verdict recorded per D-22) and TRC-01 (traceability matrix populated). After this plan, Phase 1 has met all 5 success criteria and is ready to transition to Phase 2.

Output:
- Updated `.github/workflows/ci.yml` with the new sp3-libclang-spike job (existing test job preserved)
- New `.planning/spikes/SP-3-libclang-macos-arm64.md` per D-23 template
- Updated `docs/99-trace-matrix.md` with 14 Phase 1 REQ rows

NOTE: `autonomous: false` because Task 2 is a `checkpoint:human-verify` task — after Claude pushes the commit, the user (or a CI watcher) must observe the first sp3-libclang-spike job run on GitHub Actions and report the (a)(b)(c)(d) verdicts back so Claude can fill them in the spike doc. The CI run cannot be triggered or observed by Claude directly.
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/REQUIREMENTS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.github/workflows/ci.yml
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/docs/99-trace-matrix.md
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Add sp3-libclang-spike job to .github/workflows/ci.yml + create spike doc scaffold</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.github/workflows/ci.yml (current: single `test` job on ubuntu-latest python 3.11; preserve this job)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§libclang 18.1.1 macOS arm64 — exact YAML block for sp3-libclang-spike including the 4-step (a)(b)(c)(d) verification per D-21)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md (D-18 macos-14 runner only; D-19 lowest priority within Phase 1; D-20 4 verification steps; D-21 4-tier verdict; D-22 Phase 1 close 緩和条件; D-23 spike doc location)
  </read_first>
  <action>
    Step 1 — Update `.github/workflows/ci.yml` (append, do NOT remove the existing test job):
    - Preserve the existing top-level structure: `name: CI`, `on: [push, pull_request]`, `jobs:`.
    - Preserve the existing `test` job unchanged (ubuntu-latest, python 3.11, `pip install -e ".[dev]"`, `pytest --tb=short`, `ruff check .`, `ruff format --check .`).
    - Add a new sibling job `sp3-libclang-spike` per D-18 / D-20 / D-21 / D-22 with EXACTLY the YAML pinned in RESEARCH.md §libclang 18.1.1 macOS arm64 §CI matrix YAML:
      - `runs-on: macos-14` (Apple Silicon arm64 runner per D-18)
      - `continue-on-error: true` at the JOB LEVEL (D-22 — does not block PR merges)
      - `strategy: fail-fast: false; matrix: python-version: ["3.13", "3.14"]`
      - Steps:
        - `actions/checkout@v4`
        - `actions/setup-python@v5` with `python-version: ${{ matrix.python-version }}` and `allow-prereleases: true` (needed for 3.14 if still pre-release at run time)
        - `name: Install with libclang pinned`: `pip install -e ".[dev]"; pip show libclang`
        - `name: SP-3 (a) install succeeded — already passed if we got here`: `echo "SP-3 (a) PASS"`
        - `name: SP-3 (b) dylib load + Index.create()`: `python -c "from clang.cindex import Index; idx = Index.create(); print('Index OK', idx)"`
        - `name: SP-3 (c) library_path assertion`: a Python one-liner that imports `cindex.Config` and prints `Config.library_path`, with assertion that the path is non-empty (the literal `18.1.1` may or may not appear in the path string — keep the assertion permissive: `assert Config.library_path` truthy)
        - `name: SP-3 (d) minimal C++ parse`: a Python block that calls `Index.create()`, `idx.parse('test.cpp', args=['-x', 'c++', '-std=c++17'], unsaved_files=[('test.cpp', 'int main() { return 0; }')])`, walks `tu.cursor.get_children()` to a list, and prints the count
        - `name: Record verdict`: an `if: always()` step that appends a summary line to `$GITHUB_STEP_SUMMARY` with the Python version + macOS arm64 verdict status
    - Do NOT add an Ubuntu-aarch64 / Windows / macos-x86 matrix in Phase 1 — those belong to Phase 4 (LNG-01 mandatory matrix). Phase 1 ships ONLY the macos-14 best-effort spike.
    - Do NOT change the existing `test` job's runner OS or Python version — it stays ubuntu-latest + 3.11 in Phase 1; Phase 4 will expand it to the full mandatory matrix.

    Step 2 — Create `.planning/spikes/` directory (if not present) and write `.planning/spikes/SP-3-libclang-macos-arm64.md` per D-23 template:
    - YAML frontmatter: `spike_id: SP-3`, `phase: 1`, `target: libclang==18.1.1 on macOS arm64 (Python 3.13/3.14)`, `policy: D-22 緩和 — workflow setup + first run kick + provisional verdict`, `status: pending-first-run`.
    - H2 sections required:
      1. `## 目的` — Verify libclang 18.1.1 wheel on macOS arm64 + Python 3.13/3.14 feasibility (Phase 4 LNG-02 risk profile input).
      2. `## Test matrix` — A markdown table with columns: Python version | (a) install | (b) dylib load | (c) library_path | (d) C++ parse | Verdict. Two rows: 3.13 and 3.14. All cells initialized to `?` (pending first CI run).
      3. `## Verdict legend (D-21)` — Verbatim from CONTEXT.md D-21: all (a)(b)(c)(d) ✓ → ship-best-effort; (a)(b)(c) ✓ + (d) limited failure → ship-best-effort + known limitations; (a) ✓ (b) ✗ → defer to v0.3.0; (a) ✗ → defer to v0.3.0.
      4. `## CI run URL` — Placeholder: "TBD — first run URL recorded after Phase 1 commit lands on the default branch and the sp3-libclang-spike job runs". After Task 2 user verification step lands, update with actual URL.
      5. `## Re-evaluation` — "Phase 4 入口で再確認 (D-22). If verdict was provisional or defer, plan-phase for Phase 4 re-runs the spike with current macos-14 image and updates this table."
      6. `## Provisional verdict` — Placeholder: "TBD — to be filled after Task 2 records the first CI run results."
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; grep -c "sp3-libclang-spike:" .github/workflows/ci.yml &amp;&amp; grep -c "runs-on: macos-14" .github/workflows/ci.yml &amp;&amp; grep -c "continue-on-error: true" .github/workflows/ci.yml &amp;&amp; grep -c 'python-version: \["3.13", "3.14"\]' .github/workflows/ci.yml &amp;&amp; test -f .planning/spikes/SP-3-libclang-macos-arm64.md &amp;&amp; grep -c "Verdict legend" .planning/spikes/SP-3-libclang-macos-arm64.md</automated>
  </verify>
  <acceptance_criteria>
    - `.github/workflows/ci.yml` contains both the original `test` job (unchanged) AND the new `sp3-libclang-spike` job
    - `grep -c "sp3-libclang-spike:" .github/workflows/ci.yml` returns exactly 1
    - `grep -c "runs-on: macos-14" .github/workflows/ci.yml` returns exactly 1 (only the spike job — test job stays on ubuntu-latest)
    - `grep -c "continue-on-error: true" .github/workflows/ci.yml` returns >= 1 (at the spike job level)
    - `grep -c 'allow-prereleases: true' .github/workflows/ci.yml` returns >= 1 (needed for Python 3.14 prerelease)
    - `grep -c '"3.13"' .github/workflows/ci.yml` returns >= 1
    - `grep -c '"3.14"' .github/workflows/ci.yml` returns >= 1
    - `grep -c 'Index.create()' .github/workflows/ci.yml` returns >= 1 (SP-3 (b) step)
    - `grep -c 'Config.library_path' .github/workflows/ci.yml` returns >= 1 (SP-3 (c) step)
    - `grep -c 'idx.parse' .github/workflows/ci.yml` returns >= 1 (SP-3 (d) step)
    - `grep -c "name: test" .github/workflows/ci.yml` returns >= 1 (existing job preserved)
    - YAML is valid: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` exits 0 (PyYAML may need to be available — if not, this gate is skipped and replaced with a structural grep that asserts `^jobs:$` exists exactly once)
    - File `.planning/spikes/SP-3-libclang-macos-arm64.md` exists
    - `grep -c "spike_id: SP-3" .planning/spikes/SP-3-libclang-macos-arm64.md` returns >= 1
    - `grep -c "## Test matrix" .planning/spikes/SP-3-libclang-macos-arm64.md` returns exactly 1
    - `grep -c "## Verdict legend" .planning/spikes/SP-3-libclang-macos-arm64.md` returns exactly 1
    - `grep -c "ship-best-effort" .planning/spikes/SP-3-libclang-macos-arm64.md` returns >= 2 (in verdict legend; "All (a)(b)(c)(d) ✓ → ship-best-effort" + "(a)(b)(c) ✓ + (d) limited failure → ship-best-effort + known limitations")
    - `grep -c "defer to v0.3.0" .planning/spikes/SP-3-libclang-macos-arm64.md` returns >= 2
    - `grep -c "D-22" .planning/spikes/SP-3-libclang-macos-arm64.md` returns >= 1
  </acceptance_criteria>
  <done>CI workflow updated with macos-14 SP-3 best-effort spike job; spike doc scaffold created with verdict legend and pending-first-run status placeholders.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Update docs/99-trace-matrix.md with Phase 1 14-REQ traceability matrix</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/REQUIREMENTS.md §Traceability table (the 42-row authoritative source — Phase 1 rows: ARC-01..05, SCH-01..03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01 with their US-IDs)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/docs/99-trace-matrix.md (current state — verify whether it is a template stub or already-populated; per pre-resolved Open Question #3 the rest of docs/00-07/99 are template skeletons and Phase 1 only updates docs/99 minimally for TRC-01)
  </read_first>
  <action>
    Read current `docs/99-trace-matrix.md`. If it is an empty/template skeleton, add the following content. If it already has structure, append the Phase 1 section without removing existing content.

    Required content to ADD (preserve any existing content above/below):

    `## Phase 1 — Architecture Foundation + Spec Correction (TRC-01)` H2 section followed by a markdown table with 14 rows. Columns: `Requirement | US support | Phase 1 closure plan`. Rows in this exact order:

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

    Below the table, add a paragraph noting:
    - "Phase 2-5 rows will be appended at their respective phase close. Source of truth: `.planning/REQUIREMENTS.md` §Traceability (42 rows mapped to 5 phases as of 2026-05-24)."
    - "TRC-02 / TRC-03 closure is a Phase 2 deliverable (per-module REQ-ID docstring declaration + Traces regex)."

    Style notes: pure-Markdown table syntax. Do NOT modify any other docs/00-07 SDD-chain files (those are out of scope per pre-resolved Open Question #3). Do NOT add Phase 2-5 rows pre-emptively.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; grep -c "^## Phase 1\|^## Phase 1 —" docs/99-trace-matrix.md &amp;&amp; for id in ARC-01 ARC-02 ARC-03 ARC-04 ARC-05 SCH-01 SCH-02 SCH-03 DET-04 DET-05 DOC-01 DOC-03 DOC-04 TRC-01; do grep -q "| $id |" docs/99-trace-matrix.md || echo "MISSING_ROW: $id"; done | grep -c MISSING_ROW</automated>
  </verify>
  <acceptance_criteria>
    - File `docs/99-trace-matrix.md` exists
    - `grep -c "^## Phase 1" docs/99-trace-matrix.md` returns >= 1 (the new H2 section present)
    - For each of the 14 Phase 1 REQ-IDs (ARC-01, ARC-02, ARC-03, ARC-04, ARC-05, SCH-01, SCH-02, SCH-03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01): the table contains a row starting with `| <REQ-ID> |` — verifiable by the loop in the verify command (the MISSING_ROW count must be 0)
    - `grep -c "US-01" docs/99-trace-matrix.md` returns >= 12 (most Phase 1 REQs map to US-01)
    - `grep -c "US-22" docs/99-trace-matrix.md` returns >= 12
    - `grep -c "US-25" docs/99-trace-matrix.md` returns >= 11
    - `grep -c "US-32" docs/99-trace-matrix.md` returns >= 11
    - `grep -c "Plan 01\|Plan 02\|Plan 03\|Plan 04\|Plan 05\|Plan 06\|Plan 07\|Plan 08\|Plan 09" docs/99-trace-matrix.md` returns >= 14 (each row references at least one closure plan)
    - File size > 1500 bytes (substantive content, not a stub)
  </acceptance_criteria>
  <done>docs/99-trace-matrix.md has a Phase 1 H2 section with all 14 REQ rows + US mapping + closure-plan references; TRC-01 closed.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 3: Verify SP-3 spike first CI run (kick + observe + record provisional verdict)</name>
  <what-built>
    Plan 10 Task 1 added the sp3-libclang-spike job to .github/workflows/ci.yml. After all Phase 1 plans (01-10) are committed and pushed, the GitHub Actions workflow on the default branch will run BOTH the existing `test` job (ubuntu-latest + Python 3.11) AND the new `sp3-libclang-spike` job (macos-14 + Python 3.13/3.14, continue-on-error: true). The spike job runs the 4 verification steps SP-3 (a)(b)(c)(d) per D-21. The user can observe the first-run outcomes on the GitHub Actions tab.
  </what-built>
  <how-to-verify>
    1. After Claude pushes the Phase 1 commit (or the user pushes the bundled Phase 1 PR), navigate to the repository's "Actions" tab on GitHub: `https://github.com/<owner>/lib-code-parser/actions` (the actual owner is bibi-meow per the LICENSE; check the actual URL of the repository).
    2. Look for the most recent CI workflow run. There should be TWO jobs visible: `test` (ubuntu-latest) and `sp3-libclang-spike (Python 3.13, macos-14)` and `sp3-libclang-spike (Python 3.14, macos-14)`. The `test` job MUST pass green (it gates merges); the sp3-libclang-spike job is `continue-on-error: true` so it can be yellow/red without blocking.
    3. For each of the two sp3-libclang-spike matrix runs (3.13 and 3.14), open the run and read the step results:
       - Step "SP-3 (a) install succeeded — already passed if we got here": PASS if the previous "Install with libclang pinned" step succeeded; otherwise (a) is ✗.
       - Step "SP-3 (b) dylib load + Index.create()": PASS if the log shows "Index OK"; FAIL if Python traceback (ImportError, OSError, libclang dylib load failure).
       - Step "SP-3 (c) library_path assertion": PASS if `Config.library_path` printed and assertion passed; otherwise note the failure mode.
       - Step "SP-3 (d) minimal C++ parse": PASS if `parsed N top-level cursors` printed; FAIL if traceback.
    4. Copy the CI run URL (e.g., `https://github.com/bibi-meow/lib-code-parser/actions/runs/NNNNNN`).
    5. Report back to Claude:
       - For Python 3.13 row: a/b/c/d ✓ or ✗ (4 results)
       - For Python 3.14 row: a/b/c/d ✓ or ✗ (4 results)
       - The CI run URL
    6. Claude will then update `.planning/spikes/SP-3-libclang-macos-arm64.md`: fill the Test matrix cells with the actual ✓/✗ results, fill the "CI run URL" section with the actual URL, and write the "Provisional verdict" section by applying D-21 4-tier judgment:
       - All (a)(b)(c)(d) ✓ → ship-best-effort
       - (a)(b)(c) ✓ + (d) limited failure → ship-best-effort + known limitations
       - (a) ✓ (b) ✗ → defer to v0.3.0
       - (a) ✗ → defer to v0.3.0
    7. Per D-22, this Phase 1 close condition is satisfied REGARDLESS of the verdict — even "defer to v0.3.0" closes Phase 1; Phase 4 entry point re-evaluates.

    If the user does not have access to the GitHub Actions tab or the CI cannot be triggered (e.g., not yet pushed to GitHub), the user may report "spike not yet kicked" — Claude will then complete the Phase 1 SUMMARY with the spike doc in `pending-first-run` status, document the deferred verdict-fill as a Phase 4-entry-point checklist item, and Phase 1 still closes per D-22 緩和 since "workflow setup complete" is the gating condition.
  </how-to-verify>
  <resume-signal>
    Reply with one of:
    - "verdict: 3.13 ✓✓✓✓ / 3.14 ✓✓✓✓ / URL: <run-url>" (or other a/b/c/d combination)
    - "spike not yet kicked — close Phase 1 with pending-first-run status per D-22"
    - "approved — pending-first-run is acceptable for Phase 1 close per D-22"
  </resume-signal>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Record provisional verdict in spike doc (post-user-feedback)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/spikes/SP-3-libclang-macos-arm64.md (Task 1 output — scaffold with TBD placeholders to fill)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md (D-21 verdict legend — apply the matching tier based on user-reported a/b/c/d results)
  </read_first>
  <action>
    Based on the user's response in Task 3:

    Branch A — User reported a/b/c/d results for one or both Python versions:
    1. Update the `## Test matrix` table in `.planning/spikes/SP-3-libclang-macos-arm64.md`: replace `?` cells with the actual ✓ or ✗ values per Python row.
    2. Update the `## CI run URL` section: replace "TBD" with the actual CI run URL.
    3. Update the `## Provisional verdict` section: apply D-21 4-tier judgment:
       - All (a)(b)(c)(d) ✓ → write "**Provisional verdict: ship-best-effort** (Phase 4 will mark macOS arm64 as best-effort CI per LNG-02)"
       - (a)(b)(c) ✓ + (d) limited failure → write "**Provisional verdict: ship-best-effort + known limitations** (Phase 4 will document the parse failure mode in README)"
       - (a) ✓ (b) ✗ → write "**Provisional verdict: defer to v0.3.0 (dylib load failure)** (Phase 4 will mark macOS arm64 as deferred; LNG-02 deferred to v0.3.0)"
       - (a) ✗ → write "**Provisional verdict: defer to v0.3.0 (wheel install failure)** (Phase 4 will defer LNG-02 to v0.3.0)"
    4. Update YAML frontmatter `status:` from `pending-first-run` to one of: `verdict-recorded-ship-best-effort` / `verdict-recorded-with-limitations` / `verdict-recorded-defer-v0.3.0`.

    Branch B — User reported "spike not yet kicked" or "pending-first-run acceptable":
    1. Leave the matrix `?` cells unchanged.
    2. Leave the CI run URL "TBD".
    3. Update `## Provisional verdict` section: write "**Provisional verdict: pending — first run not yet kicked. Per D-22 緩和条件, Phase 1 closes with workflow setup complete; Phase 4 entry point will re-evaluate the verdict. CHECKLIST FOR PHASE 4 PLAN-PHASE: read latest CI run from `sp3-libclang-spike` job, apply D-21 4-tier judgment, update this doc's verdict section."
    4. Leave YAML frontmatter `status: pending-first-run` unchanged.

    Either branch — Append a Markdown note at the bottom of the file: "Last updated by Plan 10 Task 4 on 2026-05-25."
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; grep -c "Provisional verdict" .planning/spikes/SP-3-libclang-macos-arm64.md &amp;&amp; grep -E "Provisional verdict:" .planning/spikes/SP-3-libclang-macos-arm64.md</automated>
  </verify>
  <acceptance_criteria>
    - `.planning/spikes/SP-3-libclang-macos-arm64.md` `## Provisional verdict` section contains a non-placeholder statement (no longer "TBD" — either an actual verdict per D-21 OR a "pending — first run not yet kicked" with the Phase 4 checklist note)
    - YAML frontmatter `status:` is one of the 4 valid values: `pending-first-run` (Branch B) / `verdict-recorded-ship-best-effort` / `verdict-recorded-with-limitations` / `verdict-recorded-defer-v0.3.0` (Branch A subtypes)
    - File contains the date stamp "Last updated by Plan 10 Task 4 on 2026-05-25"
    - If Branch A: at least one row in the `## Test matrix` table has a ✓ or ✗ cell (not all `?`)
    - If Branch B: matrix may still be all `?` and CI run URL may still be "TBD" — this is acceptable per D-22
  </acceptance_criteria>
  <done>Spike doc finalized with verdict (or pending-first-run + Phase 4 checklist); Phase 1 SP-3 deliverable closed per D-22 緩和条件.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Local repo → GitHub Actions CI | YAML workflow file controls execution on GitHub-hosted macos-14 runner; invalid YAML breaks the merge-gating `test` job too |
| CI runner → libclang wheel | GitHub Actions runner downloads libclang 18.1.1 wheel from PyPI; supply-chain integrity depends on PyPI hash + slopcheck audit (already cleared in RESEARCH.md §Package Legitimacy Audit) |
| User → Claude reporting | Task 3 checkpoint relies on user accurately reporting (a)(b)(c)(d) verdicts; misreport could lead to a wrong verdict in the spike doc |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-10-01 | Tampering | Invalid YAML breaks existing `test` job | mitigate | Task 1 acceptance includes valid-YAML structural check; the existing `test` job block is preserved verbatim per the read_first instruction |
| T-10-02 | Denial of Service | sp3-libclang-spike runs unboundedly long on macos-14 | mitigate | The spike steps are individually short (one `pip install` + 4 short `python -c` commands); GitHub Actions has a global 6h timeout on jobs; `continue-on-error: true` prevents indefinite blocking of merges |
| T-10-03 | Supply chain | libclang 18.1.1 wheel poisoned in PyPI between Phase 1 and Phase 4 | accept | RESEARCH.md §Package Legitimacy Audit confirms slopcheck [OK]; SHA256 pinning is a Phase 5 hardening deliverable (not Phase 1); current pin `libclang==18.1.1` + PyPI integrity is the working baseline |
| T-10-04 | Repudiation | User misreports a/b/c/d verdict in Task 3 | mitigate | Task 3 instructs the user to copy the CI run URL — the URL is the verifiable record; Claude records the URL in the spike doc; future re-reading can reconcile the doc against the run logs |
| T-10-SC | Tampering | npm/pip installs in CI workflow (sp3 spike step "pip install -e \".[dev]\"") | mitigate | dev extras include libclang==18.1.1 + pyright[nodejs]==1.1.409 + nodejs-wheel-binaries — all cleared in RESEARCH.md §Package Legitimacy Audit (slopcheck [OK]); pyproject.toml pins exact versions; no `[ASSUMED]` or `[SUS]` packages |
</threat_model>

<verification>
- `.github/workflows/ci.yml` parses as valid YAML AND contains both the existing `test` job (preserved verbatim) AND the new sp3-libclang-spike job (macos-14, python 3.13/3.14, continue-on-error: true)
- `.planning/spikes/SP-3-libclang-macos-arm64.md` exists with frontmatter, test matrix, verdict legend, and provisional-verdict section
- `docs/99-trace-matrix.md` contains the Phase 1 14-REQ rows with US-IDs and closure-plan references
- All 14 Phase 1 REQ-IDs appear as table rows (loop test confirms 0 MISSING_ROW output)
- Spike doc provisional-verdict section is non-placeholder (after Task 4)
</verification>

<success_criteria>
- ROADMAP §Phase 1 Success Criterion 5 finalized: SP-3 libclang feasibility spike result is recorded (verdict: ship / ship-best-effort / defer) under `.planning/spikes/SP-3-libclang-macos-arm64.md` per D-22 緩和条件 (workflow setup complete + first run kicked + provisional verdict recorded) ✓
- TRC-01 finalized: every Phase 1 REQ-ID maps to at least one US-ID via the docs/99-trace-matrix.md table ✓
- Phase 1 close gate satisfied: all 5 ROADMAP success criteria met (SC-1 by Plans 03+05+09; SC-2 by Plan 03; SC-3 by Plans 06+09; SC-4 by Plan 07; SC-5 by Plans 01+02+10)
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-10-SUMMARY.md` when done with:
- YAML validity check output for ci.yml
- Confirmation that the existing test job is preserved
- Spike doc frontmatter status
- Phase 1 14-REQ MISSING_ROW loop output (should be 0)
- Summary of user-reported verdict (or pending-first-run note) for the spike
</output>
