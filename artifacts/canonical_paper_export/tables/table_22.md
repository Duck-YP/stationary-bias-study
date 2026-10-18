# Table 22: Longest-window averaging statistics

Status: **supported**. Section C.4.3, page 39.

tab:e4-primary; seven display rows. Errors and training gaps use scale 1e6 and three decimals; individual test losses use six decimals, paired test-loss endpoints eight. All intervals are saved primary-family simultaneous intervals. Paired fields are read directly and checked for equality across their two duplicated algorithm records.

| quantity | SCAFFOLD | FedAvg | paired contrast |
| --- | --- | --- | --- |
| MSE | 17.267 [15.383, 19.151] | 10.878 [9.459, 12.297] |  |
| Train objective gap | 0.725 [0.630, 0.819] | 0.361 [0.295, 0.426] |  |
| Held-out log loss | 0.424889 [0.424879, 0.424899] | 0.424922 [0.424912, 0.424932] |  |
| Delta U |  |  | 6.378 [5.848, 6.908] |
| Delta V |  |  | 0.011 [-0.036, 0.058] |
| Delta train gap |  |  | [0.336, 0.393] |
| Delta held-out log loss |  |  | [-0.00003308, -0.00003231] |

Sources:

- `manuscript/supplementary_results/E4/BIAS_VARIANCE_MSE.csv`
- `manuscript/supplementary_results/E4/E4_v1_PROTOCOL_FROZEN.json`
