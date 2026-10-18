# Presentation-only integration QA

Scope: concise Introduction/Discussion; main coefficient/E5 tables; removal
of duplicate numerical presentation from Appendix C.

- 309 preservation/relocation/layout checks passed.
- 1,507 existing saved-value checks passed (221,919 scalar comparisons).
- No new training, bootstrap, coefficient fitting, full proof audit or batch
  reconstruction was performed.
- 36 pages; main 17, references 2, appendices 17.
- No undefined references, duplicate active labels, LaTeX errors or box warnings.
- Nine active panels unchanged; minimum final figure text 9.663758 PDF pt.
- Fresh extracted-package build and PDF render comparison are reported in
  `package_rebuild_check.json`.

`audit_presentation_executed.py` requires the old and revised source directories:

```sh
python audit_presentation_executed.py --before OLD/manuscript --after NEW/manuscript
```

For final-manuscript-only validation, use `tools/check_saved_e4_e5.py`.
