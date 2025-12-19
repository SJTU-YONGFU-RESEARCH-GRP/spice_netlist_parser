"""Compare two SPICE netlists and produce a summary report.

This module is intended for conversion-accuracy workflows:
- Compare an original `.sp` against a generated `.sp` (e.g., round-trip output)
- Compare two different netlists for structural/semantic differences

Comparison is performed on the parsed `Netlist` domain model, not on raw text.
This makes the comparison resilient to formatting differences (whitespace,
line wrapping) while still detecting meaningful semantic changes.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .models import Component, Netlist
from .parser import SpiceNetlistParser
from .roundtrip import RoundTripValidator


@dataclass(frozen=True, slots=True)
class NetlistStats:
    """Summary statistics for a netlist."""

    title: str
    components: int
    nodes: int
    models: int
    includes: int
    options: int
    component_breakdown: Dict[str, int]


@dataclass(frozen=True, slots=True)
class NetlistVerification:
    """What was verified when comparing two netlists.

    This makes the report explicit about *connectivity* (node lists/order) and
    *sizing/parameters* (e.g., MOSFET L/W, component values).
    """

    components_left: int
    components_right: int
    components_compared: int
    missing_components: List[str]
    extra_components: List[str]
    components_with_type_diffs: int
    components_with_node_diffs: int
    components_with_model_diffs: int
    components_with_parameter_diffs: int
    includes_equal: bool
    options_equal: bool
    models_equal: bool
    connectivity_fingerprint_left: str
    connectivity_fingerprint_right: str
    sizing_fingerprint_left: str
    sizing_fingerprint_right: str


@dataclass(frozen=True, slots=True)
class NetlistComparisonReport:
    """Report describing differences between two parsed netlists."""

    left_path: str
    right_path: str
    left: NetlistStats
    right: NetlistStats
    verification: NetlistVerification
    differences: List[str]

    @property
    def is_equal(self) -> bool:
        """Whether the two netlists are semantically equivalent."""

        return len(self.differences) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to a JSON-serializable dict."""

        return asdict(self)


def compute_stats(netlist: Netlist) -> NetlistStats:
    """Compute summary statistics for a parsed netlist.

    Args:
        netlist: Parsed netlist.

    Returns:
        Summary statistics.
    """

    breakdown: Dict[str, int] = {}
    for comp in netlist.components:
        key = comp.component_type.value
        breakdown[key] = breakdown.get(key, 0) + 1

    return NetlistStats(
        title=netlist.title,
        components=len(netlist.components),
        nodes=len(netlist.nodes),
        models=len(netlist.models),
        includes=len(netlist.includes),
        options=len(netlist.options),
        component_breakdown=dict(sorted(breakdown.items())),
    )

def _format_param_value(value: Any) -> str:
    """Format a parameter value into a stable string for fingerprinting.

    Args:
        value: Parameter value.

    Returns:
        Stable string representation.
    """

    if value is None:
        return "0"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return format(float(value), ".12g")
    return str(value)


def _fingerprint_connectivity(netlist: Netlist) -> str:
    """Fingerprint component connectivity (names, types, node order).

    Args:
        netlist: Parsed netlist.

    Returns:
        Short stable fingerprint string.
    """

    parts: List[str] = []
    for comp in sorted(netlist.components, key=lambda c: c.name):
        parts.append(f"{comp.name}|{comp.component_type.value}|{' '.join(comp.nodes)}")
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:12]


def _fingerprint_sizing(netlist: Netlist) -> str:
    """Fingerprint sizing/parameters (names, types, model, params).

    Args:
        netlist: Parsed netlist.

    Returns:
        Short stable fingerprint string.
    """

    parts: List[str] = []
    for comp in sorted(netlist.components, key=lambda c: c.name):
        param_parts = []
        for k in sorted(comp.parameters.keys(), key=lambda s: str(s).lower()):
            param_parts.append(f"{str(k).lower()}={_format_param_value(comp.parameters[k])}")
        model = comp.model or ""
        parts.append(
            f"{comp.name}|{comp.component_type.value}|model={model}|{' '.join(param_parts)}"
        )
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:12]


def _mapping_equivalent(a: Mapping[str, Any], b: Mapping[str, Any], *, float_tol: float) -> bool:
    """Mapping equivalence with float tolerance."""

    if set(a.keys()) != set(b.keys()):
        return False
    for k in a.keys():
        va = a[k]
        vb = b[k]
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            if abs(float(va) - float(vb)) > float_tol:
                return False
        else:
            if va != vb:
                return False
    return True


def _models_equivalent(
    a: Mapping[str, Mapping[str, Any]],
    b: Mapping[str, Mapping[str, Any]],
    *,
    float_tol: float,
) -> bool:
    """Model dict equivalence with float tolerance."""

    if set(a.keys()) != set(b.keys()):
        return False
    for model_name in a.keys():
        ma = a[model_name]
        mb = b[model_name]
        if str(ma.get("type", "")).strip() != str(mb.get("type", "")).strip():
            return False
        pa = ma.get("parameters", {})
        pb = mb.get("parameters", {})
        if isinstance(pa, Mapping) and isinstance(pb, Mapping):
            if not _mapping_equivalent(pa, pb, float_tol=float_tol):
                return False
        else:
            if pa != pb:
                return False
    return True


def compute_verification(
    left: Netlist,
    right: Netlist,
    *,
    float_tol: float = 1e-12,
) -> NetlistVerification:
    """Compute explicit connectivity/sizing verification metadata.

    Args:
        left: Left netlist.
        right: Right netlist.
        float_tol: Absolute tolerance for float comparisons.

    Returns:
        Verification metadata.
    """

    left_by = {c.name: c for c in left.components}
    right_by = {c.name: c for c in right.components}
    left_names = set(left_by.keys())
    right_names = set(right_by.keys())

    missing = sorted(left_names - right_names)
    extra = sorted(right_names - left_names)
    common = sorted(left_names & right_names)

    type_diffs = 0
    node_diffs = 0
    model_diffs = 0
    param_diffs = 0
    for name in common:
        a = left_by[name]
        b = right_by[name]
        if a.component_type != b.component_type:
            type_diffs += 1
        if list(a.nodes) != list(b.nodes):
            node_diffs += 1
        if (a.model or None) != (b.model or None):
            model_diffs += 1
        if not _mapping_equivalent(a.parameters, b.parameters, float_tol=float_tol):
            param_diffs += 1

    return NetlistVerification(
        components_left=len(left.components),
        components_right=len(right.components),
        components_compared=len(common),
        missing_components=missing,
        extra_components=extra,
        components_with_type_diffs=type_diffs,
        components_with_node_diffs=node_diffs,
        components_with_model_diffs=model_diffs,
        components_with_parameter_diffs=param_diffs,
        includes_equal=sorted(left.includes) == sorted(right.includes),
        options_equal=_mapping_equivalent(left.options, right.options, float_tol=float_tol),
        models_equal=_models_equivalent(left.models, right.models, float_tol=float_tol),
        connectivity_fingerprint_left=_fingerprint_connectivity(left),
        connectivity_fingerprint_right=_fingerprint_connectivity(right),
        sizing_fingerprint_left=_fingerprint_sizing(left),
        sizing_fingerprint_right=_fingerprint_sizing(right),
    )


def compare_netlists(
    left: Netlist,
    right: Netlist,
    *,
    float_tol: float = 1e-12,
) -> List[str]:
    """Compare two parsed netlists and return a list of differences.

    Args:
        left: Left-hand netlist.
        right: Right-hand netlist.
        float_tol: Absolute tolerance for float comparisons.

    Returns:
        List of human-readable difference strings.
    """

    validator = RoundTripValidator()
    return validator.diff(left, right, float_tol=float_tol)


def compare_files(
    left_path: Path,
    right_path: Path,
    *,
    parser: Optional[SpiceNetlistParser] = None,
    float_tol: float = 1e-12,
) -> NetlistComparisonReport:
    """Parse and compare two SPICE files.

    Args:
        left_path: Path to first SPICE file.
        right_path: Path to second SPICE file.
        parser: Optional parser instance to reuse.
        float_tol: Absolute tolerance for float comparisons.

    Returns:
        Comparison report.
    """

    p = parser or SpiceNetlistParser()
    left = p.parse_file(left_path)
    right = p.parse_file(right_path)
    diffs = compare_netlists(left, right, float_tol=float_tol)
    verification = compute_verification(left, right, float_tol=float_tol)
    return NetlistComparisonReport(
        left_path=str(left_path),
        right_path=str(right_path),
        left=compute_stats(left),
        right=compute_stats(right),
        verification=verification,
        differences=diffs,
    )


def format_report_text(
    report: NetlistComparisonReport,
    *,
    max_differences: int = 50,
) -> str:
    """Format a comparison report as human-readable text.

    Args:
        report: Comparison report.
        max_differences: Maximum number of difference lines to print.

    Returns:
        Formatted report text.
    """

    def fmt_breakdown(b: Mapping[str, int]) -> str:
        if not b:
            return "none"
        return ", ".join(f"{k}:{v}" for k, v in b.items())

    lines: List[str] = []
    lines.append("Netlist comparison")
    lines.append("==================")
    lines.append(f"Left : {report.left_path}")
    lines.append(f"Right: {report.right_path}")
    lines.append("")
    lines.append("Summary")
    lines.append("-------")
    lines.append(
        f"Left : comps={report.left.components}, nodes={report.left.nodes}, "
        f"models={report.left.models}, includes={report.left.includes}, options={report.left.options}"
    )
    lines.append(f"       breakdown: {fmt_breakdown(report.left.component_breakdown)}")
    lines.append(
        f"Right: comps={report.right.components}, nodes={report.right.nodes}, "
        f"models={report.right.models}, includes={report.right.includes}, options={report.right.options}"
    )
    lines.append(f"       breakdown: {fmt_breakdown(report.right.component_breakdown)}")
    lines.append("")

    lines.append("Connectivity & sizing verification")
    lines.append("---------------------------------")
    lines.append(
        f"Compared {report.verification.components_compared} component(s) by name "
        f"(left={report.verification.components_left}, right={report.verification.components_right})"
    )
    lines.append(
        f"Missing: {len(report.verification.missing_components)}, "
        f"Extra: {len(report.verification.extra_components)}"
    )
    lines.append(
        "Connectivity (type+node order) fingerprint: "
        f"{report.verification.connectivity_fingerprint_left} vs "
        f"{report.verification.connectivity_fingerprint_right}"
    )
    lines.append(
        "Sizing/params (model+params) fingerprint: "
        f"{report.verification.sizing_fingerprint_left} vs "
        f"{report.verification.sizing_fingerprint_right}"
    )
    lines.append(
        f"Per-component diffs: type={report.verification.components_with_type_diffs}, "
        f"nodes={report.verification.components_with_node_diffs}, "
        f"model={report.verification.components_with_model_diffs}, "
        f"params={report.verification.components_with_parameter_diffs}"
    )
    lines.append("")

    if report.is_equal:
        lines.append("Result: ✅ equivalent (connectivity + sizing/params match)")
        return "\n".join(lines) + "\n"

    lines.append(f"Result: ❌ different ({len(report.differences)} difference(s))")
    lines.append("")
    lines.append("Differences (first {n})".format(n=min(max_differences, len(report.differences))))
    lines.append("---------------------")
    for d in report.differences[:max_differences]:
        lines.append(f"- {d}")
    if len(report.differences) > max_differences:
        lines.append(f"- ... {len(report.differences) - max_differences} more")
    return "\n".join(lines) + "\n"


