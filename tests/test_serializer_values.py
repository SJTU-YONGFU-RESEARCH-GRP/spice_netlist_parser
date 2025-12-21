"""Serializer value-formatting coverage."""

from __future__ import annotations


from spice_netlist_parser.models import Component, ComponentType
from spice_netlist_parser.serializer import SpiceSerializer


def test_format_value_handles_none_bool_and_spaces() -> None:
    """_format_value should normalize special cases."""

    fmt = SpiceSerializer._format_value  # noqa: SLF001

    assert fmt(None) == "0"
    assert fmt(True) == "1"
    assert fmt(False) == "0"
    assert fmt("has space") == '"has space"'
    assert fmt('"quoted"') == "quoted"


def test_format_kv_params_sorts_keys() -> None:
    """_format_kv_params should sort keys and lower them."""

    tokens = SpiceSerializer._format_kv_params({"B": 2, "a": 1})  # noqa: SLF001
    assert tokens == ["a=1", "b=2"]


def test_serialize_component_with_value_and_params() -> None:
    """_serialize_component should place value before other params."""

    comp = Component(
        name="R1",
        component_type=ComponentType.RESISTOR,
        nodes=["0", "1"],
        parameters={"value": 10, "foo": "bar"},
        model="RMODEL",
    )
    text = SpiceSerializer()._serialize_component(comp)  # noqa: SLF001
    assert text.startswith("R1 0 1 RMODEL 10")
    assert "foo=bar" in text
