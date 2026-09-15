# P2 controlled d=5 coefficient-validation protocol

This document freezes the controlled d=5 scientific design before any d=5 formal trajectory is
generated. The machine-readable contract is `configs/d5_controlled_validation.yaml`. Implementation
and tests may follow this freeze, but the 80-chain matrix requires a later clean committed tree and
a separate one-shot evidence run.

## Scientific question and boundary

The experiment asks whether the fixed-d multidimensional higher-order coefficient remains
empirically consistent when moving from the validated d=2 case to a genuinely five-dimensional,
correlated, noncommuting controlled problem.

This is empirical validation. It does not test heterogeneous clients, state-dependent noise,
growing H, multidimensional FedAvg attribution, arbitrary-dimensional empirical validity, or
universal local/control source identification.

## Objective

Use the existing rank-one log-cosh family

```text
f(x) = 0.5 x^T A x + alpha psi(u^T x),
psi'(z) = log(cosh(z)),
grad f(x) = A x + alpha u log(cosh(u^T x)).
```

Freeze `d=5`, `alpha=0.25`, `x_star=0`, and

```text
A = [[1.40, 0.15, 0.00, 0.00, 0.00],
     [0.15, 1.20, 0.12, 0.00, 0.00],
     [0.00, 0.12, 1.10, 0.10, 0.00],
     [0.00, 0.00, 0.10, 1.30, 0.08],
     [0.00, 0.00, 0.00, 0.08, 1.00]].

v = [1, 2, -1, 1.5, -0.5],
u = v / sqrt(8.5)
  = [ 0.34299717028501764,
      0.6859943405700353,
     -0.34299717028501764,
      0.5144957554275265,
     -0.17149858514250882].
```

The direction is unit norm, non-axis, and mixed-sign. The A eigenvalues are

```text
[0.9625491531631433, 0.9999482527832112, 1.1871301563374088,
 1.3595619300283060, 1.4908105076879310].
```

The global Hessian bounds are

```text
mu = lambda_min(A - alpha u u^T) = 0.8037572789315114,
L  = lambda_max(A + alpha u u^T) = 1.6235689623537297.
```

## Additive noise

Freeze

```text
C = [[1.00, 0.18, 0.05, 0.00, 0.00],
     [0.18, 0.85, 0.12, 0.04, 0.00],
     [0.05, 0.12, 0.90, 0.15, 0.03],
     [0.00, 0.04, 0.15, 0.75, 0.10],
     [0.00, 0.00, 0.03, 0.10, 0.80]].
```

Its eigenvalues are

```text
[0.6250659950770690, 0.7003228528633275, 0.8051736035904453,
 0.9824782898780277, 1.1869592585911308].
```

Both A and C are symmetric positive definite, and
`||A C - C A||_F = 0.08761712161444248`, so the system is noncommuting.

For `C = L L^T`, draw iid Rademacher coordinates and use `epsilon = z @ L.T` for last-axis
NumPy vectors. Gaussian, state-dependent, and client-dependent-covariance variants are excluded.

## Theory targets

Let `S_C` solve `A S_C + S_C A = C`. The frozen solution is

```text
S_C =
[[ 0.35416473352098043,  0.02779582047084913,  0.01806310274307949, -0.00145694791159776,  0.00012275134005303],
 [ 0.02779582047084913,  0.34959056278983780,  0.01101626317972773,  0.01411752653201167, -0.00118698255466298],
 [ 0.01806310274307949,  0.01101626317972773,  0.40492090905985490,  0.03265048452592303,  0.01219622330574720],
 [-0.00145694791159776,  0.01411752653201167,  0.03265048452592303,  0.28476945183498037,  0.01918330202416588],
 [ 0.00012275134005303, -0.00118698255466298,  0.01219622330574720,  0.01918330202416588,  0.39846533583806676]].
```

For `T[M] = alpha u (u^T M u)`, use

```text
B11_d = [-0.007741472935786256, -0.025158890352923790,
        0.017734150314997830, -0.018766028411084970,
        0.008807230104405750].

H=2:
B20       = [-0.014024998786462132, -0.045579621552043930,
              0.032128438439286150, -0.033997861631155890,
              0.015955799697419393]
B20_local = [-0.009349999190974754, -0.030386414368029285,
              0.021418958959524100, -0.022665241087437258,
              0.010637199798279596]
B20_ctrl  = [-0.004674999595487377, -0.015193207184014642,
              0.010709479479762050, -0.011332620543718629,
              0.005318599899139798]

H=4:
B20       = [-0.044412496157130080, -0.144335468248138760,
              0.101740055057739480, -0.107659895165326980,
              0.050526699041827994]
B20_local = [-0.028049997572924260, -0.091159243104087860,
              0.064256876878572300, -0.067995723262311780,
              0.031911599394838786]
B20_ctrl  = [-0.016362498584205820, -0.053176225144050630,
              0.037483178179167190, -0.039664171903015205,
              0.018615099646989278].
```

For each H, `B20_local + B20_ctrl = B20` to numerical precision.

## Formal matrix and estimator

For each `H in {2,4}`, use

```text
(N, gamma) = (32,1/32), (48,1/48), (64,1/64), (96,1/96), (128,1/128).
```

Every setting uses seeds `1201` through `1208`. The matrix therefore has ten settings, eight
chains per setting, and 80 chain runs. No setting may be filtered or added. Along the path,
`gamma=1/N` and `delta=gamma+1/N=2 gamma`.

The primary signed coordinatewise estimator is

```text
C_hat_j = [b_hat_j - (gamma/N) B11_d_j] / gamma^2.
```

The stationary mean-balance estimate is primary. The direct stationary sample mean is diagnostic.

## Mixing, batching, and setting uncertainty

For each setting use

```text
mixing_scale  = ceil(1 / (mu H gamma)),
burn_in       = 100 * mixing_scale,
batch_length  = 20 * mixing_scale,
min_batches   = 100,
extension     = 50 batches,
max_batches   = 400.
```

The finite-state, zero-sum-control, stationarity, and direct-versus-balance semantics match the
existing P2 formal pipeline.

Eight chains give seven degrees of freedom. Bonferroni familywise 95% coverage over five
coordinates assigns a two-sided 99% interval to each coordinate, using
`t_(7,0.995) = 3.4994832973504924`. Marginal 95% intervals remain diagnostic.

After 100 batches, every coordinate must satisfy

```text
halfwidth_j <= max(0.0025, 0.10 * abs(B20_j(H))).
```

Checks extend by 50 batches up to 400, with no vector-norm replacement.

## Extrapolation and bootstrap

For each H and coordinate, fit all five settings with

```text
C_hat_j = beta0_j + beta1_j delta.
```

The coefficient estimate is `beta0_j`. Separate gamma and inverse-N regressors are forbidden on
this collinear path.

Use 5,000 bootstrap replicates and bootstrap seed `3901`. Resample the eight seed labels with
replacement and reuse each sampled label block, including multiplicities, across all five settings
within its H fit. Marginal quantiles are `[0.025,0.975]`; simultaneous Bonferroni familywise-95%
quantiles across five coordinates are `[0.005,0.995]`.

## Frozen gates

- V0 requires finite states, zero-sum controls, stationarity, and matrix validity.
- V1 requires all five H=2 targets inside their simultaneous bootstrap intercept intervals.
- V2 requires all five H=4 targets inside their simultaneous bootstrap intercept intervals.
- V3 reports setting-level sign against theory and is diagnostic only.
- V4 reports coordinatewise direct-minus-balance normalized coefficients and is diagnostic only.
- V5 requires exactly ten settings and 80 chains with no missing or unexpected run.

The combined formal verdict requires V0, V1, V2, and V5.

## Evidence contract and interpretation

The formal namespace is

```text
workstreams/p2_multidimensional_validation/artifacts/formal/p2-d5-controlled-validation/
```

It preserves provenance, raw run and batch tables, setting summaries and diagnostics, fit and
bootstrap tables, falsification gates, a formal manifest, one report, and H=2/H=4 convergence
figures. Formal execution requires a clean committed tree, pre-write provenance, exact config and
protocol hashes, matrix validation, namespace isolation, staging, and refusal to overwrite.

If V0, V1, V2, and V5 pass, the permitted empirical wording is: “The pre-registered controlled
d=5 experiment is consistent with the multidimensional higher-order coefficient for H=2 and H=4
under the frozen coordinatewise simultaneous-bootstrap criterion.”

This does not establish the theorem experimentally, arbitrary-dimensional validity, d=5 FedAvg
attribution, separate empirical identification of the local/control terms, heterogeneity,
state-dependent noise, or growing H. The local/control decomposition is theory metadata only.
