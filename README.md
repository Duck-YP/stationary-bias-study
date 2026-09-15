# Stationary Bias Study

This repository organizes numerical research by workstream.
Simulations are falsification and diagnostic tools, not mathematical proofs.

## Quick start

```text
python -m venv .venv
python -m pip install -r requirements.lock
python run.py list
python run.py check
python run.py test
```

Use `python run.py list` to discover registered workstreams and commands.
Formal runs follow the source and artifact policy declared by the selected workstream.

## Layout

```text
run.py                              repository CLI
shared/configs/                     shared numerical defaults
workstreams/<slug>/                 research definitions and artifacts
src/stationary_bias/core/           stable shared capabilities
src/stationary_bias/workstreams/    workstream implementations
tests/                              shared and workstream tests
docs/                               repository-level contracts
```

Shared architecture belongs in `core/`; research-specific code, configuration, tests, and outputs remain within one workstream.
Smoke and formal outputs use separate paths.

See [project structure](docs/project_structure.md), [numerical protocol](docs/numerical_protocol.md), and [reproducibility scope](docs/reproducibility.md).
