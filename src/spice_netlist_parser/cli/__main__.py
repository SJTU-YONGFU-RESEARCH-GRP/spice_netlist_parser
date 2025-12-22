#!/usr/bin/env python3
"""CLI entry point for the spice-netlist-parser package.

This allows the package to be run as a module with:
python -m spice_netlist_parser.cli
"""

from ..main import main  # noqa: TID252

if __name__ == "__main__":
    import sys

    sys.exit(main())
