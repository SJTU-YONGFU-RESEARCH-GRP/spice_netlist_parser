"""Tests covering main.py error branches."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING


from spice_netlist_parser import main as cli_main

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def _call_main(argv: list[str], monkeypatch: MonkeyPatch) -> int:
    """Invoke main with custom argv."""

    monkeypatch.setattr(sys, "argv", argv)
    return cli_main.main()


def test_main_file_not_found(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """FileNotFoundError should be handled."""

    def fake_parse(_args: object) -> int:  # pragma: no cover
        msg = "missing"
        raise FileNotFoundError(msg)

    monkeypatch.setattr(cli_main, "parse_command", fake_parse)
    code = _call_main(["spice-parser", "parse", "no.sp"], monkeypatch)
    err = capsys.readouterr().err
    assert code == 1
    assert "File not found" in err


def test_main_unexpected_error_verbose(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Unexpected error path with verbose flag."""

    def fake_parse(_args: object) -> int:  # pragma: no cover
        msg = "boom"
        raise RuntimeError(msg)

    monkeypatch.setattr(cli_main, "parse_command", fake_parse)
    code = _call_main(["spice-parser", "parse", "x.sp", "--verbose"], monkeypatch)
    err = capsys.readouterr().err
    assert code == 1
    assert "Unexpected Error" in err
