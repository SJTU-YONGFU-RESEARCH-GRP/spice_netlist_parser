Test Circuit: AND2 Gate

* Power supplies
V1 vdd 0 1.8
V2 vss 0 0

* Input stimuli (will be controlled by test vectors)
VINA A VSS PULSE(0 1.8 0 10p 10p 1n 2n)
VINB B VSS PULSE(0 1.8 0 10p 10p 1n 2n)

* AND2 gate implementation
MMN0 net26 B net6 vss nm1p2_svt_lp W=150n L=60n
MMN1 net6 A vss vss nm1p2_svt_lp W=150n L=60n
MPM0 net26 B vdd vdd pm1p2_svt_lp W=190n L=60n
MMP0 net26 A vdd vdd pm1p2_svt_lp W=190n L=60n

* Inverter for output
MMN_INV Y net26 vss vss nm1p2_svt_lp W=150n L=60n
MMP_INV Y net26 vdd vdd pm1p2_svt_lp W=190n L=60n

* Load capacitance
CL Y vss 10f

* Analysis
.TRAN 10p 8n

* Measurements
.MEASURE TRAN tpLH TRIG V(A) VAL=0.9 RISE=1 TARG V(Y) VAL=0.9 RISE=1
.MEASURE TRAN tpHL TRIG V(A) VAL=0.9 FALL=1 TARG V(Y) VAL=0.9 FALL=1

.END
