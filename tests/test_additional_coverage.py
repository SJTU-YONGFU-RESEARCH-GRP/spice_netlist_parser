"""Extra coverage for edge-case branches across modules."""

from __future__ import annotations

import runpy
import warnings
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from spice_netlist_parser import config
from spice_netlist_parser.ast_nodes import (
    ASTNode,
    ComponentNode,
    DirectiveNode,
    ModelNode,
    NetlistNode,
    NodeType,
    ParameterNode,
    ValueNode,
)
from spice_netlist_parser.ast_parser import SpiceASTParser
from spice_netlist_parser.comparison import (
    NetlistComparisonReport,
    NetlistStats,
    NetlistVerification,
    _format_param_value,
    _models_equivalent,
    format_report_text,
)
from spice_netlist_parser.models import Component, ComponentType, Netlist
from spice_netlist_parser import main as cli_main
from spice_netlist_parser.cli import commands as cli_commands
from spice_netlist_parser.parser import SpiceNetlistParser
from spice_netlist_parser.roundtrip import RoundTripMismatchError, RoundTripValidator
from spice_netlist_parser.serializer import SpiceSerializer, SpiceSerializerOptions
from spice_netlist_parser.visitors import NetlistTransformer

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


def test_ast_node_accepts_default_fallback() -> None:
    """ASTNode.accept should call visit_default when no specific method exists."""

    called: list[NodeType] = []

    class DummyVisitor:
        def visit_default(self, node: ASTNode) -> str:
            called.append(node.node_type)
            return "fallback"

    node = ASTNode(node_type=NodeType.NETLIST, line_number=1, position=0)
    result = node.accept(DummyVisitor())

    assert result == "fallback"
    assert called == [NodeType.NETLIST]


def test_preprocess_text_skips_title_line() -> None:
    """_preprocess_text should drop a leading title line without a designator."""

    parser = SpiceASTParser()
    raw = "Example circuit title\nR1 0 1 10k\n.END"

    cleaned = parser._preprocess_text(raw)  # noqa: SLF001
    lines = cleaned.splitlines()

    assert lines[0].startswith("R1")
    assert "Example circuit title" not in cleaned


def test_parse_string_fast_component_path() -> None:
    """parse_string should use the fast component-only path when possible."""

    parser = SpiceASTParser()
    text = "R1 0 1 1k\nC1 1 0 1u"

    ast = parser.parse_string(text)
    assert ast.title == "Untitled"
    assert len(ast.statements) == 2  # noqa: PLR2004
    assert {
        stmt.name for stmt in ast.statements if isinstance(stmt, ComponentNode)
    } == {
        "R1",
        "C1",
    }


def test_strip_inline_comment_preserves_strings() -> None:
    """_strip_inline_comment should ignore semicolons inside quoted strings."""

    parser = SpiceASTParser()
    line = 'V1 0 1 "1;2"; real comment'
    stripped = parser._strip_inline_comment(line)  # noqa: SLF001

    assert stripped == 'V1 0 1 "1;2"'


def test_comparison_helpers_cover_value_and_models() -> None:
    """Comparison helpers should handle diverse parameter shapes."""

    assert _format_param_value(None) == "0"
    assert _format_param_value(True) == "1"
    assert _format_param_value(1.25) == "1.25"
    assert _format_param_value("raw") == "raw"

    models_a = {"m": {"type": "nmos", "parameters": {"w": 1}}}
    models_b = {"m": {"type": "nmos", "parameters": "raw"}}
    assert _models_equivalent(models_a, models_a, float_tol=1e-12)
    assert not _models_equivalent(models_a, models_b, float_tol=1e-12)


def test_format_report_text_equal_and_truncated_differences() -> None:
    """format_report_text should handle equal and truncated difference outputs."""

    stats = NetlistStats(
        title="t",
        components=0,
        nodes=0,
        models=0,
        includes=0,
        options=0,
        component_breakdown={},
    )
    verification = NetlistVerification(
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
        connectivity_fingerprint_left="0",
        connectivity_fingerprint_right="0",
        sizing_fingerprint_left="0",
        sizing_fingerprint_right="0",
    )

    equal_report = NetlistComparisonReport(
        left_path="a",
        right_path="b",
        left=stats,
        right=stats,
        verification=verification,
        differences=[],
    )
    equal_text = format_report_text(equal_report)
    assert "equivalent" in equal_text

    diff_report = NetlistComparisonReport(
        left_path="a",
        right_path="b",
        left=stats,
        right=stats,
        verification=verification,
        differences=["first", "second"],
    )
    diff_text = format_report_text(diff_report, max_differences=1)
    assert "difference(s)" in diff_text
    assert "... 1 more" in diff_text


def test_serializer_quotes_includes_and_model_without_params() -> None:
    """Serializer should quote include paths and emit models without params."""

    netlist = Netlist(
        title="Title",
        components=[
            Component(
                name="R1",
                component_type=ComponentType.RESISTOR,
                nodes=["n1", "n2"],
                parameters={"value": 10, "label": "foo bar"},
            )
        ],
        models={"M1": {"type": "NMOS", "parameters": {}}},
        options={"temp": 25},
        includes=["lib path.sp"],
    )
    serializer = SpiceSerializer(SpiceSerializerOptions())
    text = serializer.serialize(netlist)

    assert '.INCLUDE "lib path.sp"' in text
    assert ".MODEL M1 NMOS" in text
    assert 'label="foo bar"' in text


def test_netlist_transformer_param_directive_and_units() -> None:
    """NetlistTransformer should handle PARAM directives and unit scaling."""

    transformer = NetlistTransformer()
    gain_value = ValueNode(
        node_type=NodeType.VALUE,
        line_number=1,
        position=0,
        value=2.0,
        unit="k",
    )
    gain_param = ParameterNode(
        node_type=NodeType.PARAMETER,
        line_number=1,
        position=0,
        name="gain",
        value=gain_value,
    )
    comp_node = ComponentNode(
        node_type=NodeType.COMPONENT,
        line_number=1,
        position=0,
        name="Z1",
        component_type="Z",
        nodes=["n1", "n2"],
        parameters=[gain_param],
        model=None,
    )
    param_value = ValueNode(
        node_type=NodeType.VALUE,
        line_number=2,
        position=0,
        value=1.0,
    )
    param_param = ParameterNode(
        node_type=NodeType.PARAMETER,
        line_number=2,
        position=0,
        name="bias",
        value=param_value,
    )
    directive = DirectiveNode(
        node_type=NodeType.DIRECTIVE,
        line_number=2,
        position=0,
        directive_type="PARAM",
        parameters=[param_param],
    )
    netlist_node = NetlistNode(
        node_type=NodeType.NETLIST,
        line_number=0,
        position=0,
        title="T",
        statements=[comp_node, directive],
    )

    netlist = transformer.transform(netlist_node)

    assert netlist.components[0].component_type is ComponentType.RESISTOR
    assert netlist.components[0].parameters["gain"] == pytest.approx(2000.0)
    assert netlist.includes == []


def test_parser_ast_helpers_with_string_and_file(tmp_path: Path) -> None:
    """SpiceNetlistParser should expose AST helpers for string and file inputs."""

    parser = SpiceNetlistParser()
    netlist_text = "R1 0 1 1k\n.END\n"

    ast_from_string = parser.parse_to_ast(netlist_text)
    assert ast_from_string.title

    file_path = tmp_path / "circuit.sp"
    file_path.write_text(netlist_text, encoding="utf-8")

    ast_from_file = parser.parse_file_to_ast(file_path)
    assert ast_from_file.title == ast_from_string.title


def test_config_reload_and_accessors(monkeypatch: MonkeyPatch) -> None:
    """Config reload should honor updated environment variables."""

    monkeypatch.setenv("SPICE_PARSER_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SPICE_PARSER_LOG_FILE", "/tmp/log.txt")
    config.reload_config()

    assert config.get_log_level() == "DEBUG"
    assert config.get_log_file() == Path("/tmp/log.txt")
    assert isinstance(config.get_max_file_size(), int)


def test_cli_dunder_main_executes_exit() -> None:
    """Running cli.__main__ as __main__ should trigger SystemExit."""

    with pytest.raises(SystemExit):
        runpy.run_module(
            "spice_netlist_parser.cli.__main__", run_name="__main__", alter_sys=True
        )


def test_main_unknown_command_triggers_error(monkeypatch: MonkeyPatch) -> None:
    """main should call parser.error when command is unexpected."""

    called: dict[str, str] = {}

    class FakeParser:
        def parse_args(self) -> SimpleNamespace:
            return SimpleNamespace(
                command="weird",
                verbose=False,
                log_level="INFO",
                log_file=None,
            )

        def error(self, message: str) -> None:
            called["msg"] = message
            raise SystemExit(2)

    monkeypatch.setattr(cli_main, "create_parser", FakeParser)

    with pytest.raises(SystemExit):
        cli_main.main()

    assert "Unknown command" in called["msg"]


def test_main_dunder_invocation_runs_sys_exit() -> None:
    """Running spice_netlist_parser.main as a module should exit via argparse."""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        with pytest.raises(SystemExit):
            runpy.run_module(
                "spice_netlist_parser.main", run_name="__main__", alter_sys=True
            )


def test_parse_command_ast_verbose_outputs_details(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    """parse_command should print AST details when requested."""

    netlist_path = tmp_path / "circuit.sp"
    netlist_path.write_text("R1 0 1 1k\n.END\n", encoding="utf-8")
    args = SimpleNamespace(
        file=netlist_path,
        ast=True,
        verbose=True,
        format="text",
        output=None,
    )

    code = cli_commands.parse_command(args)
    out = capsys.readouterr().out

    assert code == 0
    assert "AST Root" in out
    assert "Statements" in out


def test_compare_and_roundtrip_commands_missing_files(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    """compare_command and roundtrip_command should early-exit when files are missing."""

    missing = tmp_path / "missing.sp"
    args_compare = SimpleNamespace(
        file1=missing,
        file2=missing,
        format="text",
        output=None,
    )
    compare_code = cli_commands.compare_command(args_compare)
    compare_err = capsys.readouterr().err

    args_roundtrip = SimpleNamespace(file=missing, output=None)
    roundtrip_code = cli_commands.roundtrip_command(args_roundtrip)
    roundtrip_err = capsys.readouterr().err

    assert compare_code == 1
    assert "File not found" in compare_err
    assert roundtrip_code == 1
    assert "File not found" in roundtrip_err


def test_format_output_writes_json(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """format_output should honor json formatting and file output."""

    netlist = Netlist(
        title="T",
        components=[],
        models={},
        options={},
        includes=[],
    )
    output_file = tmp_path / "out.json"
    cli_commands.format_output(netlist, "json", output_file)

    out = capsys.readouterr().out
    assert output_file.exists()
    assert "Output written" in out
    content = output_file.read_text(encoding="utf-8")
    assert '"title": "T"' in content


def test_format_helpers_include_components_and_breakdown() -> None:
    """format_text and format_summary should enumerate components and counts."""

    comps = [
        Component("R1", ComponentType.RESISTOR, ["n1", "n2"], {"value": 1}, None),
        Component("C1", ComponentType.CAPACITOR, ["n2", "n3"], {}, None),
    ]
    netlist = Netlist(
        title="T",
        components=comps,
        models={"M1": {"type": "NMOS", "parameters": {"w": 1}}},
        options={},
        includes=["lib.sp"],
    )

    text = cli_commands.format_text(netlist)
    summary = cli_commands.format_summary(netlist)

    assert "Components:" in text
    assert "Parameters" in text
    assert "Component breakdown" in summary


def test_serializer_skips_empty_include_and_handles_bodyless_component() -> None:
    """Serializer should ignore blank include entries and handle components with no body."""

    netlist = Netlist(
        title="T",
        components=[Component("R1", ComponentType.RESISTOR, ["n1", "n2"], {})],
        models={},
        options={},
        includes=["", "models.lib"],
    )
    text = SpiceSerializer(SpiceSerializerOptions()).serialize(netlist)

    lines = text.splitlines()
    assert ".INCLUDE models.lib" in text
    assert not any(line.strip() == ".INCLUDE" for line in lines)
    assert "R1 n1 n2" in text


def test_visitor_collects_models_and_options() -> None:
    """NetlistTransformer should accumulate model and option dictionaries."""

    transformer = NetlistTransformer()
    model_param = ParameterNode(
        node_type=NodeType.PARAMETER,
        line_number=1,
        position=0,
        name="w",
        value=ValueNode(node_type=NodeType.VALUE, line_number=1, position=0, value=2.0),
    )
    model_node = ModelNode(
        node_type=NodeType.MODEL,
        line_number=1,
        position=0,
        name="M1",
        model_type="NMOS",
        parameters=[model_param],
    )
    option_param = ParameterNode(
        node_type=NodeType.PARAMETER,
        line_number=2,
        position=0,
        name="TEMP",
        value=ValueNode(
            node_type=NodeType.VALUE, line_number=2, position=0, value=25.0
        ),
    )
    option_directive = DirectiveNode(
        node_type=NodeType.DIRECTIVE,
        line_number=2,
        position=0,
        directive_type="OPTION",
        parameters=[option_param],
    )
    netlist_node = NetlistNode(
        node_type=NodeType.NETLIST,
        line_number=0,
        position=0,
        title="T",
        statements=[model_node, option_directive],
    )

    netlist = transformer.visit_netlist(netlist_node)

    assert netlist.models["M1"]["type"] == "NMOS"
    assert netlist.options["temp"] == 25.0  # noqa: PLR2004


def test_roundtrip_validator_reports_many_differences() -> None:
    """assert_equivalent should truncate long diff lists and include serialized text."""

    def make_netlist(prefix: str) -> Netlist:
        comps = [
            Component(
                f"R{i}",
                ComponentType.RESISTOR,
                ["n1", "n2"],
                {"value": float(i)},
                None,
            )
            for i in range(30)
        ]
        return Netlist(
            title=f"{prefix}", components=comps, models={}, options={}, includes=[]
        )

    left = make_netlist("a")
    # Ensure each component differs in multiple dimensions to inflate diff count.
    right_components = [
        Component(
            f"R{i}",
            ComponentType.CAPACITOR,
            ["n2", "n3"],
            {"value": float(i) + 0.5},
            model="M1",
        )
        for i in range(30)
    ]
    right = Netlist(
        title="b",
        components=right_components,
        models={"M1": {"type": "NMOS", "parameters": {"w": 1}}},
        options={"temp": 25},
        includes=["lib.sp"],
    )

    validator = RoundTripValidator()

    with pytest.raises(RoundTripMismatchError) as exc:
        validator.assert_equivalent(
            left, right, serialized_spice="* demo", float_tol=1e-9
        )

    msg = str(exc.value)
    assert "... " in msg
    assert "Serialized SPICE" in msg


def test_roundtrip_diff_component_fields_and_value_equivalent() -> None:
    """diff should flag type, nodes, model, and parameters differences."""

    comp_a = Component(
        "R1",
        ComponentType.RESISTOR,
        ["n1", "n2"],
        {"value": 1.0, "gain": 2.0},
        model=None,
    )
    comp_b = Component(
        "R1",
        ComponentType.CAPACITOR,
        ["n2", "n3"],
        {"value": 1.5},
        model="M1",
    )
    net_a = Netlist(title="A", components=[comp_a], models={}, options={}, includes=[])
    net_b = Netlist(title="B", components=[comp_b], models={}, options={}, includes=[])

    validator = RoundTripValidator()
    diffs = validator.diff(net_a, net_b, float_tol=1e-6)

    assert any("type" in d for d in diffs)
    assert any("nodes" in d for d in diffs)
    assert any("model" in d for d in diffs)
    assert any("parameters" in d for d in diffs)
    assert RoundTripValidator._value_equivalent("x", "x", float_tol=1e-12)  # noqa: SLF001
