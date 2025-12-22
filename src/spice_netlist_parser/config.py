"""Configuration management for SPICE netlist parser.

This module provides configuration management using environment variables
and default values for the application.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ParserConfig(BaseSettings):
    """Configuration for the SPICE netlist parser.

    All settings can be overridden using environment variables.
    """

    model_config = SettingsConfigDict(env_prefix="SPICE_PARSER_", case_sensitive=False)

    # Logging configuration
    log_level: str = Field(default="INFO")
    log_file: Path | None = Field(default=None)

    # Parser configuration
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    enable_caching: bool = Field(default=True)

    # Output configuration
    default_output_format: str = Field(default="text")
    output_encoding: str = Field(default="utf-8")


# Global configuration instance
config = ParserConfig()


def get_config() -> ParserConfig:
    """Get the current configuration instance.

    Returns:
        ParserConfig: Current configuration.
    """
    return config


def reload_config() -> None:
    """Reload configuration from environment variables.

    This is useful if environment variables have changed during runtime.
    """
    global config  # noqa: PLW0603
    config = ParserConfig()


# Convenience functions for common settings
def get_log_level() -> str:
    """Get the current log level."""
    return config.log_level


def get_log_file() -> Path | None:
    """Get the current log file path."""
    return config.log_file


def is_caching_enabled() -> bool:
    """Check if caching is enabled."""
    return config.enable_caching


def get_max_file_size() -> int:
    """Get the maximum allowed file size."""
    return config.max_file_size


def get_default_output_format() -> str:
    """Get the default output format."""
    return config.default_output_format
