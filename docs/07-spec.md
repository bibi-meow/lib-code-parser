# lib-code-parser API Spec

> lib の公開 API を定義する。dataclass / TypedDict で型を明示し、pseudocode でアルゴリズムを示す。
> design doc §7 Step 7 参照。
> **API signature は 06-architecture.md の DFD と一致させること。**

---

## 公開 API 一覧

| 関数 / クラス | 入力型 | 出力型 | 決定論性 |
|-------------|-------|-------|---------|
| `parse_code` | `bytes, str, ParserConfig` | `NormalizedArtifact` | D |
| `extract_functions` | `str` | `List[FunctionNode]` | D |
| `build_callgraph` | `str, List[FunctionNode]` | `CallGraph` | D |
| `analyze_type_deps` | `str, str, bool` | `List[TypeDep]` | D |
| `extract_contracts` | `ast.ClassDef` | `ContractInfo` | D |

---

## 型定義

```python
# models.py — 共有データクラス定義
# lib-code-parser.md の共有型定義 + bc-verification-engine.md §6 準拠

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ParamInfo:
    """関数引数の情報"""
    name: str
    type_annotation: Optional[str] = None  # 型アノテーション文字列（"str", "int" 等）


@dataclass
class SourceRange:
    """ソースコード上の行番号範囲"""
    start_line: int
    end_line: int


@dataclass
class TraceTag:
    """コードコメント内の Traces タグ"""
    tag_type: str      # "Traces"
    source_id: str     # "US-01" 等の ID
    target_id: str = ""  # 対応先 ID（将来拡張用）


@dataclass
class ContractInfo:
    """Pydantic / dataclass validator から抽出したコントラクト情報（§3.7）"""
    preconditions: List[str] = field(default_factory=list)
    # @field_validator / __post_init__ で検出した事前条件文字列
    invariants: List[str] = field(default_factory=list)
    # model_validator 等の不変条件文字列


@dataclass
class FunctionNode:
    """関数・メソッド・クラスの AST ノード情報"""
    node_id: str          # "module.ClassName.method_name" 形式の完全修飾名
    kind: str             # "function" | "method" | "class"
    params: List[ParamInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    contracts: ContractInfo = field(default_factory=ContractInfo)
    docstring: Optional[str] = None
    trace_tags: List[TraceTag] = field(default_factory=list)
    source_range: Optional[SourceRange] = None


@dataclass
class CallGraph:
    """関数間呼び出し関係グラフ"""
    nodes: List[str] = field(default_factory=list)
    # FunctionNode の node_id 一覧
    edges: List[Tuple[str, str]] = field(default_factory=list)
    # (caller_node_id, callee_node_id) ペア


@dataclass
class TypeDep:
    """型依存関係"""
    source: str           # 依存元（完全修飾型名 or 関数名）
    target: str           # 依存先（型名）
    dep_type: str = "typing"  # "typing" | "inherit" | "import"


@dataclass
class CodeContent:
    """コード解析結果の統合コンテナ"""
    functions: List[FunctionNode] = field(default_factory=list)
    call_graph: CallGraph = field(default_factory=CallGraph)
    type_deps: List[TypeDep] = field(default_factory=list)


@dataclass
class ArtifactId:
    """成果物 ID"""
    path: str
    version: str = "HEAD"


@dataclass
class NormalizedArtifact:
    """正規化された成果物（lib の公開出力型）"""
    artifact_id: ArtifactId
    artifact_type: str    # 常に "code"
    content: CodeContent


@dataclass
class ParserConfig:
    """パーサー設定"""
    artifact_type: str = "code"
    executor_lib: str = "lib_code_parser.parser"
    params: dict = field(default_factory=lambda: {
        "callgraph_tool": "internal",
        "type_tool": "pyright",
        "extract_contracts": True,
        "language": "python",
    })
    enabled: bool = True
```

---

## API signature

```python
# parser.py — メイン公開 API

def parse_code(
    raw_content: bytes,
    path: str,
    config: Optional[ParserConfig] = None,
) -> NormalizedArtifact:
    """
    Python ソースコードを解析し、NormalizedArtifact として返す。

    AST 解析で FunctionNode リスト・CallGraph・TypeDep リスト・ContractInfo を生成し、
    CodeContent にまとめて NormalizedArtifact として返す。

    Args:
        raw_content: Python ソースコードの生バイト（UTF-8 エンコード）
        path: VCS 上のファイルパス（言語補助判定に使用）
        config: パーサー設定（None の場合はデフォルト設定を使用）

    Returns:
        NormalizedArtifact: artifact_type="code", content=CodeContent

    Raises:
        ValueError: ソースコードのデコードまたは AST パースに失敗した場合
        ValueError: サポート外の言語（.cpp 等）の場合

    Traces: LIB-FR-01, LIB-FR-02, LIB-FR-03, LIB-FR-04, LIB-FR-05, LIB-FR-06
    Decision Log: #7-1
    """
    ...
```

```python
# ast_extractor.py

def extract_functions(source: str, module_name: str = "<module>") -> List[FunctionNode]:
    """
    Python ソースコード文字列から FunctionNode リストを抽出する。

    Args:
        source: Python ソースコード（str）
        module_name: モジュール名（node_id のプレフィックス）

    Returns:
        List[FunctionNode]: 検出された関数・メソッド・クラスのリスト

    Raises:
        ValueError: SyntaxError が発生した場合

    Traces: LIB-FR-01, LIB-FR-05
    """
    ...
```

```python
# callgraph_builder.py

def build_callgraph(source: str, functions: List[FunctionNode]) -> CallGraph:
    """
    Python ソースコードから ast.Call を追跡して CallGraph を生成する。

    Args:
        source: Python ソースコード（str）
        functions: extract_functions() が返した FunctionNode リスト

    Returns:
        CallGraph: nodes（node_id 一覧）+ edges（呼び出し関係）

    Traces: LIB-FR-02
    """
    ...
```

```python
# type_analyzer.py

def analyze_type_deps(
    source: str,
    path: str,
    use_pyright: bool = True,
) -> List[TypeDep]:
    """
    型依存グラフを生成する。pyright がある場合は subprocess 経由、なければ ast fallback。

    Args:
        source: Python ソースコード（str）
        path: ファイルパス（pyright の一時ファイル作成に使用）
        use_pyright: True の場合 pyright を試みる（デフォルト）

    Returns:
        List[TypeDep]: 型依存関係リスト（pyright 未インストール時は空リストまたは ast fallback）

    Traces: LIB-FR-03, LIB-NFR-01
    """
    ...
```

```python
# contract_extractor.py
import ast as ast_module

def extract_contract_info(class_node: ast_module.ClassDef) -> ContractInfo:
    """
    ClassDef ノードから ContractInfo（preconditions / invariants）を抽出する。

    @field_validator / model_validator / __post_init__ を検出する。

    Args:
        class_node: ast.ClassDef ノード

    Returns:
        ContractInfo: preconditions と invariants を含む

    Traces: LIB-FR-04
    """
    ...
```

---

## Pseudocode

```
function parse_code(raw_content, path, config):
  1. [設定確認]: config が None なら ParserConfig デフォルトを使用
  2. [言語判定]: path の拡張子が ".py" でなければ ValueError
  3. [デコード]: raw_content.decode("utf-8") → source str
                 UnicodeDecodeError → ValueError
  4. [AST パース]: ast.parse(source) → tree
                  SyntaxError → ValueError（パスとエラー位置を含む）
  5. [モジュール名]: path のファイル名から拡張子を除いた文字列
  6. [FunctionNode 抽出]: extract_functions(source, module_name)
                          → List[FunctionNode]（TraceTag / ContractInfo 含む）
  7. [CallGraph 生成]: build_callgraph(source, functions)
                       → CallGraph
  8. [TypeDep 生成]: analyze_type_deps(source, path, use_pyright=...)
                     → List[TypeDep]（失敗時は graceful degrade）
  9. [CodeContent 組立]: CodeContent(functions, call_graph, type_deps)
  10. [NormalizedArtifact 生成]:
        ArtifactId(path=path, version="HEAD")
        NormalizedArtifact(artifact_id, artifact_type="code", content)
  11. return NormalizedArtifact
```

```
function extract_functions(source, module_name):
  1. tree = ast.parse(source)
  2. class_stack = []  # クラス名スタック（ネスト対応）
  3. result = []
  4. for node in ast.walk(tree):
       if isinstance(node, ClassDef):
         node_id = module_name + "." + node.name
         source_range = SourceRange(node.lineno, node.end_lineno)
         contracts = extract_contract_info(node)  # §3.7
         fn = FunctionNode(node_id, "class", contracts=contracts, source_range=source_range)
         result.append(fn)
       elif isinstance(node, FunctionDef or AsyncFunctionDef):
         [parent クラスを特定し kind を "method" or "function" に決定]
         node_id = [module.Class.func または module.func]
         params = [arg.arg + annotation for arg in node.args.args]
         return_type = [ast.unparse(node.returns) if node.returns else None]
         docstring = ast.get_docstring(node)
         trace_tags = extract_trace_tags_from_docstring(docstring)
         fn = FunctionNode(node_id, kind, params, return_type, ContractInfo(), docstring, trace_tags, source_range)
         result.append(fn)
  5. return result
```

**Decision Log**: #7-1（API 設計の判断を記録）

---

## 決定 #7-1（Step 8: API 設計）

- **What**: `parse_code(raw_content, path, config)` を単一のエントリポイントとして設計した
- **Options considered**: A) 単一エントリポイント、B) 機能別に複数の公開関数
- **Decision**: A）`parse_code` を主エントリポイント、内部関数は `extract_functions` 等を公開（テスト容易性のため）
- **Rationale**: 06-architecture.md の DFD に従い、統合出力（NormalizedArtifact）が主目的。個別関数はテスト用に公開する
- **Determinism**: D
- **Reviewable by**: 06-architecture.md DFD との一致確認
- **Traces from**: 06-architecture.md §DFD
- **Traces to**: Step 9 scaffold（モジュール名確定）、Step 10 TDD 実装

<!-- 実装開始（Step 9）前にこの spec が 06-architecture.md と一致していることを確認すること -->
