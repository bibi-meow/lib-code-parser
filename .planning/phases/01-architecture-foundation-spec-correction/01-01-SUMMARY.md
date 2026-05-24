---
phase: 01-architecture-foundation-spec-correction
plan: 01
subsystem: infra
tags: [license, apache-2.0, pep-639, spdx, pyproject, packaging, doc-03, doc-04]

# Dependency graph
requires: []
provides:
  - Apache-2.0 LICENSE shipped at project root with patent grant clause (Section 3)
  - pyproject.toml PEP 639 SPDX license declaration + setuptools>=77.0.3
  - Phase 1 dependency declarations (pydantic>=2.13.0, lib-diagram-parser>=0.1.0, pyright[nodejs]==1.1.409, libclang==18.1.1)
  - version bump 0.1.0 -> 0.2.0
  - frozen/2026-05-24-v0.1.0-spec/LICENSE MIT backup for traceability
  - README.md License section documenting Apache-2.0 + "No GPL bundled" + bundled dep license trio
affects:
  - 01-02 (spec doc rewrite — references the corrected call-graph-internal disclosure in README License section)
  - 01-09 (pip install -e .[dev] parity test depends on these dep declarations)
  - all downstream Phase 2-5 plans (legal compliance + dependency surface fixed here)

# Tech tracking
tech-stack:
  added:
    - Apache-2.0 license (replacing MIT)
    - PEP 639 SPDX license declaration in pyproject.toml
    - setuptools>=77.0.3 (PEP 639 support)
  patterns:
    - "License-declaration trio: LICENSE file + pyproject.toml SPDX + README.md narrative kept in sync at plan boundaries"
    - "frozen/YYYY-MM-DD-vX.Y.Z-spec/ backup before destructive rewrite (backup-before-major-rewrite project rule)"

key-files:
  created:
    - frozen/2026-05-24-v0.1.0-spec/LICENSE (MIT backup, byte-identical to v0.1.0)
  modified:
    - LICENSE (MIT -> Apache-2.0 full text with Section 3 patent grant)
    - pyproject.toml (SPDX license, version 0.2.0, setuptools>=77.0.3, Phase 1 deps)
    - README.md (## License section rewritten for DOC-03 / ROADMAP SC-5)

key-decisions:
  - "Apache-2.0 (not MIT) chosen for the v0.2.0 line per PROJECT.md Key Decisions and D-23 SP-3 license posture — patent grant clause required for downstream pipeline consumers"
  - "PEP 639 SPDX string form `license = \"Apache-2.0\"` used (NOT legacy `license = {text=...}` table form); classifiers omitted as redundant"
  - "setuptools>=77.0.3 build requirement is non-negotiable — earlier versions emit SetuptoolsDeprecationWarning on SPDX strings"
  - "Distribution name kept as `lib-code-parser` per orchestrator-resolved Open Question #1"
  - "`lib-diagram-parser>=0.1.0` declared as dependency in Phase 1 even though direct use is Phase 3+ (documents schema-compat boundary per SCH-01 / D-15)"
  - "LLVM exception applies to bundled `libclang` only — lib-code-parser itself is plain Apache-2.0 (LLVM exception NOT added to LICENSE)"
  - "README explicitly states call graph extractor is internal — NOT `pyan3`, NOT `ACL-2` (the v0.1.0 spec doc misreferences being corrected by Plan 02)"

patterns-established:
  - "License trio sync: any plan touching LICENSE must verify pyproject.toml SPDX + README.md narrative agree"
  - "Backup-before-major-rewrite: pre-existing artifacts moved to frozen/YYYY-MM-DD-vX.Y.Z-spec/ before destructive replace"

requirements-completed: [DOC-04, DOC-03]

# Metrics
duration: ~12 min
completed: 2026-05-24
---

# Phase 1 Plan 01: License and pyproject.toml Summary

**Apache-2.0 LICENSE replaces MIT with patent grant clause, pyproject.toml declares license via PEP 639 SPDX form with setuptools>=77.0.3 and Phase 1 dependency surface, README License section documents "No GPL bundled" + bundled dep trio (call graph internal / pyright MIT / libclang Apache-2.0 with LLVM exception).**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-05-24T22:59Z
- **Completed:** 2026-05-24T23:12Z
- **Tasks:** 4 / 4
- **Files modified:** 3 (LICENSE, pyproject.toml, README.md)
- **Files created:** 1 (frozen/2026-05-24-v0.1.0-spec/LICENSE)

## Accomplishments
- MIT v0.1.0 LICENSE preserved under `frozen/2026-05-24-v0.1.0-spec/LICENSE` (byte-identical backup, traceability for the v0.1.0 release line)
- LICENSE at project root replaced with canonical Apache License Version 2.0 full text, including Section 3 Grant of Patent License and APPENDIX boilerplate (Copyright 2026 bibi-meow)
- pyproject.toml rewritten with PEP 639 SPDX `license = "Apache-2.0"` + `license-files = ["LICENSE"]`, build requirement bumped to `setuptools>=77.0.3` (avoids SetuptoolsDeprecationWarning), version bumped to `0.2.0`, dependencies declared (`pydantic>=2.13.0,<3.0`, `lib-diagram-parser>=0.1.0`), dev extras declared (`pyright[nodejs]==1.1.409`, `libclang==18.1.1`)
- README.md `## License` section expanded from single-line "MIT" to a section satisfying both ROADMAP SC-5 (verbatim "No GPL bundled" phrase) and REQUIREMENTS DOC-03 (bundled dependency license trio: call graph internal, pyright MIT, libclang Apache-2.0 WITH LLVM exception)
- pyproject.toml parses as valid TOML via stdlib `tomllib`

## Task Commits

Each task was committed atomically:

1. **Task 1: Backup v0.1.0 MIT LICENSE to frozen/** — `498b273` (chore)
2. **Task 2: Replace LICENSE with Apache-2.0 full text** — `9abbfc7` (feat)
3. **Task 3: Update pyproject.toml with PEP 639 SPDX + deps + version bump** — `550a98e` (feat)
4. **Task 4: README.md License section rewrite (DOC-03 / ROADMAP SC-5)** — `4216001` (docs)

_Note: All non-TDD tasks; one commit each. Plan-metadata commit (SUMMARY.md) follows separately._

## Files Created/Modified
- `frozen/2026-05-24-v0.1.0-spec/LICENSE` — MIT LICENSE backup, byte-identical to v0.1.0 source (`diff -q` exit 0; first line `MIT License`)
- `LICENSE` — Apache License Version 2.0 canonical full text (4 `Apache License` occurrences, 1 `Version 2.0, January 2004`, 1 `Grant of Patent License`, 1 `APPENDIX: How to apply the Apache License`, 1 `Copyright 2026 bibi-meow`; 0 `MIT License`, 0 `LLVM exception` traces)
- `pyproject.toml` — PEP 639 SPDX license declaration, version `0.2.0`, `setuptools>=77.0.3`, deps `pydantic>=2.13.0,<3.0` + `lib-diagram-parser>=0.1.0`, dev extras `pyright[nodejs]==1.1.409` + `libclang==18.1.1`, valid TOML
- `README.md` — `## License` section rewritten with Apache License 2.0 declaration, verbatim "No GPL bundled" phrase, and a 4-row dependency table (lib-code-parser / call graph extractor / pyright / libclang). All other sections (Installation, What it does, Quick start, Configuration, Output models, Trace tag format, Language support, Development) unchanged.

## Verification Evidence (grep gates)

### LICENSE (Task 2 acceptance)

| Check | Expected | Actual |
|---|---|---|
| `grep -c "Apache License" LICENSE` | >= 1 | **4** |
| `grep -c "Version 2.0, January 2004" LICENSE` | >= 1 | **1** |
| `grep -c "Grant of Patent License" LICENSE` | >= 1 | **1** |
| `grep -c "APPENDIX: How to apply the Apache License" LICENSE` | >= 1 | **1** |
| `grep -c "Copyright 2026 bibi-meow" LICENSE` | >= 1 | **1** |
| `grep -c "MIT License" LICENSE` | 0 | **0** |
| `grep -ci "LLVM-exception\|LLVM exception" LICENSE` | 0 | **0** |

### pyproject.toml (Task 3 acceptance)

| Check | Expected | Actual |
|---|---|---|
| `grep -c '^license = "Apache-2.0"$' pyproject.toml` | 1 | **1** |
| `grep -c '^license-files = \["LICENSE"\]$' pyproject.toml` | 1 | **1** |
| `grep -c 'setuptools>=77.0.3' pyproject.toml` | >= 1 | **1** |
| `grep -c '^version = "0.2.0"$' pyproject.toml` | 1 | **1** |
| `grep -c '^name = "lib-code-parser"$' pyproject.toml` | 1 | **1** |
| `grep -c 'pydantic>=2.13.0' pyproject.toml` | >= 1 | **1** |
| `grep -c 'lib-diagram-parser>=0.1.0' pyproject.toml` | >= 1 | **1** |
| `grep -c 'pyright\[nodejs\]==1.1.409' pyproject.toml` | >= 1 | **1** |
| `grep -c 'libclang==18.1.1' pyproject.toml` | >= 1 | **1** |
| `grep -c 'license = {text' pyproject.toml` | 0 | **0** |
| `python -c "import tomllib; tomllib.loads(...)"` exit | 0 | **0** |

### README.md (Task 4 acceptance — DOC-03 / ROADMAP SC-5)

| Check | Expected | Actual |
|---|---|---|
| `grep -c "No GPL bundled" README.md` | >= 1 | **1** |
| `grep -cE "Apache License 2\.0\|Apache-2\.0" README.md` | >= 1 | **4** |
| `grep -c "MIT" README.md` | >= 1 | **1** |
| `grep -cE "LLVM exception\|LLVM-exception" README.md` | >= 1 | **1** |
| `grep -ci "pyright" README.md` | >= 1 | **1** |
| `grep -ci "libclang" README.md` | >= 1 | **1** |
| `grep -c "^## License$" README.md` | 1 | **1** |
| `grep -c "^MIT$" README.md` | 0 | **0** |
| Other sections unchanged | 8 unchanged | **8 present** |

### Frozen backup (Task 1 acceptance)

| Check | Expected | Actual |
|---|---|---|
| `test -f frozen/2026-05-24-v0.1.0-spec/LICENSE` | exists | **OK** |
| `diff -q LICENSE.bak frozen/.../LICENSE` (vs v0.1.0 source) | byte-identical | **OK** |
| First line of backup | `MIT License` | **`MIT License`** |

## Decisions Made

None beyond what is captured in PROJECT.md Key Decisions. The plan was executed exactly as written:

- Apache-2.0 (not Apache-2.0 + LLVM exception) for `lib-code-parser` itself — the LLVM exception applies only to the bundled `libclang` dependency, which is documented in the README dependency table, not added to the project's own LICENSE.
- Distribution name `lib-code-parser` preserved (orchestrator pre-resolved Open Question #1).
- `lib-diagram-parser>=0.1.0` declared in Phase 1 dependencies even though direct use is Phase 3+ (documents the schema-compat boundary per SCH-01 / D-15; Phase 1 keeps `graph_base` self-contained per pre-resolved Open Question #5).

## Deviations from Plan

None — plan executed exactly as written. All 4 task acceptance criteria passed on first verification; no auto-fixes (Rule 1/2/3) needed; no architectural checkpoints (Rule 4) triggered.

**Total deviations:** 0
**Impact on plan:** Clean execution. ROADMAP §Phase 1 SC-5 fully satisfied at this plan boundary (no deferral). DOC-04 + DOC-03 both closed.

## Issues Encountered

- Git's CRLF auto-conversion produced a `LF will be replaced by CRLF` warning on LICENSE and pyproject.toml commits. This is benign on Windows (the working-tree file remains as written; only the staged blob is normalized). No action required.

## Known Stubs

None. No placeholders, no TODOs, no hardcoded empty values introduced. All three artifacts (LICENSE, pyproject.toml, README.md) ship with production-final content.

## Threat Flags

None. All security-relevant artifacts (LICENSE legal declaration, license-files glob, README bundled-dep disclosure) match the plan's `<threat_model>` mitigations. No new trust boundaries introduced.

## User Setup Required

None — no external service configuration. The Apache-2.0 license switch carries no retroactive obligation because `lib-code-parser` is unpublished on PyPI (orchestrator pre-resolved Open Question #2 confirmed via PyPI audit in RESEARCH.md).

## Next Phase Readiness

- **Plan 01-02 (spec doc rewrite)** can now safely reference the corrected "call graph internal, NOT pyan3 / NOT ACL-2" disclosure now present in `README.md` License section.
- **Plan 01-09 (pip install -e .[dev] parity test)** can now exercise the declared dependency surface (`pydantic>=2.13.0,<3.0`, `lib-diagram-parser>=0.1.0`, `pyright[nodejs]==1.1.409`, `libclang==18.1.1`).
- **All downstream Phase 2-5 plans** inherit the Apache-2.0 + setuptools>=77.0.3 baseline; no further license actions required at plan boundaries unless a new bundled dependency is added (in which case the README dependency table must be extended).

## Self-Check: PASSED

- LICENSE exists and contains Apache License Version 2.0 with Section 3 Grant of Patent License (verified via `grep -q "Apache License" LICENSE && grep -q "Grant of Patent License" LICENSE`)
- pyproject.toml declares `license = "Apache-2.0"` + `license-files = ["LICENSE"]` + `setuptools>=77.0.3` + `version = "0.2.0"` (verified)
- pyproject.toml parses as valid TOML (verified via `python -c "import tomllib; ..."`)
- frozen/2026-05-24-v0.1.0-spec/LICENSE exists, byte-identical to v0.1.0 source, first line `MIT License` (verified)
- README.md `## License` section contains "No GPL bundled" + "Apache License 2.0" + "MIT" + "LLVM exception" + explicit `pyright` and `libclang` references (verified)
- Commits exist in `git log --oneline -5`: 498b273, 9abbfc7, 550a98e, 4216001 (verified)

---
*Phase: 01-architecture-foundation-spec-correction*
*Plan: 01-01*
*Completed: 2026-05-24*
