# Integration QA — 10 October 2026

## Scope

This is a manuscript integration and saved-data consistency audit. No new training,
optimizer fitting, bootstrap resampling, external-literature audit or complete
proof audit was performed.

## Verified

- Input ZIP embedded PDF and separately uploaded PDF are byte-identical; 33 pages.
- Updated manuscript: 37 pages (body 1–16, references 17–18, appendices 19–37).
- Source bibliography, macros, Related Work, Setting, Main Results, Mechanism,
  and Appendices A/B are byte-identical to the supplied active project.
- All 12 original table environments are byte-identical. Original figure assets
  and data remain unchanged; two independently rendered E4 vector panels are added.
- 147 original active labels retained; 155 total, no duplicate active labels.
- Equation reference style checked after removing comments.
- Main compilation: no LaTeX warnings/errors, undefined citations/references,
  multiply defined labels or overfull/underfull boxes.
- All 37 pages rendered and visually checked; changed figures/tables inspected
  at full page size. No text outside the page boundaries.
- Final-size figure font minimum: original panels 9.66 PDF pt; E4 panels 9.86 pt.
- 1,508 numerical checks (409,407 scalar comparisons), zero failures; maximum
  absolute recomputation difference 1.73e-15 or less. Includes reconstruction
  of all 1,512 E4 averaged models from original batch sums.

## Preserved evidence boundaries

E4's unmet temporal/crossover criteria, two unpooled diagnostic pilots, small
absolute objective differences and absence of predictive harm remain explicit.
E5 retains all cells/windows, systematic magnitude overprediction and the
H-ratio discrepancy; it remains an appendix-only descriptive comparison.
Historical H=4/H=8 and long-horizon H=1 diagnostics are not reclassified.

## Records

`preservation_checks.json`, `label_checks.json`, `compile_and_layout.json`,
`point_estimate_checks.json`, `figure_font_audit.csv`, `manuscript_changes.diff`,
and the compilation logs record this integration. Package re-extraction and
render-equality tests are recorded in `package_rebuild_check.json`.

These checks establish internal consistency and reproducible typesetting, not
stationarity, theorem validity on real data, public code availability, or journal
acceptance.
