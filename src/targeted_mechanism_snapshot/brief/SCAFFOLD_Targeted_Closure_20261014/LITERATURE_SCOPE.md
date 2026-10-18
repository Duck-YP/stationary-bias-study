# Bounded literature/novelty check

## Verified source and proposed insertion

Official Glasgow et al. source: https://proceedings.mlr.press/v151/glasgow22a.html
Author/PMLR PDF: https://proceedings.mlr.press/v151/glasgow22a/glasgow22a.pdf

Read Definition 2.1, Theorems 2.4-2.5 and Section 2.3. They distinguish a finite-step iterate-bias quantity from the invariant-law mean studied in the current manuscript. The proposed insertion credits this precursor; it is not a claim that a complete novelty search has been finished.

`related_work_insert.tex` and `glasgow2022sharp.bib` are review-ready snippets, not a compiled or already-integrated manuscript revision. Table 1 should remain a comparison of stationary expansions on a shared model, rather than mixing distinct estimands.

## Audit instructions for Codex

Use primary sources only. Anchor the check on these sources and, at most, two directly relevant papers cited by them or citing them:

1. Glasgow, Yuan and Ma (2022), above.
2. Mangold et al., FedAvg: https://proceedings.mlr.press/v258/mangold25a.html ; manuscript comparison uses https://arxiv.org/abs/2412.01389v2 .
3. Mangold et al., SCAFFOLD: https://proceedings.mlr.press/v267/mangold25a.html ; manuscript comparison uses https://arxiv.org/abs/2503.07594v1 .
4. Dieuleveut, Durmus and Bach, already in the manuscript: DOI 10.1214/19-AOS1850. Obtain the primary author/publisher text before making theorem-level claims.

The audit table must record: source/version, estimand, assumptions, time/asymptotic regime, explicit coefficients versus bounds, persistent-control analysis, and exact theorem/section/page supporting each comparison.

Separate (a) prior nonlinearity/noise mechanisms, (b) local finite-step iterate-bias bounds, (c) stationary leading-coefficient analyses, and (d) the claimed explicit matched stationary gamma^2 coefficient with N-uniform remainder.

Do not declare novelty confirmed merely because a keyword is absent. Do not deny mathematical implications of prior results merely because the prior authors use another notation. If a prior formula appears to imply part of the proposed coefficient after a stationary argument, show that implication and specify which stationary/remainder steps are still needed. If genuine overlap is found, report it before recommending any new experiments.

Do not pad the bibliography to reach an arbitrary reference count. Deliver a bounded source-to-claim table, a short conclusion about overlap, and a proposed manuscript diff only. Do not modify manuscript theorems, empirical outcomes or Table 1's numerical asymptotic formulas without a separately justified correction.

No paywall access or unavailable PDF should be represented as read. If network/source access fails, record the gap and preserve the verified Glasgow insertion; do not fill the gap from an abstract or search snippet.
