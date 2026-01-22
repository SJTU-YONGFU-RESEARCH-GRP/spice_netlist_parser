"""Tests for mosfet_line utilities (PMOS/NMOS detection from raw lines)."""

from __future__ import annotations

import pytest

from spice_netlist_parser.mosfet_line import mosfet_type_from_line


class TestMosfetTypeFromLine:
    """Test mosfet_type_from_line using model-token-only rule."""

    def test_pmos_instance(self) -> None:
        """PMOS instance line returns (True, 'PMOS')."""
        line = "X_foo n1 n2 n3 n4 PMOS W=2u L=0.18u"
        ok, t = mosfet_type_from_line(line)
        assert ok is True
        assert t == "PMOS"

    def test_nmos_instance(self) -> None:
        """NMOS instance line returns (True, 'NMOS')."""
        line = "M_bar a b c d NMOS W=1u L=0.18u"
        ok, t = mosfet_type_from_line(line)
        assert ok is True
        assert t == "NMOS"

    def test_model_lines_skipped(self) -> None:
        """`.model` lines are not treated as MOSFET instances."""
        line = ".model NMOS NMOS (LEVEL=1 VTO=0.7)"
        ok, t = mosfet_type_from_line(line)
        assert ok is False
        assert t == ""

    def test_five_node_pmos(self) -> None:
        """5-node MOSFET: model at index 6, type from model token only."""
        line = "X_a n1 n2 n3 n4 n5 PMOS W=2u L=0.18u"
        ok, t = mosfet_type_from_line(line)
        assert ok is True
        assert t == "PMOS"

    def test_node_name_not_used_for_type(self) -> None:
        """A node that looks like NMOS/PMOS must not affect type."""
        line = "X_a n1 n2 n3 VDD PMOS W=2u L=0.18u"
        ok, t = mosfet_type_from_line(line)
        assert ok is True
        assert t == "PMOS"

    def test_short_line_not_mosfet(self) -> None:
        """Too few tokens -> not a MOSFET."""
        line = "X_foo n1 n2"
        ok, t = mosfet_type_from_line(line)
        assert ok is False
        assert t == ""

    def test_comment_skipped(self) -> None:
        """Comment line -> not a MOSFET."""
        ok, t = mosfet_type_from_line("* comment")
        assert ok is False
        assert t == ""

    def test_empty_skipped(self) -> None:
        """Empty line -> not a MOSFET."""
        ok, t = mosfet_type_from_line("")
        assert ok is False
        assert t == ""
