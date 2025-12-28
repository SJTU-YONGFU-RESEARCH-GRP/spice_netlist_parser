Test Circuit: INV Gate

* Power supplies
V1 vdd 0 1.8
V2 vss 0 0

* Input stimulus (will be controlled by test vectors)
V3 A vss PULSE(0 1.8 0 10p 10p 1n 2n)

* INV gate implementation
MMN0 Y A vss vss nm1p2_svt_lp W=150n L=60n
MMP0 Y A vdd vdd pm1p2_svt_lp W=190n L=60n

* Load capacitance
CLoad Y vss 10f

* Analysis
.TRAN 10p 4n

* Measurements
.MEASURE TRAN tpLH TRIG V(A) VAL=0.9 RISE=1 TARG V(Y) VAL=0.9 RISE=1
.MEASURE TRAN tpHL TRIG V(A) VAL=0.9 FALL=1 TARG V(Y) VAL=0.9 FALL=1

.END
