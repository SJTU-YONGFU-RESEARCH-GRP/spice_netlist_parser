"""CLI command error-path coverage."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from spice_netlist_parser.cli import commands

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_parse_command_exception(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """parse_command should log and return 1 on exceptions."""

    class _Parser:
        def parse_file(self, _path: Path) -> Any:  # pragma: no cover
            msg = "fail"
            raise RuntimeError(msg)

    f = tmp_path / "x.sp"
    f.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")
    monkeypatch.setattr(commands, "SpiceNetlistParser", _Parser)

    args = argparse.Namespace(
        file=f, format="text", output=None, ast=False, verbose=False
    )
    code = commands.parse_command(args)
    assert code == 1
    # Error logged; stdout/stderr may be empty due to logging config.


def test_compare_command_exception(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """compare_command should return 1 when compare_files fails."""

    left = tmp_path / "a.sp"
    right = tmp_path / "b.sp"
    left.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")
    right.write_text("R1 0 1 2k\n.END\n", encoding="utf-8")

    def _fail(*_a: object, **_kw: object) -> None:  # pragma: no cover
        msg = "cmp fail"
        raise RuntimeError(msg)

    monkeypatch.setattr(commands, "compare_files", _fail)
    args = argparse.Namespace(file1=left, file2=right, output=None, format="text")
    code = commands.compare_command(args)
    assert code == 1
    # Error logged; stdout/stderr may be empty due to logging config.


def test_roundtrip_command_exception(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """roundtrip_command should return 1 when validator fails."""

    f = tmp_path / "rt.sp"
    f.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")

    class _Validator:
        def assert_round_trip_string(self, _text: str) -> None:  # pragma: no cover
            msg = "rt fail"
            raise RuntimeError(msg)

    monkeypatch.setattr(commands, "RoundTripValidator", _Validator)
    args = argparse.Namespace(file=f, output=None)
    code = commands.roundtrip_command(args)
    assert code == 1
    # Error logged; stdout/stderr may be empty due to logging config.
