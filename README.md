# Stationary Bias Study

This repository numerically studies the stationary bias of one-dimensional
stochastic SCAFFOLD. It is organized so a first-time reader can identify the
main entry point, experiment definitions, numerical engine, tests, and outputs
without knowing the thesis's historical experiment numbers.

The simulations are falsification attempts. They do not prove or disprove the
candidate theorem by themselves.

## Start here

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe run.py check
.\.venv\Scripts\python.exe run.py smoke-test
```

The only project entry point is `run.py`:

```text
python run.py check
python run.py smoke-test
python run.py test
python run.py run coefficient-convergence
python run.py run client-count-scaling
python run.py run negative-controls
python run.py run small-step-confirmation
python run.py plot-paper-figures
python run.py build-report
python run.py reproduce
```

`plot-paper-figures` is the plotting-only entry point. It reads the saved
summary and fit CSV files and rewrites the publication PNG files without
running simulations or recomputing means, confidence intervals, or regressions.

`reproduce` runs the tests, validates all frozen matrices, executes every
formal experiment, and rebuilds all summaries, figures, reports, and the run
manifest. Formal simulations can take substantially longer than the smoke
test.

## Experiments

| Public name | Research question | Config |
| --- | --- | --- |
| `coefficient-convergence` | Does the debiased coefficient converge to the candidate theoretical value? | `configs/experiments/coefficient_convergence.yaml` |
| `client-count-scaling` | Does the normalized effect persist as the client count increases? | `configs/experiments/client_count_scaling.yaml` |
| `negative-controls` | Do zero-noise, quadratic, and boundary cases behave as expected? | `configs/experiments/negative_controls.yaml` |
| `small-step-confirmation` | Does the H=4 discrepancy shrink at smaller step sizes? | `configs/experiments/small_step_confirmation.yaml` |

Historical thesis labels such as P3-A are stored only as metadata and in the
preserved scientific report. They are not used as public file or directory
names.

## Where to look

```text
run.py                              one obvious entry point
configs/simulation_defaults.yaml    shared frozen protocol
configs/experiments/                one readable config per research question
src/stationary_bias/                simulation and analysis implementation
tests/                              mathematical, invariant, and reproducibility tests
results/                            raw results, derived tables, figures, and reports
docs/                               protocol and architecture explanations
```

Important implementation files:

| File | Responsibility |
| --- | --- |
| `scaffold_algorithm.py` | Exact one-round SCAFFOLD recursion |
| `simulation.py` | Seeds, burn-in, batches, stopping rules, and raw CSV output |
| `theoretical_bias.py` | Candidate coefficients and normalization |
| `statistical_analysis.py` | Confidence intervals and bootstrap fits |
| `validation_checks.py` | Stationarity, finite-state, invariant, and estimator checks |
| `result_tables.py` | Derived CSV tables and the main report |
| `figures.py` | Original-study figures |
| `small_step_confirmation.py` | Isolated follow-up experiment and adjudication gates |

## Main outputs

- `results/final_report.md`: original preregistered study report.
- `results/small-step-confirmation/confirmation_report.md`: confirmatory follow-up report.
- `results/*/run_summary.csv`: one row per independent chain.
- `results/*/batch_summary.csv`: batch-level observations used for inference.
- `results/run_manifest.json`: config hashes, Git state, runtime, and package versions.

Raw CSV files are treated as primary numerical records. Summary tables,
figures, and Markdown reports are derived artifacts and can be rebuilt with
`python run.py build-report`.

## Reproducibility boundary

The random number generator is isolated per chain and all formal seeds are
frozen. `requirements.lock` records the exact reference package versions.
Numerical outputs should be compared with explicit floating-point tolerances;
PNG files need not be byte-identical across operating systems.
