# P2 d=2 fixed-gamma large-N plateau protocol

Frozen for execution on 2026-09-14.

## Frozen matrix

The experiment reuses the d=2 coefficient-validation objective, covariance, theory constants,
stationary mean-balance estimator, simulator, burn-in, batching, stopping, and diagnostic logic.
It fixes `H=2` and `gamma=1/24`, varies only `N` over `8, 16, 32, 64, 128`, and runs the
fresh seed block `1301`–`1308` at every N. The resulting matrix has five settings and 40 chains.
No setting or seed may be excluded after results are inspected except for a documented
implementation failure.

The primary coordinate statistic is

```text
C_hat_j = (b_hat_j - (gamma/N) B11_d_j) / gamma^2,
```

where `b_hat` is the stationary mean-balance estimator. Direct stationary sample means are
diagnostic only.

## Frozen inference

For each coordinate, the five setting means are fit by ordinary least squares as

```text
C_hat_j(N) = beta0_j + beta1_j (1/N).
```

One seed-label bootstrap index vector is resampled and reused across all five N settings and
both coordinates. Two thousand replicates provide marginal 95% intervals and Bonferroni-style
simultaneous-coordinate 97.5% percentile intervals for `beta0`.

At fixed gamma, the comparison is `beta0 = B20(H=2) + O(gamma)`. Exact B20 interval coverage is
reported but is not a PASS gate. The report must expose `beta0-B20` and `(beta0-B20)/gamma`.

## Frozen validity and warning rules

- F0 requires finite-state, zero-sum-control, and stationarity validity for every coordinate at
  every N.
- F1 requires all 40 frozen chains and all five N settings with no exclusions.
- F2 requires finite intercepts and finite bootstrap interval endpoints for both coordinates.
- F3 requires, coordinatewise, a simultaneous intercept interval excluding zero, one consistent
  sign across all five per-N means, and the N=128 mean closer to beta0 than the N=8 mean.
- F4 requires finite, explicit B20 discrepancies and gamma-scaled discrepancies.
- F5 records exact B20 interval coverage as diagnostic only.
- F6 produces a scientific warning if an intercept has the opposite sign from B20, its magnitude
  is below 25% of `abs(B20)`, per-N means change sign at least twice, or the N=128 magnitude is
  greater than three times `abs(B20)`.

The final verdict is FAIL if F0, F1, F2, or F4 fails; WARNING if those validity gates pass but F3
fails or F6 triggers; otherwise it is PASS. The result is an empirical consistency check, not a
proof and not an exact finite-gamma test of B20.

## Artifact order and provenance

The formal runner requires a clean committed source tree. It captures the exact source commit,
environment, config and protocol hashes, seed list, frozen matrix, and commands before writing
any output. Raw and derived outputs are built in a sibling staging directory. The two figure
files are created before the report or manifest references their filenames. Only a fully
populated staged directory is atomically installed into the dedicated artifact namespace.
