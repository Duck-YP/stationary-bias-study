# Empirical numerical outcomes - matched control attribution

Simulation outcomes are not proven statements.

Primary estimator: paired signed coordinatewise stationary mean-balance.
The direct stationary-sample-mean difference is diagnostic only.

Matrix: `p3-d2-matched-attribution-primary`

## Paired coordinatewise settings

| H | N | gamma | coordinate | D_mean | simultaneous_ci_low | simultaneous_ci_high | B20_ctrl_component |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 12 | 0.0833333333 | 0 | -0.0137997287 | -0.0138931748 | -0.0137062826 | -0.0160013388 |
| 2 | 12 | 0.0833333333 | 1 | -0.0170345434 | -0.0171498816 | -0.0169192052 | -0.0200016735 |
| 2 | 16 | 0.0625 | 0 | -0.0143363728 | -0.0143873417 | -0.014285404 | -0.0160013388 |
| 2 | 16 | 0.0625 | 1 | -0.0177541824 | -0.0178173173 | -0.0176910475 | -0.0200016735 |
| 2 | 24 | 0.0416666667 | 0 | -0.0149307327 | -0.014954088 | -0.0149073774 | -0.0160013388 |
| 2 | 24 | 0.0416666667 | 1 | -0.0185488709 | -0.018577886 | -0.0185198558 | -0.0200016735 |
| 2 | 32 | 0.03125 | 0 | -0.0151952014 | -0.0152131555 | -0.0151772472 | -0.0160013388 |
| 2 | 32 | 0.03125 | 1 | -0.0189069177 | -0.0189292604 | -0.018884575 | -0.0200016735 |
| 2 | 48 | 0.0208333333 | 0 | -0.0154708296 | -0.0155093082 | -0.0154323509 | -0.0160013388 |
| 2 | 48 | 0.0208333333 | 1 | -0.0192796591 | -0.019327612 | -0.0192317062 | -0.0200016735 |
| 4 | 12 | 0.0833333333 | 0 | -0.0357997322 | -0.0362230091 | -0.0353764553 | -0.0560046858 |
| 4 | 12 | 0.0833333333 | 1 | -0.043659825 | -0.0441757662 | -0.0431438838 | -0.0700058572 |
| 4 | 16 | 0.0625 | 0 | -0.0398641588 | -0.0401451895 | -0.0395831281 | -0.0560046858 |
| 4 | 16 | 0.0625 | 1 | -0.0489045608 | -0.0492488134 | -0.0485603083 | -0.0700058572 |
| 4 | 24 | 0.0416666667 | 0 | -0.0445846423 | -0.0447116652 | -0.0444576193 | -0.0560046858 |
| 4 | 24 | 0.0416666667 | 1 | -0.0550298563 | -0.0551863498 | -0.0548733628 | -0.0700058572 |
| 4 | 32 | 0.03125 | 0 | -0.0471945322 | -0.0473317856 | -0.0470572787 | -0.0560046858 |
| 4 | 32 | 0.03125 | 1 | -0.0584324756 | -0.0586022264 | -0.0582627248 | -0.0700058572 |
| 4 | 48 | 0.0208333333 | 0 | -0.0499760959 | -0.0500460467 | -0.049906145 | -0.0560046858 |
| 4 | 48 | 0.0208333333 | 1 | -0.0620713164 | -0.0621581549 | -0.0619844779 | -0.0700058572 |

## Extrapolated paired intercepts

| H | coordinate | beta0 | beta1 | simultaneous_ci_low | simultaneous_ci_high | B20_ctrl_component | theory_covered_simultaneous |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | -0.0160363415 | 0.0134584535 | -0.0160963688 | -0.0159914783 | -0.0160013388 | True |
| 2 | 1 | -0.020036616 | 0.0180707617 | -0.0201109827 | -0.0199811131 | -0.0200016735 | True |
| 4 | 0 | -0.0543237668 | 0.113112361 | -0.054442768 | -0.0541825657 | -0.0560046858 | False |
| 4 | 1 | -0.0676943195 | 0.146866567 | -0.0678381597 | -0.0675216076 | -0.0700058572 | False |

## Prespecified falsification gates

| gate | scope | passed | detail |
| --- | --- | --- | --- |
| P3-F0 | p3-d2-matched-attribution-primary__H2__N12 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-primary__H2__N16 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-primary__H2__N24 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-primary__H2__N32 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-primary__H2__N48 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-primary__H4__N12 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-primary__H4__N16 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-primary__H4__N24 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-primary__H4__N32 | True | paired_validity |
| P3-F0 | p3-d2-matched-attribution-primary__H4__N48 | True | paired_validity |
| P3-F1 | H2_coordinate_0 | True | paired_bootstrap_coverage |
| P3-F1 | H2_coordinate_1 | True | paired_bootstrap_coverage |
| P3-F2 | H4_coordinate_0 | True | reporting_only_primary_path |
| P3-F2 | H4_coordinate_1 | True | reporting_only_primary_path |
| P3-F3 | H4 |  | deferred_to_frozen_small_step |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N12__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N12__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N16__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N16__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N24__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N24__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N32__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N32__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N48__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H2__N48__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N12__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N12__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N16__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N16__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N24__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N24__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N32__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N32__coordinate_1 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N48__coordinate_0 | True | signed_coordinate_direction |
| P3-F4 | p3-d2-matched-attribution-primary__H4__N48__coordinate_1 | True | signed_coordinate_direction |
| P3-F5 | paired_direct_sample |  | diagnostic_only |
| P3-F6 | frozen_matrix | True | all_settings_pairs_and_algorithm_members_present |
| P3-F7 | all_pairs | True | indexed_noise_blocks_identical |

## Interpretation boundary

The H=2 paired attribution simultaneous-coverage criterion passes for coordinates 0 and 1.
The H=4 primary path is reporting-only; its simultaneous coverage flags are False for coordinates 0 and 1. Final H=4 adjudication is delegated to the preregistered smaller-step experiment.
This does not prove the decomposition, establish an algorithm ranking, cover heterogeneous clients, state-dependent noise, growing H, or dimensions beyond the frozen d=2 setting.
