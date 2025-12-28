* DFFX1 Flip-Flop Test Circuit
* Generated from ICSN55H7RVT DFFX1H7R cell

* Include model definitions (would need actual model files)
* .include "models.sp"

* Power supplies
VDD VDD 0 1.8V
VSS VSS 0 0V

* Clock signal (2GHz clock for testing)
VCLK CK VSS PULSE(0 1.8 0 50p 50p 0.5n 1n)

* Data input (changes on falling clock edge to test setup time)
VDATA D VSS PULSE(0 1.8 0.25n 50p 50p 0.5n 1n)

* Subcircuit definitions (extracted from ics55_LLSC_H7CR.cdl)
* Note: Subcircuits use parameters (nw, nl, pw, pl) that are passed from instances

.SUBCKT INV A VDD VSS Y
MMN0 Y A VSS VSS nm1p2_svt_lp W=nw L=nl m=1
MMP0 Y A VDD VDD pm1p2_svt_lp W=pw L=pl m=1
.ENDS

.SUBCKT TSINV A CK CKN VDD VSS Y
MMN0 Y CK net18 VSS nm1p2_svt_lp W=nw L=nl m=1
MMN1 net18 A VSS VSS nm1p2_svt_lp W=nw L=nl m=1
MMP1 net024 A VDD VDD pm1p2_svt_lp W=pw L=pl m=1
MMP0 Y CKN net024 VDD pm1p2_svt_lp W=pw L=pl m=1
.ENDS

XI2 net46 CKP CKN VDD VSS net33 TSINV pl=6E-08 pw=1.5E-07 nl=6E-08 nw=1.5E-07
XXI6 D CKN CKP VDD VSS net33 TSINV pl=6E-08 pw=2.8E-07 nl=6E-08 nw=2E-07
XI3 net46 CKP CKN VDD VSS net25 TSINV pl=6E-08 pw=3E-07 nl=6E-08 nw=2.2E-07
XI4 net9 CKN CKP VDD VSS net25 TSINV pl=6E-08 pw=1.5E-07 nl=6E-08 nw=1.5E-07
XI1 net33 VDD VSS net46 INV pl=6E-08 pw=2.8E-07 nl=6E-08 nw=2E-07
XI0 CKN VDD VSS CKP INV pl=6E-08 pw=2.8E-07 nl=6E-08 nw=2E-07
XXI12 net25 VDD VSS Q INV pl=6E-08 pw=3E-07 nl=6E-08 nw=2.4E-07
XXI10 net25 VDD VSS net9 INV pl=6E-08 pw=3E-07 nl=6E-08 nw=2.2E-07
XI5 net9 VDD VSS QN INV pl=6E-08 pw=3E-07 nl=6E-08 nw=2.4E-07
XXI4 CK VDD VSS CKN INV pl=6E-08 pw=2.8E-07 nl=6E-08 nw=2E-07

* Load capacitances
CL_Q Q VSS 10f
CL_QN QN VSS 10f

* Analysis - capture multiple clock cycles
.TRAN 10p 10n

* Measurements - check if Q follows D after clock edges
.MEASURE TRAN setup_time TRIG V(D) VAL=0.9 RISE=1 TARG V(CK) VAL=0.9 RISE=1

.END
