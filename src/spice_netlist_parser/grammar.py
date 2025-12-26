"""SPICE netlist grammar definition for Lark parser."""

# Clean baseline grammar: fixed arity for common primitives, generic fallback,
# numeric values as SIGNED_NUMBER, node names starting with letter/underscore,
# and compact param assignments via PARAM_ASSIGN.

SPICE_GRAMMAR = r"""

// Function calls captured as single token (e.g., SIN(0 8.6 8793))
FUNCTION_CALL.10: /[A-Za-z_][A-Za-z0-9_]*\([^)]*\)/

// Component names start with designator and must include at least one digit
RESISTOR_NAME.10: /R[0-9][A-Za-z0-9_]*/
CAPACITOR_NAME.10: /C[A-Za-z0-9_]+/
INDUCTOR_NAME.10: /L[0-9][A-Za-z0-9_]*/
VOLTAGE_NAME.10: /V[0-9][A-Za-z0-9_]*|V[A-Za-z0-9_]{3,}/
CURRENT_NAME.10: /I[0-9][A-Za-z0-9_]*/
MOSFET_NAME.10: /M[0-9][A-Za-z0-9_]*|M[A-Za-z0-9_]{3,}/
BJT_NAME.10: /Q[0-9][A-Za-z0-9_]*/
DIODE_NAME.10: /D[0-9][A-Za-z0-9_]*/
SUBCKT_INST_NAME.10: /X[0-9][A-Za-z0-9_]*/

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

two_node_component: (RESISTOR_NAME | CAPACITOR_NAME | INDUCTOR_NAME | VOLTAGE_NAME | CURRENT_NAME | COMPONENT_NAME) node2 component_body?
diode_component: DIODE_NAME node2 MODEL_NAME param_or_value*
mosfet_component: MOSFET_NAME node4 (MODEL_NAME | NODE_NAME) param_or_value*
bjt_component: BJT_NAME node3 MODEL_NAME param_or_value*
             | BJT_NAME node4 MODEL_NAME param_or_value*
subckt_instance: SUBCKT_INST_NAME node_list MODEL_NAME param_or_value*

// Model names (require uppercase letter to distinguish from simple node names)
MODEL_NAME.7: /[A-Za-z0-9_]*[A-Z][A-Za-z0-9_]*/

// Parameter names (short) only when immediately followed by '='
PARAM_NAME.3: /(?![RCLVIMQDX][0-9])(?![A-Za-z_][A-Za-z0-9_]*\()[A-Za-z_][A-Za-z0-9_]{0,3}(?==)/

node: SIGNED_NUMBER | ZERO | NODE_NAME | MODEL_NAME
ZERO: "0"
// Node names: lowercase, avoid component designators, must not be function call
NODE_NAME.6: /(?![RCLVIMQDX][0-9])(?![A-Za-z_][A-Za-z0-9_]*\()[a-z_][a-z0-9_.-]*/

// Component body: optional leading model name followed by parameters/values (FUNCTION_CALL handled via value)
component_body: MODEL_NAME param_or_value*
              | param_or_value+

// Allow compact param assignments like L=0.25u as a single token
PARAM_ASSIGN.8: /[A-Za-z][A-Za-z0-9_]*=[^ \t\r\n]+/
param_or_value: parameter | value | PARAM_ASSIGN

parameter: PARAM_NAME "=" value

value: FUNCTION_CALL
     | SIGNED_NUMBER
     | ZERO
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
