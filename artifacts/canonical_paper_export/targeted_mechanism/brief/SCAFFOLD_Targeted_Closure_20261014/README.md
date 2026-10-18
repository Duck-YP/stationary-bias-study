# SCAFFOLD: bounded targeted follow-up

Created 14 October 2026. Planning/execution brief, not a new experimental result.

## Start

Give this folder to the local Codex project that holds the current manuscript and experiment archive. Read CODEX_PROMPT.md first. Reuse the existing code/data where appropriate, but keep all old outputs immutable. The prompt authorizes two narrowly specified new controlled tests, a bounded literature check, and analysis-only review of the existing H=4 evidence. It does not authorize a new real-data study or modification of the master manuscript.

## Files

- CODEX_PROMPT.md: staged instructions, budget/precision safeguards, delivery requirements.
- MODEL_DESIGN.md: a nontrivial T[C]=0 construction, two signed controls, and exact covariance-matched noise laws.
- null_model_reference.py: NumPy reference objective and analytical targets, not a production kernel.
- ANALYTICAL_TARGETS_CHECKED.json / DESIGN_VERIFICATION.json: calculations already checked in this session. No training simulations were run.
- ESTIMATOR_IDENTITY.md: finite-window raw/balance identity and its common-noise paired version.
- LITERATURE_SCOPE.md: bounded primary-source comparison instructions.
- related_work_insert.tex / glasgow2022sharp.bib: proposed Glasgow citation insertion; not applied to the current manuscript.

## Current execution status

Completed here: inspected the delivered source snapshot and existing protocol; checked the proposed objective gradient, Hessian and origin derivatives symbolically; checked analytical targets and discrete noise moments; read the cited Glasgow primary source and prepared a short insertion.

Not completed here: full bounded novelty audit, new stationary simulations, old-data H=4 estimator/window reanalysis, new bootstrap, or manuscript integration. Codex must independently validate the supplied analytical construction.

Default six CPU-hour simulation cap is a proposed engineering budget. It is not an assertion that all runs will fit or have sufficient power; the local new-kernel pilot determines feasibility before production.
