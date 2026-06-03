---
phase: 04-c-frontend-c-extractors
plan: 05
subsystem: cpp-extractors
tags: [libclang, doxygen, contracts, spc-03, trc-03, lng-04, source-kind, d-08, d-09, dispatch]

# Dependency graph
requires:
  - phase: 04-01
    provides: nested PRIMITIVES dict[language, dict[name, fn]] with reserved ["cpp"] sub-dict + executor walk indexed by cav.language + config.extract_contracts gate on the shared "contracts" slot
  - phase: 04-03
    provides: FRONTENDS["cpp"] = build_cav (the libclang parse site producing the cpp CAV with TranslationUnit payload + raw_content carried)
  - phase: 04-04
    provides: _cpp_cursor.py shared helpers (_in_main_file filter, byte-identical TRC-03 extract_trace_tags, qualified_node_id) + cpp_functions de-dup idiom (in-class decl vs out-of-line def share node_id)
provides:
  - "SourceKind Literal gains the additive value 'doxygen' (D-08) — the single model change in Phase 4; existing 4 values intact, ContractKind/ContractEntry/ContractInfo unchanged"
  - "cpp_contracts.extract(cav,config) -> dict[node_id, ContractInfo] — Doxygen \\pre/@pre/\\post/@post/\\invariant/@invariant read off the EXACT decl cursor's raw_comment into the EXISTING ContractInfo/ContractEntry schema (D-09), source_kind='doxygen'"
  - "PRIMITIVES['cpp']['contracts'] registered with the Python key spelling (LNG-04 parity); the executor's config.extract_contracts gate applies uniformly to the shared 'contracts' slot — zero executor diff"
  - "docs/09-extending.md records the SourceKind additive-Literal policy (additive allowed, deletion/rename forbidden — same discipline as EdgeKind)"
affects: [04-06, 04-07, cpp-class-diagram, cpp-acceptance-tests, spec_code_verifier]

# Tech tracking
tech-stack:
  added: []  # libclang already pinned/in-use since 04-03; no new dependency
  patterns:
    - "Doxygen contract provenance is a regex over cursor.raw_comment on the EXACT decl cursor (Pitfall 4) — never the enclosing namespace's leading comment; libclang attaches raw_comment only to the decl it documents, so namespace-level Doxygen does not bleed onto inner decls"
    - "cpp_contracts mirrors the Python contracts extractor's OUTPUT shape (dict[node_id, ContractInfo]) but NOT its provenance machinery — the Pydantic decorator-alias resolution does not carry over; Doxygen marker mapping (_MARKER_TO_KIND) replaces _DECORATOR_TO_SOURCE_KIND"
    - "one SourceKind value ('doxygen') covers three contract kinds — ContractEntry.kind is the orthogonal discriminator (pre/post/invariant), so additive provenance values stay minimal"

key-files:
  created:
    - lib_code_parser/extractors/primitives/cpp_contracts.py
    - tests/unit/extractors/test_cpp_contracts.py
    - tests/acceptance/test_cpp_doxygen_contracts.py
    - tests/parity/test_trc03_cpp_parity.py
  modified:
    - lib_code_parser/models/primitives/contracts.py
    - lib_code_parser/_dispatch.py
    - docs/09-extending.md

key-decisions:
  - "D-08 honored: SourceKind gains ONLY the additive value 'doxygen' (appended last); the original 4 values are neither deleted nor renamed; ContractKind/ContractEntry/ContractInfo shapes already cover everything (no model restructure)"
  - "D-09 honored: C++ Doxygen contracts reuse the EXISTING CodeContent.contracts slot (no new field) and emit the SAME ContractInfo/ContractEntry schema as Python — proven by an acceptance test asserting set(model_fields) equality for both models"
  - "SPC-03: _DOXY_RE = r'[\\\\@](pre|post|invariant)\\b[ \\t]*(.*)' (re.IGNORECASE) matches both \\ and @ forms; pre->precondition, post->postcondition, invariant->invariant; read off the EXACT decl cursor (Pitfall 4 — a namespace-level \\pre comment does NOT attach to an inner decl, asserted by test_pitfall4_namespace_comment_not_inferred)"
  - "TRC-03 parity: cpp_contracts reuses _cpp_cursor.extract_trace_tags (the verbatim byte-identical regex from functions.py); the parity test proves the SAME 'Traces: REQ-9, US-3' text yields identical TraceTag.refs via (a) the Python helper, (b) the cpp helper, (c) the live cpp_functions path, and asserts the compiled regex .pattern literals are equal"
  - "node_id de-dup parity: an in-class method declaration and its out-of-line definition share a qualified node_id; cpp_contracts keeps the first-seen (seen set) exactly as cpp_functions does, so contracts attach to the same id the class diagram (04-06) keys on"
  - "DET-04: main-file decls visited in preorder, result dict preserves first-seen order, per-node entries sorted by (kind, line_no, name) so libclang traversal order never leaks"
  - "additive-Literal policy distinguished from EdgeKind MAJOR policy in docs/09: SourceKind is a primitive-layer (verifier does not see it directly) provenance value, so additive growth needs no MAJOR bump; deletion/rename remains forbidden"

patterns-established:
  - "Provenance-as-additive-Literal: new contract-extraction mechanisms (future languages / dialects) append one SourceKind value and reuse the existing ContractInfo/ContractEntry schema — the cpp class/component evaluations (04-06/04-07) inherit this contracts slot unchanged"

requirements-completed: [SPC-03, TRC-03, LNG-04]

# Metrics
duration: 4min
completed: 2026-06-04
---

# Phase 4 Plan 05: Doxygen-Driven C++ Contract Extraction Summary

**C++ Doxygen contracts are live and symmetric with Python: the additive `SourceKind="doxygen"` value (D-08 — the only model touch in Phase 4) plus `cpp_contracts.py` mapping `\pre`/`@pre`/`\post`/`@post`/`\invariant`/`@invariant` (read off the EXACT decl cursor's `raw_comment`, Pitfall 4) into the EXISTING `ContractInfo`/`ContractEntry` schema reusing the shared `CodeContent.contracts` slot (D-09), registered under `PRIMITIVES["cpp"]["contracts"]` with a 0-line executor diff. Python/C++ symmetry is proven through the public executor (SPC-03 acceptance: 3 Doxygen kinds, `source_kind="doxygen"`, identical schema) and byte-identical `Traces:` extraction (TRC-03 parity: same regex literal, same helper output, same live-path refs).**

## Performance

- **Duration:** ~4 min
- **Tasks:** 3 (Tasks 2 + 3 `tdd="true"`)
- **Files modified:** 7 (4 created, 3 modified)

## Accomplishments
- **Task 1 — additive SourceKind + docs/09 policy:** appended `"doxygen"` as the FINAL `SourceKind` Literal value with the `# ADDITIVE - D-08` inline comment; left `ContractKind`/`ContractEntry`/`ContractInfo` untouched (their shapes already cover everything). Added a docs/09 section "SourceKind 追加は additive Literal 拡張" recording that `SourceKind` additions are additive-allowed (no MAJOR bump for a primitive-layer provenance value) while deletion/rename is forbidden — distinguishing it from the verifier-facing EdgeKind MAJOR policy while sharing the deletion/rename discipline.
- **Task 2 — cpp_contracts extractor:** `_DOXY_RE = r"[\\@](pre|post|invariant)\b[ \t]*(.*)"` (case-insensitive, both forms); walks main-file FUNCTION_DECL/CXX_METHOD/CLASS_DECL/STRUCT_DECL cursors, reads `cursor.raw_comment` on THAT exact cursor (Pitfall 4), maps the marker to `ContractKind`, and emits `ContractEntry(name=<spelling>, source_kind="doxygen", kind=<mapped>, line_no=<decl line>)` grouped under `qualified_node_id` into `ContractInfo`. Same `dict[node_id, ContractInfo]` shape as the Python sibling; node_id de-dup parity (first-seen wins for in-class decl vs out-of-line def); DET-04 sort by `(kind, line_no, name)`. Registered append-only as `PRIMITIVES["cpp"]["contracts"]`.
- **Task 3 — acceptance + parity tests:** `test_cpp_doxygen_contracts.py` drives the PUBLIC `CodeParserExecutor.execute` on the `.cpp` fixture (suffix override selects cpp), asserting the 3 Doxygen kinds, `source_kind=="doxygen"`, attachment to `compute_score`, and `model_fields` set-equality to `ContractInfo`/`ContractEntry` (D-09 schema parity). `test_trc03_cpp_parity.py` proves TRC-03 byte-identity three ways: the Python helper vs the cpp helper output, the compiled regex `.pattern` literals, and the live `cpp_functions` extraction path — all yielding `[["REQ-9", "US-3"]]`.
- 7 new cpp_contracts unit tests + 4 acceptance + 3 parity = 14 new tests green; **full repo suite 498 passed** (484 → +14), zero regressions; ruff check + format clean on all touched files.

## Task Commits

Each task was committed atomically:

1. **Task 1: additive SourceKind 'doxygen' (D-08) + docs/09 policy** - `25168b9` (feat)
2. **Task 2: cpp_contracts Doxygen extractor (SPC-03) + PRIMITIVES["cpp"]["contracts"]** - `13a9af1` (feat)
3. **Task 3: SPC-03 acceptance + TRC-03 parity tests** - `a1682ef` (test)

## TDD Gate Compliance
- **Task 2 (`tdd="true"`):** RED — `tests/unit/extractors/test_cpp_contracts.py` was authored first and failed on `ModuleNotFoundError: cpp_contracts` (module absent). GREEN — `cpp_contracts.py` + the `_dispatch.py` registration made all 7 unit tests pass. Committed together per the per-task atomic-commit protocol.
- **Task 3 (`tdd="true"`):** the acceptance + parity tests are GREEN immediately because Task 2's implementation already satisfies the contract; they are the behavior-locking layer (public-surface SPC-03 + cross-language TRC-03 parity) for the unit-level RED→GREEN already proven in Task 2. The plan-level RED gate is Task 2's failing unit test; the `feat` (GREEN) commit follows it. Note: this is a per-task TDD plan (tasks individually `tdd="true"`), not a single plan-level RED/GREEN feature.

## Files Created/Modified
- `lib_code_parser/models/primitives/contracts.py` (modified) — `SourceKind` Literal gains `"doxygen"` (additive, last) with the D-08 inline comment; nothing else changed.
- `lib_code_parser/extractors/primitives/cpp_contracts.py` (created) — Doxygen contract extractor; `Implements: SPC-03`, `Traces: SPC-03, TRC-03, US-01, US-22`.
- `lib_code_parser/_dispatch.py` (modified) — appended `# noqa: E402` import + `PRIMITIVES["cpp"]["contracts"] = _extract_cpp_contracts`; all prior FRONTENDS/PRIMITIVES/EVALUATIONS entries untouched (append-only invariant #4).
- `docs/09-extending.md` (modified) — new "SourceKind 追加は additive Literal 拡張" section between the EdgeKind MAJOR policy and the dispatch-entry-addition procedure.
- `tests/unit/extractors/test_cpp_contracts.py` (created) — payload assert, both-forms pre/post/invariant, case-insensitivity, no-Doxygen-no-entry, Pitfall-4 namespace non-inference, method qualified-id, dispatch registration.
- `tests/acceptance/test_cpp_doxygen_contracts.py` (created) — public-executor SPC-03 acceptance + D-09 schema parity.
- `tests/parity/test_trc03_cpp_parity.py` (created) — TRC-03 byte-identity (helper + regex literal + live cpp path).

## Decisions Made
- **Provenance machinery does NOT carry over from Python:** the Python contracts extractor's decorator-alias resolution (`_resolve_decorator_aliases` / `_classify_decorator` / `_DECORATOR_TO_SOURCE_KIND`) is Pydantic-specific; cpp_contracts replaces it wholesale with `_DOXY_RE` + `_MARKER_TO_KIND`. Only the OUTPUT shape (`dict[node_id, ContractInfo]` of `ContractEntry` lists) is mirrored — exactly the boundary the plan's action specified.
- **`decorator_name=""` on Doxygen entries:** the `ContractEntry.decorator_name` field is a Pydantic-decorator artifact with no Doxygen analog; it defaults to `""` (the same value the Python `__post_init__` path uses), keeping the schema identical without inventing a Doxygen-specific meaning.
- **Pitfall-4 verified live:** `test_pitfall4_namespace_comment_not_inferred` confirms libclang does NOT attach a namespace's leading `/** \pre ... */` block to an inner `void inner()` decl — `cursor.raw_comment` on the inner decl is empty, so no contract is mis-attributed. The fixture's `compute_score` carries its own Doxygen block and is attributed correctly.

## Deviations from Plan

None — plan executed exactly as written. All three tasks' inline automated verifies passed on first run; the only post-Write adjustments were `ruff format` reflows on two test files (cosmetic, no behavior change).

## Issues Encountered
- A `RequestsDependencyWarning` (urllib3/chardet version mismatch) prints during pytest collection — pre-existing environment noise unrelated to this plan; tests pass cleanly.
- `git` warns `LF will be replaced by CRLF` on each new file commit (Windows autocrlf) — cosmetic, no content impact.
- Pre-existing untracked harness/planning artifacts (`.claude/gsd-*.json`, `.claude/scheduled_tasks.lock`) are out of scope and were left untouched.

## User Setup Required
None — libclang 18.1.1 is already pinned/installed and was exercised live by the cpp CAV builder in every cpp test. No external service configuration required.

## Next Phase Readiness
- `PRIMITIVES["cpp"]` now holds `functions`/`call_graph`/`type_deps`/`contracts` with the Python key spelling; the executor runs them on any cpp CAV with a 0-line executor diff (D-01/D-03 from 04-01) and the `config.extract_contracts` gate applies to the shared `contracts` slot uniformly.
- `SourceKind` is now extensible by the documented additive-Literal policy (docs/09); future contract-extraction mechanisms append one value and reuse the contracts slot.
- The cpp class diagram (04-06) keys on the same `qualified_node_id` cpp_contracts uses, so contracts compose cleanly with it. No blockers.

## Self-Check: PASSED

- All 4 created files + 3 modified files verified present on disk (Edit/Write succeeded; verifies ran against them).
- All 3 commits verified in git history: `25168b9` (Task 1), `13a9af1` (Task 2), `a1682ef` (Task 3).
- Full repository test suite: 498 passed, 0 failed.

---
*Phase: 04-c-frontend-c-extractors*
*Completed: 2026-06-04*
