#!/usr/bin/env python3
"""Main CLI entry point for SPICE netlist parser.

This module provides the command-line interface for the SPICE netlist parser.
It follows the project structure requirements and provides a clean separation
between CLI logic and core parsing functionality.
"""

import argparse
import sys
import traceback
from pathlib import Path

from spice_netlist_parser.config import get_config
from spice_netlist_parser.exceptions import ParseError, ValidationError
from spice_netlist_parser.logging_config import setup_logging

from .cli.commands import (
    compare_command,
    parse_command,
    roundtrip_command,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="spice-parser",
        description="SPICE Netlist Parser - Parse and analyze SPICE netlist files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  spice-parser parse circuit.sp
  spice-parser parse circuit.sp --format json --output result.json
  spice-parser compare circuit1.sp circuit2.sp
  spice-parser roundtrip circuit.sp --output normalized.sp

Environment Variables:
  SPICE_PARSER_LOG_LEVEL     Set logging level (DEBUG, INFO, WARNING, ERROR)
  SPICE_PARSER_LOG_FILE      Set log file path
  SPICE_PARSER_MAX_FILE_SIZE Set maximum file size in bytes
  SPICE_PARSER_DEFAULT_FORMAT Set default output format (text, json, summary)
        """,
    )

    # Global options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=get_config().log_level,
        help="Set logging level (default: INFO)",
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write logs to file",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=True,
    )

    # Parse command
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse one or more SPICE netlist files",
    )
    parse_parser.add_argument(
        "files",
        type=Path,
        nargs="+",
        help="SPICE netlist files to parse",
    )
    parse_parser.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "summary"],
        default=get_config().default_output_format,
        help="Output format (default: text)",
    )
    parse_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
    )
    parse_parser.add_argument(
        "--ast",
        action="store_true",
        help="Show AST structure instead of parsed netlist",
    )
    parse_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output with detailed information",
    )
    parse_parser.add_argument(
        "--group-by-file",
        action="store_true",
        help="Group components by source file (multi-file only)",
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare two SPICE netlist files",
    )
    compare_parser.add_argument(
        "file1",
        type=Path,
        help="First SPICE netlist file",
    )
    compare_parser.add_argument(
        "file2",
        type=Path,
        help="Second SPICE netlist file",
    )
    compare_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
    )
    compare_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # Roundtrip command
    roundtrip_parser = subparsers.add_parser(
        "roundtrip",
        help="Perform round-trip validation (parse -> serialize -> parse)",
    )
    roundtrip_parser.add_argument(
        "file",
        type=Path,
        help="SPICE netlist file to validate",
    )
    roundtrip_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path for normalized netlist",
    )

    return parser


def main() -> int:  # noqa: PLR0911
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(
        level=args.log_level,
        log_file=args.log_file,
    )

    try:
        if args.command == "parse":
            return parse_command(args)
        if args.command == "compare":
            return compare_command(args)
        if args.command == "roundtrip":
            return roundtrip_command(args)
        parser.error(f"Unknown command: {args.command}")

    except ParseError as e:
        print(f"Parse Error: {e}", file=sys.stderr)  # noqa: T201
        return 1
    except ValidationError as e:
        print(f"Validation Error: {e}", file=sys.stderr)  # noqa: T201
        return 1
    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)  # noqa: T201
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)  # noqa: T201
        if args.verbose if hasattr(args, "verbose") else False:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
