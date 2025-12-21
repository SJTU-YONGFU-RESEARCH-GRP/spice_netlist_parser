"""Additional visitor coverage."""

from __future__ import annotations

from typing import Any

from spice_netlist_parser.ast_nodes import (
    DirectiveNode,
    NodeType,
    ParameterNode,
    ValueNode,
)
from spice_netlist_parser.visitors import NetlistTransformer


def _param(name: str, value: Any) -> ParameterNode:
    """Helper to create a ParameterNode."""

    return ParameterNode(
        node_type=NodeType.PARAMETER,
        line_number=1,
        position=0,
        name=name,
        value=ValueNode(NodeType.VALUE, 1, 0, value=value, unit=None),
    )


def test_visit_directive_option_param_and_default() -> None:
    """NetlistTransformer should handle OPTION, PARAM, and unknown directives."""

    transformer = NetlistTransformer()

    option_node = DirectiveNode(
        node_type=NodeType.DIRECTIVE,
        line_number=1,
        position=0,
        directive_type="OPTION",
        parameters=[_param("TEMP", 25)],
        content=None,
    )
    param_node = DirectiveNode(
        node_type=NodeType.DIRECTIVE,
        line_number=1,
        position=0,
        directive_type="PARAM",
        parameters=[_param("FOO", "BAR")],
        content=None,
    )
    unknown_node = DirectiveNode(
        node_type=NodeType.DIRECTIVE,
        line_number=1,
        position=0,
        directive_type="UNKNOWN",
        parameters=[],
        content=None,
    )

    opt = transformer.visit_directive(option_node)
    prm = transformer.visit_directive(param_node)
    unk = transformer.visit_directive(unknown_node)

    assert opt["option"]["temp"] == 25  # noqa: PLR2004
    assert prm["param"]["foo"] == "BAR"
    assert unk == {}
