"""Serialization utilities for SPICE netlists.

This module provides a minimal serializer that converts the internal `Netlist`
domain model back into a SPICE-like textual representation that can be parsed
again by this project's grammar.

Notes:
- The parser strips `*` comment lines during preprocessing, so the serializer
  intentionally emits a plain title line (not a comment).
- The grammar requires a final `.END`.
- This serializer targets *semantic* round-tripping for this repository's
  `Netlist` model, not faithful reproduction of original formatting.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import Component, Netlist


@dataclass(frozen=True, slots=True)
class SpiceSerializerOptions:
    """Options controlling SPICE serialization.

    Attributes:
        include_title_line: If True, write `netlist.title` as the first line.
        include_models: If True, write `.MODEL` statements for `netlist.models`.
        include_options: If True, write `.OPTION` statement for `netlist.options`.
        include_includes: If True, write `.INCLUDE` statements for `netlist.includes`.
        end_statement: The final terminator statement (default: `.END`).
    """

    include_title_line: bool = True
    include_models: bool = True
    include_options: bool = True
    include_includes: bool = True
    end_statement: str = ".END"


class SpiceSerializer:
    """Serialize a parsed `Netlist` back to SPICE text.

    The output is designed to be parseable by this project's grammar so it can
    be used for round-trip validation (parse -> serialize -> parse).
    """

    def __init__(self, options: SpiceSerializerOptions | None = None) -> None:
        """Initialize serializer.

        Args:
            options: Optional serializer options.
        """

        self._options = options or SpiceSerializerOptions()

    def serialize(self, netlist: Netlist) -> str:  # noqa: PLR0912
        """Serialize a `Netlist` into SPICE text.

        Args:
            netlist: Netlist domain model.

        Returns:
            A SPICE netlist string that should be parseable by this project.
        """

        lines: list[str] = []

        if self._options.include_title_line:
            title = (netlist.title or "Untitled").strip()
            # Parser strips comment lines, so do not emit a leading `*`.
            if title.startswith("*"):
                title = title.lstrip("*").strip() or "Untitled"
            lines.append(title)

        if self._options.include_includes:
            for include in netlist.includes:
                include_path = str(include).strip()
                if not include_path:
                    continue
                # Quote if it contains whitespace.
                if any(ch.isspace() for ch in include_path):
                    include_path = f'"{include_path}"'
                lines.append(f".INCLUDE {include_path}")

        if self._options.include_options and netlist.options:
            opt_parts = self._format_kv_params(netlist.options)
            if opt_parts:
                lines.append(".OPTION " + " ".join(opt_parts))

        # Components
        lines.extend(self._serialize_component(comp) for comp in netlist.components)

        if self._options.include_models and netlist.models:
            lines.append("* Models")
            for model_name in sorted(netlist.models.keys()):
                model_data = netlist.models.get(model_name, {})
                model_type = str(model_data.get("type", "")).strip() or "N/A"
                params = model_data.get("parameters", {})
                param_parts: list[str] = []
                if isinstance(params, Mapping):
                    param_parts = self._format_kv_params(params)
                # Parentheses are accepted by the grammar.
                if param_parts:
                    lines.append(
                        f".MODEL {model_name} {model_type} ({' '.join(param_parts)})"
                    )
                else:
                    lines.append(f".MODEL {model_name} {model_type}")

        lines.append(self._options.end_statement)

        # Ensure final newline for nicer CLI output and deterministic file writes.
        return "\n".join(lines).rstrip() + "\n"

    def _serialize_component(self, comp: Component) -> str:
        """Serialize a single component.

        Args:
            comp: Component to serialize.

        Returns:
            SPICE component line.
        """

        # Node list
        node_str = " ".join(str(n) for n in comp.nodes)

        # Component body:
        # - optional model name
        # - optional bare value token (for passives like R/C/L)
        # - followed by parameters (key=value)
        body_parts: list[str] = []
        if comp.model:
            body_parts.append(str(comp.model))

        # Emit a bare value token first when present. This keeps the output
        # SPICE-like (e.g. `R1 n1 n2 10k`) while still being parseable.
        params = dict(comp.parameters) if comp.parameters else {}
        value_token = None
        if "value" in params:
            value_token = params.pop("value")
        if value_token is not None:
            body_parts.append(self._format_value(value_token))

        # Emit remaining parameters in stable order.
        if params:
            body_parts.extend(self._format_kv_params(params))

        if body_parts:
            return f"{comp.name} {node_str} " + " ".join(body_parts)
        return f"{comp.name} {node_str}"

    @staticmethod
    def _format_kv_params(params: Mapping[str, Any]) -> list[str]:
        """Format a mapping into sorted `key=value` tokens.

        Args:
            params: Parameter mapping.

        Returns:
            Sorted list of `key=value` tokens.
        """

        return [
            f"{str(key).lower()}={SpiceSerializer._format_value(params[key])}"
            for key in sorted(params.keys(), key=lambda s: str(s).lower())
        ]

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format values into a token acceptable by the grammar.

        Args:
            value: Parameter value.

        Returns:
            String token.
        """

        if value is None:
            return "0"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, int | float):
            # Use a compact format; keep scientific notation when needed.
            return format(float(value), ".12g")
        s = str(value)
        # Preserve function call tokens like SIN(0 1 2) as-is.
        # Quote if it contains whitespace.
        if any(ch.isspace() for ch in s):
            return f'"{s}"'
        # Strip surrounding quotes to avoid double quoting.
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':  # noqa: PLR2004
            return s[1:-1]
        return s
