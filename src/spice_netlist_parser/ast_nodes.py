"""AST node definitions for SPICE netlist elements."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class NodeType(Enum):
    """Types of AST nodes."""

    NETLIST = "netlist"
    COMPONENT = "component"
    MODEL = "model"
    DIRECTIVE = "directive"
    PARAMETER = "parameter"
    VALUE = "value"


@dataclass
class ASTNode:
    """Base AST node class.

    Attributes:
        node_type: Type of this AST node
        line_number: Line number in source file
        position: Character position in source file
    """

    node_type: NodeType
    line_number: int
    position: int

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for traversal.

        Args:
            visitor: Visitor object implementing visit methods

        Returns:
            Result of visitor's visit method
        """
        method_name = f"visit_{self.node_type.value}"
        visitor_method = getattr(visitor, method_name, None)
        if visitor_method:
            return visitor_method(self)
        return visitor.visit_default(self)


@dataclass
class ValueNode(ASTNode):
    """Represents a parameter value with optional unit.

    Attributes:
        value: Numeric or string value
        unit: Optional unit suffix (k, m, u, etc.)
    """

    value: float | str
    unit: str | None = None

    def __post_init__(self) -> None:
        """Set node type after initialization."""
        self.node_type = NodeType.VALUE


@dataclass
class ParameterNode(ASTNode):
    """Represents a parameter name-value pair.

    Attributes:
        name: Parameter name
        value: Value node for this parameter
    """

    name: str
    value: ValueNode

    def __post_init__(self) -> None:
        """Set node type after initialization."""
        self.node_type = NodeType.PARAMETER


@dataclass
class ComponentNode(ASTNode):
    """Represents a circuit component.

    Attributes:
        name: Component name (e.g., "R1", "M2")
        component_type: Component type character (R, C, M, etc.)
        nodes: List of node names this component connects to
        parameters: List of parameter nodes
        model: Optional model name for this component
    """

    name: str
    component_type: str
    nodes: list[str]
    parameters: list[ParameterNode]
    model: str | None = None

    def __post_init__(self) -> None:
        """Set node type after initialization."""
        self.node_type = NodeType.COMPONENT


@dataclass
class ModelNode(ASTNode):
    """Represents a .MODEL directive.

    Attributes:
        name: Model name
        model_type: Type of model (NMOS, PMOS, etc.)
        parameters: List of model parameter nodes
    """

    name: str
    model_type: str
    parameters: list[ParameterNode]

    def __post_init__(self) -> None:
        """Set node type after initialization."""
        self.node_type = NodeType.MODEL


@dataclass
class DirectiveNode(ASTNode):
    """Represents various SPICE directives.

    Attributes:
        directive_type: Type of directive (INCLUDE, OPTION, etc.)
        parameters: List of parameter nodes
        content: Optional string content (e.g., file path for INCLUDE)
    """

    directive_type: str
    parameters: list[ParameterNode]
    content: str | None = None

    def __post_init__(self) -> None:
        """Set node type after initialization."""
        self.node_type = NodeType.DIRECTIVE


@dataclass
class NetlistNode(ASTNode):
    """Root node representing the entire netlist.

    Attributes:
        title: Title of the netlist
        statements: List of all statement nodes
    """

    title: str
    statements: list[ASTNode]

    def __post_init__(self) -> None:
        """Set node type after initialization."""
        self.node_type = NodeType.NETLIST
