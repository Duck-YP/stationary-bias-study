"""Saved-table analysis and reporting for frozen formal matrices."""

from __future__ import annotations

import hashlib
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
from .formal import (
    P2_FORMAL_MANIFEST,
    P2_RAW_RESULT_FILES,
    P2_ROW_PROVENANCE_FIELDS,
    P2_RUN_START_PROVENANCE,
    audit_d5_manifest,
    audit_formal_run_matrix,
    build_formal_run_matrix,
    formal_artifact_root,
    formal_config_path,
    formal_protocol_path,
    load_formal_config,
)
from .formal_inference import (
    coordinate_interval,
    seed_block_bootstrap,
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


def _required_paths(output_root: Path, names: tuple[str, ...]) -> list[Path]:
    paths = [output_root / name for name in names]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing formal saved artifact: " + ", ".join(missing))
    return paths


def _strict_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert optional DataFrame cells to JSON null instead of non-standard NaN."""

    clean = frame.astype(object).where(pd.notna(frame), None)
    return clean.to_dict(orient="records")


def validate_saved_formal_matrix(
    target: str, output_root: Path
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    run_path, batch_path, provenance_path = _required_paths(
        output_root,
        ("run_summary.csv", "batch_summary.csv", P2_RUN_START_PROVENANCE),
    )
    config = load_formal_config(target)
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    current_hash = hashlib.sha256(formal_config_path(target).read_bytes()).hexdigest()
    if provenance.get("config_sha256") != current_hash:
        raise RuntimeError("Formal config changed after simulation provenance capture")
    if provenance.get("matrix_id") != config["matrix_identifier"]:
        raise RuntimeError("Saved matrix ID differs from the frozen config")
    protocol_hash = hashlib.sha256(formal_protocol_path(target).read_bytes()).hexdigest()
    if provenance.get("protocol_sha256") != protocol_hash:
        raise RuntimeError("Formal protocol changed after simulation provenance capture")

    run_df = pd.read_csv(run_path, keep_default_na=False)
    batch_df = pd.read_csv(batch_path, keep_default_na=False)
    required_run = {
        "study",
        "phase",
        "matrix_id",
        "setting_id",
        "run_id",
        "seed",
        "d",
        "coordinate",
        "H",
        "N",
        "gamma",
        "delta",
        "estimator",
        "b_component",
        "B11_d_component",
        "C_component",
        "B20_component",
        "normalized_error_component",
        "batches_used",
        "stopping_reason",
        "validity_pass",
        "finite_state_pass",
        "zero_sum_control_error",
        "zero_sum_control_pass",
        "stationarity_pass",
    }
    required_batch = {
        "setting_id",
        "run_id",
        "seed",
        "coordinate",
        "H",
        "N",
        "gamma",
        "delta",
        "estimator",
        "batch_index",
        "C_component",
        "batches_used",
        "stopping_reason",
        "validity_pass",
    }
    if not required_run <= set(run_df.columns):
        raise ValueError(f"Run summary lacks {sorted(required_run - set(run_df.columns))}")
    if not required_batch <= set(batch_df.columns):
        raise ValueError(
            f"Batch summary lacks {sorted(required_batch - set(batch_df.columns))}"
        )

    expected_specs = build_formal_run_matrix(target, config)
    expected = {
        (spec.run_id, estimator, coordinate)
        for spec in expected_specs
        for estimator in ESTIMATORS
        for coordinate in range(spec.d)
    }
    observed_keys = list(
        zip(
            run_df["run_id"].astype(str),
            run_df["estimator"].astype(str),
            run_df["coordinate"].astype(int),
            strict=True,
        )
    )
    if len(observed_keys) != len(set(observed_keys)):
        raise ValueError("Formal run summary contains duplicate coordinate rows")
    observed = set(observed_keys)
    if observed != expected:
        missing = len(expected - observed)
        unexpected = len(observed - expected)
        raise ValueError(
            "F6 frozen matrix completeness failed: "
            f"missing={missing}, unexpected={unexpected}"
        )
    spec_by_id = {spec.run_id: spec for spec in expected_specs}
    for _, row in run_df.iterrows():
        spec = spec_by_id[str(row["run_id"])]
        discrete_identity = (int(row["seed"]), int(row["H"]), int(row["N"]))
        expected_discrete = (spec.seed, spec.H, spec.N)
        floating_identity_matches = np.allclose(
            [float(row["gamma"]), float(row["delta"])],
            [spec.gamma, spec.delta],
            rtol=0.0,
            atol=1.0e-15,
        )
        if discrete_identity != expected_discrete or not floating_identity_matches:
            raise ValueError(f"F6 identity mismatch for {spec.run_id}")
    return run_df, batch_df, provenance, config


def build_setting_summary(
    run_df: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    primary_name = "stationary_mean_balance"
    for key, group in run_df.groupby(SETTING_KEYS, sort=False):
        item = dict(zip(SETTING_KEYS, key, strict=True))
        values = group["C_component"].to_numpy(dtype=float)
        marginal = coordinate_interval(values, confidence_level=0.95)
        simultaneous = coordinate_interval(
            values,
            confidence_level=float(
                config["per_setting_uncertainty"][
                    "simultaneous_coordinate_confidence_level"
                ]
            ),
        )
        target = float(group["B20_component"].iloc[0])
        is_primary = item["estimator"] == primary_name
        threshold = max(
            float(config["precision_stopping"]["absolute_half_width"]),
            float(config["precision_stopping"]["relative_half_width"])
            * abs(target),
        )
        rows.append(
            {
                **item,
                "chain_count": len(group),
                "C_mean": simultaneous.mean,
                "C_sd": simultaneous.sd,
                "C_se": simultaneous.se,
                "marginal_ci_low": marginal.low,
                "marginal_ci_high": marginal.high,
                "simultaneous_ci_low": simultaneous.low,
                "simultaneous_ci_high": simultaneous.high,
                "simultaneous_half_width": simultaneous.half_width,
                "precision_threshold": threshold if is_primary else "",
                "precision_pass": (
                    bool(simultaneous.half_width <= threshold) if is_primary else ""
                ),
                "B20_component": target,
                "theory_covered_simultaneous": bool(
                    simultaneous.low <= target <= simultaneous.high
                ),
                "theory_sign_pass": bool(
                    np.sign(simultaneous.mean) == np.sign(target)
                ),
            }
        )
    return pd.DataFrame(rows)


def build_setting_diagnostics(
    run_df: pd.DataFrame, setting_summary: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    balance = run_df[run_df["estimator"] == "stationary_mean_balance"]
    direct = run_df[run_df["estimator"] == "direct_sample_mean"]
    required_stationary = int(config["protocol"]["stationarity_min_chains"])
    for (setting_id, H, N, gamma, delta, coordinate), group in balance.groupby(
        ["setting_id", "H", "N", "gamma", "delta", "coordinate"], sort=False
    ):
        matching_direct = direct[
            (direct["setting_id"] == setting_id)
            & (direct["coordinate"].astype(int) == int(coordinate))
        ].sort_values("seed")
        ordered_balance = group.sort_values("seed")
        if not np.array_equal(
            matching_direct["seed"].to_numpy(int),
            ordered_balance["seed"].to_numpy(int),
        ):
            raise ValueError("Direct and balance seed blocks differ")
        setting_rows = setting_summary[
            (setting_summary["setting_id"] == setting_id)
            & (setting_summary["estimator"] == "stationary_mean_balance")
        ]
        joint_precision = bool(
            setting_rows["precision_pass"].astype(bool).all()
        )
        stationarity_count = int(np.sum(_bool_series(group["stationarity_pass"])))
        finite = bool(_bool_series(group["finite_state_pass"]).all())
        control = bool(_bool_series(group["zero_sum_control_pass"]).all())
        discrepancy = (
            matching_direct["C_component"].to_numpy(float)
            - ordered_balance["C_component"].to_numpy(float)
        )
        reasons = sorted(set(group["stopping_reason"].astype(str)))
        if len(reasons) != 1:
            raise ValueError("A formal setting has inconsistent stopping reasons")
        rows.append(
            {
                "setting_id": setting_id,
                "H": int(H),
                "N": int(N),
                "gamma": float(gamma),
                "delta": float(delta),
                "coordinate": int(coordinate),
                "joint_precision_pass": joint_precision,
                "max_zero_sum_control_error": float(
                    group["zero_sum_control_error"].astype(float).max()
                ),
                "finite_state_pass": finite,
                "zero_sum_control_pass": control,
                "stationarity_chain_count": stationarity_count,
                "stationarity_pass": stationarity_count >= required_stationary,
                "validity_pass": finite
                and control
                and stationarity_count >= required_stationary,
                "direct_balance_C_difference_mean": float(np.mean(discrepancy)),
                "direct_balance_C_difference_max_abs": float(
                    np.max(np.abs(discrepancy))
                ),
                "stopping_reason": reasons[0],
                "min_batches_used": int(group["batches_used"].astype(int).min()),
                "max_batches_used": int(group["batches_used"].astype(int).max()),
            }
        )
    return pd.DataFrame(rows)


def _bootstrap_for_H(
    balance: pd.DataFrame,
    *,
    H: int,
    seeds: list[int],
    repetitions: int,
    bootstrap_seed: int,
) -> dict[str, object]:
    subset = balance[balance["H"].astype(int) == H]
    settings = (
        subset[["setting_id", "N", "gamma", "delta"]]
        .drop_duplicates()
        .sort_values("delta")
    )
    coordinates = sorted(subset["coordinate"].astype(int).unique())
    values = np.empty((len(settings), len(seeds), len(coordinates)), dtype=float)
    for setting_index, setting in enumerate(settings.itertuples(index=False)):
        for seed_index, seed in enumerate(seeds):
            for coordinate_index, coordinate in enumerate(coordinates):
                match = subset[
                    (subset["setting_id"] == setting.setting_id)
                    & (subset["seed"].astype(int) == seed)
                    & (subset["coordinate"].astype(int) == coordinate)
                ]
                if len(match) != 1:
                    raise ValueError("F6 requires one row per setting, seed, and coordinate")
                values[setting_index, seed_index, coordinate_index] = float(
                    match["C_component"].iloc[0]
                )
    result = seed_block_bootstrap(
        settings["delta"].to_numpy(float),
        values,
        seeds,
        repetitions=repetitions,
        bootstrap_seed=bootstrap_seed,
    )
    return {**result, "settings": settings, "coordinates": coordinates}


def build_fit_and_bootstrap_summaries(
    run_df: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    balance = run_df[run_df["estimator"] == "stationary_mean_balance"].copy()
    seeds = [int(seed) for seed in config["chains"]["seeds"]]
    repetitions = int(config["bootstrap"]["repetitions"])
    bootstrap_seed = int(config["bootstrap"]["seed"])
    fit_rows: list[dict[str, Any]] = []
    bootstrap_rows: list[dict[str, Any]] = []
    for H in sorted(balance["H"].astype(int).unique()):
        result = _bootstrap_for_H(
            balance,
            H=H,
            seeds=seeds,
            repetitions=repetitions,
            bootstrap_seed=bootstrap_seed,
        )
        intercepts = np.asarray(result["intercepts"])
        settings = result["settings"]
        coordinates = result["coordinates"]
        marginal_quantiles = config["bootstrap"]["marginal_diagnostic_quantiles"]
        simultaneous_quantiles = config["bootstrap"]["simultaneous_quantiles"]
        quantiles = {
            "marginal_low": np.quantile(intercepts, marginal_quantiles[0], axis=0),
            "marginal_high": np.quantile(intercepts, marginal_quantiles[1], axis=0),
            "simultaneous_low": np.quantile(
                intercepts, simultaneous_quantiles[0], axis=0
            ),
            "simultaneous_high": np.quantile(
                intercepts, simultaneous_quantiles[1], axis=0
            ),
        }
        for coordinate_index, coordinate in enumerate(coordinates):
            fit = result["fits"][coordinate_index]
            target = float(
                balance[
                    (balance["H"].astype(int) == H)
                    & (balance["coordinate"].astype(int) == coordinate)
                ]["B20_component"].iloc[0]
            )
            for setting_index, setting in enumerate(settings.itertuples(index=False)):
                fit_rows.append(
                    {
                        "H": H,
                        "coordinate": coordinate,
                        "setting_id": setting.setting_id,
                        "N": int(setting.N),
                        "gamma": float(setting.gamma),
                        "delta": float(setting.delta),
                        "num_settings": len(settings),
                        "beta0": fit.beta0,
                        "beta1": fit.beta1,
                        "observed_setting_mean": float(
                            result["setting_means"][setting_index, coordinate_index]
                        ),
                        "fitted_value": float(fit.fitted[setting_index]),
                        "residual": float(fit.residuals[setting_index]),
                        "B20_component": target,
                        "intercept_theory_error": fit.beta0 - target,
                        "marginal_ci_low": float(
                            quantiles["marginal_low"][coordinate_index]
                        ),
                        "marginal_ci_high": float(
                            quantiles["marginal_high"][coordinate_index]
                        ),
                        "simultaneous_ci_low": float(
                            quantiles["simultaneous_low"][coordinate_index]
                        ),
                        "simultaneous_ci_high": float(
                            quantiles["simultaneous_high"][coordinate_index]
                        ),
                        "theory_covered_simultaneous": bool(
                            quantiles["simultaneous_low"][coordinate_index]
                            <= target
                            <= quantiles["simultaneous_high"][coordinate_index]
                        ),
                        "bootstrap_seed": bootstrap_seed,
                        "bootstrap_repetitions": repetitions,
                    }
                )
            for replicate in range(repetitions):
                bootstrap_rows.append(
                    {
                        "replicate": replicate,
                        "H": H,
                        "coordinate": coordinate,
                        "beta0": float(intercepts[replicate, coordinate_index]),
                    }
                )
    return pd.DataFrame(fit_rows), pd.DataFrame(bootstrap_rows)


def _unique_fit_rows(fit_summary: pd.DataFrame) -> pd.DataFrame:
    return fit_summary.drop_duplicates(
        subset=["H", "coordinate", "beta0", "beta1"]
    )


def build_falsification_summary(
    target: str,
    run_df: pd.DataFrame,
    setting_summary: pd.DataFrame,
    diagnostics: pd.DataFrame,
    fit_summary: pd.DataFrame,
    *,
    primary_fit_summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    f0 = bool(diagnostics["validity_pass"].astype(bool).all())
    fits = _unique_fit_rows(fit_summary)

    if target == "d5":
        rows.append(
            {
                "gate": "V0",
                "scope": "all_settings",
                "passed": f0,
                "detail": "finite_control_stationarity_and_validated_matrix",
            }
        )
        for H, gate in ((2, "V1"), (4, "V2")):
            selected = fits[fits["H"].astype(int) == H]
            coordinates = set(selected["coordinate"].astype(int))
            passed = coordinates == set(range(5)) and bool(
                selected["theory_covered_simultaneous"].astype(bool).all()
            )
            rows.append(
                {
                    "gate": gate,
                    "scope": f"H{H}_all_five_coordinates",
                    "passed": passed,
                    "detail": "all_coordinate_simultaneous_bootstrap_coverage",
                }
            )
        balance_settings = setting_summary[
            setting_summary["estimator"] == "stationary_mean_balance"
        ]
        for _, row in balance_settings.iterrows():
            rows.append(
                {
                    "gate": "V3",
                    "scope": f"{row['setting_id']}__coordinate_{int(row['coordinate'])}",
                    "passed": "",
                    "detail": "diagnostic_only_setting_sign",
                    "theory_sign_pass": bool(row["theory_sign_pass"]),
                }
            )
        for _, row in diagnostics.iterrows():
            rows.append(
                {
                    "gate": "V4",
                    "scope": f"{row['setting_id']}__coordinate_{int(row['coordinate'])}",
                    "passed": "",
                    "detail": "diagnostic_only_direct_minus_balance",
                    "direct_balance_C_difference_mean": float(
                        row["direct_balance_C_difference_mean"]
                    ),
                    "direct_balance_C_difference_max_abs": float(
                        row["direct_balance_C_difference_max_abs"]
                    ),
                }
            )
        observed_chains = run_df["run_id"].astype(str).nunique()
        observed_settings = run_df["setting_id"].astype(str).nunique()
        rows.append(
            {
                "gate": "V5",
                "scope": "frozen_matrix",
                "passed": observed_settings == 10 and observed_chains == 80,
                "detail": "exactly_ten_settings_and_eighty_chains",
            }
        )
        return pd.DataFrame(rows)

    rows.append({"gate": "F0", "scope": "all_settings", "passed": f0, "detail": "run_validity"})

    if target == "primary":
        h2 = fits[fits["H"].astype(int) == 2]
        for _, row in h2.iterrows():
            rows.append(
                {
                    "gate": "F1",
                    "scope": f"H2_coordinate_{int(row['coordinate'])}",
                    "passed": bool(row["theory_covered_simultaneous"]),
                    "detail": "simultaneous_bootstrap_target_coverage",
                }
            )
        h4 = fits[fits["H"].astype(int) == 4]
        for _, row in h4.iterrows():
            rows.append(
                {
                    "gate": "F2",
                    "scope": f"H4_coordinate_{int(row['coordinate'])}",
                    "passed": True,
                    "detail": "reporting_only_primary_grid",
                }
            )
        rows.append({"gate": "F3", "scope": "H4", "passed": "", "detail": "deferred_to_frozen_small_step"})
        rows.append({"gate": "F4", "scope": "H4", "passed": "", "detail": "deferred_to_frozen_small_step"})
    else:
        rows.append({"gate": "F1", "scope": "H2", "passed": "", "detail": "not_applicable"})
        rows.append({"gate": "F2", "scope": "H4_primary", "passed": "", "detail": "reported_in_primary_output"})
        if primary_fit_summary is None:
            raise FileNotFoundError(
                "H4 small-step analysis requires the saved primary fit summary"
            )
        primary_fits = _unique_fit_rows(primary_fit_summary)
        for _, row in fits.iterrows():
            coordinate = int(row["coordinate"])
            primary_match = primary_fits[
                (primary_fits["H"].astype(int) == 4)
                & (primary_fits["coordinate"].astype(int) == coordinate)
            ]
            if len(primary_match) != 1:
                raise ValueError("Primary H=4 fit summary is incomplete")
            primary_row = primary_match.iloc[0]
            target_value = float(row["B20_component"])
            closer = abs(float(row["beta0"]) - target_value) < abs(
                float(primary_row["beta0"]) - target_value
            )
            rows.append(
                {
                    "gate": "F3",
                    "scope": f"H4_coordinate_{coordinate}",
                    "passed": bool(row["theory_covered_simultaneous"]),
                    "detail": "small_step_coverage",
                    "closer_to_theory": closer,
                }
            )
        confirmation = setting_summary[
            (setting_summary["estimator"] == "stationary_mean_balance")
            & (setting_summary["H"].astype(int) == 4)
        ]
        for _, row in confirmation.iterrows():
            rows.append(
                {
                    "gate": "F4",
                    "scope": f"{row['setting_id']}__coordinate_{int(row['coordinate'])}",
                    "passed": bool(row["theory_sign_pass"]),
                    "detail": "small_step_direction_sign",
                }
            )

    for _, row in diagnostics.iterrows():
        rows.append(
            {
                "gate": "F5",
                "scope": f"{row['setting_id']}__coordinate_{int(row['coordinate'])}",
                "passed": "",
                "detail": "diagnostic_only",
                "direct_balance_C_difference_mean": float(
                    row["direct_balance_C_difference_mean"]
                ),
                "direct_balance_C_difference_max_abs": float(
                    row["direct_balance_C_difference_max_abs"]
                ),
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
    output_root: Path,
    config: dict[str, Any],
    provenance: dict[str, Any],
    frames: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    figures = (
        ["p2_d5_H2_coefficient_convergence.png", "p2_d5_H4_coefficient_convergence.png"]
        if target == "d5"
        else
        ["p2_d2_H2_coefficient_convergence.png", "p2_d2_H4_coefficient_convergence.png"]
        if target == "primary"
        else ["p2_d2_H4_small_step_confirmation.png"]
    )
    report = (
        "p2_d5_controlled_validation_report.md"
        if target == "d5"
        else
        "p2_d2_coefficient_primary_report.md"
        if target == "primary"
        else "p2_d2_h4_small_step_report.md"
    )
    run_frame = frames["run_summary"]
    falsification = frames["falsification_summary"]
    required_d5_gates = falsification[
        falsification["gate"].isin(["V0", "V1", "V2", "V5"])
    ]
    manifest = {
        "schema_version": 2,
        "study": "p2_multidimensional_validation",
        "phase": "formal",
        "matrix_id": config["matrix_identifier"],
        "source_commit": provenance["source_commit"],
        "source_dirty_at_provenance_capture": provenance[
            "source_dirty_at_run_start"
        ],
        "source_dirty": provenance["source_dirty_at_run_start"],
        "environment": provenance["environment"],
        "config_path": provenance["config_path"],
        "config_sha256": provenance["config_sha256"],
        "protocol_path": provenance["protocol_path"],
        "protocol_sha256": provenance["protocol_sha256"],
        "formal_seed_group": provenance["seeds"],
        "bootstrap_seed": int(config["bootstrap"]["seed"]),
        "bootstrap_repetitions": int(config["bootstrap"]["repetitions"]),
        "bootstrap_replicate_count": int(config["bootstrap"]["repetitions"]),
        "objective": config["objective"],
        "objective_parameters": config["objective"],
        "covariance": config["noise"]["covariance"],
        "covariance_C": config["noise"]["covariance"],
        "theory": config["theory"],
        "theory_targets": config["theory"],
        "run_matrix": audit_formal_run_matrix(target),
        "expected_chain_count": len(build_formal_run_matrix(target, config)),
        "observed_chain_count": int(run_frame["run_id"].astype(str).nunique()),
        "observed_row_counts": {name: len(frame) for name, frame in frames.items()},
        "stopping_protocol": config["precision_stopping"],
        "uncertainty_protocol": config["per_setting_uncertainty"],
        "fit_model": config["extrapolation"],
        "artifact_namespace": config["artifact_namespace"],
        "artifact_filenames": [
            "run_summary.csv",
            "batch_summary.csv",
            "setting_summary.csv",
            "setting_diagnostics.csv",
            "fit_summary.csv",
            "bootstrap_intercepts.csv",
            "falsification_summary.csv",
            report,
            *figures,
            P2_FORMAL_MANIFEST,
            P2_RUN_START_PROVENANCE,
        ],
        "gate_definitions": config.get("gates", {}),
        "gate_results": _strict_records(falsification),
        "combined_formal_pass": (
            bool(required_d5_gates["passed"].astype(bool).all())
            if target == "d5" and len(required_d5_gates) == 4
            else "NOT_APPLICABLE"
        ),
        "interpretation_boundary": config["interpretation_boundary"],
        "numerical_outcomes_label": "EMPIRICAL",
    }
    if target == "d5":
        manifest["artifact_filenames"] = list(config["artifact_filenames"])
        audit_d5_manifest(manifest)
    return manifest


def analyze_formal_saved(
    target: str,
    output_root: Path | None = None,
    *,
    primary_output_root: Path | None = None,
) -> dict[str, Any]:
    """Build derived CSVs from saved raw tables without invoking a simulator."""

    output_root = output_root or formal_artifact_root(target)
    run_df, batch_df, provenance, config = validate_saved_formal_matrix(
        target, output_root
    )
    setting_summary = build_setting_summary(run_df, config)
    diagnostics = build_setting_diagnostics(run_df, setting_summary, config)
    fit_summary, bootstrap_summary = build_fit_and_bootstrap_summaries(run_df, config)
    primary_fits: pd.DataFrame | None = None
    if target == "h4-small-step":
        primary_root = primary_output_root or formal_artifact_root("primary")
        primary_fit_path = primary_root / "fit_summary.csv"
        if primary_fit_path.is_file():
            primary_fits = pd.read_csv(primary_fit_path, keep_default_na=False)
    falsification = build_falsification_summary(
        target,
        run_df,
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
    for name in (
        "setting_summary",
        "setting_diagnostics",
        "fit_summary",
        "bootstrap_intercepts",
        "falsification_summary",
    ):
        write_csv(frames[name], output_root / f"{name}.csv")
    manifest_path = output_root / P2_FORMAL_MANIFEST
    write_json(
        _manifest(target, output_root, config, provenance, frames), manifest_path
    )
    return {**frames, "manifest": manifest_path, "output_root": output_root}


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No saved rows."
    shown = frame[columns].copy()
    for column in shown.select_dtypes(include=["float"]).columns:
        shown[column] = shown[column].map(lambda value: f"{value:.9g}")
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(map(str, row)) + " |"
        for row in shown.itertuples(index=False, name=None)
    ]
    return "\n".join([header, rule, *body])


def build_formal_report_and_plots(
    target: str, output_root: Path | None = None
) -> dict[str, Any]:
    """Render a report and figures strictly from saved derived summaries."""

    output_root = output_root or formal_artifact_root(target)
    paths = _required_paths(
        output_root,
        (
            "setting_summary.csv",
            "fit_summary.csv",
            "falsification_summary.csv",
            P2_FORMAL_MANIFEST,
            P2_RUN_START_PROVENANCE,
        ),
    )
    setting = pd.read_csv(paths[0], keep_default_na=False)
    fits = pd.read_csv(paths[1], keep_default_na=False)
    gates = pd.read_csv(paths[2], keep_default_na=False)
    manifest = json.loads(paths[3].read_text(encoding="utf-8"))
    provenance = json.loads(paths[4].read_text(encoding="utf-8"))
    config = load_formal_config(target)
    unique_fits = _unique_fit_rows(fits)
    report_name = (
        "p2_d5_controlled_validation_report.md"
        if target == "d5"
        else "p2_d2_coefficient_primary_report.md"
        if target == "primary"
        else "p2_d2_h4_small_step_report.md"
    )
    dimension = int(config["objective"]["d"])
    gate_heading = "V0–V5" if target == "d5" else "F0–F6"
    if target == "d5":
        required = gates[gates["gate"].isin(["V0", "V1", "V2", "V5"])]
        combined_pass = len(required) == 4 and bool(_bool_series(required["passed"]).all())
        conclusion = (
            config["interpretation_boundary"]["permitted_conclusion"]
            if combined_pass
            else "The frozen combined empirical criterion did not pass; the permitted "
            "consistency wording is therefore not asserted."
        )
        interpretation = (
            conclusion
            + " This does not establish a theorem, arbitrary-dimensional validity, "
            "d=5 FedAvg attribution, separate empirical identification of local/control "
            "terms, heterogeneity, state-dependent noise, or growing H."
        )
    else:
        interpretation = (
            "This is an empirical consistency analysis of signed coordinatewise vector "
            "coefficients. It does not prove the theorem or test FedAvg attribution, "
            "heterogeneity, growing H, state-dependent noise, d=5, rotation invariance, "
            "or the complete finite-N gamma-squared coefficient."
        )
    report_path = output_root / report_name
    report_text = "\n".join(
        [
            f"# Formal coefficient analysis, d={dimension}",
            "",
            "## EMPIRICAL numerical outcomes",
            "",
            "All numerical tables below are simulation outcomes, not proven statements.",
            "",
            f"Source commit: `{provenance['source_commit']}`",
            "",
            f"Config SHA-256: `{provenance['config_sha256']}`",
            "",
            f"Matrix: `{config['matrix_identifier']}`",
            "",
            "## Frozen inputs",
            "",
            f"Theory: `{json.dumps(config['theory'], sort_keys=True)}`",
            "",
            f"Setting matrix: `{json.dumps(audit_formal_run_matrix(target), sort_keys=True)}`",
            "",
            f"Seed block: `{json.dumps(config['chains']['seeds'])}`",
            "",
            "Primary estimator: signed coordinatewise stationary mean-balance. "
            "The direct stationary sample mean remains diagnostic.",
            "",
            f"Stopping protocol: `{json.dumps(config['precision_stopping'], sort_keys=True)}`",
            "",
            f"Uncertainty: `{json.dumps(config['per_setting_uncertainty'], sort_keys=True)}`",
            "",
            f"Fit: `{json.dumps(config['extrapolation'], sort_keys=True)}`",
            "",
            f"Bootstrap: `{json.dumps(config['bootstrap'], sort_keys=True)}`",
            "",
            "## Coordinatewise settings",
            "",
            _markdown_table(
                setting,
                [
                    "H",
                    "N",
                    "gamma",
                    "delta",
                    "coordinate",
                    "estimator",
                    "C_mean",
                    "simultaneous_ci_low",
                    "simultaneous_ci_high",
                    "B20_component",
                ],
            ),
            "",
            "## Extrapolated intercepts",
            "",
            _markdown_table(
                unique_fits,
                [
                    "H",
                    "coordinate",
                    "beta0",
                    "beta1",
                    "simultaneous_ci_low",
                    "simultaneous_ci_high",
                    "B20_component",
                    "intercept_theory_error",
                    "theory_covered_simultaneous",
                ],
            ),
            "",
            f"## Frozen {gate_heading} gates",
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
    )
    report_path.write_text(report_text, encoding="utf-8")
    from .formal_figures import plot_saved_formal_summaries

    figures = plot_saved_formal_summaries(target, setting, output_root)
    return {
        "report": report_path,
        "figures": figures,
        "output_root": output_root,
    }


def _validate_rebuild(staged_root: Path, target_root: Path) -> dict[str, Any]:
    return validate_controlled_overwrite(
        staged_root,
        target_root,
        raw_result_files=P2_RAW_RESULT_FILES,
        provenance_filename=P2_RUN_START_PROVENANCE,
        identity_fields=("config_sha256", "protocol_sha256", "matrix_id"),
        excluded_row_fields=P2_ROW_PROVENANCE_FIELDS,
    )


def rebuild_formal_analysis(target: str) -> dict[str, Any]:
    """Rebuild derived tables in staging, then atomically replace canonical output."""

    target_root = formal_artifact_root(target)
    staged_root = stage_existing_directory(target_root)
    try:
        primary_root = formal_artifact_root("primary") if target == "h4-small-step" else None
        outputs = analyze_formal_saved(
            target,
            staged_root,
            primary_output_root=primary_root,
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
    """Rebuild reports and figures in staging, then install them atomically."""

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
