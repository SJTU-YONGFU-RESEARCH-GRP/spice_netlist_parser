"""Tests for configuration, exceptions, and logging utilities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


from spice_netlist_parser.config import (
    ParserConfig,
    get_config,
    get_default_output_format,
    get_log_level,
    get_max_file_size,
    is_caching_enabled,
    reload_config,
)
from spice_netlist_parser.exceptions import ParseError, ValidationError
from spice_netlist_parser.logging_config import get_logger, setup_logging

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def test_parse_error_formatting() -> None:
    """ParseError should include filename and line context in its message."""

    err = ParseError("boom", filename="file.sp", line_number=7)
    msg = str(err)
    assert "File: file.sp" in msg
    assert "Line 7" in msg
    assert "boom" in msg


def test_validation_error_message() -> None:
    """ValidationError should preserve the provided message."""

    err = ValidationError("invalid netlist")
    assert "invalid netlist" in str(err)
    assert err.message == "invalid netlist"


def test_config_reload_env(monkeypatch: MonkeyPatch) -> None:
    """Environment variables should override config when reloaded."""

    monkeypatch.setenv("SPICE_PARSER_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SPICE_PARSER_DEFAULT_OUTPUT_FORMAT", "json")
    reload_config()

    cfg = get_config()
    assert isinstance(cfg, ParserConfig)
    assert get_log_level() == "DEBUG"
    assert get_default_output_format() == "json"

    # Clean up and restore defaults
    monkeypatch.delenv("SPICE_PARSER_LOG_LEVEL", raising=False)
    monkeypatch.delenv("SPICE_PARSER_DEFAULT_OUTPUT_FORMAT", raising=False)
    reload_config()


def test_config_convenience_getters(monkeypatch: MonkeyPatch) -> None:
    """Convenience getters should mirror the underlying config values."""

    monkeypatch.setenv("SPICE_PARSER_MAX_FILE_SIZE", "1234")
    monkeypatch.setenv("SPICE_PARSER_ENABLE_CACHING", "false")
    reload_config()

    assert get_max_file_size() == 1234  # noqa: PLR2004
    assert is_caching_enabled() is False

    monkeypatch.delenv("SPICE_PARSER_MAX_FILE_SIZE", raising=False)
    monkeypatch.delenv("SPICE_PARSER_ENABLE_CACHING", raising=False)
    reload_config()


def test_setup_logging_writes_file(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    """setup_logging should configure console and file handlers."""

    log_file = tmp_path / "app.log"
    setup_logging(level="INFO", log_file=log_file)
    logger = get_logger("test")

    with caplog.at_level(logging.INFO):
        logger.info("hello")

    assert log_file.exists()
    contents = log_file.read_text(encoding="utf-8")
    assert "hello" in contents


def test_setup_logging_replaces_handlers(tmp_path: Path) -> None:
    """Calling setup_logging twice should reset handlers cleanly."""

    log_file = tmp_path / "first.log"
    setup_logging(level="DEBUG", log_file=log_file)
    logger = logging.getLogger()  # root
    first_count = len(logger.handlers)

    # Call again with no file; handler count should change but not duplicate endlessly.
    setup_logging(level="ERROR", log_file=None)
    second_count = len(logger.handlers)

    assert second_count <= first_count + 1
    logging.shutdown()
