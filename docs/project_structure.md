# Project structure and data flow

The public interface uses research-question names. Short historical labels are
retained only inside preserved result schemas so an auditor can trace every
row back to the original thesis protocol.

```text
YAML experiment config
        |
        v
simulation.py -----> raw run_summary.csv and batch_summary.csv
        |                            |
        |                            v
        +--------------------> result_tables.py
                                      |
                         +------------+------------+
                         |                         |
                         v                         v
                    summary CSVs             final_report.md
                         |
                         v
                     figures.py
```

The exact local update is isolated in `scaffold_algorithm.py`. It does not
choose seeds, read files, decide stopping conditions, calculate confidence
intervals, or create figures. This boundary makes it possible to test the
algorithm independently from the experimental protocol.

`simulation.py` owns all stateful experiment execution. Each independent chain
has its own NumPy random generator. The module records both the direct
stationary-mean estimator and the balance-identity estimator.

`result_tables.py` reads raw results and performs chain-level inference. It
never changes the simulation trajectory. `figures.py` reads derived tables and
does not perform hidden smoothing or refitting.

The small-step confirmation has its own config, raw directory, report, and
adjudication implementation. It cannot overwrite the original study report.

