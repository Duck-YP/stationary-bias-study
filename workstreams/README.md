# Workstreams

Each workstream owns one research question, its configuration, implementation, tests, and artifacts.
Use `python run.py list` for the current registry and CLI keys.

## Naming contract

- Slugs describe the research question and remain stable.
- Configurations use descriptive matrix or experiment names.
- Formal results live under `artifacts/formal/<matrix-id>/`.
- Smoke results live under `artifacts/smoke/`.
- Archives are read-only evidence and never formal-run targets.

Research scope is summarized in [the roadmap](ROADMAP.md).
Shared lifecycle rules are defined in [the numerical protocol](../docs/numerical_protocol.md).
