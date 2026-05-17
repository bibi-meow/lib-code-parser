"""Tests for LIB-FR-05: TraceTag extraction from code comments."""

from lib_code_parser.trace_extractor import extract_trace_tags


def test_single_trace_tag():
    source = "# Traces: US-01\ndef foo():\n    pass\n"
    tags = extract_trace_tags(source)
    all_tags = [t for ts in tags.values() for t in ts]
    assert any(t.source_id == "US-01" and t.tag_type == "Traces" for t in all_tags)


def test_multiple_trace_ids_in_one_line():
    source = "# Traces: US-01, FR-02\ndef foo():\n    pass\n"
    tags = extract_trace_tags(source)
    all_tags = [t for ts in tags.values() for t in ts]
    ids = [t.source_id for t in all_tags]
    assert "US-01" in ids
    assert "FR-02" in ids


def test_no_traces_returns_empty():
    source = "def foo():\n    pass\n"
    tags = extract_trace_tags(source)
    assert all(len(v) == 0 for v in tags.values())


def test_trace_key_is_file_level_when_outside_function():
    source = "# Traces: US-01\n"
    tags = extract_trace_tags(source)
    all_tags = [t for ts in tags.values() for t in ts]
    assert len(all_tags) == 1


def test_trace_inside_function():
    source = "def foo():\n    # Traces: FR-03\n    pass\n"
    tags = extract_trace_tags(source)
    all_tags = [t for ts in tags.values() for t in ts]
    assert any(t.source_id == "FR-03" for t in all_tags)


def test_trace_tag_type_is_traces():
    source = "# Traces: US-10\n"
    tags = extract_trace_tags(source)
    all_tags = [t for ts in tags.values() for t in ts]
    assert all(t.tag_type == "Traces" for t in all_tags)
