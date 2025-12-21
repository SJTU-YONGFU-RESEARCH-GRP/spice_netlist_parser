"""Roundtrip failure-path coverage."""

from __future__ import annotations

import pytest

from spice_netlist_parser.exceptions import ValidationError
from spice_netlist_parser.roundtrip import RoundTripMismatchError, RoundTripValidator
from spice_netlist_parser.models import Component, ComponentType, Netlist


def test_diff_reports_parameter_mismatch() -> None:
    """diff should detect parameter differences."""

    comp_a = Component("R1", ComponentType.RESISTOR, ["0", "1"], {"value": 1}, None)
    comp_b = Component("R1", ComponentType.RESISTOR, ["0", "1"], {"value": 2}, None)
    net_a = Netlist("A", [comp_a], {}, {}, [])
    net_b = Netlist("B", [comp_b], {}, {}, [])

    diffs = RoundTripValidator().diff(net_a, net_b)
    assert any("parameters" in d or "value" in d for d in diffs)


def test_assert_equivalent_raises_on_diff() -> None:
    """assert_equivalent should raise RoundTripMismatchError on diff."""

    comp_a = Component("R1", ComponentType.RESISTOR, ["0", "1"], {"value": 1}, None)
    comp_b = Component("R1", ComponentType.RESISTOR, ["0", "2"], {"value": 1}, None)
    net_a = Netlist("A", [comp_a], {}, {}, [])
    net_b = Netlist("B", [comp_b], {}, {}, [])

    with pytest.raises(RoundTripMismatchError):
        RoundTripValidator().assert_equivalent(net_a, net_b, float_tol=1e-12)


def test_round_trip_string_handles_validation_error() -> None:
    """round_trip_string should propagate validation errors cleanly."""

    class _BadValidator(RoundTripValidator):
        def assert_equivalent(self, *_args, **_kwargs) -> None:  # pragma: no cover
            msg = "oops"
            raise ValidationError(msg)

    bad = _BadValidator()
    with pytest.raises(ValidationError):
        bad.assert_equivalent(
            Netlist("A", [], {}, {}, []),
            Netlist("B", [], {}, {}, []),
        )
