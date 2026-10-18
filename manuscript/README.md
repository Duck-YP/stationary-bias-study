# SCAFFOLD — current manuscript

**Version: 18 October 2026 — V2 with final figure and layout revision.**

The current `main.pdf` is a clean **40-page** build of the current source:
18 pages of main text, 2 pages of references and 20 pages of appendices.
SHA-256: `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`.
It replaces the older PDF supplied inside the V2 archive.

All five figures (nine vector panels), their captions and float placement have
been revised for clarity. Scientific text, theorems, proofs, coefficient formulas,
numerical values, uncertainty intervals and all 23 table environments remain
unchanged by that revision. No experiment, fitting or resampling was performed.

## Build

Use pdfLaTeX and BibTeX with the declared TeX packages and Latin Modern fonts.
From this directory:

```sh
sh build.sh
```

Equivalent PowerShell commands:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -no-shell-escape main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -no-shell-escape main.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -no-shell-escape main.tex
```

`main.tex` is the entry point; `main.bbl` and the compiled `main.pdf` are included.
On Overleaf upload this directory's contents and select `main.tex`.
Build in a scratch copy to preserve the distributed file hashes.

## Figure sources and checks

- `tools/figure_layout/redraw_figures.py` and `figure_style.py` render Figures 1, 2, 3 and 5 from ten frozen CSV files.
- `tools/plot_e4_for_manuscript.py` renders Figure 4 from `supplementary_results/E4/BIAS_VARIANCE_MSE.csv`.
- [Figure provenance](FIGURE_PROVENANCE.md) maps panels to saved inputs, columns, fit coefficients, intervals and commands.
- [Figure/layout changelog](FIGURE_LAYOUT_CHANGELOG.md) records placement, page comparisons and numerical-preservation checks.

The seven-panel input directory is external to this manuscript folder. In the
local research workspace it is `figure_redraws/20261009/pipeline`; in the public
export it is `artifacts/canonical_paper_export/figure_redraw` relative to the
export root. The public workflow is documented in `../docs/FIGURE_REPRODUCTION.md`.
Never substitute values reconstructed from screenshots.

## Saved-data checks

From this directory, with the Python dependencies installed:

```powershell
python -B tools/check_targeted_table_transcription.py --out ../targeted_transcription.json
python -B tools/check_saved_e4_e5.py --out ../saved_e4_e5.json
```

The integrated E4/E5 evidence and targeted mechanism results retain their
existing scope and unfavorable or precision-insufficient results. Earlier
revision notes and audit receipts are historical; their page counts and figure
styles do not describe this new PDF. Source snapshots preserve provenance and
may require their original layouts for full production or restart workflows.

## Public export note

This export follows the 2026-10-18 final figure/layout revision of V2.
The included 40-page main.pdf is the clean compiled current source; main.bbl is its generated bibliography.
This public copy omits `SOURCE_REVIEW.zip` and machine-local `RUN_COMMANDS.md`;
source-review snapshots are provided unpacked under
`supplementary_results/source_review_snapshot/`. Metadata-only path variants
and omissions are listed in `../docs/manifests/`. Scientific TeX, numerical
results and estimators are unchanged; the E4 pilot manifest has portable path strings.
Targeted evidence is unpacked under `../artifacts/canonical_paper_export/targeted_mechanism/`
and its source snapshot under `../src/targeted_mechanism_snapshot/`. These snapshots
preserve provenance and may require the original study layout for execution.
Use `../docs/FIGURE_REPRODUCTION.md` for supported public commands.
