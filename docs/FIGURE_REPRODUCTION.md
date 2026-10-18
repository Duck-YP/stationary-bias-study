# Saved-data figure reproduction

The **18 October 2026 figure/layout revision of V2** has five figures comprising nine active standalone vector panels: seven controlled/real-data panels plus `e4_averaging_scaffold.pdf` and `e4_averaging_fedavg.pdf`. All nine were redrawn from unchanged saved numerical inputs; their CSV sidecars remain byte-identical to the clean V2 baseline. The current compiled manuscript has 40 pages, SHA-256 `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`. E5 and the targeted mechanism results remain tabular; the separate 32 targeted evidence PDFs are not active manuscript figures.

The public commands below use only release-relative paths. Detailed source columns, selected rows, hashes and display transformations are recorded in `manuscript/FIGURE_PROVENANCE.md`; the current public validation outcomes are in `docs/VALIDATION_RECEIPT.md`.

## Prerequisites

Python 3.12 or newer and the declared dependencies are required. The historical seven-panel environment is recorded in `configs/environments/figure_redraw.requirements.lock`. It used Python 3.12.14, NumPy 2.5.3 and Matplotlib 3.11.2; its other pinned packages support PDF auditing. Those pins are a recorded environment, not a fresh combined-installation receipt.

The seven-panel and E4 renderers use TeX text. TeX Live must provide `latex`, `pdflatex`, BibTeX and `dvipng`, together with the manuscript packages and Latin Modern/T1 fonts. The earlier executed build used pdfTeX 1.40.26 / TeX Live 2024. The targeted standalone plots use embedded TrueType text and their own saved style.

## Current seven-panel renderer

From the public release root in PowerShell, after installing the package:

```powershell
.venv\Scripts\python.exe -m pip install -r configs\environments\figure_redraw.requirements.lock
.venv\Scripts\python.exe -B scripts\figure_redraw\redraw_figures.py --input-root artifacts\canonical_paper_export\figure_redraw --output ..\figure_replay
.venv\Scripts\python.exe -B scripts\compare_figure_replay.py --group historical --replay ..\figure_replay --output ..\figure_replay_receipt.json
```

Use a new isolated output directory. On Linux/macOS use `.venv/bin/python` and forward slashes. The renderer and `figure_style.py` are synchronized copies of `manuscript/tools/figure_layout/`. They read ten saved CSVs and saved fit coefficients/curves, then write seven PDFs, PNGs, sidecars, geometry records and provenance without fitting or bootstrapping. The comparison group name `historical` identifies these seven panels, including their current styling; it does not select an obsolete renderer. E4 is rendered separately. Display transformations retain the R0 multiplication by 1000 and absolute residuals. The log–log diagnostic connects saved residual points rather than introducing a new fitted trend.

Use the generated comparison receipt to distinguish saved-record/geometry agreement, render agreement and PDF byte identity. TeX font subset prefixes can change PDF bytes; a rendered-equivalence result must not be described as byte-identical PDFs. The old seven-panel `PASS_RENDER_EQUIVALENT` receipt retains its original scope.

## E4 panels and E4/E5 saved-data checks

The current `manuscript/tools/plot_e4_for_manuscript.py` reads `manuscript/supplementary_results/E4/BIAS_VARIANCE_MSE.csv`. It selects the designated primary configuration, retains all seven windows and plots unchanged saved simultaneous intervals for U and V. Filled circles/solid lines distinguish U from open squares/dashed lines for V. Its unchanged symmetric-log scale (`linthresh=1e-5`, `linscale=0.75`) retains negative U estimates and intervals crossing zero.

The script writes beneath its own manuscript directory. To preserve the supplied publication artifacts, first copy `manuscript/` into a new scratch location, then run the copied script:

```powershell
Copy-Item -LiteralPath manuscript -Destination ..\manuscript_figure_replay -Recurse
.venv\Scripts\python.exe -B ..\manuscript_figure_replay\tools\plot_e4_for_manuscript.py
.venv\Scripts\python.exe -B scripts\compare_figure_replay.py --group e4 --replay ..\manuscript_figure_replay\figures\redrawn --output ..\e4_figure_replay_receipt.json
```

The destination must be a new directory. This renders two PDFs, PNGs, sidecars and E4 provenance; it does not recompute intervals. `--group e4` restricts comparison to those two outputs. If both renderers write into one scratch figure directory, `--group all` compares all nine panels. E4/E5 point estimates and saved interval consistency can be checked directly:

```powershell
.venv\Scripts\python.exe -B manuscript\tools\check_saved_e4_e5.py --out ..\saved_e4_e5_recheck.json
.venv\Scripts\python.exe -B scripts\validate_release.py
```

The E4/E5 checker reconstructs algebraic quantities from saved averaged models and vectors. Its optional original-batch reconstruction requires omitted historical input and is not part of this command. The release validator includes the current bounded targeted table/data checks; it does not refit or resample the targeted study.

## Targeted evidence figures

`artifacts/canonical_paper_export/targeted_mechanism/plots/` preserves eight main panels and 24 supplementary grid panels, `FIGURE_CAPTIONS.md`, `FIGURE_MANIFEST.json`, `FIGURE_QA.json` and plotting source. Main panels compare all three observables and both coordinates, showing the full grid and prespecified restricted-grid sensitivity. Grid panels retain all four conditions. No panel is selected by target inclusion.

Main whiskers are the saved approximate 95% simultaneous sampling intervals; grid whiskers are marginal 95% intervals. Targets and practical-resolution bands are distinct from uncertainty. These intervals exclude deterministic finite-grid and burn-in error. The saved native panel width is 3.20 inches with text at least 10 points; scaling below 95% would fall below the intended 9.5-point floor.

The supplied plotting scripts retain the original study-directory assumptions. They are provenance source, not an adapted public renderer command. Their saved manifests link the three CSV inputs to 32 single-page vector PDFs; the original QA records embedded TrueType fonts, no raster layers and page-boundary checks. That standalone-figure QA does not certify manuscript inclusions or current manuscript typography. Full orchestration reproduction requires the original layout or an explicitly reviewed path adaptation.

## Compile the current manuscript

From `manuscript/`, with the declared TeX prerequisites:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Use a scratch copy when preserving release-file hashes. The current manuscript is the newly compiled 40-page figure/layout revision, following a clean 41-page V2 baseline. The older PDF supplied inside the V2 ZIP is no longer the current manuscript. `docs/manifests/CURRENT_MANUSCRIPT_SYNC.json` records version `20261018_FIGURE_LAYOUT`. The authoring build and audit are retained under `docs/figure_audit/layout_20261018/`; consult `docs/VALIDATION_RECEIPT.md` for the separate public-layout build and replay checks actually executed.

The generated `main.bbl` accompanies the current compiled manuscript, and `references.bib` is unchanged. The BibTeX step above regenerates it for a new build. A successful compile by itself does not establish a fresh dependency installation, new scientific audit or a full experiment replay.

## Current audit and historical receipts

`docs/figure_audit/layout_20261018/` contains `BASELINE_BUILD_REPORT.json`, `BUILD_REPORT.json`, the current QA JSON/Markdown records and `BEFORE_AFTER.pdf`. The archived final font audit applies to the exact current PDF hash given above: all nine active inclusions retain embedded vector text at least 9 TeX points, including actual LaTeX placement scaling. It covers Figures 1–5 on pages 11, 12, 15, 16 and 32. The numerical audit records all nine sidecars as unchanged, and the source guard records preservation of tables and scientific content outside the permitted presentation edits.

These are evidence from the completed figure/layout task. Its standalone source-guard and baseline scripts can require the original authoring workspace, so they are not presented as portable release commands. The public render/compare commands above and the current validation receipt define the release recheck route.

`docs/figure_audit/` retains the earlier seven-panel receipts: 2,737 independent numerical checks, the 33-page manuscript/four-page gallery build, 14 audited inclusions with minimum effective font about 9.70 TeX points, isolated replay, and the narrower 2,646-check portable numerical audit. These counts and typography conclusions apply only to that earlier version. Do not run the historical font auditor and interpret its seven-panel scope as coverage of the current manuscript.

Retained E4/E5 and targeted transcription receipts are under `manuscript/revision_audit/targeted_mechanism_20261015/`; their dates and declared checks distinguish that integration evidence from the current layout audit and public validation. Numeric preservation establishes correspondence to saved evidence, not theorem correctness, stationarity or target inclusion. Full raw-batch reanalysis remains a separate archival workflow.
