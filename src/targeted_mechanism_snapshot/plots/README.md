# Targeted mechanism figures

`plot_mechanism_checks.py` reads the frozen protocol and the analysis CSVs without changing or refitting them. It produces eight primary vector-PDF panels and 24 supplementary grid panels. Each PDF contains exactly one axes; LaTeX can arrange independent panels side by side.

The eight main panels comprise the three symmetric covariance interventions for each observable and coordinate (six panels), and the covariance-matched noise-law contrast for both coordinates (two panels containing all three observables). They show both the full grid and the prespecified omission of the largest step size. The signed covariance contrasts and all four condition-specific fitted intercepts remain available numerically in the analysis CSVs. All 24 balance-grid panels are generated in `supplementary/`; no panels are chosen by target inclusion.

Run from `.` using the environment's Python 3.12:

```powershell
& 'python' 'targeted_closure_20261014/plots/plot_mechanism_checks.py'
```

Required real inputs are `results/primary_family_36.csv`, `results/intercepts_and_contrasts.csv` and `results/full_grid.csv`. Missing/incomplete inputs or inconsistent duplicated values cause failure before final plotting. The script validates all 36 primary summaries and the 24 configured cells, with 12 independent paired runs per cell.

For a layout-only run:

```powershell
& 'python' 'targeted_closure_20261014/plots/plot_mechanism_checks.py' --mock-layout
```

This writes synthetic fixtures exclusively beneath `scratch/`, stamps every panel `MOCK LAYOUT`, and marks its manifest as mock. These files are not experimental results and should be excluded from the deliverable package. `scratch/final_qa/` similarly contains PNG previews only; final paper assets are vector PDFs.

Text is at least 10 pt at the native panel width of 3.20 inches. Keep panels at their native width, or at least 95% of that width (3.04 inches), to retain text at least 9.5 pt. Fonts are embedded as TrueType; no rasterized plotting layers are used. Each export runs a text-boundary check. Captions and file/input hashes are written to `FIGURE_CAPTIONS.md` and `FIGURE_MANIFEST.json` by the final run.

Main-panel whiskers are the CSV's approximate 95% simultaneous sampling intervals, assessed separately for the full and restricted grid analyses. Grid-panel whiskers are ordinary 95% marginal Student-t intervals and are identified as such in captions. These intervals exclude burn-in and deterministic finite-grid error. Resolution bands are practical coefficient scales from the frozen protocol, not equivalence proofs or stationarity certificates.
