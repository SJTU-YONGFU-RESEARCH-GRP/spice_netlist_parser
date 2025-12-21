"""Tests for netlist comparison functionality."""

from __future__ import annotations

from spice_netlist_parser.models import Component, ComponentType, Netlist
from spice_netlist_parser.comparison import (
    NetlistComparisonReport,
    NetlistVerification,
    compare_netlists,
    compute_stats,
    compute_verification,
    format_report_text,
)


class TestComparison:
    """Test comparison functionality."""

    def test_compare_identical_netlists(self) -> None:
        """Test comparing identical netlists."""
        comp = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        netlist1 = Netlist(
            title="Test Circuit", components=[comp], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Test Circuit", components=[comp], includes=[], options={}, models={}
        )

        differences = compare_netlists(netlist1, netlist2)
        assert differences == []

    def test_compare_different_titles(self) -> None:
        """Test comparing netlists with different titles."""
        comp = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        netlist1 = Netlist(
            title="Circuit 1", components=[comp], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Circuit 2", components=[comp], includes=[], options={}, models={}
        )

        differences = compare_netlists(netlist1, netlist2)
        assert len(differences) == 1
        assert "title:" in differences[0]

    def test_compare_different_components(self) -> None:
        """Test comparing netlists with different components."""
        comp1 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 1000.0},
        )
        comp2 = Component(
            name="R1",
            component_type=ComponentType.RESISTOR,
            nodes=["0", "1"],
            parameters={"value": 2000.0},  # Different value
        )
        netlist1 = Netlist(
            title="Test Circuit", components=[comp1], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Test Circuit", components=[comp2], includes=[], options={}, models={}
        )

        differences = compare_netlists(netlist1, netlist2)
        assert len(differences) == 1
        assert "parameters:" in differences[0]

    def test_compute_stats(self) -> None:
        """Test computing netlist statistics."""
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
            includes=["file1.sp"],
            options={"ABSTOL": 1e-12},
            models={"NMOS": {"type": "NMOS", "parameters": {"VTO": 0.7}}},
        )

        stats = compute_stats(netlist)
        assert stats.title == "Test Circuit"
        assert stats.components == 2  # noqa: PLR2004
        assert stats.nodes == 3  # noqa: PLR2004  # 0, 1, 2
        assert stats.models == 1
        assert stats.includes == 1
        assert stats.options == 1
        assert ComponentType.RESISTOR.value in stats.component_breakdown
        assert ComponentType.CAPACITOR.value in stats.component_breakdown

    def test_compute_verification(self) -> None:
        """Test computing verification statistics."""
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
        netlist1 = Netlist(
            title="Circuit", components=[comp1], includes=[], options={}, models={}
        )
        netlist2 = Netlist(
            title="Circuit",
            components=[comp1, comp2],
            includes=[],
            options={},
            models={},
        )

        verification = compute_verification(netlist1, netlist2)
        assert verification.components_left == 1
        assert verification.components_right == 2  # noqa: PLR2004

    def test_report_properties(self) -> None:
        """Test NetlistComparisonReport properties."""
        report = NetlistComparisonReport(
            left_path="file1.sp",
            right_path="file2.sp",
            left=compute_stats(
                Netlist(title="", components=[], includes=[], options={}, models={})
            ),
            right=compute_stats(
                Netlist(title="", components=[], includes=[], options={}, models={})
            ),
            verification=NetlistVerification(
                components_left=0,
                components_right=0,
                components_compared=0,
                missing_components=[],
                extra_components=[],
                components_with_type_diffs=0,
                components_with_node_diffs=0,
                components_with_model_diffs=0,
                components_with_parameter_diffs=0,
                includes_equal=True,
                options_equal=True,
                models_equal=True,
                connectivity_fingerprint_left="",
                connectivity_fingerprint_right="",
                sizing_fingerprint_left="",
                sizing_fingerprint_right="",
            ),
            differences=[],
        )

        assert report.is_equal is True
        assert len(report.differences) == 0

        # Test to_dict
        report_dict = report.to_dict()
        assert "left_path" in report_dict
        assert "right_path" in report_dict
        assert "differences" in report_dict

    def test_format_report_text(self) -> None:
        """Test formatting report as text."""
        report = NetlistComparisonReport(
            left_path="file1.sp",
            right_path="file2.sp",
            left=compute_stats(
                Netlist(title="", components=[], includes=[], options={}, models={})
            ),
            right=compute_stats(
                Netlist(title="", components=[], includes=[], options={}, models={})
            ),
            verification=NetlistVerification(
                components_left=0,
                components_right=0,
                components_compared=0,
                missing_components=[],
                extra_components=[],
                components_with_type_diffs=0,
                components_with_node_diffs=0,
                components_with_model_diffs=0,
                components_with_parameter_diffs=0,
                includes_equal=True,
                options_equal=True,
                models_equal=True,
                connectivity_fingerprint_left="",
                connectivity_fingerprint_right="",
                sizing_fingerprint_left="",
                sizing_fingerprint_right="",
            ),
            differences=["Component R1 has different value"],
        )

        text = format_report_text(report)
        assert "Netlist comparison" in text
        assert "file1.sp" in text
        assert "file2.sp" in text
        assert "Component R1 has different value" in text
        assert "Result:" in text
