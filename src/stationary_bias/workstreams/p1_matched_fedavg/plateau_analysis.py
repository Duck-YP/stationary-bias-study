"""Paired large-N extrapolation, report, and manifest for the P1 plateau."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ...core.inference.statistics import linear_fit
from ...core.io import config_hash, load_configs, write_csv, write_json
from .analysis import build_algorithm_summary, build_pair_setting_summary
from .plateau import (
    PLATEAU_CONFIG_PATH,
    PLATEAU_CONFIG_SNAPSHOT,
    PLATEAU_RESULT_ROOT,
    audit_plateau_run_matrix,
    load_plateau_config,
)
from .simulation import P1_RUN_START_PROVENANCE


FIT_COLUMNS = [
    "H",
    "gamma",
    "bootstrap_unit",
    "bootstrap_repetitions",
    "beta0_FA",
    "beta0_FA_ci_low",
    "beta0_FA_ci_high",
    "beta1_FA",
    "beta0_SCAFFOLD",
    "beta0_SCAFFOLD_ci_low",
    "beta0_SCAFFOLD_ci_high",
    "beta1_SCAFFOLD",
    "beta0_delta",
    "beta0_delta_ci_low",
    "beta0_delta_ci_high",
    "beta1_delta",
    "B20_FA_target",
    "B20_SCAFFOLD_target",
    "Delta_B20_target",
]


def _paired_bootstrap_inverse_n_fit(
    frame: pd.DataFrame,
    *,
    value_column: str,
    repetitions: int,
    seed: int,
) -> dict[str, float]:
    grouped = list(frame.groupby("N", sort=True))
    seed_sets = [set(group["seed"].astype(int)) for _, group in grouped]
    if len(grouped) < 2 or any(values != seed_sets[0] for values in seed_sets[1:]):
        raise ValueError(
            "Paired plateau bootstrap requires multiple N settings with identical seeds"
        )
    seeds = np.array(sorted(seed_sets[0]), dtype=int)
    inverse_n = np.array([1.0 / float(N) for N, _ in grouped])
    values_by_n = {
        int(N): dict(
            zip(
                group["seed"].astype(int),
                group[value_column].astype(float),
                strict=True,
            )
        )
        for N, group in grouped
    }
    means = np.array(
        [np.mean([values_by_n[int(N)][item] for item in seeds]) for N, _ in grouped]
    )
    intercept, slope = linear_fit(inverse_n, means)
    rng = np.random.default_rng(seed)
    boot_intercepts = np.empty(repetitions, dtype=np.float64)
    for index in range(repetitions):
        sampled = rng.choice(seeds, size=seeds.size, replace=True)
        sampled_means = np.array(
            [
                np.mean([values_by_n[int(N)][int(item)] for item in sampled])
                for N, _ in grouped
            ]
        )
        boot_intercepts[index], _ = linear_fit(inverse_n, sampled_means)
    low, high = np.quantile(boot_intercepts, [0.025, 0.975])
    return {
        "intercept": intercept,
        "slope": slope,
        "intercept_ci_low": float(low),
        "intercept_ci_high": float(high),
    }


def build_plateau_fit_summary(
    run_df: pd.DataFrame, pair_df: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    repetitions = int(config["inference"]["bootstrap_repetitions"])
    seed = int(config["inference"]["bootstrap_seed"])
    fedavg = _paired_bootstrap_inverse_n_fit(
        run_df[run_df["algorithm"] == "fedavg"],
        value_column="C_balance",
        repetitions=repetitions,
        seed=seed,
    )
    scaffold = _paired_bootstrap_inverse_n_fit(
        run_df[run_df["algorithm"] == "scaffold"],
        value_column="C_balance",
        repetitions=repetitions,
        seed=seed + 1,
    )
    delta = _paired_bootstrap_inverse_n_fit(
        pair_df,
        value_column="Delta_C",
        repetitions=repetitions,
        seed=seed + 2,
    )
    theory = config["theory"]
    row = {
        "H": int(run_df["H"].iloc[0]),
        "gamma": float(run_df["gamma"].iloc[0]),
        "bootstrap_unit": "matched_chain_pair",
        "bootstrap_repetitions": repetitions,
        "beta0_FA": fedavg["intercept"],
        "beta0_FA_ci_low": fedavg["intercept_ci_low"],
        "beta0_FA_ci_high": fedavg["intercept_ci_high"],
        "beta1_FA": fedavg["slope"],
        "beta0_SCAFFOLD": scaffold["intercept"],
        "beta0_SCAFFOLD_ci_low": scaffold["intercept_ci_low"],
        "beta0_SCAFFOLD_ci_high": scaffold["intercept_ci_high"],
        "beta1_SCAFFOLD": scaffold["slope"],
        "beta0_delta": delta["intercept"],
        "beta0_delta_ci_low": delta["intercept_ci_low"],
        "beta0_delta_ci_high": delta["intercept_ci_high"],
        "beta1_delta": delta["slope"],
        "B20_FA_target": float(theory["B20_fedavg"]),
        "B20_SCAFFOLD_target": float(theory["B20_scaffold"]),
        "Delta_B20_target": float(theory["Delta_B20_scaffold_minus_fedavg"]),
    }
    return pd.DataFrame([row], columns=FIT_COLUMNS)


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
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
) -> str:
    phase = "smoke" if set(run_df["phase"]) == {"smoke"} else "formal"
    return "\n".join(
        [
            "# P1 Fixed-gamma Large-N Matched Plateau",
            "",
            f"Run phase: **{phase.upper()}**",
            "",
            "Smoke outputs are implementation diagnostics only."
            if phase == "smoke"
            else (
                "Primary estimates use the stationary mean-balance estimator. "
                "Direct means remain diagnostics; matched differences and extrapolation "
                "uncertainty resample matched chain pairs."
            ),
            "",
            "The fixed step size permits O(gamma) finite-step contamination, so compatibility "
            "is assessed from plateau stability, sign, ordering, and proximity—not solely "
            "from whether a 95% interval contains the asymptotic target.",
            "",
            "## Point estimates by client count",
            "",
            _markdown_table(
                algorithm_summary,
                [
                    "algorithm",
                    "N",
                    "gamma",
                    "C_mean",
                    "C_ci_low",
                    "C_ci_high",
                    "B20_target",
                    "gate_pass",
                ],
            ),
            "",
            "## Pair-level SCAFFOLD-minus-FedAvg estimates",
            "",
            _markdown_table(
                pair_summary,
                [
                    "N",
                    "gamma",
                    "Delta_C_mean",
                    "Delta_C_ci_low",
                    "Delta_C_ci_high",
                    "Delta_B20_target",
                    "pair_gate_pass",
                ],
            ),
            "",
            "## Linear extrapolation in 1/N",
            "",
            _markdown_table(fits, list(fits.columns)),
            "",
        ]
    )


def build_plateau_outputs(output_root: Path = PLATEAU_RESULT_ROOT) -> dict[str, Any]:
    """Rebuild deterministic derived artifacts from the saved plateau tables."""

    required = [
        output_root / "run_summary.csv",
        output_root / "pair_summary.csv",
        output_root / "batch_summary.csv",
        output_root / P1_RUN_START_PROVENANCE,
        output_root / PLATEAU_CONFIG_SNAPSHOT,
    ]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"Missing P1 plateau raw artifact: {path}")

    provenance = json.loads(required[3].read_text(encoding="utf-8"))
    config = load_plateau_config()
    base = load_configs()["base"]
    current_sha = hashlib.sha256(PLATEAU_CONFIG_PATH.read_bytes()).hexdigest()
    snapshot_sha = hashlib.sha256(required[4].read_bytes()).hexdigest()
    if current_sha != provenance["config_sha256"] or snapshot_sha != current_sha:
        raise RuntimeError("P1 plateau config or its snapshot changed after run start")
    if config_hash(base, config) != provenance["config_hash"]:
        raise RuntimeError("P1 base or plateau config changed after run start")

    run_df = pd.read_csv(required[0], keep_default_na=False)
    pair_df = pd.read_csv(required[1], keep_default_na=False)
    batch_df = pd.read_csv(required[2], keep_default_na=False)
    algorithm_summary = build_algorithm_summary(run_df)
    pair_summary = build_pair_setting_summary(pair_df)
    fits = build_plateau_fit_summary(run_df, pair_df, config)
    write_csv(algorithm_summary, output_root / "algorithm_summary.csv")
    write_csv(pair_summary, output_root / "pair_setting_summary.csv")
    write_csv(fits, output_root / "plateau_fit_summary.csv")
    report = output_root / "plateau_report.md"
    report.write_text(
        _report_text(run_df, algorithm_summary, pair_summary, fits), encoding="utf-8"
    )
    from .plateau_figures import plot_plateau_figure

    figure = plot_plateau_figure(algorithm_summary, pair_summary, output_root)
    manifest = output_root / "plateau_manifest.json"
    write_json(
        {
            "schema_version": 1,
            "study": "p1-fixed-gamma-large-n-matched-plateau",
            "provenance_capture_point": provenance["capture_point"],
            "environment": provenance["environment"],
            "git_commit": provenance["git_commit"],
            "source_git_dirty_at_run_start": provenance[
                "source_git_dirty_at_run_start"
            ],
            "config_path": provenance["config_path"],
            "config_snapshot": PLATEAU_CONFIG_SNAPSHOT,
            "config_sha256": provenance["config_sha256"],
            "config_hash": provenance["config_hash"],
            "experiment_matrix_identifier": provenance[
                "experiment_matrix_identifier"
            ],
            "phase": provenance["phase"],
            "seeds": provenance["seeds"],
            "run_matrix": provenance["run_matrix"],
            "formal_matrix": audit_plateau_run_matrix(),
            "estimators": {
                "primary": "stationary_mean_balance",
                "diagnostic": "direct_sample_mean",
                "delta": "pair_level_C_scaffold_minus_C_fedavg",
            },
            "rows": {
                "algorithm_runs": len(run_df),
                "matched_pairs": len(pair_df),
                "batches": len(batch_df),
            },
            "figure": figure.name,
            "report": report.name,
        },
        manifest,
    )
    return {
        "algorithm_summary": algorithm_summary,
        "pair_summary": pair_summary,
        "fit_summary": fits,
        "report": report,
        "figure": figure,
        "manifest": manifest,
    }
