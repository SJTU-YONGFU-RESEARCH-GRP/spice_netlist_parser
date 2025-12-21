"""Round-trip validation tests.

These tests ensure the library is stable under a parse -> serialize -> parse
cycle for the bundled example netlists.
"""

from __future__ import annotations


import pytest
from spice_netlist_parser import RoundTripValidator, SpiceNetlistParser


@pytest.fixture()
def sample_netlist() -> str:
    """Provide a small sample netlist for round-trip tests."""

    return "Test\\nR1 0 1 1000\\nC1 1 2 1e-6\\n.END\\n"


@pytest.fixture()
def validator() -> RoundTripValidator:
    """Create a round-trip validator instance."""

    return RoundTripValidator()


def test_round_trip_examples(validator: RoundTripValidator) -> None:
    """Round-trip a small sample netlist."""

    netlist = "R1 0 1 1000\nC1 1 2 1e-6\n.END\n"
    validator.assert_round_trip_string(netlist)


def test_round_trip_is_parseable(validator: RoundTripValidator) -> None:
    """Ensure serialized output always contains `.END` and is parseable."""

    netlist = "R1 0 1 1000\nC1 1 2 1e-6\n.END\n"
    result = validator.round_trip_string(netlist)

    assert (
        ".END" in result.serialized_spice.splitlines()[-1]
    ), "Serialized netlist must end with .END"


EXPECTED_PASSIVE_NODE_COUNT = 2


def test_values_not_in_nodes() -> None:
    """Ensure 2-node passives store their value in parameters, not as a node token."""

    parser = SpiceNetlistParser()
    netlist = parser.parse_string("R1 0 1 1000\nC1 1 2 1e-6\n.END\n")

    for comp in netlist.components:
        if comp.component_type.value in {"R", "C", "L"}:
            assert (
                len(comp.nodes) == EXPECTED_PASSIVE_NODE_COUNT
            ), f"{comp.name} should have exactly {EXPECTED_PASSIVE_NODE_COUNT} connectivity nodes"
            assert (
                "value" in comp.parameters
            ), f"{comp.name} should have its value in parameters['value']"
