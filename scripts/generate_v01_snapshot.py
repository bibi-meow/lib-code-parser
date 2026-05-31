"""Generate tests/parity/fixtures/v01_snapshot.json from conftest EXAMPLE_SOURCE.

Run once with pyright installed:

    python scripts/generate_v01_snapshot.py

Commits the resulting JSON as the byte-identical snapshot baseline consumed by
tests/parity/test_snapshot_v01_fixture.py. Re-run only when intentionally
updating the snapshot (document the rationale in the plan / SUMMARY docs).

The fixture is the source of truth; this script is a throwaway regenerator and
uses only Phase 2 deliverables (no extra dependencies).
"""

from __future__ import annotations

from pathlib import Path

from lib_code_parser import CodeParserExecutor, ParserConfig
from tests.conftest import EXAMPLE_PATH, EXAMPLE_SOURCE


def main() -> None:
    config = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    exe = CodeParserExecutor()
    result = exe.execute(config, EXAMPLE_SOURCE.encode("utf-8"), EXAMPLE_PATH)
    json_out = result.model_dump_json(indent=2)
    target = Path(__file__).parent.parent / "tests" / "parity" / "fixtures" / "v01_snapshot.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json_out, encoding="utf-8")
    print(f"Wrote {target}: {len(json_out)} chars")


if __name__ == "__main__":
    main()
