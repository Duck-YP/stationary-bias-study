# Multidimensional matched FedAvg attribution

This workstream studies whether homogeneous multidimensional FedAvg has the same client-independent local-update stationary-bias coefficient as the local component of matched SCAFFOLD.

The implementation has two descriptive components:

- `fedavg-coefficient` estimates the multidimensional FedAvg coefficient.
- `matched-attribution` uses paired SCAFFOLD and FedAvg chains with index-keyed common random numbers to isolate the control contribution.

## Entry points

```text
python run.py p3 check

python run.py p3 fedavg-coefficient check
python run.py p3 fedavg-coefficient smoke
python run.py p3 fedavg-coefficient formal check
python run.py p3 fedavg-coefficient formal primary run
python run.py p3 fedavg-coefficient formal primary analyze
python run.py p3 fedavg-coefficient formal primary report
python run.py p3 fedavg-coefficient formal h4-small-step run
python run.py p3 fedavg-coefficient formal h4-small-step analyze
python run.py p3 fedavg-coefficient formal h4-small-step report

python run.py p3 matched-attribution check
python run.py p3 matched-attribution smoke
python run.py p3 matched-attribution formal check
python run.py p3 matched-attribution formal primary run
python run.py p3 matched-attribution formal primary analyze
python run.py p3 matched-attribution formal primary report
python run.py p3 matched-attribution formal h4-small-step run
python run.py p3 matched-attribution formal h4-small-step analyze
python run.py p3 matched-attribution formal h4-small-step report
```

Protocol checks validate configuration without running simulations.
Formal runs require clean committed source and install results through a controlled staging transaction.
Reproduction replaces a canonical result only when its raw scientific fields agree with the existing result.

## Theory

[Multidimensional matched-attribution derivation](theory/multidimensional_matched_attribution_derivation.md)

## Scope

The model uses homogeneous clients, full participation, fixed dimension, fixed local-step count, additive bounded noise, constant step size, and the stationary regime.

The workstream does not cover heterogeneous clients, growing local-step counts, state-dependent noise, dimensions outside the configured matrices, the full finite-client second-order coefficient, or a global algorithm ranking.
Numerical outcomes are falsification and consistency checks rather than mathematical proofs.
