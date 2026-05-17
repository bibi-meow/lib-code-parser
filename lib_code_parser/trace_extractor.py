"""Trace tag extractor: parses '# Traces: ID, ID2' comments from source code."""

from __future__ import annotations

import io
import re
import tokenize

from lib_code_parser.models import TraceTag

# Pattern: "# Traces: US-01" or "# Traces: US-01, FR-02"
_TRACES_RE = re.compile(r"#\s*Traces\s*:\s*(.+)", re.IGNORECASE)
_ID_SPLIT_RE = re.compile(r"[,\s]+")


def extract_trace_tags(source: str) -> dict[str, list[TraceTag]]:
    """Extract Traces comments from Python source code.

    Scans all comment tokens for '# Traces: <id>[, <id>...]' patterns.

    Args:
        source: Python source code string.

    Returns:
        Dictionary mapping context key (line number as str) to list of TraceTags.
        All tags are accessible by flattening the values.
    """
    result: dict[str, list[TraceTag]] = {}

    if not source.strip():
        return result

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return result

    for tok_type, tok_string, tok_start, _tok_end, _line in tokens:
        if tok_type != tokenize.COMMENT:
            continue
        match = _TRACES_RE.match(tok_string)
        if not match:
            continue
        ids_str = match.group(1).strip()
        raw_ids = _ID_SPLIT_RE.split(ids_str)
        tags: list[TraceTag] = []
        for raw_id in raw_ids:
            raw_id = raw_id.strip()
            if raw_id:
                tags.append(TraceTag(tag_type="Traces", source_id=raw_id))

        if tags:
            key = str(tok_start[0])  # line number as key
            result.setdefault(key, []).extend(tags)

    return result
