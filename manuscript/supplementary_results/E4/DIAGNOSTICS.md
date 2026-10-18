# Diagnostics And Scientific Limits

## Chronology And Temporal Evidence

All9 R0 cells have12 paired runs and64 complete chronological batches. Counts
are uniform within each frozen cell but vary across cells (1280,2560,5110rounds).
Included batches preserve actual global sums, trace-square centered at x_ref,
endpoint snapshots and control diagnostics. batch_sumsq is not xx-transpose.
Temporal windows are correlated within run, never extra independent seeds.

TEMPORAL_DIAGNOSTICS.csv contains144 predeclared first/last and middle/last
contrasts. All equivalence gates fail under +/-0.0001 projected drift and0.001
full-vector norm margins. The joint95% bootstrap maximum covers both projection
and vector-norm gates across all contrasts. The safe zero-scale guards forbid
manufactured perfect precision. K64 has no matching64-batch alternative anchor,
so inherits the32-batch test. Failure to establish equivalence is not evidence of
nonstationarity. The original R0 runs have no independently extended burn/tail
sensitivity; finite-tail evidence cannot be upgraded to a stationary certificate.

AUTOCORRELATION_PROXIES.csv retains all seeds' lag1,2,4,8batch frozen-projection
autocorrelations. They are coarse batch-mean proxies, not raw-round IAC estimates;
no K_eff, independence of batches or1/K variance law is assumed.

## Reference, Objective And Projection

inputs/optimizer_certificates.json and reference_optimizers.npz retain the
separate optimizer crosscheck and strong-convexity reference error certificate
(parameter bound approximately1.25e-14). Objective and gradient were re-evaluated
without optimization. The frozen124-coordinate direction is bit-identical in
PROTOCOL_FROZEN.json and reference arrays and was stored before original
production. It is objective-derived descriptive, not a homogeneous theorem target.

Uniform retained32512 training rows, fixed excluded49rows, row norm division by
max(1,L2norm),123features plus intercept, all124coordinates regularizedlambda0.01.
Test16281rows have identical frozen preprocessing. Data/raw/processed hashes and
partition-membership manifests are included. No test fitting or threshold tuning.

## Inference And Precision

Signed U is unbiased for squared finite-tail mean displacement under independent
identically distributed runs of the fixed protocol. U may be negative. V is
between-run variance of the *averaged* model, not raw within-tail variance.
MSE=U+V and DeltaU=2C_U+U_delta are checked independently to roundoff.

19999 paired-seed bootstrap draws, fixed seed202610094. Exact empirical-population
centering corrects the otherwise biased U bootstrap: U0=plugin norm squared,
V0=(R-1)V/R. Standardized maximum absolute deviations give primary196-coordinate,
secondary392-coordinate and diagnostic1176-coordinate families separately.
Bootstrap standard deviations are fixed scales, not nested bootstrap-t estimates.
All claims remain approximate with R12. Delete-one jackknife-t Bonferroni is a
sensitivity, and zero/near-degenerate jackknife scales cannot establish precision.
The U-minus-V and U-minus0.1MSE contrasts receive their own degeneracy checks.
Weak zero-bias regimes, especially N8/N32 and short windows, remain flagged.

## Numerical Versions And Pilots

Kernel/model/data/engine bytes match the original frozen hashes. V2 uses these
unchanged recursions, no zero-sum projection or endpoint-increment substitution.
Full v2 pilot horizons are189440rounds; all batches/averages are finite and
control zero-sum residuals reach6.50e-11. Two short reference/common-noise/resume/H1
gates plus the14-test legacy E0 suite pass, but do not certify full-horizon H1
identity. Original approximately1e-10-scale H1 long-horizon deviations are
unresolved and retained, not corrected by overwriting results.

V2 pilots have R2 and are diagnostic only. Their descriptive U/V/MSE and temporal
differences, including unfavorable/negative values, are retained without
significance or stable-floor claims. Full48seed extension has not run. Actual
pilot throughput updates projected serial production from11.67 to5.93hours;
parallel speedup and precision remain planning assumptions.

## Historical Scientific Boundaries

The original69-cell per-run/full-result tables are included unchanged, not just
R0 successes. Historical H4 theory-target exclusions and H8 finite-grid offsets
remain. E1 concerns theory coefficients under homogeneous bounded additive noise;
E2 exact relation is limited affine objective-shift/state conjugacy; E3/E4 real
data concerns conditional implications. No universal heterogeneous theorem, no
exact R0 homogeneous control coefficient, and no H-independent entire remainder
claim is made. E1 mechanistic bridge was not executed.
