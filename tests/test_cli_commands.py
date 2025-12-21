"""Tests for CLI command helpers."""

from __future__ import annotations

import argparse
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


from spice_netlist_parser.cli import commands

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


class _DummyNetlist:
    """Simple stand-in for a parsed netlist."""

    def __init__(self) -> None:
        self.title = "T"
        self.components: list[Any] = []
        self.models: dict[str, Any] = {}
        self.nodes: set[str] = set()
        self.includes: list[str] = []
        self.options: dict[str, Any] = {}


class _DummyCompareReport:
    """Simple compare report for mocking compare_files."""

    def __init__(self) -> None:
        self.text = "ok"

    def to_dict(self) -> dict[str, str]:
        """Return a dict form."""

        return {"status": "ok"}


def test_parse_command_success(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """parse_command should return 0 and emit formatted output."""

    netlist_path = tmp_path / "net.sp"
    netlist_path.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")

    dummy_netlist = _DummyNetlist()

    class _DummyParser:
        def parse_file(self, path: Path) -> _DummyNetlist:
            assert path == netlist_path
            return dummy_netlist

        def parse_file_to_ast(self, _path: Path) -> Any:
            return dummy_netlist

    monkeypatch.setattr(commands, "SpiceNetlistParser", _DummyParser)
    args = argparse.Namespace(
        file=netlist_path, format="text", output=None, ast=False, verbose=True
    )

    code = commands.parse_command(args)
    out = capsys.readouterr().out

    assert code == 0
    assert "Successfully parsed" in out


def test_parse_command_missing_file(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    """parse_command should fail with missing file."""

    missing = tmp_path / "missing.sp"
    args = argparse.Namespace(
        file=missing, format="text", output=None, ast=False, verbose=False
    )
    code = commands.parse_command(args)
    err = capsys.readouterr().err
    assert code == 1
    assert "File not found" in err


def test_compare_command_json_and_output(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """compare_command should write json report when requested."""

    left = tmp_path / "l.sp"
    right = tmp_path / "r.sp"
    left.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")
    right.write_text("R1 0 1 2k\n.END\n", encoding="utf-8")

    monkeypatch.setattr(
        commands, "compare_files", lambda *_args, **_kwargs: _DummyCompareReport()
    )
    monkeypatch.setattr(commands, "format_report_text", lambda _r: "text-report")

    out_file = tmp_path / "report.json"
    args = argparse.Namespace(file1=left, file2=right, output=out_file, format="json")
    code = commands.compare_command(args)

    assert code == 0
    assert json.loads(out_file.read_text(encoding="utf-8")) == {"status": "ok"}


def test_roundtrip_command_success(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """roundtrip_command should succeed and write normalized output when requested."""

    f = tmp_path / "rt.sp"
    f.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")

    class _DummyResult:
        def __init__(self) -> None:
            self.original = _DummyNetlist()
            self.reparsed = _DummyNetlist()
            self.serialized_spice = "R1 0 1 1k\n.END\n"

    class _DummyValidator:
        def assert_round_trip_string(self, text: str) -> _DummyResult:
            assert "R1" in text
            return _DummyResult()

    monkeypatch.setattr(commands, "RoundTripValidator", _DummyValidator)

    out_file = tmp_path / "norm.sp"
    args = argparse.Namespace(file=f, output=out_file)
    code = commands.roundtrip_command(args)
    stdout = capsys.readouterr().out

    assert code == 0
    assert "Round-trip validation successful" in stdout
    assert out_file.read_text(encoding="utf-8").strip() == "R1 0 1 1k\n.END"
