* Test Circuit: OR2 Gate
* Generated from ICSN55H7RVT OR2X1H7R cell

* Include model definitions (would need actual model files)
* .include "models.sp"

* Power supplies
V1 vdd 0 1.8
V2 vss 0 0

* Input stimuli (will be controlled by test vectors)
VINA A vss PULSE(0 1.8 0 10p 10p 1n 2n)
VINB B vss PULSE(0 1.8 0 10p 10p 1n 2n)

* OR2 gate implementation
MMN2 net21 B vss vss nm1p2_svt_lp W=150n L=60n
MMN0 net21 A vss vss nm1p2_svt_lp W=150n L=60n
MMP2 net21 B net016 vdd pm1p2_svt_lp W=190n L=60n
MMP1 net016 A vdd vdd pm1p2_svt_lp W=190n L=60n

* Inverter for output
MMN_INV Y net21 vss vss nm1p2_svt_lp W=150n L=60n
MMP_INV Y net21 vdd vdd pm1p2_svt_lp W=190n L=60n

* Load capacitance
CL Y vss 10f

* Analysis
.TRAN 10p 8n

* Measurements
.MEASURE TRAN tpLH TRIG V(A) VAL=0.9 RISE=1 TARG V(Y) VAL=0.9 RISE=1
.MEASURE TRAN tpHL TRIG V(A) VAL=0.9 FALL=1 TARG V(Y) VAL=0.9 FALL=1

.END
