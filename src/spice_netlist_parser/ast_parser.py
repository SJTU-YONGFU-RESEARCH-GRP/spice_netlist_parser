"""AST-based SPICE netlist parser using Lark."""

from typing import List, Optional, TextIO, Union
from pathlib import Path
from io import StringIO
import lark
from lark import Lark, Tree, Token

from .grammar import SPICE_GRAMMAR
from .ast_nodes import (
    ASTNode,
    NetlistNode,
    ComponentNode,
    ModelNode,
    DirectiveNode,
    ParameterNode,
    ValueNode,
    NodeType,
)
from .exceptions import ParseError


class ASTBuilder:
    """Builds AST nodes from Lark parse trees."""
    
    def __init__(self) -> None:
        """Initialize AST builder."""
        self.line_number = 1
        self.current_component: Optional[ComponentNode] = None
        self.continuation_buffer: List[str] = []
    
    def build_netlist(self, tree: Tree) -> NetlistNode:
        """Build NetlistNode from parse tree.
        
        Args:
            tree: Root parse tree from Lark
            
        Returns:
            Root NetlistNode
        """
        title = ""
        statements: List[ASTNode] = []
        
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'title_line':
                    if child.children:
                        title = str(child.children[0]).strip()
                elif child.data == 'statement':
                    stmt = self.build_statement(child)
                    if stmt:
                        statements.append(stmt)
        
        return NetlistNode(
            node_type=NodeType.NETLIST,
            line_number=1,
            position=0,
            title=title or "Untitled",
            statements=statements,
        )
    
    def build_statement(self, tree: Tree) -> Optional[ASTNode]:
        """Build statement node from parse tree.
        
        Args:
            tree: Statement parse tree
            
        Returns:
            AST node or None if statement should be ignored
        """
        if not tree.children:
            return None
        
        child = tree.children[0]
        if isinstance(child, Tree):
            if child.data == 'component_line':
                return self.build_component(child)
            elif child.data == 'model_line':
                return self.build_model(child)
            elif child.data in ['include_line', 'option_line', 'param_line']:
                return self.build_directive(child)
        return None
    
    def build_component(self, tree: Tree) -> ComponentNode:
        """Build ComponentNode from component_line tree.
        
        Args:
            tree: Component line parse tree
            
        Returns:
            ComponentNode
        """
        # Unwrap `component_line` alternatives (e.g. `two_node_component`) so we
        # can treat all component variants uniformly.
        if tree.data == "component_line" and tree.children:
            first = tree.children[0]
            if isinstance(first, Tree):
                tree = first

        name = ""
        comp_type = ""
        nodes: List[str] = []
        parameters: List[ParameterNode] = []
        model: Optional[str] = None

        def collect_nodes(subtree: Tree) -> None:
            """Collect node tokens from any `node` subtrees."""

            nonlocal nodes
            for ch in subtree.children:
                if isinstance(ch, Tree):
                    if ch.data == "node":
                        for t in ch.children:
                            if isinstance(t, Token):
                                nodes.append(t.value)
                    else:
                        collect_nodes(ch)

        # We only treat tokens/trees as component-body content when we are inside
        # the component body region, so we don't accidentally treat node tokens
        # as values/parameters.
        BODY_TREES = {"component_body", "param_or_value", "parameter", "value"}

        def collect_body(subtree: Tree, *, in_body: bool) -> None:
            """Collect model and parameters from component body subtrees."""

            nonlocal model, parameters

            in_body = in_body or (subtree.data in BODY_TREES)

            for ch in subtree.children:
                if isinstance(ch, Tree):
                    if ch.data == "parameter":
                        param = self.build_parameter(ch)
                        if param:
                            parameters.append(param)
                        continue
                    if ch.data == "value":
                        value_node = self.build_value(ch)
                        parameters.append(
                            ParameterNode(
                                node_type=NodeType.PARAMETER,
                                line_number=self.line_number,
                                position=0,
                                name="value",
                                value=value_node,
                            )
                        )
                        continue
                    collect_body(ch, in_body=in_body)
                elif isinstance(ch, Token) and in_body:
                    if ch.type == "MODEL_NAME" and model is None:
                        model = ch.value
                    elif ch.type in {"SIGNED_NUMBER", "FUNCTION_CALL", "STRING"}:
                        value_node = self._build_value_from_token(ch)
                        if value_node:
                            parameters.append(
                                ParameterNode(
                                    node_type=NodeType.PARAMETER,
                                    line_number=self.line_number,
                                    position=0,
                                    name="value",
                                    value=value_node,
                                )
                            )
                    # Ignore other tokens outside known contexts.
                    continue

        for child in tree.children:
            if isinstance(child, Token):
                if child.type in {
                    "COMPONENT_NAME",
                    "RESISTOR_NAME",
                    "CAPACITOR_NAME",
                    "INDUCTOR_NAME",
                    "VOLTAGE_NAME",
                    "CURRENT_NAME",
                    "MOSFET_NAME",
                    "BJT_NAME",
                    "DIODE_NAME",
                    "SUBCKT_INST_NAME",
                    "SUBCKT_NAME",
                } or child.type.endswith("_NAME"):
                    name = child.value
                    comp_type = child.value[0].upper()
            elif isinstance(child, Tree):
                # Nodes can be under node2/node3/node4/node_list (all contain `node` subtrees).
                collect_nodes(child)
                # Body can be either a `component_body` subtree or raw (MODEL_NAME + param_or_value*)
                collect_body(child, in_body=False)
        
        return ComponentNode(
            node_type=NodeType.COMPONENT,
            line_number=self.line_number,
            position=0,
            name=name,
            component_type=comp_type,
            nodes=nodes,
            parameters=parameters,
            model=model,
        )
    
    def build_model(self, tree: Tree) -> ModelNode:
        """Build ModelNode from model_line tree.
        
        Args:
            tree: Model line parse tree
            
        Returns:
            ModelNode
        """
        name = ""
        model_type = ""
        parameters: List[ParameterNode] = []
        
        for child in tree.children:
            if isinstance(child, Token):
                if child.type == 'MODEL_NAME':
                    name = child.value
                elif child.type == 'MODEL_TYPE_NAME':
                    model_type = child.value
            elif isinstance(child, Tree):
                if child.data == 'model_type':
                    if child.children and isinstance(child.children[0], Token):
                        model_type = child.children[0].value
                elif child.data == 'model_params':
                    # Model params can be in parentheses or as parameter_list
                    for param_child in child.children:
                        if isinstance(param_child, Tree):
                            if param_child.data == 'parameter_list':
                                parameters.extend(self.extract_parameters(param_child))
                            elif param_child.data == 'parameter':
                                param = self.build_parameter(param_child)
                                if param:
                                    parameters.append(param)
        
        return ModelNode(
            node_type=NodeType.MODEL,
            line_number=self.line_number,
            position=0,
            name=name,
            model_type=model_type,
            parameters=parameters,
        )
    
    def build_directive(self, tree: Tree) -> DirectiveNode:
        """Build DirectiveNode from directive tree.
        
        Args:
            tree: Directive parse tree
            
        Returns:
            DirectiveNode
        """
        directive_type = tree.data.replace('_line', '').upper()
        parameters: List[ParameterNode] = []
        content: Optional[str] = None
        
        for child in tree.children:
            if isinstance(child, Token):
                if child.type == 'FILE_PATH':
                    content = child.value.strip('"')
            elif isinstance(child, Tree):
                if child.data == 'parameter_list':
                    parameters = self.extract_parameters(child)
        
        return DirectiveNode(
            node_type=NodeType.DIRECTIVE,
            line_number=self.line_number,
            position=0,
            directive_type=directive_type,
            parameters=parameters,
            content=content,
        )
    
    def extract_nodes(self, tree: Tree) -> List[str]:
        """Extract node names from node_list tree.
        
        Args:
            tree: Node list parse tree
            
        Returns:
            List of node names
        """
        nodes: List[str] = []
        for child in tree.children:
            if isinstance(child, Tree) and child.data == 'node':
                for node_child in child.children:
                    if isinstance(node_child, Token):
                        nodes.append(node_child.value)
        return nodes
    
    def extract_parameters(self, tree: Tree) -> List[ParameterNode]:
        """Extract parameters from parameter_list tree.
        
        Args:
            tree: Parameter list parse tree
            
        Returns:
            List of ParameterNode objects
        """
        parameters: List[ParameterNode] = []
        for child in tree.children:
            if isinstance(child, Tree) and child.data == 'parameter':
                param = self.build_parameter(child)
                if param:
                    parameters.append(param)
        return parameters
    
    def build_parameter(self, tree: Tree) -> Optional[ParameterNode]:
        """Build ParameterNode from parameter tree.
        
        Args:
            tree: Parameter parse tree
            
        Returns:
            ParameterNode or None if invalid
        """
        name = "value"  # Default for anonymous parameters
        value_node: Optional[ValueNode] = None
        
        for child in tree.children:
            if isinstance(child, Token) and child.type == 'PARAM_NAME':
                name = child.value
            elif isinstance(child, Tree) and child.data == 'value':
                value_node = self.build_value(child)
        
        if value_node:
            return ParameterNode(
                node_type=NodeType.PARAMETER,
                line_number=self.line_number,
                position=0,
                name=name,
                value=value_node,
            )
        return None
    
    def build_value(self, tree: Tree) -> ValueNode:
        """Build ValueNode from value tree.
        
        Args:
            tree: Value parse tree
            
        Returns:
            ValueNode
        """
        value: Union[float, str] = ""
        unit: Optional[str] = None
        
        for child in tree.children:
            if isinstance(child, Token):
                if child.type in ['NUMBER', 'SCIENTIFIC', 'SIGNED_NUMBER']:
                    try:
                        value = float(child.value)
                    except ValueError:
                        value = child.value
                elif child.type == 'STRING':
                    value = child.value.strip('"')
                elif child.type == 'FUNCTION_CALL':
                    value = child.value
                elif child.type == 'MODEL_NAME':
                    value = child.value
                elif child.type == 'unit':
                    unit = child.value
        
        # If value is still empty string, try to get from token
        if value == "" and tree.children:
            first_child = tree.children[0]
            if isinstance(first_child, Token):
                if first_child.type in ['NUMBER', 'SCIENTIFIC', 'SIGNED_NUMBER']:
                    try:
                        value = float(first_child.value)
                    except ValueError:
                        value = first_child.value
                elif first_child.type == 'FUNCTION_CALL':
                    value = first_child.value
                elif first_child.type == 'MODEL_NAME':
                    value = first_child.value
                else:
                    value = first_child.value
        
        return ValueNode(
            node_type=NodeType.VALUE,
            line_number=self.line_number,
            position=0,
            value=value,
            unit=unit,
        )
    
    def _build_value_from_token(self, token: Token) -> Optional[ValueNode]:
        """Build ValueNode directly from a token.
        
        Args:
            token: Token to convert to ValueNode
            
        Returns:
            ValueNode or None if token type not supported
        """
        value: Union[float, str] = ""
        unit: Optional[str] = None
        
        if token.type in ['NUMBER', 'SCIENTIFIC', 'SIGNED_NUMBER']:
            try:
                value = float(token.value)
            except ValueError:
                value = token.value
        elif token.type == 'FUNCTION_CALL':
            value = token.value
        elif token.type in ['STRING', 'MODEL_NAME']:
            value = token.value
        else:
            return None
        
        return ValueNode(
            node_type=NodeType.VALUE,
            line_number=self.line_number,
            position=0,
            value=value,
            unit=unit,
        )


class SpiceASTParser:
    """AST-based SPICE netlist parser using Lark."""
    
    def __init__(self) -> None:
        """Initialize SPICE AST parser."""
        try:
            self.parser = Lark(
                SPICE_GRAMMAR,
                parser='lalr',
                lexer='contextual',
                propagate_positions=True,
                maybe_placeholders=True,
            )
        except Exception as e:
            raise ParseError(f"Failed to initialize parser: {e}")
        
        self.builder = ASTBuilder()
        self.filename = ""
    
    def parse_file(self, filepath: Union[str, Path]) -> NetlistNode:
        """Parse a SPICE netlist file into an AST.
        
        Args:
            filepath: Path to the netlist file
            
        Returns:
            Root NetlistNode of the AST
            
        Raises:
            ParseError: If parsing fails
        """
        try:
            self.filename = str(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = self._preprocess_file(f)
                return self.parse_string(content)
        except FileNotFoundError:
            raise ParseError(f"File not found: {filepath}", filename=self.filename)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(
                f"Failed to parse file {filepath}: {e}",
                filename=self.filename,
            )
    
    def parse_string(self, netlist_text: str) -> NetlistNode:
        """Parse a SPICE netlist string into an AST.
        
        Args:
            netlist_text: The netlist content as a string
            
        Returns:
            Root NetlistNode of the AST
            
        Raises:
            ParseError: If parsing fails
        """
        try:
            # Preprocess to handle continuation lines
            processed_text = self._preprocess_text(netlist_text)
            
            tree = self.parser.parse(processed_text)
            return self.builder.build_netlist(tree)
            
        except lark.exceptions.UnexpectedToken as e:
            line_num = getattr(e, 'line', None) or self._find_error_line(
                netlist_text, str(e)
            )
            raise ParseError(
                f"Unexpected token at line {line_num}: {e}",
                filename=self.filename,
                line_number=line_num,
            )
        except lark.exceptions.UnexpectedCharacters as e:
            line_num = getattr(e, 'line', None) or self._find_error_line(
                netlist_text, str(e)
            )
            raise ParseError(
                f"Unexpected character at line {line_num}: {e}",
                filename=self.filename,
                line_number=line_num,
            )
        except lark.exceptions.LarkError as e:
            line_num = getattr(e, 'line', None) or self._find_error_line(
                netlist_text, str(e)
            )
            raise ParseError(
                f"Parse error at line {line_num}: {e}",
                filename=self.filename,
                line_number=line_num,
            )
        except Exception as e:
            raise ParseError(
                f"Unexpected error during parsing: {e}",
                filename=self.filename,
            )
    
    def _preprocess_file(self, file_handle: TextIO) -> str:
        """Preprocess file to handle continuation lines and filter comments.
        
        Args:
            file_handle: File handle to read from
            
        Returns:
            Preprocessed netlist text with comments removed and continuations merged
        """
        lines: List[str] = []
        current_line = ""
        
        for raw_line in file_handle:
            line = self._strip_inline_comment(raw_line.rstrip("\n\r")).rstrip()
            if not line:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                continue

            normalized = line.lstrip()

            # Skip comment lines (starting with *), allowing leading whitespace
            if normalized.startswith('*'):
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                continue

            # Handle continuation lines (starting with +), allowing leading whitespace
            if normalized.startswith('+'):
                continuation = normalized[1:].lstrip()
                if current_line:
                    current_line = f"{current_line} {continuation}"
                else:
                    current_line = continuation
                continue

            if current_line:
                lines.append(current_line)
            current_line = normalized
        
        if current_line:
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text to handle continuation lines and filter comments.
        
        Args:
            text: Raw netlist text
            
        Returns:
            Preprocessed netlist text with comments removed and continuations merged
        """
        lines: List[str] = []
        current_line = ""
        
        for line in text.split('\n'):
            cleaned_line = self._strip_inline_comment(line.rstrip()).rstrip()
            if not cleaned_line:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                continue

            normalized = cleaned_line.lstrip()

            # Skip comment lines (starting with *), allowing leading whitespace
            if normalized.startswith('*'):
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                continue
            
            # Handle continuation lines (starting with +), allowing leading whitespace
            if normalized.startswith('+'):
                continuation = normalized[1:].lstrip()
                if current_line:
                    current_line = f"{current_line} {continuation}"
                else:
                    current_line = continuation
                continue

            if current_line:
                lines.append(current_line)
            current_line = normalized
        
        if current_line:
            lines.append(current_line)
        
        return '\n'.join(lines)

    @staticmethod
    def _strip_inline_comment(line: str) -> str:
        """Remove inline comments marked by ';' while preserving strings.
        
        Args:
            line: Raw line text that may contain inline comments.
        
        Returns:
            Line content with inline comments removed.
        """
        in_string = False
        result_chars: List[str] = []

        for char in line:
            if char == '"':
                in_string = not in_string
            if char == ';' and not in_string:
                break
            result_chars.append(char)

        return "".join(result_chars)
    
    def _find_error_line(self, text: str, error_msg: str) -> int:
        """Attempt to find the line number where an error occurred.
        
        Args:
            text: Source text
            error_msg: Error message
            
        Returns:
            Estimated line number
        """
        # Try to extract line number from error message
        import re
        match = re.search(r'line\s+(\d+)', error_msg, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Fallback: return first line
        return 1

