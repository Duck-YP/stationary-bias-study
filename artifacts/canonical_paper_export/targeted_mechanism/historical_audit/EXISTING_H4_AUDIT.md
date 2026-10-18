# Existing H = 4 Cartesian-grid estimator and window audit

Analysis-only audit, 2026-10-14. Status: `DISCREPANCY_REQUIRES_AUDIT` for the interpretation of the finite-grid coefficient gap; data reconstruction is complete and no new old-objective production was run. This status does **not** identify a demonstrated kernel error or a theorem counterexample.

The nine configurations are the genuine Cartesian product N ∈ {32, 64, 128} and γ ∈ {1/128, 1/256, 1/512}, with 12 independent paired runs per configuration. This design is separate from the earlier γ = 1/N study. No exclusions in that earlier study were changed.

## What the available evidence establishes

All 108 original result files match the SHA256 references in the latest local manuscript's `per_run_estimates.csv`. Reconstructing the original first-64-batch balance and raw means reproduces the stored and manuscript vectors exactly. The three historical H = 4 Cartesian fits—full grid, omit largest γ, and omit N = 32—reproduce their published estimates, intervals and bootstrap limits to at most 1.39 × 10⁻¹⁷. There is no detected transcription, batch-selection, or fit-replay error in these outputs.

The common-noise algorithm difference is also consistent with the finite-window direct/balance algebra where both endpoints exist. Across 240 run/window pairs (480 scalar coordinate checks), the maximum residual in the equation is 7.69 × 10⁻¹⁶. Inverting B and dividing by γ² gives a maximum discrepancy of 1.29 × 10⁻⁸ on the normalized coefficient scale. This checks the available paired observables and their time alignment; it does **not** validate B20, establish stationarity, or explain a fitted-intercept discrepancy.

The original primary window lacks its starting endpoint, so its exact finite-window identity is **not reconstructible**. Individual-algorithm identities also lack the required fresh-noise η sums. Missing quantities were neither set to zero nor replaced by a checkpoint from a different time.

## Inputs, source integrity and timing

The authoritative inputs were `manuscript/supplementary_results/PROTOCOL_FROZEN.json`, its per-run and fitted-coefficient tables, and the original files under `supplementary_study/results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF/raw/production/`. `INPUT_SHA256.csv` records the exact paths and hashes.

The independently available `review_exports/20261009/AUDIT_BATCHES_E1.zip` contains compact re-exports. Its NPZ byte hashes intentionally differ from the originals: final per-client controls and per-client batch integrals were omitted, while labeled boundaries and derived paired differences were added. Every shared array of all 108 audited runs is bit-for-bit identical. `archive_array_integrity.csv` records this distinction; no shared-array discrepancy was found.

The embedded source archive's actual prefix is `SOURCE_REVIEW/`, with both `SOURCE_REVIEW/available_frozen_source/study/` and `SOURCE_REVIEW/supplementary_study/study/`. The matching frozen subset contains 8 of the 12 files named in the protocol. Frozen versions of `study/analysis.py`, `study/cli.py`, `study/tests.py`, and `run.py` are missing; the later available versions differ. The core frozen `kernels.py`, `model.py`, `data.py`, and `engine.py` match. This is an incomplete frozen snapshot, not a fully recovered historical tree. The manifest's legacy import label `7f6de2c` was not promoted to a historical supplementary-production commit.

The source confirms that `controlled_chunk` hardcodes the old logcosh objective, A = [[1.2, 0.2], [0.2, 1.0]], and α = 0.25. It stores each **post-round** global endpoint in `raw[t]`. The balance observation uses the nonlinear term evaluated at pre-local-update states. The engine stores each batch's final post-round state in `snapshot[batch]`; this is not a batch mean. No old kernel or output was edited or executed by this audit.

## Windows retained separately

All ranges below use zero-based batch indices, with the upper bound excluded.

| Window | Batch range | Availability | Starting endpoint |
|---|---:|---|---|
| Original primary | [0, 64) | All nine cells | Missing at burn end |
| First half | [0, 32) | All nine cells | Missing at burn end |
| Last half | [32, 64) | All nine cells | `snapshot[31]` |
| Endpoint-available diagnostic tail | [1, 64) | All nine cells | `snapshot[0]` |
| Original `2x_burn` | [5, 69) | N = 64, γ = 1/256 only | `snapshot[4]` |
| Original `2x_tail` | [0, 128) | Same representative cell only | Missing at burn end |
| Original `2x_burn_tail` | [5, 133) | Same representative cell only | `snapshot[4]` |

The endpoint-available tail is a newly labeled algebraic diagnostic, not a replacement primary or target-selected sensitivity. The historical representative cell has 133 retained batches; all its named windows are retained. It would be invalid to substitute its extended window into all nine cells or silently change a full-grid fit. First/last comparisons use equal 32-batch windows. No batch, round, coordinate, or overlapping window was counted as an independent seed.

`batch_sufficient_statistics.csv` retains counts, balance/raw sums and all endpoints for every available batch. `window_endpoints.csv` distinguishes missing starts from available endpoints. `per_run_windows.csv` contains both coordinates of raw post means, balance means, same-run raw-minus-balance differences, and matched algorithm differences. For windows with endpoints it additionally reconstructs the distinct pre-round means from mean_pre = mean_post − (x_end − x_start)/T.

## Direct/balance agreement and resolution

For each cell and window, raw-minus-balance differences were formed **within the same independent paired run**, then averaged and given a t interval. The paired algorithm observable uses (SCAFFOLD − FedAvg) from the same indexed noise stream. Separate algorithm SEs were never added as if these observations were independent.

The normalized estimands are Cᴬ = [bᴬ − (γ/N)B11]/γ² and D = (bˢ − bᶠ)/γ². B11 = (−0.02445942817, −0.03057428521). In the primary grid, the ordinary 95% CI widths for individual-algorithm raw C range from 4.66 to 94.13; balance C widths range from about 0.00165 to 0.02439. Broad raw intervals are therefore a precision limitation, not validation of the balance estimator. At N = 64, γ = 1/512, the individual raw-minus-balance gaps have positive nominal intervals in both coordinates; these are retained, not hidden behind a universal “agreement” claim. Coordinate 1 also excludes zero under a two-coordinate correction, while no grid-wide family claim is made. The corresponding paired algorithm gap is small because the leading fresh-noise variation cancels.

For D, the primary raw-minus-balance grid estimates range from −2.17 × 10⁻⁶ to 1.46 × 10⁻⁶, with interval widths from 1.26 × 10⁻⁶ to 8.23 × 10⁻⁶. All 18 paired gap intervals contain zero. This is substantially tighter than the individual raw comparisons, but the primary exact endpoint correction remains unavailable.

The paired identity was evaluated as

    B (mean_post(S − F) − mean(zS − zF))
      = −P^H [(xS_end − xF_end) − (xS_start − xF_start)] / T,

where P = I − γA and B = I − P^H. The independently reconstructed pre-round version is recorded separately, with −Δd/T on the right. The maximum historical control-sum norm is 9.94 × 10⁻¹². Every equation residual lies within the conservative possible nonzero-control contribution γ ||Σₕ Pʰ|| max||Σc ξc||/N. Historical accumulated round-recursion residuals were not stored, so their exact attribution cannot be reconstructed. Agreement at this scale is an arithmetic and alignment check, not a stationary or coefficient certificate.

## Historical intercepts and inference sensitivity

The descriptive design remains (1, γ, 1/N). It is not an exact model for an asymptotic remainder. The following are the original balance-D intercepts and original nominal seed-label t intervals; no point or window was selected to obtain inclusion.

| Grid | Coordinate | Estimate | Original nominal 95% CI | Target |
|---|---:|---:|---:|---:|
| Full primary | 1 | −0.05595226 | [−0.05601109, −0.05589342] | −0.05600469 |
| Full primary | 2 | −0.06993656 | [−0.07000999, −0.06986314] | −0.07000586 |
| Omit largest γ | 1 | −0.05595512 | [−0.05603562, −0.05587463] | −0.05600469 |
| Omit largest γ | 2 | −0.06994197 | [−0.07004249, −0.06984145] | −0.07000586 |
| Omit N = 32 | 1 | −0.05597227 | [−0.05605420, −0.05589033] | −0.05600469 |
| Omit N = 32 | 2 | −0.06996213 | [−0.07006439, −0.06985987] | −0.07000586 |

The raw-D full-grid intercepts are (−0.05595250, −0.06993685). Fitting the **same-run raw-minus-balance differences** gives intercept gaps −2.39 × 10⁻⁷ [−9.64 × 10⁻⁷, 4.86 × 10⁻⁷] and −2.92 × 10⁻⁷ [−1.38 × 10⁻⁶, 7.96 × 10⁻⁷]. Thus estimator substitution would not remove the paired fitted-intercept displacement observed here.

Across configurations, the SHA256 noise key includes the cell ID. Coincident numeric seed labels do not imply common random numbers across cells. For exact historical reproduction, the original simultaneous seed-label resampling is retained. As a separately labeled audit sensitivity, a 2,000-draw bootstrap independently resamples each cell while keeping its complete paired-run vector, coordinates, estimators and windows together. An independent-cell variance calculation with Welch–Satterthwaite degrees of freedom is also supplied; it never treats the two algorithms as independent.

This sensitivity matters near the target boundary. For the full balance-D fit, independent-cell nominal t intervals are [−0.05600446, −0.05590005] and [−0.07000171, −0.06987142], just excluding the two targets; the corresponding six-coordinate Bonferroni intervals include them. The original percentile-bootstrap intervals also just exclude both targets, whereas the original t intervals include them. The independent-cell percentile intervals are [−0.05599906, −0.05590645] and [−0.06999499, −0.06987941]. These are approximate small-sample sampling intervals and do not include deterministic finite-grid error. All variants appear in `fitted_coefficients.csv`; the original inference is not replaced.

This is a small finite-grid displacement whose “target inclusion” answer depends on the interval and window. It is not justified to state that the discrepancy **must** be a finite-grid effect. The audit narrows the candidates by eliminating a material paired raw/balance mismatch on the available windows; it leaves model remainder, precision, inferential sensitivity and unobserved burn-in effects distinct.

## Temporal diagnostics

All 18 primary-grid balance-D first/last-half difference intervals include zero. Their widths range from approximately 9.77 × 10⁻⁵ to 5.38 × 10⁻⁴. That does not establish stationarity.

At the representative cell, the original named-window minus primary normalized D contrasts are:

| Window contrast | Coordinate 1 estimate [95% CI] | Coordinate 2 estimate [95% CI] |
|---|---:|---:|
| `2x_burn` − primary | 1.32e−6 [−1.74e−5, 2.01e−5] | 1.65e−6 [−2.18e−5, 2.51e−5] |
| `2x_tail` − primary | −8.19e−7 [−3.63e−5, 3.46e−5] | −1.02e−6 [−4.53e−5, 4.32e−5] |
| `2x_burn_tail` − primary | 5.87e−6 [−3.49e−5, 4.66e−5] | 7.33e−6 [−4.36e−5, 5.82e−5] |

Full-grid balance-D intercepts using the first half are (−0.05597062, −0.06995948), and using the last half are (−0.05593389, −0.06991364). Both are retained as temporal diagnostics. These differences and the original named sensitivities neither prove nor refute stationarity; a missing starting endpoint cannot be recovered from non-significance.

## Remaining questions and scope limits

1. The original primary and double-tail windows have no stored burn-end startpoint. Their exact paired identity cannot be closed from the available outputs.
2. Individual-algorithm finite-window identities lack η summaries. Large raw noise cannot be set to zero just because its expectation is zero.
3. Exact historical accumulated recursion and pre-round control-mean integrals are unavailable. The small observed paired residuals are consistent with the recorded control drift bound, but a full round-by-round arithmetic attribution is not possible.
4. Sampling precision and deterministic finite-grid remainder are different uncertainties. This audit supplies neither a remainder constant nor a mixing bound, and does not force a conclusion about the small target displacement.
5. Four files in the original frozen source tree remain unavailable. The validated numerical core and output hashes do not license inventing a historical commit.

No old-objective production, new historical pilot, optimizer solve, manuscript change, or GitHub push was performed. All configurations, both coordinates, all original named sensitivities, raw disagreements and target-excluding interval variants were retained.

## Reproduction and files

From `.` in PowerShell:

```powershell
$env:PYTHONPATH='./supplementary_study/.deps'
& 'python' targeted_closure_20261014/historical_audit/audit_existing_h4.py
```

The script imports only NumPy/SciPy and the standard library. It never imports or calls a simulation kernel. It reads the original local files listed in `INPUT_SHA256.csv`; restore those original paths from the user's retained supplementary handoff when reproducing elsewhere. The separate compact archive has its own schema and hashes and is not interchangeable at the byte level. All numeric audit outputs are regenerated beside the script. Python 3.12.14, NumPy 2.5.3 and the existing local SciPy were used.

Key outputs: `AUDIT_SUMMARY.json`, `run_inventory.csv`, `batch_sufficient_statistics.csv`, `per_run_windows.csv`, `grid_summary.csv`, `window_contrasts.csv`, `window_endpoints.csv`, `finite_window_identity.csv`, `fitted_coefficients.csv`, `per_run_fit_coefficients.csv`, `historical_fit_replay.csv`, `reconstruction_checks.csv`, `archive_array_integrity.csv`, `historical_source_hash_audit.csv`, and `historical_source_inventory.json`. CSV coordinate indices are zero-based; displayed prose/table coordinates above are one-based.
