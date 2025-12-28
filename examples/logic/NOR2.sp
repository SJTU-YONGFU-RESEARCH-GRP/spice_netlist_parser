* Test Circuit: NOR2 Gate
* Generated from ICSN55H7RVT NOR2X1H7R cell

* Include model definitions (would need actual model files)
* .include "models.sp"

* Power supplies
V1 vdd 0 1.8
V2 vss 0 0

* Input stimuli (will be controlled by test vectors)
VINA A vss PULSE(0 1.8 0 10p 10p 1n 2n)
VINB B vss PULSE(0 1.8 0 10p 10p 1n 2n)

* NOR2 gate implementation
MNM0 Y B vss vss nm1p2_svt_lp W=210n L=60n
MMN0 Y A vss vss nm1p2_svt_lp W=210n L=60n
MPM0 Y B net015 vdd pm1p2_svt_lp W=270n L=60n
MMP1 net015 A vdd vdd pm1p2_svt_lp W=270n L=60n

* Load capacitance
CL Y vss 10f

* Analysis
.TRAN 10p 8n

* Measurements
.MEASURE TRAN tpLH TRIG V(A) VAL=0.9 RISE=1 TARG V(Y) VAL=0.9 RISE=1
.MEASURE TRAN tpHL TRIG V(A) VAL=0.9 FALL=1 TARG V(Y) VAL=0.9 FALL=1

.END
