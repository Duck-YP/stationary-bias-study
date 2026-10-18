# Bounded prior-work and coefficient audit

Audit date: 2026-10-14 (Asia/Taipei). Baseline: the current local `manuscript/`, not an archive replacement. Scope: the four requested papers; no additional papers were added. The master manuscript was not modified. This is a bounded comparison, not proof of worldwide novelty.

## Conclusion for the present manuscript

Credit Glasgow, Yuan and Ma for stochastic local-iterate bias without objective heterogeneity, the role of third-order smoothness, and the infinite-client round-map viewpoint. Credit Mangold et al. for stationary FedAvg/SCAFFOLD bias and the nonvanishing control covariance. These are substantive precedents, not merely background references.

There is **partial mathematical overlap**: ordinary local-update bias is an established mechanism; the FedAvg infinite-client coefficient can be obtained with a short additional discrete Taylor/fixed-point argument; and the leading persistent-control covariance is already explicit in the SCAFFOLD source. The corresponding within-round variance contribution is recoverable from its formulas. The audited sources do not themselves establish the manuscript's full matched expansion with a common step threshold and an **N-uniform** `O(gamma^2/N + gamma^3)` remainder. The defensible contribution is this explicit matched stationary resolution and its controlled remainder, not discovery of noise-induced bias, control covariance, or every ingredient of the coefficient.

No reason was found to alter Table 1's displayed Mangold remainder orders. Its title/caption should continue to compare stationary expansions only; Glasgow's distinct estimand belongs in prose. The proposed patch adds the missing credit and clarifies the control-covariance precedent.

## Source-to-claim table

Pages below are **one-based PDF pages**, which are stable across the saved copies; they are not inferred from journal page ranges. Versioned links and SHA-256 hashes are in `SOURCE_EVIDENCE.json`.

| Source/version read | Estimand and regime | Assumptions relevant to this comparison | Coefficients/bounds and precise anchors | Persistent controls; remainder implication |
|---|---|---|---|---|
| [Glasgow, Yuan and Ma (2022), PMLR 151](https://proceedings.mlr.press/v151/glasgow22a/glasgow22a.pdf) | Expected finite-step SGD iterate minus GD from the same start; the optimum is a special start. Definition 2.1, p.5. Infinite-client round-map motivation immediately precedes it. | Assumptions 1–2, pp.5–6: convex smooth stochastic objectives, bounded variance; Hessian Lipschitzness and bounded fourth noise moment for the stronger bound. | Theorems 2.4–2.5, p.6; complete A.3–A.4, p.14: sharp finite-step order `eta^3 k^2 Q sigma^2`. Section 2.3, pp.6–7: continuous explanation through third derivative and variance. | No persistent controls. No invariant-law joint expansion or N-uniform stationary remainder is asserted by these results. The discrete implication below requires additional work. |
| [Mangold et al., FedAvg, arXiv:2412.01389v2](https://arxiv.org/pdf/2412.01389v2), also checked against [PMLR 258](https://proceedings.mlr.press/v258/mangold25a.html) | Global invariant-law mean and covariance, small constant step size. | A1, p.3: strong convexity, convex/smooth stochastic losses, bounded third derivative; A3, p.5: moments through order six. Theorem 3 also requires identical objectives **and noise laws** (A6, p.7). | Theorems 3–4, p.7; proofs B.5–B.6, pp.33–42. Common-objective first coefficient equals `B11`; residuals are `O(gamma^2 H + gamma^(3/2))` and `O(gamma^2 H^2 + gamma^(3/2) H)`. Heterogeneity coefficient vanishes for identical objectives. | No persistent-control state. The residuals divided by `gamma^2` do not identify `B20`. Theorem 4 permits the broader common-objective specialization without A6. Official edition has the same compared formulas. |
| [Mangold et al., SCAFFOLD, arXiv:2503.07594v1](https://arxiv.org/pdf/2503.07594v1), also checked against [PMLR 267](https://proceedings.mlr.press/v267/mangold25a.html) | Joint global-model/control invariant law; global bias and joint second moments. | A1–A5, pp.2–3: strong convexity/smoothness, bounded third derivative, heterogeneity bounds, sixth noise moments; A6, p.8 adds bounded fourth derivative. | Theorem 5.3, p.8 and p.45: shared first coefficient plus `O(gamma^2 H + gamma^(3/2))`. Lemma 5.1, p.7, restated p.42: explicit control covariance. Lemma E.3, pp.43–44: within-round square expansion. | Persistent controls are explicitly analyzed already. Their covariance is not suppressed by N. The stated stationary/local residuals leave the desired second-order resolution open; official edition agrees on the compared orders. |
| [Dieuleveut, Durmus and Bach, arXiv:1707.06386v2](https://arxiv.org/pdf/1707.06386v2) (author version of DOI 10.1214/19-AOS1850); earlier [author-hosted text](https://www.cmap.polytechnique.fr/~aymeric.dieuleveut/papers/Dieuleveut-Durmus-Bach.pdf) also read | SGD invariant mean/covariance and averaged-iterate weak expansions; fixed problem, step tending to zero. | A1–A5, pp.5–6: strong convexity; bounded derivatives of orders 2–5; independent unbiased random fields, co-coercivity and moment conditions; regular covariance. | Theorem 4, pp.13–14: first-order stationary structure and `O(gamma^2)` error. Theorem 7, p.17: weak/averaged expansion. **Printed coefficient caveat below.** | No federated persistent controls or joint client limit. No explicit second-order federated coefficient. Publisher final PDF could not be inspected; author-version numbering is used, and final-edition equality is not assumed. |

## Direct implications: what is inherited and what must still be proved

Use the current manuscript's notation `A = Hessian f(0)`, `T = third derivative f(0)`, `C = covariance`, with `A S_C + S_C A = C`, fixed local-step count H, and additive centered independent noises. The calculations in this section are **this audit's derivations**, not quotations of prior theorems.

### 1. Ordinary local updates: an infinite-client coefficient is readily derivable

Let `M_gamma(x) = E[theta_H | theta_0=x]` for H local SGD steps. This is exactly the infinite-client round-map interpretation preceding Glasgow's Definition 2.1. Start at `x=0`. For fixed h and small gamma, bounded noise and smoothness give

```
E[theta_h theta_h^T] = gamma^2 h C + O_H(gamma^3),
E[theta_(h+1)] = (I-gamma A) E[theta_h]
                 - (gamma^3 h/2) T[C] + O_H(gamma^4).
```

Consequently

```
M_gamma(0) = -gamma^3 H(H-1) T[C]/4 + O_H(gamma^4).
```

For the manuscript's globally strongly convex/smooth additive-noise setting and sufficiently small gamma, a synchronous-noise coupling makes `M_gamma` a contraction with factor at most `(1-gamma mu)^H`. Its fixed point `m_gamma` therefore satisfies `||m_gamma|| = O_H(gamma^2)`. Expanding the map at such an x gives

```
M_gamma(x)-x = -gamma H A x
               -gamma^3 H(H-1) T[C]/4 + O_H(gamma^4),
m_gamma = -gamma^2 (H-1) A^(-1) T[C]/4 + O_H(gamma^3).
```

This recovers the manuscript's **FedAvg client-independent coefficient** in the infinite-client map. It is more than a similarity of keywords. Conversely, Glasgow's finite-step norm bound alone does not identify its vector coefficient, and its continuous approximation is not an exact discrete H-step formula. The finite-N invariant law, its `gamma/N` term, and a bound uniform under arbitrary joint limits still require a stationary argument with explicit N dependence. Taking N to infinity first is insufficient to prove the manuscript's theorem.

### 2. Persistent controls: the leading variance ingredient is already available

Specializing Mangold's Lemma 5.1 to identical objectives and covariance gives, in this manuscript's zero-sum coordinates,

```
E[xi_c xi_c^T] = (1-1/N) C/H + O_H(gamma).
```

The local displacement contains `-gamma h xi_c` in addition to the fresh partial noise sum. Hence its squared leading control contribution is

```
gamma^2 h^2 (1-1/N) C/H.
```

The term linear in `x xi_c^T` cancels **after averaging over clients**, because the controls sum to zero. The fresh round noise is independent of the starting controls. Retaining this term in the local second-moment expression of Lemma E.3, then in stationary mean balance, produces the candidate extra coefficient

```
- (1/(2H)) sum_(h=0)^(H-1) (h^2/H) A^(-1) T[C]
= - (H-1)(2H-1)/(12H) A^(-1) T[C].
```

Adding the ordinary local contribution yields

```
B20_S = - (H-1)(5H-1)/(12H) A^(-1) T[C].
```

This is a real derivational connection to prior work. It is **not**, by itself, a proof that all omitted terms are `O_H(gamma^2/N + gamma^3)`. In particular, one must sharpen the global second-moment residual, control local/global mixed terms and signed third moments, and handle stationary means before interchanging limits. A prior bound `O(gamma^(3/2))` on a global second moment cannot simply be relabeled as a smaller N-dependent error. The averaged zero-sum cancellation does not bound every remaining term. These are the substantive remainder tasks supplied by the manuscript's proof, which this literature audit does not re-prove.

### 3. Shared first coefficient and covariance-matched laws

The usual stationary Taylor balance is `0 = A b + (1/2) T[E(xx^T)] + higher terms`. With leading global second moment `(gamma/N) S_C`, it gives `B11 = -(1/2) A^(-1) T[S_C]`, consistent with both Mangold formulas under the matched submodel. This first-order curvature/covariance mechanism is established prior work.

The displayed candidate `B20` calculations use only C, but that is not evidence that all finite-N or higher-order noise-law effects vanish. No source comparison here justifies calling every symmetric/asymmetric-law difference `O(gamma^3)`; terms of order `gamma^2/N` are compatible with the manuscript. The planned mechanism checks assess coefficient resolution and cannot establish novelty.

## Source and transcription caveats

1. **DDB version caveat:** arXiv v2, p.13, Equation (15), visibly prints a positive unit multiplier on `gamma A^(-1) T[S_C]`, while Equations (16)–(17) give the covariance/Lyapunov convention used above. Direct stationary Taylor balance requires `-1/2` under those definitions. The earlier author PDF prints the same discrepancy. The p.13 page was rendered and checked: this is not merely a text-extraction artifact. This audit credits the stationary expansion method/structure but does not use that printed multiplier as an independently verified numeric coefficient. The final publisher equation and any corrigendum remain unchecked; no correction to the current manuscript is warranted from this source-version issue alone.
2. **Glasgow continuous illustration:** p.6, Equation (2.2), specifies diffusion `sqrt(eta) sigma dB`, while the displayed Equation (2.3) uses diffusion-generator coefficient `eta sigma^2`, rather than the usual `eta sigma^2/2`. The page was rendered and checked. This normalization caveat does not negate the order bounds of Theorems 2.4–2.5. We use the explicit discrete calculation above for constants and do not copy the heuristic `k^2` constant into a fixed-H stationary claim.
3. **SCAFFOLD appendix caution:** v1 p.44 Lemma E.4's displayed prefactor contains an extra `1/N` relative to its proof and Theorem 5.3 when `Sigma_theta` denotes the global covariance. We relied on the local update equation, Lemma 5.1, and main theorem, not that isolated displayed factor. This source transcription issue does not establish a flaw in the current manuscript.

## Proposed claims and remaining questions

Suitable claim: "Within the common-objective additive-noise setting, the analysis resolves explicit matched stationary second-order coefficients and an N-uniform remainder, building on prior local-iterate bias and stationary control-covariance analyses."

Avoid claims that this is the first demonstration of bias for homogeneous FedAvg, the first analysis of nonlinearity/noise interaction, the first stationary SCAFFOLD analysis, or the first observation of persistent control covariance. Avoid treating a lack of duplicate phrasing as a novelty result.

Unresolved: the final DDB publisher formula/corrigendum; whether more remote papers outside this deliberately bounded set establish the same joint remainder; and an independent proof audit of every step that sharpens the prior residuals. No additional bibliography was added merely to broaden the search. All four required primary-source texts were read; inaccessible publisher content is identified rather than represented as verified.

`proposed_related_work.patch` is a review-only unified diff against the hashed current `sections/02_related_work.tex` and `references.bib`. It adds Glasgow and the control-covariance credit, leaves theorem statements/Table 1 formulas untouched, and has not been applied to the master manuscript.
