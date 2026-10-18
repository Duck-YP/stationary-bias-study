# Targeted mechanism closure, 2026-10-14

This directory is an isolated follow-up. The authoritative local manuscript is
`../manuscript/`; its contents and the historical study source are checked by
`BASELINE_MANIFEST.json` and `BASELINE_AFTER_CHECK.json`. No manuscript patch was
applied, no historical production study was rerun, and nothing was pushed.

Start with `SCIENTIFIC_SUMMARY.md`. The review ZIP contains all 304 new paired-run
summaries (16 pilot, 288 production), all production per-run/window/batch vectors,
all conditions and both coordinates, the historical analysis-only audit, the
model and kernel certificates, proposed literature changes, and figures. The
source ZIP contains the independent trigonometric path, independent validation,
analysis, plotting, packaging, input brief, and the available current historical
test source. That test source is not represented as a complete historical freeze.

## Execution and arithmetic

`targeted/kernels.py::trigonometric_chunk` is selected explicitly. It does not
import `study/kernels.py::controlled_chunk`, whose old objective remains intact.
The new path evaluates the gradient of the fixed trigonometric objective and
regenerates diagonal weights and balance solves from A=diag(1,2). Division by the
diagonal B is a componentwise linear solve; no dense explicit inverse is formed.
Stable log1p/expm1 evaluates B. No fastmath is enabled.

The control update is algebraically rewritten as old mean control plus centered
summed non-control oracle terms divided by H. It preserves a nonzero incoming
control mean; no projection is used. Paired algorithms receive the same indexed
noise; all cells, conditions, phases and seeds have independent indexed streams.
Noise is never empirically recentered, rescaled or whitened. Hash-based generators
are pseudorandom implementations of the analytically specified independent laws.

Each batch stores its actual start/end states, count, post-round raw means,
nonlinear balance means, noise eta mean, round-recursion residual mean, and control
mean/residual maxima. The exact finite-window identity is checked both with and
without the recorded arithmetic residual. It is not a stationarity certificate.
First/last half windows are temporal diagnostics; they are not substituted for the
primary window. Pilot variance forecasts do not guarantee final precision.

## Reproduction on this machine

Run the following in PowerShell from `.`.

```powershell
$studyPython = 'python'
$env:PYTHONPATH = './supplementary_study/.deps'
$env:NUMBA_CACHE_DIR = './targeted_closure_20261014/local/numba_cache'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $studyPython targeted_closure_20261014\run.py test
& $studyPython targeted_closure_20261014\certificate\independent_kernel_checks.py
& 'python' targeted_closure_20261014\certificate\independent_model_checks.py
& $studyPython targeted_closure_20261014\run.py pilot --jobs 4
& $studyPython targeted_closure_20261014\run.py production --jobs 8
& $studyPython targeted_closure_20261014\analyze.py
& $studyPython targeted_closure_20261014\summarize_results.py
& $studyPython targeted_closure_20261014\plots\plot_mechanism_checks.py
& $studyPython targeted_closure_20261014\historical_audit\audit_existing_h4.py
```

Production reads the existing frozen protocol and verifies simulation source
hashes. Completed files are reused and checkpointed unfinished runs resume with
identical indexed noise. `forecast.py` was used once before production to create
the protocol; do not rerun it to silently re-freeze a finished study.

For a clean reproduction, keep the same directory layout with a separate output
copy and install the versions in `ENVIRONMENT.json` (plus SymPy 1.14.0 for the
independent symbolic certificate). On another system the numerical environment
may change last-bit arithmetic and timings. `run.py` uses a sibling `.deps`
directory only when it exists, otherwise the current Python environment.
Historical audit reproduction requires the original inputs listed in
`historical_audit/INPUT_SHA256.csv`; they are not recreated from manuscript tables.

## Local retrieval

The ZIP stores compact run results under `run_summaries/{pilot,production}/...`.
For analysis after unpacking, copy these folders to `local/{pilot,production}/`
under the unpacked root. Large per-round trajectories were never saved.
Resume checkpoints and cached compiled code remain under this local directory's
`local/`; literature primary PDFs and rendered source checks remain under
`literature/sources/`. `LOCAL_ARTIFACT_MANIFEST.json` records paths, sizes and
hashes for checkpoints, run summaries and source literature. The existing large
historical archives stay in their original locations, with retrieval paths in
the historical audit. No additional audit archive is needed for this small study.

## Interpretation

The 36 primary scalar summaries and their bootstrap scheme were frozen before
production. Approximate simultaneous intervals, ordinary marginal intervals and
Bonferroni-t sensitivities are sampling summaries; they exclude deterministic
grid remainder and burn-in error. A zero-target interval inside a practical band
means resolution within that band, even if it excludes exact zero. An interval
containing zero but wider than the band is inconclusive. Target exclusion alone
is neither a theorem counterexample nor permission to refit or extend the study.

Plot captions distinguish primary full-grid results from the prespecified
omit-largest-step sensitivity. The figures contain one vector-PDF panel each;
LaTeX may arrange them later. No manuscript integration has been performed.
