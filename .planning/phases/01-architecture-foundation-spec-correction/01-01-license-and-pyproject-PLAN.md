---
phase: 01-architecture-foundation-spec-correction
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - LICENSE
  - pyproject.toml
  - frozen/2026-05-24-v0.1.0-spec/LICENSE
autonomous: true
requirements: [DOC-04, DOC-03]
must_haves:
  truths:
    - "Repository ships Apache-2.0 LICENSE with patent grant clause"
    - "pyproject.toml declares license via PEP 639 SPDX string and license-files glob"
    - "Old MIT LICENSE preserved under frozen/ for historical traceability"
    - "Caller can pip install with setuptools>=77.0.3 without deprecation warning"
  artifacts:
    - path: "LICENSE"
      provides: "Apache-2.0 full text including patent grant clause (Section 3)"
      contains: "Apache License|Version 2.0|patent"
    - path: "pyproject.toml"
      provides: "PEP 639 SPDX license declaration + setuptools>=77.0.3 build requirement"
      contains: 'license = "Apache-2.0"'
    - path: "frozen/2026-05-24-v0.1.0-spec/LICENSE"
      provides: "Pre-existing MIT LICENSE backup for v0.1.0 traceability"
      contains: "MIT License"
  key_links:
    - from: "pyproject.toml"
      to: "LICENSE"
      via: 'license-files glob ["LICENSE"]'
      pattern: 'license-files\s*=\s*\["LICENSE"\]'
---

<objective>
Replace the v0.1.0 MIT LICENSE with Apache-2.0 (per PROJECT.md Key Decisions and D-23 SP-3 license posture) and declare the license in pyproject.toml using PEP 639 SPDX format. Preserve the MIT version under `frozen/2026-05-24-v0.1.0-spec/` per backup-before-major-rewrite project rule.

Purpose: Satisfies DOC-04 (Apache-2.0 declared + LICENSE shipped + patent grant clause) and unblocks DOC-03 disclosure language for the spec doc rewrite (Plan 02). PyPI confirmed: `lib-code-parser` is unpublished (orchestrator pre-resolved Open Question #2), so the MIT→Apache-2.0 switch carries no retroactive license obligation.

Output:
- New `LICENSE` containing the full Apache License Version 2.0 text including Section 3 (patent grant)
- Updated `pyproject.toml` with `license = "Apache-2.0"`, `license-files = ["LICENSE"]`, `version = "0.2.0"`, `requires = ["setuptools>=77.0.3", "wheel"]`, declared `lib-diagram-parser>=0.1.0` dependency and dev-extras for `pyright[nodejs]==1.1.409` and `libclang==18.1.1`
- Backup at `frozen/2026-05-24-v0.1.0-spec/LICENSE` (MIT, byte-identical to v0.1.0)
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/PROJECT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/ROADMAP.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/STATE.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md

<!-- Authoritative Apache-2.0 source: https://www.apache.org/licenses/LICENSE-2.0.txt -->
<!-- PEP 639 reference: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license -->
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Backup v0.1.0 MIT LICENSE to frozen/</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/LICENSE (current MIT, verify before move)
    - C:/work/agent_company/spec-reviewer-libs/.claude/rules/backup-before-major-rewrite.md (project rule: backup before destructive rewrite of >100 char files)
  </read_first>
  <action>
    Create directory `frozen/2026-05-24-v0.1.0-spec/` at project root. Copy the current `LICENSE` file (MIT, ~1KB, header line "MIT License") to `frozen/2026-05-24-v0.1.0-spec/LICENSE` via the Bash `cp` command (do NOT use Move-Item / mv — keep original in place; Task 2 overwrites it). Verify the copy is byte-identical to the source. Do NOT touch the source `LICENSE` in this task. This task satisfies the backup-before-major-rewrite project rule (D-02 parallel for LICENSE files).
  </action>
  <verify>
    <automated>test -f "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/frozen/2026-05-24-v0.1.0-spec/LICENSE" &amp;&amp; diff -q "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/LICENSE" "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/frozen/2026-05-24-v0.1.0-spec/LICENSE"</automated>
  </verify>
  <acceptance_criteria>
    - File `frozen/2026-05-24-v0.1.0-spec/LICENSE` exists
    - `diff -q LICENSE frozen/2026-05-24-v0.1.0-spec/LICENSE` exits 0 (byte-identical)
    - First line of the backup is exactly `MIT License` (the v0.1.0 starter)
    - Source `LICENSE` at project root is untouched in this task (still MIT)
  </acceptance_criteria>
  <done>MIT backup exists under `frozen/2026-05-24-v0.1.0-spec/LICENSE`, byte-identical to source.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Replace LICENSE with Apache-2.0 full text</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/LICENSE (current MIT — must overwrite)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/frozen/2026-05-24-v0.1.0-spec/LICENSE (verify Task 1 produced backup before overwriting source)
  </read_first>
  <action>
    Overwrite `LICENSE` at the project root with the full official Apache License Version 2.0 text. The text MUST contain (a) the title `Apache License`, (b) `Version 2.0, January 2004`, (c) the URL `http://www.apache.org/licenses/`, (d) the complete `TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION` block, (e) Section 3 `Grant of Patent License`, (f) the `APPENDIX: How to apply the Apache License to your work` block, (g) the standard boilerplate at end with copyright placeholder filled as `Copyright 2026 bibi-meow (lib-code-parser contributors)`. The license text is the verbatim canonical version from https://www.apache.org/licenses/LICENSE-2.0.txt; do NOT paraphrase or summarize. Do NOT add LLVM exception (lib-code-parser itself is plain Apache-2.0; the LLVM exception applies to the bundled libclang dependency only and is documented separately in the spec doc by Plan 02).
  </action>
  <verify>
    <automated>grep -c "Apache License" "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/LICENSE" &amp;&amp; grep -c "Grant of Patent License" "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/LICENSE" &amp;&amp; grep -c "Version 2.0, January 2004" "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/LICENSE"</automated>
  </verify>
  <acceptance_criteria>
    - `LICENSE` first non-blank line contains `Apache License`
    - `grep -c "Version 2.0, January 2004" LICENSE` returns >= 1
    - `grep -c "Grant of Patent License" LICENSE` returns >= 1 (Section 3 present)
    - `grep -c "APPENDIX: How to apply the Apache License" LICENSE` returns >= 1
    - `grep -c "Copyright 2026 bibi-meow" LICENSE` returns >= 1
    - `grep -c "MIT License" LICENSE` returns 0 (old MIT header removed from source)
    - `grep -ci "LLVM-exception\|LLVM exception" LICENSE` returns 0 (LLVM exception NOT added to lib's own license)
  </acceptance_criteria>
  <done>`LICENSE` at project root contains the full Apache-2.0 text with patent grant clause; MIT trace removed from source.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Update pyproject.toml with PEP 639 SPDX license + dependencies + version bump</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/pyproject.toml (current state: setuptools>=68, version 0.1.0, no license declaration)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Apache-2.0 pyproject.toml — exact final form pinned here)
  </read_first>
  <action>
    Rewrite `pyproject.toml` to satisfy PEP 639 SPDX form and Phase 1 dependency declarations. Concrete changes:
    1. `[build-system]` `requires` MUST be `["setuptools>=77.0.3", "wheel"]` (was `>=68`). This is non-negotiable per RESEARCH.md: setuptools <77 emits SetuptoolsDeprecationWarning on SPDX strings.
    2. `[project]` MUST include: `name = "lib-code-parser"` (DO NOT change distribution name — orchestrator pre-resolved Open Question #1: "lib-code-parser のまま"), `version = "0.2.0"` (bump from 0.1.0), `requires-python = ">=3.11"` (unchanged), `license = "Apache-2.0"` (PEP 639 SPDX string, NOT the legacy `license = {text = "..."}` table form), `license-files = ["LICENSE"]`.
    3. `[project]` `description` MUST be updated to: `"Deterministic Python/C++ source parser for AST primitives, diagrams, and specs (lib-diagram-parser compatible schema)"`.
    4. `[project]` `dependencies` MUST include both `"pydantic>=2.13.0,<3.0"` (was `>=2.0`; bumped to match CLAUDE.md Tech stack) and `"lib-diagram-parser>=0.1.0"` (NEW, per SCH-01 and D-15 — declared in Phase 1 even though direct use is Phase 3+; pre-resolved Open Question #5 confirms Phase 1 keeps Phase 1 self-contained graph_base which does NOT import lib-diagram-parser, but the declaration here documents the schema-compat boundary).
    5. `[project.optional-dependencies]` `dev` MUST include `"pytest>=8"`, `"pytest-cov"`, `"ruff"`, `"pyright"` (existing dev type checker) AND new entries `"pyright[nodejs]==1.1.409"` (DET-03, declared for Phase 2 PyrightAdapter), `"libclang==18.1.1"` (DET-02 strict pin + SP-3 spike).
    6. Preserve existing sections unchanged: `[tool.setuptools.packages.find]`, `[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.ruff.lint]`.
    7. Do NOT use the deprecated `license = {text = "..."}` table form. Do NOT add `classifiers = ["License :: ..."]` (PEP 639 makes them redundant when SPDX `license` is set).
  </action>
  <verify>
    <automated>grep -c '^license = "Apache-2.0"$' "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/pyproject.toml" &amp;&amp; grep -c '^license-files = \["LICENSE"\]$' "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/pyproject.toml" &amp;&amp; grep -c 'setuptools>=77.0.3' "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/pyproject.toml" &amp;&amp; grep -c '^version = "0.2.0"$' "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/pyproject.toml"</automated>
  </verify>
  <acceptance_criteria>
    - `grep '^license = "Apache-2.0"$' pyproject.toml` returns exactly one match (SPDX string form, NOT table form)
    - `grep '^license-files = \["LICENSE"\]$' pyproject.toml` returns exactly one match
    - `grep 'setuptools>=77.0.3' pyproject.toml` returns >= 1 match
    - `grep '^version = "0.2.0"$' pyproject.toml` returns exactly one match
    - `grep '^name = "lib-code-parser"$' pyproject.toml` returns exactly one match (distribution name preserved per pre-resolved decision)
    - `grep 'pydantic>=2.13.0' pyproject.toml` returns >= 1 match
    - `grep 'lib-diagram-parser>=0.1.0' pyproject.toml` returns >= 1 match
    - `grep 'pyright\[nodejs\]==1.1.409' pyproject.toml` returns >= 1 match
    - `grep 'libclang==18.1.1' pyproject.toml` returns >= 1 match
    - `grep 'license = {text' pyproject.toml` returns 0 matches (legacy table form absent)
    - `cd C:/work/agent_company/spec-reviewer-libs/lib-code-parser/ &amp;&amp; python -c "import tomllib; tomllib.loads(open('pyproject.toml','rb').read().decode())"` exits 0 (parses as valid TOML)
  </acceptance_criteria>
  <done>`pyproject.toml` declares Apache-2.0 via SPDX string, bumps to version 0.2.0, points to LICENSE, requires setuptools>=77.0.3, and adds Phase 1 dependency declarations; valid TOML.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| build-time → distribution | pyproject.toml is consumed by `pip` / `build` / PyPI; malformed declarations propagate to all downstream consumers |
| repo → legal review | LICENSE file is the authoritative license artifact; any drift between LICENSE text and pyproject.toml SPDX value is a legal compliance failure |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-01 | Repudiation | LICENSE / pyproject.toml mismatch | mitigate | Acceptance criteria assert both SPDX string AND LICENSE file presence; cross-check via grep gates in Task 3 |
| T-01-02 | Tampering | Legacy MIT trace remaining in source | mitigate | Task 2 acceptance: `grep -c "MIT License" LICENSE` must return 0 |
| T-01-03 | Information Disclosure | Loss of v0.1.0 MIT license historical record | mitigate | Task 1 mandates backup under `frozen/2026-05-24-v0.1.0-spec/LICENSE` before Task 2 overwrites |
| T-01-SC | Tampering | npm/pip installs (none in this plan) | accept | No `pip install` operations performed in this plan; pyproject.toml only declares deps without installing them. Plan 09 parity test will trigger `pip install -e .[dev]` — package legitimacy already audited in RESEARCH.md §Package Legitimacy Audit (all [OK]) |
</threat_model>

<verification>
- LICENSE file contains Apache-2.0 full text with patent grant clause (Section 3)
- pyproject.toml declares Apache-2.0 via SPDX, points to LICENSE, version 0.2.0, setuptools>=77.0.3
- MIT backup preserved at frozen/2026-05-24-v0.1.0-spec/LICENSE
- pyproject.toml parses as valid TOML
</verification>

<success_criteria>
- ROADMAP §Phase 1 Success Criterion 5 partial fulfillment: `pyproject.toml declares license = "Apache-2.0"` ✓ + `LICENSE file shipped` ✓
- DOC-04 satisfied: Apache-2.0 SPDX declaration + LICENSE shipped + patent grant clause present
- Foundation laid for DOC-03 (no GPL bundled) prose in Plan 02 spec rewrite
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-01-SUMMARY.md` when done, listing files touched and `grep` verification output for each acceptance criterion.
</output>
