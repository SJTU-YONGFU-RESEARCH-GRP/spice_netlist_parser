"""Tests for parser error handling."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from spice_netlist_parser.parser import SpiceNetlistParser
from spice_netlist_parser.exceptions import ParseError


def test_parse_file_missing(tmp_path: Path) -> None:
    """parse_file should raise ParseError for missing files."""

    parser = SpiceNetlistParser()
    missing = tmp_path / "missing.sp"
    with pytest.raises(ParseError):
        parser.parse_file(missing)


def test_preprocess_file_handles_continuations() -> None:
    """_preprocess_file should join continuation lines correctly."""

    parser = SpiceNetlistParser()
    fake = io.StringIO("R1 0 1 1k\n+ 2k\n.END\n")
    processed = parser.ast_parser._preprocess_file(fake)  # type: ignore[arg-type]  # noqa: SLF001
    assert "1k 2k" in processed
