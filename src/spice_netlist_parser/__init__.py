"""SPICE netlist parser - A robust AST-based parser for SPICE netlist files.

This package provides a comprehensive parser for SPICE netlist files using
an Abstract Syntax Tree (AST) approach for robust parsing and error handling.

Main Classes:
    SpiceNetlistParser: Main parser class for parsing netlist files
    Netlist: Domain model representing a parsed netlist
    Component: Domain model representing a circuit component
    ComponentType: Enumeration of component types
    ParseError: Exception raised during parsing
    ValidationError: Exception raised during validation

Example:
    >>> from spice_netlist_parser import SpiceNetlistParser
    >>> parser = SpiceNetlistParser()
    >>> netlist = parser.parse_file("circuit.sp")
    >>> print(f"Title: {netlist.title}")
    >>> print(f"Components: {len(netlist.components)}")
    >>> for comp in netlist.components:
    ...     print(f"  {comp.name}: {comp.component_type.value}")
"""

from .parser import SpiceNetlistParser
from .models import Netlist, Component, ComponentType
from .exceptions import ParseError, ValidationError
from .roundtrip import RoundTripValidator, RoundTripMismatchError, RoundTripResult
from .serializer import SpiceSerializer, SpiceSerializerOptions
from .comparison import (
    NetlistComparisonReport,
    NetlistStats,
    compare_files,
    compare_netlists,
    format_report_text,
)

__all__ = [
    "SpiceNetlistParser",
    "Netlist",
    "Component",
    "ComponentType",
    "ParseError",
    "ValidationError",
    "SpiceSerializer",
    "SpiceSerializerOptions",
    "RoundTripValidator",
    "RoundTripMismatchError",
    "RoundTripResult",
    "NetlistStats",
    "NetlistComparisonReport",
    "compare_files",
    "compare_netlists",
    "format_report_text",
]

__version__ = "0.1.0"


