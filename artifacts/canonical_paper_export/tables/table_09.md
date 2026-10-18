# Table 9: Sampling-uncertainty procedures

Status: **supported**. Section C.1.2, page 30.

tab:num-inference; normalized source-backed protocol inventory, not verbatim manuscript layout. All listed manuscript settings are represented by saved fields or explicit counts.

| study / component | saved field / derivation | value |
| --- | --- | --- |
| Joint grid and fixed step, d=2 | per_setting_uncertainty | {"source": "eight_independent_chain_estimates", "method": "student_t_coordinatewise", "degrees_of_freedom": 7, "familywise_confidence_level": 0.95, "correction": "bonferroni", "coordinates": 2, "simultaneous_coordinate_confidence_level": 0.975, "marginal_diagnostic_confidence_level": 0.95, "pool_coordinates": false} |
| Joint grid and fixed step, d=2 | bootstrap | {"unit": "seed_label_block", "repetitions": 2000, "seed": 2901, "preserve_same_seed_across_settings": true, "simultaneous_familywise_confidence_level": 0.95, "correction": "bonferroni", "simultaneous_coordinate_percentile_level": 0.975, "simultaneous_quantiles": [0.0125, 0.9875], "marginal_diagnostic_percentile_level": 0.95, "marginal_diagnostic_quantiles": [0.025, 0.975]} |
| Five-dimensional | per_setting_uncertainty | {"source": "eight_independent_chain_estimates", "method": "student_t_coordinatewise", "degrees_of_freedom": 7, "familywise_confidence_level": 0.95, "correction": "bonferroni", "coordinates": 5, "simultaneous_coordinate_confidence_level": 0.99, "simultaneous_t_critical": 3.4994832973504924, "marginal_diagnostic_confidence_level": 0.95, "pool_coordinates": false} |
| Five-dimensional | bootstrap | {"unit": "seed_label_block", "repetitions": 5000, "seed": 3901, "preserve_same_seed_across_settings": true, "simultaneous_familywise_confidence_level": 0.95, "correction": "bonferroni", "simultaneous_coordinate_percentile_level": 0.99, "simultaneous_quantiles": [0.005, 0.995], "marginal_diagnostic_percentile_level": 0.95, "marginal_diagnostic_quantiles": [0.025, 0.975]} |
| Cartesian/local step | resampling | independent paired seed vectors as bootstrap units; all cells resampled together; 2000 bootstrap draws seed=61009 |
| Cartesian/local step | ci | pointwise nominal Student-t 95%; coordinate families Bonferroni; bootstrap fits; no deterministic error coverage |
| Cartesian/local step | multiplicity | {"E1a_intercepts_coordinates": 16, "E1b_intercepts_coordinates": 6, "E3_signed_projections": 105} |
| Cartesian/local step | E1a_primary_fit | separate algorithm/H linear intercept against gamma; all four points; no B11 subtraction |
| Cartesian/local step | E1b_primary_fit | separate H coordinate OLS [1,gamma,1/N], all Cartesian points |
| Cartesian/local step | E1b_contrast | beta0(H4)-3.5*beta0(H2); exact kappa(4)/kappa(2)=3.5 |
| Cartesian/local step | Student-t degrees of freedom from independent run count | 11 |
| Cartesian/local step | saved contrast scalar counts by kind | {"E1a_H_intercept_difference": 12, "E1b_H4_minus_3point5_H2": 2} |
| Contraction/noise law | bootstrap_draws | 4000 |
| Contraction/noise law | resampling | Resample each independent cell run vector jointly across algorithms/coordinates/raw/balance/windows; independently across cells. Fixed bootstrap seed 2026101401, 4000 draws. |
| Contraction/noise law | intervals | Marginal Student t (df=11 conservative) and bootstrap percentile; approximate simultaneous centered bootstrap max-\|standardized error\| family of 36; Bonferroni t df11 sensitivity. |
| Contraction/noise law | primary_family | 24 condition x observable x coordinate intercepts + 6 symmetric-minus-asymmetric law contrasts + 6 rho-plus-minus-rho-minus contrasts = 36 scalars |
| Real-data allocation | ci | pointwise nominal Student-t 95%; coordinate families Bonferroni; bootstrap fits; no deterministic error coverage |
| Real-data allocation | U_statistic | unclipped cross-run squared displacement, jackknife-t CI; near-zero inference unresolved; Gaussian quadratic zero-bias calibration |
| Real-data allocation | E3_primary_estimator | direct mean; no pilot-validated shadow process |
| Real-data allocation | cellwise projection family | 105 |
| Real-data allocation | saved allocation/configuration contrast count | 36 |
| Model averaging | draws | 19999 |
| Model averaging | families | {"primary": {"coordinates": 196, "bootstrap_max_critical": 3.3208875490656267, "jackknife_Bonferroni_t": 5.293090119215704}, "secondary": {"coordinates": 392, "bootstrap_max_critical": 3.6238890929436316, "jackknife_Bonferroni_t": 5.754356046266111}, "diagnostic": {"coordinates": 1176, "bootstrap_max_critical": 3.9982655949320476, "jackknife_Bonferroni_t": 6.52967570634147}} |
| Model averaging | bootstrap_bias_center_corrected | true |
| Model averaging | bootstrap | {"draws": 19999, "seed": 202610094, "coverage": 0.95, "unit": "paired independent seed label; one multinomial count vector across all cells/algorithms/K", "method": "standardized max absolute empirical-population-centered bootstrap deviation", "centering": "U0=\|\|b_hat\|\|^2; V0=(R-1)/R V_hat; MSE0=MSE_hat; all derived functionals use these centers", "scalar_family_per_cell": ["both algorithms all K: U,V,MSE,U_minus_V,U_minus_0.1MSE,projection,train_gap,test_loss,share,V_minus_K1", "all K: delta_U,delta_V,delta_MSE,delta_projection,delta_train,delta_test,U_delta,C_cross"], "limits": "Approximate finite-R bootstrap, not exact coverage or a stationary-law certificate"} |
| Model averaging | sensitivity | {"method": "delete-one seed jackknife-t; Bonferroni within same scalar family", "decision": "positive crossover/materiality needs both max-bootstrap and nondegenerate jackknife sensitivity lower bounds >0", "degeneracy": "jackknife SE <1e-3 bootstrap SD is weak precision, never strong evidence"} |
| Directional comparison | draws | 19999 |
| Directional comparison | scalar_family_size | 1068 |
| Directional comparison | vector_family_size | 117 |
| Directional comparison | scalar_and_vector_families_separately_95_percent_not_joint | true |
| Directional comparison | bootstrap | {"draws": 19999, "seed": 202610096, "cluster": "paired_seed_shared_across_all_cells_and_K"} |
| Directional comparison | intervals | functional-centered bootstrap max-standardized deviations; delete-one paired jackknife Bonferroni t sensitivity; full-vector balls and denominator-safe scaling transformations |
| Directional comparison | alpha | 0.05 |

Sources:

- `configs/original/p2_multidimensional_validation/configs/d2_coefficient_primary.yaml`
- `configs/original/p2_multidimensional_validation/configs/d5_controlled_validation.yaml`
- `configs/supplementary/PROTOCOL_FROZEN.json`
- `manuscript/supplementary_results/tables/E1_intercept_contrasts.csv`
- `artifacts/canonical_paper_export/targeted_mechanism/PROTOCOL_FROZEN.json`
- `manuscript/supplementary_results/tables/E3_policy_allocation_contrasts.csv`
- `manuscript/supplementary_results/E4/STATISTICAL_METHOD_RECEIPT.json`
- `manuscript/supplementary_results/E4/E4_v1_PROTOCOL_FROZEN.json`
- `manuscript/supplementary_results/E5/STATISTICAL_METHOD_RECEIPT.json`
- `manuscript/supplementary_results/E5/E5_POSTHOC_ANALYSIS_SPEC.json`
