"""Saved-table analysis and reporting for FedAvg coefficient matrices."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ...core.artifacts import (
    rebase_staged_paths,
    replace_output_directory,
    stage_existing_directory,
    validate_controlled_overwrite,
)
from ...core.io import write_csv, write_json
from ..p2_multidimensional_validation.formal_inference import (
    bootstrap_percentile_intervals,
    coordinate_interval,
    seed_block_bootstrap,
)
from .formal import (
    FORMAL_MANIFEST,
    RAW_RESULT_FILES,
    ROW_PROVENANCE_FIELDS,
    RUN_START_PROVENANCE,
    audit_formal_run_matrix,
    build_formal_run_matrix,
    formal_artifact_root,
    load_formal_config,
)


ESTIMATORS = ("direct_sample_mean", "stationary_mean_balance")
SETTING_KEYS = ["setting_id", "H", "N", "gamma", "delta", "coordinate", "estimator"]


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    mapped = series.astype(str).str.lower().map({"true": True, "false": False})
    if mapped.isna().any():
        raise ValueError(f"Invalid Boolean values in {series.name}")
    return mapped.astype(bool)


def validate_saved_formal_matrix(
    target: str, output_root: Path
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    required = ["run_summary.csv", "batch_summary.csv", RUN_START_PROVENANCE]
    missing = [name for name in required if not (output_root / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing formal raw artifacts: " + ", ".join(missing))
    config = load_formal_config(target)
    provenance = json.loads((output_root / RUN_START_PROVENANCE).read_text(encoding="utf-8"))
    run_df = pd.read_csv(output_root / "run_summary.csv", keep_default_na=False)
    batch_df = pd.read_csv(output_root / "batch_summary.csv", keep_default_na=False)
    required_columns = {
        "matrix_id", "setting_id", "run_id", "seed", "coordinate", "H", "N",
        "gamma", "delta", "estimator", "b_component", "B11_d_component",
        "C_component", "B20_FA_component", "batches_used", "stopping_reason",
        "validity_pass", "finite_state_pass", "stationarity_pass",
        "direct_balance_agreement_pass", "source_commit", "source_dirty_at_run_start",
    }
    if not required_columns <= set(run_df.columns):
        raise ValueError("Saved formal run schema is incomplete")
    if "batch_index" not in batch_df.columns or not required_columns <= set(batch_df.columns):
        raise ValueError("Saved formal batch schema is incomplete")
    specs = build_formal_run_matrix(target, config)
    expected_rows = len(specs) * len(ESTIMATORS) * int(config["objective"]["d"])
    if len(run_df) != expected_rows:
        raise ValueError("F6 frozen matrix completeness failed: run row count")
    if set(run_df["run_id"].astype(str)) != {item.run_id for item in specs}:
        raise ValueError("F6 frozen matrix completeness failed: run IDs")
    if set(run_df["seed"].astype(int)) != set(config["chains"]["seeds"]):
        raise ValueError("F6 frozen matrix completeness failed: seed labels")
    if set(run_df["estimator"].astype(str)) != set(ESTIMATORS):
        raise ValueError("Saved estimator set differs from the frozen protocol")
    if "control" in " ".join(run_df.columns).lower() or "xi" in run_df.columns:
        raise ValueError("FedAvg saved schema contains control state")
    if provenance["matrix_id"] != config["matrix_identifier"]:
        raise ValueError("Saved provenance matrix differs from config")
    return run_df, batch_df, provenance, config


def build_setting_summary(run_df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    simultaneous = float(config["per_setting_uncertainty"]["simultaneous_coordinate_confidence_level"])
    marginal = float(config["per_setting_uncertainty"]["marginal_diagnostic_confidence_level"])
    for keys, group in run_df.groupby(SETTING_KEYS, sort=True):
        if len(group) != 8:
            raise ValueError("Every setting/coordinate/estimator needs eight chains")
        values = group["C_component"].to_numpy(float)
        sim = coordinate_interval(values, confidence_level=simultaneous)
        marg = coordinate_interval(values, confidence_level=marginal)
        target = float(group["B20_FA_component"].iloc[0])
        row = dict(zip(SETTING_KEYS, keys, strict=True))
        row.update(
            {
                "C_mean": sim.mean,
                "C_sd": sim.sd,
                "C_se": sim.se,
                "simultaneous_ci_low": sim.low,
                "simultaneous_ci_high": sim.high,
                "simultaneous_half_width": sim.half_width,
                "marginal_ci_low": marg.low,
                "marginal_ci_high": marg.high,
                "B20_FA_component": target,
                "theory_sign_pass": bool(sim.mean == 0.0 or np.sign(sim.mean) == np.sign(target)),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def build_setting_diagnostics(
    run_df: pd.DataFrame, setting_summary: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (setting_id, coordinate), group in run_df.groupby(["setting_id", "coordinate"], sort=True):
        balance = group[group["estimator"] == "stationary_mean_balance"]
        direct = group[group["estimator"] == "direct_sample_mean"]
        if len(balance) != 8 or len(direct) != 8:
            raise ValueError("Diagnostic estimator rows are incomplete")
        direct_by_seed = direct.set_index("seed")["C_component"].sort_index()
        balance_by_seed = balance.set_index("seed")["C_component"].sort_index()
        difference = direct_by_seed.to_numpy(float) - balance_by_seed.to_numpy(float)
        rows.append(
            {
                "setting_id": setting_id,
                "coordinate": int(coordinate),
                "H": int(balance["H"].iloc[0]),
                "N": int(balance["N"].iloc[0]),
                "gamma": float(balance["gamma"].iloc[0]),
                "delta": float(balance["delta"].iloc[0]),
                "chain_count": int(balance["seed"].nunique()),
                "finite_state_pass": bool(_bool_series(balance["finite_state_pass"]).all()),
                "stationarity_pass": bool(_bool_series(balance["stationarity_pass"]).all()),
                "validity_pass": bool(_bool_series(balance["validity_pass"]).all()),
                "direct_balance_agreement_chain_count": int(
                    _bool_series(balance["direct_balance_agreement_pass"]).sum()
                ),
                "direct_balance_C_difference_mean": float(np.mean(difference)),
                "direct_balance_C_difference_max_abs": float(np.max(np.abs(difference))),
            }
        )
    diagnostics = pd.DataFrame(rows)
    expected = setting_summary[setting_summary["estimator"] == "stationary_mean_balance"]
    if len(diagnostics) != len(expected):
        raise ValueError("Setting diagnostics are incomplete")
    return diagnostics


def build_fit_and_bootstrap_summaries(
    run_df: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    balance = run_df[run_df["estimator"] == "stationary_mean_balance"].copy()
    fit_rows: list[dict[str, Any]] = []
    bootstrap_rows: list[dict[str, Any]] = []
    seed_labels = np.asarray(config["chains"]["seeds"], dtype=int)
    for H, H_frame in balance.groupby("H", sort=True):
        settings = (
            H_frame[["setting_id", "delta"]]
            .drop_duplicates()
            .sort_values("delta")
        )
        deltas = settings["delta"].to_numpy(float)
        values = np.empty((len(settings), len(seed_labels), 2), dtype=np.float64)
        for setting_index, setting_id in enumerate(settings["setting_id"]):
            selected = H_frame[H_frame["setting_id"] == setting_id]
            for seed_index, seed in enumerate(seed_labels):
                seed_rows = selected[selected["seed"].astype(int) == seed].sort_values("coordinate")
                if len(seed_rows) != 2:
                    raise ValueError("Bootstrap seed block is incomplete")
                values[setting_index, seed_index] = seed_rows["C_component"].to_numpy(float)
        boot = seed_block_bootstrap(
            deltas,
            values,
            seed_labels,
            repetitions=int(config["bootstrap"]["repetitions"]),
            bootstrap_seed=int(config["bootstrap"]["seed"]),
        )
        intervals = bootstrap_percentile_intervals(boot["intercepts"])
        target_rows = H_frame.drop_duplicates("coordinate").sort_values("coordinate")
        targets = target_rows["B20_FA_component"].to_numpy(float)
        for coordinate, fit in enumerate(boot["fits"]):
            covered = bool(
                intervals["simultaneous_low"][coordinate]
                <= targets[coordinate]
                <= intervals["simultaneous_high"][coordinate]
            )
            fit_rows.append(
                {
                    "H": int(H),
                    "coordinate": coordinate,
                    "beta0": fit.beta0,
                    "beta1": fit.beta1,
                    "simultaneous_ci_low": intervals["simultaneous_low"][coordinate],
                    "simultaneous_ci_high": intervals["simultaneous_high"][coordinate],
                    "marginal_ci_low": intervals["marginal_low"][coordinate],
                    "marginal_ci_high": intervals["marginal_high"][coordinate],
                    "B20_FA_component": targets[coordinate],
                    "intercept_theory_error": fit.beta0 - targets[coordinate],
                    "theory_covered_simultaneous": covered,
                }
            )
        for replicate, intercept in enumerate(boot["intercepts"]):
            for coordinate in range(2):
                bootstrap_rows.append(
                    {
                        "H": int(H),
                        "replicate": replicate,
                        "coordinate": coordinate,
                        "beta0": intercept[coordinate],
                        "bootstrap_seed": int(config["bootstrap"]["seed"]),
                    }
                )
    return pd.DataFrame(fit_rows), pd.DataFrame(bootstrap_rows)


def build_falsification_summary(
    target: str,
    setting_summary: pd.DataFrame,
    diagnostics: pd.DataFrame,
    fit_summary: pd.DataFrame,
    *,
    primary_fit_summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in diagnostics.iterrows():
        rows.append(
            {
                "gate": "F0",
                "scope": f"{row['setting_id']}__coordinate_{int(row['coordinate'])}",
                "passed": bool(row["validity_pass"] and int(row["chain_count"]) == 8),
                "detail": "finite_stationary_eight_chains",
            }
        )
    if target == "primary":
        for _, row in fit_summary[fit_summary["H"].astype(int) == 2].iterrows():
            rows.append(
                {
                    "gate": "F1",
                    "scope": f"H2_coordinate_{int(row['coordinate'])}",
                    "passed": bool(row["theory_covered_simultaneous"]),
                    "detail": "primary_H2_simultaneous_coverage",
                }
            )
        for _, row in fit_summary[fit_summary["H"].astype(int) == 4].iterrows():
            rows.append(
                {
                    "gate": "F2",
                    "scope": f"H4_coordinate_{int(row['coordinate'])}",
                    "passed": True,
                    "detail": "reporting_only_primary_path",
                }
            )
        rows.append({"gate": "F3", "scope": "H4", "passed": "", "detail": "deferred_to_frozen_small_step"})
        balance = setting_summary[setting_summary["estimator"] == "stationary_mean_balance"]
        for _, row in balance.iterrows():
            rows.append(
                {
                    "gate": "F4",
                    "scope": f"{row['setting_id']}__coordinate_{int(row['coordinate'])}",
                    "passed": bool(row["theory_sign_pass"]),
                    "detail": "signed_coordinate_direction_warning",
                }
            )
    else:
        if primary_fit_summary is None:
            raise FileNotFoundError("H4 small-step analysis requires primary fit_summary.csv")
        for _, row in fit_summary.iterrows():
            coordinate = int(row["coordinate"])
            match = primary_fit_summary[
                (primary_fit_summary["H"].astype(int) == 4)
                & (primary_fit_summary["coordinate"].astype(int) == coordinate)
            ]
            if len(match) != 1:
                raise ValueError("Primary H=4 fit summary is incomplete")
            primary_error = abs(float(match.iloc[0]["intercept_theory_error"]))
            small_error = abs(float(row["intercept_theory_error"]))
            rows.append(
                {
                    "gate": "F3",
                    "scope": f"H4_coordinate_{coordinate}",
                    "passed": bool(row["theory_covered_simultaneous"]),
                    "detail": "small_step_simultaneous_coverage",
                    "closer_to_theory": small_error < primary_error,
                }
            )
        balance = setting_summary[setting_summary["estimator"] == "stationary_mean_balance"]
        for _, row in balance.iterrows():
            rows.append(
                {
                    "gate": "F4",
                    "scope": f"{row['setting_id']}__coordinate_{int(row['coordinate'])}",
                    "passed": bool(row["theory_sign_pass"]),
                    "detail": "small_step_signed_coordinate_direction",
                }
            )
    for _, row in diagnostics.iterrows():
        rows.append(
            {
                "gate": "F5",
                "scope": f"{row['setting_id']}__coordinate_{int(row['coordinate'])}",
                "passed": "",
                "detail": "direct_balance_diagnostic_only",
            }
        )
    rows.append(
        {
            "gate": "F6",
            "scope": "frozen_matrix",
            "passed": True,
            "detail": "all_settings_and_seeds_present",
        }
    )
    return pd.DataFrame(rows)


def _manifest(
    target: str,
    config: dict[str, Any],
    provenance: dict[str, Any],
    frames: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    report = "p3_d2_coefficient_primary_report.md" if target == "primary" else "p3_d2_h4_small_step_report.md"
    figures = (
        ["p3_d2_H2_coefficient_convergence.png", "p3_d2_H4_coefficient_convergence.png"]
        if target == "primary"
        else ["p3_d2_H4_small_step_confirmation.png"]
    )
    snapshot = f"p3_{target.replace('-', '_')}_config_snapshot.yaml"
    return {
        "schema_version": 1,
        "study": "p3",
        "phase": "formal",
        "matrix_id": config["matrix_identifier"],
        "source_commit": provenance["source_commit"],
        "source_dirty_at_run_start": provenance["source_dirty_at_run_start"],
        "config_path": provenance["config_path"],
        "config_sha256": provenance["config_sha256"],
        "formal_seed_group": provenance["seeds"],
        "bootstrap_seed": int(config["bootstrap"]["seed"]),
        "bootstrap_replicate_count": int(config["bootstrap"]["repetitions"]),
        "objective_parameters": config["objective"],
        "covariance_C": config["noise"]["covariance"],
        "theory_targets": config["theory"],
        "run_matrix": audit_formal_run_matrix(target),
        "observed_row_counts": {name: len(frame) for name, frame in frames.items()},
        "stopping_protocol": config["precision_stopping"],
        "uncertainty_protocol": config["per_setting_uncertainty"],
        "fit_model": config["extrapolation"],
        "control_state": False,
        "artifact_namespace": config["artifact_namespace"],
        "artifact_filenames": [
            "run_summary.csv", "batch_summary.csv", "setting_diagnostics.csv",
            "setting_summary.csv", "fit_summary.csv", "bootstrap_intercepts.csv",
            "falsification_summary.csv", FORMAL_MANIFEST, RUN_START_PROVENANCE,
            snapshot, report, *figures,
        ],
        "gate_definitions": config["gates"],
        "interpretation_boundary": config["interpretation_boundary"],
        "numerical_outcomes_label": "EMPIRICAL",
    }


def analyze_formal_saved(
    target: str,
    output_root: Path | None = None,
    *,
    primary_output_root: Path | None = None,
) -> dict[str, Any]:
    output_root = output_root or formal_artifact_root(target)
    run_df, batch_df, provenance, config = validate_saved_formal_matrix(target, output_root)
    setting_summary = build_setting_summary(run_df, config)
    diagnostics = build_setting_diagnostics(run_df, setting_summary)
    fit_summary, bootstrap_summary = build_fit_and_bootstrap_summaries(run_df, config)
    primary_fits: pd.DataFrame | None = None
    if target == "h4-small-step":
        primary_root = primary_output_root or formal_artifact_root("primary")
        primary_path = primary_root / "fit_summary.csv"
        if primary_path.is_file():
            primary_fits = pd.read_csv(primary_path, keep_default_na=False)
    falsification = build_falsification_summary(
        target,
        setting_summary,
        diagnostics,
        fit_summary,
        primary_fit_summary=primary_fits,
    )
    frames = {
        "run_summary": run_df,
        "batch_summary": batch_df,
        "setting_summary": setting_summary,
        "setting_diagnostics": diagnostics,
        "fit_summary": fit_summary,
        "bootstrap_intercepts": bootstrap_summary,
        "falsification_summary": falsification,
    }
    for name in ("setting_summary", "setting_diagnostics", "fit_summary", "bootstrap_intercepts", "falsification_summary"):
        write_csv(frames[name], output_root / f"{name}.csv")
    manifest_path = output_root / FORMAL_MANIFEST
    write_json(_manifest(target, config, provenance, frames), manifest_path)
    return {**frames, "manifest": manifest_path, "output_root": output_root}


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    shown = frame[columns].copy()
    for column in shown.select_dtypes(include=["float"]).columns:
        shown[column] = shown[column].map(lambda value: f"{value:.9g}")
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(map(str, row)) + " |" for row in shown.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *body])


def build_formal_report_and_plots(
    target: str, output_root: Path | None = None
) -> dict[str, Any]:
    output_root = output_root or formal_artifact_root(target)
    names = ["setting_summary.csv", "fit_summary.csv", "falsification_summary.csv", FORMAL_MANIFEST, RUN_START_PROVENANCE]
    missing = [name for name in names if not (output_root / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing analyzed artifacts: " + ", ".join(missing))
    setting = pd.read_csv(output_root / names[0], keep_default_na=False)
    fits = pd.read_csv(output_root / names[1], keep_default_na=False)
    gates = pd.read_csv(output_root / names[2], keep_default_na=False)
    manifest = json.loads((output_root / FORMAL_MANIFEST).read_text(encoding="utf-8"))
    config = load_formal_config(target)
    report_name = "p3_d2_coefficient_primary_report.md" if target == "primary" else "p3_d2_h4_small_step_report.md"
    report_path = output_root / report_name
    interpretation = (
        "This signed coordinatewise FedAvg-only analysis may establish empirical consistency or inconsistency with the candidate coefficient. "
        "It does not prove the theorem, prove multidimensional attribution, test the SCAFFOLD-minus-FedAvg difference, prove a SCAFFOLD control contribution, or cover heterogeneity, growing H, state-dependent noise, or the complete finite-N gamma-squared coefficient."
    )
    report_path.write_text(
        "\n".join(
            [
                "# Empirical numerical outcomes - multidimensional FedAvg coefficient",
                "",
                "Simulation outcomes are not proven statements.",
                "",
                f"Matrix: `{config['matrix_identifier']}`",
                "",
                "Primary estimator: signed coordinatewise stationary mean-balance. The direct stationary sample mean is diagnostic only.",
                "",
                "## Frozen theory and protocol",
                "",
                f"Theory: `{json.dumps(config['theory'], sort_keys=True)}`",
                "",
                f"Run matrix: `{json.dumps(audit_formal_run_matrix(target), sort_keys=True)}`",
                "",
                f"Bootstrap: `{json.dumps(config['bootstrap'], sort_keys=True)}`",
                "",
                "## Coordinatewise settings",
                "",
                _markdown_table(setting, ["H", "N", "gamma", "delta", "coordinate", "estimator", "C_mean", "simultaneous_ci_low", "simultaneous_ci_high", "B20_FA_component"]),
                "",
                "## Extrapolated intercepts",
                "",
                _markdown_table(fits, ["H", "coordinate", "beta0", "beta1", "simultaneous_ci_low", "simultaneous_ci_high", "B20_FA_component", "intercept_theory_error", "theory_covered_simultaneous"]),
                "",
                "## Frozen gates",
                "",
                _markdown_table(gates, ["gate", "scope", "passed", "detail"]),
                "",
                "## Interpretation boundary",
                "",
                interpretation,
                "",
                f"Manifest: `{manifest['matrix_id']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    from .formal_figures import plot_saved_formal_summaries

    figures = plot_saved_formal_summaries(target, setting, output_root)
    return {"report": report_path, "figures": figures, "output_root": output_root}


def _validate_rebuild(staged_root: Path, target_root: Path) -> dict[str, Any]:
    return validate_controlled_overwrite(
        staged_root,
        target_root,
        raw_result_files=RAW_RESULT_FILES,
        provenance_filename=RUN_START_PROVENANCE,
        identity_fields=("config_sha256", "matrix_id"),
        excluded_row_fields=ROW_PROVENANCE_FIELDS,
    )


def rebuild_formal_analysis(target: str) -> dict[str, Any]:
    target_root = formal_artifact_root(target)
    staged_root = stage_existing_directory(target_root)
    try:
        primary_root = formal_artifact_root("primary") if target == "h4-small-step" else None
        outputs = analyze_formal_saved(target, staged_root, primary_output_root=primary_root)
        overwrite_audit = _validate_rebuild(staged_root, target_root)
        replace_output_directory(staged_root, target_root)
    except BaseException:
        if staged_root.exists():
            shutil.rmtree(staged_root)
        raise
    outputs = rebase_staged_paths(outputs, staged_root, target_root)
    outputs["overwrite_audit"] = overwrite_audit
    return outputs


def rebuild_formal_report(target: str) -> dict[str, Any]:
    target_root = formal_artifact_root(target)
    staged_root = stage_existing_directory(target_root)
    try:
        outputs = build_formal_report_and_plots(target, staged_root)
        overwrite_audit = _validate_rebuild(staged_root, target_root)
        replace_output_directory(staged_root, target_root)
    except BaseException:
        if staged_root.exists():
            shutil.rmtree(staged_root)
        raise
    outputs = rebase_staged_paths(outputs, staged_root, target_root)
    outputs["overwrite_audit"] = overwrite_audit
    return outputs
