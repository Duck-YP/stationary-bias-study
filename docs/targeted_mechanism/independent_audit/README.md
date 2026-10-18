# Independent read-only audit bundle

See REVIEW.md for scientific conclusions, scope, limitations, and numerical-tolerance details.
The manuscript has not been modified; no production training was rerun.

## Reproduce the checks

Create a working directory and extract this ZIP there. Then extract the uploaded
TARGETED_MECHANISM_REVIEW.zip into `review/`, SOURCE_TARGETED_MECHANISM.zip
into `source/`, and manuscript(2).zip into `manuscript_input/` (which contains
`manuscript/`). Copy the contents of `source/` into a scratch `test_env/` folder
for the compiled-kernel test. Do not run against or overwrite your original files.

Dependencies: Python, numpy, scipy, pandas, sympy, numba, pytest (versions should
be pinned using the uploaded source environment for strict reproducibility).

Run from this directory:

    python audit/independent_recompute.py
    python audit/model_kernel_crosscheck.py
    python audit/historical_saved_tables_check.py

The first script reads NPZ batches and rebuilds the frozen estimators/intervals.
The second symbolically checks the model and compares the submitted compiled
kernel with separately written original update equations on short test rounds.
The third replays supplied historical sufficient-statistic fits; it does not
reopen the original historical large archive.

The historical replay and new calculations use the uploaded sources/data; this
bundle alone is not a self-contained new experiment archive.

`audit/inference_comparison_details.csv` exposes all numeric differences,
including tiny scale-dependent floating-point deviations in raw-mean bootstrap
intervals. No experimental inference procedure was altered to pass these checks.
