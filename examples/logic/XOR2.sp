* Test Circuit: XOR2 Gate
* Generated from ICSN55H7RVT XOR2X0P5H7R cell

* Include model definitions (would need actual model files)
* .include "models.sp"

* Power supplies
V1 vdd 0 1.8
V2 vss 0 0

* Input stimuli (will be controlled by test vectors)
VINA A vss PULSE(0 1.8 0 10p 10p 1n 2n)
VINB B vss PULSE(0 1.8 0 10p 10p 1n 2n)

* Subcircuit definitions (matching CDL structure)
* Note: Subcircuits use parameters (nw, nl, pw, pl) that are passed from instances

.SUBCKT INV A VDD VSS Y
MMN0 Y A VSS VSS nm1p2_svt_lp W=nw L=nl m=1
MMP0 Y A VDD VDD pm1p2_svt_lp W=pw L=pl m=1
.ENDS

.SUBCKT TG A B C D VDD VSS
* Transmission gate: A=input, B=control, C=control_bar, D=output
MMN_TG D A B VSS nm1p2_svt_lp W=nw L=nl m=1
MMP_TG D A C VDD pm1p2_svt_lp W=pw L=pl m=1
.ENDS

.SUBCKT TSINV A B C VDD VSS Y
* Tri-state inverter: A=input, B=control, C=control_bar, Y=output
MMN0 Y B net18 VSS nm1p2_svt_lp W=nw L=nl m=1
MMN1 net18 A VSS VSS nm1p2_svt_lp W=nw L=nl m=1
MMP1 net024 A VDD VDD pm1p2_svt_lp W=pw L=pl m=1
MMP0 Y C net024 VDD pm1p2_svt_lp W=pw L=pl m=1
.ENDS

* XOR2 implementation using subcircuit instances (standard SPICE/ngspice format)
XI0 AN A BN net19 vdd vss TG pl=6e-08 pw=1.9e-07 nl=6e-08 nw=1.5e-07
XI6 net19 vdd vss Y INV pl=6e-08 pw=1.9e-07 nl=6e-08 nw=1.5e-07
XI1 B vdd vss BN INV pl=6e-08 pw=1.9e-07 nl=6e-08 nw=1.5e-07
XI4 A vdd vss AN INV pl=6e-08 pw=1.9e-07 nl=6e-08 nw=1.5e-07
XI3 BN A AN vdd vss net19 TSINV pl=6e-08 pw=1.9e-07 nl=6e-08 nw=1.5e-07

* Load capacitance
CL Y vss 10f

* Analysis
.TRAN 10p 8n

* Measurements
.MEASURE TRAN tpLH TRIG V(A) VAL=0.9 RISE=1 TARG V(Y) VAL=0.9 RISE=1
.MEASURE TRAN tpHL TRIG V(A) VAL=0.9 FALL=1 TARG V(Y) VAL=0.9 FALL=1

.END
