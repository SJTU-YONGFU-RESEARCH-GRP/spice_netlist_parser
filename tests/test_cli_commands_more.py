"""Additional CLI command coverage."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


from spice_netlist_parser.cli import commands

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


class _DummyAST:
    """Tiny AST placeholder."""

    def __init__(self) -> None:
        self.node_type = type("T", (), {"value": "NETLIST"})
        self.title = "T"
        self.statements: list = []


class _DummyNetlist:
    """Netlist placeholder for formatting tests."""

    def __init__(self) -> None:
        self.title = "Title"
        self.components: list[Any] = []
        self.models: dict[str, Any] = {}
        self.nodes: set[str] = set()
        self.includes: list[str] = []
        self.options: dict[str, Any] = {}


def test_parse_command_ast_mode(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str], tmp_path: Path
) -> None:
    """parse_command should handle --ast and verbose output."""

    net = _DummyAST()

    class _Parser:
        def parse_file_to_ast(self, _path: Path) -> _DummyAST:
            return net

    netlist_path = tmp_path / "x.sp"
    netlist_path.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")

    monkeypatch.setattr(commands, "SpiceNetlistParser", _Parser)

    args = argparse.Namespace(
        file=netlist_path, format="text", output=None, ast=True, verbose=True
    )
    code = commands.parse_command(args)
    out = capsys.readouterr().out

    assert code == 0
    assert "AST Root" in out
    assert "Statements" in out


def test_parse_command_format_summary(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str], tmp_path: Path
) -> None:
    """parse_command should format summary output."""

    net = _DummyNetlist()
    net.components = []
    net.nodes = set()
    net.models = {}
    net.includes = []

    class _Parser:
        def parse_file(self, _path: Path) -> _DummyNetlist:
            return net

    monkeypatch.setattr(commands, "SpiceNetlistParser", _Parser)

    args = argparse.Namespace(
        file=tmp_path / "x.sp", format="summary", output=None, ast=False, verbose=False
    )
    args.file.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")
    code = commands.parse_command(args)
    out = capsys.readouterr().out
    assert code == 0
    assert "Netlist:" in out


def test_compare_command_text(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str], tmp_path: Path
) -> None:
    """compare_command should print text report when no output is provided."""

    left = tmp_path / "a.sp"
    right = tmp_path / "b.sp"
    left.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")
    right.write_text("R1 0 1 2k\n.END\n", encoding="utf-8")

    monkeypatch.setattr(
        commands,
        "compare_files",
        lambda *_args, **_kwargs: type(
            "R", (), {"to_dict": lambda _self: {}, "text": "ok"}
        )(),
    )
    monkeypatch.setattr(commands, "format_report_text", lambda _r: "text-report")

    args = argparse.Namespace(file1=left, file2=right, output=None, format="text")
    code = commands.compare_command(args)
    out = capsys.readouterr().out
    assert code == 0
    assert "text-report" in out


def test_roundtrip_command_failure(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str], tmp_path: Path
) -> None:
    """roundtrip_command should log and return 1 on error."""

    f = tmp_path / "rt.sp"
    f.write_text("bad\n", encoding="utf-8")

    class _DummyValidator:
        def assert_round_trip_string(self, _text: str) -> None:  # pragma: no cover
            msg = "fail"
            raise RuntimeError(msg)

    monkeypatch.setattr(commands, "RoundTripValidator", _DummyValidator)

    args = argparse.Namespace(file=f, output=None)
    code = commands.roundtrip_command(args)
    err = capsys.readouterr().out
    assert code == 1 or "failed" in err
