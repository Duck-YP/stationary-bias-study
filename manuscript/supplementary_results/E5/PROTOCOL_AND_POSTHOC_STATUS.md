# Protocol and post-hoc status

E5 is an analysis-only, post-hoc exploratory audit requested after the completed E4 study. The supplied exploratory table was read before this audit. Nothing here is preregistered or confirmatory. `E5_POSTHOC_ANALYSIS_SPEC.json` records the analysis specification written before executing the new primary analysis; its SHA-256 appears in the statistical receipt. This does not erase prior knowledge of the data. No success threshold, scale correction, outcome-dependent sign, or fitted coefficient was introduced.

## Units, family and intervals

The sampling units are 12 paired production seeds 20001 through 20012. Each is a block carrying all nine configurations, all seven K values, both algorithms and all 124 coordinates. Identical multinomial seed weights (19,999 draws, seed 202610096) are used throughout. Chronological batches and coordinates are not independent replicates. Across-cell shared seed labels define reproducible blocks; R0 H1 deliberately shares the same total-budget sample mapping across allocations.

The 1,068-coordinate scalar family contains all declared mean-vector scalar metrics, fixed comparator cosines, all paired early-late diagnostics and all scaling summaries. Following E4's max-standardized-deviation convention, the 95th percentile of the bootstrap maximum of |T*-T(empirical)| / bootstrap-SD gives symmetric simultaneous exploratory bands. These are plug-in functionals of a sample mean, so the empirical center is the observed functional. E5 does not redefine E4 U-statistic corrections. Delete-one paired-seed jackknife pseudovalue standard errors with Bonferroni Student-t(11) critical values are a sensitivity, not an exact finite-sample guarantee. Nominal percentile intervals are retained explicitly as sensitivity only: near-unit cosine and near-zero norms are nonlinear/nonregular, and percentile bias must not be hidden.

A separate 117-vector family covers 63 cell-windows and 54 first-K/last-K paired-difference contrasts. Full 124-dimensional centered seed vectors produce bootstrap Euclidean error norms, standardized by the estimated mean-vector trace standard error. The maximum gives a simultaneous confidence-ball sensitivity. Scalar and vector families are each nominally 95%, not jointly 95% with one another. Geometric norm/cosine bounds derived from the balls remain available alongside scalar intervals. No covariance isotropy or independent coordinates is assumed.

Every scaling ratio uses the original frozen signed projection as its primary scalar, with norm ratios as sensitivity. All three pairwise gamma comparisons, H4/H2, and all three allocation contrasts are evaluated for every K. No undefined resamples were dropped. Positive simultaneous projection bounds permit an additional conservative interval transformation for ratios and log slopes; unresolved denominators would be explicitly marked. Three gamma points only yield finite-grid secants, not an identified asymptotic exponent.

## Comparators fixed before the new run

- Zero vector: absolute-amplitude null predictor.
- Original x_ref: a frozen direction-only comparator, with its original sign.
- Negative T[Sigma]: the curvature/noise contraction without inverse-Hessian preconditioning, direction only.

Direction-only comparators are not assigned arbitrary amplitudes. They are not model-selection competitors, and better alignment than these comparators is not identification of a unique causal mechanism. Both algorithms' homogeneous B20 terms share the proxy direction.

## Scope and immutability

Input payload hashes are verified against the existing E4 ZIP manifest. Exact gamma values come from frozen JSON, not rounded cell IDs. All output is in a new E5 directory. No training, new seed, optimizer run, dataset split, E4 threshold change, or manuscript edit is performed. Reference derivatives and optimizer residual checks are evaluations of the existing saved x_ref, not a new optimizer fit.

E4's failed stationarity gates and outcome classifications are immutable here. E5 intervals quantify seed Monte Carlo variability conditional on one frozen dataset/protocol. They do not cover proxy remainder, state-dependent noise, reference-data uncertainty, stationary-law error, or generalization to other FL tasks. No statement here asserts that the entire bias or remainder is independent of H.
