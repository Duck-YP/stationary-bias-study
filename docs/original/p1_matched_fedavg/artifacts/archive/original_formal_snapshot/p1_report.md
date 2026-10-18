# P1-F7 Matched FedAvg vs SCAFFOLD

Run phase: **FORMAL**

Theory targets are evaluated without altering the simulated trajectories.

## Individual algorithm coefficients

| grid_name | algorithm | H | N | gamma | C_mean | C_ci_low | C_ci_high | B20_target | error_to_target | gate_pass | falsification_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | scaffold | 2 | 12 | 0.0833333333 | -0.177441831 | -0.181624611 | -0.173259052 | -0.1875 | 0.0100581686 | True | INCONSISTENT |
| primary | fedavg | 2 | 12 | 0.0833333333 | -0.122985221 | -0.127163171 | -0.118807271 | -0.125 | 0.00201477944 | True | CONSISTENT |
| primary | scaffold | 2 | 16 | 0.0625 | -0.180129091 | -0.183997384 | -0.176260799 | -0.1875 | 0.0073709087 | True | INCONSISTENT |
| primary | fedavg | 2 | 16 | 0.0625 | -0.123561839 | -0.127431364 | -0.119692314 | -0.125 | 0.00143816117 | True | CONSISTENT |
| primary | scaffold | 2 | 24 | 0.0416666667 | -0.181854168 | -0.184051206 | -0.179657129 | -0.1875 | 0.00564583216 | True | INCONSISTENT |
| primary | fedavg | 2 | 24 | 0.0416666667 | -0.123363398 | -0.125490553 | -0.121236242 | -0.125 | 0.00163660245 | True | CONSISTENT |
| primary | scaffold | 2 | 32 | 0.03125 | -0.184523665 | -0.187522014 | -0.181525316 | -0.1875 | 0.00297633487 | True | CONSISTENT |
| primary | fedavg | 2 | 32 | 0.03125 | -0.125040161 | -0.1280992 | -0.121981121 | -0.125 | -4.01606299e-05 | True | CONSISTENT |
| primary | scaffold | 2 | 48 | 0.0208333333 | -0.185740455 | -0.188277377 | -0.183203533 | -0.1875 | 0.00175954492 | True | CONSISTENT |
| primary | fedavg | 2 | 48 | 0.0208333333 | -0.125241374 | -0.127778676 | -0.122704073 | -0.125 | -0.000241374486 | True | CONSISTENT |
| primary | scaffold | 4 | 12 | 0.0833333333 | -0.480991374 | -0.485218924 | -0.476763824 | -0.59375 | 0.112758626 | True | INCONSISTENT |
| primary | fedavg | 4 | 12 | 0.0833333333 | -0.331497286 | -0.335599936 | -0.327394635 | -0.375 | 0.0435027142 | True | INCONSISTENT |
| primary | scaffold | 4 | 16 | 0.0625 | -0.50696678 | -0.510990762 | -0.502942799 | -0.59375 | 0.0867832196 | True | INCONSISTENT |
| primary | fedavg | 4 | 16 | 0.0625 | -0.342421284 | -0.34638048 | -0.338462088 | -0.375 | 0.0325787159 | True | INCONSISTENT |
| primary | scaffold | 4 | 24 | 0.0416666667 | -0.533443585 | -0.536152563 | -0.530734607 | -0.59375 | 0.0603064148 | True | INCONSISTENT |
| primary | fedavg | 4 | 24 | 0.0416666667 | -0.352236651 | -0.354507257 | -0.349966045 | -0.375 | 0.0227633488 | True | INCONSISTENT |
| primary | scaffold | 4 | 32 | 0.03125 | -0.549285537 | -0.552650423 | -0.545920652 | -0.59375 | 0.0444644625 | True | INCONSISTENT |
| primary | fedavg | 4 | 32 | 0.03125 | -0.359541074 | -0.36281436 | -0.356267788 | -0.375 | 0.0154589261 | True | INCONSISTENT |
| primary | scaffold | 4 | 48 | 0.0208333333 | -0.563924827 | -0.566590976 | -0.561258678 | -0.59375 | 0.0298251731 | True | INCONSISTENT |
| primary | fedavg | 4 | 48 | 0.0208333333 | -0.364843862 | -0.367466706 | -0.362221018 | -0.375 | 0.010156138 | True | INCONSISTENT |
| small_step_h4 | scaffold | 4 | 64 | 0.015625 | -0.570344729 | -0.571816076 | -0.568873381 | -0.59375 | 0.0234052715 | True | INCONSISTENT |
| small_step_h4 | fedavg | 4 | 64 | 0.015625 | -0.366541187 | -0.367883561 | -0.365198813 | -0.375 | 0.00845881269 | True | INCONSISTENT |
| small_step_h4 | scaffold | 4 | 96 | 0.0104166667 | -0.578315178 | -0.580770057 | -0.5758603 | -0.59375 | 0.0154348216 | True | INCONSISTENT |
| small_step_h4 | fedavg | 4 | 96 | 0.0104166667 | -0.369544202 | -0.372015269 | -0.367073135 | -0.375 | 0.00545579769 | True | INCONSISTENT |
| small_step_h4 | scaffold | 4 | 128 | 0.0078125 | -0.582708479 | -0.585027605 | -0.580389353 | -0.59375 | 0.0110415208 | True | INCONSISTENT |
| small_step_h4 | fedavg | 4 | 128 | 0.0078125 | -0.371505312 | -0.37381233 | -0.369198294 | -0.375 | 0.00349468818 | True | INCONSISTENT |
| small_step_h4 | scaffold | 4 | 192 | 0.00520833333 | -0.586291504 | -0.58839876 | -0.584184248 | -0.59375 | 0.00745849583 | True | INCONSISTENT |
| small_step_h4 | fedavg | 4 | 192 | 0.00520833333 | -0.372597234 | -0.374702809 | -0.370491659 | -0.375 | 0.00240276638 | True | INCONSISTENT |

## Paired SCAFFOLD-minus-FedAvg differences

| grid_name | H | N | gamma | Delta_C_mean | Delta_C_ci_low | Delta_C_ci_high | Delta_B20_target | error_delta | pair_gate_pass | falsification_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 2 | 12 | 0.0833333333 | -0.0544566108 | -0.0546058475 | -0.0543073742 | -0.0625 | 0.00804338916 | True | INCONSISTENT |
| primary | 2 | 16 | 0.0625 | -0.0565672525 | -0.0567647204 | -0.0563697845 | -0.0625 | 0.00593274753 | True | INCONSISTENT |
| primary | 2 | 24 | 0.0416666667 | -0.0584907703 | -0.0585819579 | -0.0583995827 | -0.0625 | 0.00400922971 | True | INCONSISTENT |
| primary | 2 | 32 | 0.03125 | -0.0594835045 | -0.0595606543 | -0.0594063547 | -0.0625 | 0.0030164955 | True | INCONSISTENT |
| primary | 2 | 48 | 0.0208333333 | -0.0604990806 | -0.0605484366 | -0.0604497246 | -0.0625 | 0.0020009194 | True | INCONSISTENT |
| primary | 4 | 12 | 0.0833333333 | -0.149494088 | -0.150822496 | -0.14816568 | -0.21875 | 0.069255912 | True | INCONSISTENT |
| primary | 4 | 16 | 0.0625 | -0.164545496 | -0.16550492 | -0.163586072 | -0.21875 | 0.0542045037 | True | INCONSISTENT |
| primary | 4 | 24 | 0.0416666667 | -0.181206934 | -0.181767902 | -0.180645966 | -0.21875 | 0.037543066 | True | INCONSISTENT |
| primary | 4 | 32 | 0.03125 | -0.189744464 | -0.190105738 | -0.189383189 | -0.21875 | 0.0290055365 | True | INCONSISTENT |
| primary | 4 | 48 | 0.0208333333 | -0.199080965 | -0.199394476 | -0.198767454 | -0.21875 | 0.0196690351 | True | INCONSISTENT |
| small_step_h4 | 4 | 64 | 0.015625 | -0.203803541 | -0.20401611 | -0.203590972 | -0.21875 | 0.0149464588 | True | INCONSISTENT |
| small_step_h4 | 4 | 96 | 0.0104166667 | -0.208770976 | -0.208868452 | -0.2086735 | -0.21875 | 0.0099790239 | True | INCONSISTENT |
| small_step_h4 | 4 | 128 | 0.0078125 | -0.211203167 | -0.211318315 | -0.21108802 | -0.21875 | 0.00754683261 | True | INCONSISTENT |
| small_step_h4 | 4 | 192 | 0.00520833333 | -0.213694271 | -0.213750219 | -0.213638322 | -0.21875 | 0.00505572944 | True | INCONSISTENT |

## Matched-pair bootstrap fits

| grid_name | H | bootstrap_unit | bootstrap_repetitions | bootstrap_seed_fedavg | bootstrap_seed_delta | fedavg_intercept | fedavg_intercept_ci_low | fedavg_intercept_ci_high | fedavg_slope | delta_intercept | delta_intercept_ci_low | delta_intercept_ci_high | delta_slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 2 | matched_chain_pair | 2000 | 20260831 | 20260832 | -0.125738325 | -0.128661936 | -0.122372574 | 0.0354767376 | -0.0625032206 | -0.0625704869 | -0.0624341085 | 0.0960788218 |
| primary | 4 | matched_chain_pair | 2000 | 20260831 | 20260832 | -0.375630335 | -0.378775536 | -0.372060554 | 0.532639369 | -0.214741036 | -0.215298132 | -0.214251831 | 0.791512621 |
| small_step_h4 | 4 | matched_chain_pair | 2000 | 20260831 | 20260832 | -0.375862878 | -0.377304967 | -0.374452501 | 0.595547604 | -0.218632262 | -0.218739605 | -0.21854628 | 0.948661566 |

## O(gamma) remainder diagnostics

| quantity | grid_name | H | num_settings | smaller_step_error_decreases | possible_decreases | scaled_error_min | scaled_error_max | assessment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fedavg | primary | 2 | 5 | 2 | 4 | -0.0115859753 | 0.0392784588 | DESCRIPTIVE_ONLY |
| fedavg | primary | 4 | 5 | 4 | 4 | 0.487494624 | 0.546320371 | DESCRIPTIVE_ONLY |
| fedavg | small_step_h4 | 4 | 4 | 3 | 3 | 0.447320087 | 0.541364012 | DESCRIPTIVE_ONLY |
| delta | primary | 2 | 5 | 4 | 4 | 0.0949239605 | 0.0965278559 | DESCRIPTIVE_ONLY |
| delta | primary | 4 | 5 | 4 | 4 | 0.831070944 | 0.944113685 | DESCRIPTIVE_ONLY |
| delta | small_step_h4 | 4 | 4 | 3 | 3 | 0.956573362 | 0.970700053 | DESCRIPTIVE_ONLY |
