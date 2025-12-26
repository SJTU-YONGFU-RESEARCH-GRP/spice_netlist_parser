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

* XOR2 implementation using pass transistors and inverters
* Input inverters
MM_INV_A AN A vss vss nm1p2_svt_lp W=150n L=60n
MMP_INV_A AN A vdd vdd pm1p2_svt_lp W=190n L=60n
MM_INV_B BN B vss vss nm1p2_svt_lp W=150n L=60n
MMP_INV_B BN B vdd vdd pm1p2_svt_lp W=190n L=60n

* Pass transistor network
MM_PT1 net19 AN BN vss vss nm1p2_svt_lp W=150n L=60n
MM_PT2 net19 A B vdd vdd pm1p2_svt_lp W=190n L=60n

* Transmission gate implementation
MM_TG1 net19 A BN net19 vdd pm1p2_svt_lp W=190n L=60n
MM_TG2 net19 AN B vss vss nm1p2_svt_lp W=150n L=60n

* Output inverter
MM_OUT Y net19 vss vss nm1p2_svt_lp W=150n L=60n
MMP_OUT Y net19 vdd vdd pm1p2_svt_lp W=190n L=60n

* Load capacitance
CL Y vss 10f

* Analysis
.TRAN 10p 8n

* Measurements
.MEASURE TRAN tpLH TRIG V(A) VAL=0.9 RISE=1 TARG V(Y) VAL=0.9 RISE=1
.MEASURE TRAN tpHL TRIG V(A) VAL=0.9 FALL=1 TARG V(Y) VAL=0.9 FALL=1

.END
