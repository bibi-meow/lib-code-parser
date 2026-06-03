---
phase: 04-c-frontend-c-extractors
plan: 07
subsystem: ci
tags: [ci, github-actions, matrix, libclang, lng-01, lng-02, cpp, multi-platform]

# Dependency graph
requires:
  - phase: 04-03
    provides: frontends/cpp.py single libclang parse site + D-07 guard (the cpp track that the matrix exercises)
  - phase: 04-06
    provides: 5 cpp diagram extractors in EVALUATIONS[cpp] (the importable cpp track the full pytest suite runs)
provides:
  - "ci.yml mandatory LNG-01 matrix (no continue-on-error) gating PR merges: Linux x86_64 + Linux aarch64 + Windows x86_64 x CPython 3.11/3.12/3.13/3.14"
  - "ci.yml LNG-02 best-effort macOS arm64 x 3.13/3.14 job (continue-on-error, observed-not-gated) graduated from the Phase-1 sp3-libclang-spike seed"
affects: [milestone-v0.2.0-ship, pr-merge-gating]

# Tech tracking
tech-stack:
  added: []  # no new dependency; libclang==18.1.1 already pinned Phase 1
  patterns:
    - "Single `runs-on: ${{ matrix.os }}` matrix with `matrix.os` list (Linux x86_64/aarch64 + Windows x86_64) x `matrix.python-version` (3.11-3.14); `fail-fast: false` isolates cells"
    - "macOS arm64 kept as a SEPARATE best-effort job (continue-on-error: true) rather than a matrix include, so it never participates in the all-green merge gate"
    - "allow-prereleases: true on setup-python for the 3.14 pre-release cells"

key-files:
  created:
    - .planning/phases/04-c-frontend-c-extractors/04-07-SUMMARY.md
  modified:
    - .github/workflows/ci.yml

key-decisions:
  - "LNG-01 mandatory matrix has NO continue-on-error anywhere: Linux x86_64 (ubuntu-latest) + Linux aarch64 (ubuntu-24.04-arm) + Windows x86_64 (windows-latest) x CPython 3.11/3.12/3.13/3.14 = 12 cells, all-green required to merge"
  - "A2 resolved: native arm64 runner label `ubuntu-24.04-arm` used; QEMU + docker/setup-qemu-action + quay.io/pypa/manylinux2014_aarch64 container documented as the YAML-comment fallback if the native label is unavailable for the repo"
  - "LNG-02: macOS arm64 x 3.13/3.14 stays a standalone continue-on-error job (graduated/renamed from sp3-libclang-spike); observed, never gates"
  - "Verified libclang smoke steps lifted verbatim from the spike job: (a) Index.create(), (b) Config.library_path non-empty assertion, (c) minimal C++ parse of 'int main(){return 0;}'"
  - "Every cell runs the FULL pytest suite (pytest --tb=short) so the cpp track (frontends/cpp.py + cpp PRIMITIVES/EVALUATIONS) is exercised on every platform/Python combo"
  - "No system-LLVM install step (the libclang wheel is self-contained per RESEARCH State of the Art)"
  - "ruff check + ruff format --check gates retained on every mandatory cell (agent discretion: run on all cells rather than gate one cell, since ruff is platform-agnostic and fast)"

patterns-established:
  - "Phase-4 close: the cpp track is now merge-gated on 3 platforms x 4 Python versions; LNG-01 is the all-green requirement, LNG-02 the best-effort observation"

requirements-completed: [LNG-01, LNG-02]

# Metrics
duration: 4min
completed: 2026-06-04
---

# Phase 4 Plan 07: CI LNG-01 Mandatory Matrix + LNG-02 Best-Effort Summary

**`ci.yml` is graduated from the single Phase-1 `sp3-libclang-spike` seed job to a mandatory LNG-01 matrix (no `continue-on-error`) covering Linux x86_64 + Linux aarch64 + Windows x86_64 × CPython 3.11/3.12/3.13/3.14 — each cell installs the pinned `libclang==18.1.1`, imports the lib, runs the three verified libclang smoke steps, and runs the full pytest suite so the cpp track is exercised everywhere; macOS arm64 × 3.13/3.14 remains a standalone `continue-on-error` LNG-02 best-effort job.**

## Performance

- **Duration:** ~4 min
- **Completed:** 2026-06-04
- **Tasks:** 1
- **Files modified:** 2 (1 modified, 1 created)

## Accomplishments
- Replaced the single `test` job (ubuntu-latest / py3.11 only) with a mandatory matrix job: `strategy.fail-fast: false`, `matrix.os: [ubuntu-latest, ubuntu-24.04-arm, windows-latest]` × `matrix.python-version: ["3.11","3.12","3.13","3.14"]` (12 cells), `runs-on: ${{ matrix.os }}`, and **no `continue-on-error`** so all-green gates merges (LNG-01).
- Each mandatory cell: `actions/checkout@v4` → `actions/setup-python@v5` with `allow-prereleases: true` (for 3.14) → `pip install -e ".[dev]"` (pulls the already-pinned `libclang==18.1.1`) → `python -c "import lib_code_parser"` (LNG-01 import) → the three verified libclang smoke steps (`Index.create()`; `Config.library_path` non-empty assertion; minimal C++ parse of `int main(){return 0;}`) → `pytest --tb=short` (full suite, exercises the cpp track) → `ruff check .` + `ruff format --check .`.
- Resolved A2: used the native `ubuntu-24.04-arm` runner label for Linux aarch64, with a YAML comment documenting the QEMU (`docker/setup-qemu-action@v3`) + `quay.io/pypa/manylinux2014_aarch64` container fallback if the native label is unavailable for the repo.
- Renamed/kept the macOS arm64 job as `macos-arm64-best-effort`: `runs-on: macos-14`, `continue-on-error: true`, `matrix.python-version: ["3.13","3.14"]`, same install + smoke + full pytest + a `if: always()` verdict step (LNG-02 best-effort, observed not gated).
- No system-LLVM install step anywhere (self-contained wheel).
- YAML validated well-formed: the plan's automated verify one-liner prints `OK` (asserts a mandatory matrix job with 3.11–3.14, a macOS `continue-on-error` best-effort job, aarch64 coverage, `pip install -e`, and `Index.create()` presence).

## Task Commits

Each task was committed atomically:

1. **Task 1: Graduate ci.yml to the LNG-01 mandatory matrix + LNG-02 best-effort macOS job** - `e0ffde8` (ci)

## Files Created/Modified
- `.github/workflows/ci.yml` (modified) - mandatory 3-platform × 4-Python matrix job (no continue-on-error) + best-effort macOS arm64 job (continue-on-error); A2 native arm64 label with QEMU/manylinux2014_aarch64 fallback documented as a comment; lint/format gates retained on every mandatory cell.
- `.planning/phases/04-c-frontend-c-extractors/04-07-SUMMARY.md` (created) - this summary.

## Decisions Made
- **Lint/format on all cells (discretion):** the plan granted "on the Linux x86_64 / py3.11 cell or all cells per discretion." Chose all cells — `ruff` is platform-agnostic and sub-second, and avoiding a per-cell `if:` conditional keeps the YAML simpler and uniform. The marginal CI cost is negligible vs. the readability/uniformity benefit.
- **macOS as a separate job, not a matrix `include`:** keeping macOS arm64 as its own `continue-on-error: true` job (rather than folding it into the mandatory matrix with a per-cell `continue-on-error`) guarantees it can never participate in the all-green merge gate, which is the precise LNG-01/LNG-02 split the success criteria require. It also makes the gating intent self-evident at the job level.
- **A2 native label chosen with documented fallback:** per RESEARCH §CI note, `ubuntu-24.04-arm` is generally available for public repos and is faster than QEMU; the fallback is documented inline so a maintainer can switch mechanisms without re-deriving the manylinux container choice.

## Deviations from Plan

None - plan executed exactly as written. (The single discretion points the plan delegated — lint/format cell placement and the A2 runner label — were resolved as documented above; these are plan-authorized choices, not deviations.)

## Verification Note
- The CI matrix structure is the artifact and is validated here as well-formed YAML satisfying the plan's automated verify. **As the plan itself notes, the matrix can only be *truly proven* by an actual CI run** — the green/red of the 12 mandatory cells (and the observed macOS cells) is established when this workflow runs on the next push/PR. The two highest-risk runtime confirmations to watch on first run: (1) the `ubuntu-24.04-arm` runner label provisions for this repo (else apply the documented QEMU fallback), and (2) `Config.library_file is None` holds on each platform so the 04-03 LNG-03 guard's override check behaves (RESEARCH A5).

## Self-Check: PASSED

- `.github/workflows/ci.yml` present and valid YAML (verify one-liner prints `OK`).
- `.planning/phases/04-c-frontend-c-extractors/04-07-SUMMARY.md` present on disk.
- Task 1 commit `e0ffde8` verified in git history.

---
*Phase: 04-c-frontend-c-extractors*
*Completed: 2026-06-04*
