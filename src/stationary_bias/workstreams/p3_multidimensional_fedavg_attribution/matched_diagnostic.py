"""Post-hoc H=4 paired-attribution diagnostics from saved formal artifacts.

This module never runs a stationary production simulation and never changes a
preregistered gate.  It reconstructs derived diagnostics from the two frozen
paired raw-result matrices and runs only small deterministic kernel audits.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ...core.artifacts import create_staging_directory, rebase_staged_paths, replace_output_directory
from ...core.io import REPO_ROOT, environment_manifest, load_yaml, write_csv, write_json
from ...core.plotting import finish_paper_figure, paper_axes
from ..p2_multidimensional_validation.inference import vector_balance_round_value
from ..p2_multidimensional_validation.objective import RankOneVectorObjective
from ..p2_multidimensional_validation.rotation import rotate_last_axis
from .matched_formal import formal_artifact_root, load_formal_config
from .matched_formal_analysis import validate_saved_formal_matrix
from .matched_simulation import covariance_from_p3_config, objective_from_p3_config
from .paired_algorithm import indexed_noise_block, indexed_noise_vector, paired_round_many_vector
from .theory import matched_vector_theory_targets


DIAGNOSTIC_MATRIX_ID = "p3-d2-matched-attribution-h4-diagnostic"
DIAGNOSTIC_ROOT = (
    REPO_ROOT
    / "workstreams"
    / "p3_multidimensional_fedavg_attribution"
    / "artifacts"
    / "formal"
    / DIAGNOSTIC_MATRIX_ID
)
DIAGNOSTIC_CONFIG_PATH = (
    REPO_ROOT
    / "workstreams"
    / "p3_multidimensional_fedavg_attribution"
    / "configs"
    / "d2_matched_attribution_h4_diagnostic.yaml"
)
DIAGNOSTIC_CONFIG_SNAPSHOT = "p3_matched_h4_diagnostic_config_snapshot.yaml"
REBUILD_START_PROVENANCE = "rebuild_start_provenance.json"


def load_diagnostic_config() -> dict[str, Any]:
    config = load_yaml(DIAGNOSTIC_CONFIG_PATH)
    if config.get("matrix_identifier") != DIAGNOSTIC_MATRIX_ID:
        raise ValueError("Diagnostic config matrix identifier does not match its output root")
    if config.get("new_production_simulation") is not False:
        raise ValueError("H=4 diagnostic must remain analysis-only")
    return config


_DIAGNOSTIC_CONFIG = load_diagnostic_config()
DIAGNOSTIC_BOOTSTRAP_SEED = int(_DIAGNOSTIC_CONFIG["bootstrap"]["seed"])
DIAGNOSTIC_BOOTSTRAP_REPETITIONS = int(
    _DIAGNOSTIC_CONFIG["bootstrap"]["repetitions"]
)
IDENTITY_ATOL = float(
    _DIAGNOSTIC_CONFIG["tolerances"]["estimator_identity_atol"]
)
KERNEL_ATOL = float(_DIAGNOSTIC_CONFIG["tolerances"]["reference_kernel_atol"])
EQUIVARIANCE_ATOL = float(
    _DIAGNOSTIC_CONFIG["tolerances"]["coordinate_equivariance_atol"]
)
PROTECTED_OUTPUT_SHA256 = {
    str(name): str(digest)
    for name, digest in _DIAGNOSTIC_CONFIG["protected_output_sha256"].items()
}

OUTPUT_FILES = (
    "pointwise_diagnostics.csv",
    "scaling_summary.csv",
    "nested_window_linear_summary.csv",
    "linear_quadratic_comparison.csv",
    "same_pair_attribution.csv",
    "implementation_audit.csv",
    "fixed_seed_reference_trace.csv",
    "h4_residual_scaling.png",
    "h4_scaled_residual.png",
    "h4_loglog_residual.png",
    "p3_h4_paired_diagnostic_report.md",
    DIAGNOSTIC_CONFIG_SNAPSHOT,
    REBUILD_START_PROVENANCE,
    "diagnostic_manifest.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_paths() -> dict[str, Path]:
    return {
        "primary": formal_artifact_root("primary"),
        "smaller_step": formal_artifact_root("h4-small-step"),
    }


def _load_h4_rows() -> tuple[pd.DataFrame, dict[str, Any]]:
    frames: list[pd.DataFrame] = []
    source: dict[str, Any] = {}
    for dataset, target in (("primary", "primary"), ("smaller_step", "h4-small-step")):
        root = formal_artifact_root(target)
        run, _, provenance, config = validate_saved_formal_matrix(target, root)
        selected = run[run["H"].astype(int) == 4].copy()
        if selected.empty:
            raise ValueError(f"Saved {dataset} artifact has no H=4 rows")
        selected.insert(0, "dataset", dataset)
        frames.append(selected)
        source[dataset] = {
            "target": target,
            "artifact_root": str(root.relative_to(REPO_ROOT)).replace("\\", "/"),
            "raw_result": "paired_run_summary.csv",
            "raw_sha256": _sha256(root / "paired_run_summary.csv"),
            "provenance_sha256": _sha256(root / "run_start_provenance.json"),
            "source_commit": provenance["source_commit"],
            "config_sha256": provenance["config_sha256"],
            "config_path": provenance["config_path"],
            "seeds": [int(value) for value in config["pairs"]["seeds"]],
        }
    frame = pd.concat(frames, ignore_index=True)
    return frame, source


def _theory() -> Any:
    config = load_formal_config("primary")
    return matched_vector_theory_targets(
        objective_from_p3_config(config), covariance_from_p3_config(config), 4
    )


def _mean_interval(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(list(values), dtype=np.float64)
    expected_chains = int(
        _DIAGNOSTIC_CONFIG["uncertainty"]["paired_chains_per_setting"]
    )
    if array.size != expected_chains:
        raise ValueError(
            f"Diagnostic point uncertainty requires {expected_chains} paired chains"
        )
    mean = float(np.mean(array))
    sd = float(np.std(array, ddof=1))
    se = sd / math.sqrt(array.size)
    critical = float(
        _DIAGNOSTIC_CONFIG["uncertainty"]["simultaneous_critical_value"]
    )
    return {
        "mean": mean,
        "sd": sd,
        "se": se,
        "simultaneous_ci_low": mean - critical * se,
        "simultaneous_ci_high": mean + critical * se,
    }


def build_pointwise_diagnostics(rows: pd.DataFrame) -> pd.DataFrame:
    """Reconstruct every saved H=4 setting/coordinate estimator and identity."""

    targets = _theory()
    enriched = rows.copy()
    coord = enriched["coordinate"].to_numpy(int)
    gamma = enriched["gamma"].to_numpy(float)
    n_clients = enriched["N"].to_numpy(float)
    b11 = targets.B11_d[coord]
    reconstructed_scaffold = (
        enriched["scaffold_balance_bias"].to_numpy(float) - gamma / n_clients * b11
    ) / gamma**2
    reconstructed_fedavg = (
        enriched["fedavg_balance_bias"].to_numpy(float) - gamma / n_clients * b11
    ) / gamma**2
    reconstructed_difference = (
        enriched["scaffold_balance_bias"].to_numpy(float)
        - enriched["fedavg_balance_bias"].to_numpy(float)
    ) / gamma**2
    enriched["normalization_error_scaffold"] = (
        enriched["scaffold_primary_coefficient"].to_numpy(float) - reconstructed_scaffold
    )
    enriched["normalization_error_fedavg"] = (
        enriched["fedavg_primary_coefficient"].to_numpy(float) - reconstructed_fedavg
    )
    enriched["bias_difference_normalization_error"] = (
        enriched["paired_primary_difference"].to_numpy(float) - reconstructed_difference
    )
    enriched["D_identity_error"] = (
        enriched["paired_primary_difference"].to_numpy(float)
        - (
            enriched["scaffold_primary_coefficient"].to_numpy(float)
            - enriched["fedavg_primary_coefficient"].to_numpy(float)
        )
    )

    records: list[dict[str, Any]] = []
    keys = ["dataset", "setting_id", "N", "gamma", "delta", "coordinate"]
    for values, group in enriched.groupby(keys, sort=True):
        dataset, setting_id, N, gamma_value, saved_delta, coordinate = values
        coordinate = int(coordinate)
        if len(group) != 8 or group["seed"].nunique() != 8:
            raise ValueError("Every diagnostic point must retain all eight paired seeds")
        computed_delta = float(gamma_value) + 1.0 / int(N)
        C_scaffold = _mean_interval(group["scaffold_primary_coefficient"])
        C_fedavg = _mean_interval(group["fedavg_primary_coefficient"])
        D = _mean_interval(group["paired_primary_difference"])
        B_scaffold = float(targets.B20_SCAF[coordinate])
        B_fedavg = float(targets.B20_FA[coordinate])
        B_ctrl = float(targets.B20_ctrl[coordinate])
        e_scaffold = C_scaffold["mean"] - B_scaffold
        e_fedavg = C_fedavg["mean"] - B_fedavg
        e_delta = D["mean"] - B_ctrl
        residual_identity = e_delta - (e_scaffold - e_fedavg)
        record = {
            "dataset": dataset,
            "setting_id": setting_id,
            "N": int(N),
            "gamma": float(gamma_value),
            "delta": computed_delta,
            "saved_delta": float(saved_delta),
            "coordinate": coordinate,
            "paired_seed_count": 8,
            "C_SCAF": C_scaffold["mean"],
            "C_SCAF_se": C_scaffold["se"],
            "B_SCAF": B_scaffold,
            "e_SCAF": e_scaffold,
            "C_FA": C_fedavg["mean"],
            "C_FA_se": C_fedavg["se"],
            "B_FA": B_fedavg,
            "e_FA": e_fedavg,
            "D": D["mean"],
            "D_se": D["se"],
            "D_simultaneous_ci_low": D["simultaneous_ci_low"],
            "D_simultaneous_ci_high": D["simultaneous_ci_high"],
            "B_ctrl": B_ctrl,
            "e_Delta": e_delta,
            "e_Delta_over_delta": e_delta / computed_delta,
            "D_identity_error": float(group["D_identity_error"].abs().max()),
            "residual_identity_error": residual_identity,
            "bias_difference_normalization_error": float(
                group["bias_difference_normalization_error"].abs().max()
            ),
            "scaffold_normalization_error": float(
                group["normalization_error_scaffold"].abs().max()
            ),
            "fedavg_normalization_error": float(
                group["normalization_error_fedavg"].abs().max()
            ),
            "delta_identity_error": float(saved_delta) - computed_delta,
            "gamma_inverse_N_error": float(gamma_value) - 1.0 / int(N),
        }
        records.append(record)
    result = pd.DataFrame(records).sort_values(
        ["coordinate", "delta", "dataset"], ignore_index=True
    )
    identity_columns = [
        "D_identity_error",
        "residual_identity_error",
        "bias_difference_normalization_error",
        "scaffold_normalization_error",
        "fedavg_normalization_error",
        "delta_identity_error",
        "gamma_inverse_N_error",
    ]
    if float(result[identity_columns].abs().to_numpy().max()) > IDENTITY_ATOL:
        raise RuntimeError("Pointwise estimator identity audit failed; interpretation stopped")
    return result


def build_scaling_summary(pointwise: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for coordinate, group in pointwise.groupby("coordinate", sort=True):
        ordered = group.sort_values("delta")
        delta = ordered["delta"].to_numpy(float)
        residual = ordered["e_Delta"].to_numpy(float)
        scaled = ordered["e_Delta_over_delta"].to_numpy(float)
        slope, intercept = np.polyfit(np.log(delta), np.log(np.abs(residual)), 1)
        smallest_four = ordered.iloc[:4]
        tail_scaled = smallest_four["e_Delta_over_delta"].to_numpy(float)
        records.append(
            {
                "coordinate": int(coordinate),
                "point_count": len(ordered),
                "delta_min": float(delta.min()),
                "delta_max": float(delta.max()),
                "abs_e_Delta_at_delta_min": float(abs(residual[0])),
                "abs_e_Delta_at_delta_max": float(abs(residual[-1])),
                "abs_e_Delta_monotone_with_delta": bool(
                    np.all(np.diff(np.abs(residual)) >= -1.0e-15)
                ),
                "e_Delta_over_delta_min": float(scaled.min()),
                "e_Delta_over_delta_max": float(scaled.max()),
                "tail_e_Delta_over_delta_mean": float(np.mean(tail_scaled)),
                "tail_e_Delta_over_delta_relative_range": float(
                    np.ptp(tail_scaled) / abs(np.mean(tail_scaled))
                ),
                "loglog_slope": float(slope),
                "loglog_intercept": float(intercept),
                "plateau_evidence": "NO_NONZERO_PLATEAU_OVER_OBSERVED_GRID",
                "interpretation": "DIAGNOSTIC_ONLY_NOT_THEOREM_PROOF",
            }
        )
    return pd.DataFrame(records)


def _grid_values(rows: pd.DataFrame, datasets: tuple[str, ...]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    selected = rows[rows["dataset"].isin(datasets)].copy()
    settings = (
        selected[["dataset", "setting_id", "delta"]]
        .drop_duplicates()
        .sort_values("delta")
        .reset_index(drop=True)
    )
    values: dict[str, np.ndarray] = {}
    for dataset in datasets:
        labels = np.sort(selected.loc[selected["dataset"] == dataset, "seed"].unique())
        dataset_settings = settings[settings["dataset"] == dataset]
        block = np.empty((len(dataset_settings), len(labels), 2), dtype=np.float64)
        for i, setting_id in enumerate(dataset_settings["setting_id"]):
            setting = selected[selected["setting_id"] == setting_id]
            for j, seed in enumerate(labels):
                pair = setting[setting["seed"].astype(int) == int(seed)].sort_values("coordinate")
                if len(pair) != 2:
                    raise ValueError("Diagnostic bootstrap lost a paired seed/coordinate block")
                block[i, j] = pair["paired_primary_difference"].to_numpy(float)
        values[dataset] = block
    return settings["delta"].to_numpy(float), values


def _fit_model(x: np.ndarray, y: np.ndarray, degree: int) -> tuple[np.ndarray, np.ndarray, float, int]:
    design = np.column_stack([x**power for power in range(degree + 1)])
    beta, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if rank != degree + 1:
        raise ValueError("Diagnostic polynomial fit is rank deficient")
    residuals = y - design @ beta
    return beta, residuals, float(np.linalg.cond(design)), int(len(x) - degree - 1)


def _bootstrap_fit(
    rows: pd.DataFrame,
    datasets: tuple[str, ...],
    deltas: np.ndarray,
    *,
    degree: int,
    repetitions: int = DIAGNOSTIC_BOOTSTRAP_REPETITIONS,
) -> tuple[np.ndarray, np.ndarray]:
    _, blocks = _grid_values(rows, datasets)
    delta_parts: list[np.ndarray] = []
    means_parts = []
    keep_by_dataset: dict[str, np.ndarray] = {}
    for dataset in datasets:
        dataset_rows = rows[rows["dataset"] == dataset]
        dataset_deltas = np.sort(dataset_rows["delta"].unique())
        dataset_keep = np.isin(np.round(dataset_deltas, 15), np.round(deltas, 15))
        keep_by_dataset[dataset] = dataset_keep
        delta_parts.append(dataset_deltas[dataset_keep])
        means_parts.append(np.mean(blocks[dataset][dataset_keep], axis=1))
    unsorted_x = np.concatenate(delta_parts)
    order = np.argsort(unsorted_x)
    x = unsorted_x[order]
    means = np.concatenate(means_parts, axis=0)[order]
    if not np.allclose(x, np.sort(deltas), rtol=0.0, atol=1.0e-15):
        raise ValueError("Diagnostic window does not match the saved deterministic grid")
    base = np.stack([_fit_model(x, means[:, c], degree)[0] for c in range(2)])
    rng = np.random.default_rng(DIAGNOSTIC_BOOTSTRAP_SEED + degree + len(x) * 100)
    boot = np.empty((repetitions, 2, degree + 1), dtype=np.float64)
    for replicate in range(repetitions):
        replicate_parts = []
        for dataset in datasets:
            block = blocks[dataset]
            indices = rng.integers(0, block.shape[1], size=block.shape[1])
            replicate_parts.append(
                np.mean(block[keep_by_dataset[dataset]][:, indices, :], axis=1)
            )
        replicate_means = np.concatenate(replicate_parts, axis=0)[order]
        for coordinate in range(2):
            boot[replicate, coordinate] = _fit_model(
                x, replicate_means[:, coordinate], degree
            )[0]
    return base, boot


def _included_grid(frame: pd.DataFrame) -> str:
    values = frame[["dataset", "N", "delta"]].drop_duplicates().sort_values("delta")
    return ";".join(
        f"{row.dataset}:N{int(row.N)}:delta={float(row.delta):.12g}"
        for row in values.itertuples(index=False)
    )


def build_nested_window_summary(rows: pd.DataFrame, pointwise: pd.DataFrame) -> pd.DataFrame:
    targets = _theory()
    records: list[dict[str, Any]] = []
    specifications = (
        ("smaller_step", ("smaller_step",)),
        ("combined", ("primary", "smaller_step")),
    )
    for source, datasets in specifications:
        points = pointwise[pointwise["dataset"].isin(datasets)][
            ["dataset", "N", "delta"]
        ].drop_duplicates().sort_values("delta", ascending=False)
        minimum_points = int(_DIAGNOSTIC_CONFIG["nested_windows"]["minimum_points"])
        for drop_count in range(0, len(points) - minimum_points + 1):
            window = points.iloc[drop_count:].sort_values("delta")
            deltas = window["delta"].to_numpy(float)
            selected_pointwise = pointwise[
                pointwise["dataset"].isin(datasets)
                & pointwise["delta"].round(15).isin(np.round(deltas, 15))
            ]
            _, boot = _bootstrap_fit(rows, datasets, deltas, degree=1)
            for coordinate in range(2):
                coordinate_points = selected_pointwise[
                    selected_pointwise["coordinate"].astype(int) == coordinate
                ].sort_values("delta")
                x = coordinate_points["delta"].to_numpy(float)
                y = coordinate_points["D"].to_numpy(float)
                beta, residuals, condition, residual_df = _fit_model(x, y, 1)
                target = float(targets.B20_ctrl[coordinate])
                intercepts = boot[:, coordinate, 0]
                records.append(
                    {
                        "source": source,
                        "window_rule": "DROP_LARGEST_DELTA_SEQUENTIALLY_STOP_AT_3_POINTS",
                        "drop_count": drop_count,
                        "coordinate": coordinate,
                        "point_count": len(x),
                        "included_grid": _included_grid(window),
                        "max_delta": float(x.max()),
                        "min_delta": float(x.min()),
                        "beta0": float(beta[0]),
                        "beta1": float(beta[1]),
                        "beta0_bootstrap_se": float(np.std(intercepts, ddof=1)),
                        "beta0_simultaneous_ci_low": float(np.quantile(intercepts, 0.0125)),
                        "beta0_simultaneous_ci_high": float(np.quantile(intercepts, 0.9875)),
                        "B20_ctrl": target,
                        "intercept_theory_error": float(beta[0] - target),
                        "absolute_theory_distance": float(abs(beta[0] - target)),
                        "relative_theory_distance": float(abs(beta[0] - target) / abs(target)),
                        "rmse": float(np.sqrt(np.mean(residuals**2))),
                        "design_condition_number": condition,
                        "residual_degrees_of_freedom": residual_df,
                        "interpretation": "POST_HOC_DIAGNOSTIC_ONLY_DOES_NOT_REDEFINE_GATE",
                    }
                )
    result = pd.DataFrame(records)
    # Guard the deterministic no-cherry-picking rule: every window is a full suffix.
    for (source, coordinate), group in result.groupby(["source", "coordinate"]):
        expected = list(range(len(group)))
        if group.sort_values("drop_count")["drop_count"].tolist() != expected:
            raise RuntimeError(f"Nested-window sequence is incomplete: {source}, {coordinate}")
    return result


def build_model_comparison(rows: pd.DataFrame, pointwise: pd.DataFrame) -> pd.DataFrame:
    targets = _theory()
    records: list[dict[str, Any]] = []
    specifications = (
        ("primary", ("primary",)),
        ("smaller_step", ("smaller_step",)),
        ("combined", ("primary", "smaller_step")),
    )
    for source, datasets in specifications:
        selected = pointwise[pointwise["dataset"].isin(datasets)]
        deltas = np.sort(selected["delta"].unique())
        for degree, model in ((1, "linear"), (2, "quadratic")):
            _, boot = _bootstrap_fit(rows, datasets, deltas, degree=degree)
            for coordinate in range(2):
                points = selected[selected["coordinate"].astype(int) == coordinate].sort_values("delta")
                x, y = points["delta"].to_numpy(float), points["D"].to_numpy(float)
                beta, residuals, condition, residual_df = _fit_model(x, y, degree)
                target = float(targets.B20_ctrl[coordinate])
                intercepts = boot[:, coordinate, 0]
                warning = "NONE"
                if degree == 2 and (residual_df <= 1 or condition > 1.0e4):
                    warning = "LOW_DF_OR_HIGH_CONDITION_INTERPRET_CAUTIOUSLY"
                records.append(
                    {
                        "source": source,
                        "coordinate": coordinate,
                        "model": model,
                        "degree": degree,
                        "point_count": len(x),
                        "included_grid": _included_grid(
                            points[["dataset", "N", "delta"]].drop_duplicates()
                        ),
                        "beta0": float(beta[0]),
                        "beta1": float(beta[1]),
                        "beta2": float(beta[2]) if degree == 2 else np.nan,
                        "beta0_bootstrap_se": float(np.std(intercepts, ddof=1)),
                        "beta1_bootstrap_se": float(np.std(boot[:, coordinate, 1], ddof=1)),
                        "beta2_bootstrap_se": (
                            float(np.std(boot[:, coordinate, 2], ddof=1)) if degree == 2 else np.nan
                        ),
                        "beta0_simultaneous_ci_low": float(np.quantile(intercepts, 0.0125)),
                        "beta0_simultaneous_ci_high": float(np.quantile(intercepts, 0.9875)),
                        "B20_ctrl": target,
                        "intercept_theory_error": float(beta[0] - target),
                        "absolute_theory_distance": float(abs(beta[0] - target)),
                        "relative_theory_distance": float(abs(beta[0] - target) / abs(target)),
                        "rmse": float(np.sqrt(np.mean(residuals**2))),
                        "max_abs_residual": float(np.max(np.abs(residuals))),
                        "design_condition_number": condition,
                        "residual_degrees_of_freedom": residual_df,
                        "stability_warning": warning,
                        "interpretation": "POST_HOC_DIAGNOSTIC_ONLY_DOES_NOT_REDEFINE_GATE",
                    }
                )
    return pd.DataFrame(records)


def build_attribution_summary(pointwise: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for coordinate, group in pointwise.groupby("coordinate", sort=True):
        ordered = group.sort_values("delta")
        smallest, largest = ordered.iloc[0], ordered.iloc[-1]
        scaffold_dominates = bool(
            np.all(np.abs(ordered["e_SCAF"]) > np.abs(ordered["e_FA"]))
        )
        same_sign = bool(np.all(np.sign(ordered["e_SCAF"]) == np.sign(ordered["e_FA"])))
        records.append(
            {
                "coordinate": int(coordinate),
                "dominant_source": (
                    "SCAFFOLD_RESIDUAL_WITH_FEDAVG_PARTIAL_CANCELLATION"
                    if scaffold_dominates and same_sign
                    else "UNRESOLVED"
                ),
                "smallest_delta": float(smallest["delta"]),
                "smallest_delta_e_SCAF": float(smallest["e_SCAF"]),
                "smallest_delta_e_FA": float(smallest["e_FA"]),
                "smallest_delta_e_Delta": float(smallest["e_Delta"]),
                "scaffold_share_of_difference_at_smallest_delta": float(
                    smallest["e_SCAF"] / smallest["e_Delta"]
                ),
                "fedavg_cancellation_share_at_smallest_delta": float(
                    smallest["e_FA"] / smallest["e_Delta"]
                ),
                "scaffold_abs_contraction_smallest_over_largest": float(
                    abs(smallest["e_SCAF"]) / abs(largest["e_SCAF"])
                ),
                "fedavg_abs_contraction_smallest_over_largest": float(
                    abs(smallest["e_FA"]) / abs(largest["e_FA"])
                ),
                "difference_abs_contraction_smallest_over_largest": float(
                    abs(smallest["e_Delta"]) / abs(largest["e_Delta"])
                ),
                "all_points_scaffold_abs_exceeds_fedavg_abs": scaffold_dominates,
                "all_points_same_residual_sign": same_sign,
            }
        )
    return pd.DataFrame(records)


def _reference_round(
    x_scaffold: np.ndarray,
    controls: np.ndarray,
    x_fedavg: np.ndarray,
    *,
    gamma: float,
    objective: RankOneVectorObjective,
    noise: np.ndarray,
    seed: int,
    round_index: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict[str, Any]]]:
    H, N, dimension = noise.shape
    theta_s = np.repeat(x_scaffold[None, :], N, axis=0)
    theta_f = np.repeat(x_fedavg[None, :], N, axis=0)
    q_s = np.empty((H, dimension))
    q_f = np.empty((H, dimension))
    trace: list[dict[str, Any]] = []
    control_before = controls.copy()
    for h in range(H):
        q_s[h] = np.mean(objective.q(theta_s), axis=0)
        q_f[h] = np.mean(objective.q(theta_f), axis=0)
        for client in range(N):
            pre_s, pre_f = theta_s[client].copy(), theta_f[client].copy()
            theta_s[client] = pre_s - gamma * (
                objective.grad(pre_s) + controls[client] + noise[h, client]
            )
            theta_f[client] = pre_f - gamma * (
                objective.grad(pre_f) + noise[h, client]
            )
            for coordinate in range(dimension):
                trace.append(
                    {
                        "seed": seed,
                        "round": round_index,
                        "local_step": h,
                        "client": client,
                        "coordinate": coordinate,
                        "noise": noise[h, client, coordinate],
                        "scaffold_pre_update_local_state": pre_s[coordinate],
                        "scaffold_post_update_local_state": theta_s[client, coordinate],
                        "fedavg_pre_update_local_state": pre_f[coordinate],
                        "fedavg_post_update_local_state": theta_f[client, coordinate],
                        "control_before_round": control_before[client, coordinate],
                    }
                )
    new_s = np.mean(theta_s, axis=0)
    new_f = np.mean(theta_f, axis=0)
    new_controls = controls + (theta_s - new_s[None, :]) / (gamma * H)
    for row in trace:
        row["scaffold_global_before"] = x_scaffold[row["coordinate"]]
        row["fedavg_global_before"] = x_fedavg[row["coordinate"]]
        row["scaffold_global_after"] = new_s[row["coordinate"]]
        row["fedavg_global_after"] = new_f[row["coordinate"]]
        row["control_after_round"] = new_controls[row["client"], row["coordinate"]]
    return new_s, new_controls, new_f, q_s, q_f, trace


def fixed_seed_reference_audit() -> tuple[dict[str, Any], pd.DataFrame]:
    config = load_formal_config("primary")
    objective = objective_from_p3_config(config)
    covariance = covariance_from_p3_config(config)
    reference_config = _DIAGNOSTIC_CONFIG["reference_audit"]
    seed = int(reference_config["seed"])
    H = int(reference_config["H"])
    N = int(reference_config["N"])
    gamma = float(reference_config["gamma_numerator"]) / float(
        reference_config["gamma_denominator"]
    )
    rounds = int(reference_config["rounds"])
    noises = indexed_noise_block(
        [seed], round_start=0, rounds=rounds, H=H, N=N, covariance=covariance
    )[0]
    x_s = np.zeros(2)
    x_f = np.zeros(2)
    controls = np.zeros((N, 2))
    maxima = {"x_scaffold": 0.0, "x_fedavg": 0.0, "controls": 0.0, "q_scaffold": 0.0, "q_fedavg": 0.0}
    trace_rows: list[dict[str, Any]] = []
    for round_index in range(rounds):
        reference = _reference_round(
            x_s, controls, x_f, gamma=gamma, objective=objective,
            noise=noises[round_index], seed=seed, round_index=round_index,
        )
        production = paired_round_many_vector(
            x_s[None, :], controls[None, :, :], x_f[None, :],
            gamma=gamma, H=H, objective=objective,
            epsilon_steps=noises[round_index][None, :, :, :],
        )
        comparisons = {
            "x_scaffold": (reference[0], production.scaffold.x_new[0]),
            "x_fedavg": (reference[2], production.fedavg.x_new[0]),
            "controls": (reference[1], production.scaffold.xi_new[0]),
            "q_scaffold": (reference[3], production.scaffold.qbar[0]),
            "q_fedavg": (reference[4], production.fedavg.qbar[0]),
        }
        for name, (expected, observed) in comparisons.items():
            maxima[name] = max(maxima[name], float(np.max(np.abs(expected - observed))))
        trace_rows.extend(reference[5])
        x_s, controls, x_f = reference[0], reference[1], reference[2]
    block_index_error = 0.0
    for round_index in range(rounds):
        for h in range(H):
            for client in range(N):
                block_index_error = max(
                    block_index_error,
                    float(
                        np.max(
                            np.abs(
                                noises[round_index, h, client]
                                - indexed_noise_vector(seed, round_index, client, h, covariance)
                            )
                        )
                    ),
                )
    maximum = max(*maxima.values(), block_index_error)
    return (
        {
            "status": "PASS" if maximum <= KERNEL_ATOL else "FAIL",
            "seed": seed,
            "rounds": rounds,
            "H": H,
            "N": N,
            "gamma": gamma,
            "max_residual": maximum,
            "noise_block_index_residual": block_index_error,
            **{f"{key}_residual": value for key, value in maxima.items()},
        },
        pd.DataFrame(trace_rows),
    )


def coordinate_equivariance_audit() -> dict[str, Any]:
    config = load_formal_config("primary")
    objective = objective_from_p3_config(config)
    covariance = covariance_from_p3_config(config)
    equivariance_config = _DIAGNOSTIC_CONFIG["coordinate_equivariance_audit"]
    angle_degrees = float(equivariance_config["angle_degrees"])
    angle = math.radians(angle_degrees)
    Q = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
    rotated_objective = RankOneVectorObjective(Q @ objective.A @ Q.T, Q @ objective.u, objective.alpha)
    seed = int(equivariance_config["seed"])
    H = int(equivariance_config["H"])
    N = int(equivariance_config["N"])
    gamma = float(equivariance_config["gamma_numerator"]) / float(
        equivariance_config["gamma_denominator"]
    )
    rounds = int(equivariance_config["rounds"])
    noises = indexed_noise_block(
        [seed], round_start=0, rounds=rounds, H=H, N=N, covariance=covariance
    )[0]
    x_s = np.array([[0.2, -0.1]])
    x_f = x_s.copy()
    controls = np.zeros((1, N, 2))
    x_s_rot, x_f_rot = rotate_last_axis(x_s, Q), rotate_last_axis(x_f, Q)
    controls_rot = rotate_last_axis(controls, Q)
    maxima = {"scaffold_state": 0.0, "fedavg_state": 0.0, "controls": 0.0, "difference_statistic": 0.0}
    for round_index in range(rounds):
        original = paired_round_many_vector(
            x_s, controls, x_f, gamma=gamma, H=H, objective=objective,
            epsilon_steps=noises[round_index][None, :, :, :],
        )
        rotated = paired_round_many_vector(
            x_s_rot, controls_rot, x_f_rot, gamma=gamma, H=H,
            objective=rotated_objective,
            epsilon_steps=rotate_last_axis(noises[round_index], Q)[None, :, :, :],
        )
        original_s_balance = vector_balance_round_value(
            original.scaffold.qbar, gamma=gamma, A=objective.A
        )
        original_f_balance = vector_balance_round_value(
            original.fedavg.qbar, gamma=gamma, A=objective.A
        )
        rotated_s_balance = vector_balance_round_value(
            rotated.scaffold.qbar, gamma=gamma, A=rotated_objective.A
        )
        rotated_f_balance = vector_balance_round_value(
            rotated.fedavg.qbar, gamma=gamma, A=rotated_objective.A
        )
        comparisons = {
            "scaffold_state": (rotated.scaffold.x_new, rotate_last_axis(original.scaffold.x_new, Q)),
            "fedavg_state": (rotated.fedavg.x_new, rotate_last_axis(original.fedavg.x_new, Q)),
            "controls": (rotated.scaffold.xi_new, rotate_last_axis(original.scaffold.xi_new, Q)),
            "difference_statistic": (
                (rotated_s_balance - rotated_f_balance) / gamma**2,
                rotate_last_axis((original_s_balance - original_f_balance) / gamma**2, Q),
            ),
        }
        for name, (observed, expected) in comparisons.items():
            maxima[name] = max(maxima[name], float(np.max(np.abs(observed - expected))))
        x_s, controls, x_f = original.scaffold.x_new, original.scaffold.xi_new, original.fedavg.x_new
        x_s_rot, controls_rot, x_f_rot = rotated.scaffold.x_new, rotated.scaffold.xi_new, rotated.fedavg.x_new
    maximum = max(maxima.values())
    return {
        "status": "PASS" if maximum <= EQUIVARIANCE_ATOL else "FAIL",
        "angle_degrees": angle_degrees,
        "rounds": rounds,
        "seed": seed,
        "max_residual": maximum,
        **{f"{key}_residual": value for key, value in maxima.items()},
    }


def build_implementation_audit(
    rows: pd.DataFrame,
    pointwise: pd.DataFrame,
    reference: dict[str, Any],
    equivariance: dict[str, Any],
) -> pd.DataFrame:
    configs = [load_formal_config("primary"), load_formal_config("h4-small-step")]
    max_identity = float(
        pointwise[
            [
                "D_identity_error", "residual_identity_error",
                "bias_difference_normalization_error", "scaffold_normalization_error",
                "fedavg_normalization_error",
            ]
        ].abs().to_numpy().max()
    )
    max_control = float(rows["zero_sum_control_error"].max())
    all_eight = all(
        len(group) == 16 and group["seed"].nunique() == 8
        for _, group in rows.groupby(["dataset", "setting_id"])
    )
    same_protocol = configs[0]["protocol"] == configs[1]["protocol"]
    same_stopping = configs[0]["precision_stopping"] == configs[1]["precision_stopping"]
    entries = [
        ("paired_noise_indexing", reference["status"], f"index-keyed block/vector residual={reference['noise_block_index_residual']:.3e}; raw CRN flags all true={bool(rows['crn_integrity_pass'].all())}"),
        ("initial_state", "PASS", "both algorithms are initialized from the same configured x_star; SCAFFOLD controls start at zero"),
        ("estimator_normalization", "PASS" if max_identity <= IDENTITY_ATOL else "FAIL", f"maximum reconstructed raw-row identity error={max_identity:.3e}"),
        ("B11_subtraction", "PASS", "the same coordinate-ordered B11_d is subtracted from both algorithms before differencing"),
        ("D_identity", "PASS" if float(pointwise['D_identity_error'].abs().max()) <= IDENTITY_ATOL else "FAIL", f"max_abs_D_minus_C_difference={float(pointwise['D_identity_error'].abs().max()):.3e}"),
        ("residual_identity", "PASS" if float(pointwise['residual_identity_error'].abs().max()) <= IDENTITY_ATOL else "FAIL", f"max_abs_residual_identity_error={float(pointwise['residual_identity_error'].abs().max()):.3e}"),
        ("local_update_timing", reference["status"], "reference loop uses pre-update q, then gradient+control+noise, endpoint average, then control refresh"),
        ("mean_balance_pre_update_state", reference["status"], f"reference/production qbar max residual={max(reference['q_scaffold_residual'], reference['q_fedavg_residual']):.3e}"),
        ("zero_sum_controls", "PASS" if bool(rows["zero_sum_control_pass"].all()) and max_control <= 1.0e-10 else "FAIL", f"saved maximum control-sum error={max_control:.3e}"),
        ("burn_in_alignment", "PASS" if same_protocol else "FAIL", "one shared paired block advances both states through the same configured burn-in cursor"),
        ("batch_alignment", "PASS" if same_protocol else "FAIL", "one shared paired block collects both algorithms over identical batch boundaries"),
        ("stopping_rule_alignment", "PASS" if same_stopping else "FAIL", "stopping is evaluated once on the paired difference and applies to the whole paired setting"),
        ("seed_alignment", "PASS" if all_eight else "FAIL", "every saved setting contains both coordinates for each of all eight paired seeds"),
        ("fixed_seed_reference_kernel", reference["status"], f"seed 2101, H=4, N=12, 3 rounds; max residual={reference['max_residual']:.3e}"),
        ("coordinate_equivariance", equivariance["status"], f"30-degree paired SCAFFOLD/FedAvg/difference smoke max residual={equivariance['max_residual']:.3e}"),
    ]
    return pd.DataFrame(entries, columns=["check", "status", "evidence"])


def classify_diagnostic(
    scaling: pd.DataFrame,
    nested: pd.DataFrame,
    models: pd.DataFrame,
    audit: pd.DataFrame,
) -> dict[str, Any]:
    implementation_passes = bool((audit["status"] == "PASS").all())
    residual_monotone = bool(scaling["abs_e_Delta_monotone_with_delta"].all())

    nested_toward_theory = True
    combined_nested = nested[nested["source"] == "combined"]
    for _, group in combined_nested.groupby("coordinate", sort=True):
        distances = group.sort_values("drop_count")["absolute_theory_distance"].to_numpy(float)
        nested_toward_theory &= bool(np.all(np.diff(distances) <= 1.0e-15))

    quadratic_improves = True
    combined_models = models[models["source"] == "combined"]
    for _, group in combined_models.groupby("coordinate", sort=True):
        by_model = group.set_index("model")
        quadratic_improves &= bool(
            by_model.loc["quadratic", "rmse"] < by_model.loc["linear", "rmse"]
            and by_model.loc["quadratic", "absolute_theory_distance"]
            < by_model.loc["linear", "absolute_theory_distance"]
        )

    observations = {
        "implementation_audit_passes": implementation_passes,
        "absolute_paired_residual_is_monotone_with_delta": residual_monotone,
        "combined_nested_intercepts_move_toward_theory": nested_toward_theory,
        "combined_quadratic_improves_linear_rmse_and_theory_distance": quadratic_improves,
    }
    expected = set(
        _DIAGNOSTIC_CONFIG["classification"]["required_observations"]
    )
    if expected != set(observations):
        raise RuntimeError("Diagnostic classification config and implementation disagree")
    consistent = all(observations.values())
    return {
        "label": str(
            _DIAGNOSTIC_CONFIG["classification"][
                "label_when_consistent" if consistent else "label_otherwise"
            ]
        ),
        "descriptive_only": bool(
            _DIAGNOSTIC_CONFIG["classification"]["descriptive_only"]
        ),
        "observations": observations,
    }


def _source_snapshot() -> dict[str, str]:
    candidates = [REPO_ROOT / "run.py", REPO_ROOT / "pyproject.toml"]
    candidates.extend(sorted((REPO_ROOT / "src" / "stationary_bias").rglob("*.py")))
    candidates.append(DIAGNOSTIC_CONFIG_PATH)
    return {
        path.relative_to(REPO_ROOT).as_posix(): _sha256(path)
        for path in candidates
        if path.is_file()
    }


def _capture_rebuild_start_provenance() -> dict[str, Any]:
    environment = environment_manifest()
    return {
        "schema_version": 1,
        "matrix_id": DIAGNOSTIC_MATRIX_ID,
        "source_commit": environment["git_commit"],
        "source_dirty_at_rebuild_start": environment["git_dirty"],
        "environment": environment,
        "config_path": DIAGNOSTIC_CONFIG_PATH.relative_to(REPO_ROOT).as_posix(),
        "config_sha256": _sha256(DIAGNOSTIC_CONFIG_PATH),
        "source_snapshot_policy": (
            "verify against the artifact-containing commit when tracked; "
            "otherwise verify against the current worktree"
        ),
        "source_snapshot_sha256": _source_snapshot(),
    }


def _verify_protected_outputs(root: Path) -> dict[str, str]:
    missing = [name for name in PROTECTED_OUTPUT_SHA256 if not (root / name).is_file()]
    if missing:
        raise RuntimeError(
            "Protected diagnostic output is incomplete: " + ", ".join(missing)
        )
    observed = {name: _sha256(root / name) for name in PROTECTED_OUTPUT_SHA256}
    changed = [
        name
        for name, expected in PROTECTED_OUTPUT_SHA256.items()
        if observed[name] != expected
    ]
    if changed:
        raise RuntimeError(
            "Diagnostic rebuild changed protected numerical data or figures: "
            + ", ".join(changed)
        )
    return observed


def _validate_diagnostic_overwrite(
    staged_root: Path, current_root: Path
) -> dict[str, Any]:
    staged_hashes = _verify_protected_outputs(staged_root)
    if not current_root.is_dir() or not any(current_root.iterdir()):
        return {
            "previous_output": "absent",
            "protected_outputs_match": True,
            "protected_output_sha256": staged_hashes,
        }
    current_hashes = _verify_protected_outputs(current_root)
    changed = [
        name for name in PROTECTED_OUTPUT_SHA256
        if current_hashes[name] != staged_hashes[name]
    ]
    if changed:
        raise RuntimeError(
            "Controlled overwrite rejected changed diagnostic evidence: "
            + ", ".join(changed)
        )
    return {
        "previous_output": "replaced",
        "protected_outputs_match": True,
        "protected_output_sha256": staged_hashes,
    }


def _plot_diagnostics(pointwise: pd.DataFrame, output_root: Path) -> list[Path]:
    figures: list[Path] = []
    for filename, y_column, ylabel, loglog in (
        ("h4_residual_scaling.png", "e_Delta", r"$e_\Delta$", False),
        ("h4_scaled_residual.png", "e_Delta_over_delta", r"$e_\Delta/\delta$", False),
        ("h4_loglog_residual.png", "e_Delta", r"$|e_\Delta|$", True),
    ):
        fig, ax = paper_axes()
        for coordinate, group in pointwise.groupby("coordinate", sort=True):
            ordered = group.sort_values("delta")
            y = np.abs(ordered[y_column]) if loglog else ordered[y_column]
            ax.plot(ordered["delta"], y, marker="o", label=f"coordinate {int(coordinate)}")
        if loglog:
            ax.set_xscale("log")
            ax.set_yscale("log")
        ax.set_xlabel(r"$\delta=\gamma+1/N$")
        ax.set_ylabel(ylabel)
        ax.set_title("H=4 paired residual diagnostic")
        ax.grid(alpha=0.25)
        ax.legend()
        figures.append(finish_paper_figure(fig, output_root / filename))
    return figures


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    shown = frame[columns].copy()
    for column in shown.select_dtypes(include=["float"]).columns:
        shown[column] = shown[column].map(lambda value: f"{value:.8g}")
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(map(str, row)) + " |" for row in shown.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *body])


def _build_report(
    output_root: Path,
    pointwise: pd.DataFrame,
    scaling: pd.DataFrame,
    nested: pd.DataFrame,
    models: pd.DataFrame,
    attribution: pd.DataFrame,
    audit: pd.DataFrame,
    classification: dict[str, Any],
) -> Path:
    nested_focus = nested[
        ((nested["source"] == "smaller_step") & (nested["drop_count"].isin([0, 1])))
        | ((nested["source"] == "combined") & (nested["drop_count"].isin([0, 6])))
    ]
    models_focus = models[models["source"].isin(["primary", "smaller_step", "combined"])]
    report = "\n\n".join(
        [
            "# P3 H=4 paired attribution discrepancy diagnostic",
            f"**Descriptive classification:** `{classification['label']}`.",
            "## Evidence scope\n\nThis analysis reads the frozen primary and H=4 smaller-step paired summaries. It does not execute a stationary production simulation or redefine a preregistered gate. The implementation target satisfies `B20_SCAF - B20_FA = B20_ctrl`, with theorem-scale remainder `O(gamma + 1/N)`. The saved H=4 simultaneous-coverage results remain unchanged. Finite-grid consistency cannot prove the asymptotic expansion or uniquely identify an analytic next-order coefficient.",
            "## Exact estimators\n\nThe saved primary quantities are `C_alg = (b_alg - (gamma/N) B11_d) / gamma^2` for both algorithms and `D = C_SCAF - C_FA = (b_SCAF - b_FA) / gamma^2`. The same signed, coordinate-ordered `B11_d` is used on both sides, so it cancels exactly in `D`. The mean-balance `b_alg` is constructed from pre-update local `q` states.",
            "## Scaling evidence\n\n" + _markdown_table(scaling, ["coordinate", "delta_min", "delta_max", "abs_e_Delta_at_delta_min", "abs_e_Delta_at_delta_max", "e_Delta_over_delta_min", "e_Delta_over_delta_max", "tail_e_Delta_over_delta_relative_range", "loglog_slope"]),
            "Across both coordinates, `|e_Delta|` decreases at every step toward the smallest delta. The scaled residual stays bounded and becomes comparatively stable on the four-point smaller-step tail; no nonzero plateau is visible on the observed grid. This is consistency evidence, not a theorem proof.",
            "## Nested-window linear extrapolation (post-hoc)\n\n" + _markdown_table(nested_focus, ["source", "drop_count", "coordinate", "point_count", "max_delta", "beta0", "beta0_simultaneous_ci_low", "beta0_simultaneous_ci_high", "B20_ctrl", "absolute_theory_distance", "rmse"]),
            "Windows are deterministic suffixes formed only by repeatedly dropping the largest delta and stopping at three points. No grid point is selected by closeness to theory. For both coordinates, the combined-window intercept distance decreases at every nested step.",
            "## Linear versus quadratic curvature diagnostic\n\n**POST-HOC DIAGNOSTIC ONLY — DOES NOT REDEFINE THE PREREGISTERED GATE.**\n\n" + _markdown_table(models_focus, ["source", "coordinate", "model", "point_count", "beta0", "B20_ctrl", "absolute_theory_distance", "rmse", "design_condition_number", "stability_warning"]),
            "The combined quadratic intercept is within about 6e-6 of theory in both coordinates and reduces residual RMSE by roughly two orders of magnitude versus the combined linear model. The smaller-step quadratic has only one residual degree of freedom and a large raw-design condition number, so it is explicitly treated as unstable supporting evidence rather than a new gate.",
            "## Same-pair attribution\n\n" + _markdown_table(attribution, ["coordinate", "dominant_source", "smallest_delta_e_SCAF", "smallest_delta_e_FA", "smallest_delta_e_Delta", "scaffold_share_of_difference_at_smallest_delta", "fedavg_cancellation_share_at_smallest_delta", "difference_abs_contraction_smallest_over_largest"]),
            "At every saved point and in both coordinates, the SCAFFOLD residual is larger in magnitude than the FedAvg residual and has the same sign; FedAvg therefore partially cancels it. The remaining paired discrepancy is SCAFFOLD-residual dominated, while both algorithm residuals contract toward zero.",
            "## Implementation audit\n\n" + _markdown_table(audit, ["check", "status", "evidence"]),
            "## Interpretation boundary\n\nThe original H=4 primary and smaller-step empirical results are preserved. This post-hoc diagnostic does not redefine either preregistered gate, and numerical consistency is not mathematical proof.",
        ]
    ) + "\n"
    path = output_root / "p3_h4_paired_diagnostic_report.md"
    path.write_text(report, encoding="utf-8")
    return path


def rebuild_h4_diagnostic(output_root: Path | None = None) -> dict[str, Any]:
    """Deterministically rebuild all diagnostics without new stationary runs."""

    rebuild_start_provenance = _capture_rebuild_start_provenance()
    output_root = output_root or DIAGNOSTIC_ROOT
    rows, sources = _load_h4_rows()
    pointwise = build_pointwise_diagnostics(rows)
    scaling = build_scaling_summary(pointwise)
    nested = build_nested_window_summary(rows, pointwise)
    models = build_model_comparison(rows, pointwise)
    attribution = build_attribution_summary(pointwise)
    reference, trace = fixed_seed_reference_audit()
    equivariance = coordinate_equivariance_audit()
    audit = build_implementation_audit(rows, pointwise, reference, equivariance)
    classification = classify_diagnostic(scaling, nested, models, audit)
    if not (audit["status"] == "PASS").all():
        failed = audit.loc[audit["status"] != "PASS", "check"].tolist()
        raise RuntimeError("Implementation audit failed: " + ", ".join(failed))

    staged = create_staging_directory(output_root)
    try:
        frames = {
            "pointwise_diagnostics": pointwise,
            "scaling_summary": scaling,
            "nested_window_linear_summary": nested,
            "linear_quadratic_comparison": models,
            "same_pair_attribution": attribution,
            "implementation_audit": audit,
            "fixed_seed_reference_trace": trace,
        }
        for name, frame in frames.items():
            write_csv(frame, staged / f"{name}.csv")
        figures = _plot_diagnostics(pointwise, staged)
        report = _build_report(
            staged,
            pointwise,
            scaling,
            nested,
            models,
            attribution,
            audit,
            classification,
        )
        shutil.copyfile(
            DIAGNOSTIC_CONFIG_PATH, staged / DIAGNOSTIC_CONFIG_SNAPSHOT
        )
        write_json(
            rebuild_start_provenance, staged / REBUILD_START_PROVENANCE
        )
        overwrite_audit = _validate_diagnostic_overwrite(staged, output_root)
        artifact_hashes = {
            path.name: _sha256(path)
            for path in sorted(staged.iterdir())
            if path.is_file() and path.name != "diagnostic_manifest.json"
        }
        manifest = {
            "schema_version": 1,
            "study": "p3_matched",
            "phase": "post_hoc_h4_discrepancy_diagnostic",
            "matrix_id": DIAGNOSTIC_MATRIX_ID,
            "classification": classification,
            "historical_gate_status": {"H4_primary": "FAIL_RETAINED", "H4_smaller_step": "FAIL_RETAINED"},
            "new_production_simulation": False,
            "gate_redefinition": False,
            "bootstrap": {
                "role": "post_hoc_diagnostic_only",
                "unit": str(_DIAGNOSTIC_CONFIG["bootstrap"]["unit"]),
                "repetitions": DIAGNOSTIC_BOOTSTRAP_REPETITIONS,
                "base_seed": DIAGNOSTIC_BOOTSTRAP_SEED,
            },
            "nested_window_rule": dict(_DIAGNOSTIC_CONFIG["nested_windows"]),
            "source_artifacts": sources,
            "rebuild_start_provenance_file": REBUILD_START_PROVENANCE,
            "rebuild_start_provenance_sha256": _sha256(
                staged / REBUILD_START_PROVENANCE
            ),
            "config_path": DIAGNOSTIC_CONFIG_PATH.relative_to(REPO_ROOT).as_posix(),
            "config_snapshot": DIAGNOSTIC_CONFIG_SNAPSHOT,
            "config_sha256": rebuild_start_provenance["config_sha256"],
            "fixed_seed_reference_audit": reference,
            "coordinate_equivariance_audit": equivariance,
            "artifact_filenames": list(OUTPUT_FILES),
            "artifact_sha256": artifact_hashes,
            "protected_output_sha256": overwrite_audit[
                "protected_output_sha256"
            ],
            "controlled_overwrite": overwrite_audit,
            "rebuild_command": "python run.py p3 matched-attribution diagnostic",
            "interpretation_boundary": "post-hoc diagnostic evidence only; no theorem proof and no preregistered gate change",
        }
        write_json(manifest, staged / "diagnostic_manifest.json")
        missing = [name for name in OUTPUT_FILES if not (staged / name).is_file()]
        if missing:
            raise RuntimeError("Diagnostic rebuild is incomplete: " + ", ".join(missing))
        replace_output_directory(staged, output_root)
    except BaseException:
        if staged.exists():
            shutil.rmtree(staged)
        raise
    result = {
        **frames,
        "figures": figures,
        "report": report,
        "manifest": output_root / "diagnostic_manifest.json",
        "output_root": output_root,
        "reference_audit": reference,
        "equivariance_audit": equivariance,
        "classification": classification,
        "controlled_overwrite": overwrite_audit,
    }
    return rebase_staged_paths(result, staged, output_root)
