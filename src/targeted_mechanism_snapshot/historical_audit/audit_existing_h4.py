"""Read-only reconstruction of the existing H=4 Cartesian study. No simulation calls.

Run from the repository root with NumPy/SciPy available. Outputs stay beside this file.
Historical source is read as text/ZIP bytes, never imported or executed.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import platform
import sys
import zipfile
import numpy as np
from scipy.stats import t
from scipy.linalg import solve_continuous_lyapunov

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
MAN = ROOT / "manuscript/supplementary_results"
DATA = ROOT / "supplementary_study/results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF"
SEEDS = list(range(20001, 20013))
A = np.array([[1.2, .2], [.2, 1.]])
C = np.array([[1., .2], [.2, .7]])
U = np.ones(2) / np.sqrt(2.)
TC = .25 * U * (U @ C @ U)
BASE = -np.linalg.solve(A, TC)
B11 = -.5 * np.linalg.solve(A, .25 * U * (U @ solve_continuous_lyapunov(A, C) @ U))
TARGETS = {"scaffold": 19 / 16 * BASE, "fedavg": 3 / 4 * BASE,
           "matched_difference": 7 / 16 * BASE, "raw_minus_balance": np.zeros(2)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_csv(name, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def ci(x, family=1):
    x = np.asarray(x)
    se = np.std(x, ddof=1, axis=0) / np.sqrt(len(x))
    hw = t.ppf(1 - .05 / (2 * family), len(x) - 1) * se
    m = x.mean(axis=0)
    return m, se, m - hw, m + hw


def summary(x, **meta):
    m, se, lo, hi = ci(x)
    _, _, alo, ahi = ci(x, 2)
    return [dict(**meta, coordinate=j, runs=len(x), estimate=m[j], paired_run_se=se[j],
                 ci_lower=lo[j], ci_upper=hi[j], ci_width=hi[j] - lo[j],
                 coordinate_bonferroni_lower=alo[j], coordinate_bonferroni_upper=ahi[j]) for j in range(2)]


def observables(raw, bal, g, N):
    values = {}
    for source, means in (("raw_post", raw), ("balance", bal)):
        for a, algorithm in enumerate(("scaffold", "fedavg")):
            values[source, algorithm, "mean"] = means[a]
            values[source, algorithm, "normalized_C"] = (means[a] - g / N * B11) / g**2
        values[source, "matched_difference", "mean"] = means[0] - means[1]
        values[source, "matched_difference", "normalized_D"] = (means[0] - means[1]) / g**2
    for a, algorithm in enumerate(("scaffold", "fedavg")):
        values["raw_minus_balance", algorithm, "mean"] = raw[a] - bal[a]
        values["raw_minus_balance", algorithm, "normalized_gap"] = (raw[a] - bal[a]) / g**2
    values["raw_minus_balance", "matched_difference", "mean"] = (raw[0] - raw[1]) - (bal[0] - bal[1])
    values["raw_minus_balance", "matched_difference", "normalized_gap"] = values["raw_minus_balance", "matched_difference", "mean"] / g**2
    return values


def source_audit(conf):
    rows = []
    zpath = MAN / "SOURCE_REVIEW.zip"
    with zipfile.ZipFile(zpath) as z:
        members = set(z.namelist())
        prefixes = ["SOURCE_REVIEW/available_frozen_source/", "SOURCE_REVIEW/supplementary_study/", "SOURCE_REVIEW/delivered_source_snapshot/"]
        for name, expected in conf["source_hashes"].items():
            for prefix in prefixes:
                member = prefix + name
                actual = hashlib.sha256(z.read(member)).hexdigest() if member in members else ""
                rows.append(dict(scope=prefix, file=name, expected_frozen_sha256=expected,
                                 actual_sha256=actual, status="MISSING" if not actual else "MATCH" if actual == expected else "DIFFERS"))
            p = ROOT / "supplementary_study" / name
            actual = sha(p) if p.exists() else ""
            rows.append(dict(scope="local_supplementary_study", file=name, expected_frozen_sha256=expected,
                             actual_sha256=actual, status="MISSING" if not actual else "MATCH" if actual == expected else "DIFFERS"))
        metadata = dict(zip_path=str(zpath.relative_to(ROOT)), sha256=sha(zpath), member_count=len(members),
                        available_prefixes=sorted({"/".join(n.split("/")[:2]) for n in members}),
                        available_frozen_files=sorted(n for n in members if n.startswith(prefixes[0])),
                        archive_crc_error=z.testzip(), historical_commit_verified=False,
                        historical_commit_note="SOURCE_MANIFEST imported_repository_base_commit is a legacy import label, not a recovered supplementary production commit.")
    write_csv("historical_source_hash_audit.csv", rows)
    write_json("historical_source_inventory.json", metadata)
    return rows, metadata


def main():
    conf = json.loads((MAN / "PROTOCOL_FROZEN.json").read_text())
    cells = sorted([c for c in conf["cells"] if c["family"] == "E1" and c["H"] == 4 and "E1b" in c["roles"]], key=lambda c: (c["N"], c["gamma"]))
    assert len(cells) == 9
    source_rows, source_meta = source_audit(conf)
    inventory, perrun, identity, endpoints, batches, crosscheck, input_hashes = [], [], [], [], [], [], []
    grouped, retained = {}, {}
    with (MAN / "per_run_estimates.csv").open(newline="", encoding="utf-8-sig") as f:
        published_runs = {(r["cell_id"], int(r["seed"]), r["algorithm"]): r for r in csv.DictReader(f)}
    azip_path = ROOT / "review_exports/20261009/AUDIT_BATCHES_E1.zip"
    azip = zipfile.ZipFile(azip_path) if azip_path.exists() else None
    archive_names = set(azip.namelist()) if azip else set()
    archive_mismatches, archive_comparison = [], []
    for c in cells:
        cid, N, g = c["id"], c["N"], c["gamma"]
        sched = c["schedule"]
        p = np.eye(2) - g * A
        ph = np.linalg.matrix_power(p, 4)
        b = np.eye(2) - ph
        sh = sum(np.linalg.matrix_power(p, h) for h in range(4))
        for seed in SEEDS:
            path = DATA / "raw/production" / cid / f"seed_{seed}/result.npz"
            runpath = path.with_name("run.json")
            r = dict(np.load(path, allow_pickle=False))
            runmeta = json.loads(runpath.read_text())
            assert runmeta["schedule"] == sched
            assert int(r["seed"]) == seed
            assert np.all(r["batch_count"] == sched["batch_length"])
            file_hash = sha(path)
            archive_member = "AUDIT_BATCHES/" + path.relative_to(DATA).as_posix()
            zip_hash = hashlib.sha256(azip.read(archive_member)).hexdigest() if archive_member in archive_names else ""
            if zip_hash:
                compact = dict(np.load(io.BytesIO(azip.read(archive_member)), allow_pickle=False))
                common = sorted(set(r) & set(compact))
                changed = [k for k in common if not np.array_equal(r[k], compact[k])]
                if changed:
                    archive_mismatches.append(dict(member=archive_member, changed_arrays=changed))
                archive_comparison.append(dict(cell_id=cid, seed=seed, original_sha256=file_hash,
                                               compact_sha256=zip_hash, byte_identical=zip_hash == file_hash,
                                               common_arrays=len(common), changed_common_arrays=";".join(changed),
                                               compact_added_arrays=";".join(sorted(set(compact) - set(r))),
                                               compact_omitted_arrays=";".join(sorted(set(r) - set(compact))),
                                               status="REPACKAGED_SHARED_ARRAYS_IDENTICAL" if not changed else "ARRAY_MISMATCH"))
            input_hashes.extend([dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size, sha256=file_hash,
                                      matching_archive_member=archive_member if zip_hash else "", archive_match=zip_hash == file_hash if zip_hash else "MISSING"),
                                 dict(path=runpath.relative_to(ROOT).as_posix(), bytes=runpath.stat().st_size, sha256=sha(runpath))])
            inventory.append(dict(cell_id=cid, N=N, gamma=g, H=4, seed=seed, batches=len(r["batch_count"]),
                                  primary_batches=int(r["primary_batches"]), primary_rounds=int(r["samples"]), burn_rounds=sched["burn"],
                                  batch_length=sched["batch_length"], raw_alignment="POST_ROUND", has_batch_endpoints=True,
                                  has_burn_end_startpoint=False, has_eta_summary=False, has_round_recursion_residual=False,
                                  max_zero_sum=float(r["max_zero_sum"]), max_relative_zero_sum=float(r["max_relative_zero_sum"]),
                                  source_hash=file_hash, manuscript_source_hash_match=published_runs[cid, seed, "scaffold"]["raw_sha256"] == file_hash))
            for k in range(len(r["batch_count"])):
                for a, alg in enumerate(("scaffold", "fedavg")):
                    for j in range(2):
                        batches.append(dict(cell_id=cid, N=N, gamma=g, seed=seed, batch_index=k, algorithm=alg, coordinate=j,
                                            round_start=sched["burn"] + k * sched["batch_length"], round_end_exclusive=sched["burn"] + (k + 1) * sched["batch_length"],
                                            count=int(r["batch_count"][k]), balance_sum=r["batch_sum"][k, a, j], raw_post_sum=r["batch_raw_sum"][k, a, j],
                                            endpoint_x=r["snapshot"][k, a, j]))
            windows = [("primary", 0, 64), ("first_half", 0, 32), ("last_half", 32, 64), ("endpoint_available_tail", 1, 64)]
            if len(r["batch_count"]) == 133:
                windows += [("2x_burn", 5, 69), ("2x_tail", 0, 128), ("2x_burn_tail", 5, 133)]
            for window, lo, hi in windows:
                count = int(r["batch_count"][lo:hi].sum())
                raw = r["batch_raw_sum"][lo:hi].sum(0) / count
                bal = r["batch_sum"][lo:hi].sum(0) / count
                values = observables(raw, bal, g, N)
                if lo:
                    raw_pre = raw - (r["snapshot"][hi-1] - r["snapshot"][lo-1]) / count
                    for a, alg in enumerate(("scaffold", "fedavg")):
                        values["raw_pre_reconstructed", alg, "mean"] = raw_pre[a]
                        values["raw_pre_reconstructed", alg, "normalized_C"] = (raw_pre[a]-g/N*B11)/g**2
                    values["raw_pre_reconstructed", "matched_difference", "mean"] = raw_pre[0]-raw_pre[1]
                    values["raw_pre_reconstructed", "matched_difference", "normalized_D"] = (raw_pre[0]-raw_pre[1])/g**2
                retained[cid, seed, window] = values
                for (est, alg, estimand), value in values.items():
                    grouped.setdefault((cid, N, g, window, est, alg, estimand), []).append(value)
                    for j in range(2):
                        perrun.append(dict(cell_id=cid, N=N, gamma=g, seed=seed, window=window,
                                           batch_start=lo, batch_stop=hi, rounds=count, estimator=est, algorithm=alg,
                                           estimand=estimand, coordinate=j, value=value[j]))
                for a, alg in enumerate(("scaffold", "fedavg")):
                    for j in range(2):
                        endpoints.append(dict(cell_id=cid, N=N, gamma=g, seed=seed, window=window,
                                              algorithm=alg, coordinate=j, start_round=sched["burn"] + lo * sched["batch_length"],
                                              end_round=sched["burn"] + hi * sched["batch_length"], start_x=r["snapshot"][lo - 1, a, j] if lo else "",
                                              end_x=r["snapshot"][hi - 1, a, j], start_available=bool(lo), end_available=True,
                                              raw_alignment="POST_ROUND"))
                if window == "primary":
                    for a, alg in enumerate(("scaffold", "fedavg")):
                        pub = published_runs[cid, seed, alg]
                        crosscheck.append(dict(cell_id=cid, seed=seed, algorithm=alg,
                                               balance_vs_saved_max_abs=float(np.max(abs(bal[a] - r["mean"][a]))),
                                               raw_vs_saved_max_abs=float(np.max(abs(raw[a] - r["raw_mean"][a]))),
                                               balance_vs_manuscript_max_abs=float(np.max(abs(bal[a] - json.loads(pub["mean_vector"])))),
                                               raw_vs_manuscript_max_abs=float(np.max(abs(raw[a] - json.loads(pub["raw_mean_vector"]))))))
                if lo:
                    delta = (r["snapshot"][hi-1, 0] - r["snapshot"][hi-1, 1]) - (r["snapshot"][lo-1, 0] - r["snapshot"][lo-1, 1])
                    gap = (raw[0] - raw[1]) - (bal[0] - bal[1])
                    lhs = b @ gap
                    rhs = -ph @ delta / count
                    resid = lhs - rhs
                    pre_lhs = b @ ((raw_pre[0]-raw_pre[1])-(bal[0]-bal[1]))
                    pre_rhs = -delta / count
                    # A conservative bound on the ignored nonzero-control-mean term.
                    control_bound = g * np.linalg.norm(sh, 2) * float(r["max_zero_sum"]) / N
                    for j in range(2):
                        identity.append(dict(cell_id=cid, N=N, gamma=g, seed=seed, window=window, coordinate=j, rounds=count,
                                             status="RECONSTRUCTIBLE_PAIRED_POST_IDENTITY", lhs=lhs[j], endpoint_rhs=rhs[j], residual=resid[j],
                                             reconstructed_pre_lhs=pre_lhs[j], pre_endpoint_rhs=pre_rhs[j], pre_identity_residual=pre_lhs[j]-pre_rhs[j],
                                             raw_minus_balance_normalized=gap[j] / g**2, endpoint_correction_normalized=np.linalg.solve(b, rhs)[j] / g**2,
                                             residual_on_normalized_mean_scale=np.linalg.solve(b, resid)[j] / g**2,
                                             control_sum_residual_bound=control_bound,
                                             residual_within_control_bound=abs(resid[j]) <= control_bound,
                                             missing_round_residual=True))
                else:
                    identity.append(dict(cell_id=cid, N=N, gamma=g, seed=seed, window=window, coordinate="", rounds=count,
                                         status="NOT_RECONSTRUCTIBLE_FROM_AVAILABLE_OUTPUTS", reason="start endpoint at burn end was not stored; not replaced by zero"))
    if azip:
        azip.close()
    input_hashes += [dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size, sha256=sha(p)) for p in
                    [MAN / "PROTOCOL_FROZEN.json", MAN / "SOURCE_MANIFEST.json", MAN / "per_run_estimates.csv", MAN / "fitted_coefficients.csv", MAN / "SOURCE_REVIEW.zip", azip_path] if p.exists()]
    grids = []
    for key, vals in grouped.items():
        cid, N, g, window, est, alg, estimand = key
        grids += summary(vals, cell_id=cid, N=N, gamma=g, window=window, estimator=est, algorithm=alg, estimand=estimand)
    changes = []
    for c in cells:
        for window in ("last_half_minus_first_half", "2x_burn_minus_primary", "2x_tail_minus_primary", "2x_burn_tail_minus_primary"):
            win1, win0 = ("last_half", "first_half") if window.startswith("last_half") else (window.replace("_minus_primary", ""), "primary")
            if (c["id"], SEEDS[0], win1) not in retained:
                continue
            for key in retained[c["id"], SEEDS[0], "primary"]:
                vals = np.array([retained[c["id"], s, win1][key] - retained[c["id"], s, win0][key] for s in SEEDS])
                est, alg, estimand = key
                changes += summary(vals, cell_id=c["id"], N=c["N"], gamma=c["gamma"], window_contrast=window,
                                   estimator=est, algorithm=alg, estimand=estimand)
    # Reproduce the historical seed-label fit exactly; also provide a bootstrap that
    # resamples independent cells independently (while preserving all within-run vectors).
    fits, fit_runs, replay = [], [], []
    published_fit = {(r["fit"], int(r["term"]), int(r["coordinate"])): r for r in csv.DictReader((MAN / "fitted_coefficients.csv").open(newline="", encoding="utf-8-sig"))}
    obskeys = [(est, alg, "normalized_D" if alg == "matched_difference" else "normalized_C")
               for est in ("balance", "raw_post") for alg in ("scaffold", "fedavg", "matched_difference")]
    obskeys += [("raw_minus_balance", alg, "normalized_gap") for alg in ("scaffold", "fedavg", "matched_difference")]
    for window in ("primary", "first_half", "last_half", "endpoint_available_tail"):
        for grid, use in [("primary", cells), ("drop_max_gamma", [c for c in cells if c["gamma"] < 1/128]), ("drop_N32", [c for c in cells if c["N"] != 32])]:
            X = np.array([[1, c["gamma"], 1/c["N"]] for c in use])
            pinv = np.linalg.pinv(X)
            rng = np.random.default_rng(61009)
            legacy_idx = rng.integers(0, len(SEEDS), size=(2000, len(SEEDS)))
            rng = np.random.default_rng(26101404)
            independent_idx = rng.integers(0, len(SEEDS), size=(2000, len(use), len(SEEDS)))
            for est, alg, estimand in obskeys:
                yy = np.stack([np.stack([retained[c["id"], s, window][est, alg, estimand] for c in use]) for s in SEEDS])
                co = np.array([np.linalg.lstsq(X, y, rcond=None)[0] for y in yy])
                residuals = yy - np.einsum("ct,rtj->rcj", X, co)
                legacy_boot = co[legacy_idx].mean(1)
                independent_cell_means = np.stack([yy[independent_idx[:, k], k].mean(1) for k in range(len(use))], axis=1)
                independent_boot = np.einsum("tc,bcj->btj", pinv, independent_cell_means)
                for s, sr in zip(SEEDS, co):
                    for term in range(3):
                        for j in range(2):
                            fit_runs.append(dict(window=window, grid=grid, estimator=est, algorithm=alg, estimand=estimand, seed=s,
                                                 term=term, coordinate=j, coefficient=sr[term, j]))
                for term in range(3):
                    m, se, lo, hi = ci(co[:, term]); _, _, alo, ahi = ci(co[:, term], 6)
                    blo, bhi = np.quantile(legacy_boot[:, term], [.025, .975], axis=0)
                    iblo, ibhi = np.quantile(independent_boot[:, term], [.025, .975], axis=0)
                    independent_variance_terms = pinv[term, :, None]**2 * yy.var(axis=0, ddof=1) / len(SEEDS)
                    independent_se = np.sqrt(independent_variance_terms.sum(axis=0))
                    independent_df = independent_variance_terms.sum(axis=0)**2 / (np.sum(independent_variance_terms**2, axis=0) / (len(SEEDS)-1))
                    independent_hw = t.ppf(.975, independent_df) * independent_se
                    independent_adjusted_hw = t.ppf(1-.05/12, independent_df) * independent_se
                    for j in range(2):
                        target = (TARGETS[alg][j] if est != "raw_minus_balance" else 0.) if term == 0 else ""
                        fits.append(dict(window=window, grid=grid, estimator=est, algorithm=alg, estimand=estimand, term=term, coordinate=j,
                                         estimate=m[j], legacy_seed_label_se=se[j], legacy_ci_lower=lo[j], legacy_ci_upper=hi[j],
                                         legacy_ci_width=hi[j]-lo[j], legacy_bonferroni6_lower=alo[j], legacy_bonferroni6_upper=ahi[j],
                                         legacy_bootstrap_lower=blo[j], legacy_bootstrap_upper=bhi[j],
                                         independent_cell_bootstrap_lower=iblo[j], independent_cell_bootstrap_upper=ibhi[j],
                                         independent_cell_bootstrap_width=ibhi[j]-iblo[j], target=target, cells=len(use), runs_per_cell=12,
                                         independent_cell_se=independent_se[j], independent_cell_welch_df=independent_df[j],
                                         independent_cell_t_lower=m[j]-independent_hw[j], independent_cell_t_upper=m[j]+independent_hw[j],
                                         independent_cell_bonferroni6_lower=m[j]-independent_adjusted_hw[j], independent_cell_bonferroni6_upper=m[j]+independent_adjusted_hw[j],
                                         design_condition_number=np.linalg.cond(X), residual_rms=np.sqrt(np.mean(residuals[:,:,j]**2))))
                        if window == "primary" and est == "balance" and alg == "matched_difference":
                            prior = published_fit[f"E1b_control_H4_{grid}", term, j]
                            replay.append(dict(grid=grid, term=term, coordinate=j, estimate=m[j], published_estimate=float(prior["estimate"]),
                                               estimate_difference=m[j]-float(prior["estimate"]),
                                               ci_lower_difference=lo[j]-float(prior["ci_lower"]), ci_upper_difference=hi[j]-float(prior["ci_upper"]),
                                               bootstrap_lower_difference=blo[j]-float(prior["bootstrap_lower"]), bootstrap_upper_difference=bhi[j]-float(prior["bootstrap_upper"])))
    for name, rows in [("run_inventory.csv", inventory), ("per_run_windows.csv", perrun), ("finite_window_identity.csv", identity),
                       ("window_endpoints.csv", endpoints), ("batch_sufficient_statistics.csv", batches), ("reconstruction_checks.csv", crosscheck),
                       ("INPUT_SHA256.csv", input_hashes), ("grid_summary.csv", grids), ("window_contrasts.csv", changes),
                       ("fitted_coefficients.csv", fits), ("per_run_fit_coefficients.csv", fit_runs), ("historical_fit_replay.csv", replay)]:
        write_csv(name, rows)
    write_csv("archive_array_integrity.csv", archive_comparison)
    evaluable = [r for r in identity if r["status"] == "RECONSTRUCTIBLE_PAIRED_POST_IDENTITY"]
    metadata = dict(status="ANALYSIS_ONLY_COMPLETED", new_old_objective_simulations=0,
                    configurations=len(cells), paired_runs=len(inventory), primary_batch_total=sum(r["primary_batches"] for r in inventory),
                    source_archive=source_meta, source_frozen_expected_files=len(conf["source_hashes"]),
                    frozen_snapshot_matches=sum(r["scope"] == "SOURCE_REVIEW/available_frozen_source/" and r["status"] == "MATCH" for r in source_rows),
                    archive_shared_array_mismatches=archive_mismatches,
                    archive_repackaged_runs=sum(r["status"] == "REPACKAGED_SHARED_ARRAYS_IDENTICAL" for r in archive_comparison),
                    all_manuscript_source_hashes_match=all(r["manuscript_source_hash_match"] for r in inventory),
                    max_reconstructed_primary_difference=max(r[k] for r in crosscheck for k in r if k.endswith("max_abs")),
                    max_historical_fit_replay_difference=max(abs(r[k]) for r in replay for k in r if k.endswith("difference")),
                    paired_identity_evaluable_scalar_rows=len(evaluable), paired_identity_missing_window_rows=sum(r["status"].startswith("NOT") for r in identity),
                    paired_identity_max_abs_residual=max(abs(r["residual"]) for r in evaluable),
                    paired_identity_max_abs_normalized_mean_residual=max(abs(r["residual_on_normalized_mean_scale"]) for r in evaluable),
                    paired_identity_control_bound_exceedances=sum(not r["residual_within_control_bound"] for r in evaluable),
                    max_control_sum_norm=max(r["max_zero_sum"] for r in inventory),
                    rng_coupling="Within each cell SCAFFOLD/FedAvg share indexed noise. Across cells the SHA256 key contains cell ID; coincident numeric seed labels do not imply cross-cell common noise.",
                    inference="Independent paired run is the sampling unit. Same-run raw/balance and window contrasts formed before SE/CI. Historical joint seed-label fits reproduced; new independent-cell bootstrap keeps full within-run vector together, 2000 draws seed 26101404. Nominal intervals do not cover deterministic grid error or burn-in.",
                    python=sys.version, platform=platform.platform(), numpy=np.__version__,
                    original_targets={k:v.tolist() for k,v in TARGETS.items()}, B11=B11.tolist())
    write_json("AUDIT_SUMMARY.json", metadata)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
