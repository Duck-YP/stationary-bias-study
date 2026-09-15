# P2 d=2 formal coefficient protocol

This document freezes the d=2 homogeneous nonquadratic stochastic-SCAFFOLD coefficient study
before any formal P2-I2 trajectory is generated. The primary matrix and the mandatory H=4
smaller-step matrix are defined in `configs/d2_coefficient_primary.yaml` and
`configs/d2_h4_small_step_confirmation.yaml`.

## Scientific question

For the controlled model, the study asks whether

```text
C_hat(gamma, N, H) = [b_hat(gamma, N, H) - (gamma/N) B11_d] / gamma^2
```

approaches

```text
B20(H) = -((H-1)(5H-1)/(12H)) A^(-1) T[C]
```

along `gamma -> 0` and `N -> infinity`. The stationary mean-balance estimator is primary; the
direct stationary sample mean is a secondary diagnostic.

## Objective and noise

The objective is

```text
f(x) = 0.5 x^T A x + alpha psi(u^T x),
psi'(z) = log(cosh(z)),
A = [[1.2, 0.2], [0.2, 1.0]],
u = [1/sqrt(2), 1/sqrt(2)],
alpha = 0.25,
x_star = [0, 0].
```

Its Hessian is `A + alpha u u^T tanh(u^T x)`. The global bounds are
`mu = lambda_min(A - alpha u u^T) = 0.85` and
`L = lambda_max(A + alpha u u^T) = 1.565036762718386`.

Formal noise uses

```text
C = [[1.0, 0.2], [0.2, 0.7]],
epsilon = cholesky(C) z,
z_i in {-1, +1}.
```

The covariance eigenvalues are `0.6` and `1.1`. It is genuinely noncommuting:

```text
A C - C A = [[0.00, -0.02], [0.02, 0.00]] != 0.
```

Fresh Rademacher vectors are independent across chains, communication rounds, local steps, and
clients. Their transformed coordinates may be correlated.

## Exact targets

The NumPy-only P2 theory utilities give a Lyapunov residual at machine precision and

```text
S_C = [[0.413009404388715, 0.021943573667712],
       [0.021943573667712, 0.345611285266458]]
B11_d = [-0.024459428167733, -0.030574285209666]

H=2:
B20       = [-0.048004016395207, -0.060005020494009]
B20_local = [-0.032002677596805, -0.040003346996006]
B20_ctrl  = [-0.016001338798402, -0.020001673498003]

H=4:
B20       = [-0.152012718584823, -0.190015898231029]
B20_local = [-0.096008032790415, -0.120010040988019]
B20_ctrl  = [-0.056004685794409, -0.070005857243011]
```

For both H values, `B20_local + B20_ctrl = B20`. The sign already contained in `B11_d` is retained
when computing every coordinate of `C_hat`.

## Matrices and seeds

The primary path uses `H in {2,4}` and

```text
(gamma, N) = (1/12,12), (1/16,16), (1/24,24), (1/32,32), (1/48,48).
```

Primary seeds are `901` through `908`. The mandatory H=4 smaller-step path uses

```text
(gamma, N) = (1/64,64), (1/96,96), (1/128,128), (1/192,192),
```

with seeds `1001` through `1008`. Every setting contains all eight independent chains.

On both paths, `gamma = 1/N`, so `O(1/N + gamma) = O(gamma)`. Define
`delta = gamma + 1/N = 2 gamma`; separate gamma and inverse-N regressors are forbidden because
they are perfectly collinear.

## Stationarity and precision

The shared numerical protocol is inherited unchanged: 100 mixing-scale burn-in multiples,
20 mixing-scale rounds per batch, 100 minimum batches, 400 maximum batches, and extensions of
50 batches. The mixing scale uses `ceil(1/(mu H gamma))` with the formal global `mu=0.85`.
Finite-state, zero-sum-control, pre-update-qbar, stationarity, and direct-versus-balance diagnostics
retain the repository conventions.

After 100 batches, let `h_j` be the Bonferroni simultaneous-familywise 95% half-width for
coordinate `j` of the balance-based normalized coefficient. Extension stops only when every
coordinate satisfies

```text
h_j <= max(0.0025, 0.10 * abs(B20_j(H))),
```

or at 400 batches, or when a validity diagnostic fails.

## Coordinate uncertainty and extrapolation

Per-setting primary intervals use the eight chain estimates, Student-t with 7 degrees of freedom,
and Bonferroni familywise 95% coverage over two coordinates. Each coordinate therefore uses a
two-sided 97.5% interval. Marginal 95% intervals are secondary diagnostics; coordinates are never
pooled.

For each H and coordinate, fit setting means from the balance estimator as

```text
C_hat_j = beta0_j + beta1_j delta.
```

The coefficient estimate is `beta0_j`. A seed-block bootstrap resamples eight seed labels with
replacement and retains each resampled label across every setting in its H path. Each replicate
recomputes setting means and refits the line. The primary path uses 2,000 replicates and seed
`2901`; the H=4 smaller-step path uses 2,000 replicates and seed `2902`. Simultaneous intervals use
Bonferroni-adjusted 97.5% coordinate percentile intervals, with quantiles 0.0125 and 0.9875.
Marginal 95% percentile intervals are diagnostics.

## Frozen gates

- F0: every setting passes finite-state, zero-sum-control, and stationarity validity checks.
- F1: both H=2 targets lie inside their simultaneous primary bootstrap intervals.
- F2: report H=4 primary intercepts and simultaneous intervals; primary-grid coverage alone does
  not adjudicate H=4.
- F3: both H=4 targets lie inside the pre-registered smaller-step simultaneous intervals; also
  report coordinatewise movement relative to the primary H=4 intercepts.
- F4: systematic coordinate sign reversal on sufficiently small confirmation settings is a
  theorem or implementation warning.
- F5: direct-versus-balance agreement is reported coordinatewise as a diagnostic and cannot
  replace the balance estimator after results are seen.
- F6: every frozen setting and seed enters summaries; result-dependent exclusion is forbidden.

## Artifact namespaces and execution contract

```text
workstreams/p2_multidimensional_validation/artifacts/formal/p2-d2-coefficient-primary/
workstreams/p2_multidimensional_validation/artifacts/formal/p2-d2-h4-small-step-confirmation/
```

No directory is created by this protocol ticket. A later formal runner must require a clean
committed source tree, capture provenance before writes, and use the P1 controlled staging and
overwrite policy.

## Interpretation boundaries

- This experiment tests consistency with the P2 multidimensional theorem; it does not prove it.
- It does not test multidimensional FedAvg attribution, heterogeneity, growing H, state-dependent
  noise, d=5, or rotation invariance.
- It does not identify the full finite-N gamma-squared coefficient.
- Primary inference is signed coordinatewise vector inference, never norm-only inference.
- The mandatory H=4 smaller-step confirmation is frozen before any formal P2-I2 result is
  observed.

