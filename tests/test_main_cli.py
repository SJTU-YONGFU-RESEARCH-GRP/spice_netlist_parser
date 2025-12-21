"""Tests for CLI entrypoint `main`."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING


from spice_netlist_parser import main as cli_main
from spice_netlist_parser.exceptions import ParseError, ValidationError

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def _invoke_main(argv: list[str], monkeypatch: MonkeyPatch) -> int:
    """Helper to invoke cli_main.main with patched argv."""

    monkeypatch.setattr(sys, "argv", argv)
    return cli_main.main()


def test_main_dispatch_parse(monkeypatch: MonkeyPatch) -> None:
    """main should dispatch to parse_command and return its code."""

    calls: list[str] = []

    def fake_parse(_args: object) -> int:
        calls.append("parse")
        return 0

    monkeypatch.setattr(cli_main, "parse_command", fake_parse)
    code = _invoke_main(["spice-parser", "parse", "dummy.sp"], monkeypatch)
    assert code == 0
    assert calls == ["parse"]


def test_main_dispatch_compare(monkeypatch: MonkeyPatch) -> None:
    """main should dispatch to compare_command."""

    calls: list[str] = []

    def fake_compare(_args: object) -> int:
        calls.append("compare")
        return 0

    monkeypatch.setattr(cli_main, "compare_command", fake_compare)
    code = _invoke_main(["spice-parser", "compare", "a.sp", "b.sp"], monkeypatch)
    assert code == 0
    assert calls == ["compare"]


def test_main_dispatch_roundtrip(monkeypatch: MonkeyPatch) -> None:
    """main should dispatch to roundtrip_command."""

    calls: list[str] = []

    def fake_rt(_args: object) -> int:
        calls.append("roundtrip")
        return 0

    monkeypatch.setattr(cli_main, "roundtrip_command", fake_rt)
    code = _invoke_main(["spice-parser", "roundtrip", "c.sp"], monkeypatch)
    assert code == 0
    assert calls == ["roundtrip"]


def test_main_parse_error(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """ParseError should be caught and return 1."""

    def fake_parse(_args: object) -> int:
        msg = "bad"
        raise ParseError(msg, filename="x", line_number=1)

    monkeypatch.setattr(cli_main, "parse_command", fake_parse)
    code = _invoke_main(["spice-parser", "parse", "file.sp"], monkeypatch)
    stderr = capsys.readouterr().err
    assert code == 1
    assert "Parse Error" in stderr


def test_main_validation_error(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """ValidationError should be caught and return 1."""

    def fake_parse(_args: object) -> int:
        msg = "oops"
        raise ValidationError(msg)

    monkeypatch.setattr(cli_main, "parse_command", fake_parse)
    code = _invoke_main(["spice-parser", "parse", "file.sp"], monkeypatch)
    stderr = capsys.readouterr().err
    assert code == 1
    assert "Validation Error" in stderr


def test_main_unexpected_error(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Unexpected errors should return 1 and print a message."""

    def fake_parse(_args: object) -> int:
        msg = "boom"
        raise RuntimeError(msg)

    monkeypatch.setattr(cli_main, "parse_command", fake_parse)
    code = _invoke_main(["spice-parser", "parse", "file.sp"], monkeypatch)
    stderr = capsys.readouterr().err
    assert code == 1
    assert "Unexpected Error" in stderr
