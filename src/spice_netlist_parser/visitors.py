"""Visitor pattern for AST traversal and transformation."""

from abc import ABC
from typing import Any

from .ast_nodes import (
    ASTNode,
    ComponentNode,
    DirectiveNode,
    ModelNode,
    NetlistNode,
    ParameterNode,
    ValueNode,
)
from .models import Component, ComponentType, Netlist


class ASTVisitor(ABC):  # noqa: B024
    """Abstract base class for AST visitors."""

    def visit_netlist(self, node: NetlistNode) -> Any:  # noqa: B027
        """Visit NetlistNode.

        Args:
            node: NetlistNode to visit
        """

    def visit_component(self, node: ComponentNode) -> Any:  # noqa: B027
        """Visit ComponentNode.

        Args:
            node: ComponentNode to visit
        """

    def visit_model(self, node: ModelNode) -> Any:  # noqa: B027
        """Visit ModelNode.

        Args:
            node: ModelNode to visit
        """

    def visit_directive(self, node: DirectiveNode) -> Any:  # noqa: B027
        """Visit DirectiveNode.

        Args:
            node: DirectiveNode to visit
        """

    def visit_parameter(self, node: ParameterNode) -> Any:  # noqa: B027
        """Visit ParameterNode.

        Args:
            node: ParameterNode to visit
        """

    def visit_value(self, node: ValueNode) -> Any:  # noqa: B027
        """Visit ValueNode.

        Args:
            node: ValueNode to visit
        """

    def visit_default(self, node: ASTNode) -> Any:  # noqa: B027
        """Default visit method for unhandled node types.

        Args:
            node: ASTNode to visit
        """


class NetlistTransformer(ASTVisitor):
    """Transforms AST into domain models."""

    def __init__(self) -> None:
        """Initialize NetlistTransformer."""
        self.unit_multipliers: dict[str, float] = {
            "t": 1e12,
            "g": 1e9,
            "meg": 1e6,
            "k": 1e3,
            "m": 1e-3,
            "u": 1e-6,
            "n": 1e-9,
            "p": 1e-12,
            "f": 1e-15,
        }

    def transform(self, ast: NetlistNode) -> Netlist:
        """Transform AST to Netlist model.

        Args:
            ast: Root AST node

        Returns:
            Netlist domain model
        """
        return self.visit_netlist(ast)

    def visit_netlist(self, node: NetlistNode) -> Netlist:
        """Transform NetlistNode to Netlist.

        Args:
            node: NetlistNode to transform

        Returns:
            Netlist domain model
        """
        components: list[Component] = []
        models: dict[str, dict[str, Any]] = {}
        options: dict[str, Any] = {}
        includes: list[str] = []

        for stmt in node.statements:
            result = stmt.accept(self)
            if isinstance(result, Component):
                # Filter out invalid components with less than 2 nodes
                if len(result.nodes) >= 2:
                    components.append(result)
            elif isinstance(result, dict):
                if "model" in result:
                    models.update(result["model"])
                elif "option" in result:
                    options.update(result["option"])
                elif "include" in result:
                    includes.extend(result["include"])

        return Netlist(
            title=node.title,
            components=components,
            models=models,
            options=options,
            includes=includes,
        )

    def visit_component(self, node: ComponentNode) -> Component:
        """Transform ComponentNode to Component.

        Args:
            node: ComponentNode to transform

        Returns:
            Component domain model
        """
        try:
            comp_type = ComponentType(node.component_type)
        except ValueError:
            # Default to resistor if type not recognized
            comp_type = ComponentType.RESISTOR

        parameters: dict[str, Any] = {}
        for param in node.parameters:
            param_result = param.accept(self)
            if isinstance(param_result, dict):
                parameters.update(param_result)

        return Component(
            name=node.name,
            component_type=comp_type,
            nodes=node.nodes,
            parameters=parameters,
            model=node.model,
        )

    def visit_parameter(self, node: ParameterNode) -> dict[str, Any]:
        """Transform ParameterNode to dict.

        Args:
            node: ParameterNode to transform

        Returns:
            Dictionary with parameter name as key
        """
        value = node.value.accept(self)
        return {node.name.lower(): value}

    def visit_value(self, node: ValueNode) -> Any:
        """Transform ValueNode to appropriate Python type.

        Args:
            node: ValueNode to transform

        Returns:
            Converted value (float with unit applied, or string)
        """
        value = node.value

        if isinstance(value, str):
            return value

        # Apply unit multiplier if unit is specified
        if node.unit:
            multiplier = self.unit_multipliers.get(node.unit.lower(), 1.0)
            return value * multiplier

        return value

    def visit_model(self, node: ModelNode) -> dict[str, dict[str, Any]]:
        """Transform ModelNode to models dict.

        Args:
            node: ModelNode to transform

        Returns:
            Dictionary with model name as key
        """
        params: dict[str, Any] = {}
        for param in node.parameters:
            param_result = param.accept(self)
            if isinstance(param_result, dict):
                params.update(param_result)

        return {
            "model": {
                node.name: {
                    "type": node.model_type,
                    "parameters": params,
                }
            }
        }

    def visit_directive(self, node: DirectiveNode) -> dict[str, Any]:
        """Transform DirectiveNode to appropriate dict.

        Args:
            node: DirectiveNode to transform

        Returns:
            Dictionary with directive type as key
        """
        if node.directive_type == "INCLUDE":
            return {"include": [node.content] if node.content else []}

        if node.directive_type == "OPTION":
            options: dict[str, Any] = {}
            for param in node.parameters:
                param_result = param.accept(self)
                if isinstance(param_result, dict):
                    options.update(param_result)
            return {"option": options}

        if node.directive_type == "PARAM":
            # Handle .PARAM directive if needed
            params: dict[str, Any] = {}
            for param in node.parameters:
                param_result = param.accept(self)
                if isinstance(param_result, dict):
                    params.update(param_result)
            return {"param": params}

        return {}

    def visit_default(self, node: ASTNode) -> Any:  # noqa: ARG002
        """Default visit method.

        Args:
            node: ASTNode to visit

        Returns:
            None for unhandled nodes
        """
        return None
