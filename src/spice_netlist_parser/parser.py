"""Main parser interface combining AST parsing with model transformation."""

from pathlib import Path

from .ast_nodes import NetlistNode
from .ast_parser import SpiceASTParser
from .logging_config import get_logger
from .models import Netlist
from .visitors import NetlistTransformer


class SpiceNetlistParser:
    """Robust AST-based SPICE netlist parser.

    This parser uses an Abstract Syntax Tree (AST) approach for robust
    parsing of SPICE netlist files. It supports:
    - All standard SPICE components (R, C, L, V, I, M, Q, D, X)
    - Model definitions (.MODEL)
    - Directives (.INCLUDE, .OPTION, .PARAM)
    - Continuation lines (lines starting with '+')
    - Unit suffixes (k, m, u, n, p, f, etc.)

    Example:
        >>> parser = SpiceNetlistParser()
        >>> netlist = parser.parse_file("circuit.sp")
        >>> print(f"Found {len(netlist.components)} components")
        >>> print(f"Nodes: {netlist.nodes}")
    """

    def __init__(self) -> None:
        """Initialize SPICE netlist parser."""
        self.logger = get_logger("parser")
        self.ast_parser = SpiceASTParser()
        self.transformer = NetlistTransformer()

    def parse_file(self, filepath: str | Path) -> Netlist:
        """Parse a SPICE netlist file.

        Args:
            filepath: Path to the netlist file

        Returns:
            Parsed Netlist object

        Raises:
            ParseError: If parsing fails
        """
        filepath = Path(filepath)
        self.logger.info(f"Parsing file: {filepath}")  # noqa: G004
        ast = self.ast_parser.parse_file(filepath)
        netlist = self.transformer.transform(ast)
        self.logger.info(
            f"Successfully parsed {len(netlist.components)} components, {len(netlist.models)} models"  # noqa: G004
        )
        return netlist

    def parse_string(self, netlist_text: str) -> Netlist:
        """Parse a SPICE netlist from a string.

        Args:
            netlist_text: The netlist content as a string

        Returns:
            Parsed Netlist object

        Raises:
            ParseError: If parsing fails
        """
        self.logger.debug("Parsing netlist from string")
        ast = self.ast_parser.parse_string(netlist_text)
        netlist = self.transformer.transform(ast)
        self.logger.debug(f"Parsed {len(netlist.components)} components from string")  # noqa: G004
        return netlist

    def parse_to_ast(self, netlist_text: str) -> NetlistNode:
        """Parse to AST without transformation (for debugging/analysis).

        This method returns the raw AST structure, which can be useful
        for debugging parsing issues or performing custom analysis
        on the parse tree.

        Args:
            netlist_text: The netlist content as a string

        Returns:
            Root AST node

        Raises:
            ParseError: If parsing fails
        """
        self.logger.debug("Parsing to AST from string")
        return self.ast_parser.parse_string(netlist_text)

    def parse_file_to_ast(self, filepath: str | Path) -> NetlistNode:
        """Parse file to AST without transformation (for debugging/analysis).

        Args:
            filepath: Path to the netlist file

        Returns:
            Root AST node

        Raises:
            ParseError: If parsing fails
        """
        filepath = Path(filepath)
        self.logger.debug(f"Parsing file to AST: {filepath}")  # noqa: G004
        return self.ast_parser.parse_file(filepath)
