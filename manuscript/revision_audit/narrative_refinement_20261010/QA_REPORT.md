# Narrative refinement QA

## Preservation

27 preservation/source/compile checks passed. The JSON and CSV files record
actual comparisons, not inferences from successful compilation.

- Four appendix sources unchanged byte-for-byte.
- Setting, macros, bibliography, build script and compiled bibliography unchanged.
- 2 theorem / 1 corollary / 1 proposition / 4 lemma / 5 proof environments identical.
- 67 equation / 8 align / 21 unnumbered display-math blocks identical.
- 14 tables and 5 figure environments identical; 9 active independent vector panels.
- All 129 supplementary-result files and all 32 figure-directory files identical.
- Numerical-section inline math containing numeric data identical as multisets.
- No active label duplication or unresolved source reference.

## Saved-value consistency

The existing bundled `tools/check_saved_e4_e5.py` was rerun, with 1,507 checks,
221,919 scalar comparisons, zero failures and maximum absolute difference
1.7208456881689926e-15. This is not a new independent statistical audit and does
not reconstruct unsupplied full batch/trajectory data.

## Layout and compilation

`sh build.sh` succeeded. The final main.log has no warnings/errors, undefined
references, duplicate labels, or overfull/underfull boxes. The PDF has 37 pages:
16 main-text, 2 references, 19 appendix. All pages were rendered; contact sheets
and the changed front/results/discussion pages were visually inspected.
The affine-shift proposition has an external samepage wrapper; its statement
and equation are unchanged. No font-size or margin reduction was used.

All nine panel sources have minimum text sizes >=9 PDF pt, with a minimum of
9.663758277893066. Final placement retains native widths (only the existing
~1.00002 TeX unit-rounding factor on half-width panels); their sizes did not shrink.

## Scope

No new simulation, resampling, proof audit, external-source verification or claim
of publisher-template compliance. Previous scientific uncertainty remains.

A separately extracted final package is rebuilt and compared in
`package_rebuild_check.json`.
