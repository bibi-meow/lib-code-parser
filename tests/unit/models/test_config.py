"""Wave 0 tests for ParserConfig (typed fields per ARC-05).

Traces: ARC-05, SCH-02, D-08.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lib_code_parser.models.infrastructure.config import ParserConfig


def test_parser_config_typed_fields() -> None:
    """All typed fields are accepted and accessible."""
    cfg = ParserConfig(
        artifact_type="code",
        executor_lib="lib_code_parser",
        language="python",
        extract_contracts=True,
        compile_args=["-std=c++17"],
        python_version="3.12",
        enabled=True,
    )
    assert cfg.artifact_type == "code"
    assert cfg.executor_lib == "lib_code_parser"
    assert cfg.language == "python"
    assert cfg.extract_contracts is True
    assert cfg.compile_args == ["-std=c++17"]
    assert cfg.python_version == "3.12"
    assert cfg.enabled is True


def test_parser_config_defaults() -> None:
    """Defaults: language='python', extract_contracts=True, compile_args=['-std=c++17'],
    python_version='3.12', enabled=True.
    """
    cfg = ParserConfig(artifact_type="code", executor_lib="lib_code_parser")
    assert cfg.language == "python"
    assert cfg.extract_contracts is True
    assert cfg.compile_args == ["-std=c++17"]
    assert cfg.python_version == "3.12"
    assert cfg.enabled is True


def test_parser_config_rejects_unknown_field() -> None:
    """ParserConfig extra='forbid'; unknown_field raises ValidationError (SCH-02 / ARC-05)."""
    with pytest.raises(ValidationError):
        ParserConfig(  # type: ignore[call-arg]
            artifact_type="code",
            executor_lib="lib_code_parser",
            unknown_field=1,
        )


def test_parser_config_language_literal() -> None:
    """ParserConfig.language is a Literal['python', 'cpp']; 'rust' must be rejected."""
    with pytest.raises(ValidationError):
        ParserConfig(  # type: ignore[arg-type]
            artifact_type="code",
            executor_lib="lib_code_parser",
            language="rust",
        )


def test_parser_config_no_params_dict_field() -> None:
    """ARC-05 hard gate: the v0.1.0 untyped `params: dict[str, object]` field must be ABSENT."""
    assert "params" not in ParserConfig.model_fields
