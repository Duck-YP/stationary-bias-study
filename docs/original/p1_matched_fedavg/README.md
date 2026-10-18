# Matched FedAvg versus SCAFFOLD

This workstream uses common random numbers, shared batch boundaries, and paired stopping to attribute stationary-bias coefficient differences.

## Commands

Use `python run.py list` to obtain the workstream ID, then run:

```text
python run.py <workstream-id> check
python run.py <workstream-id> smoke
python run.py <workstream-id> run
python run.py <workstream-id> report
python run.py <workstream-id> plateau check
python run.py <workstream-id> plateau smoke
python run.py <workstream-id> plateau run
python run.py <workstream-id> plateau report
```

`configs/matched_fedavg.yaml` defines the matched matrix.
`configs/fixed_gamma_large_n.yaml` defines the fixed-step large-client extrapolation.
Formal runners follow the [numerical protocol](../../docs/numerical_protocol.md).

The publication snapshot is read-only.
Its exact original configuration and result interpretation are documented in [archive notes](artifacts/archive/original_formal_snapshot/ARCHIVE_NOTES.md).
