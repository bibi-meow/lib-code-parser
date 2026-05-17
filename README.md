# lib-code-parser

Parse Python source code into structured representations: function nodes, call graphs, and type dependency graphs.

## What it does

Given a Python source file, `lib-code-parser` extracts:

- **FunctionNode list** — every function, method, and class with their parameters, return types, docstrings, and source locations
- **CallGraph** — static call relationships between functions (who calls whom)
- **TypeDep list** — type dependencies derived from annotations (optionally enhanced by `pyright`)
- **ContractInfo** — preconditions and invariants extracted from Pydantic validators and dataclass `__post_init__` methods
- **TraceTag list** — `# Traces: ID-01` comments parsed into structured tags

## Installation

```bash
pip install lib-code-parser
```

For enhanced type dependency analysis (optional):

```bash
pip install lib-code-parser pyright
```

## Quick start

```python
from lib_code_parser import parse_code, ParserConfig

source = b"""
def greet(name: str) -> str:
    # Traces: US-01
    return f"Hello {name}"

def main():
    greet("world")
"""

result = parse_code(source, path="example.py")

print(result.artifact_type)        # "code"
print(result.content.functions)    # [FunctionNode(node_id="<module>.greet", ...), ...]
print(result.content.call_graph.edges)  # [("<module>.main", "<module>.greet")]
print(result.content.type_deps)    # [TypeDep(source="<module>.greet", target="str", ...)]
```

## Configuration

```python
from lib_code_parser import parse_code, ParserConfig

config = ParserConfig(
    params={
        "callgraph_tool": "internal",   # always "internal" (built-in AST-based)
        "type_tool": "pyright",          # "pyright" or "ast" (fallback)
        "extract_contracts": True,       # extract Pydantic/dataclass validators
        "language": "python",            # only "python" supported currently
    }
)

result = parse_code(source_bytes, path="mymodule.py", config=config)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `callgraph_tool` | `str` | `"internal"` | Call graph engine. Only `"internal"` (AST-based) is supported. |
| `type_tool` | `str` | `"pyright"` | Type dependency tool. `"pyright"` uses subprocess; `"ast"` uses annotation parsing. Falls back gracefully if pyright is not installed. |
| `extract_contracts` | `bool` | `True` | Extract preconditions and invariants from Pydantic validators and dataclass `__post_init__`. |
| `language` | `str` | `"python"` | Source language. Only `"python"` is supported. |

## Output types

```python
@dataclass
class NormalizedArtifact:
    artifact_id: ArtifactId     # path + version
    artifact_type: str          # always "code"
    content: CodeContent

@dataclass
class CodeContent:
    functions: List[FunctionNode]
    call_graph: CallGraph
    type_deps: List[TypeDep]

@dataclass
class FunctionNode:
    node_id: str         # "module.ClassName.method_name"
    kind: str            # "function" | "method" | "class"
    params: List[ParamInfo]
    return_type: Optional[str]
    contracts: ContractInfo
    docstring: Optional[str]
    trace_tags: List[TraceTag]
    source_range: Optional[SourceRange]

@dataclass
class CallGraph:
    nodes: List[str]              # node_id list
    edges: List[Tuple[str, str]]  # (caller_id, callee_id) pairs

@dataclass
class TypeDep:
    source: str    # dependent (function or type name)
    target: str    # dependency (type name)
    dep_type: str  # "typing" | "inherit" | "import"
```

## Contract extraction (Pydantic / dataclass)

When `extract_contracts=True`, the library detects:

- `@field_validator("field_name")` decorators → `ContractInfo.preconditions`
- `@model_validator(mode=...)` decorators → `ContractInfo.invariants`
- `__post_init__` methods → `ContractInfo.preconditions`

```python
source = b"""
from pydantic import BaseModel, field_validator

class User(BaseModel):
    name: str

    @field_validator("name")
    def validate_name(cls, v):
        assert len(v) > 0
        return v
"""

result = parse_code(source, "user.py")
user_class = next(f for f in result.content.functions if f.node_id == "<module>.User")
print(user_class.contracts.preconditions)  # ["name"]
```

## Trace tag extraction

Comments in the format `# Traces: ID-01, ID-02` are extracted as `TraceTag` entries:

```python
source = b"""
def process():
    # Traces: US-01, FR-05
    pass
"""

result = parse_code(source, "proc.py")
fn = result.content.functions[0]
print(fn.trace_tags)
# [TraceTag(tag_type="Traces", source_id="US-01"), TraceTag(tag_type="Traces", source_id="FR-05")]
```

## Graceful degradation

If `pyright` is not installed, type dependency analysis falls back to AST annotation parsing. No exception is raised — `type_deps` will be populated from annotations only, or return an empty list if no annotations are found.

## License

MIT License. See [LICENSE](LICENSE).
