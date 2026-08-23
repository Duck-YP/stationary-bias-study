# Numerical protocol

## Claim boundary

The numerical study is designed to challenge a candidate asymptotic formula.
A passing simulation is evidence of numerical consistency, not a mathematical
proof. A discrepancy triggers implementation and theorem audits before any
claim about the theorem is made.

## Independent unit

The independent inferential unit is the Markov chain. Eight chains use frozen,
distinct seeds and initial states. Batch means within one chain are used to
estimate its Monte Carlo uncertainty; they are not counted as independent
replicates in cross-chain confidence intervals.

## Execution stages

1. Validate the exact run matrix and unique run keys.
2. Initialize one RNG stream and one state per chain.
3. Discard the frozen burn-in interval.
4. Collect batch means until the precision rule passes or the maximum number
   of batches is reached.
5. Check finite states, the control-sum invariant, stationarity, and agreement
   of two estimators.
6. Write raw chain and batch records before deriving summaries.
7. Apply frozen falsification or confirmation gates.

All numerical parameters and thresholds are defined in `configs/`. The
implementation records a SHA-256 hash of those files in `run_manifest.json`.

