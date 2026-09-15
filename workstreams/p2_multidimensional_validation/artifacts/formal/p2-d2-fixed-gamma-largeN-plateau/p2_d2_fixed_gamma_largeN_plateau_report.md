# P2 d=2 fixed-gamma large-N plateau

Verdict: **PASS**

Source commit: `c9c21e71710e4d8dc24b540e3c489f68debef73c`
Matrix: `p2-d2-fixed-gamma-largeN-plateau`
Primary estimator: `stationary_mean_balance`; direct sample means are diagnostic only.

The fit is `C_hat_j(N) = beta0_j + beta1_j/N`. Because gamma is fixed at 1/24,
the empirical plateau is compared with `B20(H=2) + O(gamma)`; exact B20 interval
coverage is reported only as a diagnostic and is not a PASS requirement.

## Per-N primary estimates

| N | inverse_N | coordinate | C_mean | simultaneous_ci_low | simultaneous_ci_high | B20_component |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | 0.125 | 0 | -0.0451008325 | -0.0472166254 | -0.0429850396 | -0.0480040164 |
| 8 | 0.125 | 1 | -0.056050339 | -0.0586946436 | -0.0534060345 | -0.0600050205 |
| 16 | 0.0625 | 0 | -0.0467698855 | -0.0475176825 | -0.0460220886 | -0.0480040164 |
| 16 | 0.0625 | 1 | -0.0581138712 | -0.059048779 | -0.0571789634 | -0.0600050205 |
| 32 | 0.03125 | 0 | -0.0478765996 | -0.0482599912 | -0.047493208 | -0.0480040164 |
| 32 | 0.03125 | 1 | -0.0594847311 | -0.0599640016 | -0.0590054605 | -0.0600050205 |
| 64 | 0.015625 | 0 | -0.0481662686 | -0.0483484961 | -0.0479840411 | -0.0480040164 |
| 64 | 0.015625 | 1 | -0.0598409423 | -0.0600687634 | -0.0596131213 | -0.0600050205 |
| 128 | 0.0078125 | 0 | -0.0483303893 | -0.0484244437 | -0.048236335 | -0.0480040164 |
| 128 | 0.0078125 | 1 | -0.0600432847 | -0.0601605958 | -0.0599259737 | -0.0600050205 |

## Fixed-gamma large-N intercepts

| coordinate | B20_component | beta0 | simultaneous_ci_low | simultaneous_ci_high | beta0_minus_B20 | beta0_minus_B20_over_gamma | beta1 | B20_covered_simultaneous_diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | -0.0480040164 | -0.0486142501 | -0.0489079076 | -0.0483504003 | -0.000610233693 | -0.0146456086 | 0.0281900381 | False |
| 1 | -0.0600050205 | -0.0603951818 | -0.0607621802 | -0.0600655664 | -0.00039016135 | -0.0093638724 | 0.0348603494 | False |

## Validity diagnostics

| N | coordinate | finite_state_pass | zero_sum_control_pass | stationarity_chain_count | stationarity_pass | validity_pass | stopping_reason | max_batches_used |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 0 | True | True | 8 | True | True | PRECISION_REACHED | 100 |
| 8 | 1 | True | True | 8 | True | True | PRECISION_REACHED | 100 |
| 16 | 0 | True | True | 8 | True | True | PRECISION_REACHED | 100 |
| 16 | 1 | True | True | 8 | True | True | PRECISION_REACHED | 100 |
| 32 | 0 | True | True | 8 | True | True | PRECISION_REACHED | 100 |
| 32 | 1 | True | True | 8 | True | True | PRECISION_REACHED | 100 |
| 64 | 0 | True | True | 8 | True | True | PRECISION_REACHED | 100 |
| 64 | 1 | True | True | 8 | True | True | PRECISION_REACHED | 100 |
| 128 | 0 | True | True | 8 | True | True | PRECISION_REACHED | 100 |
| 128 | 1 | True | True | 8 | True | True | PRECISION_REACHED | 100 |

## Falsification gates

| gate | scope | passed | scientific_warning | detail |
| --- | --- | --- | --- | --- |
| F0 | all_N_settings | True | False | finite_state_zero_sum_control_and_stationarity |
| F1 | frozen_matrix | True | False | all_five_N_settings_and_all_eight_seeds_present |
| F2 | coordinate_1 | True | False | finite_intercept_and_bootstrap_interval |
| F3 | coordinate_1 | True | False | {"N128_closer_to_beta0_than_N8": true, "per_N_sign_consistent": true, "simultaneous_interval_excludes_zero": true} |
| F4 | coordinate_1 | True | False | beta0_minus_B20=-0.00061023369259453203;scaled=-0.014645608622268791 |
| F5 | coordinate_1 |  | False | diagnostic_only_B20_coverage=False |
| F6 | coordinate_1 | True | False | {"large_N_magnitude_excess": false, "near_zero_intercept": false, "repeated_per_N_sign_changes": false, "theory_sign_reversed": false} |
| F2 | coordinate_2 | True | False | finite_intercept_and_bootstrap_interval |
| F3 | coordinate_2 | True | False | {"N128_closer_to_beta0_than_N8": true, "per_N_sign_consistent": true, "simultaneous_interval_excludes_zero": true} |
| F4 | coordinate_2 | True | False | beta0_minus_B20=-0.00039016135013247161;scaled=-0.0093638724031793324 |
| F5 | coordinate_2 |  | False | diagnostic_only_B20_coverage=False |
| F6 | coordinate_2 | True | False | {"large_N_magnitude_excess": false, "near_zero_intercept": false, "repeated_per_N_sign_changes": false, "theory_sign_reversed": false} |

## Figures

- `p2_d2_fixed_gamma_largeN_coordinate_1.png`
- `p2_d2_fixed_gamma_largeN_coordinate_2.png`

## Interpretation boundary

This is an empirical fixed-gamma consistency test. It is not a proof and does not
require beta0 confidence intervals to contain the asymptotic B20 value exactly.
The finite-gamma discrepancy is shown explicitly above.
