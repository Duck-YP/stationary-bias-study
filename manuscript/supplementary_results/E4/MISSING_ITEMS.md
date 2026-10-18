# Missing And Unresolved Items

Nothing is missing for the executed E4_v1 averaging replay: all9cells,108paired
runs,1512models, sevenwindows, individual losses, signed negative U estimates and
all temporal diagnostics are retained.

- A certified stationary regime or mean temporal equivalence is unresolved.
  All144 gates fail; failure is not proof of drift or no practical effect.
- A two-consecutive-window uncertainty-supported crossover is not observed;
  SCAFFOLD only K64 clears the scalar comparison, and temporal gates fail.
- Raw-round trajectories/IAC and independent historical R0 burn sensitivity are
  unavailable. Endpoints/chronological batch statistics are included; they cannot
  reconstruct every raw checkpoint or certify mixing.
- V2 completed only two fresh R2 pilots. The48fresh production seeds31001..31048
  remain PLANNED_NOT_EXECUTED. Their powered analysis is likewise NOT_EXECUTED.
  The runner and frozen settings exist; future production analysis/export needs
  separate implementation/QA under the stated v2 plan, never silent v1 pooling.
- V2 full result states, including complete control histories, are included in
  the handoff; redundant finished-run checkpoints remain local in v2/raw/pilot.
  All true-global statistics, per-run outcomes and SHA/path receipts are included.
  The delivered source can reproduce the two runs from their fresh streams.
- R12 approximate bootstrap coverage and near-zero U precision remain limitations.
  No finite-sample exact guarantee or deterministic stationary bias CI exists.
- E1 controlled averaging bridge is NOT_EXECUTED. The homogeneous control
  coefficient is not isolated in real-data state-dependent noise.
- Historical H4 exclusions, H8 discrepancies, original long-horizon H1 arithmetic
  identity deviations remain unresolved; no old numerical outputs were replaced.
- Predictive harm/material utility for broader FL tasks, neural networks,
  heterogeneous objectives, partial participation or other datasets is untested.
- Test-loss intervals cover algorithmic seeds conditional on the fixed test set,
  not population/test-sampling uncertainty or an independent dataset replicate.

The conclusion is INCONCLUSIVE_PRECISION_OR_STATIONARITY, not a scientific
negative based on compute availability. Exact cost and continuation commands
appear in PILOT_AND_BUDGET.md and REPRODUCE.md. No manuscript integration occurred.
