"""Tests for comparing two SPICE files and generating a summary report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from spice_netlist_parser.comparison import compare_files, format_report_text

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


def test_compare_same_file_is_equal(examples_dir: Path) -> None:
    """Comparing a file against itself should yield an equal report."""

    left = examples_dir / "100.sp"
    report = compare_files(left, left)
    assert report.is_equal
    assert report.differences == []


def test_compare_produces_text_report(examples_dir: Path) -> None:
    """Text report should contain a summary section and a result line."""

    left = examples_dir / "100.sp"
    right = examples_dir / "1k.sp"
    report = compare_files(left, right)

    text = format_report_text(report, max_differences=5)
    assert "Netlist comparison" in text
    assert "Summary" in text
    assert "Result:" in text


def test_compare_produces_json_report(examples_dir: Path) -> None:
    """JSON report should be serializable and include required top-level keys."""

    left = examples_dir / "100.sp"
    right = examples_dir / "1k.sp"
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


