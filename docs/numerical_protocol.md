# Numerical protocol

This document defines the numerical rules shared by all workstreams.
Each workstream defines its research question, estimators, run matrix, seeds, thresholds, stopping rules, and exceptions in its own README, study file, and configuration directory.

## Claim boundary

A passing simulation shows numerical consistency, not mathematical proof. 
A discrepancy requires implementation, configuration, and theorem audits before drawing a scientific conclusion.

## Inferential unit

Each workstream must identify its independent inferential unit and dependence structure before formal execution. 
For chain-based studies, batch means estimate within-chain Monte Carlo uncertainty and are not independent cross-chain replicates.

## Formal execution

1. Load the frozen configuration and validate the run matrix and unique run keys.
2. Initialize the configured random streams and states.
3. Apply warm-up or burn-in when required.
4. Collect data until the precision rule passes or the budget is exhausted.
5. Check model invariants, numerical stability, stationarity, estimator agreement, and workstream-specific gates.
6. Save raw records before deriving summaries, reports, or figures.
7. Build formal output in staging and validate it before replacing a canonical result.

An omitted stage must be documented by the workstream.

## Configuration and provenance

Shared defaults live in `shared/configs/`; workstream settings live in `workstreams/<slug>/configs/`.
The workstream declares its source policy.
Formal provenance records the applicable source commit, dirty state, configuration hashes, matrix identifier, seeds, runtime, platform, and package versions before any output write.

## Controlled overwrite

Result identity, schemas, row counts, run keys, discrete values, and non-numeric scientific fields must match exactly.
Numeric fields also match exactly unless the workstream declares field-level tolerances for bounded floating-point roundoff.
Tolerances must be explicit, tested, and recorded in the overwrite audit.
A failed comparison preserves the canonical result.

Expected-to-change provenance fields may be excluded from scientific comparison but remain recorded in the new provenance and manifest.
