"""Tests for round-trip validation functionality."""

from __future__ import annotations

import pytest

from spice_netlist_parser.models import Component, ComponentType, Netlist
from spice_netlist_parser.roundtrip import RoundTripResult, RoundTripValidator


class TestRoundTripValidator:
    """Test RoundTripValidator class."""

    def test_round_trip_string_simple(self) -> None:
        """Test basic round-trip functionality."""
        validator = RoundTripValidator()

        spice_text = "R1 0 1 1000\n.END\n"
        result = validator.round_trip_string(spice_text)

        assert isinstance(result, RoundTripResult)
        assert result.original.title == "Untitled"
        assert len(result.original.components) == 1
        assert result.reparsed.title == "Untitled"
        assert len(result.reparsed.components) == 1

    def test_assert_round_trip_string_success(self) -> None:
        """Test successful round-trip assertion."""
        validator = RoundTripValidator()

        spice_text = "R1 0 1 1000\n.END\n"
        result = validator.assert_round_trip_string(spice_text)

        assert isinstance(result, RoundTripResult)
        assert result.original.title == "Untitled"

    def test_assert_equivalent_success(self) -> None:
        """Test successful equivalence assertion."""
        validator = RoundTripValidator()

        comp = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        netlist1 = Netlist(
            title="Test", components=[comp], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Test", components=[comp], includes=[], options={}, models={}
        )

        # Should not raise
        validator.assert_equivalent(netlist1, netlist2)

    def test_assert_equivalent_with_serialized_spice(self) -> None:
        """Test equivalence assertion with serialized spice (for error message)."""
        validator = RoundTripValidator()

        comp1 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        comp2 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 2000.0},  # Different value
        )
        netlist1 = Netlist(
            title="Test", components=[comp1], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Test", components=[comp2], includes=[], options={}, models={}
        )

        serialized_spice = "Test Circuit\nR1 0 1 1000\n.END\n"

        with pytest.raises(AssertionError) as exc_info:
            validator.assert_equivalent(
                netlist1, netlist2, serialized_spice=serialized_spice
            )

        error_msg = str(exc_info.value)
        assert "Round-trip mismatch detected:" in error_msg
        assert "Serialized SPICE (for repro):" in error_msg
        assert serialized_spice in error_msg

    def test_diff_identical_netlists(self) -> None:
        """Test diffing identical netlists."""
        validator = RoundTripValidator()

        comp = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        netlist = Netlist(
            title="Test", components=[comp], includes=[], options={}, models={}
        )

        diffs = validator.diff(netlist, netlist)
        assert diffs == []

    def test_diff_different_titles(self) -> None:
        """Test diffing netlists with different titles."""
        validator = RoundTripValidator()

        netlist1 = Netlist(
            title="Circuit 1", components=[], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Circuit 2", components=[], includes=[], options={}, models={}
        )

        diffs = validator.diff(netlist1, netlist2)
        assert len(diffs) == 1
        assert "title:" in diffs[0]

    def test_diff_different_components(self) -> None:
        """Test diffing netlists with different components."""
        validator = RoundTripValidator()

        comp1 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        comp2 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 2000.0},
        )
        netlist1 = Netlist(
            title="Test", components=[comp1], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Test", components=[comp2], includes=[], options={}, models={}
        )

        diffs = validator.diff(netlist1, netlist2)
        assert len(diffs) == 1
        assert "parameters:" in diffs[0]

    def test_diff_missing_components(self) -> None:
        """Test diffing netlists with missing components."""
        validator = RoundTripValidator()

        comp = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        netlist1 = Netlist(
            title="Test", components=[comp], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Test", components=[], includes=[], options={}, models={}
        )

        diffs = validator.diff(netlist1, netlist2)
        assert len(diffs) == 1
        assert "components missing" in diffs[0]

    def test_diff_extra_components(self) -> None:
        """Test diffing netlists with extra components."""
        validator = RoundTripValidator()

        comp = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        netlist1 = Netlist(
            title="Test", components=[], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Test", components=[comp], includes=[], options={}, models={}
        )

        diffs = validator.diff(netlist1, netlist2)
        assert len(diffs) == 1
        assert "components added" in diffs[0]

    def test_diff_with_float_tolerance(self) -> None:
        """Test diffing with custom float tolerance."""
        validator = RoundTripValidator()

        comp1 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1.0000000001},
        )
        comp2 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1.0000000002},
        )
        netlist1 = Netlist(
            title="Test", components=[comp1], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Test", components=[comp2], includes=[], options={}, models={}
        )

        # With default tolerance, should detect difference
        diffs = validator.diff(netlist1, netlist2)
        assert len(diffs) == 1

        # With larger tolerance, should not detect difference
        diffs = validator.diff(netlist1, netlist2, float_tol=1e-9)
        assert diffs == []
