# Figure provenance

The final manuscript contains five numbered figures and nine vector PDF panels. They are the finalized 18 October 2026 presentation of unchanged saved numerical results. The authoritative manuscript SHA-256 is `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c` (40 pages).

## Single public regeneration route

```sh
python -B scripts/regenerate_paper_figures.py --output ../paper-replay/figures
python -B scripts/compare_figure_replay.py --group all --replay ../paper-replay/figures --output ../paper-replay/figure-comparison.json
```

Run from the installed repository root, with TeX, T1/Latin Modern fonts and `dvipng` available. Use a new scratch output directory. The wrapper invokes the preserved renderers with portable inputs and collects all nine panels; it does not run fitting, bootstrap resampling or simulation. See [Figure reproduction](FIGURE_REPRODUCTION.md) for lower-level routes and scratch manuscript compilation.

## Panel map

All canonical panel paths below are under `manuscript/figures/redrawn/`. Every basename has a PDF, PNG and `data/<basename>.csv` sidecar. Page numbers refer to the exact manuscript hash above. `inputs/` abbreviates `artifacts/canonical_paper_export/figure_redraw/inputs/`.

| Figure and page | Output basename | Exact source files | Renderer |
| --- | --- | --- | --- |
| 1(a), p.11 | `hist_matched_H2` | `inputs/p3_primary/paired_setting_summary.csv`, `paired_fit_summary.csv` | `manuscript/tools/figure_layout/redraw_figures.py` |
| 1(b), p.11 | `hist_matched_H4` | Same two primary CSVs | Same |
| 2(a), p.12 | `hist_fixed_gamma_coord1` | `inputs/p2_plateau/setting_summary.csv`, `plateau_fit_summary.csv`, `plateau_fit_curve.csv` | Same |
| 2(b), p.12 | `hist_fixed_gamma_coord2` | Same three fixed-step CSVs | Same |
| 3, p.15 | `real_R0_allocation` | `inputs/supplement/E3_allocation_signed_projection.csv` | Same |
| 4(a), p.16 | `e4_averaging_scaffold` | `manuscript/supplementary_results/E4/BIAS_VARIANCE_MSE.csv` | `manuscript/tools/plot_e4_for_manuscript.py` through the wrapper |
| 4(b), p.16 | `e4_averaging_fedavg` | Same temporal-averaging CSV | Same |
| 5(a), p.32 | `hist_H4_smallstep` | `inputs/p3_smallstep/paired_setting_summary.csv`, `paired_fit_summary.csv` | `manuscript/tools/figure_layout/redraw_figures.py` |
| 5(b), p.32 | `hist_H4_loglog_residual` | `inputs/p3_diagnostic/pointwise_diagnostics.csv`, `scaling_summary.csv` | Same |

The wrapper invokes the renderer and `figure_style.py` under `manuscript/tools/figure_layout/`. Byte-identical copies are retained under `scripts/figure_redraw/` for the lower-level historical command.

## Saved quantities and permitted display transformations

- **Figure 1:** select H=2 or H=4, both coordinates, all five saved points. Read `delta`, `D_mean`, `simultaneous_ci_low/high`. Plot saved `beta0 + beta1 * delta`, open-diamond intercepts at zero and saved intercept intervals; horizontal targets are `B20_ctrl_component`. Grid-point and intercept intervals retain their distinct saved Student-t/bootstrap procedures.
- **Figure 2:** select `estimator=stationary_mean_balance` and each coordinate, retaining all five points. Read `inverse_N`, `C_mean`, and saved simultaneous intervals. Use the saved fit curve and `beta0` at zero; the joint-limit target is `B20_component`. The ordinate subtracts the shared leading contribution and divides by the squared step size. Fixed-step offsets are not reinterpreted as exact joint-limit coefficients.
- **Figure 3:** select the shared-objective allocation rows (`regime=R0`, `roles` containing `allocation`, H=4, gamma=0.1/0.51). Retain both algorithms at (N,m)=(8,32),(32,8),(128,2). Multiply `signed_projection` and nominal `ci_lower/ci_upper` by 1000. Category offsets -0.045/+0.045 separate markers only. There is no fit or theoretical line.
- **Figure 4:** select `cell_id=E3_R0_p0_H4_N128_g0.196078431373`, separating SCAFFOLD/FedAvg. Retain K=1,2,4,8,16,32,64 and saved U/V values with `U_lower_simultaneous`, `U_upper_simultaneous`, `V_lower_simultaneous`, `V_upper_simultaneous`. Both panels use log-base-2 x and symmetric-log y, with linear threshold 1e-5, linear scale 0.75 and y limits [-5.5e-5,5e-4]. Negative corrected U and intervals crossing zero remain. Lines connect saved values; there is no new fit.
- **Figure 5(a):** retain all four smaller-step points per coordinate at H=4; the saved points, fits, targets and intercept intervals use the same columns as Figure 1.
- **Figure 5(b):** retain all nine points per coordinate. Plot `delta` against `abs(e_Delta)` on log–log axes. Lines connect residual observations. Saved scaling-summary coefficients remain unchanged and are not used to add a new fitted trend.

The historical seven sidecars contain 124 records; temporal averaging adds 14 rows, representing 28 plotted U/V points and 56 interval endpoints. No displayed quantity comes from PDF digitization. Colors, markers, line patterns, labels, final dimensions and symlog settings are fixed by the supplied renderers.

## Integrity evidence

Exact input hashes and row provenance are in `manuscript/figures/redrawn/data/provenance.json`, `e4_provenance.json`, and [the manuscript's detailed provenance](../manuscript/FIGURE_PROVENANCE.md). The release [source manifest](SOURCE_MANIFEST.csv) covers current scripts, inputs and outputs.

The completed layout audit in `docs/figure_audit/layout_20261018/` records all nine sidecars unchanged from the clean source baseline, 2,646 saved-input checks, 226 numerical revision checks, 190 historical-panel artist checks, and final-PDF vector/font inspection. These are imported layout-task receipts.

The separate publication replay in a fresh environment returned `PASS_RENDER_EQUIVALENT` for all nine panels: PNGs and numerical sidecars were byte-identical, and PDF operators, fonts, page boxes and rendered pixels at 216 dpi agreed. PDF bytes differed because of metadata. The [publication validation receipt](VALIDATION_RECEIPT.md) records the executed commands and environment.

Final figures use embedded text and vector paths. Renderer/PDF metadata and TeX subset prefixes may prevent PDF byte identity across environments; the comparison reports saved-record, geometry and rendered agreement separately. Fidelity to saved results does not establish stationary mixing, target inclusion or theorem correctness.

The additional 32 targeted mechanism evidence PDFs are auxiliary evidence, not numbered manuscript figures. Their original plotting source and manifests remain in `artifacts/canonical_paper_export/targeted_mechanism/plots/`; their historical production-layout assumptions are documented in the reproduction scope.
