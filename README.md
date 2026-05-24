# lib-code-parser

Parse Python source files to extract function graphs, call graphs, type dependencies, and validator contracts.

## Installation

```bash
pip install lib-code-parser
```

## What it does

Given a Python source file as bytes, `lib-code-parser` extracts:

- **Function nodes** — all functions, async functions, methods, and class definitions with their parameters, return types, docstrings, and source ranges
- **Call graph** — static call relationships between functions and methods
- **Type dependencies** — types imported or referenced via annotations
- **Validator contracts** — Pydantic `field_validator` / `model_validator` / `__post_init__` entries mapped to pre-conditions and invariants
- **Trace tags** — `Traces: FR-01, US-22` comments extracted from docstrings for traceability

## Quick start

```python
from lib_code_parser import CodeParserExecutor, ParserConfig

source = b"""
class OrderService:
    def create_order(self, items: list[str]) -> dict:
        \"\"\"Create a new order.

        Traces: FR-01
        \"\"\"
        return {}
"""

config = ParserConfig(
    artifact_type="code",
    executor_lib="lib_code_parser",
    params={"language": "python", "extract_contracts": True},
    enabled=True,
)

executor = CodeParserExecutor()
result = executor.execute(config, source, "src/order_service.py")

print(result.artifact_id.path)           # "src/order_service.py"
print(result.content.functions)          # list[FunctionNode]
print(result.content.call_graph.edges)   # list[CallEdge]
print(result.content.type_deps)          # list[TypeDep]
```

## Configuration

| `params` key | Type | Default | Description |
|---|---|---|---|
| `language` | `"python"` \| `"cpp"` | `"python"` | Source language. C++ returns empty content (not yet supported). |
| `extract_contracts` | `bool` | `True` | Extract Pydantic validators as `ContractInfo`. |

Setting `enabled=False` returns an empty `CodeContent` immediately without parsing.

## Output models

### `FunctionNode`

| Field | Type | Description |
|---|---|---|
| `node_id` | `str` | Qualified name: `"module.ClassName.method"` or `"module.function"` |
| `kind` | `"function"` \| `"method"` \| `"class"` | Node type |
| `params` | `list[ParamInfo]` | Parameters with type annotations |
| `return_type` | `str` | Return type annotation (unparsed) |
| `contracts` | `ContractInfo` | Preconditions and invariants |
| `docstring` | `str` | Raw docstring |
| `trace_tags` | `list[TraceTag]` | Extracted `Traces:` references |
| `source_range` | `SourceRange` | Line start/end in the source file |

### `CallGraph`

| Field | Type | Description |
|---|---|---|
| `nodes` | `list[str]` | All qualified node IDs |
| `edges` | `list[CallEdge]` | `caller → callee` pairs |

### `TypeDep`

| Field | Type | Description |
|---|---|---|
| `source` | `str` | Module name |
| `target` | `str` | Imported or referenced type |
| `kind` | `"imports"` \| `"uses"` | Relationship kind |

### `ContractInfo`

| Field | Type | Description |
|---|---|---|
| `preconditions` | `list[str]` | `field_validator` / `validator` / `__post_init__` method names |
| `invariants` | `list[str]` | `model_validator` method names |

## Trace tag format

Add `Traces:` lines to docstrings using comma-separated IDs:

```python
def my_function():
    """Does something important.

    Traces: US-01, FR-05
    """
```

Each ID must match the pattern `[A-Z]+-\d+` (e.g. `US-01`, `FR-05`, `REQ-123`).

## Language support

| Language | Status |
|---|---|
| Python | Supported (stdlib `ast` module) |
| C++ | Not yet supported — returns empty `CodeContent` |

## Development

```bash
git clone https://github.com/bibi-meow/lib-code-parser
cd lib-code-parser
pip install -e ".[dev]"
pytest
```

## License

`lib-code-parser` itself is licensed under the **Apache License 2.0**. See the [`LICENSE`](./LICENSE) file at the project root for the full text, including the Section 3 patent grant.

**No GPL bundled.** This library does not depend on, bundle, or invoke any GPL-licensed tool at runtime. The call graph extractor is internal to `lib-code-parser` (it is **not** `pyan3`, and **not** `ACL-2` — both of which were incorrectly referenced in the v0.1.0 spec doc and are being corrected). Bundled and runtime dependency licenses:

| Component | License | Notes |
|---|---|---|
| `lib-code-parser` itself | Apache-2.0 | This library; see [`LICENSE`](./LICENSE) |
| Call graph extractor | Internal (Apache-2.0) | Not `pyan3` (GPL v2), not `ACL-2`; ships as part of this library |
| `pyright` | MIT | Subprocess dev-dependency for Phase 2 PyrightAdapter (`pyright[nodejs]==1.1.409`) |
| `libclang` | Apache-2.0 WITH LLVM exception | In-process ctypes dependency, strictly pinned to `==18.1.1` (DET-02); the LLVM exception softens copyleft propagation for static linking |
