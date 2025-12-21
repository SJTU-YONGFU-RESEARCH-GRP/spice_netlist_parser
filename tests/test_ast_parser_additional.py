"""Additional AST parser and visitor coverage."""

from __future__ import annotations


import pytest

from lark import Token, Tree

from spice_netlist_parser.ast_parser import ASTBuilder, SpiceASTParser
from spice_netlist_parser.ast_nodes import NodeType
from spice_netlist_parser.exceptions import ParseError
from spice_netlist_parser.visitors import NetlistTransformer


def test_build_value_handles_function_call_token() -> None:
    """ASTBuilder.build_value should accept FUNCTION_CALL tokens."""

    builder = ASTBuilder()
    # Manually construct a value tree with a FUNCTION_CALL token.

    tree = Tree("value", [Token("FUNCTION_CALL", "SIN(0 1 2)")])
    value_node = builder.build_value(tree)
    assert value_node.value == "SIN(0 1 2)"
    assert value_node.node_type == NodeType.VALUE


def test_build_value_handles_string_and_number_tokens() -> None:
    """build_value should parse numbers and strings."""

    builder = ASTBuilder()

    num_tree = Tree("value", [Token("SIGNED_NUMBER", "10")])
    str_tree = Tree("value", [Token("STRING", '"abc"')])

    num_val = builder.build_value(num_tree)
    str_val = builder.build_value(str_tree)

    assert num_val.value == 10.0  # noqa: PLR2004
    assert str_val.value == "abc"


def test_build_value_from_token_string_and_number() -> None:
    """_build_value_from_token should support string and number tokens."""

    builder = ASTBuilder()

    signed_number_node = builder._build_value_from_token(Token("SIGNED_NUMBER", "3.3"))  # noqa: SLF001
    string_node = builder._build_value_from_token(Token("STRING", '"abc"'))  # noqa: SLF001
    assert signed_number_node is not None
    assert string_node is not None
    assert signed_number_node.value == 3.3  # noqa: PLR2004
    assert string_node.value == '"abc"'


def test_parse_string_raises_parse_error() -> None:
    """parse_string should raise ParseError on invalid input."""

    parser = SpiceASTParser()
    with pytest.raises(ParseError):
        parser.parse_string("???")  # Invalid tokens should fail


def test_transform_visits_directives_and_models() -> None:
    """NetlistTransformer should collect includes/options/models."""

    parser = SpiceASTParser()
    text = '.INCLUDE "lib.sp"\n.END'
    ast = parser.parse_string(text)
    netlist = NetlistTransformer().transform(ast)

    assert "lib.sp" in netlist.includes
    assert netlist.models == {}
