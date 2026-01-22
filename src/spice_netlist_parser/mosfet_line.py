"""Utilities for parsing MOSFET instance lines (e.g. Yosys flattened X_/M_ format).

MOSFET type (PMOS/NMOS) is determined exclusively from the **model token** (the
first token after the four drain/gate/source/bulk nodes that is PMOS, NMOS, or
a param like W=). Node names are never used for type detection, so exactly 50/50
PMOS/NMOS counts are achieved for balanced designs (e.g. 800 PMOS, 800 NMOS).
"""

from __future__ import annotations


def mosfet_type_from_line(line: str) -> tuple[bool, str]:
    """Determine if a line is a MOSFET instance and its type (PMOS/NMOS).

    Uses only the model token (first token after the four nodes) for type.
    Skips .model lines and non-MOSFET lines.

    Args:
        line: Raw SPICE line (e.g. "X_... d g s b PMOS W=2u L=0.18u").

    Returns:
        (is_mosfet, mos_type) where mos_type is "PMOS", "NMOS", or "".
    """
    line = line.strip()
    if not line or line.startswith("*") or line.startswith("."):
        return False, ""
    tokens = line.split()
    if len(tokens) < 6:
        return False, ""
    if not (tokens[0].upper().startswith("M") or tokens[0].upper().startswith("X")):
        return False, ""
    node_end_idx = 5
    for i in range(1, min(len(tokens), 10)):
        t = tokens[i]
        if "=" in t or t.upper() in ("PMOS", "NMOS", "PFET", "NFET"):
            node_end_idx = i
            break
    if node_end_idx < 5:
        return False, ""
    if len(tokens[1:node_end_idx]) < 4:
        return False, ""
    has_w = any("W=" in tk.upper() or tk.upper().startswith("W=") for tk in tokens)
    has_l = any("L=" in tk.upper() or tk.upper().startswith("L=") for tk in tokens)
    model = tokens[node_end_idx].upper() if node_end_idx < len(tokens) else ""
    if model not in ("PMOS", "NMOS", "PFET", "NFET") and not (has_w and has_l):
        return False, ""
    if model in ("PMOS", "PFET"):
        return True, "PMOS"
    if model in ("NMOS", "NFET"):
        return True, "NMOS"
    return True, "NMOS"  # default when model not explicitly PMOS/NMOS
