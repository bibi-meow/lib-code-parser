# Research Summary: lib-code-parser v0.2.0

Generated: 2026-05-23
Research files synthesized: STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

---

## Executive Summary

lib-code-parser v0.2.0 is a brownfield milestone that extends the v0.1.0 AST baseline into a full code-to-diagram reverse engineering library. The core value proposition is deterministic, schema-compatible output: identical source input must produce byte-identical NormalizedArtifact JSON across runs, platforms, and Python versions. This determinism is not a quality-of-life concern -- it is a hard requirement because the upstream Layer M bisimulation (spec_code_verifier, architecture_verifier) uses this library output as one side of a formal equivalence check. Any non-determinism silently corrupts verification results.

The recommended architectural approach is hexagonal (Ports and Adapters) applied at the library level. A single Common AST View (CAV) -- an immutable Pydantic envelope produced once per source file by a language-specific Frontend -- replaces v0.1.0 four-reparse anti-pattern. All downstream extractors operate on the cached CAV rather than re-invoking the parser. An explicit dispatch table in _dispatch.py replaces decorator registries to guarantee ordering determinism. The ACL-2 Adapter layer is the sole location where subprocess may be called, and it enforces canonicalization (strip timestamps, sort output, pin-and-assert tool versions) at the boundary.

The dominant risks fall into two categories. First, two specification errors must be corrected before implementation begins: the spec references ACL-2 (the University of Texas Lisp theorem prover, unrelated to Python) where it means call-graph analysis, and callgraph.py which does not exist on PyPI; the correct replacements are pyan3 v2.6.0 and pyright[nodejs]==1.1.409. Second, six architecture-phase contracts must be locked before any extractor code is written. Retrofitting these contracts after parallel extractor development is rated HIGH recovery cost in the pitfall analysis.

---

## Key Findings

### From STACK.md

Recommended technologies with exact pins:

| Component | Package | Version | Rationale |
|-----------|---------|---------|-----------|
| C++ AST | libclang | ==18.1.1 | ABI-incompatible across LLVM versions; exact pin required; PyPI wheels unavailable for Python 3.13+ |
| Call graph | pyan3 | ==2.6.0 (GPL v2) | Only maintained PyPI call-graph library; install as optional [callgraph] extra |
| Type resolution | pyright[nodejs] | ==1.1.409 | Microsoft-maintained; JSON output via --outputjson; requires Node.js 18+ |
| Data validation | pydantic | >=2.13.0,<3.0 | Schema definition, serialization, validation |
| Lint/AST augmentation | pylint | >=3.3.0,<4.0 | Supplements stdlib ast for some extraction tasks |

Critical version constraint: requires-python >=3.11,<3.13 (forced ceiling by libclang wheel availability on PyPI)

Spec errors requiring correction before implementation:
- ACL-2 in the spec is the University of Texas Lisp theorem prover (https://www.cs.utexas.edu/~moore/acl2/); replace with pyan3
- callgraph.py does not exist on PyPI; replace with pyan3 v2.6.0

Subprocess determinism requirements (mandatory in all ACL-2 Adapter calls):
    subprocess.run([...], capture_output=True, timeout=N, env={**os.environ, 'LC_ALL': 'C', 'PYTHONHASHSEED': '0'}, encoding='utf-8')
Never use Popen + wait + read -- deadlock risk when pyright JSON output exceeds 64KB.

### From FEATURES.md

Table Stakes (must ship in v0.2.0):
- TS-1: Python AST extraction (functions, classes, imports, decorators)
- TS-2: Python call graph via pyan3
- TS-3: Python type resolution via pyright
- TS-4: C++ AST extraction via libclang (classes, functions, includes)
- TS-5: Class/Inheritance diagram extraction (all languages)
- TS-6: Component/Dependency diagram extraction
- TS-7: Sequence diagram extraction (linear, no branching)
- TS-8: FSM/State diagram extraction
- TS-9: Spec element extraction (requirements, constraints)
- TS-10: NormalizedArtifact output compatibility with lib-diagram-parser schema
- TS-11: Schema compatibility layer (KEYSTONE -- required by all diagram extractors)
- Linear sequence diagram (no branching)

Should Have (differentiators):
- DF-1: Incremental/cached parsing (hash-based invalidation)
- DF-2: Parallel frontend execution (thread pool, GIL-safe)
- DF-3: Cross-language call graph stitching
- DF-4: Generic/template specialization tracking (C++)
- DF-5: Decorator/annotation semantic extraction
- DF-6: Doxygen comment extraction for C++ (RECOMMENDED for promotion to Table Stakes)

Defer to v3+: DF-6 if not promoted; runtime call graph via tracing; IDE plugin integration

Anti-features (never implement):
- AF-1: Non-deterministic output under identical input
- AF-2: Re-parsing source files more than once per extraction run
- AF-3: Runtime import of lib-diagram-parser (schema duplication is structural, not runtime)
- AF-4: Mutable shared state in Extractors
- AF-5: Direct subprocess calls outside ACL-2 Adapter layer
- AF-6: Hardcoded tool paths (pyright, pyan3 must be resolved via shutil.which)
- AF-7: Output that varies by Python version or platform
- AF-8: Blocking the GIL during long extractions without timeout

### From ARCHITECTURE.md

5-layer hexagonal design:

1. Models layer (models/) -- immutable Pydantic dataclasses; EdgeKind enum; NormalizedArtifact envelope
2. Ports layer (ports/) -- abstract base classes; FrontendPort, ExtractorPort, DiagramExtractorPort
3. Frontend layer (frontends/) -- per-language CAV producers; PythonFrontend (ast module), CppFrontend (libclang)
4. Adapter/Extractor layer (adapters/, extractors/) -- operate on cached CAV; ACL-2 Adapters (subprocess boundary)
5. Orchestrator (orchestrator.py) -- composes pipeline; reads explicit dispatch table from _dispatch.py

8 major components: models/, ports/, frontends/, adapters/, extractors/, diagram_extractors/, spec_extractors/, _dispatch.py

Key architectural decisions:
- CAV produced once per file, cached, shared across all extractors (eliminates 4x re-parse anti-pattern)
- Explicit dispatch table (not decorator registry) -- static dict guarantees ordering determinism
- Structural schema duplication from lib-diagram-parser -- zero runtime coupling; drift caught by cross-lib contract test
- subprocess confined to ACL-2 Adapter layer only
- Critical path: models/ -> CAV schema -> Python Frontend -> functions extractor -> orchestrator skeleton

7 documented anti-patterns: decorator registry for extractor registration; re-parsing source per extractor; runtime import of lib-diagram-parser; mutable extractor state; subprocess outside adapter layer; hardcoded tool versions; skipping CAV and calling language parser directly from extractors

### From PITFALLS.md

Top 5 critical pitfalls:

| Pitfall | Severity | Prevention |
|---------|----------|-----------|
| Non-deterministic output from subprocess tools | CRITICAL | LC_ALL=C, PYTHONHASHSEED=0, encoding=utf-8 in all subprocess env; sort all collections before serializing |
| libclang ABI mismatch (wrong LLVM version) | CRITICAL | Pin libclang==18.1.1 exactly; assert clang.__version__ at import time; requires-python <3.13 |
| Schema drift between lib-code-parser and lib-diagram-parser | HIGH | Structural duplication (copy, not import); add cross-lib contract test in CI |
| pyan3 DOT output format changes across versions | HIGH | Pin pyan3==2.6.0; parse DOT via pydot; add fixture-based regression test |
| pyright JSON output exceeds 64KB causing deadlock | HIGH | Always use subprocess.run(capture_output=True, timeout=120); never Popen+wait+read |

Additional architecture-phase pitfalls (HIGH recovery cost if retrofitted):
- CAV schema not locked before parallel extractor development
- EdgeKind enum values added ad-hoc -- lock full enum in Phase 1 models
- FSM extraction without three-guard pattern: (a) field typed as Enum subclass, (b) method assigns to self.field, (c) guard on current value
- Sequence diagram extraction without call depth limit -- add max_depth parameter from Phase 4 start
- Missing timeout= in subprocess calls

---

## Implications for Roadmap

Research across all four files converges on a 4-phase structure driven by dependency ordering and architecture-phase contract requirements.

### Phase 1: Architecture Foundation and Schema Lock

Rationale: Six contracts must be immutable before any extractor code is written. Retrofitting after parallel extractor development costs HIGH recovery effort (per PITFALLS.md). This phase has no code deliverables beyond scaffolding -- its value is eliminating the six highest-recovery-cost pitfalls before they can occur.

Delivers:
- Corrected pyproject.toml with exact pins (libclang==18.1.1, pyan3==2.6.0, pyright[nodejs]==1.1.409)
- models/ package: NormalizedArtifact, EdgeKind enum (complete), CAV schema
- ports/ package: FrontendPort, ExtractorPort, DiagramExtractorPort abstract bases
- Structural schema copy from lib-diagram-parser + cross-lib contract test
- _dispatch.py skeleton with explicit dispatch table
- Subprocess determinism contract documented and enforced in adapter base class
- Spec error corrections documented (ACL-2 -> pyan3, callgraph.py -> pyan3)

Pitfalls addressed: P-1 (determinism), P-3 (schema drift), P-6 (CAV lock), P-7 (EdgeKind lock), P-11 (spec errors)
Research flag: Standard patterns -- skip deep research, implement directly from ARCHITECTURE.md

### Phase 2: Python Frontend + Aspect Extractors + ACL-2 Adapters

Rationale: Python is the primary language with no native-code integration complexity. All pure-Python extractors can be built and tested against the locked CAV schema. The ACL-2 Adapter layer (pyan3, pyright) is also pure-Python subprocess wrapping with well-defined contracts.

Delivers:
- PythonFrontend (stdlib ast to CAV producer)
- FunctionExtractor, ClassExtractor, ImportExtractor, DecoratorExtractor
- Pyan3Adapter (call graph; subprocess with canonicalization)
- PyrightAdapter (type resolution; subprocess with JSON capture)
- Full test suite for Python extraction

Pitfalls addressed: P-4 (pyan3 DOT regression), P-5 (pyright deadlock), P-10 (timeout enforcement), P-13 (missing decorators), P-15 (import resolution)
Research flag: Standard patterns for extractors; pyan3/pyright subprocess wrapping needs careful implementation per STACK.md

### Phase 3: C++ Frontend via libclang

Rationale: C++ frontend is isolated from Python extractors by the CAV boundary. It introduces native-code complexity (libclang ABI, compile_args contract) that should not block Python extraction work. SP-3 spike (libclang Python 3.12 compatibility verification) should run at Phase 3 start as a gate.

Delivers:
- SP-3 spike result: libclang 18.1.1 verified on target Python version
- CppFrontend (libclang clang.cindex to CAV producer)
- compile_args contract (how callers supply -I paths and -std flags)
- C++ class/function/include extractors

Pitfalls addressed: P-2 (libclang ABI), P-5 (timeout in clang Index calls), P-12 (compile_args missing)
Research flag: Needs --research-phase -- libclang Python bindings have sparse documentation; SP-3 spike gates the entire phase

### Phase 4: Diagram + Spec + FSM Extractors

Rationale: These extractors all depend on the locked CAV schema (Phase 1), the Python Frontend (Phase 2), and in the case of cross-language diagrams, the C++ Frontend (Phase 3). SP-1 and SP-2 spikes should run at Phase 4 start.

Delivers:
- SP-1 spike: sequence diagram max_depth bounding strategy confirmed
- SP-2 spike: FSM three-guard detection validated on real codebases
- ClassDiagramExtractor, ComponentDiagramExtractor
- SequenceDiagramExtractor (linear, with max_depth)
- FSMExtractor (three-guard pattern)
- SpecExtractor (requirements, constraints)

Pitfalls addressed: P-7 (EdgeKind completeness), P-8 (FSM false positives), P-9 (sequence depth), P-14 (spec element extraction)
Research flag: Needs --research-phase for FSM extraction and sequence diagram bounding; diagram extractors have limited prior art in Python ecosystem

---

## Critical Open Questions

The following questions must be answered during requirements definition before Phase 1 can begin:

1. Which exact lib-diagram-parser schema version is the compatibility target for TS-11? The structural duplication approach requires a pinned source schema. If lib-diagram-parser is under active development, a coordination protocol (who notifies whom of schema changes) must be established before the cross-lib contract test can be written.

2. Does the Layer M bisimulation consume NormalizedArtifact directly, or does it go through an intermediate adapter? This determines whether NormalizedArtifact must be the final output schema or whether a translation layer is acceptable.

3. What is the compile_args contract for C++ source files? The CppFrontend requires -I paths and -std flags to resolve includes. Who supplies these -- the caller, a config file, or a discovery heuristic? This gates the Phase 3 C++ Frontend design.

4. Is DF-6 (Doxygen comment extraction for C++) required for the downstream verifier in v0.2.0? FEATURES.md recommends promoting DF-6 to Table Stakes. If the verifier needs doc-comment data, this must be confirmed before Phase 1 schema lock.

5. What is the maximum acceptable extraction latency per file? This determines whether DF-1 (incremental/cached parsing) and DF-2 (parallel frontend execution) are required in v0.2.0 or can be deferred.

6. Is there an existing test corpus of Python and C++ source files with known ground-truth extraction outputs? The pitfall analysis (P-4, P-8) relies on fixture-based regression tests. If no corpus exists, Phase 1 must include corpus creation as a deliverable.

7. Who owns the cross-lib contract test -- lib-code-parser CI or lib-diagram-parser CI? The structural schema duplication approach requires at least one side to gate on schema diff. Ownership must be assigned before Phase 1 ends.

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|-----------|-------|
| Stack | HIGH | Exact version pins verified; spec errors definitively identified with authoritative sources; subprocess patterns well-documented |
| Features | MEDIUM-HIGH | Table stakes well-defined; TS-11 keystone dependency clearly established; DF-6 promotion is a judgment call requiring stakeholder confirmation |
| Architecture | HIGH | Hexagonal + CAV + explicit dispatch is an established pattern with clear tradeoffs documented; build order confirmed by dependency analysis |
| Pitfalls | HIGH | 15 pitfalls with severity/likelihood ratings derived from known failure modes in Python AST tooling; recovery cost estimates conservative |

Overall: HIGH -- sufficient to begin requirements definition and Phase 1 planning without additional research.

Gaps to Address:
- lib-diagram-parser schema version for TS-11 compatibility target (Open Question 1)
- compile_args contract for CppFrontend (Open Question 3)
- Test corpus existence for fixture-based regression tests (Open Question 6)
- DF-6 promotion decision (Open Question 4)

---

## Sources

Tier 1 (authoritative):
- PyPI package registry (libclang, pyan3, pyright, pydantic, pylint version data)
- University of Texas ACL2 project page (https://www.cs.utexas.edu/~moore/acl2/)
- Python stdlib ast module documentation
- libclang Python bindings documentation (LLVM project)
- pyright documentation (Microsoft)

Tier 2 (derived analysis):
- STACK.md -- technology selection with rationale and version compatibility table
- FEATURES.md -- feature landscape with dependency graph and anti-feature list
- ARCHITECTURE.md -- hexagonal design with component boundaries and build order
- PITFALLS.md -- 15 pitfalls with phase mapping and recovery cost ratings

Tier 3 (existing codebase):
- lib-code-parser v0.1.0 implementation (brownfield baseline)
- lib-diagram-parser schema (TS-11 compatibility target)