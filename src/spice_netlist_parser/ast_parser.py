"""AST-based SPICE netlist parser using Lark."""

import re
from pathlib import Path
from typing import TextIO

import lark
from lark import Lark, Token, Tree

from .ast_nodes import (
    ASTNode,
    ComponentNode,
    DirectiveNode,
    ModelNode,
    NetlistNode,
    NodeType,
    ParameterNode,
    ValueNode,
)
from .exceptions import ParseError
from .grammar import SPICE_GRAMMAR
from .logging_config import get_logger


class ASTBuilder:
    """Builds AST nodes from Lark parse trees."""

    def __init__(self) -> None:
        """Initialize AST builder."""
        self.line_number = 1
        self.current_component: ComponentNode | None = None
        self.continuation_buffer: list[str] = []

    def build_netlist(self, tree: Tree) -> NetlistNode:
        """Build NetlistNode from parse tree.

        Args:
            tree: Root parse tree from Lark

        Returns:
            Root NetlistNode
        """
        title = ""
        statements: list[ASTNode] = []

        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == "title_line":
                    if child.children:
                        title = str(child.children[0]).strip()
                elif child.data == "statement":
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

    def build_statement(self, tree: Tree) -> ASTNode | None:
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
            if child.data == "component_line":
                return self.build_component(child)
            if child.data == "model_line":
                return self.build_model(child)
            if child.data in ["include_line", "option_line", "param_line"]:
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
        nodes: list[str] = []
        parameters: list[ParameterNode] = []
        model: str | None = None

        def collect_nodes(subtree: Tree) -> None:
            """Collect node tokens from any `node` subtrees."""

            nonlocal nodes
            if subtree.data == "param_or_value":
                return
            for ch in subtree.children:
                if isinstance(ch, Token):
                    nodes.append(ch.value)
                elif isinstance(ch, Tree):
                    if ch.data == "node":
                        nodes.extend(
                            t.value for t in ch.children if isinstance(t, Token)
                        )
                    else:
                        collect_nodes(ch)

        # We only treat tokens/trees as component-body content when we are inside
        # the component body region, so we don't accidentally treat node tokens
        # as values/parameters.
        body_trees = {"component_body", "param_or_value", "parameter", "value"}

        def collect_body(subtree: Tree, *, in_body: bool) -> None:
            """Collect model and parameters from component body subtrees."""

            nonlocal model, parameters

            in_body = in_body or (subtree.data in body_trees)

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
                    if ch.type in {"MODEL_NAME", "SUBCKT_NAME"} and model is None:
                        # For subcircuit instances, SUBCKT_NAME is the model
                        model = ch.value
                    elif ch.type in {"SIGNED_NUMBER", "FUNCTION_CALL", "STRING"}:
                        value_node = self._build_value_from_token(ch)  # type: ignore[assignment]
                        if value_node is not None:
                            # Type narrowing for MyPy - we know value_node is not None here
                            parameters.append(
                                ParameterNode(
                                    node_type=NodeType.PARAMETER,
                                    line_number=self.line_number,
                                    position=0,
                                    name="value",
                                    value=value_node,  # type: ignore[assignment,arg-type]
                                )
                            )
                    # Ignore other tokens outside known contexts.
                    continue

        for child in tree.children:
            if isinstance(child, Token):
                if child.type == "SUBCKT_INST_NAME":
                    # For subcircuit instances, use the instance name (e.g., XI0) as component name
                    name = child.value
                    comp_type = child.value[0].upper()
                elif child.type in {
                    "COMPONENT_NAME",
                    "RESISTOR_NAME",
                    "CAPACITOR_NAME",
                    "INDUCTOR_NAME",
                    "VOLTAGE_NAME",
                    "CURRENT_NAME",
                    "MOSFET_NAME",
                    "BJT_NAME",
                    "DIODE_NAME",
                } or child.type.endswith("_NAME"):
                    # Only set name/type if not already set (to avoid overwriting SUBCKT_INST_NAME)
                    if not name:
                        name = child.value
                        comp_type = child.value[0].upper()
            elif isinstance(child, Tree):
                # Nodes can be under node2/node3/node4/node_list (all contain `node` subtrees).
                collect_nodes(child)
                # Body can be either a `component_body` subtree or raw (MODEL_NAME + param_or_value*)
                collect_body(child, in_body=False)

        # Post-processing: Check if an X component is actually a MOSFET
        # This handles cases where preprocessing converted X_ to M_ but grammar still matched as subcircuit
        # or cases where X_ components with MOSFET characteristics weren't converted during preprocessing
        if comp_type == "X" and len(nodes) >= 4:
            # Check if it has MOSFET characteristics: PMOS/NMOS model or W=/L= parameters
            has_mos_model = model and model.upper() in ("PMOS", "NMOS")
            
            # Check parameters for W=/L= (handles both ParameterNode and PARAM_ASSIGN tokens)
            has_mos_params = False
            for param in parameters:
                param_name_upper = param.name.upper()
                param_value_str = str(param.value).upper()
                if param_name_upper in ("W", "L") or "W=" in param_value_str or "L=" in param_value_str:
                    has_mos_params = True
                    break
            
            # Also check if any child tokens are PARAM_ASSIGN with W=/L=
            # This catches cases where PARAM_ASSIGN tokens weren't converted to ParameterNode
            # Recursively search the tree for PARAM_ASSIGN tokens
            if not has_mos_params:
                def check_tree_for_mos_params(subtree: Tree) -> bool:
                    """Recursively check tree for MOSFET parameters."""
                    for ch in subtree.children:
                        if isinstance(ch, Token):
                            if ch.type == "PARAM_ASSIGN" and ("W=" in ch.value.upper() or "L=" in ch.value.upper()):
                                return True
                        elif isinstance(ch, Tree):
                            if check_tree_for_mos_params(ch):
                                return True
                    return False
                
                if check_tree_for_mos_params(tree):
                    has_mos_params = True
            
            # If it looks like a MOSFET, reclassify it
            if has_mos_model or has_mos_params:
                comp_type = "M"

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

    def build_model(self, tree: Tree) -> ModelNode:  # noqa: PLR0912
        """Build ModelNode from model_line tree.

        Args:
            tree: Model line parse tree

        Returns:
            ModelNode
        """
        name = ""
        model_type = ""
        parameters: list[ParameterNode] = []

        for child in tree.children:
            if isinstance(child, Token):
                if child.type == "MODEL_NAME":
                    name = child.value
                elif child.type == "MODEL_TYPE_NAME":
                    model_type = child.value
            elif isinstance(child, Tree):
                if child.data == "model_type":
                    if child.children and isinstance(child.children[0], Token):
                        model_type = child.children[0].value
                elif child.data == "model_params":
                    # Model params can be in parentheses or as parameter_list
                    for param_child in child.children:
                        if isinstance(param_child, Tree):
                            if param_child.data == "parameter_list":
                                parameters.extend(self.extract_parameters(param_child))
                            elif param_child.data == "parameter":
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
        directive_type = tree.data.replace("_line", "").upper()
        parameters: list[ParameterNode] = []
        content: str | None = None

        for child in tree.children:
            if isinstance(child, Token) and child.type == "FILE_PATH":
                content = child.value.strip('"')
            elif isinstance(child, Tree) and child.data == "parameter_list":
                parameters = self.extract_parameters(child)

        return DirectiveNode(
            node_type=NodeType.DIRECTIVE,
            line_number=self.line_number,
            position=0,
            directive_type=directive_type,
            parameters=parameters,
            content=content,
        )

    def extract_nodes(self, tree: Tree) -> list[str]:
        """Extract node names from node_list tree.

        Args:
            tree: Node list parse tree

        Returns:
            List of node names
        """
        return [
            node_child.value
            for child in tree.children
            if isinstance(child, Tree) and child.data == "node"
            for node_child in child.children
            if isinstance(node_child, Token)
        ]

    def extract_parameters(self, tree: Tree) -> list[ParameterNode]:
        """Extract parameters from parameter_list tree.

        Args:
            tree: Parameter list parse tree

        Returns:
            List of ParameterNode objects
        """
        parameters: list[ParameterNode] = []
        for child in tree.children:
            if isinstance(child, Tree) and child.data == "parameter":
                param = self.build_parameter(child)
                if param:
                    parameters.append(param)
        return parameters

    def build_parameter(self, tree: Tree) -> ParameterNode | None:
        """Build ParameterNode from parameter tree.

        Args:
            tree: Parameter parse tree

        Returns:
            ParameterNode or None if invalid
        """
        name = "value"  # Default for anonymous parameters
        value_node: ValueNode | None = None

        for child in tree.children:
            if isinstance(child, Token) and child.type == "PARAM_NAME":
                name = child.value
            elif isinstance(child, Tree) and child.data == "value":
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

    def build_value(self, tree: Tree) -> ValueNode:  # noqa: PLR0912
        """Build ValueNode from value tree.

        Args:
            tree: Value parse tree

        Returns:
            ValueNode
        """
        value: float | str = ""
        unit: str | None = None

        for child in tree.children:
            if isinstance(child, Token):
                if child.type in ["NUMBER", "SCIENTIFIC", "SIGNED_NUMBER"]:
                    try:
                        value = float(child.value)
                    except ValueError:
                        value = child.value
                elif child.type == "STRING":
                    value = child.value.strip('"')
                elif child.type == "MODEL_NAME":
                    value = child.value
                elif child.type == "unit":
                    unit = child.value
            elif isinstance(child, Tree) and child.data == "function_call":
                value = self._render_function_call(child)

        # If value is still empty string, try to get from token
        if not value and tree.children:
            first_child = tree.children[0]
            if isinstance(first_child, Token):
                if first_child.type in ["NUMBER", "SCIENTIFIC", "SIGNED_NUMBER"]:
                    try:
                        value = float(first_child.value)
                    except ValueError:
                        value = first_child.value
                elif first_child.type == "MODEL_NAME":
                    value = first_child.value
                else:
                    value = first_child.value
            elif isinstance(first_child, Tree) and first_child.data == "function_call":
                value = self._render_function_call(first_child)

        return ValueNode(
            node_type=NodeType.VALUE,
            line_number=self.line_number,
            position=0,
            value=value,
            unit=unit,
        )

    def _build_value_from_token(self, token: Token) -> ValueNode | None:
        """Build ValueNode directly from a token.

        Args:
            token: Token to convert to ValueNode

        Returns:
            ValueNode or None if token type not supported
        """
        value: float | str = ""
        unit: str | None = None

        if token.type in ["NUMBER", "SCIENTIFIC", "SIGNED_NUMBER"]:
            try:
                value = float(token.value)
            except ValueError:
                value = token.value
        elif token.type in ("STRING", "MODEL_NAME"):
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

    def _render_function_call(self, tree: Tree) -> str:
        """Render a function_call tree back into string form."""
        name = ""
        args: list[str] = []
        for child in tree.children:
            if isinstance(child, Token) and child.type == "MODEL_NAME":
                name = child.value
            elif isinstance(child, Tree) and child.data == "func_arg_list":
                args = [arg.value for arg in child.children if isinstance(arg, Token)]
        args_text = " ".join(args)
        return f"{name}({args_text})"


class SpiceASTParser:
    """AST-based SPICE netlist parser using Lark."""

    def __init__(self) -> None:
        """Initialize SPICE AST parser."""
        try:
            self.parser = Lark(
                SPICE_GRAMMAR,
                parser="lalr",
                lexer="basic",
                propagate_positions=True,
                maybe_placeholders=True,
                start=["start", "component_line"],
            )
        except Exception as e:
            msg = f"Failed to initialize parser: {e}"
            raise ParseError(msg) from e

        self.builder = ASTBuilder()
        self.filename = ""
        self.logger = get_logger("ast_parser")

    def parse_file(self, filepath: str | Path) -> NetlistNode:
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
            with Path(filepath).open(encoding="utf-8") as f:
                content = self._preprocess_file(f)
                return self.parse_string(content)
        except FileNotFoundError:
            msg = f"File not found: {filepath}"
            raise ParseError(msg, filename=self.filename) from None
        except ParseError:
            raise
        except Exception as e:
            msg = f"Failed to parse file {filepath}: {e}"
            raise ParseError(msg, filename=self.filename) from e

    def parse_string(self, netlist_text: str) -> NetlistNode:
        """Parse a SPICE netlist string into an AST.

        Args:
            netlist_text: The netlist content as a string

        Returns:
            Root NetlistNode of the AST

        Note:
            This method continues parsing even when individual lines fail,
            logging warnings for errors instead of raising exceptions.
        """
        # Preprocess to handle continuation lines
        processed_text = self._preprocess_text(netlist_text)
        processed_lines = processed_text.splitlines()

        # Try line-by-line component parsing (skipping directives).
        statement_nodes: list[ASTNode] = []
        errors: list[str] = []
        
        for line_num, raw_line in enumerate(processed_lines, start=1):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("."):
                # Skip directives for now - they'll be handled in full parse if needed
                # Directives are typically not critical for component extraction
                continue
            
            # Try to parse as component
            try:
                comp_tree = self.parser.parse(line, start="component_line")
                component_node = self.builder.build_component(comp_tree)
                statement_nodes.append(component_node)
            except lark.exceptions.LarkError as e:
                error_msg = f"Line {line_num}: Failed to parse component - {e}"
                self.logger.warning(error_msg)
                errors.append(error_msg)
                # Continue parsing other lines

        # If we have any successfully parsed statements, return them
        if statement_nodes:
            if errors:
                self.logger.warning(
                    f"Parsed {len(statement_nodes)} statements with {len(errors)} errors. "
                    f"Some lines were skipped due to parsing errors."
                )
            return NetlistNode(
            node_type=NodeType.NETLIST,
            line_number=1,
            position=0,
            title="Untitled",
            statements=statement_nodes,
        )

        # Fallback: try full parse, but catch errors gracefully
        try:
            tree = self.parser.parse(processed_text, start="start")
            return self.builder.build_netlist(tree)
        except lark.exceptions.UnexpectedToken as e:
            line_num = getattr(e, "line", None) or self._find_error_line(
                netlist_text, str(e)
            )
            error_msg = f"Line {line_num}: Unexpected token - {e}"
            self.logger.warning(error_msg)
            # Return empty netlist if full parse fails
            return NetlistNode(
                node_type=NodeType.NETLIST,
                line_number=1,
                position=0,
                title="Untitled",
                statements=[],
            )
        except lark.exceptions.UnexpectedCharacters as e:
            line_num = getattr(e, "line", None) or self._find_error_line(
                netlist_text, str(e)
            )
            error_msg = f"Line {line_num}: Unexpected character - {e}"
            self.logger.warning(error_msg)
            return NetlistNode(
                node_type=NodeType.NETLIST,
                line_number=1,
                position=0,
                title="Untitled",
                statements=[],
            )
        except lark.exceptions.LarkError as e:
            line_num = getattr(e, "line", None) or self._find_error_line(
                netlist_text, str(e)
            )
            error_msg = f"Line {line_num}: Parse error - {e}"
            self.logger.warning(error_msg)
            return NetlistNode(
                node_type=NodeType.NETLIST,
                line_number=1,
                position=0,
                title="Untitled",
                statements=[],
            )
        except Exception as e:
            error_msg = f"Unexpected error during parsing: {e}"
            self.logger.warning(error_msg)
            return NetlistNode(
                node_type=NodeType.NETLIST,
                line_number=1,
                position=0,
                title="Untitled",
                statements=[],
            )

    def _preprocess_file(self, file_handle: TextIO) -> str:
        """Preprocess file to handle continuation lines and filter comments.

        Args:
            file_handle: File handle to read from

        Returns:
            Preprocessed netlist text with comments removed and continuations merged
        """
        lines: list[str] = []
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
            if normalized.startswith("*"):
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                continue
            
            # Normalize SPICE directives to uppercase (e.g., .model -> .MODEL)
            # This ensures case-insensitive directive handling
            if normalized.startswith("."):
                directive_match = re.match(r'^\.([a-z]+)', normalized, re.IGNORECASE)
                if directive_match:
                    directive = directive_match.group(1).upper()
                    # Replace lowercase directive with uppercase
                    normalized = "." + directive + normalized[len("." + directive_match.group(1)):]

            # Handle continuation lines (starting with +), allowing leading whitespace
            if normalized.startswith("+"):
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

        # Apply X_ to M_ conversion for flattened MOSFET designs
        processed_lines = []
        for line in lines:
            # Check if line is an X_ prefixed component (allow dots in names for hierarchical names)
            if re.match(r'^X[A-Za-z0-9_.]+\s+', line) and '/' not in line:
                parts = line.split()
                
                # For flattened designs, ALL X_ prefixed components should be MOSFETs
                # Detect MOSFET by checking for PMOS/NMOS model type + W= or L= parameters
                # This is more permissive: if it has PMOS/NMOS and MOSFET parameters, convert it
                has_mos_model = False
                has_w_param = False
                has_l_param = False
                
                for part in parts:
                    part_upper = part.upper()
                    if part_upper in ("PMOS", "NMOS"):
                        has_mos_model = True
                    elif '=' in part:
                        if part_upper.startswith('W='):
                            has_w_param = True
                        elif part_upper.startswith('L='):
                            has_l_param = True
                
                # If it has PMOS/NMOS and W= or L= parameters, it's a MOSFET - convert it
                # For flattened designs, also check if it has transistor-like format (enough nodes + params)
                is_transistor_format = len(parts) >= 6  # name + 4 nodes + model/type + params
                if has_mos_model and (has_w_param or has_l_param):
                    # Convert X_ prefix to M_ prefix
                    parts[0] = 'M' + parts[0][1:]  # Replace X with M
                    line = ' '.join(parts)
                elif is_transistor_format and (has_w_param or has_l_param):
                    # Has MOSFET parameters (W=/L=) but may not have explicit PMOS/NMOS keyword
                    # Still convert it - likely a MOSFET in flattened design
                    parts[0] = 'M' + parts[0][1:]
                    line = ' '.join(parts)
            
            processed_lines.append(line)

        return "\n".join(processed_lines)

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text to handle continuation lines and filter comments.

        Args:
            text: Raw netlist text

        Returns:
            Preprocessed netlist text with comments removed and continuations merged
        """
        lines: list[str] = []
        current_line = ""

        for line in text.split("\n"):
            cleaned_line = self._strip_inline_comment(line.rstrip()).rstrip()
            if not cleaned_line:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                continue

            normalized = cleaned_line.lstrip()

            # Skip comment lines (starting with *), allowing leading whitespace
            if normalized.startswith("*"):
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                continue
            
            # Normalize SPICE directives to uppercase (e.g., .model -> .MODEL)
            # This ensures case-insensitive directive handling
            if normalized.startswith("."):
                directive_match = re.match(r'^\.([a-z]+)', normalized, re.IGNORECASE)
                if directive_match:
                    directive = directive_match.group(1).upper()
                    # Replace lowercase directive with uppercase
                    normalized = "." + directive + normalized[len("." + directive_match.group(1)):]

            # Skip title line: first non-empty, non-comment line that doesn't
            # start with a known statement/component designator.
            if (
                not lines
                and not current_line
                and normalized
                and normalized[0].upper()
                not in {".", "R", "C", "L", "V", "I", "M", "Q", "D", "X", "B"}
            ):
                continue

            # Handle continuation lines (starting with +), allowing leading whitespace
            if normalized.startswith("+"):
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

        # Post-process: Handle X_ prefixed components
        # 1. Convert X_ MOSFET instances to M_ format (Yosys flattened netlist format)
        # 2. Add '/' separator to legitimate subcircuit instances
        # Note: 're' is already imported at module level
        processed_lines = []
        for line in lines:
            # Check if line is an X_ prefixed component (allow dots in names for hierarchical names)
            if re.match(r'^X[A-Za-z0-9_.]+\s+', line) and '/' not in line:
                parts = line.split()
                
                # For flattened designs, ALL X_ prefixed components should be MOSFETs
                # Detect MOSFET by checking for PMOS/NMOS model type + W= or L= parameters
                # This is more permissive: if it has PMOS/NMOS and MOSFET parameters, convert it
                has_mos_model = False
                has_w_param = False
                has_l_param = False
                
                for part in parts:
                    part_upper = part.upper()
                    if part_upper in ("PMOS", "NMOS"):
                        has_mos_model = True
                    elif '=' in part:
                        if part_upper.startswith('W='):
                            has_w_param = True
                        elif part_upper.startswith('L='):
                            has_l_param = True
                
                # If it has PMOS/NMOS and W= or L= parameters, it's a MOSFET - convert it
                # For flattened designs, also check if it has transistor-like format (enough nodes + params)
                is_transistor_format = len(parts) >= 6  # name + 4 nodes + model/type + params
                if has_mos_model and (has_w_param or has_l_param):
                    # Convert X_ prefix to M_ prefix
                    parts[0] = 'M' + parts[0][1:]  # Replace X with M
                    line = ' '.join(parts)
                elif is_transistor_format and (has_w_param or has_l_param):
                    # Has MOSFET parameters (W=/L=) but may not have explicit PMOS/NMOS keyword
                    # Still convert it - likely a MOSFET in flattened design
                    parts[0] = 'M' + parts[0][1:]
                    line = ' '.join(parts)
                elif len(parts) >= 3:
                    # Potential subcircuit instance - try to add '/' separator
                    # Find the subcircuit name: it's the first token that:
                    # 1. Starts with uppercase letter (not X)
                    # 2. Is followed by a PARAM_ASSIGN (contains '=')
                    # 3. Matches SUBCKT_NAME pattern: [A-Z][A-Za-z0-9_]+
                    for i in range(len(parts) - 1, 0, -1):
                        part = parts[i]
                        # Check if this part looks like a subcircuit name (starts with uppercase, not X)
                        if re.match(r'^[A-Z][A-Za-z0-9_]+$', part) and not part.startswith('X'):
                            # Check if next part is PARAM_ASSIGN (contains '=')
                            if i + 1 < len(parts) and '=' in parts[i + 1]:
                                # Insert '/' before this subcircuit name
                                parts.insert(i, '/')
                                line = ' '.join(parts)
                                break
            processed_lines.append(line)

        # Join with newlines to preserve statement boundaries.
        return "\n".join(processed_lines)

    @staticmethod
    def _strip_inline_comment(line: str) -> str:
        """Remove inline comments marked by ';' while preserving strings.

        Args:
            line: Raw line text that may contain inline comments.

        Returns:
            Line content with inline comments removed.
        """
        in_string = False
        result_chars: list[str] = []

        for char in line:
            if char == '"':
                in_string = not in_string
            if char == ";" and not in_string:
                break
            result_chars.append(char)

        return "".join(result_chars)

    def _find_error_line(self, text: str, error_msg: str) -> int:  # noqa: ARG002
        """Attempt to find the line number where an error occurred.

        Args:
            text: Source text
            error_msg: Error message

        Returns:
            Estimated line number
        """
        # Try to extract line number from error message
        match = re.search(r"line\s+(\d+)", error_msg, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Fallback: return first line
        return 1
