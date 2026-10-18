# Missing Items and Audit Limits

- No full freeze-time source snapshot for hash-mismatched historical files; see SOURCE_REVIEW/FROZEN_SOURCE_AVAILABILITY.csv.
- Historical repository artifacts include run/batch tables, not original dense paths, checkpoints or noise draws; those raw originals are unavailable here.
- Original full-round paths/noise draws, within-round crossproducts and per-batch task losses were not saved; cannot infer them from batch means.
- Full primary per-client control means and batch second moments are retained. Per-client temporal batch vectors/final client states require the preserved raw result.npz.
- Original E2/stable post-hoc diagnostic arrays lack some second-moment/local-state summaries; original outputs are retained without fabricated values.
- Original IACT values are batch-projection proxies, not certified ESS; no missing true ESS is marked passed.
- Complete objective/test-loss and data-driven derivative recomputation needs data/training_csr.npz and a9a/a9a.t from original archive; hashes and retrieval URLs retained.
- Full-grid improved-arithmetic production rerun remains NOT RUN; 32 precision-insufficient cells and three long H1 numerical flags remain unchanged.
- LaTeX compilation remains UNVERIFIED_PLATFORM_COMPILER_FAILURE; no new compiler run or successful compilation claimed.
- Optional gamma/1024 extension and E3 shadow were disabled in the frozen protocol, not completed experiments.
