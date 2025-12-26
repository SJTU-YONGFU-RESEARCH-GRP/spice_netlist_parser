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

* DFFX1 instantiation (simplified - would need subcircuits expanded)
* XI2 net46 CKP CKN VDD VSS net33 / TSINV
* XXI6 D CKN CKP VDD VSS net33 / TSINV
* XI3 net46 CKP CKN VDD VSS net25 / TSINV
* XI4 net9 CKN CKP VDD VSS net25 / TSINV
* XI1 net33 VDD VSS net46 / INV
* XI0 CKN VDD VSS CKP / INV
* XXI12 net25 VDD VSS Q / INV
* XXI10 net25 VDD VSS net9 / INV
* XI5 net9 VDD VSS QN / INV
* XXI4 CK VDD VSS CKN / INV

* Simplified DFF model for testing (master-slave concept)
* Master latch
MM1 net_master D CLK net_master VDD pm1p2_svt_lp W=190n L=60n
MM2 net_master D CLKB VSS VSS nm1p2_svt_lp W=150n L=60n

* Slave latch
MM3 Q net_master CLKB Q VDD pm1p2_svt_lp W=190n L=60n
MM4 Q net_master CLK VSS VSS nm1p2_svt_lp W=150n L=60n

* Inverted output
MM5 QN Q VSS VSS nm1p2_svt_lp W=150n L=60n
MM6 QN Q VDD VDD pm1p2_svt_lp W=190n L=60n

* Clock buffer
MM7 CLK CK VSS VSS nm1p2_svt_lp W=150n L=60n
MM8 CLK CK VDD VDD pm1p2_svt_lp W=190n L=60n
MM9 CLKB CLK VSS VSS nm1p2_svt_lp W=150n L=60n
MM10 CLKB CLK VDD VDD pm1p2_svt_lp W=190n L=60n

* Load capacitances
CL_Q Q VSS 10f
CL_QN QN VSS 10f

* Analysis - capture multiple clock cycles
.TRAN 10p 10n

* Measurements - check if Q follows D after clock edges
.MEASURE TRAN setup_time TRIG V(D) VAL=0.9 RISE=1 TARG V(CK) VAL=0.9 RISE=1

.END
