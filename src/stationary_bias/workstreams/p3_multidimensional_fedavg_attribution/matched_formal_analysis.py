"""Paired inference, falsification gates, and attribution reports."""

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
from .matched_formal import (
    FORMAL_MANIFEST,
    RAW_RESULT_FILES,
    ROW_PROVENANCE_FIELDS,
    RUN_START_PROVENANCE,
    audit_formal_run_matrix,
    build_formal_run_matrix,
    formal_artifact_root,
    load_formal_config,
)


REQUIRED_COLUMNS = {
    "pair_id", "seed", "H", "N", "gamma", "delta", "coordinate",
    "scaffold_primary_coefficient", "fedavg_primary_coefficient",
    "paired_primary_difference", "paired_cancellation_difference",
    "scaffold_direct_bias", "fedavg_direct_bias", "paired_direct_difference",
    "B20_ctrl_component", "scaffold_validity_pass", "fedavg_validity_pass",
    "scaffold_stationarity_pass", "fedavg_stationarity_pass",
    "zero_sum_control_error", "zero_sum_control_pass", "crn_integrity_pass",
    "pair_validity_pass", "source_commit", "source_dirty_at_run_start",
}


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
    required_files = ["paired_run_summary.csv", "paired_batch_summary.csv", RUN_START_PROVENANCE]
    missing = [name for name in required_files if not (output_root / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing matched raw artifacts: " + ", ".join(missing))
    run_df = pd.read_csv(output_root / required_files[0], keep_default_na=False)
    batch_df = pd.read_csv(output_root / required_files[1], keep_default_na=False)
    if not REQUIRED_COLUMNS <= set(run_df) or not REQUIRED_COLUMNS | {"batch_index"} <= set(batch_df):
        raise ValueError("Matched paired artifact schema is incomplete")
    config = load_formal_config(target)
    specs = build_formal_run_matrix(target, config)
    if len(run_df) != len(specs) * 2:
        raise ValueError("Matched paired matrix row count failed")
    if set(run_df["run_id"].astype(str)) != {item.run_id for item in specs}:
        raise ValueError("Matched run identities are incomplete")
    if set(run_df["seed"].astype(int)) != set(config["pairs"]["seeds"]):
        raise ValueError("Matched paired seeds are incomplete")
    if not _bool_series(run_df["crn_integrity_pass"]).all():
        raise ValueError("Matched common-random-number integrity failed")
    if not np.allclose(
        run_df["paired_primary_difference"].to_numpy(float),
        run_df["paired_cancellation_difference"].to_numpy(float),
        rtol=5.0e-13,
        atol=5.0e-14,
    ):
        raise ValueError("Equivalent paired estimators disagree")
    provenance = json.loads((output_root / RUN_START_PROVENANCE).read_text(encoding="utf-8"))
    if provenance["matrix_id"] != config["matrix_identifier"]:
        raise ValueError("Matched provenance matrix differs from config")
    return run_df, batch_df, provenance, config


def build_setting_summary(run_df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    confidence = float(config["per_setting_uncertainty"]["simultaneous_coordinate_confidence_level"])
    marginal = float(config["per_setting_uncertainty"]["marginal_diagnostic_confidence_level"])
    keys = ["setting_id", "H", "N", "gamma", "delta", "coordinate"]
    for values, group in run_df.groupby(keys, sort=True):
        if len(group) != 8 or group["pair_id"].nunique() != 8:
            raise ValueError("Paired Student-t inference requires eight pair differences")
        differences = group["paired_primary_difference"].to_numpy(float)
        sim = coordinate_interval(differences, confidence_level=confidence)
        marg = coordinate_interval(differences, confidence_level=marginal)
        target = float(group["B20_ctrl_component"].iloc[0])
        row = dict(zip(keys, values, strict=True))
        row.update(
            {
                "paired_chain_count": 8,
                "degrees_of_freedom": 7,
                "D_mean": sim.mean,
                "D_sd": sim.sd,
                "D_se": sim.se,
                "simultaneous_ci_low": sim.low,
                "simultaneous_ci_high": sim.high,
                "simultaneous_half_width": sim.half_width,
                "marginal_ci_low": marg.low,
                "marginal_ci_high": marg.high,
                "B20_ctrl_component": target,
                "theory_sign_pass": bool(sim.mean == 0.0 or np.sign(sim.mean) == np.sign(target)),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def build_setting_diagnostics(run_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for setting_id, group in run_df.groupby("setting_id", sort=True):
        rows.append(
            {
                "setting_id": setting_id,
                "H": int(group["H"].iloc[0]),
                "N": int(group["N"].iloc[0]),
                "gamma": float(group["gamma"].iloc[0]),
                "pair_count": int(group["pair_id"].nunique()),
                "algorithm_members_per_pair": 2,
                "scaffold_validity_pass": bool(_bool_series(group["scaffold_validity_pass"]).all()),
                "fedavg_validity_pass": bool(_bool_series(group["fedavg_validity_pass"]).all()),
                "scaffold_stationarity_pass": bool(_bool_series(group["scaffold_stationarity_pass"]).all()),
                "fedavg_stationarity_pass": bool(_bool_series(group["fedavg_stationarity_pass"]).all()),
                "zero_sum_control_pass": bool(_bool_series(group["zero_sum_control_pass"]).all()),
                "max_zero_sum_control_error": float(group["zero_sum_control_error"].max()),
                "crn_integrity_pass": bool(_bool_series(group["crn_integrity_pass"]).all()),
                "pair_validity_pass": bool(_bool_series(group["pair_validity_pass"]).all()),
                "paired_direct_difference_mean": float(group["paired_direct_difference"].mean()),
            }
        )
    return pd.DataFrame(rows)


def build_fit_and_bootstrap_summaries(
    run_df: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fit_rows: list[dict[str, Any]] = []
    bootstrap_rows: list[dict[str, Any]] = []
    seed_labels = np.asarray(config["pairs"]["seeds"], dtype=int)
    for H, frame in run_df.groupby("H", sort=True):
        settings = frame[["setting_id", "delta"]].drop_duplicates().sort_values("delta")
        values = np.empty((len(settings), 8, 2), dtype=np.float64)
        for setting_index, setting_id in enumerate(settings["setting_id"]):
            selected = frame[frame["setting_id"] == setting_id]
            for seed_index, seed in enumerate(seed_labels):
                pair = selected[selected["seed"].astype(int) == seed].sort_values("coordinate")
                if len(pair) != 2:
                    raise ValueError("Paired bootstrap seed block is incomplete")
                values[setting_index, seed_index] = pair["paired_primary_difference"].to_numpy(float)
        boot = seed_block_bootstrap(
            settings["delta"].to_numpy(float),
            values,
            seed_labels,
            repetitions=int(config["bootstrap"]["repetitions"]),
            bootstrap_seed=int(config["bootstrap"]["seed"]),
        )
        intervals = bootstrap_percentile_intervals(boot["intercepts"])
        targets = frame.drop_duplicates("coordinate").sort_values("coordinate")["B20_ctrl_component"].to_numpy(float)
        for coordinate, fit in enumerate(boot["fits"]):
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
                    "B20_ctrl_component": targets[coordinate],
                    "intercept_theory_error": fit.beta0 - targets[coordinate],
                    "theory_covered_simultaneous": bool(
                        intervals["simultaneous_low"][coordinate]
                        <= targets[coordinate]
                        <= intervals["simultaneous_high"][coordinate]
                    ),
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
                        "bootstrap_unit": "paired_seed_label_block",
                    }
                )
    return pd.DataFrame(fit_rows), pd.DataFrame(bootstrap_rows)


def build_falsification_summary(
    target: str,
    setting: pd.DataFrame,
    diagnostics: pd.DataFrame,
    fits: pd.DataFrame,
    *,
    primary_fits: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in diagnostics.iterrows():
        rows.append({"gate": "P3-F0", "scope": row["setting_id"], "passed": bool(row["pair_validity_pass"] and row["pair_count"] == 8), "detail": "paired_validity"})
    if target == "primary":
        for _, row in fits[fits["H"].astype(int) == 2].iterrows():
            rows.append({"gate": "P3-F1", "scope": f"H2_coordinate_{int(row['coordinate'])}", "passed": bool(row["theory_covered_simultaneous"]), "detail": "paired_bootstrap_coverage"})
        for _, row in fits[fits["H"].astype(int) == 4].iterrows():
            rows.append({"gate": "P3-F2", "scope": f"H4_coordinate_{int(row['coordinate'])}", "passed": True, "detail": "reporting_only_primary_path"})
        rows.append({"gate": "P3-F3", "scope": "H4", "passed": "", "detail": "deferred_to_frozen_small_step"})
    else:
        for _, row in fits.iterrows():
            coordinate = int(row["coordinate"])
            entry = {"gate": "P3-F3", "scope": f"H4_coordinate_{coordinate}", "passed": bool(row["theory_covered_simultaneous"]), "detail": "small_step_paired_bootstrap_coverage"}
            if primary_fits is not None:
                match = primary_fits[(primary_fits["H"].astype(int) == 4) & (primary_fits["coordinate"].astype(int) == coordinate)]
                if len(match) != 1:
                    raise ValueError("Primary H4 paired fit is incomplete")
                entry["closer_to_theory"] = abs(float(row["intercept_theory_error"])) < abs(float(match.iloc[0]["intercept_theory_error"]))
            rows.append(entry)
    for _, row in setting.iterrows():
        rows.append({"gate": "P3-F4", "scope": f"{row['setting_id']}__coordinate_{int(row['coordinate'])}", "passed": bool(row["theory_sign_pass"]), "detail": "signed_coordinate_direction"})
    rows.append({"gate": "P3-F5", "scope": "paired_direct_sample", "passed": "", "detail": "diagnostic_only"})
    rows.append({"gate": "P3-F6", "scope": "frozen_matrix", "passed": True, "detail": "all_settings_pairs_and_algorithm_members_present"})
    rows.append({"gate": "P3-F7", "scope": "all_pairs", "passed": bool(diagnostics["crn_integrity_pass"].all()), "detail": "indexed_noise_blocks_identical"})
    return pd.DataFrame(rows)


def analyze_formal_saved(
    target: str,
    output_root: Path | None = None,
    *,
    primary_output_root: Path | None = None,
) -> dict[str, Any]:
    output_root = output_root or formal_artifact_root(target)
    run_df, batch_df, provenance, config = validate_saved_formal_matrix(target, output_root)
    setting = build_setting_summary(run_df, config)
    diagnostics = build_setting_diagnostics(run_df)
    fits, bootstrap = build_fit_and_bootstrap_summaries(run_df, config)
    primary_fits = None
    if target == "h4-small-step":
        primary_root = primary_output_root or formal_artifact_root("primary")
        path = primary_root / "paired_fit_summary.csv"
        if path.is_file():
            primary_fits = pd.read_csv(path)
    falsification = build_falsification_summary(
        target, setting, diagnostics, fits, primary_fits=primary_fits
    )
    frames = {
        "paired_setting_summary": setting,
        "paired_setting_diagnostics": diagnostics,
        "paired_fit_summary": fits,
        "paired_bootstrap_intercepts": bootstrap,
        "paired_falsification_summary": falsification,
    }
    for name, frame in frames.items():
        write_csv(frame, output_root / f"{name}.csv")
    report_name = "p3_matched_d2_attribution_primary_report.md" if target == "primary" else "p3_matched_d2_h4_small_step_report.md"
    figures = ["p3_matched_d2_H2_control_convergence.png", "p3_matched_d2_H4_control_convergence.png"] if target == "primary" else ["p3_matched_d2_H4_small_step_confirmation.png"]
    manifest = {
        "schema_version": 1,
        "study": "p3_matched",
        "phase": "formal",
        "matrix_id": config["matrix_identifier"],
        "source_commit": provenance["source_commit"],
        "source_dirty_at_run_start": provenance["source_dirty_at_run_start"],
        "config_sha256": provenance["config_sha256"],
        "paired_seed_block": config["pairs"]["seeds"],
        "objective": config["objective"],
        "covariance": config["noise"]["covariance"],
        "theory": config["theory"],
        "bootstrap": config["bootstrap"],
        "gate_definitions": config["gates"],
        "run_matrix": audit_formal_run_matrix(target),
        "artifact_filenames": [
            RUN_START_PROVENANCE,
            f"p3_matched_{target.replace('-', '_')}_config_snapshot.yaml",
            "paired_run_summary.csv", "paired_batch_summary.csv",
            "paired_setting_diagnostics.csv", "paired_setting_summary.csv",
            "paired_fit_summary.csv", "paired_bootstrap_intercepts.csv",
            "paired_falsification_summary.csv", FORMAL_MANIFEST, report_name, *figures,
        ],
        "scientific_execution": "COMPLETED_RAW_AND_ANALYZED",
        "interpretation_boundary": config["interpretation_boundary"],
    }
    manifest_path = output_root / FORMAL_MANIFEST
    write_json(manifest, manifest_path)
    return {**frames, "manifest": manifest_path, "run_rows": run_df, "batch_rows": batch_df}


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    shown = frame[columns].copy()
    for column in shown.select_dtypes(include=["float"]).columns:
        shown[column] = shown[column].map(lambda value: f"{value:.9g}")
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(map(str, row)) + " |" for row in shown.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *body])


def _coverage_coordinates(fits: pd.DataFrame, *, H: int) -> tuple[list[int], list[int]]:
    selected = fits[fits["H"].astype(int) == H].copy()
    if selected.empty:
        raise ValueError(f"Saved fit summary lacks H={H} coverage rows")
    covered = selected["theory_covered_simultaneous"].map(
        lambda value: str(value).strip().lower() == "true"
    )
    coordinates = selected["coordinate"].astype(int)
    return coordinates[covered].tolist(), coordinates[~covered].tolist()


def _format_coordinates(coordinates: list[int]) -> str:
    return " and ".join(str(coordinate) for coordinate in coordinates)


def _interpretation_lines(target: str, fits: pd.DataFrame) -> list[str]:
    if target == "primary":
        h2_passed, h2_failed = _coverage_coordinates(fits, H=2)
        _, h4_failed = _coverage_coordinates(fits, H=4)
        h2_statement = (
            "The H=2 paired attribution simultaneous-coverage criterion passes "
            f"for coordinates {_format_coordinates(h2_passed)}."
            if not h2_failed
            else "The H=2 paired attribution simultaneous-coverage criterion fails "
            f"for coordinates {_format_coordinates(h2_failed)}."
        )
        h4_statement = (
            "The H=4 primary path is reporting-only; its simultaneous coverage "
            f"flags are False for coordinates {_format_coordinates(h4_failed)}. "
            "Final H=4 adjudication "
            "is delegated to the preregistered smaller-step experiment."
            if h4_failed
            else "The H=4 primary path is reporting-only; its simultaneous coverage "
            "flags are True. Final H=4 adjudication remains delegated to the "
            "preregistered smaller-step experiment."
        )
        return [h2_statement, h4_statement]
    if target == "h4-small-step":
        _, h4_failed = _coverage_coordinates(fits, H=4)
        if h4_failed:
            return [
                "The preregistered P3-F3 simultaneous-coverage criterion fails "
                f"for H=4 coordinates {_format_coordinates(h4_failed)}. "
                "This frozen-gate result is an "
                "empirical discrepancy and does not by itself contradict the candidate "
                "asymptotic expansion, whose remainder does not imply exact finite-grid "
                "linearity."
            ]
        return [
            "The preregistered P3-F3 simultaneous-coverage criterion passes for both "
            "H=4 coordinates."
        ]
    raise ValueError(f"Unknown matched-attribution target: {target}")


def build_formal_report_and_plots(
    target: str, output_root: Path | None = None
) -> dict[str, Any]:
    output_root = output_root or formal_artifact_root(target)
    setting = pd.read_csv(output_root / "paired_setting_summary.csv", keep_default_na=False)
    fits = pd.read_csv(output_root / "paired_fit_summary.csv", keep_default_na=False)
    gates = pd.read_csv(output_root / "paired_falsification_summary.csv", keep_default_na=False)
    config = load_formal_config(target)
    name = "p3_matched_d2_attribution_primary_report.md" if target == "primary" else "p3_matched_d2_h4_small_step_report.md"
    report = output_root / name
    report.write_text(
        "\n".join(
            [
                "# Empirical numerical outcomes - matched control attribution",
                "",
                "Simulation outcomes are not proven statements.",
                "",
                "Primary estimator: paired signed coordinatewise stationary mean-balance.",
                "The direct stationary-sample-mean difference is diagnostic only.",
                "",
                f"Matrix: `{config['matrix_identifier']}`",
                "",
                "## Paired coordinatewise settings",
                "",
                _markdown_table(setting, ["H", "N", "gamma", "coordinate", "D_mean", "simultaneous_ci_low", "simultaneous_ci_high", "B20_ctrl_component"]),
                "",
                "## Extrapolated paired intercepts",
                "",
                _markdown_table(fits, ["H", "coordinate", "beta0", "beta1", "simultaneous_ci_low", "simultaneous_ci_high", "B20_ctrl_component", "theory_covered_simultaneous"]),
                "",
                "## Prespecified falsification gates",
                "",
                _markdown_table(gates, ["gate", "scope", "passed", "detail"]),
                "",
                "## Interpretation boundary",
                "",
                *_interpretation_lines(target, fits),
                "This does not prove the decomposition, establish an algorithm ranking, cover heterogeneous clients, state-dependent noise, growing H, or dimensions beyond the frozen d=2 setting.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    from .matched_formal_figures import plot_saved_formal_summaries

    figures = plot_saved_formal_summaries(target, setting, output_root)
    return {"report": report, "figures": figures, "output_root": output_root}


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
    """Rebuild derived tables through the controlled directory transaction."""

    target_root = formal_artifact_root(target)
    staged_root = stage_existing_directory(target_root)
    try:
        primary_root = formal_artifact_root("primary") if target == "h4-small-step" else None
        outputs = analyze_formal_saved(
            target, staged_root, primary_output_root=primary_root
        )
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
    """Rebuild reports and figures through the controlled directory transaction."""

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
