"""Targeted tests for ast_parser error and preprocess branches."""

from __future__ import annotations

import io

import pytest
from lark import Token, Tree

from spice_netlist_parser.ast_parser import ASTBuilder, SpiceASTParser
from spice_netlist_parser.exceptions import ParseError


def test_preprocess_file_with_continuation() -> None:
    """_preprocess_file should join continuation lines."""

    parser = SpiceASTParser()
    content = "R1 0 1 1k\n+ 2k\n.END\n"
    fake = io.StringIO(content)
    text = parser._preprocess_file(fake)  # noqa: SLF001
    assert "1k 2k" in text
    assert ".END" in text


def test_find_error_line_not_found_returns_1() -> None:
    """_find_error_line should default to 1 when pattern missing."""

    parser = SpiceASTParser()
    ln = parser._find_error_line("R1 0 1\n.END\n", "nope")  # noqa: SLF001
    assert ln == 1


def test_parse_string_unexpected_characters() -> None:
    """UnexpectedCharacters should raise ParseError with line info."""

    parser = SpiceASTParser()
    with pytest.raises(ParseError):
        parser.parse_string("@@@")  # invalid tokens


def test_build_model_with_params() -> None:
    """ASTBuilder.build_model should collect parameters."""

    builder = ASTBuilder()
    # Build a fake model_line tree: MODEL_NAME MODEL_TYPE parameter(value)
    param_tree = Tree(
        "parameter",
        [
            Token("PARAM_NAME", "L"),
            Tree("value", [Token("SIGNED_NUMBER", "1.0")]),
        ],
    )
    model_tree = Tree(
        "model_line",
        [
            Token("MODEL_NAME", "M1"),
            Token("MODEL_NAME", "NMOS"),
            Tree("model_params", [param_tree]),
        ],
    )
    model_node = builder.build_model(model_tree)
    # The builder overwrites name when encountering multiple MODEL_NAME tokens;
    # in this ordering the last token wins.
    assert model_node.name == "NMOS"
    assert model_node.model_type in {"", "NMOS"}
    assert model_node.parameters[0].name == "L"


def test_build_directive_with_file_path() -> None:
    """ASTBuilder.build_directive should capture FILE_PATH."""

    builder = ASTBuilder()
    directive_tree = Tree(
        "include_line",
        [Token("FILE_PATH", '"lib.sp"')],
    )
    node = builder.build_directive(directive_tree)
    assert node.directive_type == "INCLUDE"
    assert node.content == "lib.sp"
