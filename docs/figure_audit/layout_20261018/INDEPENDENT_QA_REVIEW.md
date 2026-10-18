# Independent figures and layout QA

**Final result: PASS.** The final checks were rerun after copying the compiled PDF and bibliography back to the master manuscript. Audited master: `manuscript/main.pdf`, SHA-256 `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`, 40 pages. It is byte-identical to `figure_layout_revision_20261018/final/manuscript/main.pdf`. This report applies to that exact PDF; a later change requires the final font check and changed-page inspection again.

The comparison baseline is the cleanly compiled **41-page V2 source**, SHA-256 `9b005005254f025caee170df75bd3efc95b188fd519cf217aca548b23673ead0`. The PDF supplied inside V2 was an older 40-page PDF and is not used as a visual or page-count baseline.

## Numerical and source preservation — PASS

- All nine plotted CSV sidecars are byte-identical to the clean baseline: 124 historical records and 14 E4 rows. These include observations, saved confidence endpoints, targets, fitted intercepts, saved fit vertices and coefficients, and display transformations.
- The earlier independent historical verifier was rerun against the ten frozen input CSVs: **2,646 checks, no failures**. Its code is identified by hash in `NUMERIC_INVARIANCE.json`; the complete detailed report is under `historical_authority/`.
- The independent revision checks add **226 checks**, including exact old/new records and every E4 saved column against `BIAS_VARIANCE_MSE.csv`. All pass. Negative corrected E4 estimates and all zero-crossing intervals are retained.
- **190 actual-artist geometry checks pass**: all seven historical panels' displayed observations, fits, targets and interval endpoints agree with their immutable sidecars. All data/errorbar vertices remain strictly inside the axes. The categorical R0 marker displacement remains exactly the existing ±0.045 display offset.
- The final source guard checks the original **1,705-file registry**: 1,682 files are byte-identical, and all 23 changed files are explicitly permitted presentation files (including the regenerated master PDF). All 23 complete table environments are unchanged. Theorems, proofs, formula sources and scientific text outside figure environments are unchanged, allowing only comments, explicit page/float barriers and the documented numerical-section float parameters. All 1,435 registered release files remain unchanged. The master `main.bbl` remains byte-identical to its baseline.
- Both revised plotters were read as source. They continue to read saved data and saved coefficients; no new regression, resampling, simulation or uncertainty calculation was performed for this audit. The diagnostic log–log panel connects the saved residual observations; its existing fitted slope values remain in the unchanged table rather than a newly introduced trend.

## PDF and visual checks — PASS for the final master

| Panels | Candidate page | Minimum effective embedded font |
|---|---:|---:|
| Matched H=2/H=4 | 11 | 9.70019 TeX pt |
| Fixed-step coordinates 1/2 | 12 | 9.70019 TeX pt |
| R0 allocation | 15 | 9.70000 TeX pt |
| E4 SCAFFOLD/FedAvg | 16 | 10.00020 TeX pt |
| Small-step and log–log diagnostic | 32 | 9.70019 TeX pt |

The font measurement uses PDF text operators and their full transformation matrices, including rotation and figure-inclusion scaling; it is not inferred from plotting-library font settings. All nine inclusions retain their source text, embedded fonts and vector drawing paths. No raster images were found inside the nine PDF assets. All text and vector path bounds, including stroke padding, remain within the figure canvases. Internal errorbar bounds are checked separately against axes limits. `FINAL_DOCUMENT_PDFFONTS.txt` independently records the final document's embedded vector fonts.

All nine color PNG previews and `ALL_NINE_PANELS_GRAYSCALE.png` were visually inspected. Filled circles/open squares, fitted-intercept diamonds, dotted fitted curves and dashed reference lines remain distinguishable. The E4 panels retain their shared symmetric-log scale, their complete negative interval portions and the FedAvg negative K=1 estimate.

The four whole-document contact sheets cover every page 1–40. The five figure-containing pages (11, 12, 15, 16, 32) were also inspected individually. No clipping or figure/caption overlap was observed. Figures 1, 2 and 5 remain connected to the relevant discussion or diagnostic tables. Figure 4's caption correctly states the symmetric-log linear interval. The figure-caption edits describe the existing estimands and saved uncertainty procedures consistently with the unchanged scientific text.

This visual inspection assesses presentation; it does not newly validate the scientific claims. The document remains `article[11pt]`, with nominal normal-text size 10.95 TeX pt. Measured ordinary caption labels range from 10.74196 to 10.95001 TeX pt under the conservative minimum-matrix-scale metric (horizontal microtype expansion accounts for the small difference). Mathematical superscripts/subscripts in manuscript captions and surrounding text follow the existing LaTeX script sizes and can be smaller than 9 pt. The ≥9 pt result above includes every glyph inside each plotted panel, including its mathematical labels; it is not a claim that the entire manuscript's math scripts exceed 9 pt.

## Build comparison

Both baseline and audited candidate build reports have zero overfull boxes, unresolved references and duplicate labels. Their only listed warning is the same `epstopdf` warning that shell escape is disabled. No new build warning was identified. No missing graphics were observed in the rendered pages.

## Reproduction

From the workspace root, using the bundled Python runtime:

```text
python figure_layout_revision_20261018/qa/independent_revision_checks.py --phase baseline
python figure_layout_revision_20261018/qa/independent_revision_checks.py --phase final
python figure_layout_revision_20261018/qa/audit_vector_bounds.py
python figure_layout_revision_20261018/qa/make_grayscale_contact.py
```

All audit outputs are written below `figure_layout_revision_20261018/qa/`. No master manuscript, release, experiment result or simulation source is modified by these checks. The JSON reports retain hashes, individual checks and scope limitations.
