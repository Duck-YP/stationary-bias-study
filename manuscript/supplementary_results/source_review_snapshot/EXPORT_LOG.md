# Export Log

- Scope: packaging existing evidence only. No training, optimizer solve, analysis selection change, or public upload.
- The first historical-copy attempt exceeded the Windows path-length limit. Only the newly generated partial export was moved to build_attempt_1_historical_long_paths, outside package staging. Original artifacts were untouched.
- Historical export paths now use short workstream IDs (p0/p1/p2/p3); HISTORICAL_ARTIFACT_INDEX.csv preserves exact original path/hash mappings. No legacy result was selected by outcome.
- Batch control endpoint summaries were checked against engine.py: batch_ctrl_vector is a chunk-endpoint weighted approximation, not an exact temporal integral. The exact primary per-client mean and summed second moments are retained; complete client-by-batch temporal vectors remain in the original raw result.
- Final ZIP integrity checks and extracted analysis-only replay are recorded in EXPORT_QA.md and the adjacent QA CSV/JSON files.
- Executed replay: 69 production cells / 828 production paired runs, plus 28 pilot pairs; 856 primary sum reconstructions bit-exact; 118 coefficient rows, 36 policy/allocation contrasts and 4,317 numeric checks matched with maximum error 0. All 15 regenerated PNGs are pixel-identical to the original figures. No training was executed.
- All 18 byte-identical partition aliases were successfully restored in the extracted QA bundle. Original archive and study source hashes remain unchanged.
