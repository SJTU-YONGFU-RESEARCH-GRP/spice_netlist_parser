"""Tests for SPICE serialization."""

from __future__ import annotations

from spice_netlist_parser.models import Component, ComponentType, Netlist
from spice_netlist_parser.serializer import SpiceSerializer, SpiceSerializerOptions


class TestSpiceSerializerOptions:
    """Test SpiceSerializerOptions class."""

    def test_default_options(self) -> None:
        """Test default serializer options."""
        options = SpiceSerializerOptions()
        assert options.include_title_line is True
        assert options.include_models is True
        assert options.include_options is True
        assert options.include_includes is True
        assert options.end_statement == ".END"

    def test_custom_options(self) -> None:
        """Test custom serializer options."""
        options = SpiceSerializerOptions(
            include_title_line=False,
            include_models=False,
            include_options=False,
            include_includes=False,
            end_statement=".FINISH",
        )
        assert options.include_title_line is False
        assert options.include_models is False
        assert options.include_options is False
        assert options.include_includes is False
        assert options.end_statement == ".FINISH"


class TestSpiceSerializer:
    """Test SpiceSerializer class."""

    def test_serialize_empty_netlist(self) -> None:
        """Test serializing an empty netlist."""
        netlist = Netlist(
            title="Empty Circuit", components=[], includes=[], options={}, models={}
        )
        serializer = SpiceSerializer()
        result = serializer.serialize(netlist)
        expected = "Empty Circuit\n.END\n"
        assert result == expected

    def test_serialize_without_title(self) -> None:
        """Test serializing without title line."""
        netlist = Netlist(
            title="Test Circuit", components=[], includes=[], options={}, models={}
        )
        options = SpiceSerializerOptions(include_title_line=False)
        serializer = SpiceSerializer(options)
        result = serializer.serialize(netlist)
        expected = ".END\n"
        assert result == expected

    def test_serialize_with_components(self) -> None:
        """Test serializing netlist with components."""
        comp1 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        comp2 = Component(
            name="C1",
            component_type=ComponentType.CAPACITOR,
            nodes=["1", "2"],
            parameters={"value": 1e-6},
        )
        netlist = Netlist(
            title="Test Circuit",
            components=[comp1, comp2],
            includes=[],
            options={},
            models={},
        )
        serializer = SpiceSerializer()
        result = serializer.serialize(netlist)

        lines = result.strip().split("\n")
        assert lines[0] == "Test Circuit"
        assert "R1 0 1 1000" in lines
        assert "C1 1 2 1e-06" in lines
        assert lines[-1] == ".END"

    def test_serialize_with_includes(self) -> None:
        """Test serializing netlist with includes."""
        netlist = Netlist(
            title="Test Circuit",
            components=[],
            includes=["models.sp", "subckt.sp"],
            options={},
            models={},
        )
        serializer = SpiceSerializer()
        result = serializer.serialize(netlist)

        lines = result.strip().split("\n")
        assert lines[0] == "Test Circuit"
        assert ".INCLUDE models.sp" in lines
        assert ".INCLUDE subckt.sp" in lines
        assert lines[-1] == ".END"

    def test_serialize_with_includes_disabled(self) -> None:
        """Test serializing with includes disabled."""
        netlist = Netlist(
            title="Test Circuit",
            components=[],
            includes=["models.sp"],
            options={},
            models={},
        )
        options = SpiceSerializerOptions(include_includes=False)
        serializer = SpiceSerializer(options)
        result = serializer.serialize(netlist)

        lines = result.strip().split("\n")
        assert ".INCLUDE" not in result
        assert lines[-1] == ".END"

    def test_serialize_with_options(self) -> None:
        """Test serializing netlist with options."""
        netlist = Netlist(
            title="Test Circuit",
            components=[],
            includes=[],
            options={"ABSTOL": 1e-12, "RELTOL": 1e-3},
            models={},
        )
        serializer = SpiceSerializer()
        result = serializer.serialize(netlist)

        lines = result.strip().split("\n")
        assert ".OPTION abstol=1e-12 reltol=0.001" in lines
        assert lines[-1] == ".END"

    def test_serialize_with_options_disabled(self) -> None:
        """Test serializing with options disabled."""
        netlist = Netlist(
            title="Test Circuit",
            components=[],
            includes=[],
            options={"ABSTOL": 1e-12},
            models={},
        )
        options = SpiceSerializerOptions(include_options=False)
        serializer = SpiceSerializer(options)
        result = serializer.serialize(netlist)

        assert ".OPTION" not in result
        assert result.endswith(".END\n")

    def test_serialize_with_models(self) -> None:
        """Test serializing netlist with models."""
        models = {
            "NMOS": {"type": "NMOS", "parameters": {"VTO": 0.7, "KP": 110e-6}},
            "PMOS": {"type": "PMOS", "parameters": {"VTO": -0.7}},
        }
        netlist = Netlist(
            title="Test Circuit", components=[], includes=[], options={}, models=models
        )
        serializer = SpiceSerializer()
        result = serializer.serialize(netlist)

        lines = result.strip().split("\n")
        assert "* Models" in lines
        assert ".MODEL NMOS NMOS (kp=0.00011 vto=0.7)" in lines
        assert ".MODEL PMOS PMOS (vto=-0.7)" in lines
        assert lines[-1] == ".END"

    def test_serialize_with_models_disabled(self) -> None:
        """Test serializing with models disabled."""
        models = {"NMOS": {"type": "NMOS", "parameters": {"VTO": 0.7}}}
        netlist = Netlist(
            title="Test Circuit", components=[], includes=[], options={}, models=models
        )
        options = SpiceSerializerOptions(include_models=False)
        serializer = SpiceSerializer(options)
        result = serializer.serialize(netlist)

        assert ".MODEL" not in result
        assert "* Models" not in result

    def test_serialize_component_with_model(self) -> None:
        """Test serializing component with model reference."""
        comp = Component(
            name="M1",
            component_type=ComponentType.MOSFET,
            nodes=["1", "2", "3", "4"],
            parameters={"L": 0.25, "W": 50.8},
            model="NMOS",
        )
        netlist = Netlist(
            title="Test Circuit", components=[comp], includes=[], options={}, models={}
        )
        serializer = SpiceSerializer()
        result = serializer.serialize(netlist)

        lines = result.strip().split("\n")
        assert "M1 1 2 3 4 NMOS l=0.25 w=50.8" in lines

    def test_serialize_title_with_comment(self) -> None:
        """Test serializing title that starts with comment marker."""
        netlist = Netlist(
            title="* Test Circuit", components=[], includes=[], options={}, models={}
        )
        serializer = SpiceSerializer()
        result = serializer.serialize(netlist)
        expected = "Test Circuit\n.END\n"
        assert result == expected

    def test_custom_end_statement(self) -> None:
        """Test custom end statement."""
        netlist = Netlist(
            title="Test Circuit", components=[], includes=[], options={}, models={}
        )
        options = SpiceSerializerOptions(end_statement=".FINISH")
        serializer = SpiceSerializer(options)
        result = serializer.serialize(netlist)
        assert result.endswith(".FINISH\n")
