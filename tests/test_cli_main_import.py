"""Coverage for cli __main__ import."""

from __future__ import annotations

import runpy


def test_cli_main_importable() -> None:
    """Ensure cli.__main__ can be imported via runpy."""

    mod = runpy.run_module("spice_netlist_parser.cli.__main__")
    assert "__name__" in mod
    assert mod["__name__"] == "__main__" or mod["__name__"].startswith(
        "spice_netlist_parser"
    )
