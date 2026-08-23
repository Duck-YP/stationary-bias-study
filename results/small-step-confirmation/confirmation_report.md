# Small-Step H=4 Confirmation

```text
Original preregistered coefficient-convergence result (thesis reference: P3-A):
P3A_STATUS = CONTRADICTION_CANDIDATE

This result is preserved and not overwritten.

The small-step confirmation (thesis reference: P3-A2) was designed after diagnosing
that the original H=4 contradiction may be sensitive to finite-gamma
linear extrapolation.
```

**Research status: CANDIDATE THEOREM. This simulation is not a proof.**

Frozen confirmation protocol commit: `a1f2e1bf712ec757963db4a5fb890ac02854d27e`

```text
directional_convergence = PASS
smallest_step_proximity = PASS
O_gamma_compatibility = PASS
validity = PASS
P3A2_STATUS = CONSISTENT_WITH_ASYMPTOTIC_COEFFICIENT
TRIGGER_H4_THEOREM_REAUDIT = NO
```

## Four frozen point estimates

| gamma | N | C_mean | C_ci_low | C_ci_high | error_to_theory | scaled_error |
| --- | --- | --- | --- | --- | --- | --- |
| 0.015625 | 64 | -0.572157079 | -0.575670814 | -0.568643344 | 0.0215929209 | 1.38194694 |
| 0.0104166667 | 96 | -0.579147509 | -0.581446607 | -0.576848411 | 0.0146024912 | 1.40183915 |
| 0.0078125 | 128 | -0.582794728 | -0.584911544 | -0.580677912 | 0.0109552723 | 1.40227485 |
| 0.00520833333 | 192 | -0.58587582 | -0.587793982 | -0.583957657 | 0.0078741805 | 1.51184266 |

## Preregistered gates

| gate_id | observed | threshold | status | notes |
| --- | --- | --- | --- | --- |
| V1_finite | PASS | Original P3 validity protocol | PASS | Core validity gate |
| V2_control_invariant | PASS | Original P3 validity protocol | PASS | Core validity gate |
| V3_estimator_agreement | PASS | Original P3 validity protocol | PASS | Core validity gate |
| V4_stationarity | PASS | Original P3 validity protocol | PASS | Core validity gate |
| V5_precision | PASS | Original P3 validity protocol | PASS | Core validity gate |
| A_directional_convergence | PASS | small reversal <= 1.0 combined SE and CI overlap >= 0.5 | PASS | reversals=[] |
| B_smallest_step_proximity | 0.013261777676873228 | 0.02 | PASS | Numerical adjudication tolerance, not a theorem error bound. |
| C_O_gamma_compatibility | 1.0939947203153932 | 2.0 | PASS | D_min=1.3819469; D_max=1.5118427; signs_compatible=True; near_zero=False |

The 2% smallest-step threshold is a numerical adjudication tolerance, not a mathematical error bound.

## Secondary diagnostic fits

| linear_beta0 | linear_beta0_ci_low | linear_beta0_ci_high | quadratic_beta0 | quadratic_beta0_ci_low | quadratic_beta0_ci_high | B_theory | role |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -0.592953109 | -0.595526267 | -0.590236465 | -0.592159976 | -0.599106027 | -0.585215969 | -0.59375 | SECONDARY_DIAGNOSTIC_ONLY |

Neither diagnostic fit overrides the primary gates.

## Interpretation

The new small-step confirmatory simulation is numerically consistent with the candidate H=4 asymptotic coefficient. The original P3 contradiction is therefore more plausibly attributable to finite-step extrapolation than to a persistent asymptotic discrepancy.

The original coefficient-convergence result remains `CONTRADICTION_CANDIDATE`; the confirmation does not rewrite its history or modify the candidate theorem.
