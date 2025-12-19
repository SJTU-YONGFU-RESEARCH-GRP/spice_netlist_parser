"""Main parser interface combining AST parsing with model transformation."""

from typing import Union
from pathlib import Path

from .ast_parser import SpiceASTParser
from .visitors import NetlistTransformer
from .models import Netlist
from .ast_nodes import NetlistNode


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
        self.ast_parser = SpiceASTParser()
        self.transformer = NetlistTransformer()
    
    def parse_file(self, filepath: Union[str, Path]) -> Netlist:
        """Parse a SPICE netlist file.
        
        Args:
            filepath: Path to the netlist file
            
        Returns:
            Parsed Netlist object
            
        Raises:
            ParseError: If parsing fails
        """
        ast = self.ast_parser.parse_file(filepath)
        return self.transformer.transform(ast)
    
    def parse_string(self, netlist_text: str) -> Netlist:
        """Parse a SPICE netlist from a string.
        
        Args:
            netlist_text: The netlist content as a string
            
        Returns:
            Parsed Netlist object
            
        Raises:
            ParseError: If parsing fails
        """
        ast = self.ast_parser.parse_string(netlist_text)
        return self.transformer.transform(ast)
    
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
        return self.ast_parser.parse_string(netlist_text)
    
    def parse_file_to_ast(self, filepath: Union[str, Path]) -> NetlistNode:
        """Parse file to AST without transformation (for debugging/analysis).
        
        Args:
            filepath: Path to the netlist file
            
        Returns:
            Root AST node
            
        Raises:
            ParseError: If parsing fails
        """
        return self.ast_parser.parse_file(filepath)


