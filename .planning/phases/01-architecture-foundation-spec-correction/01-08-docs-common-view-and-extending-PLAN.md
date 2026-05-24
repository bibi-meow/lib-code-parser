---
phase: 01-architecture-foundation-spec-correction
plan: 08
type: execute
wave: 1
depends_on: []
files_modified:
  - docs/08-common-view-pattern.md
  - docs/09-extending.md
autonomous: true
requirements: [ARC-04, DET-04]
must_haves:
  truths:
    - "docs/08-common-view-pattern.md describes CAV envelope + NormalizedArtifact[TContent] Generic + I/O variability strategy (caller-agnostic) in a form transferable to sibling libs"
    - "docs/09-extending.md enumerates all 6 Open-Closed invariants AND documents the append-only invariant on dispatch dicts per pre-resolved decision #4"
    - "docs/09-extending.md instructs that the verifier-facing logical-architecture comparison target is models/evaluations/ only (D-14)"
    - "docs/09-extending.md states adding a new EdgeKind value is a MAJOR version-bump operation, not an ad-hoc patch (Pitfall 7 prevention)"
    - "D-07: docs/08-common-view-pattern.md created on the SDD-chain numbering (08-) — lib-code-parser内に閉じる (no workspace-common doc; sibling-lib adoption recipe ships as Section 5 of docs/08)"
    - "D-13: docs/09-extending.md enumerates exactly the 6 Open-Closed invariants verbatim from CONTEXT.md (existing primitive/evaluation immutability, CodeContent optional fields only, dispatch dict append-only, pull-based primitive supply, executor scan-only)"
  artifacts:
    - path: "docs/08-common-view-pattern.md"
      provides: "Common View / CAV / Generic envelope transferable design doc"
      contains: "Common AST View|NormalizedArtifact"
    - path: "docs/09-extending.md"
      provides: "Open-Closed extension contract (6 invariants) + dispatch dict append-only + EdgeKind MAJOR-version policy"
      contains: "append-only|Open-Closed"
  key_links:
    - from: "docs/09-extending.md"
      to: "lib_code_parser/_dispatch.py docstring forward-reference"
      via: "back-link from _dispatch.py module docstring"
      pattern: "docs/09-extending.md"
    - from: "docs/09-extending.md"
      to: "models/evaluations/ vs models/primitives|infrastructure"
      via: "D-14 layer purity rule"
      pattern: "evaluations"
---

<objective>
Per D-07 and D-13: create two new SDD-chain docs in `docs/`:
1. `docs/08-common-view-pattern.md` — describes the Common AST View (CAV) envelope, `NormalizedArtifact[TContent]` Generic, and the caller-agnostic I/O pattern in a way that is transferable to sibling libs (`lib-spec-parser`, `lib-diagram-parser`, etc. as future adopters). This is the design rationale doc that the v0.2.0 spec doc rewrite (Plan 02 §採用アルゴリズム) forward-references.
2. `docs/09-extending.md` — enumerates the 6 Open-Closed invariants (per D-13) governing how Phase 2-4 contributors add new primitives / evaluation units / dispatch entries / EdgeKind values without breaking lib boundaries.

Per pre-resolved Open Question #3, SDD chain `docs/00-07/99` template skeletons remain unfilled in Phase 1 — only docs/08 and docs/09 are new prose; the existing chain is untouched until a later phase.

Purpose: Codifies the architectural rules so Phase 2-4 contributors / future agents have an authoritative reference instead of re-deriving the rules from CONTEXT.md every time. Critical for the append-only dispatch invariant (pre-resolved decision #4 — enforced by code review, NOT hook/lint — relies on docs being clear) and for preventing EdgeKind ad-hoc growth (Pitfall 7).

Output:
- 2 new markdown files in docs/
- Both files use the existing SDD-chain numbering convention (`08-` and `09-` prefixes)
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/research/PITFALLS.md
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Write docs/08-common-view-pattern.md</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md (D-04 through D-09: CAV polymorphism design)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Pydantic v2 Generic for NormalizedArtifact[TContent] — live-tested patterns; §Architecture Patterns Pattern 1 + Pattern 2; transferable rationale)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/docs/06-architecture.md (existing SDD-chain doc — match prose style)
  </read_first>
  <action>
    Create `docs/08-common-view-pattern.md` (Japanese prose to match the existing SDD chain in docs/). Required H2 sections:

    1. `## 目的` — Why the Common View pattern exists: AST 4× re-parse anti-pattern of v0.1.0; need for a single-parse envelope; the cross-cutting variability surface (Python AST vs C++ TranslationUnit) makes typed union brittle.

    2. `## CAV (Common AST View) 定義` — The Pydantic model with `language: Literal["python", "cpp"]`, `path: str`, `payload: object`, `model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True, frozen=True)`. Explain each ConfigDict flag's reason (extra="forbid" for SCH-02 schema drift prevention, arbitrary_types_allowed=True because ast.Module / cindex.TranslationUnit are not Pydantic models, frozen=True for immutability across extractors).

    3. `## NormalizedArtifact[TContent] Generic 化` — Why Pydantic v2 Generic: caller can refine `content` type via parameter binding (`NormalizedArtifact[CodeContent]`) while v0.1.0 callers writing unparameterized construction still work (byte-identical JSON, live-verified per RESEARCH). Include a small code example showing both forms.

    4. `## I/O variability — caller-agnostic 原則` — The library accepts `(config, raw_content: bytes, path: str)` and returns `NormalizedArtifact[CodeContent]`; no file I/O, no logging, no env reads. Caller owns file system and observability concerns. State this as a CONTRACT inherited from PROJECT.md Constraints.

    5. `## 兄弟 lib 採用ガイド` — Brief recipe for `lib-spec-parser` / `lib-diagram-parser` / future libs to adopt the same pattern: (1) define a `TContent` TypeVar bound=BaseModel, (2) declare `NormalizedArtifact(BaseModel, Generic[TContent])` with extra="forbid", (3) keep model_dump_json() byte-identical for v0.1.0 parity, (4) re-use this lib's `lib_code_parser/adapters/base.py:run_subprocess()` as a transferable helper (no internal state). Mark this section as Phase 1 NOT-shipped-yet: workspace-common lib is in Deferred Ideas (CONTEXT.md `## Deferred Ideas`), triggered when 2+ sibling libs adopt the same pattern.

    6. `## Traceability` — `Traces: ARC-02, ARC-04, ARC-05`. Forward reference to docs/09-extending.md and lib-code-parser.md §採用アルゴリズム.

    Style notes: 1500-3000 characters. Concrete code blocks in Python (use ```python fences). Avoid recapping content from RESEARCH.md verbatim — paraphrase to fit the SDD-chain doc style.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; test -f docs/08-common-view-pattern.md &amp;&amp; grep -c "^## 目的" docs/08-common-view-pattern.md &amp;&amp; grep -c "^## CAV" docs/08-common-view-pattern.md &amp;&amp; grep -c "^## NormalizedArtifact" docs/08-common-view-pattern.md &amp;&amp; grep -c "Traces:" docs/08-common-view-pattern.md</automated>
  </verify>
  <acceptance_criteria>
    - File `docs/08-common-view-pattern.md` exists
    - `grep -c "^## 目的" docs/08-common-view-pattern.md` returns exactly 1
    - `grep -c "^## CAV" docs/08-common-view-pattern.md` returns exactly 1
    - `grep -c "^## NormalizedArtifact" docs/08-common-view-pattern.md` returns exactly 1
    - `grep -c "^## I/O variability\|^## I/O" docs/08-common-view-pattern.md` returns >= 1
    - `grep -c "^## 兄弟 lib\|^## Sibling lib" docs/08-common-view-pattern.md` returns >= 1
    - `grep -c "^## Traceability" docs/08-common-view-pattern.md` returns >= 1
    - `grep -c "Traces:" docs/08-common-view-pattern.md` returns >= 1
    - `grep -c 'extra="forbid"' docs/08-common-view-pattern.md` returns >= 1 (SCH-02 mention)
    - `grep -c 'frozen=True' docs/08-common-view-pattern.md` returns >= 1
    - `grep -c 'Generic\[TContent\]\|Generic\[T\]' docs/08-common-view-pattern.md` returns >= 1
    - File size > 1500 bytes (substantive content, not stub)
    - `wc -l docs/08-common-view-pattern.md` returns >= 40 (real prose, not placeholder)
  </acceptance_criteria>
  <done>docs/08-common-view-pattern.md ships with 6 H2 sections, CAV + Generic + caller-agnostic + sibling-lib adoption recipe + Traceability.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Write docs/09-extending.md with 6 Open-Closed invariants</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md (D-13 — the 6 invariants verbatim; D-14 — layer purity rule; pre-resolved Open Question #4 — append-only invariant enforced via code review, NOT hook/lint)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/research/PITFALLS.md §Pitfall 7 (EdgeKind ad-hoc growth — `"associates"` is the explicit undecidable fallback, not a catch-all; adding new EdgeKind values is MAJOR version bump)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-RESEARCH.md (§Dispatch Dict Pattern — append-only rationale, enforcement strategy)
  </read_first>
  <action>
    Create `docs/09-extending.md` (Japanese prose). Required H2 sections:

    1. `## 目的` — Why this doc exists: lib-code-parser is intended to grow (Phase 2-4 add extractors; future milestones add evaluation units). Without explicit rules, ad-hoc additions break the verifier contract (Pitfall 6 cross-lib drift) or the determinism contract (Pitfall 7 EdgeKind growth).

    2. `## 6 つの Open-Closed 不変条件` — Enumerate exactly these 6 invariants (from D-13, verbatim numbering):
       1. 既存 primitive は変更不可 (新 primitive は別 file)
       2. 既存評価単位は変更不可 (新評価単位は別 file)
       3. `CodeContent` への追加は optional field で行う (v0.1.0 互換性維持)
       4. dispatch dict は append-only
       5. 評価単位は primitives を pull で取得 (push 型注入ではない)
       6. executor は dispatch dict 走査ロジックのみ (評価単位を増やしても変更しない)
       Each invariant gets one paragraph explaining how to honor it + one anti-pattern example.

    3. `## 論理アーキ比較対象は models/evaluations/ のみ (D-14)` — Layer purity rule. Verifier (LLM agent) compares ONLY `models/evaluations/` outputs (the 5 diagrams + 2 specs). `models/primitives/` and `models/infrastructure/` are NOT verifier-facing — they are intermediate data and I/O contract respectively. Explain the consequence: EdgeKind Literal (SCH-03) applies ONLY to `models/evaluations/graph_base.py` `GraphEdge.edge_type`; `models/primitives/type_deps.py` `TypeDep.kind` stays free-form `str` because it's not verifier-visible. This protects the verifier-facing surface without over-constraining intermediate data.

    4. `## EdgeKind 追加は MAJOR version 案件` — Pitfall 7 prevention. The 11 EdgeKind values are CLOSED. If a new diagram type genuinely needs a new edge semantic (rare), it requires: (a) opening an issue documenting why none of `inherits / implements / composes / aggregates / associates / field_of / param_of / returns / instantiates / calls / transitions_to` fit; (b) a major version bump (v0.x.0 → v1.0.0); (c) coordinated update to `lib-diagram-parser` and `architecture_verifier`. Ad-hoc `"uses"` / `"other"` / `"misc"` patches are PROHIBITED. The undecidable fallback is `"associates"` (an explicit semantic, not a catch-all) — use it when composition vs aggregation is undecidable per the type-annotation rule (DIA-01).

    5. `## dispatch dict への entry 追加手順` — How to add a new frontend / primitive / evaluation:
       - Frontend: write `lib_code_parser/frontends/<lang>.py` exporting `build_cav(raw_content, path, config) -> CAV`; add `FRONTENDS["<lang>"] = build_cav` in `_dispatch.py`; submit as a separate PR (not bundled with other extractor work).
       - Primitive: write `lib_code_parser/extractors/primitives/<aspect>.py` exporting `extract(cav, config)`; add `PRIMITIVES["<aspect>"] = extract`; ensure the corresponding model lives in `lib_code_parser/models/primitives/<aspect>.py` with `extra="forbid"`.
       - Evaluation: write `lib_code_parser/extractors/<diagram_or_spec>.py` exporting `extract(cav, config)`; add `EVALUATIONS["<name>"] = extract`; ensure the corresponding output model lives in `lib_code_parser/models/evaluations/<name>.py`.
       - Modifying existing entries is forbidden (invariant #4). Removing entries is also forbidden (would break the verifier contract). State that the append-only invariant is enforced via code review per pre-resolved Open Question #4 — Phase 1 does NOT install hook/lint automation; reviewer applies the rule manually.

    6. `## 拡張シナリオ例 (DDD リバース)` — Brief example of how a future DDD-reverse milestone would add: (a) new primitives `class_relations.py`, `naming_patterns.py`, `module_groups.py`; (b) new evaluation units `ddd_context_map.py`, `ddd_aggregate.py`, `ddd_layer_diagram.py`. Show that all 6 invariants hold: existing primitives unchanged, existing evaluations unchanged, CodeContent gains optional `ddd_*` fields, dispatch dicts grow by 6 entries, evaluations pull primitives via import, executor unchanged. This forward-looks toward CONTEXT.md Deferred Ideas §Future evaluation units.

    7. `## Traceability` — `Traces: ARC-01, ARC-02, ARC-03, ARC-04, ARC-05, SCH-01, SCH-02, SCH-03, DET-04`.

    Style notes: 2500-4500 characters. Use bulleted lists for the 6 invariants. Code-block examples for the dispatch entry-addition recipe.

    Do NOT add a hook/lint enforcement section. Per pre-resolved Open Question #4, append-only invariant enforcement is code-review-only in Phase 1.

    Do NOT contradict CONTEXT.md `## Claude's Discretion` — Claude has discretion on prose style and detail; but section structure and invariant content are LOCKED by D-13.
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; test -f docs/09-extending.md &amp;&amp; grep -c "^## " docs/09-extending.md &amp;&amp; grep -ic "append-only" docs/09-extending.md &amp;&amp; grep -c "EdgeKind" docs/09-extending.md &amp;&amp; grep -c "MAJOR" docs/09-extending.md &amp;&amp; grep -c "Traces:" docs/09-extending.md</automated>
  </verify>
  <acceptance_criteria>
    - File `docs/09-extending.md` exists
    - `grep -c "^## " docs/09-extending.md` returns >= 7 (all 7 required H2 sections present)
    - `grep -c "^## 目的" docs/09-extending.md` returns exactly 1
    - `grep -c "^## 6 つの Open-Closed 不変条件\|^## 6 invariants" docs/09-extending.md` returns >= 1
    - `grep -c "evaluations" docs/09-extending.md` returns >= 2 (layer purity section)
    - `grep -c "EdgeKind" docs/09-extending.md` returns >= 2
    - `grep -ci "append-only" docs/09-extending.md` returns >= 2 (mentioned in invariant #4 AND in the dispatch dict procedure section)
    - `grep -c "MAJOR" docs/09-extending.md` returns >= 1 (EdgeKind version-bump policy)
    - `grep -ci "associates" docs/09-extending.md` returns >= 1 (undecidable fallback explicit)
    - `grep -ci 'uses\|other\|misc' docs/09-extending.md | head -1` — these words MAY appear in prose (e.g., "禁止される uses / other / misc"); the gate is that they are described as FORBIDDEN, not as recommended (manual review verifies tone — no automated grep for tone)
    - `grep -c "^## Traceability" docs/09-extending.md` returns >= 1
    - `grep -c "Traces:" docs/09-extending.md` returns >= 1
    - File size > 2500 bytes (substantive content)
    - `wc -l docs/09-extending.md` returns >= 60
    - `grep -c "code review" docs/09-extending.md` returns >= 1 (per pre-resolved decision #4 — review-only enforcement)
    - `grep -c "hook\|lint" docs/09-extending.md` — if non-zero, the prose MUST state that hook/lint enforcement is NOT shipped in Phase 1 (review-only); manual review verifies
  </acceptance_criteria>
  <done>docs/09-extending.md ships with 7 H2 sections, all 6 Open-Closed invariants enumerated verbatim from D-13, EdgeKind MAJOR-version policy explicit, dispatch entry-addition recipe documented, code-review-only enforcement model stated.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| docs → Phase 2-4 contributors | Contributors consult these docs when adding extractors; ambiguity here propagates to architectural drift |
| docs/09 → code reviewer | Reviewer relies on the doc as authoritative when judging whether a PR violates the append-only invariant (per pre-resolved decision #4) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-08-01 | Tampering | EdgeKind ad-hoc growth via "uses"/"other"/"misc" being added in a future PR (Pitfall 7) | mitigate | docs/09 §"EdgeKind 追加は MAJOR version 案件" makes the policy explicit AND identifies `"associates"` as the undecidable fallback so contributors have a sanctioned out |
| T-08-02 | Tampering | Dispatch dict overwrite via PR that modifies existing entry (invariant #4 violation) | mitigate | docs/09 §"dispatch dict への entry 追加手順" + module docstring in _dispatch.py both state append-only; code review is the enforcement point per pre-resolved Open Question #4 |
| T-08-03 | Spoofing | Verifier sees primitives data and over-interprets layer boundary (D-14 violation) | mitigate | docs/09 §"論理アーキ比較対象は models/evaluations/ のみ" explicitly excludes primitives/infrastructure from verifier comparisons; consistent with EdgeKind being strict only in evaluations |
</threat_model>

<verification>
- docs/08-common-view-pattern.md has all 6 H2 sections + Traceability tags
- docs/09-extending.md enumerates all 6 Open-Closed invariants + EdgeKind MAJOR-version policy + dispatch entry-addition recipe + code-review-only enforcement model
- Both files exceed 1500/2500 bytes of substantive prose (no placeholders)
</verification>

<success_criteria>
- D-07 satisfied: docs/08-common-view-pattern.md created with transferable design rationale for CAV + NormalizedArtifact Generic
- D-13 satisfied: docs/09-extending.md enumerates all 6 invariants + EdgeKind MAJOR-version policy
- Pitfall 7 prevention documented (ad-hoc EdgeKind growth banned in writing)
- Pre-resolved Open Question #4 honored (append-only invariant is code-review-enforced; no hook/lint shipped)
- ARC-04 and DET-04 documentary substrate present (additional to the code substrate in Plans 06 and 09)
</success_criteria>

<output>
Create `.planning/phases/01-architecture-foundation-spec-correction/01-08-SUMMARY.md` when done with grep verification of all required section headers and Traces tags.
</output>
