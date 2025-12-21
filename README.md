# SPICE Netlist Parser

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![CI](https://github.com/SJTU-YONGFU-RESEARCH-GRP/spice_netlist_parser/actions/workflows/tests.yml/badge.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/spice_netlist_parser/actions/workflows/tests.yml)
[![Code Quality](https://github.com/SJTU-YONGFU-RESEARCH-GRP/spice_netlist_parser/actions/workflows/code-quality.yml/badge.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/spice_netlist_parser/actions/workflows/code-quality.yml)
[![Security](https://github.com/SJTU-YONGFU-RESEARCH-GRP/spice_netlist_parser/actions/workflows/security.yml/badge.svg)](https://github.com/SJTU-YONGFU-RESEARCH-GRP/spice_netlist_parser/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/SJTU-YONGFU-RESEARCH-GRP/spice_netlist_parser/branch/main/graph/badge.svg)](https://codecov.io/gh/SJTU-YONGFU-RESEARCH-GRP/spice_netlist_parser)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/charliermarsh/ruff)
[![Type Checking: Mypy](https://img.shields.io/badge/type%20checking-mypy-blue.svg)](https://mypy-lang.org/)


A robust, AST-based parser for SPICE netlist files with comprehensive analysis and validation capabilities.

## Features

- **AST-based Parsing**: Robust parsing using Abstract Syntax Trees for accurate representation
- **Component Support**: Full support for all standard SPICE components (R, C, L, V, I, M, Q, D, X)
- **Model Definitions**: Complete parsing of .MODEL directives with parameter extraction
- **Directive Support**: Handles .INCLUDE, .OPTION, .PARAM and other SPICE directives
- **Unit Handling**: Automatic parsing of engineering unit suffixes (k, m, u, n, p, f)
- **Continuation Lines**: Proper handling of SPICE continuation lines (+)
- **Round-trip Validation**: Verify parser accuracy with parse → serialize → parse cycles
- **Comparison Tools**: Compare netlists for structural and semantic differences
- **Multiple Output Formats**: Text, JSON, and summary output formats
- **Comprehensive CLI**: Full command-line interface with subcommands

## Installation

### From Source

```bash
git clone https://github.com/SJTU-YONGFU-RESEARCH-GRP/spice_netlist_parser.git
cd spice-netlist-parser
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Usage

### Command Line Interface

The parser provides a comprehensive CLI with multiple commands and output formats.

#### Basic Parsing

```bash
# Parse a netlist file with default text output
spice-parser parse circuit.sp

# Parse with JSON output
spice-parser parse circuit.sp --format json --output result.json

# Parse with summary output (brief overview)
spice-parser parse circuit.sp --format summary

# Show detailed AST structure for debugging
spice-parser parse circuit.sp --ast --verbose
```

#### Netlist Comparison

```bash
# Compare two netlists semantically
spice-parser compare circuit1.sp circuit2.sp

# Compare with JSON output format
spice-parser compare circuit1.sp circuit2.sp --format json --output comparison.json
```

#### Round-trip Validation

```bash
# Perform round-trip validation (parse → serialize → parse)
spice-parser roundtrip circuit.sp

# Save normalized netlist after round-trip validation
spice-parser roundtrip circuit.sp --output normalized.sp
```

### Enhanced CLI Scripts

The project includes additional convenience scripts for advanced usage:

#### netlist_parser.sh - Enhanced Parser Script

A wrapper script providing additional parsing and validation options:

```bash
# Basic parsing with verbose output
./netlist_parser.sh examples/1k.sp

# Round-trip validation
./netlist_parser.sh examples/1k.sp --roundtrip

# Round-trip validation with output file
./netlist_parser.sh examples/1k.sp --roundtrip --roundtrip-output normalized.sp

# Compare two netlists
./netlist_parser.sh examples/1k.sp --compare examples/10k.sp

# Compare with custom output
./netlist_parser.sh examples/1k.sp --compare examples/10k.sp --compare-format json --compare-output report.json
```

#### check_quality.sh - Quality Assurance

Run comprehensive quality checks before committing:

```bash
# Run all quality checks (linting, formatting, type checking, security, tests)
./check_quality.sh
```

#### regression.sh - Regression Testing

Run the parser against all example netlists for regression testing:

```bash
# Run regression tests on all examples
./regression.sh

# Run with additional parser arguments
./regression.sh --verbose
```

### Example Files

The `examples/` directory contains test netlists of various sizes:

- `100.sp` - Small test circuit (~100 components)
- `1k.sp` - Medium circuit (~1,000 components)
- `10k.sp` - Large circuit (~10,000 components)
- `100k.sp` - Very large circuit (~100,000 components)
- `1m.sp` - Massive circuit (~1,000,000 components)

Each example includes corresponding log files and JSON outputs for validation.

### Python API

```python
from spice_netlist_parser import SpiceNetlistParser

# Parse a file
parser = SpiceNetlistParser()
netlist = parser.parse_file("circuit.sp")

print(f"Title: {netlist.title}")
print(f"Components: {len(netlist.components)}")
print(f"Nodes: {len(netlist.nodes)}")

# Access components
for comp in netlist.components:
    print(f"{comp.name}: {comp.component_type.value} - nodes: {comp.nodes}")
```

## Configuration

The parser can be configured using environment variables:

```bash
# Set logging level
export SPICE_PARSER_LOG_LEVEL=DEBUG

# Write logs to file
export SPICE_PARSER_LOG_FILE=/var/log/spice-parser.log

# Set maximum file size (bytes)
export SPICE_PARSER_MAX_FILE_SIZE=10485760

# Set default output format
export SPICE_PARSER_DEFAULT_FORMAT=json
```

## Project Structure

```
spice-netlist-parser/
├── src/
│   └── spice_netlist_parser/      # Main package
│       ├── __init__.py           # Package initialization and exports
│       ├── parser.py             # Main parser interface
│       ├── ast_parser.py         # AST-based parsing logic
│       ├── ast_nodes.py          # AST node definitions
│       ├── visitors.py           # AST visitor pattern implementations
│       ├── models.py             # Domain models (Netlist, Component, etc.)
│       ├── serializer.py         # SPICE netlist serialization
│       ├── comparison.py         # Netlist comparison and diff tools
│       ├── roundtrip.py          # Round-trip validation utilities
│       ├── exceptions.py         # Custom exception classes
│       ├── grammar.py            # SPICE grammar definition
│       ├── config.py             # Configuration management
│       ├── logging_config.py     # Logging configuration
│       └── cli/                  # Command-line interface
│           ├── __init__.py       # CLI package init
│           ├── __main__.py       # CLI module entry point
│           └── commands.py       # CLI command implementations
├── tests/                        # Comprehensive unit test suite
├── examples/                     # Test netlists and validation data
│   ├── *.sp                     # SPICE netlist files (100, 1k, 10k, 100k, 1m components)
│   ├── *.json                   # Expected JSON outputs
│   └── *.log                    # Validation logs
├── htmlcov/                     # Test coverage reports
├── pyproject.toml               # Project configuration (PEP 621)
├── requirements.txt             # Legacy dependency file
├── netlist_parser.sh            # Enhanced parser script with extra options
├── check_quality.sh             # Quality assurance script
├── regression.sh                # Regression testing script
├── README.md                    # This file
└── LICENSE                      # License file
```

## Development

### Continuous Integration

The project uses GitHub Actions for continuous integration with the following checks:

- **Multi-Python Testing**: Tests run on Python 3.10, 3.11, and 3.12
- **Code Quality**: Linting with Ruff, type checking with mypy, security scanning with bandit
- **Test Coverage**: Code coverage reporting with Codecov
- **Regression Testing**: Automated testing against all example netlists

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_parser.py
```

### Code Quality

```bash
# Run all quality checks (recommended)
./check_quality.sh

# Or run individual checks:

# Lint and format code
ruff check src/ tests/
ruff format src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

### Pre-commit Hooks

The project includes a comprehensive pre-commit configuration that mirrors the CI checks:

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

The pre-commit hooks include:
- Code formatting and linting with Ruff
- Type checking with mypy
- Security scanning with bandit
- General file quality checks

### Regression Testing

```bash
# Run parser against all example netlists
./regression.sh

# Run with additional arguments
./regression.sh --verbose
```

## Supported SPICE Syntax

### Components
```
R1 1 0 1k           ; Resistor
C1 1 2 10u          ; Capacitor
L1 2 3 1mH         ; Inductor
V1 3 0 DC 5.0      ; Voltage source
I1 0 4 DC 1mA      ; Current source
M1 1 2 3 4 NMOS    ; MOSFET
Q1 1 2 3 NPN       ; BJT
D1 1 2 DIODE       ; Diode
X1 1 2 SUBCKT      ; Subcircuit instance
```

### Models
```
.MODEL NMOS NMOS LEVEL=1 VTO=0.7 KP=100e-6
.MODEL DIODE D IS=1e-14 RS=10
```

### Directives
```
.INCLUDE "library.sp"
.OPTION TEMP=27
.PARAM VDD=3.3
```

### Units
```
1k, 2.2k    ; kilo (10^3)
10u, 4.7u   ; micro (10^-6)
100n, 22n   ; nano (10^-9)
1p, 10p     ; pico (10^-12)
100f, 1f    ; femto (10^-15)
1meg, 2meg  ; mega (10^6)
```

## Error Handling

The parser provides specific exception types for different error conditions:

- `ParseError`: Syntax errors during parsing
- `ValidationError`: Semantic validation errors
- `RoundTripMismatchError`: Round-trip validation failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass and code quality checks succeed
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Requirements

- Python 3.10+
- Lark parser (PEG grammar parsing)
- Pydantic v2+ (data validation and configuration)
- Pydantic-settings (configuration management)

## License

This project is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) License - see the [LICENSE](LICENSE) file for details.

You are free to:
- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
- **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made

For more details, see: https://creativecommons.org/licenses/by/4.0/
