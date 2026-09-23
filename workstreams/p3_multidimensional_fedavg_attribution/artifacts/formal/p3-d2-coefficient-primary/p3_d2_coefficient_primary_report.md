# EMPIRICAL numerical outcomes — P3 FedAvg coefficient

Simulation outcomes are not proven statements.

Matrix: `p3-d2-coefficient-primary`

Primary estimator: signed coordinatewise stationary mean-balance. The direct stationary sample mean is diagnostic only.

## Frozen theory and protocol

Theory: `{"B11_d": [-0.024459428167733, -0.030574285209666], "B11_d_sign_is_intrinsic": true, "S_C": [[0.413009404388715, 0.021943573667712], [0.021943573667712, 0.345611285266458]], "by_H": {"2": {"B20_FA": [-0.032002677596805, -0.040003346996006]}, "4": {"B20_FA": [-0.096008032790415, -0.120010040988019]}}, "normalization": "C_hat = (b_hat - (gamma / N) * B11_d) / gamma^2", "remainder": "O(1/N + gamma)", "target_formula": "-((H-1)/4) A^{-1} T[C]"}`

Run matrix: `{"H_values": [2, 4], "N_values": [12, 16, 24, 32, 48], "all_unique": true, "chains": 80, "chains_per_setting": [8, 8, 8, 8, 8, 8, 8, 8, 8, 8], "gamma_equals_inverse_N": true, "matrix_id": "p3-d2-coefficient-primary", "seeds": [1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108], "settings": 10, "target": "primary", "unique_run_ids": 80}`

Bootstrap: `{"correction": "bonferroni", "marginal_diagnostic_percentile_level": 0.95, "marginal_diagnostic_quantiles": [0.025, 0.975], "preserve_same_seed_across_settings": true, "repetitions": 2000, "seed": 3901, "simultaneous_coordinate_percentile_level": 0.975, "simultaneous_familywise_confidence_level": 0.95, "simultaneous_quantiles": [0.0125, 0.9875], "unit": "seed_label_block"}`

## Coordinatewise settings

| H | N | gamma | delta | coordinate | estimator | C_mean | simultaneous_ci_low | simultaneous_ci_high | B20_FA_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 12 | 0.0833333333 | 0.166666667 | 0 | direct_sample_mean | -0.0508132062 | -0.124767516 | 0.0231411031 | -0.0320026776 |
| 2 | 12 | 0.0833333333 | 0.166666667 | 0 | stationary_mean_balance | -0.0326724288 | -0.0331825634 | -0.0321622943 | -0.0320026776 |
| 2 | 12 | 0.0833333333 | 0.166666667 | 1 | direct_sample_mean | -0.00431720422 | -0.267615248 | 0.258980839 | -0.040003347 |
| 2 | 12 | 0.0833333333 | 0.166666667 | 1 | stationary_mean_balance | -0.0403558586 | -0.0409931047 | -0.0397186125 | -0.040003347 |
| 2 | 16 | 0.0625 | 0.125 | 0 | direct_sample_mean | 0.0391027388 | -0.190931931 | 0.269137408 | -0.0320026776 |
| 2 | 16 | 0.0625 | 0.125 | 0 | stationary_mean_balance | -0.032657252 | -0.0334670348 | -0.0318474693 | -0.0320026776 |
| 2 | 16 | 0.0625 | 0.125 | 1 | direct_sample_mean | 0.080582024 | -0.327273296 | 0.488437344 | -0.040003347 |
| 2 | 16 | 0.0625 | 0.125 | 1 | stationary_mean_balance | -0.0404579542 | -0.0414695355 | -0.0394463728 | -0.040003347 |
| 2 | 24 | 0.0416666667 | 0.0833333333 | 0 | direct_sample_mean | -0.0732749016 | -0.693527919 | 0.546978115 | -0.0320026776 |
| 2 | 24 | 0.0416666667 | 0.0833333333 | 0 | stationary_mean_balance | -0.0323949344 | -0.0329126736 | -0.0318771952 | -0.0320026776 |
| 2 | 24 | 0.0416666667 | 0.0833333333 | 1 | direct_sample_mean | 0.112150976 | -0.263342673 | 0.487644625 | -0.040003347 |
| 2 | 24 | 0.0416666667 | 0.0833333333 | 1 | stationary_mean_balance | -0.0402514461 | -0.0408985748 | -0.0396043174 | -0.040003347 |
| 2 | 32 | 0.03125 | 0.0625 | 0 | direct_sample_mean | -0.0563081653 | -0.589791814 | 0.477175483 | -0.0320026776 |
| 2 | 32 | 0.03125 | 0.0625 | 0 | stationary_mean_balance | -0.0323588824 | -0.0329675648 | -0.0317502001 | -0.0320026776 |
| 2 | 32 | 0.03125 | 0.0625 | 1 | direct_sample_mean | 0.157672799 | -0.304052824 | 0.619398422 | -0.040003347 |
| 2 | 32 | 0.03125 | 0.0625 | 1 | stationary_mean_balance | -0.0402668839 | -0.0410276292 | -0.0395061386 | -0.040003347 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 0 | direct_sample_mean | 0.176744881 | -1.44920575 | 1.80269551 | -0.0320026776 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 0 | stationary_mean_balance | -0.0321414455 | -0.0328074945 | -0.0314753966 | -0.0320026776 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 1 | direct_sample_mean | -0.25916971 | -1.26239153 | 0.744052108 | -0.040003347 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 1 | stationary_mean_balance | -0.0400557704 | -0.0408883102 | -0.0392232305 | -0.040003347 |
| 4 | 12 | 0.0833333333 | 0.166666667 | 0 | direct_sample_mean | -0.102953622 | -0.189117041 | -0.0167902022 | -0.0960080328 |
| 4 | 12 | 0.0833333333 | 0.166666667 | 0 | stationary_mean_balance | -0.0849608787 | -0.0854425016 | -0.0844792558 | -0.0960080328 |
| 4 | 12 | 0.0833333333 | 0.166666667 | 1 | direct_sample_mean | -0.0727302314 | -0.344287159 | 0.198826697 | -0.120010041 |
| 4 | 12 | 0.0833333333 | 0.166666667 | 1 | stationary_mean_balance | -0.104285106 | -0.104888871 | -0.10368134 | -0.120010041 |
| 4 | 16 | 0.0625 | 0.125 | 0 | direct_sample_mean | -0.0170797722 | -0.250568955 | 0.216409411 | -0.0960080328 |
| 4 | 16 | 0.0625 | 0.125 | 0 | stationary_mean_balance | -0.0878294618 | -0.0886514396 | -0.087007484 | -0.0960080328 |
| 4 | 16 | 0.0625 | 0.125 | 1 | direct_sample_mean | 0.00454437474 | -0.404696474 | 0.413785223 | -0.120010041 |
| 4 | 16 | 0.0625 | 0.125 | 1 | stationary_mean_balance | -0.10825866 | -0.109283768 | -0.107233551 | -0.120010041 |
| 4 | 24 | 0.0416666667 | 0.0833333333 | 0 | direct_sample_mean | -0.120756583 | -0.767920712 | 0.526407546 | -0.0960080328 |
| 4 | 24 | 0.0416666667 | 0.0833333333 | 0 | stationary_mean_balance | -0.0904422698 | -0.0908939479 | -0.0899905918 | -0.0960080328 |
| 4 | 24 | 0.0416666667 | 0.0833333333 | 1 | direct_sample_mean | 0.0596955292 | -0.309948207 | 0.429339266 | -0.120010041 |
| 4 | 24 | 0.0416666667 | 0.0833333333 | 1 | stationary_mean_balance | -0.111972839 | -0.112536116 | -0.111409563 | -0.120010041 |
| 4 | 32 | 0.03125 | 0.0625 | 0 | direct_sample_mean | -0.167783606 | -0.670109145 | 0.334541933 | -0.0960080328 |
| 4 | 32 | 0.03125 | 0.0625 | 0 | stationary_mean_balance | -0.0918779593 | -0.0924933899 | -0.0912625288 | -0.0960080328 |
| 4 | 32 | 0.03125 | 0.0625 | 1 | direct_sample_mean | 0.108487324 | -0.413092446 | 0.630067095 | -0.120010041 |
| 4 | 32 | 0.03125 | 0.0625 | 1 | stationary_mean_balance | -0.114012991 | -0.114781732 | -0.113244249 | -0.120010041 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 0 | direct_sample_mean | 0.00922401673 | -1.4681254 | 1.48657343 | -0.0960080328 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 0 | stationary_mean_balance | -0.0932167907 | -0.0938707407 | -0.0925628407 | -0.0960080328 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 1 | direct_sample_mean | -0.351295039 | -1.28508175 | 0.58249167 | -0.120010041 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 1 | stationary_mean_balance | -0.115948479 | -0.11676569 | -0.115131269 | -0.120010041 |

## Extrapolated intercepts

| H | coordinate | beta0 | beta1 | simultaneous_ci_low | simultaneous_ci_high | B20_FA_component | intercept_theory_error | theory_covered_simultaneous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | -0.0320429883 | -0.00419478618 | -0.0326464908 | -0.0313780188 | -0.0320026776 | -4.03107153e-05 | True |
| 2 | 1 | -0.0400538937 | -0.0023341452 | -0.0408082738 | -0.0392220804 | -0.040003347 | -5.0546708e-05 | True |
| 4 | 0 | -0.0959717387 | 0.065804521 | -0.0965774402 | -0.0953321996 | -0.0960080328 | 3.62941196e-05 | True |
| 4 | 1 | -0.119805944 | 0.092977348 | -0.120563099 | -0.11900743 | -0.120010041 | 0.000204096864 | True |

## Frozen gates

| gate | scope | passed | detail |
| --- | --- | --- | --- |
| F0 | p3-d2-coefficient-primary__H2__N12__g0p0833333333__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H2__N12__g0p0833333333__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H2__N16__g0p0625000000__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H2__N16__g0p0625000000__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H2__N24__g0p0416666667__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H2__N24__g0p0416666667__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H2__N32__g0p0312500000__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H2__N32__g0p0312500000__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H2__N48__g0p0208333333__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H2__N48__g0p0208333333__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N12__g0p0833333333__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N12__g0p0833333333__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N16__g0p0625000000__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N16__g0p0625000000__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N24__g0p0416666667__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N24__g0p0416666667__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N32__g0p0312500000__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N32__g0p0312500000__coordinate_1 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N48__g0p0208333333__coordinate_0 | True | finite_stationary_eight_chains |
| F0 | p3-d2-coefficient-primary__H4__N48__g0p0208333333__coordinate_1 | True | finite_stationary_eight_chains |
| F1 | H2_coordinate_0 | True | primary_H2_simultaneous_coverage |
| F1 | H2_coordinate_1 | True | primary_H2_simultaneous_coverage |
| F2 | H4_coordinate_0 | True | reporting_only_primary_path |
| F2 | H4_coordinate_1 | True | reporting_only_primary_path |
| F3 | H4 |  | deferred_to_frozen_small_step |
| F4 | p3-d2-coefficient-primary__H2__N12__g0p0833333333__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H2__N12__g0p0833333333__coordinate_1 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H2__N16__g0p0625000000__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H2__N16__g0p0625000000__coordinate_1 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H2__N24__g0p0416666667__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H2__N24__g0p0416666667__coordinate_1 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H2__N32__g0p0312500000__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H2__N32__g0p0312500000__coordinate_1 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H2__N48__g0p0208333333__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H2__N48__g0p0208333333__coordinate_1 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N12__g0p0833333333__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N12__g0p0833333333__coordinate_1 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N16__g0p0625000000__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N16__g0p0625000000__coordinate_1 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N24__g0p0416666667__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N24__g0p0416666667__coordinate_1 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N32__g0p0312500000__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N32__g0p0312500000__coordinate_1 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N48__g0p0208333333__coordinate_0 | True | signed_coordinate_direction_warning |
| F4 | p3-d2-coefficient-primary__H4__N48__g0p0208333333__coordinate_1 | True | signed_coordinate_direction_warning |
| F5 | p3-d2-coefficient-primary__H2__N12__g0p0833333333__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H2__N12__g0p0833333333__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H2__N16__g0p0625000000__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H2__N16__g0p0625000000__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H2__N24__g0p0416666667__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H2__N24__g0p0416666667__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H2__N32__g0p0312500000__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H2__N32__g0p0312500000__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H2__N48__g0p0208333333__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H2__N48__g0p0208333333__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N12__g0p0833333333__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N12__g0p0833333333__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N16__g0p0625000000__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N16__g0p0625000000__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N24__g0p0416666667__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N24__g0p0416666667__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N32__g0p0312500000__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N32__g0p0312500000__coordinate_1 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N48__g0p0208333333__coordinate_0 |  | direct_balance_diagnostic_only |
| F5 | p3-d2-coefficient-primary__H4__N48__g0p0208333333__coordinate_1 |  | direct_balance_diagnostic_only |
| F6 | frozen_matrix | True | all_settings_and_seeds_present |

## Interpretation boundary

This signed coordinatewise FedAvg-only analysis may establish empirical consistency or inconsistency with the candidate coefficient. It does not prove the theorem, prove multidimensional attribution, test the SCAFFOLD-minus-FedAvg difference, prove a SCAFFOLD control contribution, or cover heterogeneity, growing H, state-dependent noise, or the complete finite-N gamma-squared coefficient.

Manifest: `p3-d2-coefficient-primary`
