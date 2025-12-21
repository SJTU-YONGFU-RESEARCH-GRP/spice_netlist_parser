"""SPICE netlist grammar definition for Lark parser."""

# Clean baseline grammar: fixed arity for common primitives, generic fallback,
# numeric values as SIGNED_NUMBER, node names starting with letter/underscore,
# and compact param assignments via PARAM_ASSIGN.

SPICE_GRAMMAR = r"""

// Function calls captured as single token (e.g., SIN(0 8.6 8793))
FUNCTION_CALL.5: /[A-Za-z_][A-Za-z0-9_]*\([^)]*\)/

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

// Fallback component name (must come after specific primitives)
COMPONENT_NAME: /[RCLVIMQDX][0-9][A-Za-z0-9_]*/

start: NEWLINE* (statement NEWLINE*)* ".END"

NEWLINE: /(\r?\n)+/

statement: component_line
         | model_line
         | include_line
         | option_line
         | param_line
         | subckt_line
         | control_line

// Component definitions (fixed arity)
component_line: two_node_component
             | diode_component
             | mosfet_component
             | bjt_component
             | subckt_instance

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

// Model names (simple identifier) but must not collide with component designators
MODEL_NAME.1: /(?![RCLVIMQDX][0-9])[A-Za-z_][A-Za-z0-9_]*/

// Parameter names (short) only when immediately followed by '='
PARAM_NAME.3: /(?![RCLVIMQDX][0-9])(?![A-Za-z_][A-Za-z0-9_]*\()[A-Za-z_][A-Za-z0-9_]{0,3}(?==)/

node: SIGNED_NUMBER | ZERO | NODE_NAME
ZERO: "0"
// Node names start with letter/underscore, avoid component designators, and must not be a function call (identifier followed by '(')
NODE_NAME: /(?![RCLVIMQDX][0-9])(?![A-Za-z_][A-Za-z0-9_]*\()[A-Za-z_][A-Za-z0-9_.-]*/

// Component body: optional leading model name followed by parameters/values (FUNCTION_CALL handled via value)
component_body: MODEL_NAME param_or_value*
              | param_or_value+

// Allow compact param assignments like L=0.25u as a single token
PARAM_ASSIGN.4: /[A-Za-z][A-Za-z0-9_]*=[^ \t\r\n]+/
param_or_value: parameter | value | PARAM_ASSIGN

parameter: PARAM_NAME "=" value

value: FUNCTION_CALL
     | SIGNED_NUMBER
     | STRING

// Numbers with optional unit suffix or scientific notation
SIGNED_NUMBER: /[+-]?\d+(\.\d+)?([eE][+-]?\d+)?[A-Za-z]*/
STRING: /"[^"]*"/

// Model definitions
model_line: ".MODEL" MODEL_NAME MODEL_NAME model_params
model_params: "(" parameter* ")" | parameter*

// Include directive
include_line: ".INCLUDE" FILE_PATH
// File paths: quoted strings or paths containing slashes (exclude bare numbers)
FILE_PATH: /"[^"]*"/ | /[^ \t\r\n=()]*\/[^ \t\r\n=()]*/

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
// Ignore spaces/tabs; NEWLINE is used as a statement separator
%ignore /[ \t]+/
"""
