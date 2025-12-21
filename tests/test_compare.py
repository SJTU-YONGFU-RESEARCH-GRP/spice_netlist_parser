"""Tests for comparing two SPICE files and generating a summary report."""

from __future__ import annotations

from typing import TYPE_CHECKING

import json
import pytest

if TYPE_CHECKING:
    from pathlib import Path
from spice_netlist_parser.comparison import compare_files, format_report_text


@pytest.fixture()
def temp_netlist(tmp_path: Path) -> Path:
    """Create a simple temporary netlist file."""

    path = tmp_path / "simple.sp"
    path.write_text("R1 0 1 1000\n.END\n", encoding="utf-8")
    return path


def test_compare_same_file_is_equal(temp_netlist: Path) -> None:
    """Comparing a file against itself should yield an equal report."""

    report = compare_files(temp_netlist, temp_netlist)
    assert report.is_equal
    assert report.differences == []


def test_compare_produces_text_report(temp_netlist: Path, tmp_path: Path) -> None:
    """Text report should contain a summary section and a result line."""

    left = temp_netlist
    right = tmp_path / "right.sp"
    right.write_text("Test\nR1 0 1 2000\n.END\n", encoding="utf-8")
    report = compare_files(left, right)

    text = format_report_text(report, max_differences=5)
    assert "Netlist comparison" in text
    assert "Summary" in text
    assert "Result:" in text


def test_compare_produces_json_report(temp_netlist: Path, tmp_path: Path) -> None:
    """JSON report should be serializable and include required top-level keys."""

    left = temp_netlist
    right = tmp_path / "right.sp"
    right.write_text("Test\nR1 0 1 2000\n.END\n", encoding="utf-8")
    report = compare_files(left, right)
    payload = report.to_dict()

    encoded = json.dumps(payload, default=str)
    decoded = json.loads(encoded)
    assert "left_path" in decoded
    assert "right_path" in decoded
    assert "left" in decoded
    assert "right" in decoded
    assert "verification" in decoded
    assert "differences" in decoded
