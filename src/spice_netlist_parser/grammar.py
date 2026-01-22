"""SPICE netlist grammar definition for Lark parser."""

# Clean baseline grammar: fixed arity for common primitives, generic fallback,
# numeric values as SIGNED_NUMBER, node names starting with letter/underscore,
# and compact param assignments via PARAM_ASSIGN.

SPICE_GRAMMAR = r"""

// Function calls captured as single token (e.g., SIN(0 8.6 8793))
FUNCTION_CALL.28: /[A-Za-z_][A-Za-z0-9_]*\([^)]*\)/

// Component names start with designator and must include at least one digit
RESISTOR_NAME.27: /R[0-9][A-Za-z0-9_]*/
CAPACITOR_NAME.28: /C[A-Za-z0-9_]+/
INDUCTOR_NAME.27: /L[0-9][A-Za-z0-9_]*/
VOLTAGE_NAME.31: /V[0-9][A-Za-z0-9_]*|V[A-Za-z0-9_]{2,}/
CURRENT_NAME.27: /I[0-9][A-Za-z0-9_]*/
// MOSFET component names: M prefix (standard)
// X_ prefixed MOSFETs are converted to M_ by preprocessing, so we only need to match M here
// This avoids conflicts with X_ prefixed node names
MOSFET_NAME.32: /M[A-Za-z0-9_.]+/
BJT_NAME.27: /Q[0-9][A-Za-z0-9_]*/
DIODE_NAME.27: /D[0-9][A-Za-z0-9_]*/
SUBCKT_INST_NAME.29: /X[A-Za-z0-9_.]+/

// Fallback component name (must come after specific primitives)
COMPONENT_NAME.5: /[RCLVIMQDX][A-Za-z0-9_]{3,}/

start: NEWLINE* (statement NEWLINE*)* ".END"

NEWLINE: /(\r?\n)+/

statement: component_line
         | model_line
         | include_line
         | option_line
         | param_line
         | subckt_line
         | control_line
         | ends_line
         | tran_line

// Component definitions (fixed arity) - order matters for precedence
// Note: mosfet_component before subckt_instance to handle X_ prefixed MOSFETs
component_line: mosfet_component
             | subckt_instance
             | bjt_component
             | diode_component
             | two_node_component

node2: node node
node3: node node node
node4: node node node node
node5: node node node node node
node_list: node+
subckt_node: SIGNED_NUMBER | ZERO | NODE_NAME | SUBCKT_NAME | SUBCKT_INST_NAME | VOLTAGE_NAME | CAPACITOR_NAME
subckt_node_list: subckt_node+

two_node_component: (RESISTOR_NAME | CAPACITOR_NAME | INDUCTOR_NAME | VOLTAGE_NAME | CURRENT_NAME | COMPONENT_NAME) node2 component_body?
diode_component: DIODE_NAME node2 MODEL_NAME param_or_value*
mosfet_component: MOSFET_NAME node node node node node node MODEL_NAME param_or_value*
                | MOSFET_NAME node node node node node MODEL_NAME param_or_value*
                | MOSFET_NAME node node node node MODEL_NAME param_or_value*
bjt_component: BJT_NAME node3 MODEL_NAME param_or_value*
             | BJT_NAME node4 MODEL_NAME param_or_value*
subckt_instance: SUBCKT_INST_NAME subckt_node_list ["/"] (MODEL_NAME | SUBCKT_NAME) param_or_value*

// Subcircuit names
SUBCKT_NAME.26: /(?![X])[A-Z][A-Za-z0-9_]+/

// Model names (typically short identifiers like PMOS, NMOS, NPN, nm1p2_svt_lp, etc.)
// Exclude hierarchical node names (which have dots, brackets, slashes, or colons)
// Model names must match one of these strict patterns:
//   1. All uppercase with at least 2 uppercase letters (PMOS, NMOS, NPN, etc.) - standard SPICE
//   2. Start with lowercase nm/pm/npn/pnp followed by digit (nm1p2_svt_lp, pm1p2_svt_lp) - CDL format
//   3. Contain underscore (model_name format) - but NOT simple names like "net_26"
// Higher priority (27) ensures model names win over NODE_NAME (25) for actual model names
// This is safe because the patterns are restrictive enough to avoid false matches
MODEL_NAME.27: /(?![A-Za-z0-9_]*[\.\[\:\/])(?![RCLVIMQDX][0-9])(?![A-Za-z_$][A-Za-z0-9_$]*[\\:\.\/])(?![A-Za-z_$][A-Za-z0-9_$]*\[)([A-Z]{2,}[A-Za-z0-9_]{0,18}|[nm][mp]?[0-9][A-Za-z0-9_]*|[np][np][np]?[A-Za-z0-9_]*|[A-Za-z][A-Za-z0-9_]+_[A-Za-z0-9_]+)/

// Parameter names (short) only when immediately followed by '='
PARAM_NAME.3: /(?![RCLVIMQDX][0-9])(?![A-Za-z_][A-Za-z0-9_]*\()[A-Za-z_][A-Za-z0-9_]{0,3}(?==)/

node: SIGNED_NUMBER | ZERO | NODE_NAME | SUBCKT_NAME | VOLTAGE_NAME | CAPACITOR_NAME | SUBCKT_INST_NAME
ZERO.11: "0"
// Node names: avoid component designators, must not be function call
// Support bracket notation [number] for array indices anywhere in hierarchical names
// (e.g., a[0], carries[31], carry_select_blocks[7].sum_cin_0[0], [7].block_b[0])
// Support X_ prefixed hierarchical names as nodes (e.g., X_module.node)
// Support Yosys-generated hierarchical names with $, backslashes, colons
// (e.g., $flatten\carry_select_blocks[7].adder_1.\full_adders[1].fa.$and$examples/file.v:128$20_Y)
// Support relative hierarchical paths starting with . (e.g., .full_adders[3].fa.a)
// Hierarchical names can have dots, brackets, $, backslashes, colons anywhere
// Exclude directives starting with . (e.g., .MODEL, .SUBCKT) - these are handled separately
// Priority 25 ensures it matches before FILE_PATH (which has no explicit priority)
NODE_NAME.25: /(?![RCLVIMQDX][0-9])(?![A-Za-z_][A-Za-z0-9_]*\()(?!\.(MODEL|SUBCKT|ENDS|INCLUDE|OPTION|PARAM|TRAN|OP|DC|AC|END)\b)(\.|(\$|\[\d+\]\.))?([A-Za-z_$][A-Za-z0-9_$\\:\.\/]*(\[\d+\])?[\.\\\/]?)+(\[\d+\])?/

// Component body: optional leading model name followed by parameters/values (FUNCTION_CALL handled via value)
component_body: MODEL_NAME param_or_value*
              | param_or_value+

// Allow compact param assignments like L=0.25u as a single token
PARAM_ASSIGN.26: /[A-Za-z][A-Za-z0-9_]*=[^ \t\r\n]+/
param_or_value: parameter | value | PARAM_ASSIGN

parameter: PARAM_NAME "=" value

value: FUNCTION_CALL
     | SIGNED_NUMBER
     | ZERO
     | STRING

// Numbers with optional unit suffix or scientific notation
SIGNED_NUMBER.17: /[+-]?\d+(\.\d+)?([eE][+-]?\d+)?[A-Za-z]*/
STRING: /"[^"]*"/

// Model definitions
model_line: ".MODEL" MODEL_NAME MODEL_NAME model_params
model_params: "(" parameter* ")" | parameter*

// Include directive
include_line: ".INCLUDE" FILE_PATH
// File paths: quoted strings or paths containing forward slashes
// Must start with letter, dot, or slash (not $ or [) to avoid matching node names
// Lower priority (no number) so NODE_NAME matches first for names with $ or [
FILE_PATH.20: /"[^"]*"/ | /[A-Za-z\.\/][^ \t\r\n=()]*\/[^ \t\r\n=()]*/

// Option directive
option_line: ".OPTION" parameter*

// Parameter directive
param_line: ".PARAM" parameter*

// Subcircuit definition
subckt_line: ".SUBCKT" (SUBCKT_NAME | MODEL_NAME) node_list statement*
ends_line: ".ENDS"
tran_line: ".TRAN" /[^ \t\r\n]+/ /[^ \t\r\n]+/

// Control statements
control_line: ".OP" | ".DC" | ".AC" | ".TRAN" | ".END"

%import common.WS
// Ignore spaces/tabs; NEWLINE is used as a statement separator
%ignore /[ \t]+/
"""
