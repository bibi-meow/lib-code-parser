---
phase: 02-python-frontend-ast-primitives-acl-2-adapters
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - lib_code_parser/models/infrastructure/cav.py
  - lib_code_parser/frontends/__init__.py
  - lib_code_parser/frontends/python.py
  - tests/unit/models/test_cav_raw_content.py
  - tests/unit/frontends/__init__.py
  - tests/unit/frontends/test_python_frontend.py
  - tests/parity/test_ast_05_one_parse.py
autonomous: true
requirements: [AST-05, ARC-02, TRC-02]
must_haves:
  truths:
    - "Caller (or another extractor) can call build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV exactly once per file and gets a CAV whose payload is the result of a single ast.parse() invocation"
    - "CAV exposes raw_content: bytes as an additive (default-empty) field that the Python Frontend populates; existing v0.1.0/Phase-1 callers constructing CAV(language=..., path=..., payload=...) continue to work because raw_content has a default value of b\"\""
    - "lib_code_parser/extractors/ contains zero occurrences of `ast.parse(` or `from ast import parse` (Primary AST-05 grep gate)"
    - "When an executor is wired in Wave 2, instrumenting `ast.parse` via monkeypatch shows exactly one call per execute() (Backup AST-05 dynamic gate — test is committed in this plan but only asserts the grep gate until Wave 2's executor exists; the dynamic-monkeypatch test imports the Frontend directly and asserts call_count == 1 on a build_cav() invocation)"
    - "frontends/python.py module docstring contains both `Implements: AST-05` and `Traces: AST-05, ARC-02` lines (TRC-02 + TRC-03 carrier)"
  artifacts:
    - path: "lib_code_parser/frontends/python.py"
      provides: "Python Frontend — single ast.parse() per file, emits CAV envelope"
      contains: "def build_cav"
    - path: "lib_code_parser/models/infrastructure/cav.py"
      provides: "CAV model extended with raw_content: bytes additive field for Phase 2 type_deps adapter pipeline"
      contains: "raw_content"
    - path: "tests/parity/test_ast_05_one_parse.py"
      provides: "AST-05 grep static gate + monkeypatch dynamic gate (RESEARCH §5.2 primary + backup)"
      contains: "def test_no_ast_parse_in_extractors|def test_single_parse_per_build_cav"
    - path: "tests/unit/frontends/test_python_frontend.py"
      provides: "Python Frontend behavior: single parse / CAV.payload is ast.Module / decode errors handled / raw_content carried"
      contains: "def test_build_cav"
  key_links:
    - from: "lib_code_parser/frontends/python.py::build_cav"
      to: "ast.parse"
      via: "single direct call"
      pattern: "ast\\.parse\\("
    - from: "lib_code_parser/frontends/python.py::build_cav"
      to: "lib_code_parser.models.infrastructure.cav.CAV"
      via: "CAV constructor with raw_content carry"
      pattern: "CAV\\(language=\"python\""
---

<objective>
Wave 1 並列の 1 件目。 Python Frontend を実装し、 Phase 2 で導入する 4 つの pure-CAV primitive extractor が **1 ファイル 1 回の `ast.parse()`** に従う前提を物理的に成立させる (AST-05 success criterion 1 の半分)。 同時に、 Phase 2 Wave 2 の type_deps extractor が PyrightAdapter に raw bytes を渡せるよう、 CAV モデルに **additive** な `raw_content: bytes` field を加える (RESEARCH.md §A1 推奨。 Phase 1 D-04/D-05 の CAV lock は破らない: 既存呼び出し側は default `b""` で吸収される)。 AST-05 の static gate (grep) と dynamic gate (monkeypatch) を組として `tests/parity/test_ast_05_one_parse.py` に置き、 Wave 1/2/3 の以降の plan が CAV を呼ばずに `ast.parse()` を行うことを永続的にブロックする。

Purpose: Phase 2 の中心契約 (AST-05 = 1 parse per execute) を「実装可能な単一の関数」に閉じる。 Frontend が CAV 生産者であり、 extractor は CAV consumer に限定される構造を、 grep gate で物理的に enforce する (RESEARCH.md §5.2 の primary defence)。

Output:
- `lib_code_parser/models/infrastructure/cav.py` — 既存 CAV モデルに `raw_content: bytes = b""` field を追加 (additive、 既存 frozen + extra="forbid" + arbitrary_types_allowed=True を維持)
- `lib_code_parser/frontends/__init__.py` — Phase 1 placeholder を更新し `build_cav` を re-export
- `lib_code_parser/frontends/python.py` — 新規 1 関数 `build_cav(raw_content, path, config) -> CAV`
- `tests/unit/models/test_cav_raw_content.py` — CAV.raw_content additive 性の Wave 0 unit
- `tests/unit/frontends/__init__.py` + `tests/unit/frontends/test_python_frontend.py` — Frontend 行動の Wave 0 unit
- `tests/parity/test_ast_05_one_parse.py` — AST-05 static grep + dynamic monkeypatch parity (Wave 0)
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
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-VALIDATION.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/codebase/CONVENTIONS.md
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/cav.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/frontends/__init__.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_dispatch.py
@C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/config.py

<interfaces>
<!-- Phase 1 locked CAV model (post-Plan 01-03): frozen + extra="forbid" + arbitrary_types_allowed.
     Phase 2 plan 02-01 extends with an ADDITIVE raw_content field (default b""), which
     preserves D-04 (single CAV) / D-05 (immutable, extra="forbid", arbitrary_types_allowed)
     because frozen=True is preserved and default value keeps existing callers backward-
     compatible. Per CONTEXT.md D-07-revised, this sub-contract choice is planner autonomy. -->

class CAV(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True, frozen=True)
    language: Literal["python", "cpp"]
    path: str
    payload: object
    # ADDED in Phase 2 plan 02-01:
    raw_content: bytes = b""    # additive — default keeps Phase 1 callers green

<!-- Phase 1 locked _dispatch.FrontendFn signature: (raw_content, path, config) -> CAV.
     Plan 02-01's build_cav matches this signature exactly. Registration into
     _dispatch.FRONTENDS["python"] is deferred to Plan 02-06 (Wave 2 closer) to
     avoid Wave 1 file-ownership conflict on _dispatch.py. -->

FrontendFn = Callable[[bytes, str, "ParserConfig"], "CAV"]

<!-- Phase 1 typed ParserConfig (models.infrastructure.config.ParserConfig):
     ConfigDict(extra="forbid")
     fields: artifact_type, executor_lib, enabled, language Literal["python","cpp"],
             extract_contracts, compile_args, python_version. -->
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Extend CAV model with additive raw_content field</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/cav.py (current Phase 1 locked CAV — must keep frozen / extra="forbid" / arbitrary_types_allowed / Literal language / payload: object)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§A1 Assumptions Log — `ast.unparse(cav.payload)` で line number 乖離リスク → CAV に raw_content carry が「more safe design」と明示。 §2.3 algorithm sketch も raw_content を前提とした実装を提示)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-CONTEXT.md (D-07-revised: sub-contract decision = planner 判断、 raw_content carry は推奨選択肢)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/01-architecture-foundation-spec-correction/01-CONTEXT.md (D-04/D-05: CAV は frozen + extra="forbid" + arbitrary_types_allowed=True、 language Literal、 payload opaque — 本タスクの追加 field はこの 5 不変条件を破らない)
  </read_first>
  <behavior>
    - `CAV(language="python", path="x.py", payload=ast.parse(""))` (3-field、 raw_content 省略) が Phase 1 と同じく ValidationError なしで構築できる (additive field default が後方互換性を保つ)
    - `CAV(language="python", path="x.py", payload=ast.parse(""), raw_content=b"def f(): pass")` が成功し、 `.raw_content` で同じ bytes を取り出せる
    - `CAV(language="python", path="x.py", payload=ast.parse(""), raw_content="not bytes")` は `ValidationError` を投げる (Pydantic は bytes field に str を強制変換しない設定下で fail loudly — `extra="forbid"` は別軸だが型バリデーションは継続)
    - 既存 Phase 1 unit `tests/unit/models/test_cav.py` (Plan 01-03 Task 2 で確立、 frozen 性 + Literal 性 + arbitrary_types_allowed assertion) が **そのまま pass** する (raw_content の追加は破壊しない)
    - CAV docstring の `Traces: ARC-02, SCH-02` 行は維持 (TRC-03 regex 引っかかり継続)、 docstring 本体に「Phase 2 で raw_content additive field を追加。 frontend が pyright adapter のための bytes を carry する目的」を 1-2 行追記
  </behavior>
  <action>
    `lib_code_parser/models/infrastructure/cav.py` を以下のとおり最小限編集する。 既存の `language` / `path` / `payload` 3 field と `model_config` は **1 文字も変更しない**:

    - `payload: object` の直下に新規行 `raw_content: bytes = b""` を追加する。 default 値 `b""` を付けることで Phase 1 既存 caller の 3-field 構築を吸収する。 ARC-04 / DET-04 sort 整合は本 field では発生しない (CAV は 1 file 1 envelope なので)。
    - module docstring 末尾の `Traces: ARC-02, SCH-02.` 行は維持。 ただし冒頭 docstring 本体に次の文を 1 paragraph 加える: "Phase 2 (plan 02-01) adds an additive ``raw_content: bytes`` field so the type_deps extractor's pyright adapter can write the original bytes to its internal tmpdir without re-serializing via ``ast.unparse`` (which would drift line numbers and break pyright diagnostic ↔ TypeDep mapping). The default ``b\"\"`` keeps Phase 1 callers backward-compatible — the field is additive, not breaking."
    - CAV class 本体に明示 docstring を 1 行追加: `"""Common AST View envelope. See module docstring for the Phase 2 raw_content rationale."""` (既存 class docstring を維持しつつ、 短文を追加。 既に class docstring がある場合は末尾に paragraph を追加するだけで可)。

    その後、 Wave 0 unit test `tests/unit/models/test_cav_raw_content.py` を新規作成し、 以下 4 件の test を pytest 形式 (関数群、 class 包装は不要) で実装する:

    1. `test_cav_constructs_without_raw_content_for_backcompat` — Phase 1 既存形式 `CAV(language="python", path="x.py", payload=ast.parse(""))` が成功し `.raw_content == b""` であることを assert。
    2. `test_cav_carries_raw_content_when_supplied` — `raw_content=b"def f(): pass"` を渡すと取り出せることを assert。
    3. `test_cav_raw_content_rejects_str` — `raw_content="not bytes"` で `pydantic.ValidationError` が raise されることを assert (Pydantic v2 strict 化のため、 必要なら `model_config` strict assertion を docstring で説明)。 注: Pydantic v2 既定では str → bytes 自動変換が起きるケースがあるため、 test は実機 fire してから判断する。 strict 変換が起きてしまう場合は test を `test_cav_raw_content_accepts_bytes_only` に rename し str 受領を許容する旨を rationale として SUMMARY に記録する (この点は実装 task 時に決定論的に検証する)。
    4. `test_cav_remains_frozen_after_raw_content_add` — `cav.raw_content = b"x"` 代入が `ValidationError` / `FrozenInstanceError` 相当を raise することを assert (D-05 frozen 維持の証跡)。

    既存 `tests/unit/models/test_cav.py` (Plan 01-03 が確立した frozen + Literal + arbitrary_types_allowed unit) を 1 行も編集しない。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/models/test_cav.py tests/unit/models/test_cav_raw_content.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `tests/unit/models/test_cav.py` 既存 unit が **0 件 broken** (Phase 1 baseline parity)
    - `tests/unit/models/test_cav_raw_content.py` の 4 件 (もしくは strict 変換挙動を踏まえた最終 3-4 件) が pass
    - `grep -n "raw_content" lib_code_parser/models/infrastructure/cav.py` が exactly 1 件 (field 宣言行) を返す
    - `grep -c "frozen=True" lib_code_parser/models/infrastructure/cav.py` が 1 を返す (D-05 frozen 維持の grep 証跡)
    - `grep -c 'extra="forbid"' lib_code_parser/models/infrastructure/cav.py` が 1 を返す (SCH-02 維持)
    - `grep -c "Traces:" lib_code_parser/models/infrastructure/cav.py` が 1 以上 (TRC-03 regex 維持)
    - `ruff check lib_code_parser/models/infrastructure/cav.py tests/unit/models/test_cav_raw_content.py` が exit 0
    - フル acceptance baseline parity: `pytest tests/acceptance/ tests/parity/ -x -q` が exit 0 (Phase 1 確立済 187 tests を破壊しない)
  </acceptance_criteria>
  <done>CAV モデルに additive `raw_content: bytes` field が追加され、 Phase 1 frozen / extra="forbid" / Literal language / arbitrary_types_allowed の 4 不変条件は不変。 後方互換性が unit + acceptance + parity の全 baseline で実証される。</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement frontends/python.py + register barrel re-export in frontends/__init__.py</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/frontends/__init__.py (Phase 1 placeholder docstring — 内容を本タスクで `build_cav` re-export に置換)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/_dispatch.py (`FrontendFn = Callable[[bytes, str, "ParserConfig"], "CAV"]` signature — `build_cav` はこの signature と一致させる)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/models/infrastructure/config.py (典型 ParserConfig — Frontend 実装側で `config` を直接参照する必要はないが signature 上必須)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/lib_code_parser/ast_extractor.py (v0.1.0 ast.parse + decode pattern — `source = raw_content.decode("utf-8", errors="replace")` と `ast.parse(source)` の 2 行が baseline。 Frontend が同 2 行を凝集して持つ)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§6.3 Frontend docstring template + §Code Examples §例 1 = build_cav 推奨実装の骨子)
  </read_first>
  <behavior>
    - `from lib_code_parser.frontends.python import build_cav` 成功
    - `from lib_code_parser.frontends import build_cav` 成功 (barrel re-export)
    - `build_cav(b"def foo(): pass", "foo.py", ParserConfig(artifact_type="code", executor_lib="lib_code_parser"))` が `CAV(language="python", path="foo.py", payload=<ast.Module>, raw_content=b"def foo(): pass")` を返す
    - `build_cav` 内で **`ast.parse` は厳密に 1 回呼ばれる** (monkeypatch で call_count == 1)
    - `build_cav` は raw bytes を `source = raw_content.decode("utf-8", errors="replace")` で decode する (v0.1.0 と同 policy、 Pitfall 13 の Windows cp1252 default を回避済み)
    - `build_cav(b"\xff\xfe invalid utf-8 \x80", "bad.py", config)` は decode error で fail しない (`errors="replace"` のため)、 CAV が `payload=ast.Module()` を伴って返る (`ast.parse` は string source なら invalid UTF-8 sequence を含まないため、 `�` 置換後の文字列が parse される)
    - `build_cav(b"def f(", "syntax_error.py", config)` は `SyntaxError` を caller に伝搬する (Frontend は SyntaxError を catch しない — v0.1.0 parity、 D-06 fail-loudly 原則)
    - module docstring の冒頭 1 行に `Implements: AST-05` を含み、 末尾に `Traces: AST-05, ARC-02` を含む (TRC-02 grep 検出可能形式)
  </behavior>
  <action>
    Step 1 — `lib_code_parser/frontends/python.py` を新規作成。 RESEARCH §Code Examples §例 1 を template に以下を実装する。 `from __future__ import annotations` を最初の行に置く。

    Module docstring (1 paragraph + 2 trace lines):
    ```
    """Python Frontend — ast.parse() the source exactly once and emit CAV envelope.

    This is the SINGLE site in lib_code_parser/extractors/ + frontends/ that
    calls ast.parse(). All primitive extractors consume cav.payload (already-
    parsed ast.Module) and never re-parse. The raw bytes are carried on the
    CAV envelope (cav.raw_content) so the type_deps extractor's PyrightAdapter
    can write them to its tmpdir without an ast.unparse() round-trip
    (which would drift line numbers).

    Implements: AST-05
    Traces: AST-05, ARC-02
    """
    ```

    Imports (absolute only per CONVENTIONS.md):
    ```
    import ast
    from lib_code_parser.models.infrastructure.cav import CAV
    from lib_code_parser.models.infrastructure.config import ParserConfig
    ```

    `__all__ = ["build_cav"]`.

    Function body:
    ```
    def build_cav(raw_content: bytes, path: str, config: ParserConfig) -> CAV:
        """Parse raw_content exactly once into ast.Module and wrap in a CAV envelope.

        AST-05 single-parse invariant: this is the ONLY ast.parse() call site for
        the Python language path. Primitive extractors (functions / callgraph /
        type_deps / contracts) consume cav.payload and never re-parse.
        """
        source = raw_content.decode("utf-8", errors="replace")
        module = ast.parse(source, filename=path)
        return CAV(
            language="python",
            path=path,
            payload=module,
            raw_content=raw_content,
        )
    ```

    `config` 引数は signature 上 `FrontendFn` (`_dispatch.py`) と一致させるために宣言するが、 現時点で本体内では参照しない (Python 3.x parse は ParserConfig フィールドに依存しない)。 ruff F841 (unused) を避けるため、 Python の `del config` は使わず、 signature 上の名前は `_config` ではなく `config` のまま残す (D-03 dispatch の callable contract と整合)。 ruff F841 は引数では発火しないので問題なし。

    Step 2 — `lib_code_parser/frontends/__init__.py` の Phase 1 placeholder docstring (1 行) を **以下に置換**:
    ```
    """Frontends — language-specific CAV producers (1 parse per file).

    Phase 2 ships ``build_cav`` for Python via ``lib_code_parser.frontends.python``;
    Phase 4 will add the C++ adapter. Each Frontend is the single ast.parse() /
    libclang TranslationUnit creation site for its language. AST-05 invariant
    is enforced by ``tests/parity/test_ast_05_one_parse.py``.

    Implements: AST-05
    Traces: AST-05, ARC-02
    """
    from lib_code_parser.frontends.python import build_cav

    __all__ = ["build_cav"]
    ```

    既存の Phase 1 placeholder 1-line docstring (`"""Frontends (Phase 2 adds python.py; Phase 4 adds cpp.py). Empty placeholder in Phase 1."""`) を完全に置換する。 100-char line-length lint を満たすため複数行 docstring の各行は <= 100 chars に収める。

    Step 3 — Wave 0 unit test `tests/unit/frontends/__init__.py` を空 (1-line docstring `"""Unit tests for Python and C++ frontends."""`) で新規作成。

    Step 4 — Wave 0 unit test `tests/unit/frontends/test_python_frontend.py` を新規作成。 以下 7 件の test を実装する:

    1. `test_build_cav_returns_cav_with_language_python` — return type / language discriminator 検証
    2. `test_build_cav_payload_is_ast_module` — `isinstance(cav.payload, ast.Module)` assert
    3. `test_build_cav_carries_raw_content_verbatim` — 入力 bytes と `cav.raw_content` byte-equal
    4. `test_build_cav_decodes_utf8_with_replace` — `b"\xff\xfe bad bytes \x80 def f(): pass"` を渡しても crash せず、 `cav` が返り、 `ast.parse` が成功する (replace で `�` 置換された source を parse できる ことを assert)
    5. `test_build_cav_propagates_syntax_error` — `b"def f("` で `SyntaxError` が raise されることを assert
    6. `test_build_cav_parses_exactly_once` — pytest `monkeypatch` で `ast.parse` を spy し、 `build_cav` 1 回呼び出しで spy.call_count == 1 を assert (AST-05 dynamic gate 単体版)
    7. `test_build_cav_path_carried_to_cav` — `cav.path == "some/file.py"` (caller path metadata 伝達)

    `import ast`、 `from lib_code_parser.frontends.python import build_cav`、 `from lib_code_parser.models.infrastructure.config import ParserConfig` を absolute import で記述。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/unit/frontends/test_python_frontend.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/unit/frontends/test_python_frontend.py -x -q` exit 0 with 7 tests passing
    - `python -c "from lib_code_parser.frontends.python import build_cav; from lib_code_parser.frontends import build_cav as b2; assert build_cav is b2"` exit 0 (barrel identity)
    - `grep -c "^def build_cav" lib_code_parser/frontends/python.py` が 1 を返す
    - `grep -c "ast\.parse" lib_code_parser/frontends/python.py` が 1 を返す (= AST-05 の単一 parse site の宣言。 grep の counter-gate)
    - `grep -c "Implements: AST-05" lib_code_parser/frontends/python.py` が 1 を返す (TRC-02)
    - `grep -c "Traces: AST-05" lib_code_parser/frontends/python.py` が 1 以上 (TRC-03 regex 対応)
    - `grep -c "^def build_cav\|^def cpp_build_cav\|^def libclang_build_cav" lib_code_parser/frontends/python.py` が 1 (重複 Frontend 関数なし)
    - `ruff check lib_code_parser/frontends/ tests/unit/frontends/` exit 0
    - フル baseline parity: `pytest tests/acceptance/ tests/parity/ tests/unit/ -x -q` exit 0 (既存 baseline を破壊しない)
  </acceptance_criteria>
  <done>frontends/python.py が 1-parse Frontend を実装し、 barrel 経由でも import 可能。 7 件の unit test が green。 Phase 1 baseline tests に retrogression なし。</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Wave 0 — tests/parity/test_ast_05_one_parse.py (grep static gate + monkeypatch dynamic gate)</name>
  <read_first>
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/tests/parity/test_v01_v02_compat.py (Phase 1 で確立した parity test pattern、 特に `test_no_duplicate_module_name_helper` の subprocess.run(["grep", ...]) を retrieve — Phase 2 でも同形式を再利用する)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-RESEARCH.md (§5.2 推奨組み合わせ: primary grep + backup monkeypatch + foundation 構造制約)
    - C:/work/agent_company/spec-reviewer-libs/lib-code-parser/.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-VALIDATION.md (Wave 0 必須リスト中の `tests/parity/test_ast_05_one_parse.py`)
  </read_first>
  <behavior>
    Tests in `tests/parity/test_ast_05_one_parse.py`:

    1. `test_no_ast_parse_in_extractors_directory` — subprocess `["grep", "-rn", "-E", r"ast\.parse\(|from ast import parse", "lib_code_parser/extractors/", "--include=*.py"]` を実行し、 マッチが **0 件** であることを assert。 Wave 1 で extractors 配下に新規モジュールが作られても (functions/callgraph/type_deps/contracts)、 一切 `ast.parse(` を含んではならない (primary static gate)。
    2. `test_frontends_python_is_only_ast_parse_site` — 同 grep を `lib_code_parser/frontends/` に対して実行し、 マッチが **1 件** であり、 ファイルが `python.py` であることを assert (= Frontend 1 ファイルだけが parse site)。 補助 invariant。
    3. `test_no_ast_parse_in_adapters_directory` — `lib_code_parser/adapters/` 配下に `ast.parse(` が含まれないことを assert (adapter は subprocess を呼ぶだけで parse しない)。
    4. `test_single_parse_per_build_cav` (dynamic monkeypatch backup) — pytest fixture `monkeypatch` を受け取り、 `ast.parse` を spy 化して、 `build_cav(b"class Foo: pass\n", "foo.py", config)` を 1 回 invoke、 `spy.call_count == 1` を assert。 Wave 2 で executor が wired される前でも、 Frontend 単独で AST-05 invariant が成立していることを動的に証明する。

    既存 Phase 1 parity (`test_v01_v02_compat.py`) は **編集しない**。 Phase 2 AST-05 parity は別ファイル `test_ast_05_one_parse.py` に閉じる (D-04 「parity test 再設計」は別タスク 02-07 で行う; 02-01 では Wave 0 AST-05 部分のみを置く)。
  </behavior>
  <action>
    `tests/parity/test_ast_05_one_parse.py` を新規作成。 Module docstring に AST-05 invariant の根拠 (RESEARCH §5.2 primary = grep + backup = monkeypatch + foundation = signature) を 1 paragraph で記載。

    Imports:
    ```
    from __future__ import annotations
    import ast
    import subprocess
    from pathlib import Path
    import pytest
    ```

    Helper:
    ```
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent

    def _grep_ast_parse(target: str) -> list[str]:
        result = subprocess.run(
            ["grep", "-rn", "-E", r"ast\.parse\(|from ast import parse",
             str(_REPO_ROOT / target), "--include=*.py"],
            check=False, capture_output=True, text=True,
        )
        return [line for line in result.stdout.splitlines() if line.strip()]
    ```

    4 件の test を上記 `<behavior>` のとおり実装する。 test #4 (`test_single_parse_per_build_cav`) は以下のスケルトン:

    ```
    def test_single_parse_per_build_cav(monkeypatch: pytest.MonkeyPatch) -> None:
        from lib_code_parser.frontends.python import build_cav
        from lib_code_parser.models.infrastructure.config import ParserConfig

        real_parse = ast.parse
        call_count = 0

        def spy(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return real_parse(*args, **kwargs)

        monkeypatch.setattr(ast, "parse", spy)
        cav = build_cav(
            b"class Foo:\n    def bar(self): pass\n",
            "foo.py",
            ParserConfig(artifact_type="code", executor_lib="lib_code_parser"),
        )
        assert call_count == 1, (
            f"AST-05 violation: build_cav called ast.parse {call_count} times; "
            f"expected 1. The Frontend must be the SINGLE parse site."
        )
        assert isinstance(cav.payload, ast.Module)
    ```

    `tests/parity/__init__.py` は Phase 1 で既存 (Plan 01-09 が作成済) なので新規作成不要。
  </action>
  <verify>
    <automated>cd "C:/work/agent_company/spec-reviewer-libs/lib-code-parser" &amp;&amp; pytest tests/parity/test_ast_05_one_parse.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `pytest tests/parity/test_ast_05_one_parse.py -x -q` exit 0 with 4 tests passing
    - Wave 1 Plan 02-01 終了時点 (この plan): `lib_code_parser/extractors/` 配下に Phase 1 placeholder の `__init__.py` 以外 (extractors/__init__.py / extractors/primitives/__init__.py) があり、 grep gate は 0 件で pass する (Phase 1 placeholder docstring に `ast.parse` 文字列が含まれていないこと、 Phase 2 後続 plan 02-02..04 はまだ未着手であることが前提)
    - Phase 1 既存 parity tests を **1 件も破壊しない**: `pytest tests/parity/test_v01_v02_compat.py -x -q` が引き続き 11 件 pass
    - フル baseline: `pytest tests/ -x -q` exit 0 (Phase 1 187 tests + Plan 02-01 の新規 unit + parity)
    - `grep -c "def test_" tests/parity/test_ast_05_one_parse.py` が 4 を返す
    - `ruff check tests/parity/test_ast_05_one_parse.py` exit 0
  </acceptance_criteria>
  <done>AST-05 の primary (grep) + backup (monkeypatch) parity gate が Wave 0 で立つ。 後続 Wave 1 plan 02-02..04 が `ast.parse` を再導入すれば本 parity gate で必ず caught。</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| caller bytes → Frontend → CAV envelope | caller 渡しの bytes は本 plan で initial trust 化される。 UTF-8 errors="replace" で hostile bytes を sanitize。 ast.parse は SyntaxError を raise するため信頼境界の loud failure 担保あり |
| CAV.raw_content → 後続 Wave 2 type_deps extractor → PyrightAdapter tmpdir | raw_content は Wave 2 で subprocess fixture file に書き出される。 本 plan では carry のみで file system 接触なし |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-01 | Tampering | Phase 1 lock 違反: CAV モデル変更で D-04/D-05 が壊れる | mitigate | Task 1 は additive field のみ。 frozen + extra="forbid" + arbitrary_types_allowed=True + Literal language の 4 不変条件を grep gate で保護。 Phase 1 既存 `tests/unit/models/test_cav.py` が unchanged で pass することを acceptance に組込む |
| T-02-02 | Tampering | AST-05 invariant 違反: 後続 Wave 1 plan が extractor 内で `ast.parse` を呼ぶ | mitigate | Task 3 の grep static gate が `lib_code_parser/extractors/` 配下の `ast.parse(` 出現を 0 件で固定。 Wave 1 plan 02-02..04 の plan ファイル自身にも grep gate への acceptance reference を required にする |
| T-02-03 | DoS | invalid UTF-8 bytes で `decode` が crash | mitigate | `errors="replace"` で `�` 置換。 v0.1.0 と同 policy、 ast_extractor.py L59 の pattern を継承 |
| T-02-04 | Information disclosure | CAV.raw_content がログに垂れ流される | accept | 本 plan は lib boundary、 caller が CAV を直接出力しない限り I/O なし。 PyrightAdapter (Plan 02-05) で tmpdir 書き出し時に同等のリスクがあるが、 そこは internal tmpdir + 自動 cleanup で隔離 |
| T-02-05 | Supply chain | 本 plan は新規 pip 依存 install なし | accept | 全 import は Phase 1 で declared 済 (`pydantic`, stdlib `ast`)。 Package Legitimacy Audit は Phase 1 で完了済、 Phase 2 carry-forward |
</threat_model>

<verification>
- `pytest tests/unit/models/test_cav.py tests/unit/models/test_cav_raw_content.py tests/unit/frontends/test_python_frontend.py tests/parity/test_ast_05_one_parse.py -x -q` が exit 0
- フル baseline: `pytest tests/ -x -q` exit 0 (Phase 1 187 + Plan 02-01 新規 ~14 tests = 201 ± minor)
- Phase 1 lock 不変条件の grep gate 全 pass: CAV frozen / extra=forbid / Literal language / arbitrary_types_allowed
- AST-05 grep gate: `grep -rn -E "ast\.parse\(|from ast import parse" lib_code_parser/extractors/` 出力 0 件
- AST-05 single source: `lib_code_parser/frontends/python.py` 内 `ast.parse(` が exactly 1 件
- `ruff check lib_code_parser/ tests/` exit 0
</verification>

<success_criteria>
- Phase 2 ROADMAP success criterion 1 の半分が成立 (Frontend が 1-parse、 instrumentable via monkeypatch)
- Phase 2 ROADMAP success criterion 4 の前提が成立: `from lib_code_parser.frontends.python import build_cav; build_cav(...)` が isolated 呼び出し可能
- AST-05 invariant が grep static gate で永続的に enforced
- D-04 / D-05 (Phase 1 CAV lock) を破らずに type_deps extractor 用の `raw_content` carry path が確立
- TRC-02 docstring 形式 (`Implements: AST-NN` 行) が frontends/python.py に確立、 後続 Wave 1 plan の docstring template として参照可能
- TRC-03 regex (`Traces: REQ-ID, US-NN`) が `frontends/python.py` の docstring で抽出可能
</success_criteria>

<output>
Create `.planning/phases/02-python-frontend-ast-primitives-acl-2-adapters/02-01-SUMMARY.md` when done. Include:
1. pytest output (counts per directory: acceptance / parity / unit / models / frontends)
2. grep gate output for the AST-05 static gate (must show 0 matches in extractors/, 1 match in frontends/)
3. CAV model diff (before vs after — only `raw_content: bytes = b""` field added)
4. ruff check result
5. Phase 1 baseline parity (must remain green)
</output>
