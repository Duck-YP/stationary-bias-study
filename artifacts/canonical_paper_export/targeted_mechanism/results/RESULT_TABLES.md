# Complete primary coefficient summaries

All intervals below are the approximate 95% simultaneous sampling intervals for the frozen family of 36 scalar summaries. Marginal Student-t/bootstrap intervals and Bonferroni-t sensitivity are retained in CSV. Sampling intervals omit burn-in and deterministic grid remainder.

| Comparison | Observable | Coordinate | Estimate | Interval | Target | Practical resolution / control |
|---|---|---:|---:|---|---:|---|
| rho_minus_symmetric | SCAFFOLD | 1 | 0.056090783 | [0.042457262, 0.069724304] | 0.059375 | nonzero_control |
| rho_minus_symmetric | SCAFFOLD | 2 | 0.0026155994 | [-0.0045558919, 0.0097870907] | -0 | inside_resolution_band |
| rho_minus_symmetric | FedAvg | 1 | 0.034212198 | [0.02057566, 0.047848737] | 0.0375 | nonzero_control |
| rho_minus_symmetric | FedAvg | 2 | 0.0026117661 | [-0.0045608879, 0.00978442] | -0 | intersects_resolution_band_edge |
| rho_minus_symmetric | difference | 1 | 0.021878585 | [0.021841282, 0.021915887] | 0.021875 | nonzero_control |
| rho_minus_symmetric | difference | 2 | 3.8333071e-06 | [-1.745297e-05, 2.5119584e-05] | -0 | inside_resolution_band |
| rho_zero_symmetric | SCAFFOLD | 1 | 0.004686064 | [-0.018094172, 0.0274663] | -0 | too_wide_for_resolution |
| rho_zero_symmetric | SCAFFOLD | 2 | 0.0024973403 | [-0.0060117363, 0.011006417] | -0 | inside_resolution_band |
| rho_zero_symmetric | FedAvg | 1 | 0.0047066224 | [-0.018068941, 0.027482186] | -0 | too_wide_for_resolution |
| rho_zero_symmetric | FedAvg | 2 | 0.0025118084 | [-0.0059993716, 0.011022988] | -0 | too_wide_for_resolution |
| rho_zero_symmetric | difference | 1 | -2.0558374e-05 | [-6.1503642e-05, 2.0386894e-05] | -0 | inside_resolution_band |
| rho_zero_symmetric | difference | 2 | -1.4468081e-05 | [-3.4876858e-05, 5.9406965e-06] | -0 | inside_resolution_band |
| rho_plus_symmetric | SCAFFOLD | 1 | -0.046832481 | [-0.067920663, -0.025744299] | -0.059375 | nonzero_control |
| rho_plus_symmetric | SCAFFOLD | 2 | 0.0022184516 | [-0.0040669017, 0.0085038049] | -0 | inside_resolution_band |
| rho_plus_symmetric | FedAvg | 1 | -0.024981333 | [-0.046071376, -0.0038912886] | -0.0375 | nonzero_control |
| rho_plus_symmetric | FedAvg | 2 | 0.0022413798 | [-0.004046294, 0.0085290535] | -0 | intersects_resolution_band_edge |
| rho_plus_symmetric | difference | 1 | -0.021851148 | [-0.021895362, -0.021806934] | -0.021875 | nonzero_control |
| rho_plus_symmetric | difference | 2 | -2.2928209e-05 | [-4.2340901e-05, -3.5155169e-06] | -0 | inside_resolution_band |
| rho_plus_asymmetric | SCAFFOLD | 1 | -0.058146108 | [-0.081415334, -0.034876882] | -0.059375 | nonzero_control |
| rho_plus_asymmetric | SCAFFOLD | 2 | 0.002715557 | [-0.0041148861, 0.0095460001] | -0 | inside_resolution_band |
| rho_plus_asymmetric | FedAvg | 1 | -0.036264317 | [-0.059530061, -0.012998572] | -0.0375 | nonzero_control |
| rho_plus_asymmetric | FedAvg | 2 | 0.0027160393 | [-0.0041136678, 0.0095457464] | -0 | intersects_resolution_band_edge |
| rho_plus_asymmetric | difference | 1 | -0.021881791 | [-0.021931528, -0.021832054] | -0.021875 | nonzero_control |
| rho_plus_asymmetric | difference | 2 | -4.822784e-07 | [-2.1324071e-05, 2.0359514e-05] | -0 | inside_resolution_band |
| rho_plus_symmetric minus rho_plus_asymmetric | SCAFFOLD | 1 | 0.011313627 | [-0.020135156, 0.04276241] | 0 | too_wide_for_resolution |
| rho_plus_symmetric minus rho_plus_asymmetric | SCAFFOLD | 2 | -0.00049710545 | [-0.0098863299, 0.008892119] | 0 | inside_resolution_band |
| rho_plus_symmetric minus rho_plus_asymmetric | FedAvg | 1 | 0.011282984 | [-0.02016274, 0.042728709] | 0 | too_wide_for_resolution |
| rho_plus_symmetric minus rho_plus_asymmetric | FedAvg | 2 | -0.00047465952 | [-0.0098649071, 0.0089155881] | 0 | too_wide_for_resolution |
| rho_plus_symmetric minus rho_plus_asymmetric | difference | 1 | 3.0643035e-05 | [-3.5637054e-05, 9.6923123e-05] | 0 | inside_resolution_band |
| rho_plus_symmetric minus rho_plus_asymmetric | difference | 2 | -2.244593e-05 | [-5.1052338e-05, 6.160477e-06] | 0 | inside_resolution_band |
| rho_plus_symmetric minus rho_minus_symmetric | SCAFFOLD | 1 | -0.10292326 | [-0.12796662, -0.077879904] | -0.11875 | nonzero_control |
| rho_plus_symmetric minus rho_minus_symmetric | SCAFFOLD | 2 | -0.00039714785 | [-0.009831496, 0.0090372003] | 0 | inside_resolution_band |
| rho_plus_symmetric minus rho_minus_symmetric | FedAvg | 1 | -0.059193531 | [-0.084241953, -0.034145109] | -0.075 | nonzero_control |
| rho_plus_symmetric minus rho_minus_symmetric | FedAvg | 2 | -0.00037038633 | [-0.0098072861, 0.0090665135] | 0 | too_wide_for_resolution |
| rho_plus_symmetric minus rho_minus_symmetric | difference | 1 | -0.043729733 | [-0.043787781, -0.043671684] | -0.04375 | nonzero_control |
| rho_plus_symmetric minus rho_minus_symmetric | difference | 2 | -2.6761516e-05 | [-5.5405252e-05, 1.8822202e-06] | 0 | inside_resolution_band |

## Prespecified restricted-grid sensitivity

The omitted-step sensitivity is displayed alongside the primary; it never replaces it.

| Comparison | Observable | Coordinate | Full intercept | Omit-largest-step intercept | Change |
|---|---|---:|---:|---:|---:|
| rho_minus_symmetric | SCAFFOLD | 1 | 0.056090783 | 0.051648862 | -0.0044419 |
| rho_minus_symmetric | SCAFFOLD | 2 | 0.0026155994 | 0.0042681392 | 0.0016525 |
| rho_minus_symmetric | FedAvg | 1 | 0.034212198 | 0.029784034 | -0.0044282 |
| rho_minus_symmetric | FedAvg | 2 | 0.0026117661 | 0.0042839494 | 0.0016722 |
| rho_minus_symmetric | difference | 1 | 0.021878585 | 0.021864828 | -1.3757e-05 |
| rho_minus_symmetric | difference | 2 | 3.8333071e-06 | -1.5810187e-05 | -1.9643e-05 |
| rho_zero_symmetric | SCAFFOLD | 1 | 0.004686064 | 0.0072675893 | 0.0025815 |
| rho_zero_symmetric | SCAFFOLD | 2 | 0.0024973403 | 0.0057955994 | 0.0032983 |
| rho_zero_symmetric | FedAvg | 1 | 0.0047066224 | 0.0072975735 | 0.002591 |
| rho_zero_symmetric | FedAvg | 2 | 0.0025118084 | 0.0057993352 | 0.0032875 |
| rho_zero_symmetric | difference | 1 | -2.0558374e-05 | -2.9984163e-05 | -9.4258e-06 |
| rho_zero_symmetric | difference | 2 | -1.4468081e-05 | -3.7358568e-06 | 1.0732e-05 |
| rho_plus_symmetric | SCAFFOLD | 1 | -0.046832481 | -0.016751714 | 0.030081 |
| rho_plus_symmetric | SCAFFOLD | 2 | 0.0022184516 | 0.0035456104 | 0.0013272 |
| rho_plus_symmetric | FedAvg | 1 | -0.024981333 | 0.0051013679 | 0.030083 |
| rho_plus_symmetric | FedAvg | 2 | 0.0022413798 | 0.0035593296 | 0.0013179 |
| rho_plus_symmetric | difference | 1 | -0.021851148 | -0.021853082 | -1.9342e-06 |
| rho_plus_symmetric | difference | 2 | -2.2928209e-05 | -1.371928e-05 | 9.2089e-06 |
| rho_plus_asymmetric | SCAFFOLD | 1 | -0.058146108 | -0.05941051 | -0.0012644 |
| rho_plus_asymmetric | SCAFFOLD | 2 | 0.002715557 | 0.0013937012 | -0.0013219 |
| rho_plus_asymmetric | FedAvg | 1 | -0.036264317 | -0.03757242 | -0.0013081 |
| rho_plus_asymmetric | FedAvg | 2 | 0.0027160393 | 0.001385747 | -0.0013303 |
| rho_plus_asymmetric | difference | 1 | -0.021881791 | -0.02183809 | 4.3701e-05 |
| rho_plus_asymmetric | difference | 2 | -4.822784e-07 | 7.9542201e-06 | 8.4365e-06 |
| rho_plus_symmetric minus rho_plus_asymmetric | SCAFFOLD | 1 | 0.011313627 | 0.042658796 | 0.031345 |
| rho_plus_symmetric minus rho_plus_asymmetric | SCAFFOLD | 2 | -0.00049710545 | 0.0021519092 | 0.002649 |
| rho_plus_symmetric minus rho_plus_asymmetric | FedAvg | 1 | 0.011282984 | 0.042673788 | 0.031391 |
| rho_plus_symmetric minus rho_plus_asymmetric | FedAvg | 2 | -0.00047465952 | 0.0021735827 | 0.0026482 |
| rho_plus_symmetric minus rho_plus_asymmetric | difference | 1 | 3.0643035e-05 | -1.499249e-05 | -4.5636e-05 |
| rho_plus_symmetric minus rho_plus_asymmetric | difference | 2 | -2.244593e-05 | -2.16735e-05 | 7.7243e-07 |
| rho_plus_symmetric minus rho_minus_symmetric | SCAFFOLD | 1 | -0.10292326 | -0.068400577 | 0.034523 |
| rho_plus_symmetric minus rho_minus_symmetric | SCAFFOLD | 2 | -0.00039714785 | -0.00072252883 | -0.00032538 |
| rho_plus_symmetric minus rho_minus_symmetric | FedAvg | 1 | -0.059193531 | -0.024682667 | 0.034511 |
| rho_plus_symmetric minus rho_minus_symmetric | FedAvg | 2 | -0.00037038633 | -0.00072461974 | -0.00035423 |
| rho_plus_symmetric minus rho_minus_symmetric | difference | 1 | -0.043729733 | -0.04371791 | 1.1822e-05 |
| rho_plus_symmetric minus rho_minus_symmetric | difference | 2 | -2.6761516e-05 | 2.0909071e-06 | 2.8852e-05 |
