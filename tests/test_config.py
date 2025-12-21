"""Tests for configuration management."""

from __future__ import annotations

import os
from pathlib import Path

from spice_netlist_parser.config import ParserConfig, get_config


class TestParserConfig:
    """Test ParserConfig class."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = ParserConfig()
        assert config.log_level == "INFO"
        assert config.log_file is None
        assert config.max_file_size == 10 * 1024 * 1024  # 10MB
        assert config.enable_caching is True
        assert config.default_output_format == "text"

    def test_config_from_env(self) -> None:
        """Test configuration from environment variables."""
        # Set environment variables
        env_vars = {
            "SPICE_PARSER_LOG_LEVEL": "DEBUG",
            "SPICE_PARSER_LOG_FILE": "/tmp/test.log",
            "SPICE_PARSER_MAX_FILE_SIZE": "5000000",
            "SPICE_PARSER_ENABLE_CACHING": "False",
            "SPICE_PARSER_DEFAULT_OUTPUT_FORMAT": "json",
        }

        # Save original values
        original_env: dict[str, str | None] = {}
        for key in env_vars:
            original_env[key] = os.environ.get(key)

        try:
            # Set environment variables
            for key, value in env_vars.items():
                os.environ[key] = value

            # Create config (should pick up env vars)
            config = ParserConfig()

            assert config.log_level == "DEBUG"
            assert config.log_file == Path("/tmp/test.log")
            assert config.max_file_size == 5000000  # noqa: PLR2004
            assert config.enable_caching is False
            assert config.default_output_format == "json"

        finally:
            # Restore original environment
            for key, value in original_env.items():  # type: ignore[assignment]
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_config_case_insensitive(self) -> None:
        """Test that environment variables are case insensitive."""
        env_vars = {
            "spice_parser_log_level": "WARNING",
            "SPICE_PARSER_LOG_FILE": "/tmp/test2.log",
        }

        original_env: dict[str, str | None] = {}
        for key in env_vars:
            original_env[key] = os.environ.get(key)

        try:
            for key, value in env_vars.items():
                os.environ[key] = value

            config = ParserConfig()
            assert config.log_level == "WARNING"
            assert config.log_file == Path("/tmp/test2.log")

        finally:
            for key, value in original_env.items():  # type: ignore[assignment]
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


class TestGetConfig:
    """Test get_config function."""

    def test_get_config_returns_instance(self) -> None:
        """Test that get_config returns a ParserConfig instance."""
        config = get_config()
        assert isinstance(config, ParserConfig)

    def test_get_config_singleton(self) -> None:
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
