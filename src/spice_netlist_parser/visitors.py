"""Visitor pattern for AST traversal and transformation."""

from typing import Any, Dict, List
from abc import ABC, abstractmethod

from .ast_nodes import (
    ASTNode,
    NetlistNode,
    ComponentNode,
    ModelNode,
    DirectiveNode,
    ParameterNode,
    ValueNode,
)
from .models import Netlist, Component, ComponentType


class ASTVisitor(ABC):
    """Abstract base class for AST visitors."""
    
    def visit_netlist(self, node: NetlistNode) -> Any:
        """Visit NetlistNode.
        
        Args:
            node: NetlistNode to visit
        """
        pass
    
    def visit_component(self, node: ComponentNode) -> Any:
        """Visit ComponentNode.
        
        Args:
            node: ComponentNode to visit
        """
        pass
    
    def visit_model(self, node: ModelNode) -> Any:
        """Visit ModelNode.
        
        Args:
            node: ModelNode to visit
        """
        pass
    
    def visit_directive(self, node: DirectiveNode) -> Any:
        """Visit DirectiveNode.
        
        Args:
            node: DirectiveNode to visit
        """
        pass
    
    def visit_parameter(self, node: ParameterNode) -> Any:
        """Visit ParameterNode.
        
        Args:
            node: ParameterNode to visit
        """
        pass
    
    def visit_value(self, node: ValueNode) -> Any:
        """Visit ValueNode.
        
        Args:
            node: ValueNode to visit
        """
        pass
    
    def visit_default(self, node: ASTNode) -> Any:
        """Default visit method for unhandled node types.
        
        Args:
            node: ASTNode to visit
        """
        pass


class NetlistTransformer(ASTVisitor):
    """Transforms AST into domain models."""
    
    def __init__(self) -> None:
        """Initialize NetlistTransformer."""
        self.unit_multipliers: Dict[str, float] = {
            't': 1e12,
            'g': 1e9,
            'meg': 1e6,
            'k': 1e3,
            'm': 1e-3,
            'u': 1e-6,
            'n': 1e-9,
            'p': 1e-12,
            'f': 1e-15,
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
        components: List[Component] = []
        models: Dict[str, Dict[str, Any]] = {}
        options: Dict[str, Any] = {}
        includes: List[str] = []
        
        for stmt in node.statements:
            result = stmt.accept(self)
            if isinstance(result, Component):
                components.append(result)
            elif isinstance(result, dict):
                if 'model' in result:
                    models.update(result['model'])
                elif 'option' in result:
                    options.update(result['option'])
                elif 'include' in result:
                    includes.extend(result['include'])
        
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
        
        parameters: Dict[str, Any] = {}
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
    
    def visit_parameter(self, node: ParameterNode) -> Dict[str, Any]:
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
    
    def visit_model(self, node: ModelNode) -> Dict[str, Dict[str, Any]]:
        """Transform ModelNode to models dict.
        
        Args:
            node: ModelNode to transform
            
        Returns:
            Dictionary with model name as key
        """
        params: Dict[str, Any] = {}
        for param in node.parameters:
            param_result = param.accept(self)
            if isinstance(param_result, dict):
                params.update(param_result)
        
        return {
            'model': {
                node.name: {
                    'type': node.model_type,
                    'parameters': params,
                }
            }
        }
    
    def visit_directive(self, node: DirectiveNode) -> Dict[str, Any]:
        """Transform DirectiveNode to appropriate dict.
        
        Args:
            node: DirectiveNode to transform
            
        Returns:
            Dictionary with directive type as key
        """
        if node.directive_type == 'INCLUDE':
            return {'include': [node.content] if node.content else []}
        elif node.directive_type == 'OPTION':
            options: Dict[str, Any] = {}
            for param in node.parameters:
                param_result = param.accept(self)
                if isinstance(param_result, dict):
                    options.update(param_result)
            return {'option': options}
        elif node.directive_type == 'PARAM':
            # Handle .PARAM directive if needed
            params: Dict[str, Any] = {}
            for param in node.parameters:
                param_result = param.accept(self)
                if isinstance(param_result, dict):
                    params.update(param_result)
            return {'param': params}
        
        return {}
    
    def visit_default(self, node: ASTNode) -> Any:
        """Default visit method.
        
        Args:
            node: ASTNode to visit
            
        Returns:
            None for unhandled nodes
        """
        return None


