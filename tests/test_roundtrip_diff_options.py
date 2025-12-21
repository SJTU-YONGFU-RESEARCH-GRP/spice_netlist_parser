"""Additional roundtrip diff coverage for options/models/includes."""

from __future__ import annotations

from typing import Any

from spice_netlist_parser.models import Component, ComponentType, Netlist
from spice_netlist_parser.roundtrip import RoundTripValidator


def _netlist_with(extras: dict[str, Any]) -> Netlist:
    """Helper to build netlists with optional parts."""

    comp = Component("R1", ComponentType.RESISTOR, ["0", "1"], {"value": 1}, None)
    return Netlist(
        title="T",
        components=[comp],
        models=extras.get("models", {}),
        options=extras.get("options", {}),
        includes=extras.get("includes", []),
    )


def test_diff_options_models_includes() -> None:
    """diff should report differences for options/models/includes."""

    a = _netlist_with({
        "models": {"M1": {"type": "NMOS", "parameters": {"l": 1}}},
        "options": {"temp": 25},
        "includes": ["a.inc"],
    })
    b = _netlist_with({
        "models": {"M1": {"type": "NMOS", "parameters": {"l": 2}}},
        "options": {"temp": 50},
        "includes": ["b.inc"],
    })

    diffs = RoundTripValidator().diff(a, b)
    assert any("models" in d or "options" in d or "includes" in d for d in diffs)
