# P2 — Multidimensional homogeneous SCAFFOLD validation

P2 validates homogeneous vector SCAFFOLD through a d=2 engineering smoke setting, frozen d=2
coefficient matrices, a paired coordinate-rotation matrix, and a controlled d=5 coefficient
matrix. It also includes a fixed-gamma large-N plateau matrix. Numerical evidence is a
consistency and implementation check, not a mathematical proof.

## Entry points

```text
.venv/bin/python run.py p2 check
.venv/bin/python run.py p2 smoke
.venv/bin/python run.py p2 formal check
.venv/bin/python run.py p2 formal primary run
.venv/bin/python run.py p2 formal primary analyze
.venv/bin/python run.py p2 formal primary report
.venv/bin/python run.py p2 formal h4-small-step run
.venv/bin/python run.py p2 formal h4-small-step analyze
.venv/bin/python run.py p2 formal h4-small-step report
.venv/bin/python run.py p2 rotation check
.venv/bin/python run.py p2 rotation run
.venv/bin/python run.py p2 rotation report
.venv/bin/python run.py p2 d5 check
.venv/bin/python run.py p2 d5 run
.venv/bin/python run.py p2 d5 analyze
.venv/bin/python run.py p2 d5 report
.venv/bin/python run.py p2 plateau check
.venv/bin/python run.py p2 plateau run
.venv/bin/python run.py p2 plateau analyze
.venv/bin/python run.py p2 plateau report
```

The formal `run` routes consume only frozen YAML matrices and require a clean committed source.
Raw CSVs, summaries, reports, figures, and manifests are built in a sibling staging directory.
An existing canonical matrix is replaced only when its identity and raw scientific fields match;
directory exchange is atomic and restores the prior snapshot if installation fails. The `analyze`
and `report` routes rebuild from saved data in staging and never invoke the simulator.

The smoke setting uses `d=2`, `H=2`, `N=4`, `gamma=0.05`, seeds `801`–`803`, five
mixing-time burn-in multiples, two mixing-time rounds per batch, and four fixed batches.
Artifacts are isolated under `artifacts/smoke/`.

## Formal matrices

- `p2-d2-coefficient-primary`: ten H=2/H=4 settings and 80 chains.
- `p2-d2-h4-small-step-confirmation`: four H=4 settings and 32 chains.
- `p2-d2-rotation-invariance`: 16 pathwise-coupled rotation pairs.
- `p2-d5-controlled-validation`: ten H=2/H=4 settings, 80 chains, and five-coordinate inference.
- `p2-d2-fixed-gamma-largeN-plateau`: five N settings at H=2 and gamma=1/24, 40 chains,
  coordinatewise `1/N` intercept fits, and exactly two formal figures.

Each matrix is isolated under `artifacts/formal/<matrix-id>/`. Exact inputs, uncertainty rules,
gates, and interpretation boundaries are defined by the corresponding YAML and protocol document.

## Notation compatibility

The manuscript notation \(B_{11}^{(d)}\) denotes the signed multidimensional coefficient of the
leading \(\gamma/N\) term. Machine-readable experiment inputs and immutable formal artifacts retain
the historical field label `B10`, with the exact correspondence

```text
B10 (experiment artifact) = B_{11}^{(d)} (manuscript)
C_hat = [b_hat - (gamma/N) B_{11}^{(d)}] / gamma^2.
```

This is a notation mapping only. The tensor definition, numerical values, normalization, seeds,
raw outputs, statistical analysis, and scientific conclusions are unchanged.

## Vector stationary mean-balance estimator

Let `P = I - gamma A`, and let `qbar_h` be the client average of `q(theta_h)` evaluated
before local update `h`. For each communication round, P2 records

```text
z = -(I - P^H)^(-1) gamma sum_{h=0}^{H-1} P^(H-1-h) qbar_h.
```

This is the exact stationary-server-mean identity induced by the same pre-update convention used
in P0 and P1. The direct sampled server mean is retained as a separate diagnostic estimator.

CSV outputs use one row per coordinate and estimator. Signed coordinate values are preserved;
vector norms appear only in the chain diagnostic table.

## Smoke matrix

The engineering setting fixes `d=2`, `H=2`, `N=4`, `gamma=0.05`, and seeds
`801`, `802`, and `803`. Its mixing scale is 12 rounds, burn-in is 5 mixing scales
(60 rounds), every batch is 2 mixing scales (24 rounds), and exactly 4 batches are
collected. These values exercise the full pipeline without supporting a scientific inference.
