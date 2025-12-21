"""Tests for domain models."""

from __future__ import annotations

import pytest

from spice_netlist_parser.models import Component, ComponentType, Netlist


class TestComponent:
    """Test Component class."""

    def test_component_creation_valid(self) -> None:
        """Test creating a valid component."""
        comp = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        assert comp.name == "R1"
        assert comp.component_type == ComponentType.RESISTOR
        assert comp.nodes == ["0", "1"]
        assert comp.parameters == {"value": 1000.0}
        assert comp.model is None

    def test_component_with_model(self) -> None:
        """Test component with model."""
        comp = Component(
            name="M1",
            component_type=ComponentType.MOSFET,
            nodes=["1", "2", "3", "4"],
            parameters={"L": 0.25, "W": 50.8},
            model="NMOS",
        )
        assert comp.model == "NMOS"

    def test_component_insufficient_nodes(self) -> None:
        """Test that component with insufficient nodes raises ValueError."""
        with pytest.raises(ValueError, match="must have at least 2 nodes"):
            Component(
                name="R1",
                component_type=ComponentType.RESISTOR,
                nodes=["0"],  # Only 1 node
                parameters={"value": 1000.0},
            )

    def test_component_minimum_nodes(self) -> None:
        """Test component with minimum required nodes."""
        comp = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        assert len(comp.nodes) == 2  # noqa: PLR2004


class TestNetlist:
    """Test Netlist class."""

    def test_netlist_creation(self) -> None:
        """Test creating a netlist."""
        netlist = Netlist(
            title="Test Circuit", components=[], includes=[], options={}, models={}
        )
        assert netlist.title == "Test Circuit"
        assert netlist.components == []
        assert netlist.nodes == []

    def test_netlist_with_components(self) -> None:
        """Test netlist with components."""
        comp1 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        comp2 = Component(
            name="C1",
            component_type=ComponentType.CAPACITOR,
            nodes=["1", "2"],
            parameters={"value": 1e-6},
        )
        netlist = Netlist(
            title="Test Circuit",
            components=[comp1, comp2],
            includes=[],
            options={},
            models={},
        )
        assert len(netlist.components) == 2  # noqa: PLR2004
        assert netlist.nodes == ["0", "1", "2"]

    def test_get_components_by_type(self) -> None:
        """Test filtering components by type."""
        comp1 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        comp2 = Component(
            name="C1",
            component_type=ComponentType.CAPACITOR,
            nodes=["1", "2"],
            parameters={"value": 1e-6},
        )
        comp3 = Component(
            name="R2",
            component_type=ComponentType.RESISTOR,
            nodes=["2", "3"],
            parameters={"value": 2000.0},
        )
        netlist = Netlist(
            title="Test Circuit",
            components=[comp1, comp2, comp3],
            includes=[],
            options={},
            models={},
        )

        resistors = netlist.get_components_by_type(ComponentType.RESISTOR)
        assert len(resistors) == 2  # noqa: PLR2004
        assert resistors[0].name == "R1"
        assert resistors[1].name == "R2"

        capacitors = netlist.get_components_by_type(ComponentType.CAPACITOR)
        assert len(capacitors) == 1
        assert capacitors[0].name == "C1"

    def test_get_component_by_name(self) -> None:
        """Test getting component by name."""
        comp1 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        comp2 = Component(
            name="C1",
            component_type=ComponentType.CAPACITOR,
            nodes=["1", "2"],
            parameters={"value": 1e-6},
        )
        netlist = Netlist(
            title="Test Circuit",
            components=[comp1, comp2],
            includes=[],
            options={},
            models={},
        )

        found = netlist.get_component("R1")
        assert found is not None
        assert found.name == "R1"

        not_found = netlist.get_component("R3")
        assert not_found is None

    def test_netlist_empty_nodes(self) -> None:
        """Test nodes property with empty component list."""
        netlist = Netlist(
            title="Empty Circuit", components=[], includes=[], options={}, models={}
        )
        assert netlist.nodes == []
