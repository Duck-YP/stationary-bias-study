# Multidimensional homogeneous SCAFFOLD validation

This workstream validates the vector implementation through coefficient, rotation, fixed-step extrapolation, and higher-dimensional studies.

## Commands

Use `python run.py list` to obtain the workstream ID, then run:

```text
python run.py <workstream-id> check
python run.py <workstream-id> smoke
python run.py <workstream-id> formal check
python run.py <workstream-id> formal <matrix> <run|analyze|report>
python run.py <workstream-id> rotation <check|run|report>
python run.py <workstream-id> d5 <check|run|analyze|report>
python run.py <workstream-id> plateau <check|run|analyze|report>
```

Configurations define the matrices, seeds, estimators, and gates.
Formal runners follow the [numerical protocol](../../docs/numerical_protocol.md).

Protocol snapshots used by provenance checks are stored under `artifacts/archive/`.
