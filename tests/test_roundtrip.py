"""Round-trip validation tests.

These tests ensure the library is stable under a parse -> serialize -> parse
cycle for the bundled example netlists.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from spice_netlist_parser import RoundTripValidator

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


@pytest.fixture
def project_root() -> Path:
    """Return repository root directory."""

    return Path(__file__).resolve().parent.parent


@pytest.fixture
def examples_dir(project_root: Path) -> Path:
    """Return examples directory."""

    return project_root / "examples"


@pytest.fixture
def validator() -> RoundTripValidator:
    """Create a round-trip validator instance."""

    return RoundTripValidator()


def test_round_trip_examples(validator: RoundTripValidator, examples_dir: Path) -> None:
    """Round-trip all bundled `examples/*.sp` fixtures."""

    example_files = sorted(examples_dir.glob("*.sp"))
    assert example_files, "No example SPICE files found under examples/"

    for path in example_files:
        text = path.read_text(encoding="utf-8")
        # Assert round-trip equivalence; error messages include the serialized SPICE.
        validator.assert_round_trip_string(text)


def test_round_trip_is_parseable(validator: RoundTripValidator, examples_dir: Path) -> None:
    """Ensure serialized output always contains `.END` and is parseable."""

    path = examples_dir / "100.sp"
    text = path.read_text(encoding="utf-8")
    result = validator.round_trip_string(text)

    assert ".END" in result.serialized_spice.splitlines()[-1], "Serialized netlist must end with .END"


def test_values_not_in_nodes(examples_dir: Path) -> None:
    """Ensure 2-node passives store their value in parameters, not as a node token."""

    from spice_netlist_parser import SpiceNetlistParser

    parser = SpiceNetlistParser()
    netlist = parser.parse_file(examples_dir / "100.sp")

    for comp in netlist.components:
        if comp.component_type.value in {"R", "C", "L"}:
            assert len(comp.nodes) == 2, f"{comp.name} should have exactly 2 connectivity nodes"
            assert "value" in comp.parameters, f"{comp.name} should have its value in parameters['value']"


