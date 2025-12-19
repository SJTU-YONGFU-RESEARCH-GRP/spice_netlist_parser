"""Round-trip validation utilities for conversion accuracy.

Round-trip validation checks that the parser is *stable* under a
parse -> serialize -> parse cycle:

1) Parse a SPICE input into a `Netlist`.
2) Serialize the `Netlist` back to SPICE text.
3) Parse the serialized SPICE again.
4) Compare the two `Netlist` objects using a canonical representation.

This is useful for catching:
- Non-determinism in parsing
- Loss of information in the internal model
- Serializer issues that produce unparsable or semantically different output

Important caveat:
This repository's parser intentionally ignores some statements (e.g. `.OP`)
when building the domain model. The round-trip comparison therefore validates
the *domain model*, not perfect textual equivalence of the original file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .models import Component, Netlist
from .parser import SpiceNetlistParser
from .serializer import SpiceSerializer, SpiceSerializerOptions


@dataclass(frozen=True, slots=True)
class RoundTripResult:
    """Result of a round-trip validation.

    Attributes:
        original: The first parsed netlist.
        serialized_spice: SPICE emitted from `original`.
        reparsed: The netlist produced from parsing `serialized_spice`.
    """

    original: Netlist
    serialized_spice: str
    reparsed: Netlist


class RoundTripMismatchError(AssertionError):
    """Raised when a round-trip comparison finds a mismatch."""


class RoundTripValidator:
    """Validate that parse -> serialize -> parse preserves the `Netlist` model."""

    def __init__(
        self,
        parser: SpiceNetlistParser | None = None,
        serializer: SpiceSerializer | None = None,
    ) -> None:
        """Initialize round-trip validator.

        Args:
            parser: Optional parser instance to reuse.
            serializer: Optional serializer instance to reuse.
        """

        self._parser = parser or SpiceNetlistParser()
        self._serializer = serializer or SpiceSerializer(SpiceSerializerOptions())

    def round_trip_string(self, netlist_text: str) -> RoundTripResult:
        """Perform a full round-trip on a netlist text.

        Args:
            netlist_text: SPICE netlist text.

        Returns:
            RoundTripResult containing the original parse, serialized text, and reparsed model.
        """

        original = self._parser.parse_string(netlist_text)
        serialized = self._serializer.serialize(original)
        reparsed = self._parser.parse_string(serialized)
        return RoundTripResult(original=original, serialized_spice=serialized, reparsed=reparsed)

    def assert_round_trip_string(self, netlist_text: str) -> RoundTripResult:
        """Round-trip a string and assert equivalence.

        Args:
            netlist_text: SPICE netlist text.

        Returns:
            RoundTripResult.

        Raises:
            RoundTripMismatchError: If the round-tripped netlist differs.
        """

        result = self.round_trip_string(netlist_text)
        self.assert_equivalent(result.original, result.reparsed, serialized_spice=result.serialized_spice)
        return result

    def assert_equivalent(
        self,
        a: Netlist,
        b: Netlist,
        *,
        serialized_spice: str | None = None,
        float_tol: float = 1e-12,
    ) -> None:
        """Assert that two `Netlist` models are semantically equivalent.

        Comparison is done on a canonical representation:
        - Components compared by name with stable ordering
        - Parameters compared as sorted key/value pairs
        - Floats compared using tolerance

        Args:
            a: First netlist.
            b: Second netlist.
            serialized_spice: Optional SPICE text used for reparsing (included in error message).
            float_tol: Absolute tolerance for float comparisons.

        Raises:
            RoundTripMismatchError: If a mismatch is found.
        """

        diffs = self.diff(a, b, float_tol=float_tol)
        if not diffs:
            return

        msg_lines: list[str] = ["Round-trip mismatch detected:"]
        msg_lines.extend(f"- {d}" for d in diffs[:25])
        if len(diffs) > 25:
            msg_lines.append(f"- ... {len(diffs) - 25} more differences")
        if serialized_spice is not None:
            msg_lines.append("\nSerialized SPICE (for repro):\n")
            msg_lines.append(serialized_spice)
        raise RoundTripMismatchError("\n".join(msg_lines))

    def diff(self, a: Netlist, b: Netlist, *, float_tol: float = 1e-12) -> list[str]:
        """Compute a list of differences between two netlists.

        Args:
            a: First netlist.
            b: Second netlist.
            float_tol: Absolute tolerance for float comparisons.

        Returns:
            List of human-readable difference strings.
        """

        diffs: list[str] = []

        # Title is not reliable across preprocess/serialization. Compare but don't fail hard?
        # We'll include it in diffs if it differs, since it can still indicate a bug.
        if (a.title or "").strip() != (b.title or "").strip():
            diffs.append(f"title: {a.title!r} != {b.title!r}")

        # Includes/options/models
        if sorted(a.includes) != sorted(b.includes):
            diffs.append(f"includes: {sorted(a.includes)!r} != {sorted(b.includes)!r}")

        if not self._mapping_equivalent(a.options, b.options, float_tol=float_tol):
            diffs.append(f"options: {a.options!r} != {b.options!r}")

        if not self._models_equivalent(a.models, b.models, float_tol=float_tol):
            diffs.append("models: models differ")

        # Components
        a_by_name = {c.name: c for c in a.components}
        b_by_name = {c.name: c for c in b.components}
        a_names = set(a_by_name.keys())
        b_names = set(b_by_name.keys())

        missing = sorted(a_names - b_names)
        extra = sorted(b_names - a_names)
        if missing:
            diffs.append(f"components missing after round-trip: {missing!r}")
        if extra:
            diffs.append(f"components added after round-trip: {extra!r}")

        for name in sorted(a_names & b_names):
            ca = a_by_name[name]
            cb = b_by_name[name]
            comp_diffs = self._diff_component(ca, cb, float_tol=float_tol)
            diffs.extend(f"component[{name}]: {d}" for d in comp_diffs)

        return diffs

    @staticmethod
    def _diff_component(a: Component, b: Component, *, float_tol: float) -> list[str]:
        """Diff two components.

        Args:
            a: First component.
            b: Second component.
            float_tol: Absolute tolerance for float comparisons.

        Returns:
            List of difference strings.
        """

        diffs: list[str] = []
        if a.component_type != b.component_type:
            diffs.append(f"type: {a.component_type!r} != {b.component_type!r}")
        if list(a.nodes) != list(b.nodes):
            diffs.append(f"nodes: {a.nodes!r} != {b.nodes!r}")
        if (a.model or None) != (b.model or None):
            diffs.append(f"model: {a.model!r} != {b.model!r}")
        if not RoundTripValidator._mapping_equivalent(a.parameters, b.parameters, float_tol=float_tol):
            diffs.append(f"parameters: {a.parameters!r} != {b.parameters!r}")
        return diffs

    @staticmethod
    def _mapping_equivalent(
        a: Mapping[str, Any],
        b: Mapping[str, Any],
        *,
        float_tol: float,
    ) -> bool:
        """Check mapping equivalence with float tolerance.

        Args:
            a: First mapping.
            b: Second mapping.
            float_tol: Absolute tolerance for float comparisons.

        Returns:
            True if equivalent.
        """

        if set(a.keys()) != set(b.keys()):
            return False
        for k in a.keys():
            if not RoundTripValidator._value_equivalent(a[k], b[k], float_tol=float_tol):
                return False
        return True

    @staticmethod
    def _models_equivalent(
        a: Mapping[str, Mapping[str, Any]],
        b: Mapping[str, Mapping[str, Any]],
        *,
        float_tol: float,
    ) -> bool:
        """Check model dictionaries equivalence.

        Args:
            a: First models mapping.
            b: Second models mapping.
            float_tol: Absolute tolerance for float comparisons.

        Returns:
            True if equivalent.
        """

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
                if not RoundTripValidator._mapping_equivalent(pa, pb, float_tol=float_tol):
                    return False
            else:
                if pa != pb:
                    return False
        return True

    @staticmethod
    def _value_equivalent(a: Any, b: Any, *, float_tol: float) -> bool:
        """Compare values with float tolerance.

        Args:
            a: First value.
            b: Second value.
            float_tol: Absolute tolerance.

        Returns:
            True if equivalent.
        """

        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(float(a) - float(b)) <= float_tol
        return a == b


