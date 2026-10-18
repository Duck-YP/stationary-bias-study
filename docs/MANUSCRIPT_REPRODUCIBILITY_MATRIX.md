# Manuscript reproducibility matrix

This matrix refers to the finalized 40-page manuscript, SHA-256 `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`. Its active graph has **five numbered figures, nine PDF panels and 22 numbered tables**. A 23rd table environment belongs to an unused appendix and has no active number or page.

The paths, routes and commands defined below form part of every record that cites them. A route supplies the exact implementation/configuration/seed paths; the exhibit row supplies its canonical saved inputs, output and validation. This avoids conflating a portable renderer with the historical scientific implementation.

The executed [canonical table coverage](../artifacts/canonical_paper_export/tables/coverage.json) and [table validation receipt](../artifacts/canonical_paper_export/tables/VALIDATION_RECEIPT.json) report `PASS_WITH_DISCLOSED_GAPS`: 21 active data exports, 17 supported tables, four partial tables, one noncomputational table and one inactive archival table. All 453 decimal cells in the fourteen fully covered decimal-result tables match the displayed values. These counts do not turn the partial metadata or Table 18 entries into complete reproductions.

## Status and execution levels

- **Supported (artifact):** the named saved-data export is implemented without simulation, refitting or resampling. Execution outcomes are recorded separately in the [validation receipt](VALIDATION_RECEIPT.md).
- **Supported (bounded):** a small implementation/identity check is executable; it does not reproduce stationary coefficient precision.
- **Partial:** named fields or historical inputs are missing, or a displayed value is not exactly recovered. Available exports and unfavorable results are retained.
- **Archival-only:** retained source/results establish lineage, but the complete original execution is not a portable public workflow.
- **Missing:** required evidence is absent and has no supported substitute. Individual missing fields are listed even when the enclosing exhibit is partial.

Full-study reproduction remains partial across the original, supplementary and targeted campaigns because the compact checkout omits original raw/batch/restart inputs. No artifact or bounded status below should be read as a full-study reproduction claim. See [Data and archives](DATA_AND_ARCHIVES.md).

## Exact path prefixes and public commands

All paths are repository-relative. The following prefixes expand literally; filenames written after a prefix are exact files, not glob patterns.

| Prefix | Exact directory |
| --- | --- |
| `P2/` | `artifacts/canonical_paper_export/original/p2_multidimensional_validation/artifacts/formal/` |
| `P3/` | `artifacts/canonical_paper_export/original/p3_multidimensional_fedavg_attribution/artifacts/formal/` |
| `SUP/` | `artifacts/canonical_paper_export/supplementary/` |
| `TM/` | `artifacts/canonical_paper_export/targeted_mechanism/` |
| `MS/` | `manuscript/supplementary_results/` |
| `AVG/` | `manuscript/supplementary_results/E4/` |
| `VEC/` | `manuscript/supplementary_results/E5/` |
| `FIG/` | `artifacts/canonical_paper_export/figure_redraw/inputs/` |
| `OUT/` | `manuscript/figures/redrawn/` |
| `C2/` | `configs/original/p2_multidimensional_validation/configs/` |
| `C3/` | `configs/original/p3_multidimensional_fedavg_attribution/configs/` |
| `S2/` | `src/stationary_bias/workstreams/p2_multidimensional_validation/` |
| `S3/` | `src/stationary_bias/workstreams/p3_multidimensional_fedavg_attribution/` |

Commands run from an installed checkout. Scratch destinations must be new or empty; table and figure generation preserve repository artifacts.

| Command ID | Exact command and scope |
| --- | --- |
| **F** | `python -B scripts/regenerate_paper_figures.py --output ../paper-replay/figures` |
| **FC** | `python -B scripts/compare_figure_replay.py --group all --replay ../paper-replay/figures --output ../paper-replay/figure-comparison.json` |
| **T** | `python -B scripts/regenerate_paper_tables.py --output ../paper-replay/tables` |
| **B** | `python -B scripts/run_representative_example.py --output ../paper-replay/example.json` |
| **S** | `python -B manuscript/tools/check_saved_e4_e5.py --out ../paper-replay/saved-array-checks.json` |
| **I** | `python -B scripts/validate_release.py` |
| **P** | `python -B -m pytest -q -p no:cacheprovider` |

T produces `table_NN.csv`, `table_NN.md` and `table_NN.tex` for Tables 2–22, plus `coverage.json`, `coverage.csv` and `VALIDATION_RECEIPT.json`. These are data exports, not replacements for the manuscript's table layout. Table builders never read displayed TeX values as input; TeX is used only in the independent display-comparison step.

## Scientific implementation, configurations and seed routes

| Route | Exact scientific implementation | Frozen configuration and input/seed paths |
| --- | --- | --- |
| **H — historical coefficients** | `S2/objective.py`, `noise.py`, `algorithm.py`, `simulation.py`, `theory.py`, `formal_analysis.py`, `plateau_analysis.py`; `S3/algorithm.py`, `simulation.py`, `paired_algorithm.py`, `matched_simulation.py`, `theory.py`, `formal_analysis.py`, `matched_formal_analysis.py`, `matched_diagnostic.py` | `C2/d2_coefficient_primary.yaml`, `d2_h4_small_step_confirmation.yaml`, `d2_fixed_gamma_largeN_plateau.yaml`, `d5_controlled_validation.yaml`; `C3/d2_coefficient_primary.yaml`, `d2_h4_small_step_confirmation.yaml`, `d2_matched_attribution_primary.yaml`, `d2_matched_attribution_h4_small_step.yaml`, `d2_matched_attribution_h4_diagnostic.yaml`. Each contains the original grid/chains/seed/inference design; matching `configs/original/.../artifacts/formal/` snapshots are retained. Saved run summaries retain realized seed labels. Raw batch/bootstrap files listed in omission manifests are not inputs to artifact replay. |
| **C — independent Cartesian grid** | `src/study/model.py`, `kernels.py`, `engine.py`, `accuracy.py`, `analysis.py` | `configs/supplementary/PROTOCOL_FROZEN.json`: controlled cells, production seeds 20001–20012, pilot seeds 10001–10004, primary/extended schedules and inference specifications. `SUP/per_run_estimates.csv` and `full_results.csv` retain saved run-level results. Four freeze-time analysis/CLI/test/runner files are unavailable; later delivered versions are identified. |
| **M — targeted mechanism** | `src/targeted_mechanism_snapshot/targeted/model.py`, `kernels.py`, `workflow.py`, `tests.py` | `TM/PROTOCOL_FROZEN.json`: all 24 cells, production seeds, covariance/noise conditions, schedules and primary family; `TM/PILOT_DESIGN.json` and certificates preserve pilot/design choices. `TM/results/per_run_vectors.csv`, `window_summaries.csv` and `run_summaries/production/` preserve compact run evidence. The reference and compiled kernels are separate from the older hardcoded controlled kernel. |
| **R — logistic allocations** | `src/study/data.py`, `model.py`, `kernels.py`, `protocol.py`, `analysis.py` | `configs/supplementary/PROTOCOL_FROZEN.json`: all real-data cells, N/m/H/gamma, partitions and production seeds. `SUP/DATA_MANIFEST.json` identifies a9a bytes and subset seed 20261009; partition seeds are 4101–4103. `SUP/reference_optimizers.npz`, `optimizer_certificates.json`, `per_run_estimates.csv` and partition tables are compact inputs. Full raw data/partition matrices are external, as documented in the archive register. |
| **A — temporal averaging** | `AVG/source_snapshot/replay.py`, `freeze.py`, `pilot_analysis.py`, `v2.py`; portable checker `manuscript/tools/check_saved_e4_e5.py` | `AVG/E4_v1_PROTOCOL_FROZEN.json`, `E4_v2_PROTOCOL_FROZEN.json`, `STATISTICAL_METHOD_RECEIPT.json`; the first specifies nine shared-objective cells, twelve paired seeds and seven windows. Saved `models.npz`, `inference_arrays.npz`, `WINDOW_RESULTS.csv` and `BIAS_VARIANCE_MSE.csv` support the public checks. The two later pilots and unexecuted proposed extension are separate. |
| **V — vector proxy** | `VEC/source_snapshot/bridge.py`, `prepare.py`, `reports.py`; portable checker `manuscript/tools/check_saved_e4_e5.py` | `VEC/E5_POSTHOC_ANALYSIS_SPEC.json`, `STATISTICAL_METHOD_RECEIPT.json`, `INPUT_SHA256.csv`; paired seeds/windows derive from route A. `VEC/VECTORS.npz`, `PAIRED_SEED_RESULTS.csv` and the saved summaries are canonical evidence. No proxy direction/amplitude is fit to observed means. |
| **X — structural identities** | `S2/rotation.py`, `theory.py`; `src/study/checks.py`, `kernels.py`; targeted kernels in route M | `C2/d2_rotation_invariance.yaml`; `SUP/tables/E2_exact_checks.csv` and `E2_zero_initialization.csv`. The rotation YAML records initialization/noise coupling; some affine prose-level settings are absent from the structured summary (Table 19 gap below). Bounded fixtures/seeds and maximum work are explicit in `scripts/representative_checks.py`. |
| **G — final presentation** | `scripts/regenerate_paper_figures.py`, `manuscript/tools/figure_layout/redraw_figures.py`, `figure_style.py`, `manuscript/tools/plot_e4_for_manuscript.py` | No simulation seeds are consumed. The saved inputs and fixed selectors below determine all values; renderer constants preserve the final dimensions, fonts, labels, line patterns and axes. |
| **D — table data export** | `scripts/regenerate_paper_tables.py`; `scripts/table_regeneration/historical_tables.py`, `recent_tables.py`, `config_tables.py`, `catalog.py` | No simulation or bootstrap seeds are consumed. Historical seeds/configurations are supplied by H/C/M/R/A/V/X. `coverage.json` records exact sources/selectors and `VALIDATION_RECEIPT.json` hashes every actual input. |

For historical rows, specify the relevant H configuration by the study name in the canonical path: primary, smaller-step, fixed-step, five-dimensional, matched-primary, matched-smaller-step, or matched diagnostic. The pairing is explicit in the following six-file fit inventory used by Tables 2 and 11.

| Fit ID | Exact canonical input | Exact configuration |
| --- | --- | --- |
| **HS-P** | `P2/p2-d2-coefficient-primary/fit_summary.csv` | `C2/d2_coefficient_primary.yaml` |
| **HS-S** | `P2/p2-d2-h4-small-step-confirmation/fit_summary.csv` | `C2/d2_h4_small_step_confirmation.yaml` |
| **HF-P** | `P3/p3-d2-coefficient-primary/fit_summary.csv` | `C3/d2_coefficient_primary.yaml` |
| **HF-S** | `P3/p3-d2-h4-small-step-confirmation/fit_summary.csv` | `C3/d2_h4_small_step_confirmation.yaml` |
| **HD-P** | `P3/p3-d2-matched-attribution-primary/paired_fit_summary.csv` | `C3/d2_matched_attribution_primary.yaml` |
| **HD-S** | `P3/p3-d2-matched-attribution-h4-small-step-confirmation/paired_fit_summary.csv` | `C3/d2_matched_attribution_h4_small_step.yaml` |

## Numbered figures

Each named panel below expands to `OUT/<name>.pdf`, its PNG, and `OUT/data/<name>.csv`. Figure-source hashes and selected columns are detailed in [Figure provenance](FIGURE_PROVENANCE.md). All figure routes use F, FC and I.

| Manuscript location | Scientific purpose | Source/config/seed route | Canonical inputs and output panels | Validation | Status |
| --- | --- | --- | --- | --- | --- |
| Figure 1, Section 6.2.2, p.11; `fig:num-matched-primary` | Matched control coefficient on H=2 and H=4 primary grids | H (HD-P) + G | `FIG/p3_primary/paired_setting_summary.csv`, `paired_fit_summary.csv`; panels `hist_matched_H2`, `hist_matched_H4` | All point/intercept intervals, saved beta0/beta1 and targets; sidecar/hash/geometry and rendered comparison | Supported (artifact) |
| Figure 2, Section 6.2.3, p.12; `fig:E-p2-plateau` | Client-count dependence at fixed step size | H, `C2/d2_fixed_gamma_largeN_plateau.yaml` + G | `FIG/p2_plateau/setting_summary.csv`, `plateau_fit_summary.csv`, `plateau_fit_curve.csv`; panels `hist_fixed_gamma_coord1`, `hist_fixed_gamma_coord2` | Saved normalized remainder, target, fixed-step offset and intercept/point intervals; FC | Supported (artifact) |
| Figure 3, Section 6.3, p.15; `fig:real-allocation` | Fixed total minibatch budget across three allocations | R + G | `FIG/supplement/E3_allocation_signed_projection.csv`; panel `real_R0_allocation` | All six shared-objective H=4 allocation rows, signed projection/nominal interval multiplied by 1000; FC | Supported (artifact) |
| Figure 4, Section 6.4, p.16; `fig:e4-averaging` | Temporal squared mean displacement versus variance | A + G | `AVG/BIAS_VARIANCE_MSE.csv`; panels `e4_averaging_scaffold`, `e4_averaging_fedavg` | Seven windows, 28 U/V points, 56 interval endpoints; symlog/negative/cross-zero preservation; FC and S | Supported (artifact) |
| Figure 5, Appendix C.2.2, p.32; `fig:E-control-h4` | Smaller-step H=4 and all nine residual observations | H (HD-S and `C3/d2_matched_attribution_h4_diagnostic.yaml`) + G | `FIG/p3_smallstep/paired_setting_summary.csv`, `paired_fit_summary.csv`; `FIG/p3_diagnostic/pointwise_diagnostics.csv`, `scaling_summary.csv`; panels `hist_H4_smallstep`, `hist_H4_loglog_residual` | Saved smaller-step fit/intervals, all residual points, absolute-value display, log axes; no new slope fit; FC | Supported (artifact) |

The publication replay returned `PASS_RENDER_EQUIVALENT` for all nine panels in the recorded fresh environment. Numerical sidecars and PNGs are byte-identical; PDF operators, font records, page boxes and rendered pixels at 216 dpi agree. PDF bytes differ because of metadata. This is artifact evidence, not a rerun of the scientific campaigns.

## Numbered tables

For each row, D identifies the exact regeneration implementation; the additional route supplies the scientific source, frozen configurations and original input/seed paths. T writes the corresponding `table_NN` exports. I/P check canonical integrity. “Decimal comparison” means an exact multiset comparison of generated decimal strings with the displayed TeX body, supplemented by fixed source selectors; it alone is not a proof of row association.

| Table, section, page and label | Purpose | Source/config/seed routes | Exact canonical inputs | Regeneration and validation | Status |
| --- | --- | --- | --- | --- | --- |
| 1; Section 2, p.3; `tab:prior-bias-resolution` | Compare prior analytical resolution | `manuscript/sections/02_related_work.tex`, `manuscript/references.bib`; no experimental configuration or seed | Those manuscript sources and cited papers | T catalogs this exhibit but does not generate it. Analytical/source review, not a numeric computation | Archival-only; noncomputational |
| 2; Section 6.2.1, p.11; `tab:num-attribution-summary` | Analytical vectors and fitted finite-grid intercepts | H + D (`historical_tables.py`) | All six HS-P/HS-S/HF-P/HF-S/HD-P/HD-S inputs | T; saved-target/intercept selection, repeated-fit equality, seven-decimal comparison | Supported (artifact) |
| 3; Section 6.2.5, p.13; `tab:supp-control` | Independent Cartesian-grid matched coefficients at H=2,4,8 | C + D (`historical_tables.py`) | `SUP/fitted_coefficients.csv`, experiment E1b, primary window, term 0, both coordinates | T; stored estimates/targets/nominal intervals, eight-decimal comparison | Supported (artifact) |
| 4; Section 6.2.7, p.14; `tab:mechanism-controls` | Contraction null, signed controls and law contrast, matched first coordinate | M + D (`recent_tables.py`) | `TM/results/primary_family_36.csv`, `TM/PROTOCOL_FROZEN.json` | T; five fixed balance/full-grid selections, saved simultaneous intervals, decimal comparison | Supported (artifact) |
| 5; Section 6.3, p.15; `tab:supp-policy` | Step-size and local-step policies at fixed allocation | R + D (`historical_tables.py`) | `SUP/full_results.csv`, shared-objective N=32 policy rows | T; saved projection/raw-variance scaling by 1000, decimal comparison | Supported (artifact) |
| 6; Section 6.5, p.17; `tab:e5-bridge` | Full-vector directional alignment at longest window | V + D (`recent_tables.py`) | `VEC/FULL_VECTOR_ALIGNMENT.csv`, `E5_POSTHOC_ANALYSIS_SPEC.json` | T and S; all six nonzero-proxy cells at saved primary K, six-decimal comparison | Supported (artifact) |
| 7; Appendix C.1.1, p.28; `tab:num-controlled-settings` | Controlled design sizes, grids and replication | H/C/M + D (`config_tables.py`) | Four C2 design YAMLs listed under H; `configs/supplementary/PROTOCOL_FROZEN.json`; `MS/fitted_coefficients.csv`; `TM/PROTOCOL_FROZEN.json`, `certificate/independent_model_checks.json` | T; seven normalized numerical design records; source fields, exact reciprocal step sizes and explicit counts | Supported (artifact metadata) |
| 8; Appendix C.1.2, p.29; `tab:num-run-schedules` | Burn-in and measurement/batch schedules | H/C/M/A + D (`config_tables.py`) | Four C2 design YAMLs; supplementary and targeted frozen protocols; `TM/certificate/independent_model_checks.json`; `AVG/E4_v1_PROTOCOL_FROZEN.json` | T; actual saved cell schedules and planned historical min/max policy; gaps below | Partial |
| 9; Appendix C.1.2, p.30; `tab:num-inference` | Methods, multiplicity and confidence families | H/C/M/R/A/V + D (`config_tables.py`) | `C2/d2_coefficient_primary.yaml`, `d5_controlled_validation.yaml`; supplementary/targeted protocols; `MS/tables/E1_intercept_contrasts.csv`, `E3_policy_allocation_contrasts.csv`; AVG/VEC statistical receipts, AVG v1 protocol and VEC post-hoc specification | T; method metadata, family sizes, saved contrast counts and run-derived degrees of freedom; no CI recomputation | Supported (artifact metadata) |
| 10; Appendix C.1.4, p.30; `tab:num-noise-laws` | Exact scalar noise supports, probabilities and moments | M + D (`recent_tables.py`) | `TM/certificate/independent_model_checks.json` | T; exact rational marginalization at rho=0, symbolic third/fourth moments; B checks finite-support centeredness/covariance | Supported (artifact/bounded) |
| 11; Appendix C.2.1, p.31; `tab:num-core` | Joint-grid simultaneous intervals | H + D (`historical_tables.py`) | Same six fit inputs as Table 2 | T; stored simultaneous endpoints, seven/ten-decimal comparison; no bootstrap run | Supported (artifact) |
| 12; Appendix C.2.2, p.32; `tab:E-h4diag` | H=4 residual scale and saved log–log slope | H, matched diagnostic config + D (`historical_tables.py`) | `P3/p3-d2-matched-attribution-h4-diagnostic/scaling_summary.csv` | T; saved residual extrema/scaled ranges/slopes, decimal comparison; no new slope fit | Supported (artifact) |
| 13; Appendix C.2.3, p.32; `tab:E-plateau` | Fixed-step extrapolated intervals and offsets | H, fixed-step config + D (`historical_tables.py`) | `P2/p2-d2-fixed-gamma-largeN-plateau/plateau_fit_summary.csv` | T; stored endpoints and beta0-minus-target, decimal comparison | Supported (artifact) |
| 14; Appendix C.2.3, p.33; `tab:E-d5` | Five-dimensional coefficients under noncommuting curvature/noise | H, `C2/d5_controlled_validation.yaml` + D (`historical_tables.py`) | `P2/p2-d5-controlled-validation/fit_summary.csv` | T; all five coordinates and H=2,4, repeated-fit equality, ten-decimal comparison | Supported (artifact) |
| 15; Appendix C.2.4, p.33; `tab:supp-leading` | Shared leading coefficient and H=1 boundary | C + D (`historical_tables.py`) | `SUP/fitted_coefficients.csv`, E1a/primary/term 0, both algorithms, H=1,2,4,8 | T; stored nominal intervals/estimates, six-decimal comparison | Supported (artifact) |
| 16; Appendix C.2.5, p.34; `tab:mechanism-complement` | Individual coefficients/contrasts and paired second coordinate | M + D (`recent_tables.py`) | `TM/results/primary_family_36.csv`, `TM/PROTOCOL_FROZEN.json` | T; 17 display rows from 29 fixed scalar selections, scaling by 1000, decimal comparison | Supported (artifact) |
| 17; Appendix C.2.5, p.35; `tab:num-restricted-mechanism` | Prespecified largest-step omission sensitivity | M + D (`recent_tables.py`) | `TM/results/intercepts_and_contrasts.csv` | T; three fixed balance/omit-largest-gamma/coordinate-1 selections; retain exclusions and decimal-compare | Supported (artifact) |
| 18; Appendix C.3.1, p.35; `tab:E-direct-balance` | Four historical direct–balance discrepancies | H, FedAvg primary config + D (`historical_tables.py`) | `P3/p3-d2-coefficient-primary/run_summary.csv` | T; join both estimators by run/coordinate, compute absolute saved-mean difference; source seeds retained; missing thresholds and one formatting discrepancy below | Partial |
| 19; Appendix C.3.2, p.36; `tab:num-structural-settings` | Rotation/affine settings and coupling | X + D (`config_tables.py`) | `C2/d2_rotation_invariance.yaml`, `MS/tables/E2_exact_checks.csv` | T; rotation metadata plus 24 affine-check records and distinct settings; affine metadata gaps below | Partial |
| 20; Appendix C.4.1, p.37; `tab:num-real-settings` | Data, allocations, windows, horizons and pilots | R/A + D (`config_tables.py`) | `MS/DATA_MANIFEST.json`, supplementary protocol, `AVG/E4_v1_PROTOCOL_FROZEN.json`, `E4_v2_PROTOCOL_FROZEN.json` | T; saved data/seed/cell/window metadata and explicit horizon/evaluation counts; prose-level gaps below | Partial |
| 21; Appendix C.4.1, p.38; `tab:supp-real-full` | Shared/IID/label-skew allocation errors and loss | R + D (`historical_tables.py`) | `SUP/full_results.csv`, all allocation-role cells at H=4 and base step | T; nominal projection intervals, raw MSE and held-out loss; decimal comparison; no replacement by adjusted intervals | Supported (artifact) |
| 22; Appendix C.4.3, p.39; `tab:e4-primary` | Longest-window MSE, training loss, test loss and paired contrasts | A + D (`recent_tables.py`) | `AVG/BIAS_VARIANCE_MSE.csv`, `E4_v1_PROTOCOL_FROZEN.json` | T and S; designated primary cell/max K, saved individual and genuinely paired simultaneous fields, decimal comparison | Supported (artifact) |
| No active number/page; unused Appendix D; `tab:F-artifacts` | Historical artifact map | `manuscript/appendix/D_reproducibility.tex`; no new config/seed | Retained inactive source only | T catalogs it as inactive; no numerical export or active-paper coverage claim | Archival-only; inactive |

### Disclosed table gaps

**Table 8:** the export retains actual tau/tau0, burn-in, batch lengths and counts where stored, including primary versus extended batches. Supplementary/targeted ceiling formulas are not structured formula fields. Historical YAML min/max batch policies do not by themselves establish every run's realized stopping batch.

**Table 18:** the original per-run combined-SE thresholds for all four reported discrepancies are absent from the saved compact summary; the exported threshold cells are `UNAVAILABLE`. No uncertainty is recomputed and no manuscript threshold is copied back into data. For H=4, N=16, coordinate 2, the saved balance coefficient is -0.10802366831450083, which rounds to -0.1080237 at seven decimals; the manuscript displays -0.1080240. The difference from the raw saved value is approximately 3.31685e-7. A six-decimal intermediate display followed by a trailing zero could explain it, but no recovered formatting record establishes that history. This discrepancy is retained for author attention; neither paper nor source value is changed.

**Table 19:** rotation metadata is complete. The affine CSV records 24 checks and their N/H/rho/round settings, but lacks gamma and structured fields for the offset construction, translated initialization and matched-noise semantics. Those concepts are inspectable in source/theory and exercised by bounded checks; they are not regenerated as CSV metadata.

**Table 20:** saved data dimensions/preprocessing, cell allocations, seed sets, windows, horizon/evaluation counts and later pilot schedules are exported. The selected protocols do not encode the sampling-with-replacement rule or the L_sample/base-step formula as structured fields (actual gamma is saved). Regime IDs alone do not reconstruct label conversion, equal-client weighting, IID/two-shard construction, or the prose distinction between primary and alternative partitions. The implementation and [data register](DATA_AND_ARCHIVES.md) document these separately.

Fourteen decimal result tables are checked against their displayed decimal strings. Table 10 is an exact symbolic certificate export; Tables 7 and 9 are source-backed metadata exports. Protocol metadata completeness is distinct from literal equality of prose/LaTeX layout. The generated `coverage.json` and `VALIDATION_RECEIPT.json` are the machine-readable coverage authority.

## Important numerical and structural claims beyond table cells

| Manuscript location and claim | Purpose | Implementation/config/input-seed route | Canonical saved output | Verification and status |
| --- | --- | --- | --- | --- |
| Sections 4–5, 6.2.1–6.2.2: shared leading term and matched second-order difference | Check numerical formulas and matched attribution, without treating simulation as proof | H/C; `S2/theory.py`, `S3/theory.py`; fixed bounded fixtures in `scripts/representative_checks.py` | Six fit inputs above; `SUP/fitted_coefficients.csv` | B/P test Lyapunov/tensor/coefficient identities; T/F expose saved finite-grid evidence. Supported (bounded/artifact); theorem proof remains in the manuscript |
| Section 6.2.4 and Appendix C.3.2: noncommuting 5D model and orthogonal equivariance | Verify dimension/noncommutation and coordinate transformations | H/X; 5D and rotation YAMLs | `P2/p2-d5-controlled-validation/fit_summary.csv`; `P2/p2-d2-rotation-invariance/theory_rotation_summary.csv`, `rotation_residual_summary.csv`, `pair_summary.csv` | B/P independent algebra/path transformation; T14 and I saved records. Supported (bounded/artifact); full rotation campaign archival-only |
| Sections 6.2.5 and C.2.4: H=2,4,8 behavior, leading coefficient and restricted-grid differences | Preserve local-step dependence and deviations | C; frozen primary/extended windows | `SUP/fitted_coefficients.csv`, `tables/E1_intercept_contrasts.csv`, `per_run_estimates.csv` | T3/T15 and I; source inspection for the original fit. Supported saved evidence; full statistical replay partial |
| Sections 4.5, 6.2.6 and C.3.3: affine objective/control translation | Verify identical translated updates with matched noise | X; `src/study/checks.py`, `kernels.py`; bounded fixtures | `SUP/tables/E2_exact_checks.csv`, `E2_zero_initialization.csv` | B/P translated paths/control sums and saved checks. Supported (bounded/artifact); Table 19 metadata remains partial |
| Sections 6.2.7 and C.1.4: nontrivial contraction null and matched covariance laws | Exclude quadratic/trivial cancellation; check exact centeredness/covariance and coefficients | M; separate model/reference/compiled kernels and frozen law conditions | `TM/certificate/independent_model_checks.json`, `independent_kernel_checks.json`, `results/primary_family_36.csv` | B/P exact finite supports, covariance, contraction and kernel equivalence; T4/T10/T16. Supported (bounded/artifact); no production rerun |
| Appendix C.2.5: resolution bands, individual precision and restricted-grid/second-coordinate exclusions | Retain all prespecified primary/sensitivity conclusions | M; same frozen 36-scalar family and restricted grid | `TM/results/primary_family_36.csv`, `intercepts_and_contrasts.csv`, `fit_diagnostics.csv`, `temporal_diagnostics.csv` | T4/T16/T17 and I. Supported saved evidence; confidence intervals are frozen, not re-estimated |
| Appendix C.3.1: historical H=4 estimator/window audit | Distinguish balance identities from unavailable boundary/noise information | C plus `TM/historical_audit/audit_existing_h4.py`; original archived batches identified by input hashes | `TM/historical_audit/historical_fit_replay.csv`, `reconstruction_checks.csv`, `finite_window_identity.csv`, `window_endpoints.csv`, `AUDIT_SUMMARY.json` | I/hash inspection, bounded finite-window identity via B/P. Partial archival replay: missing starting states and individual noise statistics prevent every original identity |
| Section 6.3 and Appendix C.4.1–C.4.2: fixed budget, IID/label-skew and run-length sensitivity | Preserve conditional finite-tail interpretation across partitions and lengths | R; partition/production seeds in frozen protocol | `SUP/full_results.csv`, `tables/E3_conditional_partition_estimates.csv`, `E3_across_partition_sensitivity.csv`, `E3_policy_allocation_contrasts.csv`; `AVG/pilots/PILOT_TEMPORAL_DIAGNOSTICS.csv` | F3/T5/T21, I and saved diagnostic inspection. Supported artifact summaries; complete raw-data/training replay partial |
| Section 6.4 and Appendix C.4.3: finite-window error decomposition, negative U and component shares | Verify algebra without requiring stationarity | A; same twelve paired seeds and seven overlapping windows | `AVG/models.npz`, `inference_arrays.npz`, `BIAS_VARIANCE_MSE.csv`, `PRACTICAL_IMPLICATIONS.csv`, `TEMPORAL_DIAGNOSTICS.csv`, `AUTOCORRELATION_PROXIES.csv` | S reconstructs saved-array quantities; F4/T22 preserve simultaneous intervals; I. Supported (artifact/algebra); no stationarity or certified crossover claim |
| Section 6.5 and Appendix C.4.4: full-vector proxy, alternative directions and temporal sensitivity | Check directional agreement independently of fitting the proxy | V/A; post-hoc specification and saved paired seeds | `VEC/VECTORS.npz`, `FULL_VECTOR_ALIGNMENT.csv`, `ALL_CELLS_ALL_WINDOWS.csv`, `NEGATIVE_CONTROLS.csv`, `EARLY_LATE_PAIRED_DIAGNOSTICS.csv`, `PAIRED_BOOTSTRAP_SENSITIVITY.csv` | S/T6/I; all nonzero-proxy configurations retained, H=1 zero-proxy metrics remain undefined. Supported (artifact/algebra); no prefactor identification |

The separate targeted evidence directory also contains 32 auxiliary PDFs with original plotting sources/manifests. They are archival supporting evidence and are not additional numbered manuscript figures. Their original plotting scripts assume the historical layout; F deliberately regenerates the nine active manuscript panels.

## Integrity and interpretation

`docs/SOURCE_MANIFEST.csv` and the copy/variant/omission manifests hash the public files. T records exact input hashes, source code hashes, saved-row selectors and export hashes; FC compares all nine panels. Imported historical receipts retain their original scope and are distinguished from the current publication execution receipt.

The compact export keeps historical H=4 differences, H=8 deviations, individual precision limitations, negative corrected U and unfavorable sensitivities. No route selects configurations by target inclusion. Missing data are disclosed rather than reconstructed, and no result table or scientific manuscript content is changed by this matrix.
