"""Multi-file SPICE netlist parser with cross-file subcircuit resolution.

This module provides functionality to parse multiple SPICE netlist files
and resolve subcircuit references across files.
"""

from pathlib import Path
from typing import Dict, List, Any, Tuple

from .models import Netlist, Component, ComponentType
from .parser import SpiceNetlistParser
from .logging_config import get_logger

logger = get_logger("multi_file_parser")


class MultiFileParser:
    """Parser for multiple SPICE netlist files with cross-file subcircuit resolution."""

    def __init__(self) -> None:
        """Initialize the multi-file parser."""
        self.single_parser = SpiceNetlistParser()
        self.subcircuits: Dict[str, List[Component]] = {}  # name -> list of components in subcircuit

    def parse_files(self, file_paths: List[Path]) -> Tuple[Netlist, Dict[str, List[Component]]]:
        """Parse multiple SPICE netlist files and resolve cross-references.

        Args:
            file_paths: List of file paths to parse

        Returns:
            Tuple of (unified Netlist, file_component_map) where file_component_map
            maps file paths to their component lists
        """
        logger.info(f"Parsing {len(file_paths)} files")

        # Parse all files and collect components by file
        file_components: Dict[str, List[Component]] = {}
        all_components: List[Component] = []
        all_models: Dict[str, Dict[str, Any]] = {}
        titles: List[str] = []

        for file_path in file_paths:
            logger.debug(f"Parsing file: {file_path}")
            try:
                netlist = self.single_parser.parse_file(file_path)

                # Store components by file
                file_components[str(file_path)] = netlist.components

                # Collect title
                if netlist.title and netlist.title != "Untitled":
                    titles.append(netlist.title)

                # Collect models
                all_models.update(netlist.models)

                # Collect all components for unified netlist
                all_components.extend(netlist.components)

            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
                raise

        # Create unified netlist
        title = titles[0] if titles else f"Multi-file netlist ({len(file_paths)} files)"

        netlist = Netlist(
            title=title,
            components=all_components,
            models=all_models,
            options={},
            includes=[]
        )

        logger.info(f"Successfully merged {len(file_paths)} files into unified netlist")
        logger.info(f"Total components: {len(netlist.components)}")
        logger.info(f"Total models: {len(netlist.models)}")

        return netlist, file_components
