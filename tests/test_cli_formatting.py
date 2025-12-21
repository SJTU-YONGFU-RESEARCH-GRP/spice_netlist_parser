"""Formatting helpers coverage."""

from __future__ import annotations

from typing import Any

from spice_netlist_parser.cli import commands


class _Net:
    """Simple netlist stub."""

    def __init__(self) -> None:
        self.title = "T"
        self.components: list[Any] = []
        self.nodes: set[str] = set()
        self.models: dict[str, dict[str, Any]] = {
            "M1": {"type": "NMOS", "parameters": {"l": 1}}
        }
        self.includes: list[str] = ["inc1.sp"]
        self.options: dict[str, Any] = {"temp": 27}


def test_format_text_and_json() -> None:
    """format_text/json should include key sections."""

    net = _Net()
    txt = commands.format_text(net)
    js = commands.format_json(net)

    assert "Title" in txt
    assert "Components" in txt
    assert "Models" in txt
    assert "includes" in js
    assert "models" in js


def test_format_summary() -> None:
    """format_summary should produce compact summary lines."""

    net = _Net()
    summary = commands.format_summary(net)
    assert "Netlist:" in summary
    assert "Components" in summary
    assert "Nodes" in summary
