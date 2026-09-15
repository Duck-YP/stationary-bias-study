# SCAFFOLD stationary-bias baseline

This workstream preserves the one-dimensional publication study and its small-step confirmation.

## Commands

Use `python run.py list` to obtain the workstream ID, then run:

```text
python run.py <workstream-id> check
python run.py <workstream-id> smoke
python run.py <workstream-id> run <experiment>
python run.py <workstream-id> report
python run.py <workstream-id> plot
```

Configurations define the matrices and gates.
Publication, confirmation, and smoke artifacts remain isolated.
Shared execution rules are defined in the [numerical protocol](../../docs/numerical_protocol.md).
