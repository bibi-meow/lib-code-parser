# lib-code-parser Requirements

> cicd の lib-*.md から lib-level の機能要求（FR）を導出する。
> design doc §7 Step 5 参照。
> **Gherkin 形式で受入テスト（AT）を記述すること。**

---

## 対応 cicd lib 設計

| 設計ドキュメント | パス |
|---------------|------|
| lib-code-parser.md | cicd/doc/sys/lib/lib-code-parser.md |

---

## 機能要求一覧

| FR ID | 説明 | 決定論性 | Decision Log |
|-------|------|---------|-------------|
| LIB-FR-01 | Python コードから FunctionNode 一覧を抽出する | D | #6-1 |
| LIB-FR-02 | Python コードから CallGraph を生成する | D | #6-2 |
| LIB-FR-03 | Python コードから TypeDep リストを生成する（pyright/fallback） | D | #6-3 |
| LIB-FR-04 | Pydantic / dataclass validator から ContractInfo を抽出する | D | #6-4 |
| LIB-FR-05 | コードコメントから TraceTag を抽出する | D | #6-5 |
| LIB-FR-06 | 全結果を NormalizedArtifact に統合して返す | D | #6-6 |
| LIB-NFR-01 | pyright がない環境でも graceful degrade する（TypeDep は空リスト） | D | #6-7 |
| LIB-NFR-02 | extract_contracts=False の場合は ContractInfo を空で返す | D | #6-8 |

---

## LIB-FR-01: Python コードから FunctionNode 一覧を抽出する

**概要**: Python ソースコード（bytes）を ast.parse し、関数・メソッド・クラスを FunctionNode として抽出する

**入力**: `raw_content: bytes`（Python ソースコード）, `path: str`（ファイルパス）
**出力**: `List[FunctionNode]`
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: FunctionNode 抽出
  Python コードファイルから関数・メソッド・クラスの情報を抽出する

  Scenario: 単純な関数を抽出する
    Given Python ソースコード "def greet(name: str) -> str:\n    return f'Hello {name}'"
    When parse_code を実行する
    Then functions に 1 件の FunctionNode が含まれる
    And FunctionNode.node_id は "<module>.greet" である
    And FunctionNode.kind は "function" である
    And FunctionNode.params に name (type: str) が含まれる
    And FunctionNode.return_type は "str" である

  Scenario: クラスとメソッドを抽出する
    Given Python ソースコードにクラス MyClass と メソッド my_method がある
    When parse_code を実行する
    Then FunctionNode の kind="class" と kind="method" が両方含まれる
    And メソッドの node_id は "<module>.MyClass.my_method" 形式である

  Scenario: 空ファイルを処理する
    Given 空の Python ソースコード ""
    When parse_code を実行する
    Then functions は空リスト [] である
    And call_graph.nodes は空リスト [] である
```

**AT ファイル**: `tests/test_function_extraction.py`
**Decision Log**: #6-1

---

## LIB-FR-02: Python コードから CallGraph を生成する

**概要**: ast.Call ノードを追跡して関数間呼び出し関係を抽出し、CallGraph として返す

**入力**: `raw_content: bytes`（Python ソースコード）
**出力**: `CallGraph(nodes, edges)`
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: CallGraph 生成
  Python コードの関数間呼び出し関係を静的解析で生成する

  Scenario: 関数呼び出しを検出する
    Given Python ソースコード:
      """
      def foo():
          bar()

      def bar():
          pass
      """
    When parse_code を実行する
    Then call_graph.edges に ("<module>.foo", "<module>.bar") が含まれる
    And call_graph.nodes に "<module>.foo" と "<module>.bar" が含まれる

  Scenario: 呼び出しがない場合
    Given 関数間の呼び出しがない Python ソースコード
    When parse_code を実行する
    Then call_graph.edges は空リスト [] である
    And call_graph.nodes に関数名が含まれる
```

**AT ファイル**: `tests/test_callgraph.py`
**Decision Log**: #6-2

---

## LIB-FR-03: TypeDep リストを生成する

**概要**: pyright subprocess 経由（利用可能な場合）または ast アノテーション解析（fallback）で型依存グラフを生成する

**入力**: `raw_content: bytes`（Python ソースコード）, `config.params.type_tool: str`
**出力**: `List[TypeDep]`
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: TypeDep 生成
  Python コードの型依存関係を解析する

  Scenario: ast fallback で型アノテーションから TypeDep を生成する
    Given Python ソースコード "def process(data: MyData) -> ResultType:\n    pass"
    And pyright がインストールされていない（または type_tool="ast"）
    When parse_code を実行する
    Then type_deps に TypeDep(source="<module>.process", target="MyData") が含まれる

  Scenario: pyright が利用不可の場合は graceful degrade する
    Given pyright がインストールされていない環境
    When parse_code を実行する
    Then type_deps は空リスト [] または ast fallback の結果が返される
    And 例外は発生しない
```

**AT ファイル**: `tests/test_type_deps.py`
**Decision Log**: #6-3

---

## LIB-FR-04: Pydantic / dataclass validator から ContractInfo を抽出する

**概要**: @field_validator / model_validator / __post_init__ を AST で検出し、ContractInfo として返す

**入力**: ClassDef を含む `raw_content: bytes`
**出力**: 各 FunctionNode の `contracts: ContractInfo`
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: ContractInfo 抽出（§3.7 Pydantic / dataclass validator）
  Pydantic v2 および dataclass の validator からコントラクト情報を抽出する

  Scenario: Pydantic @field_validator を抽出する
    Given Python ソースコード:
      """
      from pydantic import BaseModel, field_validator

      class User(BaseModel):
          name: str

          @field_validator("name")
          def validate_name(cls, v):
              assert len(v) > 0
              return v
      """
    When parse_code を実行する
    Then User クラスの FunctionNode.contracts.preconditions に "name" が含まれる

  Scenario: dataclass __post_init__ を抽出する
    Given Python ソースコード:
      """
      from dataclasses import dataclass

      @dataclass
      class Point:
          x: float
          y: float

          def __post_init__(self):
              assert self.x >= 0
      """
    When parse_code を実行する
    Then Point クラスの FunctionNode.contracts.preconditions に "x >= 0" 相当の情報が含まれる

  Scenario: extract_contracts=False の場合は抽出しない
    Given extract_contracts=False の ParserConfig
    When parse_code を実行する
    Then 全 FunctionNode.contracts.preconditions は空リストである
    And 全 FunctionNode.contracts.invariants は空リストである
```

**AT ファイル**: `tests/test_contract_extraction.py`
**Decision Log**: #6-4

---

## LIB-FR-05: コードコメントから TraceTag を抽出する

**概要**: "Traces: US-01, FR-02" 形式のコメントを TraceTag として抽出する

**入力**: `raw_content: bytes`（Python ソースコード）
**出力**: 各 FunctionNode の `trace_tags: List[TraceTag]`
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: TraceTag 抽出
  コードコメント内の Traces タグを抽出する

  Scenario: 単一 Trace タグを抽出する
    Given Python ソースコード:
      """
      def process():
          # Traces: US-01
          pass
      """
    When parse_code を実行する
    Then process の FunctionNode.trace_tags に TraceTag(tag_type="Traces", source_id="US-01") が含まれる

  Scenario: 複数 Trace タグを抽出する
    Given 関数に "# Traces: US-01, FR-02" コメントがある
    When parse_code を実行する
    Then trace_tags に US-01 と FR-02 の 2 件の TraceTag が含まれる

  Scenario: Trace タグなしの場合
    Given Traces コメントがない Python ソースコード
    When parse_code を実行する
    Then 全 FunctionNode.trace_tags は空リスト [] である
```

**AT ファイル**: `tests/test_trace_tags.py`
**Decision Log**: #6-5

---

## LIB-FR-06: NormalizedArtifact に統合して返す

**概要**: FR-01〜05 の結果を CodeContent にまとめ、NormalizedArtifact として返す

**入力**: `raw_content: bytes`, `path: str`, `config: ParserConfig`
**出力**: `NormalizedArtifact(artifact_id, artifact_type="code", content=CodeContent)`
**決定論性**: D

### Gherkin 受入テスト

```gherkin
Feature: NormalizedArtifact 統合
  全解析結果を NormalizedArtifact として返す

  Scenario: 正常な Python ファイルを解析する
    Given 有効な Python ソースコードと ParserConfig
    When parse_code を実行する
    Then NormalizedArtifact が返される
    And artifact_type は "code" である
    And content は CodeContent 型である
    And content.functions は List[FunctionNode] である
    And content.call_graph は CallGraph である
    And content.type_deps は List[TypeDep] である

  Scenario: 不正な Python ファイルを処理する
    Given SyntaxError を含む Python ソースコード
    When parse_code を実行する
    Then ValueError が raise される
```

**AT ファイル**: `tests/test_normalized_artifact.py`
**Decision Log**: #6-6
