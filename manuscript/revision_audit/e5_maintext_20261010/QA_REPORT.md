# Current revision QA — E5 main-text integration

- Baseline manuscript: `SCAFFOLD_Final_E4_E5_20261010.zip`.
- PDF: 38 pages; 17 main-text, 2 reference, 19 appendix pages.
- Complete pdfLaTeX/BibTeX/pdfLaTeX build: success.
- Undefined references, duplicate active labels, LaTeX warning/error lines,
  overfull/underfull boxes: none in the final build log.
- Equation references retain `Equation~\eqref{...}` conventions.
- The existing E5 proxy equation and label were relocated unchanged to Section 6.8.
- Nine protected theory/model/bibliography files remain byte-identical.
- All 14 existing tables, all 32 figure-directory files and all 129
  supplementary-result files remain unchanged.
- Nine active panels retain their PDF files, native widths, placement widths,
  and font sizes; minimum final-size font is approximately 9.66 PDF pt.
- Saved-value checker rerun: 1,507 checks, 221,919 scalar values compared,
  0 failures. No new training, resampling, or batch reconstruction.
- Added E5 summary ranges and H ratio were checked directly against frozen CSVs.
- Final PDF was rendered at 100 dpi with the PDF skill renderer; all-page
  contact sheets and full-size key pages were checked for layout.
- Two inherited malformed cross-references were repaired and recorded.

`verification_script_used.py` records the analysis-time checks and requires
both the baseline and revised directories at the paths declared in that script.
It is a provenance record, not an independently packaged experiment runner.
`tools/check_saved_e4_e5.py` is the portable saved-record checker supplied in
the manuscript project.

This is an editorial, preservation and compilation check, not a new mathematical
proof audit or empirical stationarity certification. Historical E4/E5 source
reports remain unchanged, including the earlier appendix-first recommendation.
