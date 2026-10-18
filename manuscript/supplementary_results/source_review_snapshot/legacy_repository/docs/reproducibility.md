# Reproducibility scope

Tracked artifact directories are evidence snapshots, not standalone execution environments.
Reproduction uses the full repository at the source commit recorded in provenance.

From the repository root:

1. Check out the recorded commit.
2. Install the environment from `requirements.lock`.
3. Run `python run.py check` and `python run.py test`.
4. Run the workstream command recorded by its README and configuration.

Manifests and provenance identify inputs and outputs. 
Stored test logs are not authoritative because they can become stale; validation is rerun against the recorded source instead.
