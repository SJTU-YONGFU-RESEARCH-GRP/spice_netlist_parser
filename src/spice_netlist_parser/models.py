"""Domain models for SPICE netlist elements."""

from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum


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
    nodes: List[str]
    parameters: Dict[str, Union[float, str]]
    model: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate component data after initialization.
        
        Raises:
            ValueError: If component has insufficient nodes
        """
        if len(self.nodes) < 2:
            raise ValueError(
                f"Component {self.name} must have at least 2 nodes, "
                f"got {len(self.nodes)}"
            )


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
    components: List[Component]
    models: Dict[str, Dict[str, Any]]
    options: Dict[str, Any]
    includes: List[str]
    
    @property
    def nodes(self) -> List[str]:
        """Get all unique nodes in the netlist.
        
        Returns:
            Sorted list of unique node names
        """
        nodes = set()
        for comp in self.components:
            nodes.update(comp.nodes)
        return sorted(list(nodes))
    
    def get_components_by_type(self, comp_type: ComponentType) -> List[Component]:
        """Get all components of a specific type.
        
        Args:
            comp_type: The component type to filter by
            
        Returns:
            List of components matching the specified type
        """
        return [comp for comp in self.components if comp.component_type == comp_type]
    
    def get_component(self, name: str) -> Optional[Component]:
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


