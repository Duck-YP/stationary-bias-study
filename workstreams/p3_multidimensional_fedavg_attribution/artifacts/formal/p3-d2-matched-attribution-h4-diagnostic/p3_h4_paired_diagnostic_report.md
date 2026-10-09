# P3 H=4 paired attribution discrepancy diagnostic

**Descriptive classification:** `finite_grid_higher_order_curvature_consistent`.

## Evidence scope

This analysis reads the frozen primary and H=4 smaller-step paired summaries. It does not execute a stationary production simulation or redefine a preregistered gate. The implementation target satisfies `B20_SCAF - B20_FA = B20_ctrl`, with theorem-scale remainder `O(gamma + 1/N)`. The saved H=4 simultaneous-coverage results remain unchanged. Finite-grid consistency cannot prove the asymptotic expansion or uniquely identify an analytic next-order coefficient.

## Exact estimators

The saved primary quantities are `C_alg = (b_alg - (gamma/N) B11_d) / gamma^2` for both algorithms and `D = C_SCAF - C_FA = (b_SCAF - b_FA) / gamma^2`. The same signed, coordinate-ordered `B11_d` is used on both sides, so it cancels exactly in `D`. The mean-balance `b_alg` is constructed from pre-update local `q` states.

## Scaling evidence

| coordinate | delta_min | delta_max | abs_e_Delta_at_delta_min | abs_e_Delta_at_delta_max | e_Delta_over_delta_min | e_Delta_over_delta_max | tail_e_Delta_over_delta_relative_range | loglog_slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.010416667 | 0.16666667 | 0.0015750033 | 0.020204954 | 0.12122972 | 0.15120031 | 0.029734418 | 0.92678217 |
| 1 | 0.010416667 | 0.16666667 | 0.0020784914 | 0.026346032 | 0.15807619 | 0.19953517 | 0.031488247 | 0.92250098 |

Across both coordinates, `|e_Delta|` decreases at every step toward the smallest delta. The scaled residual stays bounded and becomes comparatively stable on the four-point smaller-step tail; no nonzero plateau is visible on the observed grid. This is consistency evidence, not a theorem proof.

## Nested-window linear extrapolation (post-hoc)

| source | drop_count | coordinate | point_count | max_delta | beta0 | beta0_simultaneous_ci_low | beta0_simultaneous_ci_high | B20_ctrl | absolute_theory_distance | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| smaller_step | 0 | 0 | 4 | 0.03125 | -0.055926159 | -0.055948575 | -0.055899322 | -0.056004686 | 7.8526591e-05 | 5.8877387e-06 |
| smaller_step | 0 | 1 | 4 | 0.03125 | -0.069895658 | -0.069923588 | -0.069862223 | -0.070005857 | 0.00011019971 | 8.4381431e-06 |
| smaller_step | 1 | 0 | 3 | 0.020833333 | -0.055936369 | -0.055973158 | -0.055889954 | -0.056004686 | 6.8317099e-05 | 5.8776224e-06 |
| smaller_step | 1 | 1 | 3 | 0.020833333 | -0.069913374 | -0.069959272 | -0.069855583 | -0.070005857 | 9.2483667e-05 | 7.7320261e-06 |
| combined | 0 | 0 | 9 | 0.16666667 | -0.055232988 | -0.055297546 | -0.05517149 | -0.056004686 | 0.00077169761 | 0.00041339317 |
| combined | 0 | 1 | 9 | 0.16666667 | -0.068940065 | -0.069019813 | -0.068864392 | -0.070005857 | 0.0010657918 | 0.0005649398 |
| combined | 6 | 0 | 3 | 0.020833333 | -0.055936369 | -0.055974487 | -0.055891966 | -0.056004686 | 6.8317099e-05 | 5.8776224e-06 |
| combined | 6 | 1 | 3 | 0.020833333 | -0.069913374 | -0.069960891 | -0.069858046 | -0.070005857 | 9.2483667e-05 | 7.7320261e-06 |

Windows are deterministic suffixes formed only by repeatedly dropping the largest delta and stopping at three points. No grid point is selected by closeness to theory. For both coordinates, the combined-window intercept distance decreases at every nested step.

## Linear versus quadratic curvature diagnostic

**POST-HOC DIAGNOSTIC ONLY — DOES NOT REDEFINE THE PREREGISTERED GATE.**

| source | coordinate | model | point_count | beta0 | B20_ctrl | absolute_theory_distance | rmse | design_condition_number | stability_warning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 0 | linear | 5 | -0.054323767 | -0.056004686 | 0.0016809189 | 0.00029847323 | 22.488502 | NONE |
| primary | 1 | linear | 5 | -0.067694319 | -0.070005857 | 0.0023115378 | 0.00040423531 | 22.488502 | NONE |
| primary | 0 | quadratic | 5 | -0.056026247 | -0.056004686 | 2.1561355e-05 | 2.0088446e-06 | 657.57387 | NONE |
| primary | 1 | quadratic | 5 | -0.06999997 | -0.070005857 | 5.8872284e-06 | 4.5332513e-06 | 657.57387 | NONE |
| smaller_step | 0 | linear | 4 | -0.055926159 | -0.056004686 | 7.8526591e-05 | 5.8877387e-06 | 129.86522 | NONE |
| smaller_step | 1 | linear | 4 | -0.069895658 | -0.070005857 | 0.00011019971 | 8.4381431e-06 | 129.86522 | NONE |
| smaller_step | 0 | quadratic | 4 | -0.055958808 | -0.056004686 | 4.5877502e-05 | 4.2719595e-06 | 20816.767 | LOW_DF_OR_HIGH_CONDITION_INTERPRET_CAUTIOUSLY |
| smaller_step | 1 | quadratic | 4 | -0.069948347 | -0.070005857 | 5.7510139e-05 | 5.3337528e-06 | 20816.767 | LOW_DF_OR_HIGH_CONDITION_INTERPRET_CAUTIOUSLY |
| combined | 0 | linear | 9 | -0.055232988 | -0.056004686 | 0.00077169761 | 0.00041339317 | 19.752702 | NONE |
| combined | 1 | linear | 9 | -0.068940065 | -0.070005857 | 0.0010657918 | 0.0005649398 | 19.752702 | NONE |
| combined | 0 | quadratic | 9 | -0.056008582 | -0.056004686 | 3.8960221e-06 | 5.6463388e-06 | 465.60819 | NONE |
| combined | 1 | quadratic | 9 | -0.070000016 | -0.070005857 | 5.8412811e-06 | 6.4176715e-06 | 465.60819 | NONE |

The combined quadratic intercept is within about 6e-6 of theory in both coordinates and reduces residual RMSE by roughly two orders of magnitude versus the combined linear model. The smaller-step quadratic has only one residual degree of freedom and a large raw-design condition number, so it is explicitly treated as unstable supporting evidence rather than a new gate.

## Same-pair attribution

| coordinate | dominant_source | smallest_delta_e_SCAF | smallest_delta_e_FA | smallest_delta_e_Delta | scaffold_share_of_difference_at_smallest_delta | fedavg_cancellation_share_at_smallest_delta | difference_abs_contraction_smallest_over_largest |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | SCAFFOLD_RESIDUAL_WITH_FEDAVG_PARTIAL_CANCELLATION | 0.0020824554 | 0.00050745213 | 0.0015750033 | 1.3221912 | 0.32219116 | 0.077951343 |
| 1 | SCAFFOLD_RESIDUAL_WITH_FEDAVG_PARTIAL_CANCELLATION | 0.0028618461 | 0.00078335468 | 0.0020784914 | 1.3768862 | 0.37688618 | 0.078892008 |

At every saved point and in both coordinates, the SCAFFOLD residual is larger in magnitude than the FedAvg residual and has the same sign; FedAvg therefore partially cancels it. The remaining paired discrepancy is SCAFFOLD-residual dominated, while both algorithm residuals contract toward zero.

## Implementation audit

| check | status | evidence |
| --- | --- | --- |
| paired_noise_indexing | PASS | index-keyed block/vector residual=0.000e+00; raw CRN flags all true=True |
| initial_state | PASS | both algorithms are initialized from the same configured x_star; SCAFFOLD controls start at zero |
| estimator_normalization | PASS | maximum reconstructed raw-row identity error=1.017e-13 |
| B11_subtraction | PASS | the same coordinate-ordered B11_d is subtracted from both algorithms before differencing |
| D_identity | PASS | max_abs_D_minus_C_difference=1.180e-16 |
| residual_identity | PASS | max_abs_residual_identity_error=9.714e-17 |
| local_update_timing | PASS | reference loop uses pre-update q, then gradient+control+noise, endpoint average, then control refresh |
| mean_balance_pre_update_state | PASS | reference/production qbar max residual=0.000e+00 |
| zero_sum_controls | PASS | saved maximum control-sum error=7.272e-12 |
| burn_in_alignment | PASS | one shared paired block advances both states through the same configured burn-in cursor |
| batch_alignment | PASS | one shared paired block collects both algorithms over identical batch boundaries |
| stopping_rule_alignment | PASS | stopping is evaluated once on the paired difference and applies to the whole paired setting |
| seed_alignment | PASS | every saved setting contains both coordinates for each of all eight paired seeds |
| fixed_seed_reference_kernel | PASS | seed 2101, H=4, N=12, 3 rounds; max residual=0.000e+00 |
| coordinate_equivariance | PASS | 30-degree paired SCAFFOLD/FedAvg/difference smoke max residual=1.256e-15 |

## Interpretation boundary

The original H=4 primary and smaller-step empirical results are preserved. This post-hoc diagnostic does not redefine either preregistered gate, and numerical consistency is not mathematical proof.
