---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/extractors/primitives/functions.py
  - tests/unit/extractors/__init__.py
  - tests/unit/extractors/test_functions_extractor.py
autonomous: true
requirements: [AST-01, AST-05, TRC-02, TRC-03]
must_haves:
  truths:
    - "Caller can write `from lib_code_parser.extractors.primitives.functions import extract; extract(cav, config)` and gets a list[FunctionNode] without instantiating CodeParserExecutor (ROADMAP Phase 2 SC-4 sub-clause)"
    - "extract(cav, config) re-uses cav.payload (an already-parsed ast.Module) and never calls ast.parse() — verified by Plan 02-01's parity test"
    - "Emitted FunctionNode entries match v0.1.0 ast_extractor.extract_functions output for the conftest EXAMPLE_SOURCE fixture: same node_id format, same kind discriminator ('function'|'method'|'class'), same skip_self_cls semantics, same _extract_annotation result, same docstring extraction, same source_range tuples, same TraceTag tags (TRC-03 verbatim regex parity)"
    - "Module docstring contains 'Implements: AST-01, AST-05' (TRC-02 gate) AND 'Traces: AST-01, AST-05, US-01, US-22' (TRC-03 regex gate)"
    - "Module imports get_module_name from lib_code_parser._paths (ARC-04 single source) — no local _get_module_name function definition (no-duplication grep gate continues to pass)"
  artifacts:
    - path: "lib_code_parser/extractors/primitives/functions.py"
      provides: "Pure-CAV FunctionNode extractor (AST-01) — v0.1.0 logic ported to CAV consumer signature"
      contains: "def extract"
    - path: "tests/unit/extractors/test_functions_extractor.py"
      provides: "Unit tests covering kind discriminator / skip_self_cls / TraceTag parity / source_range / docstring extraction"
      contains: "def test_extract"
  key_links:
    - from: "extractors/primitives/functions.py::extract"
      to: "CAV.payload (ast.Module)"
      via: "no re-parse, pulls cav.payload directly"
      pattern: "cav\\.payload"
    - from: "extractors/primitives/functions.py::extract"
      to: "lib_code_parser._paths.get_module_name"
      via: "ARC-04 single source import"
      pattern: "from lib_code_parser\\._paths import get_module_name"
---

<objective>
Wave 1 並列の 2 件目。 v0.1.0 `lib_code_parser/ast_extractor.py` の AST 走査ロジック (FunctionNode 抽出 + ParamInfo + SourceRange + TraceTag) を、 CAV consumer signature `extract(cav, config) -> list[FunctionNode]` に書き換えて `lib_code_parser/extractors/primitives/functions.py` に新規実装する。 v0.1.0 が持っていた `_extract_annotation` / `_extract_trace_tags` / `_make_source_range` / `_extract_params` の 4 helper はそのまま継承するが、 module-level `_get_module_name` は **本ファイルで定義しない** (`_paths.get_module_name` を import するのみ) — Phase 1 D-01 / ARC-04 / DET-04 の no-duplication 不変条件を継続。 ast.parse は **呼ばない** (Plan 02-01 の grep static gate が `extractors/` 配下を 0 件で固定するため、 本ファイル内で `ast.parse` が出現してはならない)。

TRC-03 の `_extract_trace_tags` 正規表現 `r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)"` は v0.1.0 ast_extractor.py L28 から **1 文字も変えずに verbatim 移植** する (RESEARCH §6.4 + TRC-03 success criterion)。

Purpose: ROADMAP Phase 2 success criterion 1 (FunctionNode 抽出) と criterion 4 (各 extractor が isolated 呼び出し可能) を AST-01 について成立させる。 同時に TRC-02 (docstring 内 `Implements: AST-NN` 宣言) と TRC-03 (Traces regex parity) を本ファイルで初の実例として確立する。

Output:
- `lib_code_parser/extractors/primitives/functions.py` — 新規 1 ファイル、 `extract(cav, config)` + 4 internal helper + module docstring (TRC-02/TRC-03 形式)
- `tests/unit/extractors/__init__.py` — empty pytest 包装
- `tests/unit/extractors/test_functions_extractor.py` — 8 件以上の unit (kind / params / return_type / docstring / TraceTag / source_range / class+method 階層 / isolated call 性)
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
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/ast_extractor.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_paths.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/cav.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/config.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/functions.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/conftest.py

<interfaces>
<!-- Phase 1 locked FunctionNode / ParamInfo / SourceRange / TraceTag models — they live in
     lib_code_parser/models/primitives/functions.py and are unchanged in Phase 2. The Phase
     2 extractor produces these exact models. -->

class TraceTag(BaseModel):
    tag: str
    refs: list[str] = []

class SourceRange(BaseModel):
    start_line: int
    end_line: int

class ParamInfo(BaseModel):
    name: str
    type_annotation: str = ""

class FunctionNode(BaseModel):
    node_id: str
    kind: str  # "function" | "method" | "class"
    params: list[ParamInfo] = []
    return_type: str = ""
    contracts: ContractInfo  # default factory — NOT populated by AST-01 extractor; the
                              # executor (Plan 02-06) merges ContractInfo into FunctionNode
                              # after both AST-01 and AST-04 extractors return.
    docstring: str = ""
    trace_tags: list[TraceTag] = []
    source_range: SourceRange

<!-- v0.1.0 ast_extractor.extract_functions semantics that Plan 02-02 inherits verbatim:
     1. class node_id = f"{module_name}.{class.name}"
     2. method node_id = f"{module_name}.{class.name}.{method.name}", skip_self_cls=True
     3. top-level function node_id = f"{module_name}.{func.name}", skip_self_cls=False
     4. _extract_annotation = ast.unparse(node) (return "" if node is None)
     5. _extract_trace_tags regex = r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)"
     6. _make_source_range start_line=node.lineno, end_line=node.end_lineno or node.lineno
     7. emit order: first pass = classes + their methods, second pass = top-level functions -->

<!-- AST-05 grep gate from Plan 02-01: lib_code_parser/extractors/ MUST have 0 matches
     of `ast.parse(` or `from ast import parse`. -->
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement lib_code_parser/extractors/primitives/functions.py (CAV consumer + v0.1.0 parity)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/ast_extractor.py (v0.1.0 reference — extract_functions + 4 helpers; copy semantics verbatim except (a) signature is now (cav, config), (b) ast.parse is gone, (c) module_name is sourced from _paths.get_module_name)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/functions.py (Phase 1 locked models — match emitted Pydantic shape)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_paths.py (single source for get_module_name)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§6.3 docstring template for extractors/primitives/functions.py + §7.1 v0.1.0 parity table — emit order is "classes+methods first, then top-level functions, no DET-04 sort applied" because ROADMAP SC-1 規定なし)
  </read_first>
  <behavior>
    - `from lib_code_parser.extractors.primitives.functions import extract` 成功 (ROADMAP SC-4 — isolated import)
    - `extract(cav, config)` で `cav.payload` (`ast.Module`) を 1 回 walk し、 class / method / top-level function ごとに `FunctionNode` を emit
    - emit 順 = v0.1.0 順 = (1st pass) ast.body の各 ClassDef を順に → クラス自身 + その body 内 FunctionDef / AsyncFunctionDef を順に → (2nd pass) ast.body の各 FunctionDef / AsyncFunctionDef (top-level) を順に。 ROADMAP SC-1 で `DET-04 sort` は規定されていないため、 v0.1.0 emit 順を厳密に維持する (parity baseline)。
    - `_extract_trace_tags` 内の regex は v0.1.0 と **byte-identical**: `r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)"`、 `re.MULTILINE` flag 付き
    - module-level `_get_module_name` 関数は **定義しない**。 module top で `from lib_code_parser._paths import get_module_name` のみを import (`as _get_module_name` alias は本ファイルでは不要 — 新規ファイルで v0.1.0 private symbol を維持する必要なし; Phase 2 D-01 clean break で legacy symbol path は閉じる)
    - `ast.parse` は **import しない / 呼ばない**: `import ast` は OK (ast.Module / ast.FunctionDef 等の型を使う)、 しかし `ast.parse(` / `from ast import parse` は appear しない
    - module docstring に `Implements: AST-01, AST-05` 行と `Traces: AST-01, AST-05, US-01, US-22` 行を含む
  </behavior>
  <action>
    `lib_code_parser/extractors/primitives/functions.py` を新規作成。 全 imports は absolute。

    Module docstring (RESEARCH §6.3 template に準拠):
    ```
    """Python AST → FunctionNode extractor (pure CAV consumer).

    Walks the CAV's ast.Module payload once and emits FunctionNode entries for
    each class, method, and top-level function with kind/params/return_type/
    docstring/trace_tags/source_range populated.

    The TRC-03 trace-tag regex is preserved verbatim from v0.1.0 ast_extractor.py
    (`r"Traces:\\s*([A-Z]+-\\d+(?:\\s*,\\s*[A-Z]+-\\d+)*)"`) so the same
    `Traces:` lines extracted in v0.1.0 are extracted in v0.2.0 byte-identically.

    Implements: AST-01, AST-05
    Traces: AST-01, AST-05, US-01, US-22
    """
    ```

    Imports:
    ```
    from __future__ import annotations
    import ast
    import re

    from lib_code_parser._paths import get_module_name
    from lib_code_parser.models.infrastructure.cav import CAV
    from lib_code_parser.models.infrastructure.config import ParserConfig
    from lib_code_parser.models.primitives.functions import (
        FunctionNode,
        ParamInfo,
        SourceRange,
        TraceTag,
    )

    __all__ = ["extract"]
    ```

    Helper functions — 4 件、 v0.1.0 ast_extractor.py L18-52 のロジックを verbatim 移植 (ast.parse は呼ばないので signature 内では現れない):

    ```
    _TRACE_TAGS_RE = re.compile(
        r"Traces:\s*([A-Z]+-\d+(?:\s*,\s*[A-Z]+-\d+)*)", re.MULTILINE
    )


    def _extract_annotation(node: ast.expr | None) -> str:
        if node is None:
            return ""
        return ast.unparse(node)


    def _extract_trace_tags(docstring: str) -> list[TraceTag]:
        tags: list[TraceTag] = []
        for m in _TRACE_TAGS_RE.finditer(docstring):
            refs = [r.strip() for r in m.group(1).split(",")]
            tags.append(TraceTag(tag="Traces", refs=refs))
        return tags


    def _make_source_range(
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    ) -> SourceRange:
        end = node.end_lineno if node.end_lineno is not None else node.lineno
        return SourceRange(start_line=node.lineno, end_line=end)


    def _extract_params(
        args: ast.arguments, skip_self_cls: bool = True
    ) -> list[ParamInfo]:
        params: list[ParamInfo] = []
        for arg in args.args:
            if skip_self_cls and arg.arg in ("self", "cls"):
                continue
            params.append(
                ParamInfo(
                    name=arg.arg,
                    type_annotation=_extract_annotation(arg.annotation),
                )
            )
        return params
    ```

    Main extractor — v0.1.0 ast_extractor.py L55-117 (`extract_functions`) のロジックを CAV consumer に書き換え:

    ```
    def extract(cav: CAV, config: ParserConfig) -> list[FunctionNode]:
        """AST-01: emit FunctionNode list from cav.payload (ast.Module).

        config is accepted for FrontendFn / PrimitiveFn signature alignment but
        is not currently consumed (FunctionNode extraction does not depend on
        per-config flags). Phase 3+ may use config.python_version for
        language-version-aware annotation parsing.
        """
        tree = cav.payload  # type: ignore[assignment]  # ast.Module — declared opaque in CAV
        assert isinstance(tree, ast.Module), (
            f"functions extractor requires Python CAV (ast.Module payload), "
            f"got {type(tree).__name__}"
        )
        module_name = get_module_name(cav.path)
        functions: list[FunctionNode] = []

        # First pass: process classes and their methods (v0.1.0 parity emit order)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_id = f"{module_name}.{node.name}"
                doc = ast.get_docstring(node) or ""
                trace_tags = _extract_trace_tags(doc)
                functions.append(
                    FunctionNode(
                        node_id=class_id,
                        kind="class",
                        docstring=doc,
                        trace_tags=trace_tags,
                        source_range=_make_source_range(node),
                    )
                )
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"{module_name}.{node.name}.{item.name}"
                        method_doc = ast.get_docstring(item) or ""
                        method_tags = _extract_trace_tags(method_doc)
                        functions.append(
                            FunctionNode(
                                node_id=method_id,
                                kind="method",
                                params=_extract_params(item.args, skip_self_cls=True),
                                return_type=_extract_annotation(item.returns),
                                docstring=method_doc,
                                trace_tags=method_tags,
                                source_range=_make_source_range(item),
                            )
                        )

        # Second pass: top-level functions (v0.1.0 parity)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_id = f"{module_name}.{node.name}"
                doc = ast.get_docstring(node) or ""
                tags = _extract_trace_tags(doc)
                functions.append(
                    FunctionNode(
                        node_id=func_id,
                        kind="function",
                        params=_extract_params(node.args, skip_self_cls=False),
                        return_type=_extract_annotation(node.returns),
                        docstring=doc,
                        trace_tags=tags,
                        source_range=_make_source_range(node),
                    )
                )

        return functions
    ```

    `_dispatch.PRIMITIVES["functions"]` への登録は **本 plan では行わない**。 _dispatch.py は Plan 02-06 (Wave 2 closer) が排他的に保有・編集する (file-ownership 競合回避)。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/extractors/test_functions_extractor.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `python -c "from lib_code_parser.extractors.primitives.functions import extract; print(extract.__name__)"` が `extract` を出力 (isolated import)
    - `grep -c "ast\.parse" lib_code_parser/extractors/primitives/functions.py` が 0 を返す (AST-05 grep gate 適合)
    - `grep -c "^def _get_module_name\|^def get_module_name" lib_code_parser/extractors/primitives/functions.py` が 0 を返す (ARC-04 / DET-04 no-duplication 維持)
    - `grep -c "from lib_code_parser\._paths import get_module_name" lib_code_parser/extractors/primitives/functions.py` が 1 を返す
    - `grep -c "Implements: AST-01" lib_code_parser/extractors/primitives/functions.py` が 1 (TRC-02)
    - `grep -c "Traces: AST-01" lib_code_parser/extractors/primitives/functions.py` が 1 以上 (TRC-03 regex 引っかかり)
    - `grep -c "Traces:" lib_code_parser/extractors/primitives/functions.py` >= 1 (regex 抽出可能)
    - `grep -E -c 'Traces:\\\\s\*\(' lib_code_parser/extractors/primitives/functions.py` 該当 regex 文字列が 1 件 (v0.1.0 verbatim 再利用)
    - Phase 1 baseline parity: `pytest tests/acceptance/ tests/parity/ -x -q` exit 0
    - Plan 02-01 で立てた AST-05 parity: `pytest tests/parity/test_ast_05_one_parse.py -x -q` exit 0 (`extractors/` 配下に新規 functions.py を入れても 0 件 grep gate を破らない)
    - `ruff check lib_code_parser/extractors/primitives/functions.py` exit 0
  </acceptance_criteria>
  <done>functions extractor が CAV consumer signature で実装され、 v0.1.0 emit 順 + node_id 形式 + skip_self_cls + TraceTag regex (verbatim) parity を維持。 AST-05 grep gate と ARC-04 no-duplication gate を破らない。</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Wave 0 — tests/unit/extractors/test_functions_extractor.py (8 件以上の unit)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/acceptance/test_fr01_function_extraction.py (v0.1.0 acceptance — 13 件中の主要 assertion を CAV signature に持ち上げた unit に変換する。 acceptance test 本体は Plan 02-07 で書き換え)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/conftest.py (`EXAMPLE_SOURCE` fixture を test 内で参照する。 ただし `build_cav` は Plan 02-01 の deliverable なので、 unit 内では直接 `ast.parse` で CAV を組み立てるのではなく `build_cav` を import して使う — AST-05 parity gate 内で test 内 `ast.parse` 呼び出しが catch されるリスクを避ける)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§Pitfall 7 — test 内で `ast.parse` を直接呼ぶと AST-05 hard gate の意図と乖離。 推奨: test fixture 内で `build_cav` を import して CAV を組み立てる)
  </read_first>
  <behavior>
    Tests in `tests/unit/extractors/test_functions_extractor.py` (関数群、 class 包装は任意):

    1. `test_extract_class_node` — `EXAMPLE_SOURCE` から `order_service.OrderService` が `kind="class"` で出る
    2. `test_extract_method_node` — `order_service.OrderService.create_order` が `kind="method"` + `skip_self_cls=True` で出る (params に `self` が含まれない)
    3. `test_extract_top_level_function` — `order_service.process_payment` が `kind="function"` + params に `amount` / `method` が含まれる
    4. `test_extract_return_type_annotation` — `create_order` の `.return_type == "dict"`
    5. `test_extract_docstring` — `OrderService` の docstring に `"Order management service"` が含まれる
    6. `test_extract_trace_tags_verbatim_regex_parity` — `OrderService` docstring の `Traces: US-01, FR-02` から `TraceTag(tag="Traces", refs=["US-01", "FR-02"])` が抽出される。 v0.1.0 同 fixture の出力と byte-equal であることを assert (この test が TRC-03 success criterion を unit レベルで pin)
    7. `test_extract_source_range_positive` — `create_order` の `source_range.start_line > 0 and source_range.end_line >= source_range.start_line`
    8. `test_extract_emit_order_classes_first_then_top_level` — emit 順が「classes + methods、 その後 top-level functions」 (v0.1.0 parity emit order)
    9. `test_extract_isolated_call_without_executor` — `CodeParserExecutor` を一切 import せず `extract(cav, config)` 直接呼び出しで完結することを assert (ROADMAP SC-4)
    10. `test_extract_no_self_in_method_params` — `create_order` params に `self` 名が出現しないことを assert (skip_self_cls)
    11. `test_extract_no_self_for_top_level` — `process_payment` params に `amount` / `method` 両方が出現 (top-level は skip しない)
  </behavior>
  <action>
    `tests/unit/extractors/__init__.py` を空 (1-line docstring `"""Unit tests for primitive extractor functions."""`) で新規作成。

    `tests/unit/extractors/test_functions_extractor.py` を新規作成し、 上記 11 件の test を実装する。 各 test の共通 fixture は次の helper を使う:

    ```
    from __future__ import annotations
    import pytest

    from lib_code_parser.extractors.primitives.functions import extract
    from lib_code_parser.frontends.python import build_cav  # Plan 02-01 deliverable
    from lib_code_parser.models.infrastructure.config import ParserConfig
    from tests.conftest import EXAMPLE_SOURCE


    @pytest.fixture
    def example_cav():
        config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
        return build_cav(EXAMPLE_SOURCE.encode("utf-8"), "src/order_service.py", config)


    @pytest.fixture
    def example_config():
        return ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    ```

    全 test で `extract(example_cav, example_config)` を呼び、 戻り値の `list[FunctionNode]` を assert する。 test 内で `ast.parse` を直接呼ばないこと (RESEARCH §Pitfall 7 + AST-05 grep gate 整合)。

    `test_extract_trace_tags_verbatim_regex_parity` の expected 値は v0.1.0 ast_extractor.py の現実機 fire 結果を baseline とする: `OrderService` class docstring `Traces: US-01, FR-02` から `[TraceTag(tag="Traces", refs=["US-01", "FR-02"])]` が抽出される (1 つの TraceTag、 refs が 2 文字列)。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/extractors/test_functions_extractor.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/extractors/test_functions_extractor.py -x -q` が exit 0 with 11 tests passing
    - `grep -E -c "ast\\.parse\\(" tests/unit/extractors/test_functions_extractor.py` が 0 (Pitfall 7 回避、 test 内に ast.parse 直接呼び出しなし)
    - `grep -c "from lib_code_parser.frontends.python import build_cav" tests/unit/extractors/test_functions_extractor.py` が 1 (Frontend 経由で CAV を組み立てる pattern)
    - Plan 02-01 AST-05 parity: `pytest tests/parity/test_ast_05_one_parse.py -x -q` exit 0 (test ファイル追加が grep gate を破らない、 grep gate scope は `lib_code_parser/extractors/` だけ)
    - フル baseline: `pytest tests/ -x -q` exit 0
    - `ruff check tests/unit/extractors/` exit 0
  </acceptance_criteria>
  <done>functions extractor の 11 件 unit が green。 isolated call 性 (SC-4) と TRC-03 verbatim parity がコード単位で固定される。</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| CAV.payload (untrusted ast.Module) → extract logic | payload 形状は Frontend が作るが、 isolated call 時は caller が任意 object を渡せる。 `isinstance(tree, ast.Module)` assert で fail loudly |
| docstring text → re.findall (TraceTag extraction) | docstring 内の悪意あるパターンは ReDoS リスクなし (regex は固定 char class + 量詞のみ、 catastrophic backtracking なし) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-06 | Tampering | AST-05 違反: 本 plan が `ast.parse` を引き入れる | mitigate | Task 1 acceptance に `grep -c "ast\.parse" functions.py == 0` を組込み。 Plan 02-01 の parity gate が更に外周で catch |
| T-02-07 | Tampering | ARC-04 違反: `_get_module_name` ローカル定義 | mitigate | Task 1 acceptance で `grep -c "^def _get_module_name\|^def get_module_name" functions.py == 0` を assertion |
| T-02-08 | Information disclosure | CAV.payload が non-Python の場合 (例: cpp CAV) で混入 | mitigate | extract() 冒頭で `isinstance(tree, ast.Module)` assert (fail loudly + 開発者向けに型情報を提示) |
| T-02-09 | DoS | docstring 巨大化で TraceTag regex で性能劣化 | accept | regex は linear-time (no backtracking)、 v0.1.0 も同 regex で問題なし |
| T-02-10 | Supply chain | 新規 pip 依存なし | accept | stdlib `ast` / `re`、 Phase 1 で declared 済 |
</threat_model>

<verification>
- `pytest tests/unit/extractors/test_functions_extractor.py -x -q` 11 件 pass
- AST-05 grep gate: `grep -rn -E "ast\.parse\(|from ast import parse" lib_code_parser/extractors/` = 0 件 (Plan 02-01 parity test pass)
- ARC-04 no-duplication grep gate: `grep -rn -E "^def _get_module_name|^def get_module_name" lib_code_parser/` = 1 件 (`_paths.py:18`)
- TRC-02 grep: `grep -c "Implements: AST-01" lib_code_parser/extractors/primitives/functions.py` = 1
- TRC-03 regex (`r"Traces:\s*([A-Z]+-\d+...)"`) 検出: 同ファイル docstring から `[A-Z]+-\d+` 形式タグが抽出可能 (parity baseline)
- フル baseline: `pytest tests/ -x -q` exit 0
- `ruff check lib_code_parser/extractors/ tests/unit/extractors/` exit 0
</verification>

<success_criteria>
- ROADMAP Phase 2 success criterion 1 のうち FunctionNode 抽出 (kind / params / return_type / docstring / trace_tags / source_range) を成立
- ROADMAP Phase 2 success criterion 4 のうち functions extractor の isolated call 性 (`from lib_code_parser.extractors.primitives.functions import extract`) を成立
- TRC-02 docstring 内 `Implements: AST-01, AST-05` 宣言が確立
- TRC-03 trace tag regex の v0.1.0 verbatim parity がコード + unit でロック
</success_criteria>

<output>
Create `.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-02-SUMMARY.md` when done. Include:
1. pytest output (full test count + Plan 02-02 contribution)
2. AST-05 grep gate result (0 件 in extractors/)
3. ARC-04 no-duplication grep gate result (1 件 in _paths.py)
4. TRC-02 / TRC-03 grep evidence on functions.py
5. v0.1.0 baseline parity (Phase 1 187 tests still green)
</output>
