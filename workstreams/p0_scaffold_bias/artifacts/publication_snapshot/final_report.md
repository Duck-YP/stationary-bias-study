# Stationary-Bias Numerical Falsification Report

**Research status: CANDIDATE THEOREM.** This simulation is a falsification attempt, not a proof.

```text
P3A_STATUS = CONTRADICTION_CANDIDATE
P3B_STATUS = SUPPORT_N_NONVANISHING
NC1_STATUS = PASS
NC2_STATUS = PASS
NC3_STATUS = SANITY_CONSISTENT
NC4_STATUS = NOT_RUN_MISSING_APPROVED_RECURSION
OVERALL_P3_STATUS = CONTRADICTION_CANDIDATE
```

## Formal run ledger

- Expected independent chains: 168
- Completed independent chains: 168
- Invalid chains (nonfinite or control invariant): 0
- Precision-not-reached chains: 0

## Coefficient convergence (thesis reference: P3-A)

| H | gamma | N | C_mean | C_ci_low | C_ci_high | B_theory | precision_status | overall_validity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.020833333 | 48 | -0.18473771 | -0.18791078 | -0.18156465 | -0.1875 | reached | VALID |
| 2 | 0.03125 | 32 | -0.18382267 | -0.18519457 | -0.18245077 | -0.1875 | reached | VALID |
| 2 | 0.041666667 | 24 | -0.18302954 | -0.18477319 | -0.18128588 | -0.1875 | reached | VALID |
| 2 | 0.0625 | 16 | -0.17967812 | -0.1818874 | -0.17746885 | -0.1875 | reached | VALID |
| 2 | 0.083333333 | 12 | -0.17819585 | -0.18057423 | -0.17581748 | -0.1875 | reached | VALID |
| 4 | 0.020833333 | 48 | -0.56281134 | -0.56595843 | -0.55966425 | -0.59375 | reached | VALID |
| 4 | 0.03125 | 32 | -0.54829248 | -0.54970296 | -0.546882 | -0.59375 | reached | VALID |
| 4 | 0.041666667 | 24 | -0.53500374 | -0.53704459 | -0.53296289 | -0.59375 | reached | VALID |
| 4 | 0.0625 | 16 | -0.50628901 | -0.50820137 | -0.50437666 | -0.59375 | reached | VALID |
| 4 | 0.083333333 | 12 | -0.48305446 | -0.48580349 | -0.48030544 | -0.59375 | reached | VALID |

| H | beta0 | beta0_ci_low | beta0_ci_high | beta1 | B_theory | p3a_status |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | -0.18721386 | -0.18925032 | -0.18517537 | 0.1110487 | -0.1875 | SUPPORT |
| 4 | -0.58863303 | -0.59077575 | -0.58651352 | 1.284372 | -0.59375 | CONTRADICTION_CANDIDATE |

## Client-count scaling (thesis reference: P3-B)

| N | gamma | C_mean | C_ci_low | C_ci_high | overall_validity |
| --- | --- | --- | --- | --- | --- |
| 8 | 0.041666667 | -0.16873618 | -0.17542788 | -0.16204448 | VALID |
| 16 | 0.041666667 | -0.17804611 | -0.18039402 | -0.17569819 | VALID |
| 32 | 0.041666667 | -0.18471142 | -0.1858118 | -0.18361105 | VALID |
| 64 | 0.041666667 | -0.18667371 | -0.18770051 | -0.1856469 | VALID |
| 128 | 0.041666667 | -0.18759745 | -0.18799407 | -0.18720082 | VALID |

| H | gamma | alpha0 | alpha0_ci_low | alpha0_ci_high | alpha1 | p3b_status |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.041666667 | -0.1891448 | -0.19039779 | -0.18803492 | 0.16499257 | SUPPORT_N_NONVANISHING |

## Negative controls and boundary sanity (thesis reference: P3-C)

| control_name | gamma | N | H | target | estimate | ci_low | ci_high | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no_stochastic_noise | 0.0416666666666666 | 24 | 2 | 0.0 | -1.0453729711064724e-17 | -2.2752786655376943e-17 | 1.845327233247494e-18 | PASS |
| no_stochastic_noise | 0.0208333333333333 | 48 | 2 | 0.0 | -1.0730456940884472e-17 | -2.5994454205177313e-17 | 4.533540323408369e-18 | PASS |
| no_nonlinear_conversion | 0.0416666666666666 | 24 | 2 | 0.0 | 0.0 | 0.0 | 0.0 | PASS |
| no_nonlinear_conversion | 0.0208333333333333 | 48 | 2 | 0.0 | 0.0 | 0.0 | 0.0 | PASS |
| h1_boundary_sanity | 0.0416666666666666 | 24 | 1 | 0.0 | -0.0023448817821127878 | -0.00415649742875885 | -0.0005332661354667256 | SANITY_CONSISTENT |
| h1_boundary_sanity | 0.0208333333333333 | 48 | 1 | 0.0 | -0.00048669339114816264 | -0.003657538222475939 | 0.0026841514401796133 | SANITY_CONSISTENT |
| no_persistent_control_fluctuation |  |  |  |  |  |  |  | NOT_RUN_MISSING_APPROVED_RECURSION |

## Post-hoc negative-control estimator robustness audit

This audit was added after the frozen numerical protocol and is reported as a robustness check, not as a pre-registered falsification gate.

| Control | Setting | Frozen statistic | Independent/direct audit | Verdict |
| --- | --- | --- | --- | --- |
| NC1 deterministic | gamma=0.041666667, N=24, H=2 | b_balance=-1.045e-17; last max|x|=1.278e-15 | b_direct=5.393e-16, 95% CI [-1.49e-16, 1.228e-15], contains 0=True | PASS |
| NC1 deterministic | gamma=0.020833333, N=48, H=2 | b_balance=-1.073e-17; last max|x|=1.636e-14 | b_direct=-3.571e-15, 95% CI [-1.061e-14, 3.472e-15], contains 0=True | PASS |
| NC2 quadratic | gamma=0.041666667, N=24, H=2 | b_balance=0 structurally because q(x) is identically zero | b_direct=0.0007108, 95% CI [-0.000198, 0.00162], contains 0=True | PASS |
| NC2 quadratic | gamma=0.020833333, N=48, H=2 | b_balance=0 structurally because q(x) is identically zero | b_direct=0.0001916, 95% CI [-0.0003028, 0.0006861], contains 0=True | PASS |
| NC3 H=1 boundary | gamma=0.041666667, N=24, H=1 | normalized C_balance=-0.002345, 95% CI [-0.004156, -0.0005333] | b_direct=3.995e-05; agreement=pass; trend=smaller_gamma_closer_to_zero | SANITY_CONSISTENT |
| NC3 H=1 boundary | gamma=0.020833333, N=48, H=1 | normalized C_balance=-0.0004867, 95% CI [-0.003658, 0.002684] | b_direct=-0.0001004; agreement=pass; trend=smaller_gamma_closer_to_zero | SANITY_CONSISTENT |

The balance estimator is structurally zero for the quadratic objective because q(x) is identically zero; therefore the independent direct stationary-mean estimator is used as the robustness check.

For H=1, this is a boundary sanity check. The relevant quantity is the normalized residual after subtracting B10*gamma/N, not the raw stationary bias.

## Research interpretation

1. What the simulations support: coefficient convergence is `CONTRADICTION_CANDIDATE` and client-count scaling is `SUPPORT_N_NONVANISHING` under the frozen gates.
2. What remains inconclusive: any setting or fit explicitly marked `INCONCLUSIVE`, plus NC4, whose status is `NOT_RUN_MISSING_APPROVED_RECURSION`.
3. Any numerical contradiction: A strict contradiction candidate was triggered.
4. Any implementation concern: consult `falsification_gates.csv`; failed recursion, finite-state, stationarity, or estimator-agreement gates are never treated as theorem evidence.
5. Whether a human theorem re-audit is triggered: YES by the pre-registered contradiction rule. Independent human/advisor verification remains required regardless.

Allowed claim boundary: these numerical results may be described as consistent, inconclusive, or as a discrepancy requiring audit. They do not prove the candidate theorem and do not by themselves establish that it is false.
