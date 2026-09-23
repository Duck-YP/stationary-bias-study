# EMPIRICAL numerical outcomes — P3 FedAvg coefficient

Simulation outcomes are not proven statements.

Matrix: `p3-d2-h4-small-step-confirmation`

Primary estimator: signed coordinatewise stationary mean-balance. The direct stationary sample mean is diagnostic only.

## Frozen theory and protocol

Theory: `{"B11_d": [-0.024459428167733, -0.030574285209666], "B11_d_sign_is_intrinsic": true, "B20_FA": [-0.096008032790415, -0.120010040988019], "H": 4, "S_C": [[0.413009404388715, 0.021943573667712], [0.021943573667712, 0.345611285266458]], "normalization": "C_hat = (b_hat - (gamma / N) * B11_d) / gamma^2", "remainder": "O(1/N + gamma)", "target_formula": "-((H-1)/4) A^{-1} T[C]"}`

Run matrix: `{"H_values": [4], "N_values": [64, 96, 128, 192], "all_unique": true, "chains": 32, "chains_per_setting": [8, 8, 8, 8], "gamma_equals_inverse_N": true, "matrix_id": "p3-d2-h4-small-step-confirmation", "seeds": [1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208], "settings": 4, "target": "h4-small-step", "unique_run_ids": 32}`

Bootstrap: `{"correction": "bonferroni", "marginal_diagnostic_percentile_level": 0.95, "marginal_diagnostic_quantiles": [0.025, 0.975], "preserve_same_seed_across_settings": true, "repetitions": 2000, "seed": 3902, "simultaneous_coordinate_percentile_level": 0.975, "simultaneous_familywise_confidence_level": 0.95, "simultaneous_quantiles": [0.0125, 0.9875], "unit": "seed_label_block"}`

## Coordinatewise settings

| H | N | gamma | delta | coordinate | estimator | C_mean | simultaneous_ci_low | simultaneous_ci_high | B20_FA_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 128 | 0.0078125 | 0.015625 | 0 | direct_sample_mean | 0.517668957 | -1.7787236 | 2.81406152 | -0.0960080328 |
| 4 | 128 | 0.0078125 | 0.015625 | 0 | stationary_mean_balance | -0.0951573435 | -0.0957224835 | -0.0945922035 | -0.0960080328 |
| 4 | 128 | 0.0078125 | 0.015625 | 1 | direct_sample_mean | 1.3447299 | -0.847484422 | 3.53694422 | -0.120010041 |
| 4 | 128 | 0.0078125 | 0.015625 | 1 | stationary_mean_balance | -0.118724594 | -0.119430992 | -0.118018195 | -0.120010041 |
| 4 | 192 | 0.00520833333 | 0.0104166667 | 0 | direct_sample_mean | -0.900147432 | -4.0723139 | 2.27201904 | -0.0960080328 |
| 4 | 192 | 0.00520833333 | 0.0104166667 | 0 | stationary_mean_balance | -0.0954055489 | -0.0959517287 | -0.0948593692 | -0.0960080328 |
| 4 | 192 | 0.00520833333 | 0.0104166667 | 1 | direct_sample_mean | 1.88511012 | -0.756170975 | 4.52639121 | -0.120010041 |
| 4 | 192 | 0.00520833333 | 0.0104166667 | 1 | stationary_mean_balance | -0.119107865 | -0.119790619 | -0.118425111 | -0.120010041 |
| 4 | 64 | 0.015625 | 0.03125 | 0 | direct_sample_mean | 0.233470451 | -0.676563765 | 1.14350467 | -0.0960080328 |
| 4 | 64 | 0.015625 | 0.03125 | 0 | stationary_mean_balance | -0.0943488558 | -0.0952045568 | -0.0934931549 | -0.0960080328 |
| 4 | 64 | 0.015625 | 0.03125 | 1 | direct_sample_mean | -0.0631416789 | -0.866754158 | 0.7404708 | -0.120010041 |
| 4 | 64 | 0.015625 | 0.03125 | 1 | stationary_mean_balance | -0.117500549 | -0.11857042 | -0.116430677 | -0.120010041 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 0 | direct_sample_mean | 0.283458997 | -1.21900264 | 1.78592063 | -0.0960080328 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 0 | stationary_mean_balance | -0.0950851738 | -0.0956593189 | -0.0945110287 | -0.0960080328 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 1 | direct_sample_mean | 0.436972367 | -0.918292343 | 1.79223708 | -0.120010041 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 1 | stationary_mean_balance | -0.118562196 | -0.119279838 | -0.117844554 | -0.120010041 |

## Extrapolated intercepts

| H | coordinate | beta0 | beta1 | simultaneous_ci_low | simultaneous_ci_high | B20_FA_component | intercept_theory_error | theory_covered_simultaneous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 0 | -0.0959727302 | 0.049843182 | -0.0964743358 | -0.0953790293 | -0.0960080328 | 3.53026221e-05 | True |
| 4 | 1 | -0.119958983 | 0.076041319 | -0.120585965 | -0.119216865 | -0.120010041 | 5.10583075e-05 | True |

## Frozen gates

| gate | scope | passed | detail |
| --- | --- | --- | --- |
| F0 | p3-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_1 | True | finite_stationary_eight_chains |
| F3 | H4_coordinate_0 | True | small_step_simultaneous_coverage |
| F3 | H4_coordinate_1 | True | small_step_simultaneous_coverage |
| F4 | p3-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_0 | True | small_step_signed_coordinate_direction |
| F4 | p3-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_1 | True | small_step_signed_coordinate_direction |
| F4 | p3-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_0 | True | small_step_signed_coordinate_direction |
| F4 | p3-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_1 | True | small_step_signed_coordinate_direction |
| F4 | p3-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_0 | True | small_step_signed_coordinate_direction |
| F4 | p3-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_1 | True | small_step_signed_coordinate_direction |
| F4 | p3-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_0 | True | small_step_signed_coordinate_direction |
| F4 | p3-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_1 | True | small_step_signed_coordinate_direction |
| F5 | p3-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_1 |  | direct_balance_diagnostic_only |
| F6 | frozen_matrix | True | all_settings_and_seeds_present |

## Interpretation boundary

This signed coordinatewise FedAvg-only analysis may establish empirical consistency or inconsistency with the candidate coefficient. It does not prove the theorem, prove multidimensional attribution, test the SCAFFOLD-minus-FedAvg difference, prove a SCAFFOLD control contribution, or cover heterogeneity, growing H, state-dependent noise, or the complete finite-N gamma-squared coefficient.

Manifest: `p3-d2-h4-small-step-confirmation`
