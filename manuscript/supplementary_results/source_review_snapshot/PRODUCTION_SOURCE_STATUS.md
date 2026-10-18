# Production Source Availability

Current uncommitted study source and the originally delivered source.zip snapshot are both retained.
FROZEN_SOURCE_AVAILABILITY.csv compares each recorded freeze-time hash to obtainable files.
Exact matching files are copied into available_frozen_source. Numerical kernels/model/data/engine
match freeze-time hashes. Changed historical analysis/CLI/test files are not silently substituted.
A complete freeze-time source tree/patch for unavailable hashes cannot be recovered from this
untracked study; no fabricated snapshot is supplied. Current reporting/replay source is separately versioned.
Legacy repository code is not imported by the supplementary implementation.
