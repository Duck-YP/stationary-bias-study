# Empirical numerical outcomes - matched control attribution

Simulation outcomes are not proven statements.

Primary estimator: paired signed coordinatewise stationary mean-balance.
The direct stationary-sample-mean difference is diagnostic only.

Matrix: `p3-d2-matched-attribution-h4-small-step-confirmation`

## Paired coordinatewise settings

| H | N | gamma | coordinate | D_mean | simultaneous_ci_low | simultaneous_ci_high | B20_ctrl_component |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 128 | 0.0078125 | 0 | -0.0536617931 | -0.0537105051 | -0.053613081 | -0.0560046858 |
| 4 | 128 | 0.0078125 | 1 | -0.0669152262 | -0.0669759726 | -0.0668544798 | -0.0700058572 |
| 4 | 192 | 0.00520833333 | 0 | -0.0544296825 | -0.0544493002 | -0.0544100648 | -0.0560046858 |
| 4 | 192 | 0.00520833333 | 1 | -0.0679273659 | -0.0679518559 | -0.0679028758 | -0.0700058572 |
| 4 | 64 | 0.015625 | 0 | -0.0514181352 | -0.0515083111 | -0.0513279592 | -0.0560046858 |
| 4 | 64 | 0.015625 | 1 | -0.0639637508 | -0.0640759585 | -0.0638515431 | -0.0700058572 |
| 4 | 96 | 0.0104166667 | 0 | -0.0529188403 | -0.0529854407 | -0.0528522399 | -0.0560046858 |
| 4 | 96 | 0.0104166667 | 1 | -0.0659358908 | -0.0660188919 | -0.0658528897 | -0.0700058572 |

## Extrapolated paired intercepts

| H | coordinate | beta0 | beta1 | simultaneous_ci_low | simultaneous_ci_high | B20_ctrl_component | theory_covered_simultaneous |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 0 | -0.0559261592 | 0.144335178 | -0.0559502332 | -0.0559007437 | -0.0560046858 | False |
| 4 | 1 | -0.0698956575 | 0.189957075 | -0.0699256032 | -0.0698639209 | -0.0700058572 | False |

## Prespecified falsification gates

| gate | scope | passed | detail |
| --- | --- | --- | --- |
| P3-F0 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N128 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N192 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N64 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N96 | True | paired_validity |
| P3-F3 | H4_coordinate_0 | False | small_step_paired_bootstrap_coverage |
| P3-F3 | H4_coordinate_1 | False | small_step_paired_bootstrap_coverage |
| P3-F4 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N128__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N128__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N192__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N192__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N64__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N64__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N96__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-h4-small-step-confirmation__H4__N96__coordinate_1 | True | signed_coordinate_direction |
| P3-F5 | paired_direct_sample |  | diagnostic_only |
| P3-F6 | frozen_matrix | True | all_settings_pairs_and_algorithm_members_present |
| P3-F7 | all_pairs | True | indexed_noise_blocks_identical |

## Interpretation boundary

The preregistered P3-F3 simultaneous-coverage criterion fails for H=4 coordinates 0 and 1. This frozen-gate result is an empirical discrepancy and does not by itself contradict the candidate asymptotic expansion, whose remainder does not imply exact finite-grid linearity.
This does not prove the decomposition, establish an algorithm ranking, cover heterogeneous clients, state-dependent noise, growing H, or dimensions beyond the frozen d=2 setting.
