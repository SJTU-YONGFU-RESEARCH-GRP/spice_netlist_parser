"""Tests for AST visitor functionality."""

from __future__ import annotations

from spice_netlist_parser.ast_nodes import (
    ComponentNode,
    NetlistNode,
    NodeType,
    ParameterNode,
    ValueNode,
)
from spice_netlist_parser.models import ComponentType
from spice_netlist_parser.visitors import NetlistTransformer


class TestNetlistTransformer:
    """Test NetlistTransformer class."""

    def test_visit_component_valid_type(self) -> None:
        """Test transforming component with valid type."""
        transformer = NetlistTransformer()

        # Create a component node
        comp_node = ComponentNode(
            node_type=NodeType.COMPONENT,
            line_number=1,
            position=0,
            name="R1",
            component_type="R",
            nodes=["0", "1"],
            parameters=[],
            model=None,
        )

        component = transformer.visit_component(comp_node)
        assert component.name == "R1"
        assert component.component_type == ComponentType.RESISTOR
        assert component.nodes == ["0", "1"]

    def test_visit_component_invalid_type(self) -> None:
        """Test transforming component with invalid type defaults to resistor."""
        transformer = NetlistTransformer()

        # Create a component node with invalid type
        comp_node = ComponentNode(
            node_type=NodeType.COMPONENT,
            line_number=1,
            position=0,
            name="X1",
            component_type="INVALID",
            nodes=["0", "1"],
            parameters=[],
            model=None,
        )

        component = transformer.visit_component(comp_node)
        assert component.name == "X1"
        assert (
            component.component_type == ComponentType.RESISTOR
        )  # Defaults to resistor
        assert component.nodes == ["0", "1"]

    def test_visit_component_with_parameters(self) -> None:
        """Test transforming component with parameters."""
        transformer = NetlistTransformer()

        # Create parameter node
        value_node = ValueNode(
            node_type=NodeType.VALUE, line_number=1, position=5, value="1000"
        )
        param_node = ParameterNode(
            node_type=NodeType.PARAMETER,
            line_number=1,
            position=0,
            name="value",
            value=value_node,
        )

        # Create component node with parameter
        comp_node = ComponentNode(
            node_type=NodeType.COMPONENT,
            line_number=1,
            position=0,
            name="R1",
            component_type="R",
            nodes=["0", "1"],
            parameters=[param_node],
            model=None,
        )

        component = transformer.visit_component(comp_node)
        assert component.name == "R1"
        assert component.parameters == {"value": "1000"}

    def test_visit_parameter(self) -> None:
        """Test transforming parameter node."""
        transformer = NetlistTransformer()

        value_node = ValueNode(
            node_type=NodeType.VALUE, line_number=1, position=5, value="0.25u"
        )
        param_node = ParameterNode(
            node_type=NodeType.PARAMETER,
            line_number=1,
            position=0,
            name="L",
            value=value_node,
        )

        result = transformer.visit_parameter(param_node)
        assert result == {"l": "0.25u"}

    def test_visit_value(self) -> None:
        """Test transforming value node."""
        transformer = NetlistTransformer()

        value_node = ValueNode(
            node_type=NodeType.VALUE, line_number=1, position=0, value="3.3"
        )

        result = transformer.visit_value(value_node)
        assert result == "3.3"

    def test_visit_netlist(self) -> None:
        """Test transforming netlist node."""
        transformer = NetlistTransformer()

        # Create empty netlist node
        netlist_node = NetlistNode(
            node_type=NodeType.NETLIST,
            line_number=0,
            position=0,
            title="Test Circuit",
            statements=[],
        )

        netlist = transformer.visit_netlist(netlist_node)
        assert netlist.title == "Test Circuit"
        assert netlist.components == []
        assert netlist.models == {}
        assert netlist.options == {}
        assert netlist.includes == []

    def test_transform_method(self) -> None:
        """Test the transform method."""
        transformer = NetlistTransformer()

        netlist_node = NetlistNode(
            node_type=NodeType.NETLIST,
            line_number=0,
            position=0,
            title="Test Circuit",
            statements=[],
        )

        netlist = transformer.transform(netlist_node)
        assert netlist.title == "Test Circuit"
