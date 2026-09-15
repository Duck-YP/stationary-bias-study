# P1 Fixed-gamma Large-N Matched Plateau

Run phase: **FORMAL**

Primary estimates use the stationary mean-balance estimator. Direct means remain diagnostics; matched differences and extrapolation uncertainty resample matched chain pairs.

The fixed step size permits O(gamma) finite-step contamination, so compatibility is assessed from plateau stability, sign, ordering, and proximity—not solely from whether a 95% interval contains the asymptotic target.

## Point estimates by client count

| algorithm | N | gamma | C_mean | C_ci_low | C_ci_high | B20_target | gate_pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| scaffold | 8 | 0.0416666667 | -0.176152404 | -0.183238012 | -0.169066795 | -0.1875 | True |
| fedavg | 8 | 0.0416666667 | -0.12274094 | -0.129884881 | -0.115597 | -0.125 | True |
| scaffold | 16 | 0.0416666667 | -0.181437846 | -0.184110936 | -0.178764757 | -0.1875 | True |
| fedavg | 16 | 0.0416666667 | -0.124180824 | -0.126887991 | -0.121473657 | -0.125 | True |
| scaffold | 32 | 0.0416666667 | -0.184786383 | -0.186420084 | -0.183152682 | -0.1875 | True |
| fedavg | 32 | 0.0416666667 | -0.125529249 | -0.127203537 | -0.123854961 | -0.125 | True |
| scaffold | 64 | 0.0416666667 | -0.187439074 | -0.18833028 | -0.186547869 | -0.1875 | True |
| fedavg | 64 | 0.0416666667 | -0.127182047 | -0.128059978 | -0.126304116 | -0.125 | True |
| scaffold | 128 | 0.0416666667 | -0.187598859 | -0.187864238 | -0.18733348 | -0.1875 | True |
| fedavg | 128 | 0.0416666667 | -0.126934601 | -0.127162941 | -0.126706261 | -0.125 | True |

## Pair-level SCAFFOLD-minus-FedAvg estimates

| N | gamma | Delta_C_mean | Delta_C_ci_low | Delta_C_ci_high | Delta_B20_target | pair_gate_pass |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | 0.0416666667 | -0.0534114634 | -0.0536139325 | -0.0532089944 | -0.0625 | True |
| 16 | 0.0416666667 | -0.0572570226 | -0.0573544573 | -0.057159588 | -0.0625 | True |
| 32 | 0.0416666667 | -0.059257134 | -0.0593236981 | -0.0591905699 | -0.0625 | True |
| 64 | 0.0416666667 | -0.0602570276 | -0.0603292856 | -0.0601847696 | -0.0625 | True |
| 128 | 0.0416666667 | -0.0606642584 | -0.0607276917 | -0.0606008252 | -0.0625 | True |

## Linear extrapolation in 1/N

| H | gamma | bootstrap_unit | bootstrap_repetitions | beta0_FA | beta0_FA_ci_low | beta0_FA_ci_high | beta1_FA | beta0_SCAFFOLD | beta0_SCAFFOLD_ci_low | beta0_SCAFFOLD_ci_high | beta1_SCAFFOLD | beta0_delta | beta0_delta_ci_low | beta0_delta_ci_high | beta1_delta | B20_FA_target | B20_SCAFFOLD_target | Delta_B20_target |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.0416666667 | matched_chain_pair | 2000 | -0.127146956 | -0.128300855 | -0.125959392 | 0.0378513274 | -0.188333186 | -0.189409297 | -0.187197028 | 0.100134658 | -0.0611862301 | -0.0612355063 | -0.0611424347 | 0.0622833309 | -0.125 | -0.1875 | -0.0625 |
