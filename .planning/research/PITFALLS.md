# Pitfalls Research

**Domain:** Deterministic multi-language code parser library (Python + C++ via libclang) with ACL-2 subprocess integration, diagram/FSM extraction, and cross-lib schema compatibility
**Researched:** 2026-05-24
**Confidence:** HIGH (libclang/subprocess/Pydantic schema findings verified against official docs and project issue trackers; FSM and call graph claims verified against academic papers)

> Scope reminder: the four anti-patterns already documented in `ARCHITECTURE.md` (`_get_module_name` duplication, AST re-parsed 4x, untyped `params`, `__post_init__` mis-tagging) are NOT re-researched here. They are tracked in `PROJECT.md` Active. This document covers the *new* pitfall surface introduced by v0.2.0 scope: libclang, subprocess integration, diagram extraction, FSM extraction, determinism in multi-language settings, and schema compatibility with sibling libs.

---

## Critical Pitfalls

### Pitfall 1: TranslationUnit / Index lifetime crash (libclang)

**Severity:** HIGH
**Likelihood:** HIGH — almost guaranteed if extractors return Cursor-derived data

**What goes wrong:**
A function builds a `clang.cindex.TranslationUnit`, walks the AST, returns a list of `Cursor` objects (or anything that internally holds a `Cursor`), and the caller crashes — sometimes immediately with a segfault, sometimes hours later under load when GC kicks in. The official libclang Python bindings explicitly warn: "client must hold on to index and translation unit, or risk crashes." Cursors, types, source locations, and diagnostics all reference memory owned by the `TranslationUnit`; once `tu` is garbage-collected the references dangle.

**Why it happens:**
Python developers assume Python's GC handles all reachability. But `clang.cindex` is a `ctypes` wrapper over a C library that has no idea what Python references exist. The natural Python pattern (`return [cursor for cursor in tu.cursor.walk_preorder()]`) silently drops the `tu` reference at function return, leaving the cursors pointing at freed memory.

**How to avoid:**
- **Extract eagerly inside the parse boundary.** The `cpp_extractor` module should *never* return `Cursor` or `Type` objects across the module boundary. Convert to plain Pydantic models (strings, ints, lists) before the `TranslationUnit` goes out of scope.
- **Hold the `Index` for the process lifetime.** Create one `clang.cindex.Index` per `CppExtractor` instance (or process-global) and reuse it. Disposing the Index between calls is both slower and crash-prone.
- **Document the contract in the extractor docstring**: "Caller receives plain data only; no libclang handles escape this module."
- **Write a test that explicitly triggers GC** between parse and assertion: `tu = parse(...); result = extract(tu); del tu; gc.collect(); assert_things_about(result)`. This catches lifetime bugs that pass under normal test ordering.

**Warning signs:**
- Intermittent segfaults that disappear when adding `print` statements (the print extends an object's lifetime)
- Crashes that surface only when parsing multiple files in a loop (each iteration GCs the previous TU)
- Crashes only on CI but not locally (different GC timing)
- Tests pass when run individually, fail when run together

**Phase to address:**
**Architecture phase** — the rule "no libclang handles escape the cpp_extractor module" must be in the architecture contract before any code is written. Adding it later means auditing every cursor-returning function.

---

### Pitfall 2: libclang version / ABI drift across environments

**Severity:** HIGH
**Likelihood:** HIGH — different developers on different OSes

**What goes wrong:**
Developer A installs `pip install libclang==16.0.6` on Linux and everything works. Developer B on Windows installs the same package but the underlying `libclang.dll` they pulled in is from a different LLVM release, and they get `OSError: symbol not found: clang_getCursorPrettyPrinted` (added in clang 13) or, worse, silently different AST cursor kind enum values because clang 15 broke ABI without bumping SOVERSION (llvm-project#60270). CI passes on Linux; reviewer's Mac shows different `node_id`s in golden tests. Reproducibility — the whole point of the library — collapses.

**Why it happens:**
- The `libclang` PyPI package bundles a libclang shared library, but users may also have a system `libclang` that gets loaded depending on `LD_LIBRARY_PATH` / DLL search order.
- `clang.cindex.Config.set_library_file(...)` is global mutable state; if anything (a test, a dev tool, the IDE) sets it differently, the library binds to a different version.
- Clang 15 changed `CXCursor_TranslationUnit` without bumping the SOVERSION (llvm-project#60270), so the same Python code linked against the "compatible" `.so` returns different cursor kind ints.
- Wheels on PyPI carry a specific LLVM revision; pinning `libclang==16.0.6` does NOT pin LLVM itself, only the PyPI wrapper.

**How to avoid:**
- **Pin the `libclang` PyPI version exactly** in `pyproject.toml`, with a comment recording the bundled LLVM version (e.g., `libclang==16.0.6  # LLVM 16.0.6`).
- **At process start, log/assert the loaded library path and clang version.** Provide a `cpp_extractor.environment_fingerprint() -> dict` that returns `{libclang_path, clang_version, platform}` and write a smoke test that asserts the expected version.
- **Never call `Config.set_library_file` from library code.** If a caller wants to override, they do it before importing.
- **Forbid relying on raw cursor-kind ints in serialized output.** Always normalize to strings (`cursor.kind.name`) before they reach `node_id` or any persistent field.
- **CI matrix**: Linux + macOS + Windows with identical `libclang` pin. Golden tests for C++ must produce byte-identical output across all three.

**Warning signs:**
- A test produces different output on a teammate's machine
- `OSError` / `AttributeError` for cursor-kind names that exist in newer LLVM
- Golden fixture diffs appear after a `pip install --upgrade` of unrelated package
- `clang.cindex.LibclangError` mentioning symbol resolution

**Phase to address:**
**Language frontend phase (C++)** — pin and fingerprint at the moment libclang is first introduced.

---

### Pitfall 3: subprocess deadlock when pyright/callgraph.py produce large output

**Severity:** HIGH
**Likelihood:** HIGH — pyright JSON for a medium project routinely exceeds 64 KB

**What goes wrong:**
The extractor does `proc = subprocess.Popen([pyright, "--outputjson", path], stdout=PIPE, stderr=PIPE); proc.wait(); out = proc.stdout.read()`. On small files this works. On any real project pyright's JSON exceeds the OS pipe buffer (typically 64 KB on Linux, 4 KB on Windows). The child blocks writing to a full stdout pipe; the parent blocks on `wait()`. Deadlock. The library hangs forever and the caller has no idea why.

**Why it happens:**
Standard `Popen` + `wait` + `read` is the textbook wrong pattern, documented as a deadlock hazard in the Python stdlib docs since at least Python 2. Developers reach for it because it looks simple, especially when stderr is "expected to be small."

**How to avoid:**
- **Always use `subprocess.run(..., capture_output=True, timeout=N)` or `Popen.communicate(timeout=N)`.** Both internally use threads/select to drain both pipes concurrently.
- **Always set a timeout** (e.g., 60 s for pyright, 30 s for callgraph.py). A hung subprocess must surface as a `TimeoutExpired` exception, not as a frozen library.
- **Use `encoding="utf-8", errors="replace"`** explicitly. Default text decoding uses the locale codec which is non-deterministic across machines (CP1252 on Windows, UTF-8 on Linux).
- **Never use `shell=True`** — both a security and a determinism issue (different shells interpret arguments differently).
- **On timeout, kill the entire process tree** (use `psutil` or `os.killpg`) — pyright may have spawned its own helper processes that survive the parent kill.

**Warning signs:**
- The library appears to hang on large input files
- CI tasks for the parser exceed their wall-clock limits
- Memory usage of the pyright/callgraph child grows unboundedly (parent draining one pipe but not the other)
- Process tree shows orphaned pyright/callgraph processes after a test failure

**Phase to address:**
**ACL-2 integration phase** — fixed by the very first subprocess wrapper. Make the wrapper a single internal utility (`_run_acl2_tool`) so the right pattern is used everywhere.

---

### Pitfall 4: pyright / callgraph.py JSON schema drift between versions

**Severity:** HIGH
**Likelihood:** MEDIUM — known to have happened at least once for pyright

**What goes wrong:**
The team writes `result["generalDiagnostics"][0]["file"]` to extract the file path from pyright's JSON. Six months later, CI starts failing across all environments — pyright shipped 1.1.340, which replaced `file: str` with `uri: str` in `generalDiagnostics` (microsoft/pyright#6740, December 2023). Every downstream consumer of the parser breaks at the same time. Worse, if the schema change is *additive* (a new optional field), the parser may silently produce wrong output for months.

**Why it happens:**
External tool authors don't consider their JSON output to be a public API in the same way library authors treat function signatures. Pyright explicitly does not version its JSON schema. callgraph.py is a research-grade tool with even weaker stability guarantees. Schema-validated parsing protects against this; raw dict indexing does not.

**How to avoid:**
- **Define a Pydantic model for each external tool's output and parse with it.** When the schema changes, you get a `ValidationError` at parse time, not silent corruption six layers down.
- **Pin tool versions exactly** in `pyproject.toml`. Pyright bumps weekly; pin to a specific release (e.g., `pyright==1.1.401`) and treat upgrades as a deliberate change with a regression test.
- **Maintain golden fixtures**: store the full JSON output of each tool against a small reference codebase. CI re-runs and diffs. Any drift surfaces immediately.
- **Use a schema-version probe**: on first invocation, run `pyright --version` and assert it matches the pinned version. Emit a clear error ("This library was built against pyright 1.1.401; you have 1.1.452. Update the parser or downgrade pyright.").

**Warning signs:**
- Empty extraction results where there used to be content (new field name that the parser ignores)
- `KeyError` after a routine `pip install -U`
- Differences in output across CI / dev / prod that correlate with installed pyright versions

**Phase to address:**
**ACL-2 integration phase** — Pydantic models for tool output must exist from day one.

---

### Pitfall 5: Non-determinism from libclang's environment-dependent parsing

**Severity:** HIGH
**Likelihood:** HIGH for C++; this is the canonical libclang gotcha

**What goes wrong:**
The same `.cpp` file parsed on machine A produces 12 `FunctionNode`s; on machine B it produces 8. Reason: libclang ran with different include paths (the developer's `/usr/include` differs), so some headers couldn't be resolved, some templates couldn't be instantiated, and some declarations were silently dropped. Layer M bisimulation across machines fails. The library is no longer deterministic in the sense required by the Core Value.

**Why it happens:**
libclang behaves like a real C++ compiler. C++ parsing depends on:
- Include path resolution (system headers, compiler-shipped headers, project headers)
- Preprocessor definitions (different `-D` flags → different active branches; libclang only parses the active branch)
- C++ standard version (`-std=c++17` vs `c++20` → different AST nodes)
- Target triple (different architectures → different `size_t`, different builtins)
- The presence/absence of a `compile_commands.json`

Default arguments differ across LLVM packagings and OSes. Without explicit control, the AST is a function of the developer's machine.

**How to avoid:**
- **Pass an explicit, machine-independent compile command** every time. Never rely on libclang defaults. At minimum: `["-x", "c++", "-std=c++20", "-nostdinc++", "-isysroot", "<bundled>"]`.
- **Require the caller to supply `compile_args: list[str]`** in `ParserConfig.params` for C++. Refuse to parse if absent (or default to an explicit minimal set and document it loudly).
- **Treat parse diagnostics as part of output.** Surface unresolved-include warnings as `CodeContent.diagnostics`. If they differ across machines, the user knows.
- **Don't try to be smart about includes.** Document: "This library does not search for headers. If your code uses `<vector>`, supply the include path explicitly or accept that templates may not instantiate."
- **Add a determinism test**: parse the same fixture on Linux/macOS/Windows in CI and `diff` the output. Treat any diff as a release blocker.

**Warning signs:**
- Output differs across teammates' machines on the same input
- Some `FunctionNode`s have `return_type=None` on one machine and a real type on another
- `CodeContent.diagnostics` (if exposed) contains "file not found" only on some platforms

**Phase to address:**
**Language frontend phase (C++)** — the `compile_args` contract has to be defined before any C++ code is written. Retrofitting it means changing the public API.

---

### Pitfall 6: Schema drift between lib-code-parser and lib-diagram-parser

**Severity:** HIGH
**Likelihood:** HIGH — independent evolution of sibling libs is the default failure mode

**What goes wrong:**
At v0.2.0 release, `lib-code-parser.ClassDiagram` and `lib-diagram-parser.ClassDiagram` are structurally identical and the `architecture_verifier` happily diffs them. Three months later, `lib-diagram-parser` adds a `stereotypes: list[str]` field; six months later `lib-code-parser` adds `cyclomatic_complexity: int` on `ClassNode`. Both add fields independently as "optional" — neither breaks alone. But the verifier now sees two non-isomorphic shapes and bisimulation fails for reasons that have nothing to do with spec/code divergence. The Core Value silently degrades.

**Why it happens:**
- The two libs live in separate repos (or at least separate packages) and ship independently.
- "Optional field, backward compatible" is true for *each lib in isolation* but not for the *shared schema*.
- No automated check enforces structural compatibility.
- Pydantic's `extra="ignore"` by default hides the drift — diff just silently ignores unknown fields rather than flagging them.

**How to avoid:**
- **Extract the shared schema into a third package** (e.g., `lib-architecture-schema` or `spec_reviewer_schemas`) that both libs depend on. Neither lib defines `ClassDiagram` locally.
- If a separate package is too heavyweight initially, **vendor an identical Pydantic model file** in both repos and add a CI check that `diff` the file across repos.
- **Set `model_config = ConfigDict(extra="forbid")`** on shared diagram models. Any unknown field surfaces as a `ValidationError` immediately, not silently.
- **Version the shared schema explicitly** with a `schema_version: Literal["1.0"]` field that both libs assert on.
- **A cross-lib contract test** (run in CI of *both* libs): construct a fixture from one lib, validate it with the other lib's model. Failure = drift.

**Warning signs:**
- The two libs' `models.py` start to differ on field names (`source` vs `from_node`)
- `architecture_verifier` reports "shape mismatch" for files that previously matched
- Adding a field to one lib does not cause review of the other lib
- Either lib's tests do not import the other lib's types

**Phase to address:**
**Schema / architecture phase** — has to be settled before any diagram code is written.

---

### Pitfall 7: Diagram edge semantics ambiguity ("uses" vs "depends" vs "references")

**Severity:** HIGH
**Likelihood:** HIGH — almost every diagram tool gets this wrong initially

**What goes wrong:**
The class diagram extractor emits an edge from `OrderService` to `Logger`. Is that edge:
- An association (field of type `Logger`)?
- A dependency (parameter of type `Logger`)?
- A usage (calls `Logger.log()` inside a method)?
- All three?

If the parser collapses them into one "uses" edge, the diagram cannot be compared to the spec diagram (which had a precise "Aggregation" arrow). If it emits three separate edges between the same nodes, the verifier sees a multigraph and bisimulation explodes combinatorially. If it picks one arbitrarily, the choice differs between Python (where everything looks like an "uses") and C++ (where the type system distinguishes), breaking cross-language consistency.

**Why it happens:**
UML and source code don't have a 1:1 mapping. Source code has facts (a field, a call, a parameter); UML has interpretations (association, dependency, composition). The mapping is a *policy decision* that must be made explicitly.

**How to avoid:**
- **Define a fixed edge taxonomy as an enum in the shared schema**: `EdgeKind = Literal["inherits", "implements", "field_of", "param_of", "returns", "calls", "instantiates"]`. No "uses" catch-all.
- **Emit one edge per (source, target, kind) triple**, with multiplicity preserved as a count if needed. Never collapse different kinds.
- **Map source-level facts to edge kinds with a documented rule table**, identical for Python and C++. The rule table is part of the architecture contract.
- **Let the verifier decide which kinds to compare** — the parser must not make that decision.
- **Test cross-language consistency**: a hand-written Python class and a hand-written C++ class that model the same UML must produce isomorphic edge sets (modulo language-specific kinds like `friend`).

**Warning signs:**
- The `EdgeKind` enum starts gaining "uses" / "other" / "misc" values
- Reviewer asks "why is this an inherits edge?" and the answer requires reading the extractor source
- The same logical relationship gets different `EdgeKind` in Python and C++

**Phase to address:**
**Diagram phase architecture** — edge taxonomy must be locked before any extractor is written.

---

### Pitfall 8: FSM extractor false positives from non-state-machine enums

**Severity:** MEDIUM
**Likelihood:** HIGH — most Python enums are not state machines

**What goes wrong:**
The extractor sees `class Color(Enum): RED, GREEN, BLUE` and a method `def darken(self, c: Color) -> Color`. The pattern (enum + method returning enum) matches "FSM transition method". The extractor emits a 3-state, 9-transition FSM that has nothing to do with any state machine in the system. The state diagram output is polluted with garbage FSMs, the verifier compares them against a spec that has no such machine, and the bisimulation fails not because of a real divergence but because the parser hallucinated structure.

**Why it happens:**
"Enum + transition method" is necessary but very far from sufficient for "this is an FSM". Real FSMs have:
- A privileged "current state" attribute on an instance
- Transition methods that *mutate* that attribute
- A bounded, total transition function (not all (state, event) combinations are valid)

Color examples, request priority enums, and most flag enums all match the surface pattern.

**How to avoid:**
- **Restrict the "must-have" FSM extractor to highly explicit patterns only**:
  1. A class has a field whose type is an `Enum` subclass
  2. At least one method assigns to `self.<that field>` with a value of the enum type
  3. The method's body shows a guard on the current value (e.g., `if self.state == X: self.state = Y`)
  All three must hold. Anything weaker goes to the spike pile.
- **Emit a confidence score or, better, a `FSMExtractionReason: Literal["explicit_state_field", "transition_table", "decorator_pattern"]`** so the verifier can filter.
- **Treat the spike (generic control-flow FSM extraction) as separate** and ship it disabled-by-default until the explicit-pattern path has run in production for a milestone.
- **Document the negative test cases** — `Color(Enum)`, `LogLevel(Enum)`, `Priority(Enum)` must produce zero FSMs. Add them as fixtures.
- **Per the FSMExtractor paper (Chen et al., 2019)** — even careful static analysis on 160 programs produced only 2 false positives. Without their precise guards (state variable mutation + control-flow transition table), false-positive rates will be much higher.

**Warning signs:**
- The FSM list contains classes that nobody on the team thinks of as state machines
- The number of extracted FSMs grows linearly with the number of enums in the codebase
- The spec verifier reports many "extra states in code" failures
- The FSM has all-to-all transitions (real FSMs are sparse)

**Phase to address:**
**Diagram phase (FSM sub-phase)** — the pattern definition is the deliverable, not the code that implements it.

---

### Pitfall 9: Method overloading and overriding hide state changes from FSM detection

**Severity:** MEDIUM
**Likelihood:** MEDIUM — common in OO codebases with inheritance

**What goes wrong:**
A base class `Connection` has `def open(self): self.state = OPEN`. A subclass `SecureConnection` overrides `open` but does not assign to `self.state` (relying on `super().open()` to do it). The FSM extractor walks `SecureConnection`'s methods, sees `open` doesn't assign to `self.state`, and concludes `SecureConnection` has fewer transitions than `Connection`. Worse, C++ method overloading (same name, different signatures) can produce two `open(int)` and `open(string)` methods where only one mutates state — the extractor either picks one arbitrarily or merges them.

**Why it happens:**
Static AST analysis sees only the lexical method bodies. It doesn't follow `super()` calls or virtual dispatch. Detecting transitions across an inheritance hierarchy requires a flow-sensitive analysis the parser deliberately avoids.

**How to avoid:**
- **For FSM extraction, work on the *fully resolved* class** — flatten the inheritance chain and analyze the union of methods. Mark transitions discovered in a parent as belonging to the child.
- **Record `super()` calls explicitly as part of the transition** — `transition: super_call_chain + own_assignments`.
- **For C++, use libclang's `CXXMethodDecl::overloads`** to detect overloaded transition methods; emit one transition per overload with the parameter types as guards.
- **Document the limitation**: "If state mutation happens via callback/strategy pattern (not via direct assignment or super call), it will not be detected. Use the explicit-state-machine library annotation as a workaround."
- **Test**: a 3-deep inheritance chain where each level adds a transition. Verify the leaf class shows the union.

**Warning signs:**
- Subclasses appear as FSMs with fewer transitions than their parents
- Tests pass for single-class FSMs but fail for inherited ones
- C++ overloaded transition methods produce duplicate or missing transitions

**Phase to address:**
**Diagram phase (FSM sub-phase)** — inheritance handling is a separate concern from pattern recognition.

---

### Pitfall 10: Static call graphs systematically over- or under-approximate Python's dynamism

**Severity:** MEDIUM
**Likelihood:** HIGH for any non-trivial Python codebase

**What goes wrong:**
The codebase has `handler = HANDLERS[event_type]; handler(payload)`. A static call graph either:
- (under-approximation) emits no edge for `handler(payload)` because the callee is unknown → spec verifier reports "spec mentions X.handle but code never calls it" — false negative
- (over-approximation) emits edges to every callable that could possibly be in `HANDLERS` → spec verifier reports "code calls 47 things spec doesn't mention" — false positive

Same problem with: decorators that return a different function (`@staticmethod` applied via factory), `getattr(obj, name)()`, `functools.partial`, `*args` forwarding, and metaclass-injected methods.

**Why it happens:**
"Given the dynamic nature of Python, accurate call-graphs are impossible without full type inference" (Gopinath, 2022). Even with type inference (pyright + callgraph.py), Python's `getattr`, `__getattr__`, and runtime patching remain genuinely undecidable statically.

**How to avoid:**
- **Be explicit about the analysis precision**: the parser advertises "type-resolved static call graph; dynamic dispatch via `getattr`/string lookup is not tracked". Document this in the README and in the model docstring.
- **Emit edges with a confidence/source field**: `CallEdge(caller, callee, source: Literal["direct_call", "method_call_resolved", "decorator_chain"])`. Verifier can filter by source.
- **Surface unresolved calls as a separate output**: `CallGraph.unresolved_call_sites: list[SourceRange]`. The verifier knows where it's blind.
- **For Python, prefer `callgraph.py` over hand-rolled AST analysis** for resolved edges — it does fixed-point alias analysis. Use AST only for trace metadata (line numbers, comments).
- **Document the false-negative / false-positive expectation in tests**: e.g., a test that confirms `HANDLERS[x]()` produces *no* edge, so the verifier knows not to expect one.

**Warning signs:**
- Spec verifier reports many "missing call" or "extra call" failures on code that looks correct
- Call graph has zero edges out of a function that obviously calls things (over-pruning)
- Call graph has edges between functions that never actually call each other (alias over-approximation)

**Phase to address:**
**ACL-2 integration phase (callgraph.py)** — precision policy is set at the boundary between callgraph.py output and `CallGraph` model.

---

### Pitfall 11: Line-ending and Unicode normalization breaks source positions

**Severity:** MEDIUM
**Likelihood:** HIGH — guaranteed if anyone develops on Windows

**What goes wrong:**
The parser stores `source_range = (line, col_start, col_end)`. A Linux developer commits a file with LF line endings; CI runs on Windows where git autocrlf converts to CRLF on checkout. Same source content but byte offsets shift. If the parser uses byte offsets (libclang's default `clang_getCursorExtent` returns byte offsets), every range is off. If the parser uses line/column from libclang while the verifier uses Python `ast` line/column on a different line-ending normalization, ranges silently disagree. Determinism dies.

Unicode is worse: a file with `café` written as NFC (`U+00E9`) vs NFD (`U+0065 U+0301`) produces different column counts in libclang vs Python `ast`. Trace tag regex matching can also break depending on normalization.

**Why it happens:**
- libclang and Python's `ast` use different position conventions (libclang gives offsets; `ast` gives 1-indexed lines).
- Git's `core.autocrlf` rewrites files on checkout.
- UTF-8 + Unicode normalization is not enforced — files can be NFC, NFD, NFKC, or mixed.
- The codebase already silently substitutes invalid UTF-8 with `errors="replace"` (executor.py:59) which masks problems.

**How to avoid:**
- **Normalize the source bytes at the executor boundary** before any extractor sees them:
  1. Decode with `errors="replace"` (already done), then
  2. Normalize line endings to `\n` (`source = source.replace("\r\n", "\n").replace("\r", "\n")`)
  3. Normalize Unicode to NFC (`unicodedata.normalize("NFC", source)`)
- **Document the normalization in the schema**: positions in `source_range` always refer to NFC-normalized, LF-only source. Round-tripping to original requires a separate offset map (out of scope).
- **Configure `.gitattributes`** with `* text=auto eol=lf` for the parser's own fixtures.
- **Add a determinism test**: same source content with CRLF, LF, NFC, NFD → identical `NormalizedArtifact` output.
- **Remove the `errors="replace"` default** or surface it: if non-UTF-8 bytes appear, return a diagnostic, don't silently replace.

**Warning signs:**
- `source_range` differs between Linux and Windows runs of the same test
- Trace tags `Traces: FR-01` not detected in some files but visible to the eye
- Golden test diffs show only whitespace / position changes after a Windows developer commits

**Phase to address:**
**Architecture phase** — the normalization policy belongs in the executor, before any extractor runs. Must be defined before extractors start writing position-handling code.

---

### Pitfall 12: libclang AST surprises with templates, macros, friend, multiple inheritance

**Severity:** MEDIUM
**Likelihood:** HIGH — any real C++ codebase has these

**What goes wrong:** Several distinct failure modes:

1. **Templates not instantiated**: `template<class T> class Foo { void bar(T x); };` — libclang gives you a `ClassTemplate` cursor, not a `ClassDecl`. `bar`'s parameter type is `T`, not the resolved type. If you treat this like a regular class, you get a `ClassNode` with one method whose signature is meaningless. Specializations (`Foo<int>`) are separate cursors; the parser may emit them as additional classes or miss them entirely.

2. **Macros invisible**: `#define BEGIN_INTERFACE(name) class name { public:` — libclang parses what the preprocessor produced. The `name` symbol appears in the AST without any cursor pointing back to `BEGIN_INTERFACE`. Trace tags inside macro bodies are lost.

3. **Anonymous namespaces**: cursors inside `namespace { ... }` have `spelling == ""`. `node_id` construction that joins `parent.spelling` produces collisions for everything in any anonymous namespace.

4. **Friend declarations**: `friend class Bar;` appears as a `CXCursor_FriendDecl` whose child is a typeref, not a real class declaration. Naive extractors emit a phantom `Bar` class.

5. **Multiple inheritance**: a `ClassDecl` has multiple `CXX_BASE_SPECIFIER` children. The parser must emit *multiple* inheritance edges from the child class, not one merged edge. Virtual inheritance adds a `is_virtual=True` attribute the schema may not have.

6. **Preprocessor conditional code**: libclang parses only the *active* branch. Code inside an `#if 0` block is invisible. If the active branch depends on a macro the caller didn't define, half the code disappears.

**Why it happens:**
libclang exposes the *compiler's* view of C++. The compiler resolves preprocessing, picks active branches, leaves uninstantiated templates abstract, and treats friend/anonymous as first-class. Extractors written for Python (where each `class` keyword is one class) misinterpret all of these.

**How to avoid:**
- **Maintain a C++ AST-surprise checklist** in the test suite. For each surprise, a minimal fixture and an assertion about what the parser produces.
- **For templates**: emit `ClassNode` only for `CXCursor_ClassDecl` (concrete), not `ClassTemplate` (definition). Emit specializations as separate classes with a `template_args: list[str]` field.
- **For anonymous namespaces**: synthesize a deterministic ID using the source location (`__anon_<file>_<line>`).
- **For friend**: skip `FriendDecl` cursors unless they introduce a *definition* (not just a forward).
- **For multiple inheritance**: enumerate all `CXX_BASE_SPECIFIER` children, emit one edge each, preserve `access_specifier` and `is_virtual`.
- **For preprocessor**: require the caller to specify a canonical macro configuration in `compile_args`. Document that `#if`-branched code outside the active configuration is not parsed (this matches pyright's behavior on Python's `TYPE_CHECKING` blocks).
- **For macros**: do not attempt to extract trace tags from inside macro bodies. Restrict trace-tag scanning to source code, not macro-expanded code.

**Warning signs:**
- A C++ file produces fewer classes than expected — likely templates/conditionals
- `node_id` collisions (multiple nodes with same ID) — likely anonymous namespaces
- "Phantom" classes appearing in the diagram that don't exist as definitions — friend decls
- Inheritance edges missing for multiply-inherited classes

**Phase to address:**
**Language frontend phase (C++)** — the fixture checklist is part of the C++ extractor's definition of done.

---

### Pitfall 13: Encoding mismatches in subprocess output (Windows-specific)

**Severity:** MEDIUM
**Likelihood:** HIGH — anyone running tests on Windows

**What goes wrong:**
`subprocess.run([pyright, "--outputjson", path], capture_output=True, text=True)` on Windows decodes stdout with `cp1252` (the system codec), not UTF-8. Pyright's JSON contains a path like `C:\src\café.py` — the `é` byte sequence is misinterpreted, `json.loads` either fails or silently produces a wrong path string. The parser emits a `node_id` containing mojibake. Cross-platform determinism is broken at the subprocess boundary, independently of every other determinism control.

**Why it happens:**
`subprocess.run(..., text=True)` uses `locale.getpreferredencoding(False)`. On Windows Python <3.15 this is the system ANSI codepage (cp1252 in most Western locales), not UTF-8. PEP 686 (UTF-8 mode by default) is opt-in until Python 3.15.

**How to avoid:**
- **Always pass `encoding="utf-8", errors="strict"` explicitly** to `subprocess.run`. If a tool actually emits non-UTF-8 (rare), use `errors="replace"` and log it.
- **Pass paths to subprocesses with `os.fspath()` and pre-normalize to absolute paths.** Avoid relative paths that get re-resolved by the child against a different CWD.
- **Run the test suite on Windows in CI** with a non-ASCII path fixture (`tests/fixtures/café.py`). If it doesn't break, the encoding is locked.
- **For pyright/callgraph.py invocation, set `PYTHONIOENCODING=utf-8` in the child env** as belt-and-suspenders.

**Warning signs:**
- Tests pass on Linux/macOS, fail on Windows with `UnicodeDecodeError`
- Output `node_id` contains `Ã©` instead of `é`
- `json.loads` raises on Windows but not other platforms

**Phase to address:**
**ACL-2 integration phase** — the subprocess wrapper sets encoding explicitly; once set everywhere, this is solved.

---

### Pitfall 14: Cursor child ordering and dict iteration order leak into output

**Severity:** MEDIUM
**Likelihood:** MEDIUM — subtle, surfaces after refactor

**What goes wrong:**
The extractor builds `params: dict[str, ParamInfo]` from libclang cursor children. Cursor children come in source order (deterministic), but at some point the extractor does `set(...)` for deduplication or `sorted_by_something` with an unstable key — and the output ordering becomes a function of Python's hash seed (`PYTHONHASHSEED`). Two runs in the same process produce identical output; runs in fresh interpreters produce different orderings. CI golden tests fail intermittently.

Similar trap: `pyright`'s JSON output ordering is not guaranteed; iterating its diagnostics in returned order propagates non-determinism.

**Why it happens:**
- Python dicts preserve insertion order since 3.7, but `set` and `frozenset` do not.
- `PYTHONHASHSEED` is randomized by default for security.
- External tools (pyright, callgraph.py) may not guarantee output ordering.

**How to avoid:**
- **Sort every collection on the way out** of an extractor by a stable, content-derived key. For `FunctionNode` lists: sort by `(source_range.start_line, source_range.start_col, node_id)`. For edges: sort by `(source, target, kind)`.
- **Never use `set` for ordered output.** Use a list with explicit dedup (`seen = []; for x in items: if x not in seen: seen.append(x)`).
- **Add a determinism test that runs the parser twice in separate subprocesses** (so they have different hash seeds) and diffs the output. CI must run this every PR.
- **Set `PYTHONHASHSEED=0` in test infra** as a backstop, but do NOT rely on it for production determinism — pip users won't have it set.

**Warning signs:**
- CI golden tests fail intermittently with field-order-only diffs
- Output is identical within a session but differs after restart
- Two consecutive `pytest` runs produce different file outputs

**Phase to address:**
**Architecture phase** — the "every collection sorted on exit" rule is an architecture invariant. Easier to enforce from day one than retrofit.

---

### Pitfall 15: Pyright reports type errors that the parser misinterprets as missing types

**Severity:** LOW
**Likelihood:** MEDIUM — depends on user code quality

**What goes wrong:**
Pyright is asked for `TypeDep` info on code that has type errors (missing imports, unresolved references). Pyright still emits JSON but with `"type": "Unknown"` or `"type": "Unbound"`. The parser writes these into `TypeDep.target_type = "Unknown"`, treating "Unknown" as a real type name. The verifier sees "code declares dependency on type Unknown" and reports a spurious mismatch.

Also: pyright exit codes 1 (type errors found) vs 2-4 (tool failure) get treated identically by a naive wrapper. Exit 1 is normal — the user's code has type errors — but the parser may abort and produce no output.

**Why it happens:**
Tool exit codes are not standardized; pyright uses 1 for "found problems" rather than the typical "tool failure". Pyright's JSON sentinel values for unresolvable types are not advertised as such.

**How to avoid:**
- **Whitelist pyright exit codes**: `0` = clean, `1` = clean (just had type warnings), `2-4` = tool failure → raise.
- **Filter sentinel type strings**: maintain a `_PYRIGHT_UNRESOLVED = {"Unknown", "Unbound", "Never"}` set and drop `TypeDep` entries whose target is in it (or mark them with `resolved=False`).
- **Test against intentionally type-broken Python** to confirm sentinel handling.

**Warning signs:**
- `TypeDep` output contains literal `"Unknown"` as type
- Parser aborts on code that obviously has type errors (instead of returning a partial result)
- Verifier reports many type-mismatch failures on the same target name

**Phase to address:**
**ACL-2 integration phase (pyright)** — handled by the pyright wrapper.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Pass `Cursor` objects across module boundaries instead of converting to Pydantic | Less code in extractor; "we'll convert later" | Lifetime crashes (Pitfall 1); cannot serialize for tests; downstream code accidentally depends on libclang API | Never |
| `subprocess.run(...)` without `timeout=` | Simpler call sites | Library hangs forever on malformed input or large output; impossible to debug in production | Never for ACL-2 tools |
| Share Pydantic models by copy-pasting between repos | No new package to publish/version | Pitfall 6 schema drift; every change is two-place edit; review burden | Acceptable for v0.2 if `gh actions` cross-repo diff check is in place; not acceptable past v0.3 |
| Hardcode libclang compile args inside the extractor | Caller doesn't need to think about it | Cannot parse real-world C++ that needs `-I` or `-D`; non-determinism across LLVM versions | Acceptable for the v0.2 "self-contained C++ fixture" tests only; never for production |
| Allow "Unknown" as a literal type string in `TypeDep` output | Doesn't require special handling | Verifier sees pyright-internal sentinel as a real type; spurious mismatches | Never |
| Ship the FSM extractor without a confidence/reason field | Smaller schema, simpler models | Cannot filter out false positives downstream; whole feature gets disabled by users | Never |
| Single `EdgeKind = "uses"` catch-all in diagrams | Faster to ship | Cannot compare with spec diagrams; verifier collapses signal | Never |
| Use Python `set` for ordering deduplication | One-line dedup | `PYTHONHASHSEED`-dependent output; intermittent test failures | Never in extractor output paths |
| Skip Unicode normalization, rely on developers committing only ASCII | Less code | Pitfall 11; cross-platform determinism breaks the moment a non-ASCII identifier appears | Never |
| Bind to system libclang via `Config.set_library_file` for "real-world" tests | Tests cover what users actually have | Pitfall 2; non-reproducible CI; "works on my machine" | Never; pin the PyPI wheel |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `clang.cindex.TranslationUnit` | Return cursors/types to caller; let `tu` get GC'd | Extract eagerly to plain Pydantic models inside the same function; keep `Index` alive for the extractor's lifetime |
| `clang.cindex.Index` | Create a new `Index` per parse call | Create once per `CppExtractor` instance; reuse for the process lifetime |
| `libclang` PyPI wheel | Trust whatever gets installed; don't pin LLVM version | Pin to a specific version with comment recording bundled LLVM; assert at process start |
| `pyright` subprocess | `Popen` + `wait` + `read` | `subprocess.run(..., capture_output=True, timeout=60, encoding="utf-8")`; raise on timeout; pin pyright version |
| `pyright` JSON output | `result["generalDiagnostics"][0]["file"]` raw dict indexing | Parse with a Pydantic `PyrightOutput` model; pin pyright version; golden fixture in CI |
| `pyright` exit codes | Treat exit 1 as failure | Whitelist `{0, 1}` as success; only `2,3,4` are tool failures |
| `callgraph.py` subprocess | Assume stable JSON schema | Pydantic model + pinned version; golden fixture |
| Subprocess on Windows | Default text mode (cp1252 decode) | `encoding="utf-8", errors="strict"` explicit; `PYTHONIOENCODING=utf-8` in child env; CI fixture with non-ASCII path |
| `lib-diagram-parser` schema | Each lib defines its own `ClassDiagram` model | Shared schema package (or vendored-with-diff-check); `extra="forbid"`; explicit `schema_version` |
| C++ `compile_args` | Rely on libclang defaults | Require caller to specify; minimal explicit set documented |
| Source content (line endings) | Trust git checkout | Normalize CRLF → LF and NFC at executor entry |
| Pydantic `extra` config on shared models | Default `extra="ignore"` | `extra="forbid"` on cross-lib schemas so drift surfaces as `ValidationError` |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| New `clang.cindex.Index()` per file | Parser is 5-10× slower than expected on C++ codebases | Reuse one `Index` per `CppExtractor` instance | Any real codebase (>100 C++ files) |
| Pyright spawned per file | 1-3 s startup × N files = minutes | Batch files into a single pyright invocation when possible; or use pyright's watch mode for repeated calls | >50 Python files |
| Walking libclang AST `walk_preorder()` without skipping system headers | Parse times in minutes for `#include <vector>` | Pass `-isystem` flags so system headers are marked as such; skip cursors where `cursor.location.is_in_system_header` | First file that includes any STL header |
| Reading subprocess output via `proc.stdout.read()` for large outputs | Hangs or OOM | Use `communicate()` / `subprocess.run(capture_output=True)`; consider streaming line-by-line for very large outputs | Pyright JSON >64 KB (a few hundred LOC) |
| Re-parsing AST per extractor (already a known anti-pattern) | 4× CPU on parse-heavy workloads | Parse once in executor, pass to extractors (tracked separately in `PROJECT.md` Active) | Any non-toy file |
| Storing libclang cursors in a list to "process later" | Crashes hours after parse | Convert to Pydantic models immediately, before list grows | Production workloads with deferred processing |

Note: This library targets pip distribution to a verifier pipeline. Expected scale is "single repo at a time" — tens to low thousands of files. Throughput tuning beyond the above is YAGNI for v0.2.

---

## Security Mistakes

Library is offline / stateless / no network — most web-app security concerns don't apply. Domain-specific concerns:

| Mistake | Risk | Prevention |
|---------|------|------------|
| `subprocess.run([pyright, ...], shell=True)` | Shell injection via crafted file paths if caller passes untrusted paths | Never use `shell=True`; always pass `list[str]` argv |
| Pass user-controlled paths to pyright/callgraph.py without sanitization | Pyright/callgraph.py may read additional files in the project tree, including secrets if `.env` is present | Document: "Caller is responsible for ensuring the parsed directory is sandboxed"; require absolute paths; never expand `~` for the subprocess |
| libclang parsing untrusted C++ source | libclang may have its own CVEs; parsing attacker code with billion-laughs-style template recursion can OOM | Parse with `timeout` set on the parsing call too (not just subprocess); set memory limits via `resource` module on Linux; document the offline-only / trusted-input use case |
| Logging full source content on parse error | Leaks intellectual property in logs | Library does not log anyway (caller-agnostic principle); preserve this — never add logging that includes source bytes |
| Loading bundled libclang from an unsigned source | Supply-chain attack if PyPI `libclang` package is compromised | Pin to a specific version with a hash; verify with `pip install --require-hashes` in production environments |

---

## "Looks Done But Isn't" Checklist

- [ ] **C++ extractor works**: Often missing the `compile_args` plumbing — verify it parses real C++ that uses `<vector>` with caller-supplied include path
- [ ] **C++ extractor works**: Often missing template specialization handling — verify `Foo<int>` produces a distinct `ClassNode` from `Foo<T>`
- [ ] **C++ extractor works**: Often missing anonymous-namespace ID disambiguation — verify two anonymous-namespace classes don't collide on `node_id`
- [ ] **Pyright integration works**: Often missing timeout — verify the wrapper raises `TimeoutExpired`, not hangs, on `--watch` accidentally being passed
- [ ] **Pyright integration works**: Often missing exit-code-1-is-OK handling — verify the wrapper succeeds on Python code that has type errors
- [ ] **Pyright integration works**: Often missing schema validation — verify a fixture pyright JSON validates against the Pydantic model
- [ ] **Callgraph integration works**: Often missing handling of unresolved callees — verify a `HANDLERS[x]()` site produces an `unresolved_call_sites` entry, not a missing edge
- [ ] **FSM extraction works**: Often missing the negative case — verify `class Color(Enum): RED, GREEN, BLUE` produces zero FSMs
- [ ] **FSM extraction works**: Often missing inheritance flattening — verify `SecureConnection(Connection)` shows all of `Connection`'s transitions plus its own
- [ ] **Schema compatibility works**: Often missing cross-lib contract test — verify a `ClassDiagram` instance from `lib-code-parser` validates against `lib-diagram-parser`'s model
- [ ] **Schema compatibility works**: Often missing `extra="forbid"` — verify an extra field in `ClassDiagram` causes `ValidationError`, not silent ignore
- [ ] **Determinism works**: Often missing the cross-platform check — verify output is byte-identical on Linux, macOS, Windows for the same fixture
- [ ] **Determinism works**: Often missing the cross-session check — verify two `python -c "..."` invocations produce identical output (catches `PYTHONHASHSEED` leakage)
- [ ] **Determinism works**: Often missing CRLF/Unicode normalization test — verify same content with different line endings and Unicode normalizations produces identical output
- [ ] **Subprocess wrapper works**: Often missing the encoding parameter — verify it works on Windows with non-ASCII paths
- [ ] **libclang version pin works**: Often missing the runtime assertion — verify the parser refuses to run with an unexpected libclang version
- [ ] **Diagram edge taxonomy works**: Often missing the rule table — verify the documented mapping from source-level facts to `EdgeKind` is complete (no "uses" catch-all in code paths)

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Pitfall 1 (libclang lifetime crash) | MEDIUM | Audit every extractor for cursor-returning functions; refactor to eager conversion; add GC test |
| Pitfall 2 (libclang version drift) | LOW–MEDIUM | Add pin + runtime assertion; pin in `pyproject.toml`; re-baseline golden fixtures on chosen version |
| Pitfall 3 (subprocess deadlock) | LOW | Replace all `Popen+wait+read` with `subprocess.run(capture_output=True, timeout=N)`; one-line per call site |
| Pitfall 4 (tool schema drift) | MEDIUM | Add Pydantic models for tool output; pin tool versions; add golden fixtures |
| Pitfall 5 (libclang non-determinism) | HIGH | Define `compile_args` contract; rewrite C++ extractor entry point; re-baseline all golden fixtures; possibly invalidate older fixtures entirely |
| Pitfall 6 (cross-lib schema drift) | HIGH | Extract shared schema to third package; coordinate releases of both libs; migrate consumers |
| Pitfall 7 (diagram edge ambiguity) | HIGH | Define edge taxonomy; rewrite diagram extractor; re-baseline golden fixtures; coordinate with verifier expectations |
| Pitfall 8 (FSM false positives) | MEDIUM | Tighten extraction pattern to require state-field assignment guard; add confidence/reason field; re-validate fixtures |
| Pitfall 9 (overloading/overriding) | MEDIUM | Add inheritance flattening pass before FSM extraction; handle overloads as distinct transitions |
| Pitfall 10 (call graph approximation) | LOW–MEDIUM | Add `source` field on `CallEdge`; add `unresolved_call_sites` list; document precision in README |
| Pitfall 11 (encoding/line-ending) | LOW | Add normalization step in executor entry; add cross-platform determinism test; set `.gitattributes` |
| Pitfall 12 (C++ AST surprises) | MEDIUM | Add fixture checklist; iterate the C++ extractor against each surprise; document negative cases |
| Pitfall 13 (subprocess encoding on Windows) | LOW | One-line fix in subprocess wrapper (`encoding="utf-8"`); add Windows CI |
| Pitfall 14 (set/hash ordering) | LOW–MEDIUM | Audit all extractor outputs for `set` usage; add sort-on-exit; add cross-session determinism test |
| Pitfall 15 (pyright sentinel/exit) | LOW | Whitelist exit codes 0,1; filter `Unknown`/`Unbound` from `TypeDep`; add type-broken fixture |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. libclang lifetime crash | Architecture phase (contract: no libclang handles cross module boundary) | GC-and-assert test in C++ extractor test suite |
| 2. libclang version drift | Language frontend phase (C++) | Runtime assertion at extractor init; CI matrix Linux/macOS/Windows |
| 3. subprocess deadlock | ACL-2 integration phase (subprocess wrapper) | Unit test with a process that outputs >1 MB to stdout |
| 4. tool JSON schema drift | ACL-2 integration phase | Golden fixture of tool output in CI; Pydantic validation as the parse step |
| 5. libclang non-determinism | Language frontend phase (C++) | `compile_args` required in `ParserConfig`; cross-platform CI diff |
| 6. cross-lib schema drift | Architecture phase (schema design) + ongoing | Cross-lib contract test (CI of both libs); `extra="forbid"` |
| 7. diagram edge ambiguity | Diagram phase architecture | Edge taxonomy committed before any extractor code; rule table doc as test fixture |
| 8. FSM false positives | Diagram phase (FSM sub-phase) | Negative fixtures (`Color(Enum)` produces 0 FSMs); confidence/reason field |
| 9. overloading/overriding hides transitions | Diagram phase (FSM sub-phase) | 3-deep inheritance fixture; C++ overload fixture |
| 10. call graph approximation | ACL-2 integration phase (callgraph.py) | `source` field on edge; `unresolved_call_sites` test |
| 11. encoding / line-ending | Architecture phase (executor normalization) | Cross-LF/CRLF and NFC/NFD fixture pair → identical output |
| 12. C++ AST surprises | Language frontend phase (C++) | Fixture checklist as part of definition-of-done |
| 13. subprocess encoding on Windows | ACL-2 integration phase | Windows CI with non-ASCII path fixture |
| 14. set / hash ordering | Architecture phase (sort-on-exit invariant) | Two-subprocess determinism test |
| 15. pyright sentinel / exit codes | ACL-2 integration phase (pyright wrapper) | Type-broken Python fixture |

**Phase ordering implication for the roadmap:**
1. **Architecture phase first** — pitfalls 1, 6, 7, 11, 14 must be addressed by architectural rules before any extractor code is written. Retrofitting these is high cost (see Recovery Strategies).
2. **ACL-2 integration phase next** — pitfalls 3, 4, 10, 13, 15 share a single subprocess wrapper; building it correctly once is much cheaper than fixing each tool integration separately.
3. **Language frontend (C++) phase** — pitfalls 2, 5, 12 cluster around libclang adoption. The `compile_args` contract (5) shapes the public API and must be settled before diagram extractors consume C++ output.
4. **Diagram + FSM phase last** — pitfalls 7, 8, 9 depend on stable AST + call-graph output and on the shared schema being locked.

---

## Sources

### libclang lifetime and ABI

- [libclang Python bindings official docs](https://libclang.readthedocs.io/) — TODO note: "client must hold on to index and translation unit, or risk crashes"
- [llvm-project#60270 — clang 15 broke ABI without bumping SOVERSION](https://github.com/llvm/llvm-project/issues/60270)
- [llvm-project#182907 — Libclang Python bindings lack holistic error reporting](https://github.com/llvm/llvm-project/issues/182907)
- [libclang PyPI package](https://pypi.org/project/libclang/) — bundled wheels, version pinning
- [Libclang tutorial — official LLVM docs](https://clang.llvm.org/docs/LibClang.html)
- [Shahar Mike — Using libclang to Parse C++](https://shaharmike.com/cpp/libclang/) — practical lifetime advice
- [Dealing with parse errors with Python bindings of libclang (cfe-dev)](https://lists.llvm.org/pipermail/cfe-dev/2016-August/050332.html)

### subprocess and pyright

- [Python subprocess official docs — deadlock warning](https://docs.python.org/3/library/subprocess.html)
- [Python bug #14872 — subprocess is not safe from deadlocks](https://bugs.python.org/issue14872)
- [dcreager — Problems with Python's subprocess.communicate](https://dcreager.net/2009/08/06/subprocess-communicate-drawbacks/)
- [pyright command-line docs](https://github.com/microsoft/pyright/blob/main/docs/command-line.md) — exit code semantics, `--outputjson`
- [pyright#6740 — `--outputjson` schema changed in 1.1.340 (file → uri)](https://github.com/microsoft/pyright/issues/6740) — concrete evidence of schema drift
- [pyright#300 — Command-line pyright should exit non-zero if config file can't be parsed](https://github.com/microsoft/pyright/issues/300)

### Call graphs and Python static analysis

- [Gopinath — A Minimal Static Call Graph for Python Programs (2022)](https://rahul.gopinath.org/post/2022/02/16/python-callgraph/) — "accurate call-graphs are impossible without full type inference"
- [PyCG: Practical Call Graph Generation in Python (arXiv 2103.00587)](https://arxiv.org/pdf/2103.00587)
- [AutoPruner: Transformer-Based Call Graph Pruning (arXiv 2209.03230)](https://arxiv.org/pdf/2209.03230)
- [pyan — Python static call graph generator](https://github.com/Technologicat/pyan)

### FSM extraction

- [Chen et al. — Automated Finite State Machine Extraction (FEAST 2019)](https://songlh.github.io/paper/feast02.pdf) — 160 programs, 2 false positives, defines the precise pattern (state variable mutation + control-flow guard)
- [PROSPER — LLM-based FSM extraction comparison (arXiv 2507.11222)](https://arxiv.org/html/2507.11222v1)

### Schema and Pydantic

- [Pydantic Migration Guide (v2)](https://docs.pydantic.dev/latest/migration/)
- [stable_pydantic — compatibility checks and migrations](https://github.com/QuartzLibrary/stable_pydantic)
- [Pydantic as a Backward Compatibility Layer — Roman Imankulov](https://roman.pt/posts/pydantic-as-backward-compatibility-layer/)

### Determinism, line endings, Unicode

- [Python ast module official docs](https://docs.python.org/3/library/ast.html)
- [Git and normalization of line-endings — DEV Community](https://dev.to/kevinshu/git-and-normalization-of-line-endings-228j)
- [W3C — Canonical Normalization Issues](https://www.w3.org/wiki/I18N/CanonicalNormalizationIssues)
- [CRLF vs LF: Normalizing Line Endings in Git — Aleksandr Hovhannisyan](https://www.aleksandrhovhannisyan.com/blog/crlf-vs-lf-normalizing-line-endings-in-git/)

### Project context

- `c:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/PROJECT.md` — Active scope for v0.2.0
- `c:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/ARCHITECTURE.md` — Existing anti-patterns (not re-covered here)
- `c:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib-code-parser.md` — Determinism requirement (§ "採用する検証手法・アルゴリズム"); Layer M bisimulation rationale

---
*Pitfalls research for: deterministic multi-language (Python + C++) code parser library with ACL-2 subprocess integration, diagram + FSM extraction, and cross-lib schema compatibility*
*Researched: 2026-05-24*
