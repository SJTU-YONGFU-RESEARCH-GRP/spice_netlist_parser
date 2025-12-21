"""Additional coverage for ast_parser preprocess and helpers."""

from __future__ import annotations


import pytest

from lark import Token, Tree

from spice_netlist_parser.ast_parser import ASTBuilder, SpiceASTParser
from spice_netlist_parser.exceptions import ParseError


def test_preprocess_text_strips_comments_and_continuations() -> None:
    """_preprocess_text should drop comments and join continuations."""

    parser = SpiceASTParser()
    raw = "* title comment\nR1 0 1 1k\n+ 2k\n.END"
    cleaned = parser._preprocess_text(raw)  # noqa: SLF001
    assert "* title" not in cleaned
    assert "1k 2k" in cleaned
    assert cleaned.strip().endswith(".END")


def test_find_error_line_matches_string() -> None:
    """_find_error_line should return a line number when token text present."""

    parser = SpiceASTParser()
    text = "R1 0 1 1k\n.END\n"
    ln = parser._find_error_line(text, "1k")  # noqa: SLF001
    assert ln == 1


def test_parse_string_unexpected_characters() -> None:
    """parse_string should raise ParseError on bad characters."""

    parser = SpiceASTParser()
    with pytest.raises(ParseError):
        parser.parse_string("$$$")  # invalid tokens


def test_render_function_call_helper() -> None:
    """_render_function_call should build string from func_arg_list."""

    builder = ASTBuilder()
    func_tree = Tree(
        "function_call",
        [
            Token("MODEL_NAME", "SIN"),
            Tree(
                "func_arg_list",
                [Token("SIGNED_NUMBER", "0"), Token("SIGNED_NUMBER", "1")],
            ),
        ],
    )
    assert builder._render_function_call(func_tree) == "SIN(0 1)"  # noqa: SLF001
