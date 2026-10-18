# Data and historical archives

## a9a source and preprocessing

The authoritative download entry is the [LIBSVM binary-classification a9a page](https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary.html#a9a), checked on 18 October 2026. It identifies the Adult-derived dataset, 32,561 training observations, 16,281 test observations and a declared space of 123 features. Download links are [a9a](https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary/a9a) and [a9a.t](https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary/a9a.t).

The study's historical `artifacts/canonical_paper_export/supplementary/DATA_MANIFEST.json` records retrieval on 9 October 2026 and these exact bytes:

| File | SHA-256 |
| --- | --- |
| `a9a` | `f5d5ffd8d865ff41328e7ee043e4b020816914ff6843ff15b98905ddbedce906` |
| `a9a.t` | `1f448a153f0320399a7e40836eb207655b0bde0f21fc941cc472193daa9f5de9` |
| Processed `training_csr.npz` | `5bab537d3c034a00afd29942e5f4ac436f40849ea8b82f925af3eb90a1430b6d` |
| `membership.npz` | `e8ab826501e53efdd3780cfe1fddc38dd7ddf20d1bcca1f41134d2b0df053536` |

The original raw files and full processed data/partition matrices are not redistributed in this compact repository. Dataset redistribution permission was not established by this publication task. The upstream download source and historical checksums allow a reader to identify the inputs; software licensing is a separate matter.

The executed preprocessing is preserved in `src/study/data.py`:

1. Read LIBSVM feature indices into a 123-column float64 sparse matrix and map labels -1/+1 to 0/1. The test file omits feature 123, but shares the declared 123-dimensional feature space.
2. Divide each row by `max(1, L2 norm)`, then append an intercept of one, producing 124 parameters. Logistic regularization is lambda=0.01 on all 124 coordinates, including the intercept.
3. Use `numpy.random.default_rng(20261009).permutation(32561)`; retain the first 32,512 rows and exclude the other 49. Membership IDs refer to zero-based original training rows.
4. Generate shared-objective clients by replicating all retained rows. For disjoint IID clients, permute retained rows and reshape into equal client groups. For label-skew clients, separately permute each label group, form 2N shards, permute shards and allocate two per client.
5. The frozen protocol records partition seeds 4101, 4102, 4103 (shared-objective cells use the recorded zero marker), production seeds 20001–20012, and pilot seeds 10001–10004. Cell-level N, minibatch sizes, step sizes, H and partition IDs are in `configs/supplementary/PROTOCOL_FROZEN.json`.

The same source records the reference optimizer and cross-check, Hessian/noise matrices and a frozen descriptive direction. `optimizer_certificates.json` and `reference_optimizers.npz` preserve compact reference evidence. Repeating preprocessing or optimizer fitting is outside the saved-artifact regeneration commands. The test data support held-out loss reporting; they are not used to choose the training subset.

## Archive register

These are exact historical archive identities, not download promises. **No public download endpoint for any archive below has been established.** Their public-retrievability status is therefore **not established**; the ZIPs themselves are excluded. This does not prevent saved-artifact regeneration from the compact derivatives in the checkout.

Checksums below come from the existing historical package index, archive QA records and import manifests inspected during release preparation. The publication file manifest separately hashes current exported files. `canonical/` abbreviates `artifacts/canonical_paper_export/`.

| Exact archive filename | SHA-256 | Scientific role and compact derivative |
| --- | --- | --- |
| `REVIEW_CORE.zip` | `0f57ece1ad5939e379d7742f05a69899c14d27b70549e410e0a87c4c63cb091d` | Saved coefficient/affine/logistic summaries and diagnostics; canonical/supplementary/ and manuscript/supplementary_results/. |
| `REVIEW_CORE_E3_DIAGNOSTICS_R0.zip` | `b9fa259d72ed92845d47a7ba6ca0fcec018d70130b357cba5e51543c0b30c700` | Full client-membership, gradient, Hessian and noise matrices for the named partition regime; compact partition diagnostics and reference summaries in canonical/supplementary/. |
| `REVIEW_CORE_E3_DIAGNOSTICS_R1.zip` | `3a77b0ce6bcce816af9d42252badf676a00632824f76bac3510e646bc41dfd2d` | Full client-membership, gradient, Hessian and noise matrices for the named partition regime; compact partition diagnostics and reference summaries in canonical/supplementary/. |
| `REVIEW_CORE_E3_DIAGNOSTICS_R2.zip` | `97d8dbf657889cc4eedfd1c0e55ae97342c495de53f910d5ca17e90997727ea4` | Full client-membership, gradient, Hessian and noise matrices for the named partition regime; compact partition diagnostics and reference summaries in canonical/supplementary/. |
| `SOURCE_REVIEW.zip` | `0f26743d91095fa7c1cb6b8cc0d3c9b06dc5ab7dc6bc32f93359eaca4c392818` | Delivered/current source, recovered frozen files and environment; manuscript/supplementary_results/source_review_snapshot/ and src/study/. |
| `AUDIT_BATCHES_E1.zip` | `b5bf3ca442093f992452c7f8e58c299119ee70ac751c6603dc0e6fe8e881e4c9` | Controlled Cartesian-grid global/balance batches; canonical/supplementary/per_run_estimates.csv, fitted_coefficients.csv and full_results.csv. |
| `AUDIT_BATCHES_E2.zip` | `636a1b8a4fdf998d705a01de05d7b5c882d5c239a76cdba304c9df46d6a23c33` | Affine-control paired batches; canonical/supplementary/tables/E2_exact_checks.csv and summaries. |
| `AUDIT_BATCHES_E3_R0.zip` | `ba21ea02320be1981bad19f3850ae505ef4c62346ef7f8d4d802f9c57e44de1a` | Logistic batches and aligned pairs for the named partition regime; canonical/supplementary/ tables, per-run summaries and manuscript temporal-averaging evidence. |
| `AUDIT_BATCHES_E3_R1_01.zip` | `dc69f8dab1914df732ed8fc348145269631a8cecb4dad0ade0c641a364c9fcfa` | Logistic batches and aligned pairs for the named partition regime; canonical/supplementary/ tables, per-run summaries and manuscript temporal-averaging evidence. |
| `AUDIT_BATCHES_E3_R1_02.zip` | `e333a3188237acf2f734b77fe1c5f448a30e49e46df850c3c66b62fb6568664a` | Logistic batches and aligned pairs for the named partition regime; canonical/supplementary/ tables, per-run summaries and manuscript temporal-averaging evidence. |
| `AUDIT_BATCHES_E3_R2_01.zip` | `633714289f8e5319830d527704c2eef7de48d42d4c4693ff8f205f659cfe17b2` | Logistic batches and aligned pairs for the named partition regime; canonical/supplementary/ tables, per-run summaries and manuscript temporal-averaging evidence. |
| `AUDIT_BATCHES_E3_R2_02.zip` | `cf317cb9201c15e90c63f1f2bf687a39cbe53ad5cbfa7f0c53bbdc0e693a14bf` | Logistic batches and aligned pairs for the named partition regime; canonical/supplementary/ tables, per-run summaries and manuscript temporal-averaging evidence. |
| `AUDIT_BATCHES_PILOTS.zip` | `000f5f8be96600745917f524d452baff9c12ed40a441d7c62da6323b3ae79c9f` | Separate pilot batches; compact pilot/temporal diagnostics retained in canonical/supplementary/. |
| `AUDIT_BATCHES_POSTHOC.zip` | `44238668cdffe1be8ccbad3a2ea9c8ca3679ce12b4248628831ad959bda5e93d` | Post-hoc supplementary batches; compact saved sensitivity and diagnostic summaries in canonical/supplementary/. |
| `SIGNIFICANCE_E4_HANDOFF.zip` | `8a1d9e0e5a4d8f05c117a998a4d780075c85583fc7b6065a1c7388b0a33b8f54` | Temporal averaging handoff/source and replay evidence; manuscript/supplementary_results/E4/ arrays, intervals, protocols, diagnostics and source_snapshot/. |
| `SOURCE_E4.zip` | `50eb7c9ba9b0a2630bc662ce6ccb0c1941a3220045c132d7a328a89731168e9a` | Temporal averaging handoff/source and replay evidence; manuscript/supplementary_results/E4/ arrays, intervals, protocols, diagnostics and source_snapshot/. |
| `E5_ANALYTIC_BRIDGE_HANDOFF.zip` | `f76483fa69c5944878033383f91a7bbde40b28b894eda1be44cd466d4420e711` | Full-vector post-hoc proxy handoff/source and audit; manuscript/supplementary_results/E5/ vectors, summaries, sensitivities and source_snapshot/. |
| `E5_SOURCE_AUDIT.zip` | `75e9e2b9e70c8ad8ca79fbd1aaf1c3bd2afaad0a769fd0750a4c8c27352d5ecc` | Full-vector post-hoc proxy handoff/source and audit; manuscript/supplementary_results/E5/ vectors, summaries, sensitivities and source_snapshot/. |
| `TARGETED_MECHANISM_REVIEW.zip` | `d65425d30237a646371d76bfb664d72109528f40ca6b8d76296a283142ce563a` | Extracted source/evidence retained at `artifacts/canonical_paper_export/targeted_mechanism`; current omission manifests identify publication cleanup. |
| `SOURCE_TARGETED_MECHANISM.zip` | `7be6a3c046792a83187e90c0639b135db3a448f34c5fa06239fa9312d691a8d4` | Extracted source/evidence retained at `src/targeted_mechanism_snapshot`; current omission manifests identify publication cleanup. |
| `SCAFFOLD_Targeted_Mechanism_Independent_Audit_20261015.zip` | `9507bbf2bb652e418604868c80ad5e727eeb409200982ec52212b4f1dc9d0546` | Extracted source/evidence retained at `docs/targeted_mechanism/independent_audit`; current omission manifests identify publication cleanup. |

The V2 manuscript source archive is `Characterizing_Client_Independent_Stationary_Bias_for_SCAFFOLD_and_FedAvg_in_Federated_Learning_V2.zip`, SHA-256 `bf0ddf18830e323bdabb57e12effb959d21d8c9f76f93fc3b2d68df16f9f8f70`. The earlier integration archive is `SCAFFOLD_Targeted_Mechanism_Integrated_20261015.zip`, SHA-256 `10ec90589e0f1ba73926cea7d6b17e03e3885191a313af109f46acf398cf41cc`. Their role is manuscript/evidence handoff, not a replacement for the finalized PDF hash. Current sources and evidence have been exported; neither archive has an established public download here.

The original scalar/2D/5D studies also have omitted `batch_summary.csv`, `paired_batch_summary.csv`, `bootstrap_intercepts.csv` and `paired_bootstrap_intercepts.csv` files in their experiment-specific directories. Their exact relative paths, byte sizes and SHA-256 values are recorded in `docs/manifests/COMPACT_OMISSIONS.csv`. No verified enclosing archive filename is available for all of those files, so no archive identity is invented. Compact setting/fit/residual summaries remain in `artifacts/canonical_paper_export/original/` and support the historical figure replay. Recomputing every original estimator/bootstrap requires the omitted inputs.

The targeted local checkpoint/result files are enumerated by `artifacts/canonical_paper_export/targeted_mechanism/LOCAL_ARTIFACT_MANIFEST.json`; its identities describe original local files, not files promised in this checkout. Compact pilot/production per-run and window summaries remain. Some original audit starting states and individual noise statistics were not saved or recovered and cannot be reconstructed from mean summaries alone.

## What remains reproducible without the archives

The public saved-data routes rebuild all nine numbered-figure panels, reconstruct supported computational table entries, check the saved temporal-averaging/vector algebra, and exercise bounded scientific identities. They require neither the archive ZIPs nor raw a9a downloads. The current table generator explicitly records partial or unresolved historical cells rather than refitting them.

Full training/simulation, reconstruction of all historical raw-batch identities, new bootstrap distributions, and complete restart workflows are outside that scope. The archive hashes above identify evidence that existed; they do not imply full-study reproduction from a fresh checkout. See [Reproducibility scope](REPRODUCIBILITY_SCOPE.md) and [Result provenance](RESULT_PROVENANCE.md).
