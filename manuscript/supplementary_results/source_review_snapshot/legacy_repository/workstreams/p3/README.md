# Multidimensional matched FedAvg attribution

This workstream studies whether homogeneous multidimensional FedAvg has the same client-independent local-update stationary-bias coefficient as the local component of matched SCAFFOLD.

It has two components:

- `fedavg-coefficient` estimates the multidimensional FedAvg coefficient.
- `matched-attribution` uses paired SCAFFOLD and FedAvg chains with index-keyed common random numbers to isolate the control contribution.

## Commands

Use `python run.py list` to obtain the workstream ID, then run:

```text
python run.py <workstream-id> check

python run.py <workstream-id> fedavg-coefficient check
python run.py <workstream-id> fedavg-coefficient smoke
python run.py <workstream-id> fedavg-coefficient formal check
python run.py <workstream-id> fedavg-coefficient formal <primary|h4-small-step> <run|analyze|report>

python run.py <workstream-id> matched-attribution check
python run.py <workstream-id> matched-attribution smoke
python run.py <workstream-id> matched-attribution formal check
python run.py <workstream-id> matched-attribution formal <primary|h4-small-step> <run|analyze|report>
python run.py <workstream-id> matched-attribution diagnostic
```

Configurations under `configs/` define the matrices, seeds, estimators, stopping rules, and gates.
Canonical results are isolated by matrix ID under `artifacts/formal/`.
The diagnostic command rebuilds deterministic analyses from existing matched-attribution artifacts without running a new production simulation.
Formal runners follow the [numerical protocol](../../docs/numerical_protocol.md).

## Theory

[Multidimensional matched-attribution derivation](theory/multidimensional_matched_attribution_derivation.md)
