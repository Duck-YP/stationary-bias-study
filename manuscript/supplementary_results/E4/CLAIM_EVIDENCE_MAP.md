# Claim-Evidence Map

All E4_v1 claims use reused frozen production trajectories, not new training.
All statistical intervals are approximate finite-R seed inference, not theorem
proof, stationary-law certification, or uncertainty over the fixed test sample.

| Candidate claim | Evidence | Estimator / uncertainty | Scope / limitation |
|---|---|---|---|
| Actual deployable time-averaged models can be reconstructed |inputs/batches.npz; WINDOW_RESULTS.csv; models.npz; PHASE0_INPUT_AUDIT.md|Count-weighted true post-update global sums; independent replay|K=1 is a batch average, not a raw checkpoint; no balance-estimator substitution|
| Averaging reduces variance at the primary setting |BIAS_VARIANCE_MSE.csv; E4_bias_variance_vs_window.pdf|Between12independent-run V; paired196-coordinate primary max-bootstrap family; V_minus_K1 intervals|Measured finite-tail reduction; no1/K assumption or K_eff claim|
| Squared mean displacement becomes a large MSE fraction at K64 |BIAS_VARIANCE_MSE.csv; E4_bias_fraction_vs_window.pdf|Signed U, V, MSE; U/MSE simultaneous interval; unclipped negative estimates|68.13%/49.51% point shares;10% is a chosen benchmark; NOT certified stationary practical impact|
| SCAFFOLD descriptively crosses at32/64 |DECISIONS.json; BIAS_VARIANCE_MSE.csv|Point U>=V|Only64 uncertainty-positive; all temporal gates fail; NO_CERTIFIED_CROSSOVER|
| Stable stationary floor established |TEMPORAL_DIAGNOSTICS.csv; DIAGNOSTICS.md|Joint temporal confidence ball/projection equivalence margins|NOT SUPPORTED; failed equivalence is not proof of drift; no R0 burn-sensitivity certificate|
| SCAFFOLD-FedAvg mean differs |E4_matched_mean_difference.pdf; BIAS_VARIANCE_MSE.csv|Paired frozen objective-derived projection;12seed clusters|Not itself squared-bias difference, MSE difference or exact controlled coefficient|
| Averaged-model MSE differs |BIAS_VARIANCE_MSE.csv; PRACTICAL_IMPLICATIONS.csv|Paired DeltaMSE=DeltaU+DeltaV; corrected2C_U+U_delta identity|Setting-specific parameter metric; no inference from norm(Delta mean)^2 alone|
| Worse parameter error implies worse predictions |PRACTICAL_IMPLICATIONS.csv; practical/losses.npz|Test logloss at individual Y; paired simultaneous contrasts|NOT SUPPORTED: SCAFFOLD test loss improves slightly; fixed test set; tiny absolute effect|
| Averaging has no extra gradient/communication requirement |PRACTICAL_IMPLICATIONS.csv; practical/README.md|Existing horizon cost, zero added optimization samples/scalars for averaging, fixed-window accumulator|Loss evaluations cost forward passes; scalar communication is original source proxy, not full wire traffic|
| Homogeneous analytic control coefficient isolated in R0 |E4_v1_PROTOCOL_FROZEN.json; DIAGNOSTICS.md|No coefficient fitting or E1 bridge|NOT SUPPORTED; state-dependent noise; CONTROL_COEFFICIENT_NOT_ISOLATED_IN_REAL_DATA|
| New long-burn/tail study completed |v2/PILOT_RUN_MANIFEST.csv; E4_v2_PROTOCOL_FROZEN.json|Two complete fresh paired pilots,189440rounds each|Only R2 diagnostic pilots complete;48seed production NOT_STARTED, never pooled into v1|
| Historical theory checks are improved/replaced by E4 |inputs/full_results.csv; inputs/per_run_estimates.csv; historical manifests|Original records retained unchanged|NOT CLAIMED; H4 exclusions/H8 discrepancies/H1 arithmetic failures remain|

Primary and secondary families are not one joint confidence claim across all
experiments. Primary196, combined secondary392 and diagnostic1176 coordinates
are explicitly separate95% families. The shared bootstrap resamples paired seed
labels and carries all algorithms/windows/configs together. Jackknife
Bonferroni sensitivities and degeneracy flags are additional checks, not exact
small-sample coverage guarantees.
