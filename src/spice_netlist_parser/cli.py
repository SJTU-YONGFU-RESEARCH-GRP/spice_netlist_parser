"""Command-line interface for SPICE netlist parser."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .parser import SpiceNetlistParser
from .exceptions import ParseError, ValidationError


def format_output(
    netlist,
    output_format: str = "text",
    output_file: Optional[Path] = None,
) -> None:
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
        output_file.write_text(output, encoding='utf-8')
        print(f"Output written to {output_file}")
    else:
        print(output)


def format_text(netlist) -> str:
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
                params_str = ", ".join(
                    f"{k}={v}" for k, v in comp.parameters.items()
                )
                lines.append(f"    Parameters: {params_str}")
            if comp.model:
                lines.append(f"    Model: {comp.model}")
            lines.append("")
    
    if netlist.models:
        lines.append("Models:")
        for model_name, model_data in netlist.models.items():
            lines.append(f"  {model_name}: {model_data.get('type', 'N/A')}")
            if 'parameters' in model_data:
                params_str = ", ".join(
                    f"{k}={v}" for k, v in model_data['parameters'].items()
                )
                lines.append(f"    Parameters: {params_str}")
            lines.append("")
    
    if netlist.includes:
        lines.append("Includes:")
        for include in netlist.includes:
            lines.append(f"  {include}")
        lines.append("")
    
    return "\n".join(lines)


def format_json(netlist) -> str:
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


def format_summary(netlist) -> str:
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
    comp_types = {}
    for comp in netlist.components:
        comp_type = comp.component_type.value
        comp_types[comp_type] = comp_types.get(comp_type, 0) + 1
    
    if comp_types:
        lines.append("  Component breakdown:")
        for comp_type, count in sorted(comp_types.items()):
            lines.append(f"    {comp_type}: {count}")
    
    return "\n".join(lines)


def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="SPICE Netlist Parser - Parse and analyze SPICE netlist files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s circuit.sp
  %(prog)s circuit.sp --format json --output result.json
  %(prog)s circuit.sp --format summary
  %(prog)s circuit.sp --ast  # Show AST structure
        """,
    )
    
    parser.add_argument(
        "file",
        type=Path,
        help="SPICE netlist file to parse",
    )
    
    parser.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "summary"],
        default="text",
        help="Output format (default: text)",
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
    )
    
    parser.add_argument(
        "--ast",
        action="store_true",
        help="Show AST structure instead of parsed netlist",
    )
    
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output with detailed information",
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1
    
    try:
        spice_parser = SpiceNetlistParser()
        
        if args.ast:
            # Show AST structure
            ast = spice_parser.parse_file_to_ast(args.file)
            print(f"AST Root: {ast.node_type.value}")
            print(f"Title: {ast.title}")
            print(f"Statements: {len(ast.statements)}")
            if args.verbose:
                print("\nDetailed AST:")
                for i, stmt in enumerate(ast.statements, 1):
                    print(f"  {i}. {stmt.node_type.value}: {stmt}")
        else:
            # Parse to netlist
            netlist = spice_parser.parse_file(args.file)
            
            if args.verbose:
                print(f"Successfully parsed: {args.file}")
                print(f"Title: {netlist.title}")
                print(f"Components: {len(netlist.components)}")
                print(f"Nodes: {netlist.nodes}")
                print("")
            
            format_output(netlist, args.format, args.output)
        
        return 0
        
    except ParseError as e:
        print(f"Parse Error: {e}", file=sys.stderr)
        return 1
    except ValidationError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


