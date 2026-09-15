"""Paired inference, neutral falsification summaries, and reports for P1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ...core.inference.statistics import linear_fit, student_t_summary
from ...core.io import config_hash, load_configs, write_csv, write_json
from .simulation import (
    P1_CONFIG_PATH,
    P1_RESULT_ROOT,
    P1_RUN_START_PROVENANCE,
    audit_p1_run_matrix,
    load_p1_config,
)


ALGORITHM_SETTING_KEYS = ["grid_name", "algorithm", "H", "N", "gamma"]
PAIR_SETTING_KEYS = ["grid_name", "H", "N", "gamma"]
FIT_COLUMNS = [
    "grid_name",
    "H",
    "bootstrap_unit",
    "bootstrap_repetitions",
    "bootstrap_seed_fedavg",
    "bootstrap_seed_delta",
    "fedavg_intercept",
    "fedavg_intercept_ci_low",
    "fedavg_intercept_ci_high",
    "fedavg_slope",
    "delta_intercept",
    "delta_intercept_ci_low",
    "delta_intercept_ci_high",
    "delta_slope",
]
CONTRACTION_COLUMNS = [
    "quantity",
    "grid_name",
    "H",
    "num_settings",
    "smaller_step_error_decreases",
    "possible_decreases",
    "scaled_error_min",
    "scaled_error_max",
    "assessment",
]


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().map({"true": True, "false": False}).fillna(False)


def build_algorithm_summary(run_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, group in run_df.groupby(ALGORITHM_SETTING_KEYS, sort=False):
        C = student_t_summary(group["C_balance"].to_numpy(float))
        direct = student_t_summary(group["b_direct"].to_numpy(float))
        balance = student_t_summary(group["b_balance"].to_numpy(float))
        target = float(group["B20_target"].iloc[0])
        gate = bool(_bool_series(group["gate_pass"]).all())
        contains = C.ci_low <= target <= C.ci_high
        row = dict(zip(ALGORITHM_SETTING_KEYS, key, strict=True))
        row.update(
            {
                "num_pairs": len(group),
                "b_direct_mean": direct.mean,
                "b_direct_se": direct.se,
                "b_direct_ci_low": direct.ci_low,
                "b_direct_ci_high": direct.ci_high,
                "b_balance_mean": balance.mean,
                "b_balance_se": balance.se,
                "b_balance_ci_low": balance.ci_low,
                "b_balance_ci_high": balance.ci_high,
                "C_mean": C.mean,
                "C_std": C.std,
                "C_se": C.se,
                "C_ci_low": C.ci_low,
                "C_ci_high": C.ci_high,
                "B20_target": target,
                "error_to_target": C.mean - target,
                "scaled_error": (C.mean - target) / float(row["gamma"]),
                "target_in_95pct_ci": contains,
                "gate_pass": gate,
                "falsification_status": (
                    "INCONCLUSIVE"
                    if not gate
                    else "CONSISTENT"
                    if contains
                    else "INCONSISTENT"
                ),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def build_pair_setting_summary(pair_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, group in pair_df.groupby(PAIR_SETTING_KEYS, sort=False):
        # Delta inference is performed on the per-seed paired differences,
        # never by subtracting two independently constructed confidence limits.
        delta = student_t_summary(group["Delta_C"].to_numpy(float))
        target = float(group["Delta_B20_target"].iloc[0])
        gate = bool(_bool_series(group["pair_gate_pass"]).all())
        contains = delta.ci_low <= target <= delta.ci_high
        row = dict(zip(PAIR_SETTING_KEYS, key, strict=True))
        row.update(
            {
                "num_pairs": len(group),
                "Delta_C_mean": delta.mean,
                "Delta_C_std": delta.std,
                "Delta_C_se": delta.se,
                "Delta_C_ci_low": delta.ci_low,
                "Delta_C_ci_high": delta.ci_high,
                "Delta_B20_target": target,
                "error_delta": delta.mean - target,
                "scaled_error_delta": (delta.mean - target) / float(row["gamma"]),
                "target_in_95pct_ci": contains,
                "pair_gate_pass": gate,
                "falsification_status": (
                    "INCONCLUSIVE"
                    if not gate
                    else "CONSISTENT"
                    if contains
                    else "INCONSISTENT"
                ),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def build_falsification_summary(
    algorithm_summary: pd.DataFrame, pair_summary: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    fedavg = algorithm_summary[algorithm_summary["algorithm"] == "fedavg"]
    for _, row in fedavg.iterrows():
        rows.append(
            {
                "target_type": "fedavg_coefficient",
                "grid_name": row["grid_name"],
                "H": int(row["H"]),
                "N": int(row["N"]),
                "gamma": float(row["gamma"]),
                "estimate": float(row["C_mean"]),
                "ci_low": float(row["C_ci_low"]),
                "ci_high": float(row["C_ci_high"]),
                "theory_target": float(row["B20_target"]),
                "error": float(row["error_to_target"]),
                "gate_pass": bool(row["gate_pass"]),
                "status": row["falsification_status"],
            }
        )
    for _, row in pair_summary.iterrows():
        rows.append(
            {
                "target_type": "scaffold_minus_fedavg",
                "grid_name": row["grid_name"],
                "H": int(row["H"]),
                "N": int(row["N"]),
                "gamma": float(row["gamma"]),
                "estimate": float(row["Delta_C_mean"]),
                "ci_low": float(row["Delta_C_ci_low"]),
                "ci_high": float(row["Delta_C_ci_high"]),
                "theory_target": float(row["Delta_B20_target"]),
                "error": float(row["error_delta"]),
                "gate_pass": bool(row["pair_gate_pass"]),
                "status": row["falsification_status"],
            }
        )
    return pd.DataFrame(rows)


def _paired_bootstrap_linear_fit(
    frame: pd.DataFrame,
    *,
    value_column: str,
    repetitions: int,
    seed: int,
) -> dict[str, float]:
    grouped = list(frame.groupby("gamma", sort=True))
    gammas = np.array([float(gamma) for gamma, _ in grouped])
    seed_sets = [set(group["seed"].astype(int)) for _, group in grouped]
    if len(grouped) < 2 or any(values != seed_sets[0] for values in seed_sets[1:]):
        raise ValueError("Paired bootstrap requires at least two settings with identical seeds")
    seeds = np.array(sorted(seed_sets[0]), dtype=int)
    values_by_gamma = {
        float(gamma): dict(zip(group["seed"].astype(int), group[value_column].astype(float), strict=True))
        for gamma, group in grouped
    }
    means = np.array(
        [np.mean([values_by_gamma[gamma][item] for item in seeds]) for gamma in gammas]
    )
    intercept, slope = linear_fit(gammas, means)
    rng = np.random.default_rng(seed)
    boot_intercepts = np.empty(repetitions, dtype=np.float64)
    for index in range(repetitions):
        sampled = rng.choice(seeds, size=seeds.size, replace=True)
        sampled_means = np.array(
            [
                np.mean([values_by_gamma[gamma][int(item)] for item in sampled])
                for gamma in gammas
            ]
        )
        boot_intercepts[index], _ = linear_fit(gammas, sampled_means)
    low, high = np.quantile(boot_intercepts, [0.025, 0.975])
    return {
        "intercept": intercept,
        "slope": slope,
        "intercept_ci_low": float(low),
        "intercept_ci_high": float(high),
    }


def build_fit_summary(pair_df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    repetitions = int(config["inference"]["bootstrap_repetitions"])
    seed = int(config["inference"]["bootstrap_seed"])
    rows: list[dict[str, Any]] = []
    for (grid_name, H), group in pair_df.groupby(["grid_name", "H"], sort=False):
        if group["gamma"].nunique() < 2:
            continue
        fedavg = _paired_bootstrap_linear_fit(
            group,
            value_column="C_fedavg",
            repetitions=repetitions,
            seed=seed,
        )
        delta = _paired_bootstrap_linear_fit(
            group,
            value_column="Delta_C",
            repetitions=repetitions,
            seed=seed + 1,
        )
        rows.append(
            {
                "grid_name": grid_name,
                "H": int(H),
                "bootstrap_unit": "matched_chain_pair",
                "bootstrap_repetitions": repetitions,
                "bootstrap_seed_fedavg": seed,
                "bootstrap_seed_delta": seed + 1,
                "fedavg_intercept": fedavg["intercept"],
                "fedavg_intercept_ci_low": fedavg["intercept_ci_low"],
                "fedavg_intercept_ci_high": fedavg["intercept_ci_high"],
                "fedavg_slope": fedavg["slope"],
                "delta_intercept": delta["intercept"],
                "delta_intercept_ci_low": delta["intercept_ci_low"],
                "delta_intercept_ci_high": delta["intercept_ci_high"],
                "delta_slope": delta["slope"],
            }
        )
    return pd.DataFrame(rows, columns=FIT_COLUMNS)


def build_contraction_summary(
    algorithm_summary: pd.DataFrame, pair_summary: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    sources = [
        (
            "fedavg",
            algorithm_summary[algorithm_summary["algorithm"] == "fedavg"],
            "error_to_target",
            "scaled_error",
        ),
        ("delta", pair_summary, "error_delta", "scaled_error_delta"),
    ]
    for quantity, frame, error_column, scaled_column in sources:
        for (grid_name, H), group in frame.groupby(["grid_name", "H"], sort=False):
            ordered = group.sort_values("gamma", ascending=False)
            if len(ordered) < 2:
                continue
            absolute_errors = np.abs(ordered[error_column].to_numpy(float))
            decreases = int(np.sum(absolute_errors[1:] < absolute_errors[:-1]))
            scaled = ordered[scaled_column].to_numpy(float)
            rows.append(
                {
                    "quantity": quantity,
                    "grid_name": grid_name,
                    "H": int(H),
                    "num_settings": len(ordered),
                    "smaller_step_error_decreases": decreases,
                    "possible_decreases": len(ordered) - 1,
                    "scaled_error_min": float(np.min(scaled)),
                    "scaled_error_max": float(np.max(scaled)),
                    "assessment": "DESCRIPTIVE_ONLY",
                }
            )
    return pd.DataFrame(rows, columns=CONTRACTION_COLUMNS)


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No rows."
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


def _report_text(
    run_df: pd.DataFrame,
    algorithm_summary: pd.DataFrame,
    pair_summary: pd.DataFrame,
    fits: pd.DataFrame,
    contraction: pd.DataFrame,
) -> str:
    phase = "smoke" if set(run_df["phase"]) == {"smoke"} else "formal"
    return "\n".join(
        [
            "# P1 Matched FedAvg vs SCAFFOLD",
            "",
            f"Run phase: **{phase.upper()}**",
            "",
            "Smoke outputs are implementation diagnostics only and must not be interpreted scientifically."
            if phase == "smoke"
            else "Theory targets are evaluated without altering the simulated trajectories.",
            "",
            "## Individual algorithm coefficients",
            "",
            _markdown_table(
                algorithm_summary,
                [
                    "grid_name",
                    "algorithm",
                    "H",
                    "N",
                    "gamma",
                    "C_mean",
                    "C_ci_low",
                    "C_ci_high",
                    "B20_target",
                    "error_to_target",
                    "gate_pass",
                    "falsification_status",
                ],
            ),
            "",
            "## Paired SCAFFOLD-minus-FedAvg differences",
            "",
            _markdown_table(
                pair_summary,
                [
                    "grid_name",
                    "H",
                    "N",
                    "gamma",
                    "Delta_C_mean",
                    "Delta_C_ci_low",
                    "Delta_C_ci_high",
                    "Delta_B20_target",
                    "error_delta",
                    "pair_gate_pass",
                    "falsification_status",
                ],
            ),
            "",
            "## Matched-pair bootstrap fits",
            "",
            _markdown_table(fits, list(fits.columns)) if not fits.empty else "No multi-setting grid was run.",
            "",
            "## O(gamma) remainder diagnostics",
            "",
            _markdown_table(contraction, list(contraction.columns))
            if not contraction.empty
            else "No multi-setting grid was run.",
            "",
        ]
    )


def build_p1_outputs(output_root: Path = P1_RESULT_ROOT) -> dict[str, Any]:
    """Rebuild deterministic derived artifacts from the saved raw result tables."""

    run_path = output_root / "run_summary.csv"
    pair_path = output_root / "pair_summary.csv"
    batch_path = output_root / "batch_summary.csv"
    for path in (run_path, pair_path, batch_path):
        if not path.exists():
            raise FileNotFoundError(f"Missing P1 raw output: {path}")
    provenance_path = output_root / P1_RUN_START_PROVENANCE
    if not provenance_path.exists():
        raise FileNotFoundError(
            f"Missing P1 run-start provenance: {provenance_path}"
        )
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    run_df = pd.read_csv(run_path, keep_default_na=False)
    pair_df = pd.read_csv(pair_path, keep_default_na=False)
    batch_df = pd.read_csv(batch_path, keep_default_na=False)
    config = load_p1_config()
    base = load_configs()["base"]
    current_config_sha256 = hashlib.sha256(P1_CONFIG_PATH.read_bytes()).hexdigest()
    if current_config_sha256 != provenance["config_sha256"]:
        raise RuntimeError("P1 config file changed after the simulation started")
    if config_hash(base, config) != provenance["config_hash"]:
        raise RuntimeError("P1 base or experiment config changed after the simulation started")
    algorithm_summary = build_algorithm_summary(run_df)
    pair_summary = build_pair_setting_summary(pair_df)
    fits = build_fit_summary(pair_df, config)
    contraction = build_contraction_summary(algorithm_summary, pair_summary)
    falsification = build_falsification_summary(algorithm_summary, pair_summary)
    write_csv(algorithm_summary, output_root / "algorithm_summary.csv")
    write_csv(pair_summary, output_root / "pair_setting_summary.csv")
    write_csv(fits, output_root / "fit_summary.csv")
    write_csv(contraction, output_root / "contraction_summary.csv")
    write_csv(falsification, output_root / "falsification_summary.csv")
    report = output_root / "p1_report.md"
    report.write_text(
        _report_text(run_df, algorithm_summary, pair_summary, fits, contraction),
        encoding="utf-8",
    )
    from .figures import plot_p1_figures

    figures = plot_p1_figures(algorithm_summary, pair_summary, output_root)
    manifest = output_root / "p1_manifest.json"
    write_json(
        {
            "schema_version": 1,
            "study": "p1-matched-fedavg",
            "provenance_capture_point": provenance["capture_point"],
            "environment": provenance["environment"],
            "git_commit": provenance["git_commit"],
            "source_git_dirty_at_run_start": provenance[
                "source_git_dirty_at_run_start"
            ],
            "config_path": provenance["config_path"],
            "config_sha256": provenance["config_sha256"],
            "config_hash": provenance["config_hash"],
            "experiment_matrix_identifier": provenance[
                "experiment_matrix_identifier"
            ],
            "phase": provenance["phase"],
            "seeds": provenance["seeds"],
            "run_matrix": provenance["run_matrix"],
            "formal_matrix": audit_p1_run_matrix(),
            "rows": {
                "algorithm_runs": len(run_df),
                "matched_pairs": len(pair_df),
                "batches": len(batch_df),
            },
            "figures": [path.name for path in figures],
        },
        manifest,
    )
    return {
        "algorithm_summary": algorithm_summary,
        "pair_summary": pair_summary,
        "fit_summary": fits,
        "contraction_summary": contraction,
        "falsification_summary": falsification,
        "report": report,
        "figures": figures,
        "manifest": manifest,
    }
