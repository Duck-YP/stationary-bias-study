# Source/evidence validation receipt

Validated on 2026-10-09, including finalized manuscript/renderer integration.

- Exact-copy manifest: 339 files, 20,337,825 bytes; all hashes and sizes match.
- Python scientific source: 80 files parsed successfully.
- Supplementary registry: 104 rows; all 69 production cells present.
- Production per-run evidence: all 1,656 algorithm-level rows present, covering
  every cell, both algorithms, and all 12 production seeds without duplicate
  keys. H = 4 and H = 8 cells remain included.
- Saved NPZ archive CRC/readability and CSV/JSON structural checks passed.
- Bounded tests: **3 passed in 1.54 seconds**. They check release integrity,
  closed-form scalar coefficient decomposition, and deterministic Lyapunov /
  matched coefficient identities. They do not perform stochastic simulations.
- Original source/result export: **no training, simulation, optimizer rerun,
  estimator refit or resampling**.
- Compact source/evidence omissions: 28 files, recorded individually by original relative path,
  size, SHA-256 and reason. Original archives remain untouched.

Observed test environment: Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1,
Matplotlib 3.11.2, pytest 9.1.1. The tests used already-installed workspace
dependencies. A clean editable-install validation of the combined public
package has not been performed; the declared PyYAML/pandas dependencies are
needed by additional legacy modules not invoked by these bounded tests.

## Final publication integration

- Seven independently rendered vector-PDF panels, each with PNG and saved-data
  CSV sidecar. No in-program panel merging; six LaTeX subfigure blocks.
- Compiled manuscript: 33 pages, SHA-256
  `9ecdbd9f8e4df1dc0f2649d3d90f17034342c82dc1fdec8892b32c7bc5ac9ef3`.
- Compiled gallery: four pages, SHA-256
  `3407f8138cfa7b16a23fb59f2620beb7fac0f102e71b43bc2844bfb388e8421a`.
- Independent full-workspace numerical preservation: 2,737 checks / zero
  failures. Portable public-input numerical verifier re-executed: 2,646 checks /
  zero failures across ten input CSVs. Its broader original/proof checks remain
  explicitly archived, not re-executed in portable mode.
- Release validator checks 740 saved sidecar values/display transforms without
  fitting. All historical H = 4 observations and exclusion flags are retained.
- Final effective-font audit re-executed from the public script: 14 panel
  inclusions pass, minimum 9.699996948261125 TeX points. Actual body size 10.95
  TeX points; required floor 9. Twelve subcaptions and eight parent captions
  pass; source fonts are embedded, with zero clipped text/raster images.
- Isolated public-renderer replay: all seven sidecars, provenance and PNG
  bytes/pixels match exactly. Seven PDF bytes differ because of TeX font subset
  prefixes, but all vector operator streams, media boxes, normalized font names
  and 216-dpi rendered PDF pixels match. Status `PASS_RENDER_EQUIVALENT` does
  not claim PDF byte identity.
- Public manuscript/source-review integration: six archive/privacy omissions
  and four metadata-only variants recorded individually. Scientific TeX,
  source code and CSV results are not changed.
- Git-byte audit: 536 CRLF text files found; nine representative text-type Git
  filter/no-filter hashes agree. `.gitattributes` disables newline normalization
  to preserve archived source/result hashes across Git checkouts.

The complete public-file manifest checks closure, size, hashes and absence of
machine-local paths/large archives. No commit or push was performed. These
receipts establish artifact fidelity, not theorem correctness or resolution of
the recorded finite-grid scientific limitations.

Final manifest closure: **729 public files, 42,719,283 bytes**, excluding only
the complete manifest itself and this receipt (runtime caches are not packaged).
The 339 original scientific/evidence copies and 362 publication-integration
copies have separate provenance manifests. Final release validation passed after
integration; the three bounded tests passed without writing cache artifacts.
