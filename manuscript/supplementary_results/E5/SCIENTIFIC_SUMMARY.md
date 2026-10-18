# E5 scientific summary

**Decision: BRIDGE_DESCRIPTIVE_ONLY. Appendix-first, with at most one restrained main-text pointer. NO MORE RUNS.**

This analysis-only audit was executed locally using the saved E4 production artifacts. All nine cells, 12 paired seeds, seven windows and 124 coordinates are retained. No training or optimizer fitting was performed. E1's theoretical coefficient checks, E2's restricted affine-heterogeneity relation, and E3/R0's real-data implications remain distinct. E5 concerns only a post-hoc R0 plug-in interpretation; it supplies no general heterogeneous theorem.

## What the saved evidence supports

The parameter-free vector -gamma^2 kappa(H) A_ref^(-1) T_ref[Sigma_ref]/m captures a specific direction and a nontrivial order of magnitude of the finite-tail SCAFFOLD-minus-FedAvg mean shift. At K=64 the six non-H1 cosines are 0.996500 to 0.999254, and observed/proxy projection ratios are 0.715730 to 0.938327. Norm ratios are 0.718243 to 0.940472. These are ratios of a paired mean difference to a proxy, NOT fractions of squared bias, variance or MSE explained.

| H | N | m | gamma | observed projection | observed/proxy projection | cosine | residual/proxy norm |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 128 | 2 | 0.19607843 | -2.37524311e-12 | undefined: zero proxy | undefined: zero proxy | undefined: zero proxy |
| 1 | 32 | 8 | 0.19607843 | -3.37937987e-12 | undefined: zero proxy | undefined: zero proxy | undefined: zero proxy |
| 1 | 8 | 32 | 0.19607843 | 1.96846936e-12 | undefined: zero proxy | undefined: zero proxy | undefined: zero proxy |
| 2 | 32 | 8 | 0.19607843 | 9.28104167e-05 | 0.938327 | 0.997719 | 0.088505 |
| 4 | 128 | 2 | 0.19607843 | 0.00110323291 | 0.796703 | 0.999254 | 0.205615 |
| 4 | 32 | 8 | 0.04901961 | 2.02472035e-05 | 0.935781 | 0.997252 | 0.094644 |
| 4 | 32 | 8 | 0.09803922 | 7.50792214e-05 | 0.867499 | 0.998972 | 0.138225 |
| 4 | 32 | 8 | 0.19607843 | 0.000271656493 | 0.784711 | 0.998994 | 0.218151 |
| 4 | 8 | 32 | 0.19607843 | 6.19440398e-05 | 0.715730 | 0.996500 | 0.290542 |

All six proxy magnitudes overpredict. Full-vector residual/proxy norms range from 0.088505 to 0.290542; the mismatch is not rounded away or absorbed into a fitted scale. The reference direction aligns more closely than frozen x_ref (cosines 0.8953-0.9087) and the unpreconditioned -T[Sigma] direction (0.6590-0.6929). The zero-amplitude null has a larger point residual than the proxy in all six cells. These fixed comparisons support descriptive explanatory information beyond a generic statement that some bias exists, but not exclusive mechanism attribution.

## Why this is not control-prefactor validation

Both algorithms' homogeneous B20 terms are multiples of the same -A^(-1)T[C] direction: FedAvg has factor (H-1)/4, SCAFFOLD has (H-1)(5H-1)/(12H), and their difference has kappa(H)=(H-1)(2H-1)/(12H). High cosine by itself cannot identify the control-associated term. The matched implementations differ by their control state, so the finite-tail paired shift is algorithmically associated with controls; what is not isolated is how much of it is the particular additive-noise coefficient rather than other finite-step and state-dependent effects.

The observed H4/H2 projection ratio is 2.927004345, versus the control-coefficient ratio 3.5: a 16.37% shortfall. The global exploratory scalar band is [2.741514, 3.112494], the jackknife sensitivity is [2.710071, 3.143937], and the conservative projection-band transform is [2.692847, 3.191868]. All exclude 3.5 while including the ordinary FedAvg local-update coefficient ratio 3.0. That comparison is a collinearity/identification warning, NOT evidence that a FedAvg coefficient is the true model for the paired difference. The theorem remainder is not included in these intervals; this is not a theorem falsification.

H1 has exactly zero proxy and observed K64 residual norms of approximately 1e-11 to 1e-10. It is useful as an algebraic and implementation negative control, not a unique identification test. Historical H1 long-horizon numerical issues remain disclosed, not repaired or recast as exact empirical zero.

## Scaling and window sensitivity

At H4,N32,m8, the observed/proxy projection ratio rises from 0.784711 to 0.867499 to 0.935781 as gamma decreases from 0.19607843 to 0.09803922 to 0.04901961. Adjacent descriptive gamma log slopes are 1.855298 and 1.890691; the overall secant is 1.872994. This is compatible with improving leading-term approximation on this grid, but three points do not identify a general asymptotic rate.

For allocations (N,m)=(8,32),(32,8),(128,2), adjacent observed projection ratios are 4.385515 and 4.061132 versus plug-in ratios of 4; the endpoint ratio is 17.810154 versus 16. N and m change together: this is not a fixed-C cross-N test. Every K is tabulated; across all non-H1 windows cosines fall as low as 0.872197, and projection ratios range approximately 0.707491-1.006733. K64 was designated primary in the E5 brief, not selected for strongest alignment. Short-window noisiness is retained.

All 54 paired first-K/last-K contrasts are reported. Their uncertainty is not a replacement for stationarity testing of each algorithm. E4's 144 failed temporal-equivalence gates, NO_CERTIFIED_CROSSOVER, and INCONCLUSIVE_PRECISION_OR_STATIONARITY remain unchanged. A failure to establish equivalence is not proof of drift or proof of no stationary law.

## Practical meaning and stopping decision

At the E4 primary cell H4,N128,m2,K64, estimated finite-tail squared-bias shares are 68.1299% for SCAFFOLD and 49.5122% for FedAvg. Between-seed averaged-model variance is not single-checkpoint variance. E4's matched total-MSE difference is 6.388780175270564e-6; the matched training-objective difference is only 3.640946888613013e-7. The SCAFFOLD held-out log loss is slightly LOWER, with a matched difference -3.269249154080889e-5. A mean-difference vector is not an MSE difference, and a statistical parameter-space distinction does not establish predictive harm.

The audit reduces source/formula ambiguity and provides a useful appendix diagnostic, but does not materially establish a new broad practical mechanism or guarantee improved publication prospects. Submit/review the paper as a focused theory contribution with its existing bounded empirical interpretation. No further experiment is scientifically necessary for that narrow claim; stronger stationarity or control-prefactor identification would be a separate future study, not an automatic extension of this task.

## Mandatory limitation language

> This post-hoc analysis uses a reference-point plug-in coefficient on a single shared-objective logistic dataset with state-dependent minibatch noise and finite averaging windows. It is not a test or extension of the additive-noise stationary theorem, does not isolate its specific control coefficient from other finite-step and state-dependent-noise effects, and does not certify stationarity or bias-variance crossover. Its seed-resampling intervals do not cover proxy approximation/remainder or dataset uncertainty. No predictive harm, universal algorithm ranking, or optimal choice of H or step size is established.

Full numerical precision, bootstrap/jackknife sensitivity, vector balls, exact round lengths and source hashes are in the accompanying CSV/NPZ files and audit receipts. No claim is made that the entire bias or remainder is independent of H.
