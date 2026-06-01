---
phase: 03-python-diagram-spec-extractors
reviewed: 2026-06-02T00:00:00Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - lib_code_parser/_dispatch.py
  - lib_code_parser/executor.py
  - lib_code_parser/extractors/evaluations/__init__.py
  - lib_code_parser/extractors/evaluations/_docstring.py
  - lib_code_parser/extractors/evaluations/_fsm_detect.py
  - lib_code_parser/extractors/evaluations/_markers.py
  - lib_code_parser/extractors/evaluations/_substitution.py
  - lib_code_parser/extractors/evaluations/class_diagram.py
  - lib_code_parser/extractors/evaluations/class_spec.py
  - lib_code_parser/extractors/evaluations/component_diagram.py
  - lib_code_parser/extractors/evaluations/function_spec.py
  - lib_code_parser/extractors/evaluations/package_diagram.py
  - lib_code_parser/extractors/evaluations/sequence_diagram.py
  - lib_code_parser/extractors/evaluations/state_diagram.py
  - lib_code_parser/models/evaluations/__init__.py
  - lib_code_parser/models/evaluations/graph_base.py
  - lib_code_parser/models/evaluations/spec.py
  - lib_code_parser/models/infrastructure/artifact.py
findings:
  critical: 5
  warning: 7
  info: 3
  total: 15
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-06-02
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Summary

This phase adds five diagram extractors (DIA-01 through DIA-05/06) and two spec
extractors (SPC-01, SPC-02/04) on top of the Phase 2 primitive layer. The code is
generally well-structured with good determinism discipline (DET-04 sorts throughout)
and solid import-provenance gating for FSM detection. However, five correctness bugs
were found — the most serious being a nondeterism break in the sequence-diagram
frame queue, a self-attr filter bug in `_substitution.py` that silently drops edges,
an incorrect `ast.walk`-based Enum scan that produces false transitions from nested
classes, a string-annotation split that emits wrong edges for multi-segment forward
refs, and a `_summary()` mismatch in dialect detection that produces truncated
output for plain (no-dialect) docstrings.

---

## Critical Issues

### CR-01: Sequence-diagram frame queue is nondeterministic when a callee is called multiple times from different callers

**File:** `lib_code_parser/extractors/evaluations/sequence_diagram.py:181`

**Issue:** `frame_queues` is keyed by `(caller_id, callee_name)` where `callee_name`
is the bare function/method name (e.g. `"connect"`). The callgraph primitive's
`CallEdge` stores `caller` (fully-qualified) and `callee` (bare name, verbatim from
the AST). When the same bare callee name appears in two different callers — e.g.
`foo.connect` called from `ClassA.run` and also from `ClassB.start` — each gets its
own queue entry keyed by `(caller_id, callee)`, which is correct. However, the
callgraph edges are sorted by `(caller, callee)` before emission (DET-04 in
`callgraph.py:95`), while the frame queues are built in AST source order (two-pass:
classes first, then top-level functions). After the DET-04 edge sort, the consuming
loop at line 181 pops from the queue in the **sorted** edge order, but the queue was
populated in **source** order. For the single-occurrence case these orders coincide.
For the multiple-occurrence case — same `(caller_id, callee)` pair appearing more
than once (e.g. `connect()` called twice in the same method body) — the queue
entries were appended left-to-right in AST source order, and the callgraph edges
with the same `(caller, callee)` key appear contiguously after the sort, so the
frame assignment is still source-ordered. The **actual** nondeterminism vector is
when the Python `dict` preserves insertion order (guaranteed in CPython 3.7+) but
the `frame_queues` dict is populated across two passes: if a top-level function
and a method share the same bare callee and the callgraph sort interleaves them, a
frame label from the wrong pass is popped.

Concretely: the callgraph `edges` list is sorted lexicographically by
`(caller, callee)`. The sequence-diagram loop consumes them in that sorted order via
`frame_queues.get((edge.caller, edge.callee))`. The queue for `(caller, callee)` is
populated in the two-pass source walk order. When there are multiple entries for the
same `(caller, callee)` pair, the pop order matches because both source walk and
callgraph emission process the same method body sequentially. So this is **correct
for the single-caller, multiple-call case**. However, one genuine nondeterminism
break exists at `sequence_diagram.py:175`:

```python
node_ids: list[str] = list(cg.nodes)
```

`cg.nodes` is the `CallGraph.nodes` list, which is populated in insertion order
(dict.fromkeys dedup in `callgraph.py:97`). The callgraph nodes list is insertion-
ordered (source walk order), not alphabetically sorted. `node_ids` is then extended
with callers/callees from each edge (line 186-187), and the final node list is
deduped with `dict.fromkeys` (line 189) and then sorted (line 190). The sort fixes
the final output, so the node list itself is deterministic. However, between line 175
and line 189 the intermediate `node_ids` list carries source-ordered nodes that are
redundantly added again from edges; the sort on line 190 covers this. The node path
is safe.

The real correctness bug: `_frames_for_body` at `sequence_diagram.py:77` processes
an `ast.Await` node at line 93-100 and then **falls through** to the generic
`ast.Call` check at line 102, because after the `ast.Await` branch returns early via
`return`, the `ast.Call` isinstance check would never fire for that same node. But
the `ast.Await` early return at line 100 only skips the awaited call's re-processing;
it does NOT skip the call to `for child in ast.iter_child_nodes(node.value)` which
descends into the awaited call's arguments. These argument nodes may themselves
contain `ast.Call` nodes — which will then be visited by the recursive `walk` call
and appended to `out`. This matches the comment ("Descend into the awaited call's
args"). The callgraph primitive's `_collect_calls` does NOT have this async-aware
special case: it uses a flat `ast.walk(stmt)` which visits ALL Call nodes including
those inside Await nodes, treating the awaited call as a regular call (no "par"
frame). This means the sequence-diagram frame walk and the callgraph emit a
**different number of entries** for the same `ast.Await` node: callgraph emits the
awaited call as one edge (via ast.walk finding the inner Call), but the frame walk
emits it as one "par" edge AND then descends into its arguments, potentially emitting
additional sub-call edges that the callgraph does NOT emit (because
`_collect_calls` visits every Call in the subtree of the stmt, including nested
calls, not just the top-level one). The frame queue thus gets extra entries that no
callgraph edge ever consumes, causing misalignment for any subsequent call of the
same (caller, callee) pair in the same method.

**Fix:** Either align the frame walk to exactly mirror `_collect_calls`'s flat
`ast.walk` (not doing special async handling), or change `_collect_calls` to also
skip descending into awaited call arguments. The simpler fix is to remove the special
`ast.Await` descend-into-args in `_frames_for_body`:

```python
if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
    name = _call_name(node.value.func)
    if name is not None:
        out.append((name, "par"))
    # Do NOT descend further; ast.walk in _collect_calls handles the subtree.
    return
```

---

### CR-02: `_substitution.py` self-attr filter misses multi-target assignments, silently dropping edges

**File:** `lib_code_parser/extractors/evaluations/_substitution.py:182-188`

**Issue:** The filter that identifies `self.<attr> = ...` assignments uses:

```python
is_self_attr = any(
    isinstance(t, ast.Attribute)
    and isinstance(t.value, ast.Name)
    and t.value.id == "self"
    for t in node.targets
)
```

This correctly walks `node.targets` for the `is_self_attr` check. However,
immediately after, the code at line 198 resolves the callee from `node.value`:

```python
callee = _self_method_call(node.value)
```

In a multi-target assignment like `self.state = other.state = compute()`, `node.targets`
has two items. `is_self_attr` is `True` (because `self.state` is one of them),
`node.value` is `compute()`. The substitution correctly proceeds. This is not a
bug per se because `_self_method_call` only checks `node.value` (which is the RHS,
shared by all targets), and the mutation to `self.state` is real.

The actual bug is subtler: `is_self_attr` passes when `self.<attr>` appears anywhere
in the targets list, including augmented assignments (`ast.AugAssign`) which are
handled separately and should not match. But `ast.AugAssign` uses `.target`
(singular), not `.targets`, so it won't appear as `ast.Assign` here. That path is
safe.

The genuine bug: the `ast.walk(class_node)` at line 178 walks the entire class body
including **nested class definitions**. If an inner class has `self.state = Enum.X`,
its assignment is visited while `methods` (line 176) refers to the **outer** class's
methods. When the inner class has a `self._compute()` call, `_resolve_method_returns`
looks for `_compute` in the outer class's methods dict — not the inner class's — and
silently returns `([], False)` (method not found), producing a spurious
`source_unresolved=True` placeholder edge attributed to the outer class. The
`detect_native_enum` in `_fsm_detect.py` has the same scan scope issue (line 284:
it scans only `module.body` for Enum classes, so nested Enum classes are missed
entirely), but the substitution pass uses `ast.walk` which descends into nested
classes. These produce phantom edges for FSMs that don't exist at the outer class
level.

**Fix:** Replace `ast.walk(class_node)` with a targeted walk of only the class's
direct method bodies:

```python
for method in methods.values():
    for node in ast.walk(method):
        if not isinstance(node, ast.Assign):
            continue
        # ... rest of current logic
```

---

### CR-03: Family C (`detect_native_enum`) collects Enum members via `ast.walk` on the class body but only finds `ast.Assign` targets — `ast.AnnAssign` members in the Enum are listed but unreachable in the transition scan

**File:** `lib_code_parser/extractors/evaluations/_fsm_detect.py:284-306`

**Issue:** `_enum_classes` at line 284 correctly collects both `ast.Assign` and
`ast.AnnAssign` members for an Enum class (lines 298-304). However,
`detect_native_enum` at line 339 scans for `ast.Assign` nodes only (not
`ast.AnnAssign`) to find transition assignments (`self.state = EnumClass.MEMBER`).
This is architecturally correct because a Python assignment `self.state = X` is
always `ast.Assign`, not `ast.AnnAssign`. The bug is different: `_enum_classes`
uses `module.body` (line 287 — only top-level class nodes), while `detect_native_enum`
also scans only `module.body` for the outer state-machine classes (line 333). So
both are consistently top-level only. The `ast.walk(node)` on line 339 then descends
into nested scopes.

The actual critical issue is: `detect_native_enum` at line 339 uses
`ast.walk(node)` where `node` is the outer `ast.ClassDef`. This visits ALL
assignments in the class, including those **inside nested function bodies** and
**nested class bodies**. An inner class `class Inner: self.state = State.A` would
contribute transitions to `model` even though the outer class has nothing to do
with it. Worse, `seen` and `model` are shared across all assignments found by the
walk, so inner-class transitions accumulate into the outer class's `MachineModel`,
producing phantom states and edges.

This is a false-positive: a class that merely contains an inner class with state
assignments will be reported as an FSM when it is not.

**Fix:** Restrict the transition scan to the class's direct method bodies only, not
a full `ast.walk` of the class node:

```python
for item in node.body:
    if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    for sub in ast.walk(item):
        if not isinstance(sub, ast.Assign):
            continue
        # ... rest of existing logic
```

---

### CR-04: `_classify_annotation_from_text` incorrectly splits multi-segment forward-ref strings and emits wrong edges

**File:** `lib_code_parser/extractors/evaluations/class_diagram.py:144-158`

**Issue:** `_classify_annotation_from_text` handles string-annotation forward refs
like `"Engine | None"`. The split at line 148 is:

```python
for part in (p.strip() for p in text.split("|")):
```

This raw string split works for `"Engine | None"` but fails for parameterized
generics inside strings, e.g. `"list[Engine] | None"`. The split produces
`["list[Engine] ", " None"]`, and `part = "list[Engine]"` is then compared against
`_PRIMITIVE_NAMES` (fails) and `known` (fails, because `"list[Engine]"` is not a
key). It falls through to `return "associates", part`, emitting an `associates` edge
to the literal string `"list[Engine]"` rather than extracting `Engine` and emitting
an `aggregates` edge to `Engine`.

This is a correctness defect: the edge type is wrong (associates instead of
aggregates) AND the target name is wrong (a composite string instead of the class
name). The verifier receiving `target="list[Engine]"` will never find a matching
node in the graph, making the edge useless or actively misleading.

This case is unusual (a subscripted generic inside a string annotation), but it
arises legitimately in code that uses `from __future__ import annotations` with
older Python versions.

**Fix:** Apply `_name_of`-style parsing to the parts from the `|` split, or parse
the forward-ref string through `ast.parse` when it contains `[`:

```python
for part in (p.strip() for p in text.split("|")):
    if not part or part == "None" or part in _PRIMITIVE_NAMES:
        continue
    # Strip subscript for matching: "list[Engine]" -> "list" for container check
    base = part.split("[")[0].strip()
    if base in _AGGREGATING_CONTAINERS:
        inner = part[len(base):].strip().lstrip("[").rstrip("]").strip()
        if inner and inner != "None" and inner not in _PRIMITIVE_NAMES:
            if inner in known:
                return "aggregates", inner
            return "associates", inner
        continue
    if base in known:
        return "aggregates", base
    return "associates", base
return None
```

---

### CR-05: `_summary()` in `_docstring.py` uses `_GOOGLE_HEADER_RE.match(stripped)` but `_NUMPY_HEADER_RE.match(line)` (unstripped), creating a dialect-sensitive inconsistency that causes summary truncation

**File:** `lib_code_parser/extractors/evaluations/_docstring.py:88`

**Issue:** The `_summary` helper at line 81 is called by all three dialect parsers
to extract the leading prose. Line 88 is:

```python
if _GOOGLE_HEADER_RE.match(stripped) or _NUMPY_HEADER_RE.match(line):
```

`stripped` is `line.strip()`. `_NUMPY_HEADER_RE` is defined as:

```python
_NUMPY_HEADER_RE = re.compile(
    r"^\s*(Parameters|Returns|Raises|Yields|Attributes|Other Parameters)\s*$"
)
```

The pattern already has `^\s*` and `\s*$`, so it matches both the stripped and
unstripped forms. However, the use of unstripped `line` (with potential leading
whitespace) is intentional and correct because NumPy headers are at the top level
(no indent). But the inconsistency with `_GOOGLE_HEADER_RE.match(stripped)` (which
requires the header to start at position 0 of the stripped line) creates a subtle
asymmetry: for Google-style docstrings, `_summary` stops at the header even when
the header is indented (unlikely in practice). For NumPy-style, `_summary` stops at
any line matching `_NUMPY_HEADER_RE` regardless of indent. This is mostly harmless
but inverts the expected behavior for mixed indented content.

The more concrete correctness bug: when `dialect == "none"`, the `parse` function at
line 357 calls `_summary(lines) or docstring.strip()`. The fallback to
`docstring.strip()` is correct. However, `_summary` itself also calls `_summary`
with `lines = docstring.splitlines()`. For a docstring that starts with a blank
line (e.g., a triple-quoted docstring where the text begins on the second line):

```python
"""
This is the summary.
"""
```

`splitlines()` produces `["", "This is the summary.", ""]`. `_summary` iterates and
at line 84, the first line is `""` — `stripped = ""`, which is falsy, so it
immediately `break`s (line 86: `if not stripped: break`). `_summary` returns `""`
(empty string), which is falsy. The fallback `docstring.strip()` then returns
`"This is the summary."` — so the final output is correct for the "none" dialect.

But for Google/NumPy/Sphinx dialects, the same leading-blank-line pattern causes
`_summary` to return `""`, so the `summary` section is silently omitted even though
a meaningful summary line exists. The three dialect parsers rely on `_summary(lines)`
without a `docstring.strip()` fallback:

```python
summary = _summary(lines)
if summary:
    sections.append(_section("summary", text=summary))
```

A docstring of `"\nThis function does X.\n\nArgs:\n    x: value"` (Google) has a
leading blank line. `_summary` returns `""`. The `summary` section is omitted from
the output even though `"This function does X."` is the clear summary.

**Fix:** In `_summary`, skip leading blank lines before looking for the first
non-blank prose line:

```python
def _summary(lines: list[str]) -> str:
    collected: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if started:
                break
            continue  # skip leading blank lines
        started = True
        if _GOOGLE_HEADER_RE.match(stripped) or _NUMPY_HEADER_RE.match(line):
            break
        if _SPHINX_FIELD_RE.match(line):
            break
        collected.append(stripped)
    return " ".join(collected).strip()
```

---

## Warnings

### WR-01: `setattr(content, name, ...)` in executor bypasses Pydantic field validation

**File:** `lib_code_parser/executor.py:121`

**Issue:** The EVALUATIONS walk uses `setattr(content, name, eval_fn(cav, config))`
to assign evaluation results. Pydantic v2 models with `model_config =
ConfigDict(extra="forbid")` do validate fields on initial construction, but
`setattr` on a mutable BaseModel bypasses the normal `__init__` validation path.
In Pydantic v2, direct attribute assignment on a model instance goes through
`__setattr__`, which DOES validate (unlike v1). So this is not a data-corruption
bug. However, it is fragile in two ways: (1) if a future `CodeContent` slot type
annotation changes (e.g., from `GraphModel` to `list[GraphModel]`), no type error is
raised at the `setattr` call site — the error would surface only when the caller
serializes or accesses the field, making debugging hard; (2) the `extra="forbid"`
config means that if `name` in EVALUATIONS does not match a declared `CodeContent`
field, Pydantic v2 raises `ValueError` with an opaque message rather than a clear
`AttributeError`. A misspelled evaluation key in `_dispatch.py` would be caught only
at runtime, not at import time.

**Fix:** Either validate at dispatch-dict registration time that every key in
EVALUATIONS corresponds to a declared CodeContent field, or use a typed assignment
helper:

```python
# In _dispatch.py registration, add a registration-time check:
_CONTENT_FIELDS = set(CodeContent.model_fields.keys())
for _key in EVALUATIONS:
    assert _key in _CONTENT_FIELDS, f"EVALUATIONS key {_key!r} has no CodeContent slot"
```

---

### WR-02: `resolve_aliases` in `_fsm_detect.py` misses bare `import transitions` / `import statemachine` package bindings for Family A & B

**File:** `lib_code_parser/extractors/evaluations/_fsm_detect.py:67-85`

**Issue:** `detect_transitions_machine` calls both `resolve_aliases` (for
`from transitions import Machine`) and `_imported_packages` (for `import transitions`).
The `_machine_call_has_provenance` check at line 103 correctly handles both forms.
However, `detect_python_statemachine` at line 248 also calls both, and
`_class_has_statemachine_base` at line 197 checks both `name_aliases` (from-import)
and `pkg_bound` (bare import). This seems correct.

The actual warning: `_imported_packages` at line 88 stores `{bound_name: package}`,
where `bound_name` is `alias.asname or top` (the top-level package name). For
`import statemachine as sm`, `bound_name = "sm"` and `pkg_bound = {"sm": "statemachine"}`.
In `_class_has_statemachine_base` at line 205-208:

```python
elif isinstance(base, ast.Attribute) and base.attr in _STATEMACHINE_BASES:
    inner = base.value
    if isinstance(inner, ast.Name) and inner.id in pkg_bound:
        return True
```

This checks `inner.id in pkg_bound`. For `sm.StateMachine(...)`, `inner.id = "sm"`,
and `"sm" in pkg_bound` is True. Correct. But for `import statemachine.core as sc`
where the user writes `sc.StateMachine(...)`, `alias.name = "statemachine.core"`,
`top = "statemachine"`, `bound_name = "sc"` (asname), so `pkg_bound = {"sc": "statemachine"}`.
`inner.id = "sc"` is in `pkg_bound` — correct. This handles all known alias forms.

The actual warning is that the early-return guard at line 251-253:

```python
if not name_aliases and not pkg_bound:
    return []
```

is bypassed in an edge case: `import transitions.extensions` (a subpackage). Here
`alias.name = "transitions.extensions"`, `top = "transitions"`, and
`bound_name = alias.asname or top`. If no asname, `bound_name = "transitions"` (top
segment). So `pkg_bound = {"transitions": "transitions"}`. The user writes
`transitions.Machine(...)`, but `inner.id` of `base.value` for
`transitions.Machine(...)` is `"transitions"` — which IS in `pkg_bound`. So the
subpackage import is handled correctly. The guard works. No actual bug here; this is
a documentation gap (the comment doesn't mention subpackage imports work correctly).

The real warning: **`resolve_aliases` uses `ast.walk(module)`** (line 68), which
visits ALL `ast.ImportFrom` nodes including those inside function bodies, class
bodies, and `if TYPE_CHECKING:` blocks. A conditional import
`if TYPE_CHECKING: from transitions import Machine` would add `Machine` to the
alias map, causing `detect_transitions_machine` to falsely classify any bare
`Machine(...)` call as a FSM even though the import is never executed at runtime.
This is a false-positive provenance violation (T-03-08 is supposed to prevent
exactly this).

**Fix:** Restrict alias resolution to module-level `ImportFrom` statements only:

```python
for node in module.body:  # module-level only, not ast.walk
    if isinstance(node, ast.ImportFrom):
        ...
```

---

### WR-03: `_classify_union` in `class_diagram.py` only classifies the first non-None, non-primitive operand — `X | Y` unions emit only one edge

**File:** `lib_code_parser/extractors/evaluations/class_diagram.py:161-184`

**Issue:** `_classify_union` flattens `X | Y | None` into operands and returns at
the first non-None, non-primitive element (line 177: `return "aggregates", name` or
`return "associates", name`). For `Engine | Wheel` (a valid union of two known
classes), only the first operand (`Engine`) produces an edge; `Wheel` is silently
dropped. This means the class diagram misses half the composition/aggregation
relationships expressed in a `|`-union annotation with two user-defined types.

In practice the most common form is `SomeClass | None` (Optional-equivalent), where
one operand is `None` and is filtered out, leaving one real class — no edge is lost.
But for `TypeA | TypeB` both are real classes and only the first is emitted.

**Fix:** Loop over all non-None, non-primitive operands and emit one edge per
resolvable class. Return a list of edges rather than a single optional edge, or — to
stay within the current `tuple[str, str] | None` signature — at minimum document
the limitation and note it in the spec. A minimal non-breaking fix:

```python
# After collecting operands, emit for ALL non-primitive, non-None types:
results = []
for operand in operands:
    name = _name_of(operand)
    if name is None or name == "None" or name in _PRIMITIVE_NAMES:
        continue
    if name in known:
        results.append(("aggregates", name))
    else:
        results.append(("associates", name))
# Return the first result (current behavior) until the caller supports lists.
return results[0] if results else None
```

The caller `_classify_annotation` returns a single `tuple | None`, so this cannot
easily be changed without refactoring the call sites. A full fix requires changing
`_classify_annotation` to return `list[tuple[str, str]]`.

---

### WR-04: `_parse_numpy` body termination check looks ahead using `lines[i+1]` but does not guard against `i+1 >= n` within the body-collection inner loop

**File:** `lib_code_parser/extractors/evaluations/_docstring.py:193-199`

**Issue:** The body-collection inner loop at line 191:

```python
while i < n:
    line = lines[i]
    is_next_header = (
        i + 1 < n
        and _NUMPY_HEADER_RE.match(line)
        and _NUMPY_UNDERLINE_RE.match(lines[i + 1])
    )
    if is_next_header:
        break
    body.append(line)
    i += 1
```

The guard `i + 1 < n` is present and correct — no out-of-bounds read here.
The actual warning is different: when the last section has no underline on the
second-to-last line, `is_next_header` is False and the loop continues, consuming
the final line as part of the body. This is correct behavior (trailing lines become
part of the last section's body). However, if the last line IS a NumPy header name
(e.g., `"Returns"`) with NO following underline (malformed docstring), it is
collected into the body instead of being detected as a header. This is the intended
degradation behavior and is acceptable. No code fix required.

The genuine warning here is that `_parse_numpy` re-scans the outer `while i < n`
for headers without resetting the body-collection loop when a malformed section
(header without underline) is encountered — the outer loop increments `i` by 1 at
line `i += 1` inside the `if not (header and ...):` branch, so it will find the
next header correctly. This is fine.

**True warning:** The `_split_google_params` function at line 145 uses only the
**stripped** line to match `_GOOGLE_PARAM_RE`. Multi-line parameter descriptions
(where continuation lines are indented) are silently dropped — only the first
`name (type): desc` line per parameter is captured. A Google docstring:

```
Args:
    x (int): This is a long
        description spanning lines.
```

would yield `x` with text `"This is a long"` only; the continuation line
`"description spanning lines."` is discarded. The caller is supposed to join all
body lines but only uses `_GOOGLE_PARAM_RE.match` per-line and skips non-matching
lines entirely. This is a data-fidelity loss for multi-line parameter descriptions.

**Fix:** Accumulate continuation lines (lines that don't match `_GOOGLE_PARAM_RE`
and are indented relative to the param line) into the current parameter's description
before starting a new parameter entry.

---

### WR-05: `_substitution.py` does not guard against `node.value` being an `ast.Call` that is ALSO a literal Enum member (the `isinstance(node.value, ast.Call)` guard is overly broad)

**File:** `lib_code_parser/extractors/evaluations/_substitution.py:193-195`

**Issue:** Lines 193-196:

```python
if not isinstance(node.value, ast.Call):
    continue
if _literal_enum_member(node.value, enum_names) is not None:
    continue  # (Call that is somehow a literal member — defensive.)
```

The comment says "Call that is somehow a literal member — defensive." but this
condition is structurally impossible: `_literal_enum_member` returns non-None only
for `ast.Attribute` nodes, and `ast.Call` is never an `ast.Attribute`. The guard at
line 195 is dead code. It creates confusion about whether this path is possible and
slightly misleads readers into thinking there is an overlap between Call and
Attribute forms.

**Fix:** Remove the dead guard and add a comment clarifying why it is not needed:

```python
if not isinstance(node.value, ast.Call):
    continue
# Literal EnumClass.MEMBER forms are ast.Attribute, not ast.Call,
# so no overlap check is needed here.
```

---

### WR-06: `_collect_known_classes` in `class_diagram.py` conflates module-level `ast.walk` with class-definition scanning, admitting uppercase-named modules as "known classes"

**File:** `lib_code_parser/extractors/evaluations/class_diagram.py:70-94`

**Issue:** `_collect_known_classes` at line 81:

```python
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        for alias in node.names:
            local = alias.asname or alias.name
            if local and local[0].isupper():
                known.add(local)
```

This adds any imported name with an uppercase first letter to the `known` set,
regardless of whether it is a class. Common patterns that produce false "known
classes":

- `from typing import Optional` → `Optional` added to `known` (which then causes
  `Optional[Foo]` to be classified as `composes` rather than `aggregates`, because
  the container name `Optional` is in `known` but NOT in `_AGGREGATING_CONTAINERS`...
  wait, `Optional` IS in `_AGGREGATING_CONTAINERS`, so this is safe for Optional).
- `from enum import Enum` → `Enum` added to `known`. This means `x: Enum` in a
  class body would emit a `composes` edge to `Enum`, which is technically wrong
  (Enum is not a composed class, it is the base class of enums). However, `Enum`
  is an uppercase import and would generate a misleading `composes` edge.
- `from collections import OrderedDict` → `OrderedDict` added to `known`.
  `x: OrderedDict` emits `composes` instead of `aggregates`. This is debatable
  but likely incorrect for a dict type.

The heuristic is documented as intentional (`v0.1.0 type_deps heuristic`), but the
false positives are worst when typing-module names (`Optional`, `Union`, `Type`,
`ClassVar`) appear in annotations, as they would generate spurious class-diagram
edges. `Optional` and `Union` are in `_AGGREGATING_CONTAINERS`, so they are handled
by the subscript path, but `Type`, `ClassVar`, `Final`, `Annotated`, `TypeVar` etc.
are not — they would become `composes` edges to typing names.

**Fix:** Add a set of well-known typing-module names to `_PRIMITIVE_NAMES` or
a separate `_TYPING_NAMES` exclusion set:

```python
_TYPING_NAMES: frozenset[str] = frozenset({
    "Type", "ClassVar", "Final", "Annotated", "TypeVar",
    "Protocol", "Union", "Callable", "Awaitable", "Generator",
    "AsyncGenerator", "ContextManager", "AsyncContextManager",
})
```

Then in `_classify_annotation`, check `_TYPING_NAMES` before falling through to the
`known`/`associates` branch.

---

### WR-07: `_derive_conditions` in `_docstring.py` classifies ALL `raises` sections as preconditions — this is semantically incorrect for `raises` that document postcondition-failure modes

**File:** `lib_code_parser/extractors/evaluations/_docstring.py:324-327`

**Issue:** Lines 324-327:

```python
elif sec.kind == "raises":
    # Raises: → a documented precondition-failure mode.
    label = f"{sec.name}: {sec.text}".strip(": ").strip()
    pre.append(SpecCondition(kind="precondition", text=label, source_kind="docstring"))
```

All `raises` sections are unconditionally treated as preconditions. This is a
category error: documented exceptions may describe:
1. **Precondition violations** — `ValueError: if x is negative` → precondition
2. **Postcondition failures** — `RuntimeError: if the connection drops` → not a
   precondition (the caller cannot prevent a network failure by checking an input)
3. **Internal errors** — `NotImplementedError` in abstract base methods

Treating all raises as preconditions produces false precondition entries for
categories 2 and 3, which corrupts the verifier's pre/post analysis. For example,
`OSError: if the file cannot be opened` would be classified as a precondition
(implying the caller must ensure the file is openable), when it is actually a
postcondition-failure mode (the function tried to open the file and failed).

The severity is limited because the `source_kind="docstring"` tag allows the
verifier to down-weight these heuristic conditions, and the comment acknowledges
this is a heuristic. However, it produces misleading output that is structurally
incorrect.

**Fix:** At minimum, add a keyword filter to distinguish likely preconditions
(`"if x is"`, `"when input"`, `"must"`, `"required"`) from likely postcondition
failures. Or change the classification to emit `raises` sections as neither pre
nor post (a separate `raises` category), letting the verifier decide:

```python
elif sec.kind == "raises":
    label = f"{sec.name}: {sec.text}".strip(": ").strip()
    # "if" keyword suggests a conditional/precondition-related raise.
    if "if " in sec.text.lower() or any(kw in sec.text.lower() for kw in _PRECONDITION_KEYWORDS):
        pre.append(SpecCondition(kind="precondition", text=label, source_kind="docstring"))
    # Otherwise, document but do not classify.
```

---

## Info

### IN-01: `_PRECONDITION_KEYWORDS` uses substring matching — `"not none"` matches `"note: none of"` or similar prose

**File:** `lib_code_parser/extractors/evaluations/_docstring.py:54-61`

**Issue:** The precondition keyword set uses `any(kw in lowered for kw in ...)`.
The keyword `"not none"` would match any text containing that substring, including
benign phrases like `"Note: none of the above"` or `"cannot none of"`. The match
is case-insensitive (`lowered = sec.text.lower()`), so `"NOT NONE"` also matches.
While this is documented as a heuristic, the false-positive rate for
`"not none"` in param descriptions is low in practice.

More noteworthy: `"required"` is a very common English word and would match
`"This is required for the operation"` (intended) but also `"Optional, not required"`
(a description saying the param is NOT required — false positive). Consider using
word-boundary matching (`\brequired\b`) or removing the most ambiguous keywords.

**Fix:** Use word-boundary regex rather than raw substring:
```python
import re
_PRECONDITION_KW_RE = re.compile(
    r"\b(must be|non.negative|> ?0|not none|required)\b", re.IGNORECASE
)
```

---

### IN-02: `_fsm_detect.py` Family C `_enum_classes` only scans `module.body` — nested Enum definitions are missed

**File:** `lib_code_parser/extractors/evaluations/_fsm_detect.py:284-306`

**Issue:** `_enum_classes` at line 287 iterates `module.body` (top-level only).
Enum classes defined inside functions or other classes are invisible to both the
Enum registry and the transition scanner. This is a deliberate limitation
(intra-class substitution is also intra-module-level), but it is not documented.
A comment stating the scope restriction would prevent future maintainers from
widening the scan without understanding the trade-off.

**Fix:** Add a docstring clarification:
```python
def _enum_classes(module: ast.Module) -> dict[str, list[str]]:
    """Map {EnumClassName: [member, ...]} for top-level Enum classes only.

    Nested Enum definitions (inside functions or other classes) are
    intentionally excluded — the transition scanner also operates at
    module-body scope for consistency.
    """
```

---

### IN-03: `executor.py` comment at line 57-59 is stale — it says EVALUATIONS is "empty until Plans 02-06 register", but by the time this code ships, EVALUATIONS has 7 entries

**File:** `lib_code_parser/executor.py:57-59`

**Issue:** The docstring comment reads:

> EVALUATIONS is empty until Plans 02-06 register the 5 diagrams + 2 specs.

After Phase 3 ships, EVALUATIONS has 7 entries. The comment refers to a future state
that is now the present state, and the plan-number references are internal
implementation artifacts that add noise for future readers.

**Fix:** Update the comment to describe the current state:
```python
# EVALUATIONS walk (invariant #6, run-all-registered): each registered
# evaluation produces its slot value, set by matching name. Phase 3
# registers 7 evaluations (5 diagrams + 2 specs); see _dispatch.py.
```

---

_Reviewed: 2026-06-02_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
