# Independent Scientific Data-Mapping Audit

## Scope and Status

This is a presentation-only independent audit. The original plotting source,
saved CSVs, active root input graph, and existing figure content were inspected.
No experiment, fitting procedure, bootstrap, sampling window, or diagnostic
calculation was executed. The numerical sidecar and protected-source verifier is
`verify_numerical_preservation.py`; its executed results are reported separately
in `NUMERICAL_AUDIT_SUMMARY.json` and
`NUMERICAL_PRESERVATION_INDEPENDENT.csv`. This document alone does not assert
that final PDF typography, rendering, or all numerical records passed.

## Active Manuscript Identity

The baseline entry point is `figure_redraws/20261009/baseline/main.tex`, not a
backup manuscript. Its uncommented graph contains four active figure
environments with seven scientific panels. The `fig:E-control-h4` and
`fig:E-h4diag` labels intentionally identify one shared figure.

The following existing assets are companions, not active inclusions:
`E1_leading_intercepts.pdf`, `E1_control_kappa.pdf`, and the full
`E3_allocation_signed_projection.pdf`. They must not be substituted for the
historical matched panels. Historical H=4 exclusions and independent
supplementary H=4 results belong to different saved designs.

## Required Content by Panel

| Panel | Authoritative selection | Required scientific content |
|---|---|---|
| `hist_matched_H2` | Primary H=2, both saved coordinates | Ten observed settings, simultaneous setting intervals, two targets, saved linear coefficients and two intercept intervals |
| `hist_matched_H4` | Primary H=4, both saved coordinates | Ten observed settings, simultaneous setting intervals, two targets, saved linear coefficients and two intercept intervals; both target exclusions retained |
| `hist_fixed_gamma_coord1` | `stationary_mean_balance`, code coordinate 0 | Five estimates and simultaneous intervals, saved fit curve, intercept and simultaneous interval, asymptotic reference |
| `hist_fixed_gamma_coord2` | `stationary_mean_balance`, code coordinate 1 | Same selection and content; display coordinate 2, not code coordinate 1 |
| `real_R0_allocation` | R0 allocation, H=4, frozen base step, three saved (N,m) pairs | Exactly six estimates, two algorithms per allocation; nominal signed-projection intervals |
| `hist_H4_smallstep` | Historical smaller-step H=4, both coordinates | Eight observed settings, simultaneous setting intervals, saved linear fit/intercepts and targets; both target exclusions retained |
| `hist_H4_loglog_residual` | All combined saved diagnostic rows | Eighteen points: nine positive delta values per coordinate, ordinate `abs(e_Delta)`; no newly fitted trend, confidence band, or delta=0 substitute |

The original matched primary/smaller-step plotting function drew observed
paths, point intervals, and reference lines but did not draw fit intercepts.
The baseline captions nevertheless refer to fitted intercepts. The requested
redraw makes those saved fit/intercept records visible; it does not estimate
new coefficients. Pointwise-setting and bootstrap-intercept intervals remain
different recorded procedures and must not be interchanged.

The original fixed-gamma plotting source used the saved coefficients for its
linear line, plotted its extrapolated intercept interval, and showed a theory
reference. The saved `plateau_fit_curve.csv` has five values per coordinate,
not a confidence band. A band would require unsupported new numerical data and
is therefore not introduced. At fixed gamma, the reference is not a certified
exact finite-step, infinite-client limit.

The original log-log source used only delta and the absolute saved residual.
`scaling_summary.csv` is protected diagnostic evidence, not authorization to
introduce a new fitted slope line or fitting window.

## Historical H=4 Outcomes Are Unchanged

| Grid | Code coordinate | Saved intercept | Saved simultaneous interval | Saved target | Target covered |
|---|---:|---:|---|---:|---|
| Primary | 0 | -0.05432376684741969 | [-0.05444276803060828, -0.054182565652720206] | -0.0560046857944086 | No |
| Primary | 1 | -0.0676943194701779 | [-0.06783815969917076, -0.06752160761140037] | -0.0700058572430108 | No |
| Smaller-step | 0 | -0.05592615920351892 | [-0.05595023319840869, -0.055900743658430195] | -0.0560046857944086 | No |
| Smaller-step | 1 | -0.06989565753216591 | [-0.06992560322740032, -0.0698639209002024] | -0.0700058572430108 | No |

These are read from saved fit CSVs, not rounded manuscript tables. Their target
exclusions must remain even if the intervals are visually short at the
publication scale. No estimate or interval is moved for target inclusion.

## R0 Interpretation and Exact Transform

R0 replicates a common empirical objective and is not a disjoint private-client
deployment. Its ordinate is a finite-tail signed mean displacement along the
frozen projection direction, not a bias norm, MSE, predictive error, or certified
stationary mean. The plot uses the stored nominal `ci_lower`/`ci_upper`; the
adjusted endpoint contrasts reported in prose belong to a separate family.

The frozen allocation pairs are (8,32), (32,8), and (128,2), with N*m=256.
The original CSV serializes gamma as `0.196078431372549`, so the verifier uses
a 1e-15 selection tolerance relative to the frozen base value
`0.19607843137254902`; this tolerates only serialization, not another step size.
Exactly multiplying all signed estimates and interval endpoints by 1000 is
permitted and must be explicitly labeled. Categorical x positions 0,1,2 are
not estimates of a continuous interpolation law; algorithm jitter is only a
fixed presentation offset.

## Independent Verifier Design

The verifier independently selects original full-CSV row ordinals, not the
renderer-selected rows. It checks point completeness, coordinate 0->display 1
and 1->display 2, estimator selection, saved fit coefficients, exact curve
vertices, original CI endpoints, targets, and source hashes. Numeric comparisons
use round-trip Python float conversion of the authoritative CSV strings.
Display values must equal the exact declared transform; inversion allows at
most one source-value ULP for binary multiplication/division.

Original saved CSV/JSON/YAML/NPZ files are hash-protected, together with active
scientific TeX and ordered manuscript table environments. The two edited
figure-bearing TeX files are also compared after removing only their figure
environments. A passing audit does not certify theorem correctness or replace
the final manuscript PDF font/visual audit.

## Portable Recheck

The independent verifier also supports an extracted handoff without the old
experiment workspace. Use `--input-root` (alias `--source-input-root`) for the
directory containing the ten bundled `inputs/` CSVs, `--manuscript` for the
revised LaTeX project, and `--output` for a new audit-report directory. This
mode independently reselects all seven panel records and verifies input hashes
against `provenance.json`; when the original hash manifest is bundled beside
the verifier, it also checks the ten input hashes against that archived receipt.

Portable mode explicitly reports
`ARCHIVED_RECEIPT_NOT_REEXECUTED` for preservation of the broader 95-file original
workspace and protected proof/manuscript sources. Those broader checks require
the original workspace and are not misrepresented as having been rerun from
only the lightweight plotting inputs. No original capture manifest is reset by
a portable execution.
