# Text-only readability revision — 2026-10-12

Base: `SCAFFOLD_Main_Appendix_Deduplicated_20261012.zip` (36-page PDF).
New: `SCAFFOLD_Text_Readability_20261012.zip` (37-page PDF).

## Changes made (text only)

1. **Introduction:** Distinguishes within-round client averaging from across-round temporal averaging, before explaining stationary mean and error shares.
2. **Section 6.1:** Explains why subtracting the shared leading term and normalizing by `gamma^2` yields a finite-grid intercept estimator of the joint-limit coefficient.
3. **Section 6.2:** Provides a reader-facing comparison of the two controlled designs: joint `gamma=1/N` paths versus independently implemented Cartesian-grid / leading-coefficient checks. Table 2's caption now describes the grid design rather than calling it historical.
4. **Section 6.3:** Defines `x_ref` and `Sigma_ref` at the outset, identifies the precommitted projection `v` with the normalized reference curvature–noise direction, and explicitly distinguishes across-run estimation from the actual averaged-model output.
5. **Section 6.4 (E4):** Defines the per-run time-averaged output `Y_{r,K}`, gives the exact finite-window parameter-MSE bias–variance identity (independent of a stationarity assumption), distinguishes averaged-model variance from checkpoint variance, and explains why the corrected `U_hat` can be negative.
6. **Section 6.5 (E5):** Uses the prior reference definitions, makes clear the precommitted projection shares the curvature–noise direction, and aligns the prose with **Table 5's projection ratio** (0.716–0.938) and relative residual (0.089–0.291), rather than introducing a separate norm-ratio range. Observed norm overprediction and the `H=4/H=2` discrepancy are retained.
7. **Appendix C.11:** Redirects `Y_{r,K}` reference from Section 6.5 to its new definition in Section 6.4.

## Scope and preservation

- Existing equations, proofs, theoretical claims, algorithm definitions, experimental point estimates, CIs, E4/E5 diagnostics, and historic exceptions remain unchanged; one explanatory exact MSE identity was **added** in E4.
- All **21** graphics files under `manuscript/figures/` (PNG/PDF) are bitwise identical to the base ZIP. No figure redraw was performed.
- Tables, figure floats, caption text and layout controls were not intentionally changed; reflow naturally shifted pagination from 36 to 37 pages.
- `Appendix A/B`, setting/main-results/mechanism source, bibliography and macros are bitwise unchanged.
- Text edits are limited to these three `.tex` files: `sections/01_introduction.tex`, `sections/07_numerical_study.tex`, `appendix/C_numerical_details.tex`.

## Build verification

- Compiled successfully using unmodified `sh build.sh` (pdfLaTeX/BibTeX) from the package.
- PDF: 37 pages; no LaTeX warnings, undefined references, duplicated labels, or overfull/underfull boxes in the final compile log.
- The body introduction, two controlled-study descriptions, E4 identity, E5 metric explanation, and Appendix C.11 reference were checked in the rendered output.
- Figure/float placements are **not finalized**; they are intentionally reserved for a separate Codex figure-and-layout pass.

## Next figure/layout pass — draft acceptance criteria (not performed here)

- Redraw **every panel individually** and let LaTeX compose adjacent panels; all panels share a coherent visual format.
- Use at least **9 pt figure text in the final embedded PDF** (roughly 2 pt below this manuscript's nominal 11 pt body text); prefer 9.5–10 pt for tick labels and legends.
- Rename ambiguous labels such as `Saved fit`, `Matched difference`, `Normalized residual`, and `Squared mean (U)` so a reader sees the actual estimand directly.
- Do not split a short explanatory sentence or a definition with a float when a better page break is feasible. Avoid forcing every float to `[H]` or shrinking figure text.
- Keep estimator, CI and all historical result values fixed; verify plotted numeric values before/after.

## Compilation

Extract the ZIP and run `cd manuscript && sh build.sh` with pdfLaTeX and BibTeX available.
