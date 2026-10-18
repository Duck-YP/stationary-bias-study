# Public receipt context

The following is a recorded local compilation receipt.
Full baseline/build logs remain in the local handoff, not this compact
public tree. Baseline-specific recheck commands require that original
handoff; supported public commands are in `docs/FIGURE_REPRODUCTION.md`.

# LaTeX integration and compilation

## Manuscript identity

The root project is `main.tex` in the supplied integrated 9 October 2026
archive. Its active uncommented input graph contains 14 TeX files, four
figure environments and seven image panels. Backup roots are not active.
The fresh `manuscript/` directory contains that active project, all 63 compact
supplementary evidence files, three retained companion assets, the redraws,
and figure-only gallery/probe source. It contains no alternate historical
manuscript root or unrelated backup material.

## Targeted presentation changes

- Three original two-panel arrangements use independently generated vector
  PDFs in six `subfigure` blocks, at `0.49\textwidth` each.
- The R0 panel uses one independently generated PDF at `0.58\textwidth`.
- Six prose-only subcaptions use local `\small` formatting, measured as
  10 TeX points. Existing global macros remain byte-identical.
- Historical captions distinguish saved Student-t pointwise intervals from
  seed-block-bootstrap fitted-intercept intervals and identify saved fits.
- Historical H=4 exclusions are explicitly retained in the diagnostic caption.
- R0 caption records categorical allocation positions, within-allocation
  algorithm offsets, and exact multiplication by 1000 of values/endpoints.
  Its base-step symbol is expressed in prose in the caption to avoid a small
  mathematical subscript; the main text's definition/value is unchanged.
- Both parent labels intentionally referring to the historical H=4 figure
  remain attached to the same figure.

`LATEX_REVISION.diff` contains the complete readable source diff. All
non-figure text and all numerical tables in the two changed files are
verbatim. Main results, assumptions, proofs, abstract, bibliography and
other active scientific sections are SHA256-identical. The source checks
do not assert that every existing scientific claim is true; they establish
that this presentation revision has not changed those claims.

## Executed builds

Compiler: pdfTeX 3.141592653-2.6-1.40.26, TeX Live 2024 on Windows.

The baseline was compiled for three passes in `baseline_build/`, producing
31 pages. Its settled log has no undefined references, duplicate labels,
overfull/underfull boxes or LaTeX errors. It retains one original PDF-version
warning from the extracted R0 PDF (version 1.7 included into version 1.5).

The revision was compiled in `manuscript_build/`. BibTeX was then executed
against `references.bib`, followed by two settling pdfLaTeX passes. The
regenerated bibliography is exactly identical to the supplied bibliography.
The revised manuscript has 33 pages; the larger, legible standalone panels
were not shrunk to enforce the original page count. The figure-only gallery
was compiled for two passes in `gallery_build/` and has four pages.

Both final settled logs have zero warnings, undefined references,
duplicate labels, overfull/underfull boxes and errors. The earlier
PDF-version warning is removed because the newly drawn R0 PDF replaces
the original cropped asset. Complete logs and console output are retained.

An independent visual review found that an automatic locator could place
matched-panel ticks at half-millisteps while three-decimal labels rounded
them ambiguously. The plotting code's shared matched-panel locator was
corrected to use the saved formatting specification's 1/2/5/10 step family,
without changing any estimates, intervals, fits or targets. All seven panel
assets were regenerated, then the manuscript and gallery were recompiled
for two final settling passes each. Console logs named
`final_after_tick_correction_pass1.txt` and
`final_after_tick_correction_pass2.txt` record this final compilation.
The settled `main.log`, gallery log and validation hashes refer to these
latest corrected assets, not the earlier preview build.

## Measured typography

The actual manuscript macros give body size 10.95 TeX points and text width
452.9679 TeX points. The formal floor is body minus 2 = 8.95 TeX points;
the task enforces at least 9 TeX points. Paired insertion width is
221.95676 TeX points and single insertion width is 262.7222 TeX points.
Convert physical widths using 72.27 TeX points/inch and 72 PDF points/inch.
These source measurements are not by themselves a final font validation;
the assembled-PDF audit and visual inspection are supplied separately.

Final figure pages: 11 (primary matched), 12 (fixed step), 14 (R0),
27 (historical H=4, with both preserved alias labels).

## Recheck

```powershell
python verify_latex_revision.py --baseline ../baseline --manuscript ../../../manuscript --output .
```

Run from this QA directory. Use the documented bundled Python executable
if `python` is not on PATH. No experimental, training or bootstrap program
is called by this validation.
