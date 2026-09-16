# Formal coefficient analysis, d=2

## EMPIRICAL numerical outcomes

All numerical tables below are simulation outcomes, not proven statements.

Source commit: `85e97fa34e23084410c148b63d814c75d92dbc1e`

Config SHA-256: `f977860d1299ee9b3b94de0470dbe00fe486b3238c7df20ed9a09fd442cdb826`

Matrix: `p2-d2-h4-small-step-confirmation`

## Frozen inputs

Theory: `{"B11_d": [-0.024459428167733, -0.030574285209666], "B11_d_sign_is_intrinsic": true, "B20": [-0.152012718584823, -0.190015898231029], "B20_ctrl": [-0.056004685794409, -0.070005857243011], "B20_local": [-0.096008032790415, -0.120010040988019], "H": 4, "S_C": [[0.413009404388715, 0.021943573667712], [0.021943573667712, 0.345611285266458]], "normalization": "C_hat = (b_hat - (gamma / N) * B11_d) / gamma^2", "remainder": "O(1/N + gamma)"}`

Setting matrix: `{"H_values": [4], "N_values": [64, 96, 128, 192], "all_unique": true, "chains": 32, "chains_per_setting": [8, 8, 8, 8], "gamma_equals_inverse_N": true, "matrix_id": "p2-d2-h4-small-step-confirmation", "seeds": [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008], "settings": 4, "target": "h4-small-step", "unique_run_ids": 32}`

Seed block: `[1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008]`

Primary estimator: signed coordinatewise stationary mean-balance. The direct stationary sample mean remains diagnostic.

Stopping protocol: `{"absolute_half_width": 0.0025, "check_after_batches": 100, "coordinate_rule": "h_j <= max(0.0025, 0.10 * abs(B20_j(H)))", "extend_by_batches": 50, "relative_half_width": 0.1, "scope": "every_coordinate", "simultaneous_interval": "bonferroni_familywise_95_percent", "statistic": "primary_balance_normalized_coefficient", "stop_at_batches": 400, "stop_on_invalidity": true}`

Uncertainty: `{"coordinates": 2, "correction": "bonferroni", "degrees_of_freedom": 7, "familywise_confidence_level": 0.95, "marginal_diagnostic_confidence_level": 0.95, "method": "student_t_coordinatewise", "pool_coordinates": false, "simultaneous_coordinate_confidence_level": 0.975, "source": "eight_independent_chain_estimates"}`

Fit: `{"coefficient_estimate": "beta0_j", "delta": "gamma + 1/N", "model": "C_hat_j = beta0_j + beta1_j * delta", "per": ["H", "coordinate"], "response": "setting_mean_balance_C_hat_coordinate"}`

Bootstrap: `{"correction": "bonferroni", "marginal_diagnostic_percentile_level": 0.95, "marginal_diagnostic_quantiles": [0.025, 0.975], "preserve_same_seed_across_settings": true, "repetitions": 2000, "seed": 2902, "simultaneous_coordinate_percentile_level": 0.975, "simultaneous_familywise_confidence_level": 0.95, "simultaneous_quantiles": [0.0125, 0.9875], "unit": "seed_label_block"}`

## Coordinatewise settings

| H | N | gamma | delta | coordinate | estimator | C_mean | simultaneous_ci_low | simultaneous_ci_high | B20_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 64 | 0.015625 | 0.03125 | 0 | direct_sample_mean | 0.0733285039 | -1.2570607 | 1.40371771 | -0.152012719 |
| 4 | 64 | 0.015625 | 0.03125 | 1 | direct_sample_mean | -0.0440115748 | -0.580698148 | 0.492674998 | -0.190015898 |
| 4 | 64 | 0.015625 | 0.03125 | 0 | stationary_mean_balance | -0.145394625 | -0.146353615 | -0.144435635 | -0.152012719 |
| 4 | 64 | 0.015625 | 0.03125 | 1 | stationary_mean_balance | -0.180999296 | -0.182197745 | -0.179800847 | -0.190015898 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 0 | direct_sample_mean | 0.685218832 | -1.43762165 | 2.80805931 | -0.152012719 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 1 | direct_sample_mean | 0.265423281 | -1.61553638 | 2.14638294 | -0.190015898 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 0 | stationary_mean_balance | -0.147316118 | -0.148195432 | -0.146436804 | -0.152012719 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 1 | stationary_mean_balance | -0.183638389 | -0.184737407 | -0.182539371 | -0.190015898 |
| 4 | 128 | 0.0078125 | 0.015625 | 0 | direct_sample_mean | 0.565905796 | -2.00293034 | 3.13474193 | -0.152012719 |
| 4 | 128 | 0.0078125 | 0.015625 | 1 | direct_sample_mean | 1.02789729 | -1.16224617 | 3.21804074 | -0.190015898 |
| 4 | 128 | 0.0078125 | 0.015625 | 0 | stationary_mean_balance | -0.148360053 | -0.149145285 | -0.147574821 | -0.152012719 |
| 4 | 128 | 0.0078125 | 0.015625 | 1 | stationary_mean_balance | -0.185065961 | -0.186047544 | -0.184084378 | -0.190015898 |
| 4 | 192 | 0.00520833333 | 0.0104166667 | 0 | direct_sample_mean | 1.21616147 | -1.77346295 | 4.20578589 | -0.152012719 |
| 4 | 192 | 0.00520833333 | 0.0104166667 | 1 | direct_sample_mean | 0.1123387 | -2.68690906 | 2.91158646 | -0.190015898 |
| 4 | 192 | 0.00520833333 | 0.0104166667 | 0 | stationary_mean_balance | -0.1495082 | -0.150213081 | -0.148803319 | -0.152012719 |
| 4 | 192 | 0.00520833333 | 0.0104166667 | 1 | stationary_mean_balance | -0.18662646 | -0.187507555 | -0.185745365 | -0.190015898 |

## Extrapolated intercepts

| H | coordinate | beta0 | beta1 | simultaneous_ci_low | simultaneous_ci_high | B20_component | intercept_theory_error | theory_covered_simultaneous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 0 | -0.151477229 | 0.196222985 | -0.152243514 | -0.150778134 | -0.152012719 | 0.000535489375 | True |
| 4 | 1 | -0.189327282 | 0.268531472 | -0.190285415 | -0.188452956 | -0.190015898 | 0.000688616555 | True |

## Frozen F0–F6 gates

| gate | scope | passed | detail |
| --- | --- | --- | --- |
| F0 | all_settings | True | run_validity |
| F1 | H2 |  | not_applicable |
| F2 | H4_primary |  | reported_in_primary_output |
| F3 | H4_coordinate_0 | True | small_step_coverage |
| F3 | H4_coordinate_1 | True | small_step_coverage |
| F4 | p2-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_0 | True | small_step_direction_sign |
| F4 | p2-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_1 | True | small_step_direction_sign |
| F4 | p2-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_0 | True | small_step_direction_sign |
| F4 | p2-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_1 | True | small_step_direction_sign |
| F4 | p2-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_0 | True | small_step_direction_sign |
| F4 | p2-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_1 | True | small_step_direction_sign |
| F4 | p2-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_0 | True | small_step_direction_sign |
| F4 | p2-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_1 | True | small_step_direction_sign |
| F5 | p2-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-h4-small-step-confirmation__H4__N64__g0p0156250000__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-h4-small-step-confirmation__H4__N96__g0p0104166667__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-h4-small-step-confirmation__H4__N128__g0p0078125000__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-h4-small-step-confirmation__H4__N192__g0p0052083333__coordinate_1 |  | diagnostic_only |
| F6 | frozen_matrix | True | all_settings_and_seeds_present |

## Interpretation boundary

This is an empirical consistency analysis of signed coordinatewise vector coefficients. It does not prove the theorem or test FedAvg attribution, heterogeneity, growing H, state-dependent noise, d=5, rotation invariance, or the complete finite-N gamma-squared coefficient.

Manifest: `p2-d2-h4-small-step-confirmation`
