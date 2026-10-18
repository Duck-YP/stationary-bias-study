# Formal coefficient analysis, d=2

## EMPIRICAL numerical outcomes

All numerical tables below are simulation outcomes, not proven statements.

Source commit: `85e97fa34e23084410c148b63d814c75d92dbc1e`

Config SHA-256: `9409e25e7a417794c61d94eadbedc8dd0a498a79968d7d206ede205db3b73197`

Matrix: `p2-d2-coefficient-primary`

## Frozen inputs

Theory: `{"B11_d": [-0.024459428167733, -0.030574285209666], "B11_d_sign_is_intrinsic": true, "S_C": [[0.413009404388715, 0.021943573667712], [0.021943573667712, 0.345611285266458]], "by_H": {"2": {"B20": [-0.048004016395207, -0.060005020494009], "B20_ctrl": [-0.016001338798402, -0.020001673498003], "B20_local": [-0.032002677596805, -0.040003346996006]}, "4": {"B20": [-0.152012718584823, -0.190015898231029], "B20_ctrl": [-0.056004685794409, -0.070005857243011], "B20_local": [-0.096008032790415, -0.120010040988019]}}, "normalization": "C_hat = (b_hat - (gamma / N) * B11_d) / gamma^2", "remainder": "O(1/N + gamma)"}`

Setting matrix: `{"H_values": [2, 4], "N_values": [12, 16, 24, 32, 48], "all_unique": true, "chains": 80, "chains_per_setting": [8, 8, 8, 8, 8, 8, 8, 8, 8, 8], "gamma_equals_inverse_N": true, "matrix_id": "p2-d2-coefficient-primary", "seeds": [901, 902, 903, 904, 905, 906, 907, 908], "settings": 10, "target": "primary", "unique_run_ids": 80}`

Seed block: `[901, 902, 903, 904, 905, 906, 907, 908]`

Primary estimator: signed coordinatewise stationary mean-balance. The direct stationary sample mean remains diagnostic.

Stopping protocol: `{"absolute_half_width": 0.0025, "check_after_batches": 100, "coordinate_rule": "h_j <= max(0.0025, 0.10 * abs(B20_j(H)))", "extend_by_batches": 50, "relative_half_width": 0.1, "scope": "every_coordinate", "simultaneous_interval": "bonferroni_familywise_95_percent", "statistic": "primary_balance_normalized_coefficient", "stop_at_batches": 400, "stop_on_invalidity": true}`

Uncertainty: `{"coordinates": 2, "correction": "bonferroni", "degrees_of_freedom": 7, "familywise_confidence_level": 0.95, "marginal_diagnostic_confidence_level": 0.95, "method": "student_t_coordinatewise", "pool_coordinates": false, "simultaneous_coordinate_confidence_level": 0.975, "source": "eight_independent_chain_estimates"}`

Fit: `{"coefficient_estimate": "beta0_j", "delta": "gamma + 1/N", "model": "C_hat_j = beta0_j + beta1_j * delta", "per": ["H", "coordinate"], "response": "setting_mean_balance_C_hat_coordinate"}`

Bootstrap: `{"correction": "bonferroni", "marginal_diagnostic_percentile_level": 0.95, "marginal_diagnostic_quantiles": [0.025, 0.975], "preserve_same_seed_across_settings": true, "repetitions": 2000, "seed": 2901, "simultaneous_coordinate_percentile_level": 0.975, "simultaneous_familywise_confidence_level": 0.95, "simultaneous_quantiles": [0.0125, 0.9875], "unit": "seed_label_block"}`

## Coordinatewise settings

| H | N | gamma | delta | coordinate | estimator | C_mean | simultaneous_ci_low | simultaneous_ci_high | B20_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 12 | 0.0833333333 | 0.166666667 | 0 | direct_sample_mean | -0.00759101756 | -0.274305429 | 0.259123394 | -0.0480040164 |
| 2 | 12 | 0.0833333333 | 0.166666667 | 1 | direct_sample_mean | -0.215543099 | -0.383921564 | -0.0471646341 | -0.0600050205 |
| 2 | 12 | 0.0833333333 | 0.166666667 | 0 | stationary_mean_balance | -0.0460264607 | -0.0465654483 | -0.045487473 | -0.0480040164 |
| 2 | 12 | 0.0833333333 | 0.166666667 | 1 | stationary_mean_balance | -0.0568322575 | -0.0575058253 | -0.0561586896 | -0.0600050205 |
| 2 | 16 | 0.0625 | 0.125 | 0 | direct_sample_mean | -0.00991505295 | -0.36502678 | 0.345196674 | -0.0480040164 |
| 2 | 16 | 0.0625 | 0.125 | 1 | direct_sample_mean | -0.195680889 | -0.459918349 | 0.0685565702 | -0.0600050205 |
| 2 | 16 | 0.0625 | 0.125 | 0 | stationary_mean_balance | -0.0464535305 | -0.0470017018 | -0.0459053592 | -0.0480040164 |
| 2 | 16 | 0.0625 | 0.125 | 1 | stationary_mean_balance | -0.0575357438 | -0.058221345 | -0.0568501427 | -0.0600050205 |
| 2 | 24 | 0.0416666667 | 0.0833333333 | 0 | direct_sample_mean | 0.0398566053 | -0.456439699 | 0.53615291 | -0.0480040164 |
| 2 | 24 | 0.0416666667 | 0.0833333333 | 1 | direct_sample_mean | -0.259406499 | -0.784775148 | 0.26596215 | -0.0600050205 |
| 2 | 24 | 0.0416666667 | 0.0833333333 | 0 | stationary_mean_balance | -0.0468892912 | -0.04746258 | -0.0463160024 | -0.0480040164 |
| 2 | 24 | 0.0416666667 | 0.0833333333 | 1 | stationary_mean_balance | -0.0582548927 | -0.0589716077 | -0.0575381776 | -0.0600050205 |
| 2 | 32 | 0.03125 | 0.0625 | 0 | direct_sample_mean | 0.202965819 | -0.390557418 | 0.796489056 | -0.0480040164 |
| 2 | 32 | 0.03125 | 0.0625 | 1 | direct_sample_mean | -0.155306541 | -0.661213164 | 0.350600082 | -0.0600050205 |
| 2 | 32 | 0.03125 | 0.0625 | 0 | stationary_mean_balance | -0.047043696 | -0.0477375441 | -0.0463498479 | -0.0480040164 |
| 2 | 32 | 0.03125 | 0.0625 | 1 | stationary_mean_balance | -0.0585360146 | -0.0594034078 | -0.0576686214 | -0.0600050205 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 0 | direct_sample_mean | 0.369064424 | -0.253505018 | 0.991633867 | -0.0480040164 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 1 | direct_sample_mean | -0.452487282 | -1.47697781 | 0.572003241 | -0.0600050205 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 0 | stationary_mean_balance | -0.0472515656 | -0.0478105713 | -0.0466925598 | -0.0480040164 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 1 | stationary_mean_balance | -0.0588844845 | -0.0595832761 | -0.0581856929 | -0.0600050205 |
| 4 | 12 | 0.0833333333 | 0.166666667 | 0 | direct_sample_mean | -0.0803475765 | -0.331546733 | 0.17085158 | -0.152012719 |
| 4 | 12 | 0.0833333333 | 0.166666667 | 1 | direct_sample_mean | -0.300743172 | -0.464236547 | -0.137249798 | -0.190015898 |
| 4 | 12 | 0.0833333333 | 0.166666667 | 0 | stationary_mean_balance | -0.120168738 | -0.120928742 | -0.119408734 | -0.152012719 |
| 4 | 12 | 0.0833333333 | 0.166666667 | 1 | stationary_mean_balance | -0.14720919 | -0.148145556 | -0.146272824 | -0.190015898 |
| 4 | 16 | 0.0625 | 0.125 | 0 | direct_sample_mean | -0.0984319595 | -0.453182643 | 0.256318724 | -0.152012719 |
| 4 | 16 | 0.0625 | 0.125 | 1 | direct_sample_mean | -0.294331428 | -0.557377028 | -0.0312858293 | -0.190015898 |
| 4 | 16 | 0.0625 | 0.125 | 0 | stationary_mean_balance | -0.126992436 | -0.127764735 | -0.126220137 | -0.152012719 |
| 4 | 16 | 0.0625 | 0.125 | 1 | stationary_mean_balance | -0.156289412 | -0.157243862 | -0.155334962 | -0.190015898 |
| 4 | 24 | 0.0416666667 | 0.0833333333 | 0 | direct_sample_mean | -0.0734352324 | -0.57781667 | 0.430946205 | -0.152012719 |
| 4 | 24 | 0.0416666667 | 0.0833333333 | 1 | direct_sample_mean | -0.29963503 | -0.777816454 | 0.178546395 | -0.190015898 |
| 4 | 24 | 0.0416666667 | 0.0833333333 | 0 | stationary_mean_balance | -0.134997628 | -0.135678255 | -0.134317 | -0.152012719 |
| 4 | 24 | 0.0416666667 | 0.0833333333 | 1 | stationary_mean_balance | -0.166959722 | -0.16780708 | -0.166112363 | -0.190015898 |
| 4 | 32 | 0.03125 | 0.0625 | 0 | direct_sample_mean | 0.12067711 | -0.531874159 | 0.773228379 | -0.152012719 |
| 4 | 32 | 0.03125 | 0.0625 | 1 | direct_sample_mean | -0.268464685 | -0.781219221 | 0.24428985 | -0.190015898 |
| 4 | 32 | 0.03125 | 0.0625 | 0 | stationary_mean_balance | -0.13875372 | -0.139400848 | -0.138106591 | -0.152012719 |
| 4 | 32 | 0.03125 | 0.0625 | 1 | stationary_mean_balance | -0.172045623 | -0.172853629 | -0.171237617 | -0.190015898 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 0 | direct_sample_mean | 0.258999649 | -0.347830525 | 0.865829824 | -0.152012719 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 1 | direct_sample_mean | -0.513795096 | -1.54383788 | 0.516247687 | -0.190015898 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 0 | stationary_mean_balance | -0.142920415 | -0.143500951 | -0.14233988 | -0.152012719 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 1 | stationary_mean_balance | -0.177678787 | -0.178403856 | -0.176953718 | -0.190015898 |

## Extrapolated intercepts

| H | coordinate | beta0 | beta1 | simultaneous_ci_low | simultaneous_ci_high | B20_component | intercept_theory_error | theory_covered_simultaneous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | -0.047671279 | 0.00979168913 | -0.0482374437 | -0.0471965275 | -0.0480040164 | 0.000332737409 | True |
| 2 | 1 | -0.0595811057 | 0.0164079351 | -0.0602886041 | -0.0589882748 | -0.0600050205 | 0.000423914774 | True |
| 4 | 0 | -0.150261357 | 0.182554114 | -0.150890645 | -0.149751845 | -0.152012719 | 0.0017513619 | False |
| 4 | 1 | -0.187452381 | 0.244339146 | -0.188235134 | -0.186816469 | -0.190015898 | 0.00256351676 | False |

## Frozen F0–F6 gates

| gate | scope | passed | detail |
| --- | --- | --- | --- |
| F0 | all_settings | True | run_validity |
| F1 | H2_coordinate_0 | True | simultaneous_bootstrap_target_coverage |
| F1 | H2_coordinate_1 | True | simultaneous_bootstrap_target_coverage |
| F2 | H4_coordinate_0 | True | reporting_only_primary_grid |
| F2 | H4_coordinate_1 | True | reporting_only_primary_grid |
| F3 | H4 |  | deferred_to_frozen_small_step |
| F4 | H4 |  | deferred_to_frozen_small_step |
| F5 | p2-d2-coefficient-primary__H2__N12__g0p0833333333__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H2__N12__g0p0833333333__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H2__N16__g0p0625000000__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H2__N16__g0p0625000000__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H2__N24__g0p0416666667__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H2__N24__g0p0416666667__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H2__N32__g0p0312500000__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H2__N32__g0p0312500000__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H2__N48__g0p0208333333__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H2__N48__g0p0208333333__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N12__g0p0833333333__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N12__g0p0833333333__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N16__g0p0625000000__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N16__g0p0625000000__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N24__g0p0416666667__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N24__g0p0416666667__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N32__g0p0312500000__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N32__g0p0312500000__coordinate_1 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N48__g0p0208333333__coordinate_0 |  | diagnostic_only |
| F5 | p2-d2-coefficient-primary__H4__N48__g0p0208333333__coordinate_1 |  | diagnostic_only |
| F6 | frozen_matrix | True | all_settings_and_seeds_present |

## Interpretation boundary

This is an empirical consistency analysis of signed coordinatewise vector coefficients. It does not prove the theorem or test FedAvg attribution, heterogeneity, growing H, state-dependent noise, d=5, rotation invariance, or the complete finite-N gamma-squared coefficient.

Manifest: `p2-d2-coefficient-primary`
