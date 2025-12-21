# SPICE Netlist Parser

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
git clone https://github.com/yourusername/spice-netlist-parser.git
cd spice-netlist-parser
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Usage

### Command Line Interface

```bash
# Parse a netlist file
spice-parser parse circuit.sp

# Parse with JSON output
spice-parser parse circuit.sp --format json --output result.json

# Compare two netlists
spice-parser compare circuit1.sp circuit2.sp

# Perform round-trip validation
spice-parser roundtrip circuit.sp --output normalized.sp

# Show AST structure for debugging
spice-parser parse circuit.sp --ast --verbose
```

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
│   ├── main.py                    # CLI entry point
│   └── spice_netlist_parser/
│       ├── __init__.py           # Package initialization
│       ├── parser.py             # Main parser interface
│       ├── ast_parser.py         # AST-based parsing
│       ├── ast_nodes.py          # AST node definitions
│       ├── visitors.py           # AST visitor pattern
│       ├── models.py             # Domain models
│       ├── serializer.py         # SPICE serialization
│       ├── comparison.py         # Netlist comparison tools
│       ├── roundtrip.py          # Round-trip validation
│       ├── exceptions.py         # Custom exceptions
│       ├── grammar.py            # SPICE grammar definition
│       ├── config.py             # Configuration management
│       ├── logging_config.py     # Logging configuration
│       └── cli/
│           ├── __init__.py       # CLI package
│           └── commands.py       # CLI command implementations
├── tests/                        # Unit tests
├── pyproject.toml               # Project configuration
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Development

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
# Lint and format code
ruff check src/ tests/
ruff format src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files
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
- Lark parser
- Pydantic (for configuration)
