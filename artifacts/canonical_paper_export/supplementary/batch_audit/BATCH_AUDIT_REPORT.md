# SCAFFOLD supplementary experiment batch audit and integration

Date: 2026-10-09. This report distinguishes supplied evidence, independently recomputed quantities, new post-hoc sensitivity, and manuscript edits.

## Decision

The supplied E1 and R0 data support the previously reported finite-grid and finite-tail results. No mismatch was found between the retained batch sufficient statistics and the primary run-level means/raw second moments. It is appropriate to integrate the restricted affine-control proposition, the E1 local-step study, and the R0 fixed-budget implication study while retaining the unresolved diagnostics. This is not a certification of a real-data invariant distribution or of every supplementary run.

## Inputs and scope

Five archives were extracted into one new directory: REVIEW_CORE.zip, SOURCE_REVIEW.zip, AUDIT_BATCHES_E1(1).zip, AUDIT_BATCHES_E3_R0.zip, and REVIEW_CORE_E3_DIAGNOSTICS_R0.zip. SHA-256 hashes and CRC results are in input_integrity.json. All match the archive hashes recorded in UPLOAD_ORDER.md (the renamed E1 archive has identical bytes).

The audit covers 34 E1 configurations / 408 paired runs and 9 R0 configurations / 108 paired runs: 516 paired runs, 1,032 algorithm trajectories, and 33,852 stored paired batches. There are twelve independent run seeds within each configuration; the same seed labels are coupled across configurations, so the 516 pairs are not asserted to be mutually independent. It does not cover R1/R2 batches, raw-example optimizer or held-out-loss recomputation, full per-client temporal controls, or production restarts. No new stochastic training, optimizer solve, tolerance adjustment, or primary-window replacement was performed.

## Independent reconstruction

The audit script imports NumPy/Pandas/SciPy but no original `study.*` analysis routines. It independently rebuilds:

1. Primary and raw run means from the first 64 batch sums divided by the actual counts; centered checkpoint second moments from separately retained batch squared-error sums. Every one of these run summaries is bit-identical to the saved NPZ/CSV values.
2. Batch start/end identities, frozen schedules, endpoint indexing, full-horizon accumulators, paired batch differences, control second moments, global temporal control means, and sample-gradient cost accounting.
3. Signed projection intervals, unclipped cross-run squared-bias U-statistics (implemented using the Gram matrix), jackknife variance intervals, MSE, and matched estimates.
4. All 118 E1 fitted-coefficient rows, including primary and named sensitivity windows, with per-seed OLS and the original seed-block bootstrap. All 14 H contrasts are preserved.
5. The 12 R0 allocation/policy contrasts from the originally specified 36-member family; no new family or preferred window was substituted.
6. Batch autocorrelation proxies, first/last-half projected differences, raw-versus-primary differences, and the available six extended-window comparisons.
7. R0 membership and complete stored gradient/Hessian/noise-covariance matrices, plus the recorded 60 long-H1 checks restricted to R0.

There are 26,970 scalar/array reproduction checks, all within their explicit tolerances. This count is not a count of independent scientific validations. Maximum difference among statistical outputs is 4.55e-13 (including design condition numbers); the largest difference overall is 4.66e-10 in large full-horizon SUMS accumulated in a different order, not in normalized primary means. Every primary mean/raw mean/second-moment reconstruction is exact. A further 516 Jensen consistency checks compare batch squared-error averages to the corresponding squared batch means; all are nonnegative within numerical tolerance.

## E1 interpretation

The source conclusions do not change. H=1 is a boundary-recursion check, not an extension of the H>=2 theorem. B11 is fitted independently rather than subtracted in advance. The H=8 primary leading intercepts remain displaced; both adjusted SCAFFOLD H8-minus-H2 coordinate contrasts exclude zero. The control-coefficient fits include H=2,4,8 and retain H=8's target exclusions.

The H4-minus-3.5-H2 control contrasts reconstructed from batches are approximately:

| Coordinate (1-indexed) | Estimate | Adjusted interval |
|---|---:|---:|
| 1 | 3.18e-5 | [-5.60e-5, 1.20e-4] |
| 2 | 4.27e-5 | [-6.66e-5, 1.52e-4] |

These are compatibility checks, not equivalence certification. Exact unrounded values are in reconstructed_H_contrasts.csv. New Cartesian-grid H4 results do not replace the historical gamma=1/N target exclusions.

Four nominal raw-versus-balance projected discrepancies are reproduced among the 68 E1 algorithm cells: H4/N64 at gamma=1/512 and 1/256, both algorithms. They are supplementary cell-level diagnostics, not the four historical chain-coordinate exceptions in the original manuscript. These nominal comparisons are not four independent algorithm failures; paired algorithms share the underlying draws. Their complete values are in cell_diagnostics.csv. No estimate was discarded.

## R0: fixed-budget allocation effect survives the batch audit

R0 replicates the same empirical objective across clients; it is a controlled real-data configuration, not disjoint private-client deployment. It retains all 124 parameters. Nm=256, H=4 and gamma_base=0.196078431372549 are fixed for allocation comparisons.

The N128-minus-N8 signed-projection contrasts are:

| Algorithm | Contrast | Original 36-family adjusted interval |
|---|---:|---:|
| SCAFFOLD | 0.00311367526694 | [0.00274928744214, 0.00347806309175] |
| FedAvg | 0.00207238639802 | [0.00171348518421, 0.00243128761183] |

These reproduce the preceding per-run review, now from the batch layer. Raw variance estimates remain near 0.00235--0.00236. Squared finite-tail mean displacement accounts for about 0.50% and 0.23% of parameter MSE at N128 for SCAFFOLD and FedAvg. This is a resolved signed mean-shift effect, not evidence of a large task-performance penalty.

Complete R0 diagnostic arrays show identical client membership, Hessians and single-example covariances. Recomputing Sigma_c sums / (N^2*m) reproduces the saved server-average reference covariance. The largest entrywise discrepancy from Sigma_ref/256 is 3.26e-19. This statement is about evaluation at the common reference point. Distinct later local trajectories need not have identical state-dependent noise covariances. Raw examples were not supplied, so the matrices themselves were not regenerated from examples.

## Important boundary newly confirmed: no extended R0 burn/tail data

All 108 R0 runs contain exactly 64 collected batches. No R0 run has 133 batches. The one extended E1 configuration is H4/N64/gamma=1/256, with 12 runs. Six E1 extended-window/algorithm comparisons are reproducible and their existing adjusted intervals include zero. Extended R2 reports exist in the core but their batches are outside this audit. They do not establish an R0 extension.

No first/last-half projected contrast among the 86 audited algorithm cells excludes zero under the original 138-member family adjustment. This is a consistency diagnostic, not proof of mixing. Median batch IACT proxies are about 1.0002 for E1 and 1.0027 for R0; maxima are 3.7914 and 2.5145. These truncated, positive-sequence proxies are neither exact effective sample sizes nor stationarity certificates. Independent run seeds, not individual batches, remain the inferential units.

A NEW POST-HOC audit subdivides the existing primary R0 tail without changing its production estimate:

| Window | SCAFFOLD N128-N8 | FedAvg N128-N8 |
|---|---:|---:|
| Primary 64 batches | 0.003114 | 0.002072 |
| First 32 | 0.003098 | 0.002053 |
| Last 32 | 0.003129 | 0.002092 |
| Last 16 | 0.003292 | 0.002255 |

The direction persists within these windows. Their descriptive intervals are saved separately; they are correlated post-hoc subdivisions, not independent replications or extended-burn runs. Manuscript R0 claims are therefore explicitly finite-tail implications, not certified stationary-law identification.

## Numerical arithmetic flags

The R0 subset of the original full-horizon H1 audit has 24 failures among 60 strict 1e-10 checks. All statuses and residuals are exactly reproduced from the retained batch means/snapshots. The maximum coordinate residual is 4.325947e-10. This must not be confused with the all-regime reported maximum vector discrepancy of about 7.54e-10 or the all-regime count of 48/132.

The reported stable endpoint-increment audits concern two H1 paths, not all production runs and not the H4 allocation experiment. They are left as source-reported post-hoc diagnostics, not newly rerun here. We have not changed the arithmetic, reprojected controls, relaxed a threshold or removed a flagged row. H4 allocation effects are far larger than the measured H1 discrepancies, but that scale comparison alone is not a full H4 roundoff validation.

## Scope of the manuscript integration

Base: SCAFFOLD_Coefficient_Comparison_Revised_20261009.zip, the last complete compiled project in the conversation.

- The two homogeneous theorem statements, their coefficients/remainders, and all shared proof lemmas remain unchanged. Appendix B is byte-identical.
- Introduction explains why common objectives isolate stochastic controls from deterministic drift correction.
- Main Results adds a restricted affine-shift proposition: f_c=f+a_c^T x with zero-sum fixed offsets; the invertible control translation proves equality of global stationary marginals. Appendix A appends only this short proof. No general heterogeneous FedAvg coefficient formula is asserted.
- Numerical study adds the independent H sweep and audited R0 allocation/policy evidence. Only the R0 panel of the supplied plot is cropped for the main text; the full original plot and all R1/R2 tabular records are retained.
- Appendix C keeps the entire existing historical section and appends supplementary design, result and diagnostic summaries. Primary/nested H8 results, historical H4 exclusions, near-zero/precision flags and long-H1 arithmetic discrepancies stay visible.
- R1/R2 table rows and task losses are source-derived contextual results; this audit does not claim new independent batch verification for them.
- Discussion preserves the parameter bias/variance/MSE/predictive-loss distinctions. Conclusion narrows future heterogeneity work to unequal curvature and other unproved settings.
- A repository remote DOES exist in SOURCE_REVIEW/VERSION.json. It identifies a historical commit with the supplementary study directory untracked. Thus it is recorded as provenance, not advertised as a verified public release of these supplementary runs.

## Limits of inference and reproducibility

Passing reconstruction checks establishes agreement among stored sufficient statistics, exports and reported analyses. It cannot validate unsaved per-round trajectories, prove asymptotic coefficients, certify finite-burn error, or certify 95% frequentist coverage of nominal t/jackknife intervals. Raw-example optimizer/loss recomputation, full R1/R2 batch diagnostics and a full-grid stable-kernel run were not performed. No evidence is silently replaced with general knowledge.

## Reproduction of this audit

Extract the five supplied archives into one directory, preserving their root folders, then run:

```sh
python audit_batches.py --bundle PATH_TO_EXTRACTED_EXPORTS --output NEW_AUDIT_OUTPUT
python r0_sensitivity.py --bundle PATH_TO_EXTRACTED_EXPORTS --output NEW_AUDIT_OUTPUT
```

The second command is explicitly post-hoc analysis of existing tails. Both commands are analysis-only. Dependencies: NumPy, Pandas, SciPy. The original inputs remain unmodified.
