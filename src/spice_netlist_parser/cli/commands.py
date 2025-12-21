"""CLI command implementations for SPICE netlist parser.

This module contains the implementation of individual CLI commands,
separated from the main CLI entry point for better organization.
"""

import json
import sys
from pathlib import Path
from typing import Any

from ..comparison import compare_files, format_report_text  # noqa: TID252
from ..logging_config import get_logger  # noqa: TID252
from ..parser import SpiceNetlistParser  # noqa: TID252
from ..roundtrip import RoundTripValidator  # noqa: TID252
from ..serializer import SpiceSerializer, SpiceSerializerOptions  # noqa: TID252,F401

logger = get_logger("cli")


def parse_command(args: Any) -> int:
    """Handle the 'parse' command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Check if file exists
    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)  # noqa: T201
        return 1

    try:
        spice_parser = SpiceNetlistParser()

        if args.ast:
            # Show AST structure
            ast = spice_parser.parse_file_to_ast(args.file)
            print(f"AST Root: {ast.node_type.value}")  # noqa: T201
            print(f"Title: {ast.title}")  # noqa: T201
            print(f"Statements: {len(ast.statements)}")  # noqa: T201
            if args.verbose:
                print("\nDetailed AST:")  # noqa: T201
                for i, stmt in enumerate(ast.statements, 1):
                    print(f"  {i}. {stmt.node_type.value}: {stmt}")  # noqa: T201
        else:
            # Parse to netlist
            netlist = spice_parser.parse_file(args.file)

            if args.verbose:
                print(f"Successfully parsed: {args.file}")  # noqa: T201
                print(f"Title: {netlist.title}")  # noqa: T201
                print(f"Components: {len(netlist.components)}")  # noqa: T201
                print(f"Models: {len(netlist.models)}")  # noqa: T201
                print(f"Nodes: {len(netlist.nodes)}")  # noqa: T201
                print()  # noqa: T201

            format_output(netlist, args.format, args.output)

    except Exception as e:
        logger.error(f"Failed to parse {args.file}: {e}")  # noqa: TRY400,G004
        return 1
    else:
        return 0


def compare_command(args: Any) -> int:
    """Handle the 'compare' command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Check if files exist
    if not args.file1.exists():
        print(f"Error: File not found: {args.file1}", file=sys.stderr)  # noqa: T201
        return 1
    if not args.file2.exists():
        print(f"Error: File not found: {args.file2}", file=sys.stderr)  # noqa: T201
        return 1

    try:
        report = compare_files(args.file1, args.file2)

        if args.format == "json":
            output = json.dumps(report.to_dict(), indent=2)
        else:
            output = format_report_text(report)

        if args.output:
            args.output.write_text(output, encoding="utf-8")
            print(f"Comparison report written to {args.output}")  # noqa: T201
        else:
            print(output)  # noqa: T201

    except Exception as e:
        logger.error(f"Failed to compare files: {e}")  # noqa: TRY400,G004
        return 1
    else:
        return 0


def roundtrip_command(args: Any) -> int:
    """Handle the 'roundtrip' command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Check if file exists
    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)  # noqa: T201
        return 1

    try:
        validator = RoundTripValidator()
        result = validator.assert_round_trip_string(args.file.read_text())

        print("Round-trip validation successful!")  # noqa: T201
        print(f"Original components: {len(result.original.components)}")  # noqa: T201
        print(f"Reparsed components: {len(result.reparsed.components)}")  # noqa: T201

        if args.output:
            args.output.write_text(result.serialized_spice, encoding="utf-8")
            print(f"Normalized netlist written to {args.output}")  # noqa: T201

    except Exception as e:
        logger.error(f"Round-trip validation failed: {e}")  # noqa: TRY400,G004
        return 1
    else:
        return 0


def format_output(netlist: Any, output_format: str, output_file: Path | None) -> None:
    """Format and output netlist information.

    Args:
        netlist: Parsed Netlist object
        output_format: Output format ('text', 'json', 'summary')
        output_file: Optional file path to write output to
    """
    output = ""

    if output_format == "json":
        output = format_json(netlist)
    elif output_format == "summary":
        output = format_summary(netlist)
    else:
        output = format_text(netlist)

    if output_file:
        output_file.write_text(output, encoding="utf-8")
        print(f"Output written to {output_file}")  # noqa: T201
    else:
        print(output)  # noqa: T201


def format_text(netlist: Any) -> str:
    """Format netlist as human-readable text.

    Args:
        netlist: Parsed Netlist object

    Returns:
        Formatted text string
    """
    lines = []
    lines.append(f"Title: {netlist.title}")
    lines.append(f"Components: {len(netlist.components)}")
    lines.append(f"Nodes: {len(netlist.nodes)}")
    lines.append(f"Models: {len(netlist.models)}")
    lines.append("")

    if netlist.components:
        lines.append("Components:")
        for comp in netlist.components:
            lines.append(f"  {comp.name}: {comp.component_type.value}")
            lines.append(f"    Nodes: {' '.join(comp.nodes)}")
            if comp.parameters:
                params_str = ", ".join(f"{k}={v}" for k, v in comp.parameters.items())
                lines.append(f"    Parameters: {params_str}")
            if comp.model:
                lines.append(f"    Model: {comp.model}")
            lines.append("")

    if netlist.models:
        lines.append("Models:")
        for model_name, model_data in netlist.models.items():
            lines.append(f"  {model_name}: {model_data.get('type', 'N/A')}")
            if "parameters" in model_data:
                params_str = ", ".join(
                    f"{k}={v}" for k, v in model_data["parameters"].items()
                )
                lines.append(f"    Parameters: {params_str}")
            lines.append("")

    if netlist.includes:
        lines.append("Includes:")
        lines.extend(f"  {include}" for include in netlist.includes)
        lines.append("")

    return "\n".join(lines)


def format_json(netlist: Any) -> str:
    """Format netlist as JSON.

    Args:
        netlist: Parsed Netlist object

    Returns:
        JSON string
    """
    data = {
        "title": netlist.title,
        "components": [
            {
                "name": comp.name,
                "type": comp.component_type.value,
                "nodes": comp.nodes,
                "parameters": comp.parameters,
                "model": comp.model,
            }
            for comp in netlist.components
        ],
        "models": netlist.models,
        "options": netlist.options,
        "includes": netlist.includes,
        "nodes": netlist.nodes,
    }
    return json.dumps(data, indent=2, default=str)


def format_summary(netlist: Any) -> str:
    """Format netlist as a brief summary.

    Args:
        netlist: Parsed Netlist object

    Returns:
        Summary text string
    """
    lines = []
    lines.append(f"Netlist: {netlist.title}")
    lines.append(f"  Components: {len(netlist.components)}")
    lines.append(f"  Nodes: {len(netlist.nodes)}")
    lines.append(f"  Models: {len(netlist.models)}")

    # Component type breakdown
    comp_types: dict[str, int] = {}
    for comp in netlist.components:
        comp_type = comp.component_type.value
        comp_types[comp_type] = comp_types.get(comp_type, 0) + 1

    if comp_types:
        lines.append("  Component breakdown:")
        for comp_type, count in sorted(comp_types.items()):
            lines.append(f"    {comp_type}: {count}")

    return "\n".join(lines)
