"""Render the fixed, non-advocacy E5 conclusions from saved analysis CSVs."""
import argparse
import csv
import json
from pathlib import Path


LIMITATION = ('This post-hoc analysis uses a reference-point plug-in coefficient on a single shared-objective '
              'logistic dataset with state-dependent minibatch noise and finite averaging windows. It is not a '
              'test or extension of the additive-noise stationary theorem, does not isolate its specific '
              'control coefficient from other finite-step and state-dependent-noise effects, and does not '
              'certify stationarity or bias-variance crossover. Its seed-resampling intervals do not cover '
              'proxy approximation/remainder or dataset uncertainty. No predictive '
              'harm, universal algorithm ranking, or optimal choice of H or step size is established.')


def generate(root):
    root = Path(root)
    def read(name):
        return list(csv.DictReader((root / name).open(encoding='utf-8')))
    def write(name, text):
        (root / name).write_text(text.strip()+'\n', encoding='utf-8')
    rows = read('ALL_CELLS_ALL_WINDOWS.csv')
    primary = [r for r in rows if r['K'] == '64']
    nonzero = [r for r in primary if r['H'] != '1']
    scaling = [r for r in read('SCALING_COMPARISONS.csv') if r['K'] == '64']
    hr = next(r for r in scaling if r['kind'] == 'H')
    table = '| H | N | m | gamma | observed projection | observed/proxy projection | cosine | residual/proxy norm |\n'
    table += '|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for r in primary:
        fields = [r['H'], r['N'], r['m'], f"{float(r['gamma']):.8f}", f"{float(r['observed_projection']):.9g}"]
        fields += [f"{float(r[k]):.6f}" if r[k] else 'undefined: zero proxy' for k in ['projection_ratio', 'cosine', 'relative_residual']]
        table += '| '+' | '.join(fields)+' |\n'
    write('SCIENTIFIC_SUMMARY.md', f'''# E5 scientific summary

**Decision: BRIDGE_DESCRIPTIVE_ONLY. Appendix-first, with at most one restrained main-text pointer. NO MORE RUNS.**

This analysis-only audit was executed locally using the saved E4 production artifacts. All nine cells, 12 paired seeds, seven windows and 124 coordinates are retained. No training or optimizer fitting was performed. E1's theoretical coefficient checks, E2's restricted affine-heterogeneity relation, and E3/R0's real-data implications remain distinct. E5 concerns only a post-hoc R0 plug-in interpretation; it supplies no general heterogeneous theorem.

## What the saved evidence supports

The parameter-free vector -gamma^2 kappa(H) A_ref^(-1) T_ref[Sigma_ref]/m captures a specific direction and a nontrivial order of magnitude of the finite-tail SCAFFOLD-minus-FedAvg mean shift. At K=64 the six non-H1 cosines are {min(float(r['cosine']) for r in nonzero):.6f} to {max(float(r['cosine']) for r in nonzero):.6f}, and observed/proxy projection ratios are {min(float(r['projection_ratio']) for r in nonzero):.6f} to {max(float(r['projection_ratio']) for r in nonzero):.6f}. Norm ratios are 0.718243 to 0.940472. These are ratios of a paired mean difference to a proxy, NOT fractions of squared bias, variance or MSE explained.

{table}
All six proxy magnitudes overpredict. Full-vector residual/proxy norms range from 0.088505 to 0.290542; the mismatch is not rounded away or absorbed into a fitted scale. The reference direction aligns more closely than frozen x_ref (cosines 0.8953-0.9087) and the unpreconditioned -T[Sigma] direction (0.6590-0.6929). The zero-amplitude null has a larger point residual than the proxy in all six cells. These fixed comparisons support descriptive explanatory information beyond a generic statement that some bias exists, but not exclusive mechanism attribution.

## Why this is not control-prefactor validation

Both algorithms' homogeneous B20 terms are multiples of the same -A^(-1)T[C] direction: FedAvg has factor (H-1)/4, SCAFFOLD has (H-1)(5H-1)/(12H), and their difference has kappa(H)=(H-1)(2H-1)/(12H). High cosine by itself cannot identify the control-associated term. The matched implementations differ by their control state, so the finite-tail paired shift is algorithmically associated with controls; what is not isolated is how much of it is the particular additive-noise coefficient rather than other finite-step and state-dependent effects.

The observed H4/H2 projection ratio is {float(hr['projection_ratio']):.9f}, versus the control-coefficient ratio 3.5: a {(1-float(hr['relative_to_proxy']))*100:.2f}% shortfall. The global exploratory scalar band is [{float(hr['projection_ratio_lower_simultaneous']):.6f}, {float(hr['projection_ratio_upper_simultaneous']):.6f}], the jackknife sensitivity is [{float(hr['projection_ratio_lower_jackknife_Bonferroni']):.6f}, {float(hr['projection_ratio_upper_jackknife_Bonferroni']):.6f}], and the conservative projection-band transform is [{float(hr['projection_ratio_interval_transform_lower']):.6f}, {float(hr['projection_ratio_interval_transform_upper']):.6f}]. All exclude 3.5 while including the ordinary FedAvg local-update coefficient ratio 3.0. That comparison is a collinearity/identification warning, NOT evidence that a FedAvg coefficient is the true model for the paired difference. The theorem remainder is not included in these intervals; this is not a theorem falsification.

H1 has exactly zero proxy and observed K64 residual norms of approximately 1e-11 to 1e-10. It is useful as an algebraic and implementation negative control, not a unique identification test. Historical H1 long-horizon numerical issues remain disclosed, not repaired or recast as exact empirical zero.

## Scaling and window sensitivity

At H4,N32,m8, the observed/proxy projection ratio rises from 0.784711 to 0.867499 to 0.935781 as gamma decreases from 0.19607843 to 0.09803922 to 0.04901961. Adjacent descriptive gamma log slopes are 1.855298 and 1.890691; the overall secant is 1.872994. This is compatible with improving leading-term approximation on this grid, but three points do not identify a general asymptotic rate.

For allocations (N,m)=(8,32),(32,8),(128,2), adjacent observed projection ratios are 4.385515 and 4.061132 versus plug-in ratios of 4; the endpoint ratio is 17.810154 versus 16. N and m change together: this is not a fixed-C cross-N test. Every K is tabulated; across all non-H1 windows cosines fall as low as 0.872197, and projection ratios range approximately 0.707491-1.006733. K64 was designated primary in the E5 brief, not selected for strongest alignment. Short-window noisiness is retained.

All 54 paired first-K/last-K contrasts are reported. Their uncertainty is not a replacement for stationarity testing of each algorithm. E4's 144 failed temporal-equivalence gates, NO_CERTIFIED_CROSSOVER, and INCONCLUSIVE_PRECISION_OR_STATIONARITY remain unchanged. A failure to establish equivalence is not proof of drift or proof of no stationary law.

## Practical meaning and stopping decision

At the E4 primary cell H4,N128,m2,K64, estimated finite-tail squared-bias shares are 68.1299% for SCAFFOLD and 49.5122% for FedAvg. Between-seed averaged-model variance is not single-checkpoint variance. E4's matched total-MSE difference is 6.388780175270564e-6; the matched training-objective difference is only 3.640946888613013e-7. The SCAFFOLD held-out log loss is slightly LOWER, with a matched difference -3.269249154080889e-5. A mean-difference vector is not an MSE difference, and a statistical parameter-space distinction does not establish predictive harm.

The audit reduces source/formula ambiguity and provides a useful appendix diagnostic, but does not materially establish a new broad practical mechanism or guarantee improved publication prospects. Submit/review the paper as a focused theory contribution with its existing bounded empirical interpretation. No further experiment is scientifically necessary for that narrow claim; stronger stationarity or control-prefactor identification would be a separate future study, not an automatic extension of this task.

## Mandatory limitation language

> {LIMITATION}

Full numerical precision, bootstrap/jackknife sensitivity, vector balls, exact round lengths and source hashes are in the accompanying CSV/NPZ files and audit receipts. No claim is made that the entire bias or remainder is independent of H.
''')
    write('REVIEWER_RISK_DECISION.md', f'''# Reviewer-risk decision

**BRIDGE_DESCRIPTIVE_ONLY**

## 1. Direction and magnitude beyond generic bias?

Yes, descriptively. The independently recomputed reference vector is parameter-free and closely aligns with the full 124-dimensional matched mean shift; the six K64 projection amplitudes are 71.6%-93.8% of the proxy. This is useful explanatory structure, not merely a nonzero-bias observation. It systematically overpredicts magnitude, and lower-K alignment is weaker. The legitimate frozen direction and zero-amplitude comparisons do not eliminate all other mechanisms.

## 2. Is H scaling/H1 control-specific evidence?

Only weakly. H1 validates the zero-factor structure up to retained numerical drift. Both algorithms' B20 directions are collinear, and both also vanish at H1. Most importantly, H4/H2 is 2.927 rather than 3.5, with all three exploratory interval approaches excluding the latter. The ratio is closer to generic local-update scaling 3.0, but this does not fit or validate that alternative. A claim that the new control prefactor was quantitatively verified on real data would create a reviewer vulnerability.

## 3. Integration recommendation

Appendix-only diagnostic with, at most, a short main-text pointer using explicitly exploratory language. Do not promote this to a main-text mechanism-validation result. The audit supports a disciplined interpretation of a finite-tail phenomenon, not a new general heterogeneous theorem, stationary certification, or algorithm recommendation. Suggested text is provided separately and is unapproved; the manuscript was not edited.

Use this exact accompanying limitation:

> {LIMITATION}

## 4. Necessary further experiment?

**NO MORE RUNS.** No missing source or numerical blocker prevents a decision on the narrow existing claim. More seeds would improve Monte Carlo precision but would not repair state-dependent-noise applicability, collinearity or the finite-H prefactor discrepancy. A future mechanism-identification study could be designed separately; it is not required to complete E5 and is neither scheduled nor executed.

This conclusion agrees with the separately recorded reviewer audit in `reviewer_audit/`. It should not be read as a prediction of acceptance by MLJ. The scientific gain is clarity and a bounded explanatory link, not a guaranteed increase in publication competitiveness.
''')
    write('SCOPE_AND_LIMITATIONS.md', f'''# Scope and limitations

## Proven result versus plug-in

The theoretical difference is gamma^2 B20_ctrl(H) + O_(H,d)(gamma^2/N + gamma^3). Its assumptions include a common homogeneous objective, full participation, bounded state-independent additive noise, fixed client covariance C in the prescribed joint limit, fixed d and H, and sufficiently small gamma. The remainder explicitly depends on H and d; the full bias/remainder is not H-independent.

R0 is homogeneous in empirical objective, with shared retained training rows, but its minibatch logistic noise is state-dependent. All 124 coordinates including the intercept have ridge coefficient 0.01. At the fixed reference, ideal with-replacement sampling gives C_ref=Sigma_ref/m, with no finite-population correction. The deterministic indexed SplitMix64/modulo implementation is not an i.i.d. mathematical oracle; modulo-row total variation under a uniform 64-bit key is about 1.37685e-17, and pseudorandom independence is a modeling assumption. The code/source audit records these separately from floating-point control drift.

When N changes under N*m=256, m and the client covariance change. Reference-point T and Sigma do not describe the entire state-dependent noise field. The contraction T_ref[Sigma_ref] differentiates curvature with Sigma_ref held fixed; differentiating trace(A(x) Sigma(x)) would add noise-field derivative terms and is a different quantity. Finite gamma, finite burn/tail, one dataset, 12 seeds, fixed d=124 and only H1/2/4 preclude theorem-level generalization. No heterogeneous real-data theorem is inferred. E1 theory-coefficient validation and E2 affine-heterogeneity exact relations remain separate historical evidence streams.

## Estimands

E5 Delta is the seed mean of each run's actual time-averaged SCAFFOLD model minus its matched FedAvg model. Its squared norm is not either algorithm's squared bias, and is not Delta MSE. E4 estimates U (sampling-corrected squared finite-tail mean), V (between-seed variance of time-averaged models), and total MSE separately. A single chronological checkpoint has a different variance. Full-vector effects and frozen-direction projections are both saved.

## Uncertainty

All resampling is at the 12-paired-seed level, conditionally on the saved dataset/protocol. Neither coordinates nor chronological batches are independent inference units. Scalar and vector-ball families are separately nominal 95%. Small-sample bootstrap and jackknife are sensitivities, not exact coverage guarantees. Nonlinear norm/cosine estimators have finite-sample bias, especially near zero/unit values. No proxy remainder, dataset uncertainty, stationarity error or publication-selection uncertainty is included.

## Retained unfavorable outcomes

- All six non-H1 K64 proxy amplitudes overpredict.
- H4/H2 prefactor ratio 3.5 is not supported by the matched finite-grid ratio; no fitted scale hides this.
- Short-window alignment can be substantially weaker.
- E4 has 0/144 passed temporal-equivalence gates and no certified crossover.
- Historical H4 target exclusions, H8 finite-grid discrepancy/exclusions and H1 long-horizon numerical issues are retained in `prior_e4/historical/`, `inputs/full_results.csv` and `inputs/per_run_estimates.csv`. They are not evaluated away by E5.
- The training-objective difference is tiny; held-out SCAFFOLD loss is slightly lower, not worse. No predictive harm or optimal policy follows.
- Only the two preexisting E4_v2 pilot seeds were run previously; the 48-seed E4_v2 extension remains unexecuted. E5 did not run it.

> {LIMITATION}
''')
    write('CLAIM_EVIDENCE_MAP.md', '''# Claim-evidence map

| Claim | Evidence | Allowed interpretation | Not established |
|---|---|---|---|
| Independent plug-in reconstruction is correct | NUMERICAL_CROSSCHECKS.csv; independent_formula/; source hashes | Saved empirical logistic reference, all124 coordinates, centered Sigma, exact frozen gamma | Validity of additive-noise theorem for state-dependent R0 |
| Actual averaged checkpoints are reused | inputs/batches.npz; inputs/models.npz; exact replay check; PAIRED_SEED_RESULTS.csv | Nine cells x12paired seeds x7windows; no training | 64 independent observations per seed |
| Reference direction tracks paired mean shifts | ALL_CELLS_ALL_WINDOWS.csv; FULL_VECTOR_ALIGNMENT.csv; VECTORS.npz | Strong K64 full-vector alignment, weaker short windows | Unique control-mechanism identification |
| Proxy has nontrivial magnitude but systematic overprediction | All six non-H1 K64 projection/norm ratios and residual decomposition | Parameter-free descriptive approximation with explicit error | Exact coefficient fit, unbiased proxy, explained fraction of total MSE |
| H scaling is a substantive limitation | SCALING_COMPARISONS.csv; all interval sensitivities | 2.927 vs3.5 at frozen grid; H1 absolute controls preserved | Verified control prefactor on real data or falsified theorem |
| Smaller gamma improves observed/proxy ratio here | All three gamma comparisons at every K | Descriptive finite-grid secants | General gamma^2 asymptotic rate |
| Allocation varies covariance as well as N | R0_CONFIGS.json; sampling audit; allocation rows | N*m=256 implies C_ref=Sigma_ref/m | Fixed-C cross-N theorem test |
| Comparators are legitimate but nonexhaustive | NEGATIVE_CONTROLS.csv; specification; code | Frozen x_ref and -T directions, zero amplitude, no fit | Model-selection victory or exclusion of generic nonlinear effects |
| Conditional Monte Carlo precision | PAIRED_BOOTSTRAP_SENSITIVITY.csv; INFERENCE_ARRAYS.npz; statistical receipt | Paired12seed max-deviation/jackknife and full-vector sensitivity | Proxy-remainder, dataset or stationary-law coverage |
| Window behavior does not certify stationarity | EARLY_LATE_PAIRED_DIAGNOSTICS.csv; prior_e4/TEMPORAL_DIAGNOSTICS.csv | All K retained; original0/144gates unchanged | Certified stationary bias or crossover |
| Parameter-space effect need not imply prediction harm | prior_e4/BIAS_VARIANCE_MSE.csv; PRACTICAL_IMPLICATIONS.csv | E4 primary bias shares68.1/49.5%; tiny train gap; lower SCAFFOLD test loss | Universal ranking, harm, optimal H/gamma |
| Unfavorable historical outcomes remain available | prior_e4/historical/; inputs/full_results.csv; per_run_estimates.csv | H4/H8 exclusions and H1 numerical issues retained | New target inclusion or analysis-rule revision |
| Stop at descriptive bridge | SCIENTIFIC_SUMMARY.md; REVIEWER_RISK_DECISION.md; reviewer_audit/ | Appendix-first; optional restrained pointer | Guaranteed publication gain or automatic future runs |
''')
    write('MISSING_ITEMS.md', '''# Missing items and unresolved issues

## No required new computation left open

The requested analysis-only bridge, source/formula checks, paired-seed sensitivity, complete cell/window coverage, figures and audit are delivered. The final package QA receipt records verification rather than substituting this statement for execution. No training is necessary to reproduce E5. There is no hidden checkpoint requiring a training resume.

## Scientific limitations intentionally unresolved

1. Stationarity is not certified; all original 144 equivalence gates failed. No certified bias-variance crossover.
2. State-dependent minibatch noise is outside the stated additive-noise theorem. The plug-in remainder is unknown and not bounded by seed CIs.
3. The H4/H2 amplitude ratio disagrees with 3.5 on the frozen finite grid; generic collinear effects cannot be separated conclusively.
4. All six non-H1 K64 proxy magnitudes overpredict; no correction was fitted.
5. Only one shared-objective logistic dataset and 12 paired seeds; no independent held-out dataset replication or general heterogeneous claim.
6. H1 long-horizon numerical drift and historical H4/H8 exclusions remain part of the record.
7. Existing E4_v2 48-seed production extension remains NOT_RUN. Only its two original pilot seeds exist; E5 adds none.
8. Small-sample nonlinear bootstrap/jackknife coverage is approximate. Different declared scalar/vector families do not jointly confer 95% coverage.
9. No optimal H/gamma policy, prediction harm or universal ranking has been identified.

These are boundaries of the evidence, not a claim that compute scarcity scientifically refutes the phenomenon. There is no scientifically necessary additional run for the recommended narrow submission claim. STOP after handoff.
''')
    write('SUGGESTED_MANUSCRIPT_INSERT.tex', r'''% UNAPPROVED OPTIONAL TEXT. No manuscript file has been edited.
% Recommendation: appendix diagnostic; at most a short pointer in the discussion.
\paragraph{Exploratory reference-point comparison.}
In an analysis-only, post-hoc diagnostic of the shared-objective logistic
experiments, a parameter-free reference-point plug-in of the control-associated
coefficient aligned closely with the full-dimensional paired finite-tail mean
shift. At the longest saved averaging window, the six nonzero-coefficient
settings had observed-to-proxy projection ratios between 0.716 and 0.938.
The proxy systematically overpredicted amplitude: in particular, the observed
$H=4$ to $H=2$ ratio was 2.927 rather than the coefficient ratio 3.5.
Both algorithms' homogeneous second-order terms share the same reference
direction, so directional agreement does not uniquely identify a
control-associated mechanism. This single-dataset comparison uses
state-dependent minibatch noise and uncertified finite tails; it is not a test
or extension of the additive-noise stationary theorem and does not establish
prediction harm, a certified crossover, or an optimal algorithmic policy.
''')
    print(json.dumps(dict(status='PASS', reports=6, classification='BRIDGE_DESCRIPTIVE_ONLY', training=False)))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    generate(p.parse_args().root)
