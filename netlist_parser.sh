#!/bin/bash

# SPICE Netlist Parser - Run Script
# This script runs the SPICE netlist parser CLI

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo -e "${BLUE}SPICE Netlist Parser${NC}"
echo "===================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Error: Python not found. Please install Python 3.10+"
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Check if we're in a virtual environment
if [ -z "${VIRTUAL_ENV-}" ]; then
    echo "Note: Not in a virtual environment. Consider using one."
    echo ""
fi

# Add src to PYTHONPATH
export PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

print_help() {
    echo "Usage: $0 <netlist_file> [options]"
    echo ""
    echo "Parser options (passed through to CLI):"
    echo "  -f, --format <format>       Output format: text, json, summary (default: text)"
    echo "  -o, --output <file>         Output file path"
    echo "  --ast                       Show AST structure"
    echo "  -v, --verbose               Verbose output"
    echo ""
    echo "Quality / accuracy options:"
    echo "  --roundtrip                 Run parse -> serialize -> parse validation on the input file"
    echo "  --roundtrip-only            Only run round-trip validation (do not print parsed output)"
    echo "  --roundtrip-output <file>   Write the serialized SPICE produced by round-trip to a file"
    echo "  --compare <file2>           Compare <netlist_file> against <file2> (semantic model diff)"
    echo "  --compare-format <format>   Compare output format: text, json (default: text)"
    echo "  --compare-output <file>     Write compare report to a file (default: stdout)"
    echo ""
    echo "Examples:"
    echo "  $0 examples/1k.sp"
    echo "  $0 examples/1k.sp --format json --output result.json"
    echo "  $0 examples/1k.sp --roundtrip"
    echo "  $0 examples/1k.sp --roundtrip --roundtrip-output rt.sp"
    echo "  $0 examples/1k.sp --compare examples/10k.sp"
    echo "  $0 examples/1k.sp --compare examples/10k.sp --compare-format json --compare-output report.json"
}

# Parse wrapper arguments, keep the rest for the Python CLI
ROUNDTRIP=0
ROUNDTRIP_ONLY=0
ROUNDTRIP_OUTPUT=""
COMPARE_FILE=""
COMPARE_FORMAT="text"
COMPARE_OUTPUT=""
PASSTHROUGH_ARGS=()

if [ $# -eq 0 ]; then
    print_help
    exit 1
fi

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            print_help
            exit 0
            ;;
        --roundtrip)
            ROUNDTRIP=1
            shift
            ;;
        --roundtrip-only)
            ROUNDTRIP=1
            ROUNDTRIP_ONLY=1
            shift
            ;;
        --roundtrip-output)
            shift
            if [ $# -eq 0 ]; then
                echo -e "${RED}Error:${NC} --roundtrip-output requires a file path"
                exit 1
            fi
            ROUNDTRIP_OUTPUT="$1"
            shift
            ;;
        --compare)
            shift
            if [ $# -eq 0 ]; then
                echo -e "${RED}Error:${NC} --compare requires a file path"
                exit 1
            fi
            COMPARE_FILE="$1"
            shift
            ;;
        --compare-format)
            shift
            if [ $# -eq 0 ]; then
                echo -e "${RED}Error:${NC} --compare-format requires a value (text|json)"
                exit 1
            fi
            COMPARE_FORMAT="$1"
            shift
            ;;
        --compare-output)
            shift
            if [ $# -eq 0 ]; then
                echo -e "${RED}Error:${NC} --compare-output requires a file path"
                exit 1
            fi
            COMPARE_OUTPUT="$1"
            shift
            ;;
        *)
            PASSTHROUGH_ARGS+=("$1")
            shift
            ;;
    esac
done

# Check if file argument is provided (first passthrough arg is the input file)
if [ ${#PASSTHROUGH_ARGS[@]} -eq 0 ]; then
    echo -e "${RED}Error:${NC} netlist file argument is required"
    echo ""
    print_help
    exit 1
fi

# Round-trip validation (conversion accuracy check)
if [ "$ROUNDTRIP" -eq 1 ]; then
    NETLIST_FILE="${PASSTHROUGH_ARGS[0]}"
    if [ ! -f "$NETLIST_FILE" ]; then
        echo -e "${RED}Error:${NC} File not found: $NETLIST_FILE"
        exit 1
    fi

    echo -e "${BLUE}Round-trip validation${NC}"
    echo "----------------------"
    echo -e "${GREEN}Running:${NC} parse -> serialize -> parse"
    echo ""

    # Use the library's RoundTripValidator; if it fails, it raises an AssertionError with a diff.
    PY_ARGS=("$PYTHON_CMD" "-" "$NETLIST_FILE")
    if [ -n "$ROUNDTRIP_OUTPUT" ]; then
        PY_ARGS+=("--roundtrip-output" "$ROUNDTRIP_OUTPUT")
    fi

    "${PY_ARGS[@]}" <<'PY'
from __future__ import annotations

import argparse
from pathlib import Path

from spice_netlist_parser import RoundTripValidator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("netlist_file", type=Path)
    parser.add_argument("--roundtrip-output", type=Path, default=None)
    args = parser.parse_args()

    text = args.netlist_file.read_text(encoding="utf-8")
    validator = RoundTripValidator()
    result = validator.assert_round_trip_string(text)

    if args.roundtrip_output is not None:
        args.roundtrip_output.write_text(result.serialized_spice, encoding="utf-8")

    print("✅ Round-trip OK")
    if args.roundtrip_output is not None:
        print(f"Serialized SPICE written to: {args.roundtrip_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

    echo ""
fi

if [ "$ROUNDTRIP_ONLY" -eq 1 ]; then
    exit 0
fi

# Compare two SPICE files (semantic comparison on parsed Netlist models)
if [ -n "$COMPARE_FILE" ]; then
    NETLIST_FILE="${PASSTHROUGH_ARGS[0]}"
    if [ ! -f "$NETLIST_FILE" ]; then
        echo -e "${RED}Error:${NC} File not found: $NETLIST_FILE"
        exit 1
    fi
    if [ ! -f "$COMPARE_FILE" ]; then
        echo -e "${RED}Error:${NC} File not found: $COMPARE_FILE"
        exit 1
    fi

    echo -e "${BLUE}Netlist comparison${NC}"
    echo "-------------------"
    echo -e "${GREEN}Comparing:${NC} $NETLIST_FILE  <->  $COMPARE_FILE"
    echo ""

    PY_ARGS=("$PYTHON_CMD" "-" "$NETLIST_FILE" "$COMPARE_FILE" "--format" "$COMPARE_FORMAT")
    if [ -n "$COMPARE_OUTPUT" ]; then
        PY_ARGS+=("--output" "$COMPARE_OUTPUT")
    fi

    "${PY_ARGS[@]}" <<'PY'
from __future__ import annotations

import argparse
import json
from pathlib import Path

from spice_netlist_parser.comparison import compare_files, format_report_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    report = compare_files(args.left, args.right)

    if args.format == "json":
        out = json.dumps(report.to_dict(), indent=2, default=str) + "\n"
    else:
        out = format_report_text(report)

    if args.output is not None:
        args.output.write_text(out, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(out, end="")

    # Non-zero exit code when different is useful in CI.
    return 0 if report.is_equal else 2


if __name__ == "__main__":
    raise SystemExit(main())
PY

    echo ""
fi

# Run the parser
echo -e "${GREEN}Running parser...${NC}"
echo ""

$PYTHON_CMD -m spice_netlist_parser.cli "${PASSTHROUGH_ARGS[@]}"

