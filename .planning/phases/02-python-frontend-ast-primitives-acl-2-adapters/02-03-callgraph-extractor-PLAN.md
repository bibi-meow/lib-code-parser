---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 03
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/extractors/primitives/callgraph.py
  - tests/unit/extractors/test_callgraph_extractor.py
  - tests/unit/test_callgraph_sort.py
autonomous: true
requirements: [AST-02, AST-05, DET-04, TRC-02, TRC-03]
must_haves:
  truths:
    - "Caller can write `from lib_code_parser.extractors.primitives.callgraph import extract; extract(cav, config)` and gets a CallGraph populated by static AST walk over cav.payload — no GPL deps, no external subprocess (AST-02 invariant)"
    - "Emitted CallGraph.edges are sorted lexicographically by (caller, callee) per DET-04 + ROADMAP Phase 2 SC-2 — sort is applied at emit time, callee resolution is v0.1.0-parity (bare-name for self.foo() / 2 edges for a.b().c() chain / nested function flattened to outer)"
    - "Emitted CallGraph.nodes contains classes, methods, and top-level functions in v0.1.0 emit order with dict.fromkeys-style dedup (insertion-preserving + unique) — node order is NOT sorted (ROADMAP SC-2 規定なし、v0.1.0 parity 維持)"
    - "Module docstring contains 'Implements: AST-02, AST-05, DET-04' and 'Traces: AST-02, AST-05, DET-04, US-01, US-22, US-25'"
    - "Module imports get_module_name from lib_code_parser._paths — no local _get_module_name (ARC-04 no-duplication grep gate continues to pass)"
  artifacts:
    - path: "lib_code_parser/extractors/primitives/callgraph.py"
      provides: "Pure-CAV internal CallGraph extractor (AST-02) — v0.1.0 resolution + DET-04 sort"
      contains: "def extract"
    - path: "tests/unit/extractors/test_callgraph_extractor.py"
      provides: "Unit tests covering v0.1.0 resolution rules (self.foo→bare, chain a.b().c()→2 edges, nested flatten, edges_sorted)"
      contains: "def test_extract"
    - path: "tests/unit/test_callgraph_sort.py"
      provides: "DET-04 sort invariant: edges output is monotonically (caller, callee) lex-sorted on representative fixtures"
      contains: "def test_edges_sorted"
  key_links:
    - from: "extractors/primitives/callgraph.py::extract"
      to: "CAV.payload (ast.Module)"
      via: "no re-parse, pulls cav.payload directly"
      pattern: "cav\\.payload"
    - from: "extractors/primitives/callgraph.py::extract — emit time sort"
      to: "DET-04 lexicographic (caller, callee)"
      via: "edges.sort(key=lambda e: (e.caller, e.callee))"
      pattern: "\\(e\\.caller, e\\.callee\\)"
---

<objective>
Wave 1 並列の 3 件目。 v0.1.0 `lib_code_parser/callgraph_builder.py` の static AST walk による caller→callee 抽出ロジックを CAV consumer signature に書き換えて `lib_code_parser/extractors/primitives/callgraph.py` に新規実装する。 RESEARCH §4.1 が 7 fixture で実機 fire して全列挙した v0.1.0 解像度 rule (self.foo() → bare、 a.b().c() chain → 2 edges、 nested function → outer に flatten、 deep `a.b.c.d()` → innermost 1 edge、 @staticmethod/@classmethod → 普通の method 扱い) を **そのまま継承**。 emit 順序は v0.1.0 通り (classes + methods 1st pass / top-level 2nd pass、 同 pass 内は AST 出現順)、 ただし最終 `CallGraph.edges` を emit する直前に `edges.sort(key=lambda e: (e.caller, e.callee))` を 1 pass で適用し ROADMAP Phase 2 SC-2 の `(caller, callee)` lexicographic sort + DET-04 を成立させる (RESEARCH §4.2 推奨)。 重複 edge (v0.1.0 が emit する `helper` + `other.helper` のような同名 callee 重複) は **dedup しない** — v0.1.0 parity 優先 (ROADMAP SC-2 は dedup 規定なし)。 `nodes` は v0.1.0 同様 `list(dict.fromkeys(nodes))` で挿入順保持 + 重複除去。

chain call `a.b().c()` の edge 数は v0.1.0 と同じ 2 edges を維持し、 RESEARCH §Pitfall 4 が予告した「Phase 3 で sequence diagram から逆算が必要になれば拡張」の余地を Phase 3 入口に deferred (CONTEXT.md G-5 Claude's Discretion 範囲)。 本 plan では future readers のために `test_chain_call_emits_two_edges` を unit test に明示する (RESEARCH §Pitfall 4 早期警告)。

Purpose: ROADMAP Phase 2 success criterion 2 のうち「CallGraph 内製 + `(caller, callee)` lex sort」を成立させ、 同時に SC-4 の「callgraph extractor の isolated 呼び出し性」を満たす。 AST-05 grep gate (Plan 02-01) と ARC-04 no-duplication grep gate を破らない。

Output:
- `lib_code_parser/extractors/primitives/callgraph.py` — 新規 1 ファイル、 `extract(cav, config)` + 2 internal helper (`_get_call_name` / `_collect_calls`) + module docstring (TRC-02/TRC-03 形式)
- `tests/unit/extractors/test_callgraph_extractor.py` — 解像度 rule の v0.1.0 parity を fixture 単位で固定する unit (RESEARCH §4.1 の 7 fixture を unit に翻訳)
- `tests/unit/test_callgraph_sort.py` — Wave 0 必須リスト中の DET-04 sort 単独 unit (VALIDATION.md)
</objective>

<execution_context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/workflows/execute-plan.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/PROJECT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/REQUIREMENTS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/ROADMAP.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/callgraph_builder.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_paths.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/callgraph.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/cav.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/config.py

<interfaces>
<!-- Phase 1 locked CallEdge / CallGraph (lib_code_parser/models/primitives/callgraph.py) — Plan 02-03 emits these unchanged. -->

class CallEdge(BaseModel):
    caller: str
    callee: str

class CallGraph(BaseModel):
    nodes: list[str] = []
    edges: list[CallEdge] = []

<!-- v0.1.0 callgraph_builder resolution rules (RESEARCH §4.1 7 fixture で実機列挙、 Plan 02-03 で verbatim 継承):

CG1 self.foo() in method:
    class Foo: def bar(self): self.baz()
  → edges = [(m.Foo.bar, baz)]   # bare "baz" (NOT Class.baz)

CG2 chain a.b().c() at module level:
    def outer(): a.b().c()
  → edges = [(m.outer, c), (m.outer, b)]   # 2 edges (walk visits both Call nodes)

CG3 imported call helper() + other.helper():
    from other import helper; def outer(): helper(); other.helper()
  → edges = [(m.outer, helper), (m.outer, helper)]   # duplicate allowed (no dedup)

CG4 nested function inside outer:
    def outer():
        def inner(): leaf()
        inner()
  → nodes = ["m.outer"]   # inner is NOT a node (top-level/method only)
    edges = [(m.outer, leaf), (m.outer, inner)]   # nested callee flatten to outer

CG5 @staticmethod / @classmethod:
    class Foo: @staticmethod def smethod(): ...
  → nodes = ["m.Foo", "m.Foo.smethod"]   # decorator ignored, treated as method
    edges = []

CG6 edge order (pre-sort):
    def b(): z(); a(); m()
  → edges = [(m.b, z), (m.b, a), (m.b, m)]   # AST出現順、 未sort

CG7 deep attribute a.b.c.d():
    def outer(): a.b.c.d()
  → edges = [(m.outer, d)]   # innermost Call only; b/c are attribute access, not Call
-->

<!-- v0.1.0 callgraph_builder.py helpers (Plan 02-03 が verbatim 継承):
_get_call_name(func_node):
    if isinstance(func_node, ast.Name): return func_node.id
    if isinstance(func_node, ast.Attribute): return func_node.attr
    return None

_collect_calls(body_nodes):
    names = []
    for stmt in body_nodes:
        for call in ast.walk(stmt):
            if isinstance(call, ast.Call):
                name = _get_call_name(call.func)
                if name: names.append(name)
    return names
-->
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement lib_code_parser/extractors/primitives/callgraph.py (CAV consumer + v0.1.0 parity + DET-04 sort)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/callgraph_builder.py (v0.1.0 reference — copy `_get_call_name` / `_collect_calls` / build_callgraph semantics verbatim)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§4.1 全 7 fixture の解像度 rule + §4.2 推奨実装の骨子 + §Pitfall 4 chain call の semantics 注意)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_paths.py (single source get_module_name)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/callgraph.py (Phase 1 locked CallEdge / CallGraph)
  </read_first>
  <behavior>
    - `from lib_code_parser.extractors.primitives.callgraph import extract` 成功 (isolated import)
    - `extract(cav, config)` で `cav.payload` (`ast.Module`) を 1 回 walk して `CallGraph` を返す
    - 解像度 rule = RESEARCH §4.1 の CG1-CG7 全件と同じ動作:
      - CG1: `class Foo: def bar(self): self.baz()` → edges=[(`m.Foo.bar`, `baz`)]
      - CG2: `def outer(): a.b().c()` → edges=[(`m.outer`, `c`), (`m.outer`, `b`)] (2 edges、 sort 適用後は `(m.outer, b), (m.outer, c)`)
      - CG3: 重複 edge は dedup しない (v0.1.0 parity)
      - CG4: nested function は node に登録しない、 outer に callee flatten
      - CG5: `@staticmethod` / `@classmethod` decorator は無視 (普通の method 扱い)
      - CG6 → DET-04 sort 適用後の emission 順は `(caller, callee)` lex 順
      - CG7: deep `a.b.c.d()` は innermost 1 edge のみ
    - `CallGraph.nodes` は v0.1.0 同様 `list(dict.fromkeys(nodes))` で insertion-order + 重複除去 (sort なし — ROADMAP SC-2 は edges のみ sort 規定)
    - `CallGraph.edges` は emit 直前に `edges.sort(key=lambda e: (e.caller, e.callee))` で lex sort
    - 重複 edge は sort 後も保持 (e.g., 同名 callee が 2 件あれば 2 件のまま、 sort で隣接化されるだけ)
    - `ast.parse` は呼ばない、 `_get_module_name` をローカル定義しない
    - module docstring: `Implements: AST-02, AST-05, DET-04` 行 + `Traces: AST-02, AST-05, DET-04, US-01, US-22, US-25` 行
  </behavior>
  <action>
    `lib_code_parser/extractors/primitives/callgraph.py` を新規作成。

    Module docstring (RESEARCH §6.3 template に準拠):
    ```
    """Python internal call graph extractor (pure CAV consumer, no GPL deps, no subprocess).

    Walks the CAV's ast.Module payload once and emits (caller, callee) edges.
    Resolution rules are inherited verbatim from v0.1.0 callgraph_builder.py
    (RESEARCH §4 for the full 7-fixture truth table):

    - self.foo() in method → callee is bare ``foo`` (not Class.foo)
    - chain a.b().c() → 2 edges (callee=c and callee=b), reflecting the AST walk
      visiting both Call nodes; future expansion deferred to Phase 3 if
      sequence-diagram rendering requires single-edge semantics
    - nested function bodies → callees flattened to the enclosing top-level /
      method node; nested function itself is NOT a graph node
    - deep attribute a.b.c.d() → 1 edge (callee=d, innermost Call only)
    - emission order before sort = v0.1.0 (classes+methods 1st pass, top-level
      functions 2nd pass, AST appearance order within each pass)
    - emission order after sort = lexicographic by (caller, callee) per DET-04

    Implements: AST-02, AST-05, DET-04
    Traces: AST-02, AST-05, DET-04, US-01, US-22, US-25
    """
    ```

    Imports:
    ```
    from __future__ import annotations
    import ast

    from lib_code_parser._paths import get_module_name
    from lib_code_parser.models.infrastructure.cav import CAV
    from lib_code_parser.models.infrastructure.config import ParserConfig
    from lib_code_parser.models.primitives.callgraph import CallEdge, CallGraph

    __all__ = ["extract"]
    ```

    Helpers (v0.1.0 callgraph_builder.py L14-32 verbatim、 module-private naming で):
    ```
    def _get_call_name(func_node: ast.expr) -> str | None:
        if isinstance(func_node, ast.Name):
            return func_node.id
        if isinstance(func_node, ast.Attribute):
            return func_node.attr
        return None


    def _collect_calls(body_nodes: list[ast.stmt]) -> list[str]:
        names: list[str] = []
        for stmt in body_nodes:
            for call in ast.walk(stmt):
                if isinstance(call, ast.Call):
                    name = _get_call_name(call.func)
                    if name:
                        names.append(name)
        return names
    ```

    Main extractor — v0.1.0 build_callgraph L35-66 のロジックを CAV consumer に書き換え、 末尾に DET-04 sort を 1 行追加:

    ```
    def extract(cav: CAV, config: ParserConfig) -> CallGraph:
        """AST-02: emit deterministic CallGraph from cav.payload (ast.Module).

        Sort invariant (DET-04 / ROADMAP Phase 2 SC-2): edges are lexicographically
        sorted by (caller, callee) before emission. Nodes are kept in insertion
        order with duplicate elimination via dict.fromkeys (v0.1.0 parity).

        config is accepted for FrontendFn/PrimitiveFn signature alignment but is
        not consumed; call graph extraction does not depend on per-config flags.
        """
        tree = cav.payload  # type: ignore[assignment]
        assert isinstance(tree, ast.Module), (
            f"callgraph extractor requires Python CAV (ast.Module payload), "
            f"got {type(tree).__name__}"
        )
        module_name = get_module_name(cav.path)
        nodes: list[str] = []
        edges: list[CallEdge] = []

        # 1st pass: classes and their methods (v0.1.0 parity emit order)
        for top_node in tree.body:
            if isinstance(top_node, ast.ClassDef):
                class_id = f"{module_name}.{top_node.name}"
                nodes.append(class_id)
                for item in top_node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"{module_name}.{top_node.name}.{item.name}"
                        nodes.append(method_id)
                        for callee in _collect_calls(item.body):
                            edges.append(CallEdge(caller=method_id, callee=callee))

        # 2nd pass: top-level functions
        for top_node in tree.body:
            if isinstance(top_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_id = f"{module_name}.{top_node.name}"
                nodes.append(func_id)
                for callee in _collect_calls(top_node.body):
                    edges.append(CallEdge(caller=func_id, callee=callee))

        # DET-04 / ROADMAP Phase 2 SC-2: edge sort by (caller, callee) lex
        edges.sort(key=lambda e: (e.caller, e.callee))

        return CallGraph(nodes=list(dict.fromkeys(nodes)), edges=edges)
    ```

    重複 edge dedup は **行わない** (v0.1.0 parity)。 nodes は `dict.fromkeys` で順序保持 dedup。

    `_dispatch.PRIMITIVES["call_graph"]` への登録は Plan 02-06 (Wave 2 closer) が排他保有。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/extractors/test_callgraph_extractor.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `python -c "from lib_code_parser.extractors.primitives.callgraph import extract; print(extract.__name__)"` 出力 `extract`
    - `grep -c "ast\.parse" lib_code_parser/extractors/primitives/callgraph.py` が 0
    - `grep -c "^def _get_module_name\|^def get_module_name" lib_code_parser/extractors/primitives/callgraph.py` が 0
    - `grep -c "from lib_code_parser\._paths import get_module_name" lib_code_parser/extractors/primitives/callgraph.py` が 1
    - `grep -c "edges.sort" lib_code_parser/extractors/primitives/callgraph.py` >= 1 (DET-04 sort 行の存在 grep 証跡)
    - `grep -c "(e.caller, e.callee)" lib_code_parser/extractors/primitives/callgraph.py` >= 1 (sort key)
    - `grep -c "Implements: AST-02" lib_code_parser/extractors/primitives/callgraph.py` = 1 (TRC-02)
    - `grep -c "Traces: AST-02" lib_code_parser/extractors/primitives/callgraph.py` >= 1 (TRC-03)
    - Plan 02-01 AST-05 parity: `pytest tests/parity/test_ast_05_one_parse.py -x -q` exit 0 (extractors/ 0 件 grep gate 維持)
    - Phase 1 baseline parity: `pytest tests/acceptance/ tests/parity/ -x -q` exit 0
    - `ruff check lib_code_parser/extractors/primitives/callgraph.py` exit 0
  </acceptance_criteria>
  <done>callgraph extractor が v0.1.0 解像度 + DET-04 sort で実装され、 isolated call 可能。 AST-05 grep gate / ARC-04 no-duplication gate ともに維持。</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Wave 0 — tests/unit/extractors/test_callgraph_extractor.py (v0.1.0 解像度 7 件 + isolated import)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/acceptance/test_fr02_callgraph.py (v0.1.0 acceptance — fixture 単位の assertion を unit に持ち上げる; acceptance 本体は Plan 02-07 で書き換え)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§4.1 CG1-CG7 fixture truth table、 §Pitfall 4 chain call 早期警告)
  </read_first>
  <behavior>
    Tests in `tests/unit/extractors/test_callgraph_extractor.py` (RESEARCH §4.1 fixture を 1:1 で unit 化):

    1. `test_self_dot_foo_resolves_to_bare_name` (CG1) — `class Foo:\n    def bar(self):\n        self.baz()` → edges に `CallEdge(caller="m.Foo.bar", callee="baz")` が含まれる (Class.baz でなく bare baz)
    2. `test_chain_call_emits_two_edges` (CG2 + RESEARCH Pitfall 4 早期警告) — `def outer():\n    a.b().c()` → edges に `(outer, c)` と `(outer, b)` の 2 件が両方含まれる。 sort 後の順序は `(outer, b)` → `(outer, c)` (lex)
    3. `test_duplicate_callee_not_deduped` (CG3) — `from other import helper\ndef outer():\n    helper()\n    other.helper()` → edges に `(outer, helper)` が 2 件 (重複保持、 dedup なし)
    4. `test_nested_function_flattened_to_outer` (CG4) — nested `def inner` 内の `leaf()` 呼び出しが `(outer, leaf)` として emit され、 `inner` は node リストに含まれない
    5. `test_staticmethod_classmethod_treated_as_method` (CG5) — `class Foo:\n    @staticmethod\n    def smethod(): ...\n    @classmethod\n    def cmethod(cls): ...` → nodes に `m.Foo.smethod` / `m.Foo.cmethod` が含まれる
    6. `test_deep_attribute_innermost_only` (CG7) — `def outer():\n    a.b.c.d()` → edges に `(outer, d)` の 1 件のみ
    7. `test_edges_lex_sorted_by_caller_callee` (DET-04 + ROADMAP SC-2) — `def b():\n    z(); a(); m()` → edges = `[(m.b, a), (m.b, m), (m.b, z)]` (lex sort 後)
    8. `test_nodes_insertion_order_with_dedup` — 同じ class/method/function を重複定義しても nodes は dict.fromkeys で uniqueness
    9. `test_isolated_import_no_executor` — `CodeParserExecutor` 一切 import せず `extract(cav, config)` 直接呼び出しで完結 (ROADMAP SC-4)
    10. `test_extract_on_example_source` — `EXAMPLE_SOURCE` conftest fixture を build_cav 経由で CAV にして渡し、 `create_order` method が `_calculate_total` を caller→callee として持つことを assert (v0.1.0 acceptance test_fr02 と semantic parity)
  </behavior>
  <action>
    `tests/unit/extractors/test_callgraph_extractor.py` を新規作成。 `tests/unit/extractors/__init__.py` は Plan 02-02 Task 2 が作成済 (両 plan が同じ Wave 1 なので、 どちらが先に commit するかで `__init__.py` 重複作成を避ける必要あり)。

    file-ownership 競合の回避策: Plan 02-02 と 02-03 の **両方** が `__init__.py` を作る記述を持つが、 内容は 1-line docstring で同一なので merge 衝突は起きない。 Wave 1 並列実行時に「先に走ったほうが ok、 後発は既存ファイルを上書きしないこと」を action 内で明示。

    上記 10 件の test を関数群として実装する。 共通 fixture は次の通り (Plan 02-02 と同形式):

    ```
    from __future__ import annotations
    import pytest

    from lib_code_parser.extractors.primitives.callgraph import extract
    from lib_code_parser.frontends.python import build_cav
    from lib_code_parser.models.infrastructure.config import ParserConfig


    def _build_cav(source: str, path: str = "m.py"):
        config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
        return build_cav(source.encode("utf-8"), path, config)


    @pytest.fixture
    def config():
        return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    ```

    test 内で `ast.parse` を **直接呼ばない** (RESEARCH §Pitfall 7 + Plan 02-01 AST-05 grep gate 整合)。 CAV は `_build_cav(source)` 経由で作る。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/extractors/test_callgraph_extractor.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/extractors/test_callgraph_extractor.py -x -q` exit 0 with 10 件 pass
    - `grep -E -c "ast\\.parse\\(" tests/unit/extractors/test_callgraph_extractor.py` が 0
    - `grep -c "from lib_code_parser.frontends.python import build_cav" tests/unit/extractors/test_callgraph_extractor.py` が 1
    - フル baseline: `pytest tests/ -x -q` exit 0
    - `ruff check tests/unit/extractors/test_callgraph_extractor.py` exit 0
  </acceptance_criteria>
  <done>RESEARCH §4.1 fixture 7 件 + sort 1 件 + dedup 1 件 + isolated 1 件 = 10 件の unit が green。 v0.1.0 解像度 rule が unit でロックされ、 Phase 3 拡張時の breaking 検出基盤が立つ。</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Wave 0 — tests/unit/test_callgraph_sort.py (VALIDATION.md 必須リスト, DET-04 sort 単独 unit)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-VALIDATION.md (Wave 0 required: `tests/unit/test_callgraph_sort.py`)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§4.2 sort 行のサンプル + ROADMAP SC-2)
  </read_first>
  <behavior>
    Tests in `tests/unit/test_callgraph_sort.py` (DET-04 invariant を AST-02 extractor の出力上で再確認する小さな gate):

    1. `test_edges_are_lex_sorted_for_simple_fixture` — `def b():\n    z(); a(); m()\ndef a():\n    pass` の callgraph で edges が `(m.a, *) < (m.b, *)` 順、 `m.b` の callee 群が `a < m < z` 順
    2. `test_edges_sort_is_stable_across_runs` — 同 source を 3 回 extract した結果が byte-identical (CallGraph.model_dump_json 文字列が 3 回とも等しい) — DET-01 byte-identical の前提となる安定性を確認
    3. `test_edges_sort_handles_empty_callgraph` — `class Empty: pass` → edges = []、 sort 適用後も問題なし (empty list の sort)
    4. `test_edges_sort_with_duplicates_preserves_count` — CG3 同様の duplicate edge を持つ source で sort 後の edge 数が変わらない (dedup していないことを再確認)
  </behavior>
  <action>
    `tests/unit/test_callgraph_sort.py` を新規作成 (`tests/unit/` 直下、 `extractors/` 配下ではない — VALIDATION.md の path に合わせる)。 Module docstring に「ROADMAP Phase 2 SC-2 invariant: edges lex-sorted by (caller, callee)」を 1 paragraph で記載。

    上記 4 件を実装。 共通 helper:

    ```
    from __future__ import annotations
    import pytest

    from lib_code_parser.extractors.primitives.callgraph import extract
    from lib_code_parser.frontends.python import build_cav
    from lib_code_parser.models.infrastructure.config import ParserConfig


    def _cg(source: str):
        config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
        cav = build_cav(source.encode("utf-8"), "m.py", config)
        return extract(cav, config)
    ```

    `test_edges_sort_is_stable_across_runs` では `_cg(src).model_dump_json()` を 3 回呼び、 3 文字列が全部等しいことを assert。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/test_callgraph_sort.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/test_callgraph_sort.py -x -q` exit 0 with 4 件 pass
    - `grep -E -c "ast\\.parse\\(" tests/unit/test_callgraph_sort.py` が 0
    - `grep -c "model_dump_json" tests/unit/test_callgraph_sort.py` >= 1 (byte-identical stability test の根拠)
    - Plan 02-01 AST-05 parity: `pytest tests/parity/test_ast_05_one_parse.py -x -q` exit 0
    - フル baseline: `pytest tests/ -x -q` exit 0
    - `ruff check tests/unit/test_callgraph_sort.py` exit 0
  </acceptance_criteria>
  <done>DET-04 sort と byte-identical stability が CallGraph emit 出力上で確認される。 VALIDATION.md Wave 0 必須リストの `tests/unit/test_callgraph_sort.py` を charge close。</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| CAV.payload (ast.Module) → walk / Call resolution | payload 形状は Frontend が保証するが、 isolated call 時の caller 任意性は `isinstance(tree, ast.Module)` assert で防御 |
| edges 重複 → CallGraph emit | v0.1.0 parity で意図的に dedup していない。 caller (verifier) がこの重複を「ノイズ」と受け取らない rationale は ContractInfo と同様、 verifier 側が物理↔論理ギャップを解釈する Core Value に整合 |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-11 | Tampering | AST-05 違反: 本 plan が `ast.parse` を引き入れる | mitigate | Task 1 acceptance grep gate + Plan 02-01 parity test |
| T-02-12 | Tampering | DET-04 sort 適用忘れで `(caller, callee)` lex 順が壊れる | mitigate | Task 1 acceptance に `edges.sort` + `(e.caller, e.callee)` grep 証跡、 Task 2 と Task 3 の unit で実機 fire 検証 |
| T-02-13 | Tampering | ARC-04 違反: `_get_module_name` ローカル定義 | mitigate | Task 1 acceptance grep gate |
| T-02-14 | Information disclosure | nested function flatten で機微情報 (内部関数名) が混入 | accept | v0.1.0 parity 維持の意図的選択。 verifier 側で解釈責任 |
| T-02-15 | Supply chain | 新規依存なし | accept | stdlib `ast`、 Phase 1 declared |
</threat_model>

<verification>
- `pytest tests/unit/extractors/test_callgraph_extractor.py tests/unit/test_callgraph_sort.py -x -q` 14 件 pass
- AST-05 grep gate (Plan 02-01 parity): `grep -rn -E "ast\.parse\(|from ast import parse" lib_code_parser/extractors/` = 0 件
- DET-04 sort grep: `grep -c "edges.sort" lib_code_parser/extractors/primitives/callgraph.py` >= 1
- ARC-04 no-duplication grep gate: 1 件 (`_paths.py`)
- TRC-02 / TRC-03 grep on callgraph.py
- フル baseline: `pytest tests/ -x -q` exit 0
- `ruff check lib_code_parser/extractors/ tests/unit/` exit 0
</verification>

<success_criteria>
- ROADMAP Phase 2 success criterion 2 の「内製 CallGraph + `(caller, callee)` lex sort」を成立
- ROADMAP Phase 2 success criterion 4 のうち callgraph extractor の isolated call 性を成立
- v0.1.0 解像度 rule の 7 fixture parity が unit でロック (Phase 3 拡張時の breaking 検出基盤)
- DET-04 invariant が edges 出力上で固定 + byte-identical stability が確認
- TRC-02 docstring 形式と TRC-03 regex 抽出が callgraph.py で確立
</success_criteria>

<output>
Create `.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-03-SUMMARY.md` when done. Include:
1. pytest output (Plan 02-03 contribution counts)
2. AST-05 grep gate / ARC-04 no-duplication grep gate / DET-04 sort grep evidence
3. RESEARCH §4.1 7-fixture truth table の unit カバレッジ (どの test が CG1-CG7 を担当しているか)
4. v0.1.0 baseline parity 維持の証跡
</output>
