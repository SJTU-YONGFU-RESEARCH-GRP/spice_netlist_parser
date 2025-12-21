"""SPICE netlist grammar definition for Lark parser."""

SPICE_GRAMMAR = r"""
start: title_line? statement* ".END"

title_line: /[^\n]+/

statement: component_line
         | model_line
         | include_line
         | option_line
         | param_line
         | subckt_line
         | control_line

// Function calls (e.g., SIN(...)) must be matched as a single token
FUNCTION_CALL: /[A-Za-z_][A-Za-z0-9_]*\([^)]*\)/

// Component definitions
//
// IMPORTANT:
// Many SPICE primitives have a fixed node arity (e.g. R/C/L are 2-node).
// Using a greedy `node+` list causes the value token (e.g. "25k") to be parsed
// as a node, which breaks connectivity/sizing accuracy.
//
// We therefore use per-component rules with fixed node counts where possible.
component_line: two_node_component
             | diode_component
             | mosfet_component
             | bjt_component
             | subckt_instance
             | generic_component

// Component names start with designator and must include at least one digit
RESISTOR_NAME: /R[0-9][A-Za-z0-9_]*/
CAPACITOR_NAME: /C[0-9][A-Za-z0-9_]*/
INDUCTOR_NAME: /L[0-9][A-Za-z0-9_]*/
VOLTAGE_NAME: /V[0-9][A-Za-z0-9_]*/
CURRENT_NAME: /I[0-9][A-Za-z0-9_]*/
MOSFET_NAME: /M[0-9][A-Za-z0-9_]*/
BJT_NAME: /Q[0-9][A-Za-z0-9_]*/
DIODE_NAME: /D[0-9][A-Za-z0-9_]*/
SUBCKT_INST_NAME: /X[0-9][A-Za-z0-9_]*/

COMPONENT_NAME: /[RCLVIMQDX][0-9][A-Za-z0-9_]*/

node2: node node
node3: node node node
node4: node node node node
node_list: node+

two_node_component: (RESISTOR_NAME | CAPACITOR_NAME | INDUCTOR_NAME | VOLTAGE_NAME | CURRENT_NAME) node2 component_body?
diode_component: DIODE_NAME node2 MODEL_NAME param_or_value*
mosfet_component: MOSFET_NAME node4 MODEL_NAME param_or_value*
bjt_component: BJT_NAME node3 MODEL_NAME param_or_value*
             | BJT_NAME node4 MODEL_NAME param_or_value*
subckt_instance: SUBCKT_INST_NAME node_list MODEL_NAME param_or_value*

// Fallback (kept for flexibility; may be ambiguous for some custom elements)
generic_component: COMPONENT_NAME node_list component_body?

node: SIGNED_NUMBER | ZERO | NODE_NAME
ZERO: "0"
NODE_NAME: /[A-Za-z0-9_.]+/

// Component body: optional leading model name followed by parameters/values
component_body: MODEL_NAME param_or_value*
              | param_or_value+

param_or_value: parameter | value

// Model names (allow typical identifier)
MODEL_NAME: /[A-Za-z_][A-Za-z0-9_]*/

parameter: PARAM_NAME "=" value
// Parameter names (allow single-letter like L, W)
PARAM_NAME: /[A-Za-z_][A-Za-z0-9_]*/

value: FUNCTION_CALL
     | SIGNED_NUMBER
     | STRING

// Numbers with optional unit suffix or scientific notation
SIGNED_NUMBER: /[+-]?\d+(\.\d+)?([eE][+-]?\d+)?[A-Za-z]*/
STRING: /"[^"]*"/

// Model definitions
model_line: ".MODEL" MODEL_NAME MODEL_TYPE_NAME model_params
MODEL_TYPE_NAME: /[A-Za-z_][A-Za-z0-9_]*/
model_params: "(" parameter* ")" | parameter*

// Include directive
include_line: ".INCLUDE" FILE_PATH
// Avoid capturing parentheses that belong to function calls
FILE_PATH: /"[^"]*"/ | /[^ \t\n=()]+/

// Option directive
option_line: ".OPTION" parameter*

// Parameter directive
param_line: ".PARAM" parameter*

// Subcircuit definition
subckt_line: ".SUBCKT" SUBCKT_NAME node_list statement* ".ENDS"
SUBCKT_NAME: /X[A-Za-z0-9_]+/

// Control statements
control_line: ".OP" | ".DC" | ".AC" | ".TRAN" | ".END"

%import common.WS
%ignore WS
"""
