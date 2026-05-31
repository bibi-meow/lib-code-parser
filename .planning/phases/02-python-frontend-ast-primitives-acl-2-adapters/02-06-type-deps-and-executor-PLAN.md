---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 06
type: execute
wave: 2
depends_on: [02-01, 02-02, 02-03, 02-04, 02-05]
files_modified:
  - lib_code_parser/models/primitives/type_deps.py
  - lib_code_parser/extractors/primitives/type_deps.py
  - lib_code_parser/_dispatch.py
  - lib_code_parser/executor.py
  - tests/unit/models/test_type_deps_model.py
  - tests/unit/extractors/test_type_deps_extractor.py
  - tests/unit/test_executor_dispatch.py
autonomous: true
requirements: [AST-03, AST-05, DET-03, DET-04, ARC-03, TRC-02, TRC-03]
must_haves:
  truths:
    - "Caller can write `from lib_code_parser.extractors.primitives.type_deps import extract; extract(cav, config)` and gets list[TypeDep] populated via stdlib ast walk + pyright resolved annotation per RESEARCH §2.3 (CONTEXT.md D-07-revised algorithm)"
    - "TypeDep model carries new optional `resolved: bool = True` and `source_line: int = 0` fields (additive, default-bearing, no breaking change to Phase 1 TypeDep usage in CodeContent forward refs)"
    - "PyrightAdapter is invoked with cav.raw_content (carried by Plan 02-01 Frontend); when pyright fires reportMissingImports diagnostic on a given line, the TypeDep entries whose source_line falls within that diagnostic's start_line..end_line range have resolved=False; otherwise resolved=True (default)"
    - "Emitted TypeDep list is sorted by (source, target, kind, source_line) per DET-04 + RESEARCH §2.3 algorithm step 4 — sort key tuple is stable across runs (DET-01 byte-identical 前提)"
    - "_dispatch.py FRONTENDS['python'] = build_cav from frontends.python; PRIMITIVES contains 4 entries: 'functions' → functions.extract, 'call_graph' → callgraph.extract, 'type_deps' → type_deps.extract, 'contracts' → contracts.extract (Open-Closed invariant #4 — append-only registration)"
    - "executor.py is rewritten as dispatch-dict-driven (D-03): the execute() method walks FRONTENDS[config.language] for CAV construction then PRIMITIVES.items() for each primitive output, applying config.extract_contracts to gate the contracts entry; ContractInfo entries are merged into matching FunctionNode.contracts after both AST-01 and AST-04 extractors return (v0.1.0 parity for FunctionNode.contracts merger semantics)"
    - "CodeContent gains a typed view that contains all 4 primitives: functions / call_graph / type_deps / contracts — Phase 1 model already supports this via forward-refs (artifact.py lines 56-70)"
    - "executor.py uses the TYPED ParserConfig (lib_code_parser.models.infrastructure.config.ParserConfig) not the v0.1.0 stub — barrel-level ParserConfig graduation to typed variant is part of THIS plan (Plan 02-07 closer no longer needs to do graduation; Plan 02-07 only handles legacy file deletion + parity test redesign + acceptance test rewrites)"
    - "Each extractor module's `Implements: AST-NN` docstring line is preserved (TRC-02 grep gate continues to pass after Wave 2 integration)"
  artifacts:
    - path: "lib_code_parser/models/primitives/type_deps.py"
      provides: "TypeDep model with additive resolved + source_line fields"
      contains: "resolved|source_line"
    - path: "lib_code_parser/extractors/primitives/type_deps.py"
      provides: "TypeDep extractor — RESEARCH §2.3 hybrid algorithm (ast walk + pyright reportMissingImports annotation)"
      contains: "def extract"
    - path: "lib_code_parser/_dispatch.py"
      provides: "FRONTENDS / PRIMITIVES populated with 1 + 4 entries"
      contains: 'FRONTENDS\["python"\]|PRIMITIVES\["functions"\]'
    - path: "lib_code_parser/executor.py"
      provides: "Dispatch-dict-driven executor (D-03) consuming typed ParserConfig"
      contains: "FRONTENDS\\[|PRIMITIVES\\["
  key_links:
    - from: "extractors/primitives/type_deps.py::extract"
      to: "adapters.pyright.PyrightAdapter.analyze(cav.raw_content, cav.path)"
      via: "diagnostic-driven resolved annotation"
      pattern: "PyrightAdapter|reportMissingImports"
    - from: "executor.py"
      to: "_dispatch.FRONTENDS / _dispatch.PRIMITIVES"
      via: "dict walk per D-03"
      pattern: "FRONTENDS\\[|PRIMITIVES\\["
    - from: "executor.py"
      to: "models.infrastructure.config.ParserConfig (typed)"
      via: "barrel graduation"
      pattern: "from lib_code_parser\\.models\\.infrastructure\\.config import ParserConfig"
---

<objective>
Wave 2 sequential closer for Phase 2 production code. Wave 1 で並列に確立した 4 extractor + Frontend + PyrightAdapter を統合して end-to-end の Python parser pipeline を稼働させる。 具体的に以下を実装する:

1. **TypeDep model 拡張** (`models/primitives/type_deps.py`): 既存 `source / target / kind` に `resolved: bool = True` と `source_line: int = 0` を additive で追加。 default 値で Phase 1 forward-ref 使用は破壊しない。 Open-Closed invariant #3 (`CodeContent` への追加は optional field) と整合。

2. **type_deps extractor** (`extractors/primitives/type_deps.py`): RESEARCH §2.3 algorithm を実装:
   - Step 1: stdlib ast walk で `ast.Import` / `ast.ImportFrom` / annotation type 名を抽出 (v0.1.0 `type_dep_builder.py` の logic を verbatim 流用)、 各 TypeDep に source_line を記録
   - Step 2: `PyrightAdapter(python_version=config.python_version).analyze(cav.raw_content, cav.path)` を呼び PyrightOutput を取得
   - Step 3: 各 TypeDep について「source_line が `reportMissingImports` 発火行 range に含まれる」場合 `resolved=False`、 そうでなければ `resolved=True` (default) を annotate
   - Step 4: `(source, target, kind, source_line)` で sort して emit (DET-04)

3. **_dispatch.py 登録** (D-12 append-only): `FRONTENDS["python"] = build_cav`、 `PRIMITIVES["functions" | "call_graph" | "type_deps" | "contracts"]` を 4 件 register。

4. **executor.py rewrite** (D-03): if/elif の v0.1.0 logic を破棄し、 dispatch dict walk 型に書き換え:
   - `if not config.enabled` → 空 CodeContent 返却 (v0.1.0 parity)
   - C++ extension detection → 空 CodeContent 返却 (Phase 4 で本実装、 現状は Phase 1 v0.1.0 と同じ早期 return)
   - `frontend = FRONTENDS[config.language]` → `cav = frontend(raw_content, path, config)`
   - `for primitive_name, primitive_fn in PRIMITIVES.items(): result[primitive_name] = primitive_fn(cav, config)` (順序 = dict 挿入順 = D-12 append-only 順)
   - `extract_contracts` の戻り値を AST-01 functions と merge: `for fn in functions: if fn.node_id in contracts: fn.contracts = contracts[fn.node_id]` (v0.1.0 parity)
   - `config.extract_contracts == False` 時は contracts dict を空に skip
   - 最終 `CodeContent(functions=..., call_graph=..., type_deps=..., contracts=...)` を NormalizedArtifact に包んで返す

5. **typed ParserConfig graduation** (D-01 / D-12 の半分): executor.py が `from lib_code_parser.models.infrastructure.config import ParserConfig` を import するように変更 (v0.1.0 stub `lib_code_parser.models.ParserConfig` の依存は executor 内部から消える)。 barrel `lib_code_parser.ParserConfig` の置き換えは Plan 02-07 (Wave 3 closer) が行う — 本 plan は executor 内部のみ。

Phase 1 acceptance test (`tests/acceptance/test_fr01..03/05/06`) は v0.1.0 stub `ParserConfig` を渡す形式なので、 executor が typed に切り替わると **明示的に壊れる**: stub の `params: dict[str, object]` が typed に存在しないため `AttributeError`。 これは Plan 02-07 で「acceptance test を typed ParserConfig + CAV signature に書き換え」する範囲。 本 plan の acceptance では Plan 02-04 で既に壊れている test_fr04_contracts.py に加え、 5 acceptance test が壊れることを許容する (Plan 02-07 で全 6 件をまとめて書き換え)。

Purpose: ROADMAP Phase 2 success criterion 1 (end-to-end FunctionNode emit via dispatch driven executor) / criterion 2 (CallGraph sort + pyright TypeDep resolved annotation + DET-03 env pin) / criterion 3 (executor が ContractInfo を FunctionNode に merge) を一括成立。 SC-4 の dispatch dict 走査による isolated 性 (executor logic は dict walk のみ) も成立。

Output:
- `lib_code_parser/models/primitives/type_deps.py` — `resolved` + `source_line` field 追加
- `lib_code_parser/extractors/primitives/type_deps.py` — 新規 1 ファイル
- `lib_code_parser/_dispatch.py` — 5 entry 登録
- `lib_code_parser/executor.py` — dispatch-driven 型に rewrite
- `tests/unit/models/test_type_deps_model.py` — TypeDep additive field unit
- `tests/unit/extractors/test_type_deps_extractor.py` — extractor unit (mock PyrightAdapter + ast walk parity)
- `tests/unit/test_executor_dispatch.py` — executor dispatch-dict walk 単独 unit (Wave 0)
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
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_dispatch.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/executor.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/type_dep_builder.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/type_deps.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/artifact.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/config.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/cav.py

<interfaces>
<!-- Plan 02-01 deliverable: build_cav signature + CAV.raw_content field -->
build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV
CAV(language, path, payload, raw_content)

<!-- Plan 02-02 / 02-03 / 02-04 deliverables: -->
extractors.primitives.functions.extract(cav, config) -> list[FunctionNode]
extractors.primitives.callgraph.extract(cav, config) -> CallGraph
extractors.primitives.contracts.extract(cav, config) -> dict[str, ContractInfo]

<!-- Plan 02-05 deliverable: -->
adapters.pyright.PyrightAdapter.analyze(raw_content: bytes, path: str) -> PyrightOutput
PyrightOutput.diagnostics: list[PyrightDiagnostic]
PyrightDiagnostic: file / severity / message / rule / start_line / end_line

<!-- Phase 1 locked artifact envelope: -->
NormalizedArtifact(artifact_id=ArtifactId(path=...), artifact_type="code", content=CodeContent(...))
CodeContent(functions, call_graph, type_deps, contracts)  # all 4 fields supported via forward refs

<!-- v0.1.0 type_dep_builder.build_type_deps logic (RESEARCH §7.3 parity baseline):
- ast.Import → TypeDep(source=module_name, target=alias.asname or alias.name, kind="imports", source_line=node.lineno)
- ast.ImportFrom → TypeDep(source=module_name, target=f"{from_module}.{alias.name}" or alias.name, kind="imports", source_line=node.lineno)
- ast.FunctionDef/AsyncFunctionDef arg annotations → TypeDep(source=module_name, target=Name.id or Attribute.attr, kind="uses", source_line=arg.lineno)
- ast.FunctionDef.returns → same as args
- Excluded names: "None", "True", "False"
- uppercase-first heuristic for Attribute (`Attribute.attr[0].isupper()`)
-->
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Extend TypeDep model with additive resolved + source_line fields</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/primitives/type_deps.py (Phase 1 model — 3 field, kind: str free-form)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§2.3 algorithm + Open Question 4 — model 拡張は新 field `resolved: bool` を推奨; `kind` の Literal 化は v0.1.0 free-form parity と衝突するので不採用)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/artifact.py (CodeContent.type_deps forward ref — additive field なら破壊しない)
  </read_first>
  <behavior>
    - `TypeDep(source="m", target="os.path")` (2 必須 field のみ) が成功し、 `kind == "uses"` (Phase 1 default 維持) / `resolved == True` / `source_line == 0`
    - `TypeDep(source="m", target="os.path", kind="imports", resolved=False, source_line=5)` が成功
    - `TypeDep(source="m", target="os", extra_field=1)` が `ValidationError` (extra="forbid" 維持)
    - `TypeDep.model_dump_json()` 出力に `"resolved"` と `"source_line"` の 2 key が含まれる
    - Phase 1 既存 unit (`tests/unit/models/test_type_deps.py` — Plan 01-04 で確立) は **そのまま pass** する (additive default field のため後方互換)
  </behavior>
  <action>
    `lib_code_parser/models/primitives/type_deps.py` を以下のとおり最小限編集する:

    既存 module docstring と `model_config` は維持。 `kind: str = "uses"` の直後に 2 行追加:

    ```
    class TypeDep(BaseModel):
        model_config = ConfigDict(extra="forbid")

        source: str
        target: str
        kind: str = "uses"
        # Phase 2 (plan 02-06) additive fields per CONTEXT.md D-07-revised algorithm:
        # - resolved: pyright reportMissingImports diagnostic did NOT fire on the
        #   ast.Import / ast.ImportFrom line → True; fired → False. Default True
        #   for v0.1.0 parity (callers ignoring resolution semantics see same shape).
        # - source_line: 1-based source line of the import statement / annotation
        #   for diagnostic ↔ TypeDep mapping. Default 0 = "unknown / not tracked".
        resolved: bool = True
        source_line: int = 0
    ```

    module docstring の `Traces: SCH-02.` 行に AST-03 と DET-03 を追加: `Traces: SCH-02, AST-03, DET-03.`。

    `tests/unit/models/test_type_deps_model.py` を新規作成 (Phase 1 既存 `test_type_deps.py` は touch しない — Plan 01-04 が確立した unit を破壊しないため)。 上記 `<behavior>` 5 件の test を実装。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/models/test_type_deps.py tests/unit/models/test_type_deps_model.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/models/test_type_deps.py tests/unit/models/test_type_deps_model.py -x -q` exit 0 (Phase 1 既存 unit と新 unit が同時に pass)
    - `python -c "from lib_code_parser.models.primitives.type_deps import TypeDep; t = TypeDep(source='m', target='os'); assert t.resolved is True and t.source_line == 0 and t.kind == 'uses'"` exit 0
    - `grep -c "resolved: bool" lib_code_parser/models/primitives/type_deps.py` = 1
    - `grep -c "source_line: int" lib_code_parser/models/primitives/type_deps.py` = 1
    - `grep -c 'extra="forbid"' lib_code_parser/models/primitives/type_deps.py` = 1
    - `ruff check lib_code_parser/models/primitives/type_deps.py tests/unit/models/test_type_deps_model.py` exit 0
  </acceptance_criteria>
  <done>TypeDep model に additive 2 field 追加。 Phase 1 既存 unit + 新 unit が同時に green。 Phase 1 forward-ref 互換性維持。</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement extractors/primitives/type_deps.py (RESEARCH §2.3 hybrid ast walk + pyright resolved annotation)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/type_dep_builder.py (v0.1.0 reference — Import / ImportFrom / annotation walk の logic を流用、 ただし source_line を新規に記録)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§2.3 algorithm pseudocode + §Code Examples §例 3 type_deps extractor skeleton + §7.3 v0.1.0 parity table)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/adapters/pyright.py (Plan 02-05 deliverable; PyrightAdapter / PyrightOutput / PyrightDiagnostic を import)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/cav.py (Plan 02-01 deliverable; CAV.raw_content field 経由で bytes を取得)
  </read_first>
  <behavior>
    - `from lib_code_parser.extractors.primitives.type_deps import extract` 成功
    - `extract(cav, config)` で:
      - Step 1: cav.payload (`ast.Module`) を walk して raw TypeDeps を構築 (v0.1.0 parity + source_line 記録)
        - `ast.Import` 各 alias → `TypeDep(source=module_name, target=alias.asname or alias.name, kind="imports", source_line=node.lineno)`
        - `ast.ImportFrom` 各 alias → `TypeDep(source=module_name, target=f"{from_module}.{alias.name}" if from_module else alias.name, kind="imports", source_line=node.lineno)`
        - `ast.FunctionDef` / `AsyncFunctionDef` の arg annotation を walk → `TypeDep(source=module_name, target=name_or_attr, kind="uses", source_line=arg.lineno or annotation.lineno)`
        - return type annotation 同上
        - Excluded names: `"None"`, `"True"`, `"False"`
        - uppercase-first heuristic for Attribute
      - Step 2: `PyrightAdapter(python_version=config.python_version).analyze(cav.raw_content, cav.path)` を呼ぶ
      - Step 3: `unresolved_lines = {(d.start_line, d.end_line) for d in pyright_result.diagnostics if d.rule == "reportMissingImports"}` を集合化。 各 TypeDep について source_line が「いずれかの (start, end) 範囲に含まれる」場合 `resolved=False` に annotate (Pyright は 0-based or 1-based?: RESEARCH §2.1 fixture では `"line": 2` → これは 0-based — `start_line` は 0-based 表現。 ast の `lineno` は 1-based。 整合のため diagnostic.start_line を +1 して比較するか、 TypeDep.source_line を 0-based に統一するか — RESEARCH の sketch では大雑把に line == line で比較しているが、 実装上は明示的に 1-based 統一が読みやすい。 本 plan では「diagnostic.start_line に +1 して比較」を採用 = pyright の 0-based を ast の 1-based に揃える)
      - Step 4: `result.sort(key=lambda d: (d.source, d.target, d.kind, d.source_line))` で sort
    - **PyrightAdapter エラー伝搬**: PyrightAdapter が `RuntimeError` を raise すれば本 extractor も同 RuntimeError を上位伝搬 (D-06 fail-loudly 継続)、 silent empty list を返さない
    - `ast.parse` は呼ばない、 `_get_module_name` ローカル定義しない
    - module docstring: `Implements: AST-03, AST-05, DET-03` + `Traces: AST-03, AST-05, DET-03, US-01, US-22`
  </behavior>
  <action>
    `lib_code_parser/extractors/primitives/type_deps.py` を新規作成。

    Module docstring (RESEARCH §6.3 template):
    ```
    """Python type dependency extractor (CAV + pyright adapter).

    Combines a stdlib ast walk over cav.payload (RESEARCH §7.3 v0.1.0 parity for
    import / annotation extraction) with PyrightAdapter (Plan 02-05) to annotate
    each TypeDep with resolved=True when pyright did NOT fire a
    reportMissingImports diagnostic on the source line, and resolved=False when
    it did. This is the CONTEXT.md D-07-revised algorithm — pyright's
    --outputjson cannot provide resolved type info (RESEARCH §2.1 empirical),
    so pyright is used as a diagnostic-driven resolution oracle.

    PyrightAdapter is invoked with cav.raw_content (carried by the Python
    Frontend via Plan 02-01). This avoids the ast.unparse round-trip that would
    drift line numbers and break the diagnostic ↔ TypeDep mapping (Assumption A1).

    D-06 fail-loudly: PyrightAdapter RuntimeError propagates; silent empty list
    is never returned.

    Implements: AST-03, AST-05, DET-03
    Traces: AST-03, AST-05, DET-03, US-01, US-22
    """
    ```

    Imports:
    ```
    from __future__ import annotations

    import ast

    from lib_code_parser._paths import get_module_name
    from lib_code_parser.adapters.pyright import PyrightAdapter
    from lib_code_parser.models.infrastructure.cav import CAV
    from lib_code_parser.models.infrastructure.config import ParserConfig
    from lib_code_parser.models.primitives.type_deps import TypeDep

    __all__ = ["extract"]
    ```

    Helpers — v0.1.0 type_dep_builder.py の logic を verbatim 流用 (source_line を新規記録):

    ```
    _EXCLUDED_NAMES: frozenset[str] = frozenset({"None", "True", "False"})


    def _collect_annotation_deps(
        annotation: ast.expr,
        module_name: str,
        source_line: int,
        deps: list[TypeDep],
    ) -> None:
        """Walk annotation tree and record TypeDep entries with source_line."""
        for sub in ast.walk(annotation):
            if isinstance(sub, ast.Name):
                name = sub.id
                if name and name not in _EXCLUDED_NAMES:
                    deps.append(
                        TypeDep(
                            source=module_name,
                            target=name,
                            kind="uses",
                            source_line=source_line,
                        )
                    )
            elif isinstance(sub, ast.Attribute):
                # Uppercase-first heuristic for class-like types (v0.1.0 parity)
                if sub.attr and sub.attr[0].isupper():
                    deps.append(
                        TypeDep(
                            source=module_name,
                            target=sub.attr,
                            kind="uses",
                            source_line=source_line,
                        )
                    )
    ```

    Main extractor:
    ```
    def extract(cav: CAV, config: ParserConfig) -> list[TypeDep]:
        """AST-03 / AST-05 / DET-03 / DET-04: emit type_deps list from cav.

        Algorithm (RESEARCH §2.3 hybrid):
            1. stdlib ast walk → raw TypeDeps (v0.1.0 parity + source_line tracking)
            2. PyrightAdapter.analyze(cav.raw_content, cav.path) → diagnostics
            3. annotate resolved=False for source_line in reportMissingImports range
            4. sort by (source, target, kind, source_line) — DET-04
        """
        tree = cav.payload  # type: ignore[assignment]
        assert isinstance(tree, ast.Module), (
            f"type_deps extractor requires Python CAV (ast.Module payload), "
            f"got {type(tree).__name__}"
        )
        module_name = get_module_name(cav.path)
        raw_deps: list[TypeDep] = []

        # Step 1: ast walk for imports + annotations (v0.1.0 parity + source_line)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    raw_deps.append(
                        TypeDep(
                            source=module_name,
                            target=alias.asname if alias.asname else alias.name,
                            kind="imports",
                            source_line=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                from_module = node.module or ""
                for alias in node.names:
                    target = (
                        f"{from_module}.{alias.name}" if from_module else alias.name
                    )
                    raw_deps.append(
                        TypeDep(
                            source=module_name,
                            target=target,
                            kind="imports",
                            source_line=node.lineno,
                        )
                    )

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in node.args.args:
                    if arg.annotation:
                        _collect_annotation_deps(
                            arg.annotation,
                            module_name,
                            arg.lineno,
                            raw_deps,
                        )
                if node.returns:
                    _collect_annotation_deps(
                        node.returns,
                        module_name,
                        node.returns.lineno,
                        raw_deps,
                    )

        # Step 2: pyright diagnostics — fail-loudly per D-06 (RuntimeError propagates)
        adapter = PyrightAdapter(python_version=config.python_version)
        pyright_result = adapter.analyze(cav.raw_content, cav.path)

        # Step 3: annotate resolved flag
        # pyright range.start.line is 0-based; ast.lineno is 1-based. Normalize
        # to 1-based for comparison.
        unresolved_ranges: list[tuple[int, int]] = [
            (d.start_line + 1, d.end_line + 1)
            for d in pyright_result.diagnostics
            if d.rule == "reportMissingImports"
        ]

        annotated: list[TypeDep] = []
        for dep in raw_deps:
            is_resolved = True
            for start_one_based, end_one_based in unresolved_ranges:
                if start_one_based <= dep.source_line <= end_one_based:
                    is_resolved = False
                    break
            annotated.append(dep.model_copy(update={"resolved": is_resolved}))

        # Step 4: DET-04 sort by (source, target, kind, source_line)
        annotated.sort(key=lambda d: (d.source, d.target, d.kind, d.source_line))
        return annotated
    ```

    Wave 0 unit test `tests/unit/extractors/test_type_deps_extractor.py` を新規作成。 unit は **PyrightAdapter を mock** して fixed PyrightOutput を返させる pattern を採用 (実 pyright 起動依存を避ける、 Plan 02-05 test_pyright_adapter.py との責務分離):

    Tests:
    1. `test_extract_emits_import_typedep_with_source_line` — `import os\n` の input で TypeDep(source="m", target="os", kind="imports", source_line=1) が出る (PyrightAdapter mock = 空 diagnostics → resolved=True)
    2. `test_extract_emits_importfrom_with_dotted_target` — `from os.path import join` で TypeDep(target="os.path.join", kind="imports", source_line=1)
    3. `test_extract_annotation_uses_uppercase_attribute_heuristic` — `def f() -> models.OrderModel: ...` で TypeDep(target="OrderModel", kind="uses")
    4. `test_extract_excludes_none_true_false_names` — annotation 内の `None` / `True` / `False` は TypeDep 化しない
    5. `test_extract_marks_unresolved_when_pyright_diagnostic_fires` — PyrightAdapter mock を `PyrightOutput(version="1.1.409", diagnostics=[PyrightDiagnostic(file="x", severity="error", message="", rule="reportMissingImports", start_line=0, end_line=0)])` で構築 (start_line=0 + end_line=0、 1-based 化で 1..1 範囲); source: `import nonexistent_pkg\n` (source_line=1) で resolved=False に annotate される
    6. `test_extract_keeps_resolved_when_diagnostic_is_different_rule` — `rule="reportMissingTypeArgument"` のような他 rule diagnostic は resolved=False に影響しない
    7. `test_extract_emits_sorted_by_source_target_kind_source_line` — 複数 imports + annotation で出力が `(source, target, kind, source_line)` 順
    8. `test_extract_pyright_runtime_error_propagates` — PyrightAdapter.analyze が `RuntimeError("pyright timed out")` を raise する mock; `extract(cav, config)` も同 RuntimeError を上位伝搬 (D-06 fail-loudly 継続)
    9. `test_extract_isolated_import_no_executor` — `CodeParserExecutor` を import せず `extract(cav, config)` 直接呼び出し (SC-4)

    Mock PyrightAdapter は `monkeypatch.setattr("lib_code_parser.extractors.primitives.type_deps.PyrightAdapter", lambda **kw: _MockPyright(...))` pattern で差し替え。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/extractors/test_type_deps_extractor.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/extractors/test_type_deps_extractor.py -x -q` exit 0 with 9 件 pass
    - `grep -c "ast\.parse" lib_code_parser/extractors/primitives/type_deps.py` が 0
    - `grep -c "^def _get_module_name\|^def get_module_name" lib_code_parser/extractors/primitives/type_deps.py` が 0
    - `grep -c "PyrightAdapter" lib_code_parser/extractors/primitives/type_deps.py` >= 2 (import + use)
    - `grep -c "reportMissingImports" lib_code_parser/extractors/primitives/type_deps.py` >= 1 (RESEARCH §2.3 hybrid algorithm grep 証跡)
    - `grep -c "result.sort\|annotated.sort" lib_code_parser/extractors/primitives/type_deps.py` >= 1 (DET-04 sort)
    - `grep -c "Implements: AST-03" lib_code_parser/extractors/primitives/type_deps.py` = 1
    - `grep -c "Traces: AST-03" lib_code_parser/extractors/primitives/type_deps.py` >= 1
    - Plan 02-01 AST-05 parity 維持: `pytest tests/parity/test_ast_05_one_parse.py -x -q` exit 0
    - `ruff check lib_code_parser/extractors/primitives/type_deps.py tests/unit/extractors/test_type_deps_extractor.py` exit 0
  </acceptance_criteria>
  <done>type_deps extractor が RESEARCH §2.3 hybrid algorithm で実装。 v0.1.0 ast walk parity + pyright resolved annotation + DET-04 sort + D-06 fail-loudly 伝搬。 unit 9 件で全 path がロック。</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Populate _dispatch.py registries + rewrite executor.py as dispatch-driven</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_dispatch.py (Phase 1 locked 空 dict 3 件)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/executor.py (v0.1.0 logic; Phase 1 で保持された orchestration body — Plan 02-06 が dispatch-driven 型に rewrite)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md (D-03 executor rewrite + D-12 dispatch dict 走査型)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/docs/09-extending.md (Open-Closed 6 不変条件、 特に #4 append-only + #6 executor は dict 走査のみ)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/config.py (typed ParserConfig — executor が今後 import するもの)
  </read_first>
  <behavior>
    - `_dispatch.FRONTENDS == {"python": build_cav}` — Plan 02-01 deliverable 1 件 register
    - `_dispatch.PRIMITIVES` の挿入順が `{"functions": fn, "call_graph": fn, "type_deps": fn, "contracts": fn}` の 4 件 (D-12 append-only、 Python 3.7+ dict は挿入順保持)
    - `_dispatch.EVALUATIONS == {}` (Phase 3 で populate)
    - `lib_code_parser.executor.CodeParserExecutor().execute(typed_config, raw_bytes, path)` が dispatch dict walk で動作:
      - `config.enabled == False` → 空 CodeContent を NormalizedArtifact に包んで返す (v0.1.0 parity)
      - file extension `.cpp / .c / .h / .cc` → 空 CodeContent (Phase 4 で本実装、 現状 v0.1.0 parity)
      - `config.language not in FRONTENDS` → `KeyError` を raise (fail-loudly)
      - `frontend = FRONTENDS[config.language]; cav = frontend(raw_bytes, path, config)`
      - `for primitive_name, primitive_fn in PRIMITIVES.items():` walk
        - `"functions"` → `functions = primitive_fn(cav, config)`
        - `"call_graph"` → `call_graph = primitive_fn(cav, config)`
        - `"type_deps"` → `type_deps = primitive_fn(cav, config)`
        - `"contracts"` → `config.extract_contracts == True` 時のみ `contracts_dict = primitive_fn(cav, config)`; False 時は `contracts_dict = {}` で skip
      - **ContractInfo merger**: `for fn in functions: if fn.node_id in contracts_dict: fn.contracts = contracts_dict[fn.node_id]` (v0.1.0 parity)
      - 返却: `NormalizedArtifact(artifact_id=ArtifactId(path=path), artifact_type="code", content=CodeContent(functions=functions, call_graph=call_graph, type_deps=type_deps, contracts=contracts_dict))`
    - executor 内部で `from lib_code_parser.models.infrastructure.config import ParserConfig` を import (typed graduation の executor 部分)
    - executor 内部に `if/elif` の primitive-specific 分岐は **一切ない** (D-03 / Open-Closed invariant #6)、 ただし `config.extract_contracts` gate と `language == "cpp"` 早期 return のみ allow される (これらは primitive 名でなく config field レベルの分岐)
  </behavior>
  <action>
    Step 1 — `lib_code_parser/_dispatch.py` を以下のとおり編集。 module docstring と type alias は維持、 末尾の 3 空 dict 宣言の **後** に登録 import + 代入を追加 (append-only inheritance):

    ```
    # existing top (Phase 1 locked):
    from __future__ import annotations
    from typing import TYPE_CHECKING, Callable

    if TYPE_CHECKING:
        from lib_code_parser.models.infrastructure.cav import CAV
        from lib_code_parser.models.infrastructure.config import ParserConfig

    FrontendFn = Callable[[bytes, str, "ParserConfig"], "CAV"]
    PrimitiveFn = Callable[["CAV", "ParserConfig"], object]
    EvaluationFn = Callable[["CAV", "ParserConfig"], object]

    FRONTENDS: dict[str, FrontendFn] = {}
    PRIMITIVES: dict[str, PrimitiveFn] = {}
    EVALUATIONS: dict[str, EvaluationFn] = {}

    # Phase 2 (plan 02-06) registrations — append-only per Open-Closed invariant #4
    # ============================================================================
    # NOTE: these imports are at module bottom (not top) intentionally — register
    # AFTER the empty dict declarations to make the append-only contract explicit.
    # Phase 3 will append diagram + spec entries to EVALUATIONS similarly.
    from lib_code_parser.extractors.primitives.callgraph import extract as _extract_callgraph
    from lib_code_parser.extractors.primitives.contracts import extract as _extract_contracts
    from lib_code_parser.extractors.primitives.functions import extract as _extract_functions
    from lib_code_parser.extractors.primitives.type_deps import extract as _extract_type_deps
    from lib_code_parser.frontends.python import build_cav as _build_cav_python

    FRONTENDS["python"] = _build_cav_python
    PRIMITIVES["functions"] = _extract_functions
    PRIMITIVES["call_graph"] = _extract_callgraph
    PRIMITIVES["type_deps"] = _extract_type_deps
    PRIMITIVES["contracts"] = _extract_contracts

    __all__ = [
        "FrontendFn", "PrimitiveFn", "EvaluationFn",
        "FRONTENDS", "PRIMITIVES", "EVALUATIONS",
    ]
    ```

    Step 2 — `lib_code_parser/executor.py` を **全面 rewrite** (D-03)。 v0.1.0 body を保持しない、 dispatch dict 駆動の薄い orchestrator に書き換え:

    ```
    """CodeParserExecutor — dispatch-dict-driven orchestrator (Phase 2 D-03 rewrite).

    Phase 2 Plan 02-06 replaces the v0.1.0 if/elif body with a walk over
    _dispatch.FRONTENDS / PRIMITIVES. Adding a new primitive becomes a single
    line in _dispatch.py (Open-Closed invariant #4 + #6) — executor body never
    changes. Frontend selection is config.language → FRONTENDS[language].
    Contract merger (ContractInfo into FunctionNode.contracts) is the only
    cross-primitive coordination logic; it mirrors v0.1.0 executor.py L72-76.

    Traces: ARC-01, ARC-02, D-03, D-12.
    """

    from __future__ import annotations

    import pathlib

    from lib_code_parser._dispatch import FRONTENDS, PRIMITIVES
    from lib_code_parser.models.infrastructure.artifact import (
        ArtifactId,
        CodeContent,
        NormalizedArtifact,
    )
    from lib_code_parser.models.infrastructure.config import ParserConfig
    from lib_code_parser.models.primitives.callgraph import CallGraph
    from lib_code_parser.models.primitives.contracts import ContractInfo
    from lib_code_parser.models.primitives.functions import FunctionNode
    from lib_code_parser.models.primitives.type_deps import TypeDep

    _CPP_EXTENSIONS = frozenset({".cpp", ".c", ".h", ".cc"})


    class CodeParserExecutor:
        """Execute the dispatch-dict pipeline for a single source file."""

        def execute(
            self,
            config: ParserConfig,
            raw_content: bytes,
            path: str,
        ) -> NormalizedArtifact[CodeContent]:
            """Parse raw_content (bytes) from path using config.

            D-03 dispatch-driven flow:
                Frontend (FRONTENDS[language]) → CAV
                  ↓
                for each primitive in PRIMITIVES → primitive(cav, config) → CodeContent slot
                  ↓
                ContractInfo merger → FunctionNode.contracts
                  ↓
                NormalizedArtifact[CodeContent]

            Disabled / C++ extension early returns preserve v0.1.0 parity.
            """
            if not config.enabled:
                return NormalizedArtifact[CodeContent](
                    artifact_id=ArtifactId(path=path),
                    artifact_type="code",
                    content=CodeContent(),
                )

            language = config.language
            suffix = pathlib.Path(path).suffix.lower()
            if suffix in _CPP_EXTENSIONS:
                language = "cpp"

            if language not in FRONTENDS:
                # Phase 4 will register "cpp"; until then, empty content (v0.1.0 parity)
                return NormalizedArtifact[CodeContent](
                    artifact_id=ArtifactId(path=path),
                    artifact_type="code",
                    content=CodeContent(),
                )

            frontend = FRONTENDS[language]
            cav = frontend(raw_content, path, config)

            functions: list[FunctionNode] = []
            call_graph: CallGraph = CallGraph()
            type_deps: list[TypeDep] = []
            contracts_dict: dict[str, ContractInfo] = {}

            for name, primitive_fn in PRIMITIVES.items():
                if name == "contracts" and not config.extract_contracts:
                    continue
                result = primitive_fn(cav, config)
                if name == "functions":
                    functions = result  # type: ignore[assignment]
                elif name == "call_graph":
                    call_graph = result  # type: ignore[assignment]
                elif name == "type_deps":
                    type_deps = result  # type: ignore[assignment]
                elif name == "contracts":
                    contracts_dict = result  # type: ignore[assignment]

            # ContractInfo merger (v0.1.0 parity): assign per-class ContractInfo to
            # the matching FunctionNode.contracts where node_id aligns.
            for fn in functions:
                if fn.node_id in contracts_dict:
                    fn.contracts = contracts_dict[fn.node_id]

            return NormalizedArtifact[CodeContent](
                artifact_id=ArtifactId(path=path),
                artifact_type="code",
                content=CodeContent(
                    functions=functions,
                    call_graph=call_graph,
                    type_deps=type_deps,
                    contracts=contracts_dict,
                ),
            )
    ```

    内部の `if name == "..."` の 4 件分岐は logic 上必要 (各 primitive の output 型が異なり、 異なる CodeContent slot に格納するため) だが、 これは Open-Closed invariant #6 の解釈境界線上にある。 rationale: `name` 比較は "primitive 名 -> CodeContent slot" の dispatch 続編であり、 これ自体が PRIMITIVES の意味づけを decode しているだけ。 新 primitive 追加時に this 分岐を増やす必要があるが、 これは「executor が新 extractor の output を CodeContent のどの slot に置くか」を decode する責任を持つ限界点。 完全 dispatch 化するには CodeContent を `dict[str, object]` 化する必要があり、 これは SCH-02 typed contract と衝突する。 RESEARCH §Architectural Responsibility Map で本 plan の責務範囲内 (executor.py: dispatch 走査 + ContractInfo merger 部分)。 docs/09-extending.md に rationale を追記する余地は Plan 02-07 closer で。

    Step 3 — Wave 0 unit test `tests/unit/test_executor_dispatch.py` を新規作成。 dispatch walk が正しく動作することを mock 単位で証明。 Tests:

    1. `test_dispatch_walks_all_4_primitives` — _dispatch.PRIMITIVES の 4 entry を mock 化、 executor.execute() がそれぞれを 1 回ずつ call することを assert
    2. `test_dispatch_skips_contracts_when_extract_contracts_false` — config.extract_contracts=False で contracts primitive が call されないことを assert
    3. `test_dispatch_enabled_false_returns_empty_content` — config.enabled=False で空 CodeContent (v0.1.0 parity)
    4. `test_dispatch_cpp_extension_returns_empty_content` — `path="x.cpp"` で空 CodeContent (Phase 4 待ち)
    5. `test_dispatch_frontend_python_called` — config.language="python" で FRONTENDS["python"] が build_cav として call される
    6. `test_dispatch_contract_merger_assigns_to_functionnode` — mock contracts_dict が `{"m.Foo": ContractInfo(...)}` を返し、 functions の `FunctionNode(node_id="m.Foo", ...)` の `.contracts` が更新される

    各 test は `monkeypatch.setitem(PRIMITIVES, "functions", mock_fn)` 等で dispatch 内容を差し替える。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/test_executor_dispatch.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/test_executor_dispatch.py -x -q` exit 0 with 6 件 pass
    - `python -c "from lib_code_parser._dispatch import FRONTENDS, PRIMITIVES; assert 'python' in FRONTENDS; assert sorted(PRIMITIVES.keys()) == ['call_graph','contracts','functions','type_deps']"` exit 0
    - `python -c "from lib_code_parser._dispatch import PRIMITIVES; assert list(PRIMITIVES.keys()) == ['functions','call_graph','type_deps','contracts']"` exit 0 (挿入順保持の検証)
    - `grep -c 'FRONTENDS\["python"\]' lib_code_parser/_dispatch.py` = 1
    - `grep -c 'PRIMITIVES\["functions"\]\|PRIMITIVES\["call_graph"\]\|PRIMITIVES\["type_deps"\]\|PRIMITIVES\["contracts"\]' lib_code_parser/_dispatch.py` = 4
    - `grep -c "FRONTENDS\[" lib_code_parser/executor.py` >= 1 (D-03 dispatch use 証跡)
    - `grep -c "PRIMITIVES.items\|PRIMITIVES\[" lib_code_parser/executor.py` >= 1
    - `grep -c "from lib_code_parser\.models\.infrastructure\.config import ParserConfig" lib_code_parser/executor.py` = 1 (typed graduation の executor 部分)
    - `grep -c "config.params" lib_code_parser/executor.py` = 0 (v0.1.0 stub use が消えていること)
    - `grep -c "from lib_code_parser.ast_extractor\|from lib_code_parser.callgraph_builder\|from lib_code_parser.type_dep_builder\|from lib_code_parser.contract_extractor" lib_code_parser/executor.py` = 0 (v0.1.0 import が消えていること)
    - Plan 02-01 AST-05 parity: `pytest tests/parity/test_ast_05_one_parse.py -x -q` exit 0
    - Phase 1 baseline parity の状況確認: Plan 02-04 + 02-06 の breaking 連鎖により、 既存 6 acceptance tests (test_fr01..06) は **全部失敗する** 想定 (typed ParserConfig 切替で旧 v0.1.0 stub API が壊れる + ContractInfo 構造変更で test_fr04 が壊れる + test_fr01..03/05 は v0.1.0 `from lib_code_parser.{ast_extractor,callgraph_builder,...} import ...` の import path を使っていて Plan 02-06 が executor を切り替えただけでは壊れないが、 Plan 02-07 で legacy 4 ファイル削除時に壊れる)。 本 plan の acceptance では `pytest tests/parity/test_v01_v02_compat.py tests/parity/test_ast_05_one_parse.py -x -q` exit 0 だけを必須 (acceptance test suite の状態は Plan 02-07 で正常化)。
    - `ruff check lib_code_parser/_dispatch.py lib_code_parser/executor.py tests/unit/test_executor_dispatch.py` exit 0
  </acceptance_criteria>
  <done>_dispatch.py に 5 entry append-only 登録。 executor.py が dispatch-driven 型に rewrite され typed ParserConfig 経由で動作。 dispatch walk の 6 件 unit が green。 AST-05 parity test 維持。</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| _dispatch.PRIMITIVES → executor.execute | append-only 登録順保持の Open-Closed invariant #4。 Python 3.7+ dict の挿入順保持を前提に決定論性が成立 |
| PyrightAdapter.analyze RuntimeError → type_deps extractor → executor | D-06 fail-loudly 連鎖。 silent empty は禁止 |
| ContractInfo merger (functions × contracts_dict) | v0.1.0 parity 維持。 FunctionNode.contracts 更新が in-place で行われる (Pydantic v2 mutability は default; FunctionNode の model_config は frozen=False) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-29 | Tampering | _dispatch.py の挿入順がランダム化される (Python < 3.7 想定) | accept | pyproject.toml で `requires-python = ">=3.11"` declared 済 — dict 挿入順保持は OS 仕様 |
| T-02-30 | Tampering | executor.py rewrite が ContractInfo merger を取り除く (v0.1.0 parity 違反) | mitigate | Task 3 acceptance に `test_dispatch_contract_merger_assigns_to_functionnode` を含む |
| T-02-31 | Tampering | PyrightAdapter エラーが silent empty に degrade | mitigate | Task 2 `test_extract_pyright_runtime_error_propagates` で実証 |
| T-02-32 | Tampering | _dispatch.py に Phase 3 / 4 で追加されるべき "cpp" frontend / 評価単位を本 plan で前倒し登録 | accept | Task 3 acceptance grep gate で PRIMITIVES key 集合 == 4 件 (functions/call_graph/type_deps/contracts) を assert; "cpp" / 評価単位 entries が無いことを保証 |
| T-02-33 | DoS | pyright timeout / startup 失敗で executor が hang | mitigate | run_subprocess timeout=60.0 (Phase 1 既定) + D-06 RuntimeError propagation で 60s 上限で fail-loudly |
| T-02-34 | Tampering | barrel-level lib_code_parser.ParserConfig が依然 v0.1.0 stub のため executor の dispatch が壊れる | mitigate | executor は **typed** ParserConfig を import (本 plan で graduation)、 barrel-level の v0.1.0 stub は Plan 02-07 で graduation。 Plan 02-07 までは barrel から ParserConfig を呼んだ caller が `ValidationError` を喰らうが、 executor 自身は typed 経路で動作する |
| T-02-35 | Supply chain | 新規 install なし | accept | stdlib + Phase 1 declared 依存のみ |
</threat_model>

<verification>
- `pytest tests/unit/models/test_type_deps_model.py tests/unit/extractors/test_type_deps_extractor.py tests/unit/test_executor_dispatch.py -x -q` 21 件 pass
- `_dispatch.py` 登録の grep gate: FRONTENDS["python"] / PRIMITIVES 4 entry すべて
- executor.py が typed ParserConfig 経由になっていることの grep 証跡
- AST-05 parity / TRC-02 / TRC-03 grep gate 全 pass
- Plan 02-01 frontend-python の AST-05 dynamic monkeypatch test が **executor を介して** call_count == 1 で動作することを別 unit (本 plan の test_executor_dispatch.py で 1 件追加可能) で確認 — RESEARCH §5.2 backup gate のフル invocation
- フル baseline (acceptance test 6 件は意図的に壊れる、 parity test は維持): `pytest tests/parity/ tests/unit/ -x -q` exit 0
- `ruff check lib_code_parser/ tests/unit/` exit 0
</verification>

<success_criteria>
- ROADMAP Phase 2 success criterion 1 完全成立 (single ast.parse via Frontend + FunctionNode emit via dispatch)
- ROADMAP Phase 2 success criterion 2 完全成立 (CallGraph DET-04 sort + pyright TypeDep resolved annotation + DET-03 env pin)
- ROADMAP Phase 2 success criterion 3 完全成立 (executor が ContractInfo を FunctionNode に merge した結果として source_kind per-entry discriminator が verifier に届く)
- ROADMAP Phase 2 success criterion 4 部分成立 (4 extractor が isolated 呼び出し可能 — Plan 02-02..04 + 02-06 のすべて)
- D-03 dispatch-driven executor 実装
- D-12 append-only invariant が `_dispatch.py` に成立
- typed ParserConfig が executor.py 内部で graduation
</success_criteria>

<output>
Create `.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-06-SUMMARY.md` when done. Include:
1. pytest output (Plan 02-06 contribution: 21 件 unit pass; acceptance suite は意図的失敗 6 件、 parity は維持)
2. `_dispatch.py` 登録ダンプ (`python -c "from lib_code_parser._dispatch import FRONTENDS, PRIMITIVES; print(list(FRONTENDS.keys())); print(list(PRIMITIVES.keys()))"`)
3. executor.py rewrite diff highlight (v0.1.0 logic 削除 / dispatch walk 導入 / typed ParserConfig 切替)
4. AST-05 / DET-04 / DET-03 / D-03 / D-12 の grep 証跡
5. Plan 02-07 で書き換える acceptance test の list (Plan 02-07 への引き継ぎメモ)
</output>
