# Reproduce And Continue

No command below edits the manuscript or original supplementary artifacts.
Unzip each ordinary ZIP into its own new directory. The handoff is independently
replayable; SOURCE_E4 contains source, frozen settings and compact numerical inputs.
No dependencies or redundant finished-run checkpoints are bundled.

## Portable Existing-Data Replay (No Training)

From the extracted package root, use Python3.12 with the tested versions in
requirements_e4.lock. A clean pip install was NOT tested; the existing local
dependency runtime was used. Keep the recorded environment instead of assuming
cross-platform bitwise equivalence.

```powershell
python code/replay.py models --root .
python practical/evaluate_models.py --model-file models.npz --input-root practical/inputs --output practical
python code/replay.py inference --root .
python independent_audit/verify_e4_reassembly.py --root . --output independent_recheck
python -m pytest statistical_review/test_reference_math.py independent_audit/test_independent_math.py practical/test_evaluate_models.py -q -p no:cacheprovider --basetemp e4_test_tmp
```

Inference uses19999 draws seed202610094, all paired seed labels20001..20012,
all9cells and all sevenwindows. It reproduces signed U, V, MSE, corrections,
loss contrasts, temporal equivalence and precision flags. Replaying replaces
generated output files *in that extracted copy*, not immutable source data.

```powershell
python code/figures.py --root .
pdflatex -interaction=nonstopmode -halt-on-error E4_FIGURES_GALLERY.tex
python code/audit_fonts.py --root .
pdftoppm -png -r 120 E4_FIGURES_GALLERY.pdf figures/gallery
```

Figures require TeX with lmodern, dvipng and Matplotlib; gallery layout performs
the PDF insertion, not plot grids. Panel source dimensions must not be arbitrarily
rescaled below the verified final9pt floor. Initial failed font/visual checks are
retained in FIGURE_QA_FAILURES.md.

## Exact Local Runtime Used

```powershell
Set-Location '.'
$python='python'
$env:PYTHONPATH=(Resolve-Path 'supplementary_study/.deps').Path
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MPLCONFIGDIR=(Join-Path (Resolve-Path 'significance_e4/20261009').Path 'mpl_cache')
$env:NUMBA_CACHE_DIR=(Join-Path (Resolve-Path 'significance_e4/20261009').Path 'numba_cache')
& $python 'significance_e4/20261009/code/replay.py' models --root 'significance_e4/20261009'
& $python 'significance_e4/20261009/code/replay.py' inference --root 'significance_e4/20261009'
& $python 'significance_e4/20261009/independent_audit/verify_e4_reassembly.py' --root 'significance_e4/20261009' --output 'significance_e4/20261009/independent_recheck' --workspace '.'
```

Original preparation (already executed, requires original full artifacts):

```powershell
& $python 'significance_e4/20261009/code/prepare.py' --original 'supplementary_study/results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF' --out 'significance_e4/20261009'
```

Freeze scripts refuse existing protocol files. Do not rerun freeze to overwrite
the archived protocols. Independent portable mode needs neither the3.16GB archive
nor the original workspace; historical preservation is then an explicitly
archived receipt, not a new audit of unavailable files.

## E4_v2: Executed Pilots And Exact Production Continuation

The command actually executed was:

```powershell
& $python 'significance_e4/20261009/code/v2.py' pilot --root 'significance_e4/20261009' --max-seconds 600
& $python 'significance_e4/20261009/code/v2.py' pilot_summary --root 'significance_e4/20261009'
& $python 'significance_e4/20261009/code/pilot_analysis.py' --root 'significance_e4/20261009'
```

Both pilot seeds30001,30002 completed189440rounds and128batches. Finished result
files make the runner skip those seeds; it must not pretend they are new samples.
Unchanged frozen kernels, data and protocol hashes are checked on continuation.

**Not yet executed:48seed E4_v2 production.** To start the preregistered block
with a10-minute wall-clock cap and deterministic checkpoints:

```powershell
& $python 'significance_e4/20261009/code/v2.py' production --root 'significance_e4/20261009' --max-seconds 600
```

Then continue the same block without discarding or restarting checkpoints:

```powershell
& $python 'significance_e4/20261009/code/v2.py' production --root 'significance_e4/20261009' --max-seconds 600 --resume
```

Repeat the latter command until all48result files exist; it resumes the first
unfinished seed and records remaining not-started seeds. Streams, horizon,
objective and reference are fixed. Each chunk checks deadline and memory4GB.
The planned output path is
`v2/raw/production/E4_v2_R0_H4_N128_g0.196078431373/seed_31001..31048`.
Single-seed execution can use `--seed31001` written as `--seed 31001`; use unique
seeds/worker directories and memory budgeting, never concurrent writes to one
seed. Serial projected cost11.67h before pilots,5.93h at pilot throughput;
full controls/results project~6.55GB plus checkpoint storage. No speed/precision
guarantee is made.

**Production analysis/export is NOT IMPLEMENTED OR EXECUTED in this delivery.**
The frozen v2 plan uses48seeds, dyadic K through1024, paired bootstrap19999draws
seed202610095, separate K-family intervals and the same temporal margins. The
v1 inference entry point is deliberately fixed to the9-cell/R12/K<=64 study:
do not feed v2 output into it or pool old/new/pilot trajectories. A separate
v2 analysis implementation and QA are a necessary continuation step after
training. This explicit unfinished item is not marked complete or negative.

## Source And Archive Verification

```powershell
python code/package.py verify --root .
```

SOURCE_SHA256.csv and PACKAGE_MANIFEST.csv identify code and all packaged evidence.
Archive CRC and extracted portable replay receipts are retained separately.
Historical full Phase0 log remains local; its complete compact check list,
original path/hash/size and all per-run statuses are included. Historical
repository tables/configs/diagnostic failure reports are preserved without
altering H4 selection/target-inclusion rules.
