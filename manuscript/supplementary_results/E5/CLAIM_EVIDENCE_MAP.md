# Claim-evidence map

| Claim | Evidence | Allowed interpretation | Not established |
|---|---|---|---|
| Independent plug-in reconstruction is correct | NUMERICAL_CROSSCHECKS.csv; independent_formula/; source hashes | Saved empirical logistic reference, all124 coordinates, centered Sigma, exact frozen gamma | Validity of additive-noise theorem for state-dependent R0 |
| Actual averaged checkpoints are reused | inputs/batches.npz; inputs/models.npz; exact replay check; PAIRED_SEED_RESULTS.csv | Nine cells x12paired seeds x7windows; no training | 64 independent observations per seed |
| Reference direction tracks paired mean shifts | ALL_CELLS_ALL_WINDOWS.csv; FULL_VECTOR_ALIGNMENT.csv; VECTORS.npz | Strong K64 full-vector alignment, weaker short windows | Unique control-mechanism identification |
| Proxy has nontrivial magnitude but systematic overprediction | All six non-H1 K64 projection/norm ratios and residual decomposition | Parameter-free descriptive approximation with explicit error | Exact coefficient fit, unbiased proxy, explained fraction of total MSE |
| H scaling is a substantive limitation | SCALING_COMPARISONS.csv; all interval sensitivities | 2.927 vs3.5 at frozen grid; H1 absolute controls preserved | Verified control prefactor on real data or falsified theorem |
| Smaller gamma improves observed/proxy ratio here | All three gamma comparisons at every K | Descriptive finite-grid secants | General gamma^2 asymptotic rate |
| Allocation varies covariance as well as N | R0_CONFIGS.json; sampling audit; allocation rows | N*m=256 implies C_ref=Sigma_ref/m | Fixed-C cross-N theorem test |
| Comparators are legitimate but nonexhaustive | NEGATIVE_CONTROLS.csv; specification; code | Frozen x_ref and -T directions, zero amplitude, no fit | Model-selection victory or exclusion of generic nonlinear effects |
| Conditional Monte Carlo precision | PAIRED_BOOTSTRAP_SENSITIVITY.csv; INFERENCE_ARRAYS.npz; statistical receipt | Paired12seed max-deviation/jackknife and full-vector sensitivity | Proxy-remainder, dataset or stationary-law coverage |
| Window behavior does not certify stationarity | EARLY_LATE_PAIRED_DIAGNOSTICS.csv; prior_e4/TEMPORAL_DIAGNOSTICS.csv | All K retained; original0/144gates unchanged | Certified stationary bias or crossover |
| Parameter-space effect need not imply prediction harm | prior_e4/BIAS_VARIANCE_MSE.csv; PRACTICAL_IMPLICATIONS.csv | E4 primary bias shares68.1/49.5%; tiny train gap; lower SCAFFOLD test loss | Universal ranking, harm, optimal H/gamma |
| Unfavorable historical outcomes remain available | prior_e4/historical/; inputs/full_results.csv; per_run_estimates.csv | H4/H8 exclusions and H1 numerical issues retained | New target inclusion or analysis-rule revision |
| Stop at descriptive bridge | SCIENTIFIC_SUMMARY.md; REVIEWER_RISK_DECISION.md; reviewer_audit/ | Appendix-first; optional restrained pointer | Guaranteed publication gain or automatic future runs |
