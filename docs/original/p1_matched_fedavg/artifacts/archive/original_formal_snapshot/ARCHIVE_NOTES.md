# Archive notes

## Configuration closure

`supplement/original_run_config.yaml` is the exact configuration blob identified by the recorded source commit and path. `supplement_manifest.json` records its origin and SHA256. Existing run-produced files remain unchanged.

## Status semantics

`falsification_status = INCONSISTENT` means that a finite-setting confidence interval does not cover the asymptotic target. It does not by itself falsify the asymptotic theorem, whose conclusion depends on the configured extrapolation and smaller-step checks.

## Reproduction scope

This archive is an evidence snapshot. Execution requirements are defined in [the repository reproduction policy](../../../../../docs/reproducibility.md).
