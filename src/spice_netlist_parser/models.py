"""Domain models for SPICE netlist elements."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

# Constants
MIN_COMPONENT_NODES = 2


class ComponentType(Enum):
    """Enumeration of SPICE component types."""

    RESISTOR = "R"
    CAPACITOR = "C"
    INDUCTOR = "L"
    VOLTAGE_SOURCE = "V"
    CURRENT_SOURCE = "I"
    MOSFET = "M"
    BJT = "Q"
    DIODE = "D"
    SUBCIRCUIT = "X"


@dataclass
class Component:
    """Represents a circuit component.

    Attributes:
        name: Component name (e.g., "R1", "M2")
        component_type: Type of component (resistor, capacitor, etc.)
        nodes: List of node names this component connects to
        parameters: Dictionary of component parameters (values, model params, etc.)
        model: Optional model name for this component
    """

    name: str
    component_type: ComponentType
    nodes: list[str]
    parameters: dict[str, float | str]
    model: str | None = None

    def __post_init__(self) -> None:
        """Validate component data after initialization.

        Raises:
            ValueError: If component has insufficient nodes
        """
        # Allow components with 0 nodes for now (they will be filtered out later)
        if len(self.nodes) < MIN_COMPONENT_NODES and len(self.nodes) > 0:
            msg = f"Component {self.name} must have at least {MIN_COMPONENT_NODES} nodes, got {len(self.nodes)}"
            raise ValueError(msg)


@dataclass
class Netlist:
    """Represents a complete SPICE netlist.

    Attributes:
        title: Title of the netlist (first non-comment line)
        components: List of all components in the netlist
        models: Dictionary of model definitions (model name -> model parameters)
        options: Dictionary of .OPTION directive parameters
        includes: List of included file paths
    """

    title: str
    components: list[Component]
    models: dict[str, dict[str, Any]]
    options: dict[str, Any]
    includes: list[str]

    @property
    def nodes(self) -> list[str]:
        """Get all unique nodes in the netlist.

        Returns:
            Sorted list of unique node names
        """
        nodes = set()
        for comp in self.components:
            nodes.update(comp.nodes)
        return sorted(nodes)

    def get_components_by_type(self, comp_type: ComponentType) -> list[Component]:
        """Get all components of a specific type.

        Args:
            comp_type: The component type to filter by

        Returns:
            List of components matching the specified type
        """
        return [comp for comp in self.components if comp.component_type == comp_type]

    def get_component(self, name: str) -> Component | None:
        """Get a component by name.

        Args:
            name: Component name to search for

        Returns:
            Component if found, None otherwise
        """
        for comp in self.components:
            if comp.name == name:
                return comp
        return None
