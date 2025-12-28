* Test Circuit: NAND2 Gate
* Generated from ICSCORE NAND2 cell

* Include model definitions (would need actual model files)
* .include "models.sp"

* Power supplies
V1 vdd 0 1.8
V2 vss 0 0

* Input stimuli (will be controlled by test vectors)
VINA A vss PULSE(0 1.8 0 10p 10p 1n 2n)
VINB B vss PULSE(0 1.8 0 10p 10p 1n 2n)

* NAND2 gate implementation
MMN0 Y B net15 vss nm1p2_svt_lp W=150n L=60n
MMN2 net15 A vss vss nm1p2_svt_lp W=150n L=60n
MMP2 Y A vdd vdd pm1p2_svt_lp W=190n L=60n
MMP0 Y B vdd vdd pm1p2_svt_lp W=190n L=60n

* Load capacitance
CL Y vss 10f

* Analysis
.TRAN 10p 8n

* Measurements
.MEASURE TRAN tpLH TRIG V(A) VAL=0.9 RISE=1 TARG V(Y) VAL=0.9 RISE=1
.MEASURE TRAN tpHL TRIG V(A) VAL=0.9 FALL=1 TARG V(Y) VAL=0.9 FALL=1

.END
