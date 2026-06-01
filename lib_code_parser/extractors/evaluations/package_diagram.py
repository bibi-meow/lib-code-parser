"""DIA-04 package diagram extractor (directory/namespace hierarchy).

Emits ``GraphNode(node_type="package")`` for each package level derived from the
source file's path (``src/foo/bar/baz.py`` → packages ``src``, ``src.foo``,
``src.foo.bar`` and the module ``src.foo.bar.baz``). One CAV carries one file,
so a single ``extract`` call yields the chain of packages containing that file;
the verifier (or caller) unions multiple files into the full project tree.

D-04 / D-05 / D-06 (must-haves):
- ``node_type="package"`` is a plain ``str`` value — GraphNode.node_type is a
  plain str (not a Literal), so this needs NO GraphNode schema change and NO
  sibling lib-diagram-parser code change. DIA-04 is completed entirely in-lib;
  it is NOT blocked on any sibling-lib PR.
- Containment is expressed via ``GraphNode.attributes={"parent_package": ...}``
  (the D-01 sub-decision resolved in Plan 01) rather than a ``contains`` edge —
  GraphNode already carries ``attributes: dict[str, str]``. No ``contains``
  EdgeKind is added; package containment as an attribute is sufficient for
  verifier comparison.

DET-04: nodes sorted by ``node_id`` on exit → byte-identical across
PYTHONHASHSEED. ``dict.fromkeys`` gives ordered dedup.

Implements: DIA-04, DIA-07
Traces: DIA-04, DIA-07, US-25, US-32
"""

from __future__ import annotations

import ast
from pathlib import PurePosixPath

from lib_code_parser.models.evaluations.graph_base import GraphModel, GraphNode
from lib_code_parser.models.infrastructure.cav import CAV
from lib_code_parser.models.infrastructure.config import ParserConfig

__all__ = ["extract"]


def _package_chain(path: str) -> list[str]:
    """Derive the dotted package chain (excluding the module itself) from a path.

    ``src/foo/bar/baz.py`` → ``["src", "src.foo", "src.foo.bar"]``. Backslashes
    are normalized to forward slashes so Windows-style paths produce the same
    deterministic chain. A bare ``baz.py`` (no directory) yields ``[]``.
    """
    # Normalize separators so the chain is OS-independent (DET-04: byte-stable).
    normalized = path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    # Drop the filename component (the module); keep the directory chain.
    dir_parts = parts[:-1]
    chain: list[str] = []
    for i in range(len(dir_parts)):
        chain.append(".".join(dir_parts[: i + 1]))
    return chain


def extract(cav: CAV, config: ParserConfig) -> GraphModel:
    """DIA-04: emit a package GraphModel (package nodes + attribute containment).

    Each directory level of ``cav.path`` becomes one ``package`` node. Containment
    is carried on each node's ``attributes["parent_package"]`` (the enclosing
    package's node_id, or absent for the top-level package). Multiple packages
    per file path are represented; a flat single-file path yields no packages.
    """
    tree = cav.payload
    assert isinstance(tree, ast.Module), (
        f"package_diagram extractor requires Python CAV (ast.Module payload), "
        f"got {type(tree).__name__}"
    )

    chain = _package_chain(cav.path)
    # Ordered dedup (a single chain is already unique, but keep the idiom).
    chain = list(dict.fromkeys(chain))

    nodes: list[GraphNode] = []
    for pkg_id in chain:
        # parent_package is the dotted prefix up to the last segment.
        parent = pkg_id.rsplit(".", 1)[0] if "." in pkg_id else ""
        attributes = {"parent_package": parent} if parent else {}
        nodes.append(
            GraphNode(
                node_id=pkg_id,
                node_type="package",
                label=pkg_id.rsplit(".", 1)[-1],
                attributes=attributes,
            )
        )

    # DET-04 sort-on-exit.
    nodes.sort(key=lambda n: n.node_id)

    return GraphModel(nodes=nodes)
