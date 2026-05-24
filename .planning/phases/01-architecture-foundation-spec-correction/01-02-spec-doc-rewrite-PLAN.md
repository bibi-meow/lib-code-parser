---
phase: 01-architecture-foundation-spec-correction
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - lib-code-parser.md
  - frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md
autonomous: true
requirements: [DOC-01, DOC-03]
must_haves:
  truths:
    - "lib-code-parser.md no longer mentions callgraph.py or ACL-2 (both are misidentifications; live-verified non-existent 2026-05-24)"
    - "Spec doc cites Apache-2.0 license and bundled-dependency license matrix (call graph internal, pyright MIT, libclang Apache-2.0 WITH LLVM-exception)"
    - "v0.1.0 spec doc preserved under frozen/ for traceability"
    - "Downstream verifier agents see the v0.2.0 architecture (CAV, EdgeKind, nested layout, 5 diagrams + 2 specs, Doxygen, physical_*/source_* prefix)"
  artifacts:
    - path: "lib-code-parser.md"
      provides: "v0.2.0 architecture spec doc"
      contains: "Apache-2.0|CAV|EdgeKind"
    - path: "frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md"
      provides: "v0.1.0 historical spec doc (pre-rewrite)"
      contains: "lib-code-parser"
  key_links:
    - from: "lib-code-parser.md §License"
      to: "LICENSE file"
      via: "SPDX identifier Apache-2.0"
      pattern: "Apache-2.0"
    - from: "lib-code-parser.md §採用アルゴリズム"
      to: "internal call graph extractor (no callgraph.py / no ACL-2)"
      via: "explicit prose stating internal extractor + no GPL viral"
      pattern: "内製|internal call graph"
---

<objective>
Per D-01 / D-02 / D-03, fully rewrite `lib-code-parser.md` (project root) into the v0.2.0 architecture spec doc — removing every reference to `callgraph.py` (does not exist) and `ACL-2` (Common Lisp theorem prover, not a call graph tool) — and back up the pre-rewrite version to `frozen/2026-05-24-v0.1.0-spec/` per the project's backup-before-major-rewrite rule.

Purpose: Satisfies DOC-01 (remove misreferences + reflect Key Decisions + cite Apache-2.0) and DOC-03 (no GPL bundled disclosure in spec doc §License). This is the **single source of truth** for downstream verifier agents (spec_code_verifier, architecture_verifier); leaving stale `callgraph.py`/`ACL-2` text would mislead them.

Output:
- New `lib-code-parser.md` with sections §概要 / §インターフェース / §出力 schema / §採用アルゴリズム / §License / §Traceability (per D-03)
- Backup at `frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md` (byte-identical pre-rewrite copy)
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/PROJECT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/ROADMAP.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/REQUIREMENTS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Backup current lib-code-parser.md to frozen/</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib-code-parser.md (current v0.1.0 spec — verify presence of `callgraph.py` and `ACL-2` strings before backup so the rewrite removal can be validated)
    - C:/work/agent_company/spec-reviewer-libs/.claude/rules/backup-before-major-rewrite.md (project rule: backup before rewrites >100 lines or destructive moves)
  </read_first>
  <action>
    Ensure directory `frozen/2026-05-24-v0.1.0-spec/` exists (Plan 01 may have created it; if not, create it via `mkdir -p`). Copy `lib-code-parser.md` to `frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md` byte-identical. Do NOT touch the source `lib-code-parser.md` in this task — Task 2 overwrites it. Verify the copy is byte-identical via `diff -q`. This satisfies D-02 (旧版を frozen/ に退避してから rewrite).
  </action>
  <verify>
    <automated>test -f "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md" &amp;&amp; diff -q "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib-code-parser.md" "C:/work/agent_company/spec-reviewer-libs/lib-code-parser/frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md"</automated>
  </verify>
  <acceptance_criteria>
    - File `frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md` exists
    - `diff -q lib-code-parser.md frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md` exits 0 (byte-identical)
    - Source `lib-code-parser.md` is untouched (still contains the v0.1.0 text including the strings to be removed in Task 2)
    - Sanity check: backup file size > 0 bytes
  </acceptance_criteria>
  <done>Pre-rewrite spec doc preserved at `frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md`, byte-identical to source.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Full rewrite lib-code-parser.md with v0.2.0 sections</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/frozen/2026-05-24-v0.1.0-spec/lib-code-parser.md (the backup — reference for what to remove; Task 1 must have created it)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/PROJECT.md (Core Value, 16 Key Decisions, Constraints — all must be reflected)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/REQUIREMENTS.md (42 v1 requirements with US mapping — §Traceability summary draws from this)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§lib-code-parser.md Rewrite Strategy: exact section structure, deletions, additions, and License Matrix table verbatim)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md (D-01/D-02/D-03 — section structure mandate)
  </read_first>
  <action>
    Overwrite `lib-code-parser.md` (project root) with a full rewrite (per D-01 surgical edit rejected). The new document MUST contain exactly the following H2 sections in this order, written in Japanese to match the existing project documentation style:

    1. `## §概要` — Describe lib-code-parser v0.2.0 purpose: deterministic Python/C++ source parser supplying lib-diagram-parser-compatible AST primitives / 5 diagrams / function-class specs to spec-reviewer's spec_code_verifier (US-01/US-22) and architecture_verifier (US-32). State explicitly: "内製 call graph extractor" (no callgraph.py, no ACL-2, no GPL viral), pyright MIT subprocess, libclang Apache-2.0 WITH LLVM-exception in-process, CAV (Common AST View) single-parse envelope, EdgeKind closed Literal, 5 diagrams (class/sequence/component/package/state), function/class spec extractors (Python + C++ Doxygen), icontract/deal/PEP-316 supplementary, Apache-2.0 license (LICENSE 同梱 with patent grant clause), physical_*/source_* prefix convention, Traceability.

    2. `## §インターフェース` — Document the caller API: `CodeParserExecutor.execute(config, raw_content, path) -> NormalizedArtifact[CodeContent]`. Include a table of typed ParserConfig fields per D-08 / ARC-05: `enabled: bool`, `language: Literal["python", "cpp"]`, `extract_contracts: bool`, `compile_args: list[str]` (C++ only, default `["-std=c++17"]`), `python_version: str`. Explicitly note that the v0.1.0 untyped `params: dict[str, object]` is REMOVED in v0.2.0 (ARC-05). Do NOT include a `params.callgraph_tool` row (the v0.1.0 spec had it referencing callgraph.py — that row is removed).

    3. `## §出力 schema` (new section per D-03) — Describe the Pydantic Generic envelope `NormalizedArtifact[TContent]`, the `CodeContent` aggregate (`functions: list[FunctionNode]`, `call_graph: CallGraph`, `type_deps: list[TypeDep]`, `contracts: dict[str, ContractInfo]`), the `GraphNode` / `GraphEdge` / `GraphModel` / `GuardExpr` schema (lib-diagram-parser compatible), the closed `EdgeKind` Literal listing all 11 values (inherits / implements / composes / aggregates / associates / field_of / param_of / returns / instantiates / calls / transitions_to) and explicitly stating "uses / other / misc は採用しない (Pitfall 7)", and the `physical_*` / `source_*` prefix rule for physical-side-only metadata (SCH-02).

    4. `## §採用アルゴリズム` — For each capability state the tool used. Required statements: (a) Python AST = stdlib `ast` (1 parse per file → CAV), (b) **内製 call graph extractor (AST 静的解析、 GPL viral 回避; pyan3 不採用、 PyCG archived 不採用、 code2flow 非決定論 不採用)** — this is the explicit text that replaces all `callgraph.py` / `ACL-2` references, (c) pyright[nodejs]==1.1.409 subprocess for type resolution (MIT license, Node bundled), (d) libclang==18.1.1 in-process ctypes (Apache-2.0 WITH LLVM-exception, strictly pinned, runtime guard via `cindex.Index.create()`), (e) Pydantic v2 validator / dataclass `__post_init__` discrimination for ContractInfo (`source_kind ∈ {pydantic_validator, pydantic_model_validator, pydantic_field_validator, dataclass_post_init}`), (f) Doxygen `\pre` / `\post` / `\invariant` for C++ contracts (symmetric to Python), (g) subprocess hardening: `encoding="utf-8"`, `errors="replace"`, `env={LC_ALL=C, LANG=C, PYTHONHASHSEED=0, PYTHONIOENCODING=utf-8}`, explicit `timeout` and `cwd`, `capture_output=True`, `shell=False` — all isolated to `lib_code_parser/adapters/` (ARC-03 / DET-05). State the Open-Closed contract briefly: dispatch dicts (FRONTENDS / PRIMITIVES / EVALUATIONS in `_dispatch.py`) are append-only; existing primitives / evaluation units are not modified after Phase 1 fix; new analyses go in new files. Forward-reference `docs/09-extending.md` for the full 6 invariants.

    5. `## §License` (new section per D-03) — Include the License Matrix table verbatim from 01-RESEARCH.md §Apache-2.0 pyproject.toml: lib-code-parser itself is Apache-2.0 (SPDX `Apache-2.0`); internal call graph extractor is part of this lib (Apache-2.0, no GPL viral, explicitly note pyan3 was rejected for GPL, PyCG archived, code2flow non-deterministic); pyright dependency is MIT (Microsoft, subprocess); libclang bundled wheel is `Apache-2.0 WITH LLVM-exception` (SPDX, LLVM exception makes it GPL-v2 compatible by exempting compiler-produced artifacts from attribution; lib-code-parser invokes it via ctypes in-process). State "No GPL-licensed tools are bundled" — this is the DOC-03 disclosure (will be mirrored to README.md in Phase 5; the spec doc is the authoritative source until then). Include patent grant clause notice ("LICENSE file ships Section 3 Grant of Patent License").

    6. `## §Traceability` (new section per D-03) — Summarize the 42 v1 requirements → US mapping from REQUIREMENTS.md §Traceability table. Group by category (AST / DIA / SPC / LNG / ARC / DET / SCH / TRC / DOC) and within each category list the REQ-IDs + which US (US-01 / US-22 / US-25 / US-32) they support. Add the line "TRC-02 / TRC-03 (per-module REQ-ID docstring declaration and trace tag extraction) は Phase 2 で実装" and "詳細 mapping table は `docs/99-trace-matrix.md` を参照". For each of the 14 Phase 1 REQ IDs (ARC-01, ARC-02, ARC-03, ARC-04, ARC-05, SCH-01, SCH-02, SCH-03, DET-04, DET-05, DOC-01, DOC-03, DOC-04, TRC-01) include the literal token `Traces: <REQ-ID>` so the trace tag regex from v0.1.0 (`Traces:\s*([A-Z]+-\d+...)`) can extract them (this is the §Traceability count gate in Plan 02 verification).

    Constraints / removals (DOC-01 acceptance gate):
    - The strings `callgraph.py` and `ACL-2` (case-sensitive) MUST NOT appear anywhere in the new document. If the rewrite mentions them at all (e.g., "the old spec referenced callgraph.py"), the grep gate fails — describe the migration without using these literal strings. The literal SPDX identifier `Apache-2.0` does NOT contain "ACL-2" as a substring (it contains "che-2.0" inside "Apache-2.0"), so plain SPDX usage is fine; just avoid the literal `ACL-2` token.
    - DO NOT add a `params.callgraph_tool` row to the interface table.
    - DO NOT include placeholder text like "TBD" or "to be filled" — every section above MUST contain real prose drawn from PROJECT.md / REQUIREMENTS.md / RESEARCH.md.

    Validation note: Plan 09 acceptance criteria do NOT depend on lib-code-parser.md content; this rewrite is independent of any code change.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; ! grep -E "callgraph\.py|ACL-2" lib-code-parser.md &amp;&amp; grep -c "Apache-2.0" lib-code-parser.md &amp;&amp; grep -c "EdgeKind" lib-code-parser.md &amp;&amp; grep -c "CAV" lib-code-parser.md &amp;&amp; grep -c "## §概要" lib-code-parser.md &amp;&amp; grep -c "## §License" lib-code-parser.md &amp;&amp; grep -c "## §Traceability" lib-code-parser.md &amp;&amp; [ $(grep -c "Traces:" lib-code-parser.md) -ge 14 ]</automated>
  </verify>
  <acceptance_criteria>
    - `grep -E "callgraph\.py|ACL-2" lib-code-parser.md` returns NOTHING (exit code 1; no matches) — DOC-01 hard gate
    - `grep -c "## §概要" lib-code-parser.md` returns exactly 1
    - `grep -c "## §インターフェース" lib-code-parser.md` returns exactly 1
    - `grep -c "## §出力 schema" lib-code-parser.md` returns exactly 1
    - `grep -c "## §採用アルゴリズム" lib-code-parser.md` returns exactly 1
    - `grep -c "## §License" lib-code-parser.md` returns exactly 1
    - `grep -c "## §Traceability" lib-code-parser.md` returns exactly 1
    - `grep -c "Apache-2.0" lib-code-parser.md` returns >= 2 (one in §概要, one in §License)
    - `grep -c "patent" lib-code-parser.md` returns >= 1 (Section 3 patent grant referenced in §License)
    - `grep -c "LLVM-exception" lib-code-parser.md` returns >= 1 (libclang license correctly identified)
    - `grep -c "MIT" lib-code-parser.md` returns >= 1 (pyright license correctly identified)
    - `grep -c "GPL" lib-code-parser.md` returns >= 1 ("No GPL bundled" disclosure or "GPL viral 回避" in §採用アルゴリズム — DOC-03 substrate)
    - `grep -c "内製" lib-code-parser.md` returns >= 1 (internal call graph extractor)
    - `grep -c "CAV" lib-code-parser.md` returns >= 1 (Common AST View introduced)
    - `grep -c "EdgeKind" lib-code-parser.md` returns >= 1 (closed Literal mentioned)
    - `grep -c "extra=\"forbid\"\|extra=forbid" lib-code-parser.md` returns >= 1 (SCH-02 mentioned in §出力 schema)
    - `grep -c "physical_\|source_" lib-code-parser.md` returns >= 1 (SCH-02 prefix convention)
    - `grep -cE "^Traces: [A-Z]+-[0-9]+|Traces: [A-Z]+-[0-9]+" lib-code-parser.md` returns >= 14 (one literal `Traces:` line per Phase 1 REQ-ID — TRC-01)
    - All 14 Phase 1 REQ-IDs appear at least once: `for id in ARC-01 ARC-02 ARC-03 ARC-04 ARC-05 SCH-01 SCH-02 SCH-03 DET-04 DET-05 DOC-01 DOC-03 DOC-04 TRC-01; do grep -q "$id" lib-code-parser.md || echo "MISSING: $id"; done` produces no MISSING output
    - File is well-formed Markdown (no broken section headers; `awk '/^## /{print}' lib-code-parser.md | wc -l` returns >= 6)
  </acceptance_criteria>
  <done>`lib-code-parser.md` contains all 6 required sections, all forbidden strings (callgraph.py / ACL-2) absent, all 14 Phase 1 REQ-IDs cited with `Traces:` tags, License Matrix prose includes Apache-2.0 + MIT + LLVM-exception + "No GPL bundled".</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| lib-code-parser.md → downstream verifier agents (spec_code_verifier, architecture_verifier) | The spec doc is the canonical input that defines what the lib does and how it should be invoked; misinformation here propagates to LLM agents that consume it |
| repo history → future contributors | Removing v0.1.0 text without backup would destroy the historical record of MIT-era / callgraph.py-era design intent |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-01 | Spoofing | Spec doc misidentifies tools (T6 from security_threat_model_required) | mitigate | Task 2 acceptance: `grep -E "callgraph\.py|ACL-2" lib-code-parser.md` MUST return nothing (DOC-01 hard gate) |
| T-02-02 | Information Disclosure | Loss of v0.1.0 spec doc historical record | mitigate | Task 1 backup to `frozen/2026-05-24-v0.1.0-spec/` before Task 2 rewrite |
| T-02-03 | Tampering | Hidden placeholder text ("TBD", "to be filled") sneaks into shipped spec doc | mitigate | Task 2 acceptance: all 6 sections must contain prose; awk header count >= 6 |
| T-02-04 | Repudiation | License declaration in spec doc disagrees with pyproject.toml + LICENSE file | mitigate | Task 2 §License section text is sourced from RESEARCH.md §Apache-2.0 pyproject.toml table (single source); Plan 01 produces the matching LICENSE/pyproject.toml |
</threat_model>

<verification>
- Forbidden strings absent: `callgraph.py`, `ACL-2`
- All 6 H2 sections present (§概要, §インターフェース, §出力 schema, §採用アルゴリズム, §License, §Traceability)
- All 14 Phase 1 REQ-IDs cited via `Traces:` tags
- License Matrix prose includes Apache-2.0 SPDX + MIT (pyright) + LLVM-exception (libclang) + "No GPL bundled"
- Backup at frozen/ is byte-identical to pre-rewrite source
</verification>

<success_criteria>
- ROADMAP §Phase 1 Success Criterion 5: `lib-code-parser.md` spec doc no longer mentions `callgraph.py` or "ACL-2" ✓
- DOC-01 satisfied: misreferences removed + Key Decisions reflected + Apache-2.0 cited
- DOC-03 substrate present: spec doc §License has "No GPL bundled" disclosure (README.md gets the same disclosure in Phase 5)
- TRC-01 partially supported: 14 Phase 1 REQs have at least one `Traces:` tag in spec doc (final TRC-01 closure in Plan 10's docs/99-trace-matrix.md update)
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-02-SUMMARY.md` when done, including grep output for each acceptance criterion (forbidden-string absence + section-presence counts + Traces tag count).
</output>
