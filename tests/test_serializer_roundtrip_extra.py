"""Extra coverage for serializer and roundtrip utilities."""

from __future__ import annotations


import pytest

from spice_netlist_parser.roundtrip import RoundTripMismatchError, RoundTripValidator
from spice_netlist_parser.serializer import SpiceSerializer, SpiceSerializerOptions
from spice_netlist_parser.models import Component, ComponentType, Netlist


def _sample_netlist() -> Netlist:
    """Create a tiny netlist for serialization tests."""

    comp = Component(
        name="R1",
        component_type=ComponentType.RESISTOR,
        nodes=["0", "1"],
        parameters={"value": 1000},
        model=None,
    )
    return Netlist(
        title="* Title line",
        components=[comp],
        models={"MTEST": {"type": "NMOS", "parameters": {"l": 1e-6}}},
        options={"temp": 27},
        includes=["lib.sp"],
    )


def test_serializer_strips_title_star_and_quotes_in_includes() -> None:
    """Serializer should normalize title and quote includes with spaces."""

    netlist = _sample_netlist()
    netlist.includes.append("path with space.sp")
    serializer = SpiceSerializer(SpiceSerializerOptions())

    text = serializer.serialize(netlist)
    assert text.startswith("Title line")
    assert '".sp"' not in text  # ensure no double quotes
    assert 'INCLUDE "path with space.sp"' in text


def test_serializer_formats_values_and_models() -> None:
    """Serializer should render values and models predictably."""

    netlist = _sample_netlist()
    serializer = SpiceSerializer(SpiceSerializerOptions())
    text = serializer.serialize(netlist)

    assert ".MODEL MTEST NMOS (l=1e-06)" in text
    assert "R1 0 1 1000" in text
    assert ".OPTION temp=27" in text


def test_roundtrip_validator_diff_reports_mismatch() -> None:
    """RoundTripValidator.diff should highlight component differences."""

    comp_a = Component("R1", ComponentType.RESISTOR, ["0", "1"], {"value": 1}, None)
    comp_b = Component("R1", ComponentType.RESISTOR, ["0", "2"], {"value": 2}, None)

    net_a = Netlist(title="A", components=[comp_a], models={}, options={}, includes=[])
    net_b = Netlist(title="B", components=[comp_b], models={}, options={}, includes=[])

    validator = RoundTripValidator()
    diffs = validator.diff(net_a, net_b)
    assert any("nodes" in d for d in diffs)

    with pytest.raises(RoundTripMismatchError):
        validator.assert_equivalent(net_a, net_b)
