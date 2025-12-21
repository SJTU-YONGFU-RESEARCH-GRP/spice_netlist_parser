"""Parser error-path coverage for parse_file and main guard."""

from __future__ import annotations

import runpy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from spice_netlist_parser import parser as parser_module
from spice_netlist_parser.exceptions import ParseError

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_parse_file_raises_parse_error(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """parse_file should wrap unexpected exceptions as ParseError."""

    bad = tmp_path / "bad.sp"
    bad.write_text("R1 0 1\n", encoding="utf-8")

    def _fail(*_a: object, **_kw: object) -> str:  # pragma: no cover
        msg = "oops"
        raise RuntimeError(msg)

    monkeypatch.setattr(parser_module.Path, "open", lambda *_a, **_k: (_fail()))

    parser = parser_module.SpiceNetlistParser()
    with pytest.raises(ParseError):
        parser.parse_file(bad)


def test_cli_main_guard_importable() -> None:
    """cli.__main__ should be runnable as a script."""

    mod = runpy.run_module("spice_netlist_parser.cli.__main__")
    assert mod["__name__"] in {"__main__", "spice_netlist_parser.cli.__main__"}
