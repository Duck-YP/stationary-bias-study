"""Isolated small-step confirmation orchestration and adjudication.

This module reuses the original simulation engine. It never writes into the
original result files, and diagnostic fits never override the primary gates.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from ...core.inference.statistics import student_t_critical_95
from ...core.io import (
    P0_CONFIG_ROOT,
    P0_CONFIRMATION_ARTIFACT_ROOT,
    P0_PUBLICATION_ARTIFACT_ROOT,
    git_commit,
    load_configs,
    load_yaml,
    write_csv,
)
from ...core.theory.one_dimensional import b20_total
from .analysis import build_setting_summary
from .simulation import RunSpec, simulate_setting


CONFIRMATION_CONFIG_PATH = P0_CONFIG_ROOT / "small_step_confirmation.yaml"
CONFIRMATION_RESULT_ROOT = P0_CONFIRMATION_ARTIFACT_ROOT
PUBLICATION_REPORT = P0_PUBLICATION_ARTIFACT_ROOT / "final_report.md"


def load_confirmation_config() -> dict[str, Any]:
    return load_yaml(CONFIRMATION_CONFIG_PATH)


def error_to_theory(C: float | np.ndarray, B_theory: float) -> float | np.ndarray:
    result = np.asarray(C) - B_theory
    return float(result) if result.ndim == 0 else result


def scaled_error(C: float | np.ndarray, B_theory: float, gamma: float) -> float | np.ndarray:
    result = np.asarray(error_to_theory(C, B_theory)) / gamma
    return float(result) if result.ndim == 0 else result


def build_confirmation_matrix(config: dict[str, Any] | None = None) -> list[RunSpec]:
    config = config or load_confirmation_config()
    model = config["model"]
    seeds = config["chains"]["seeds"]
    initial_x = config["chains"]["initial_x"]
    runs: list[RunSpec] = []
    for point in config["grid"]:
        gamma = 1.0 / int(point["gamma_denominator"])
        for seed in seeds:
            runs.append(
                RunSpec(
                    experiment="small_step_confirmation",
                    control_name="smaller_steps_h4",
                    objective=model["objective"],
                    noise=model["noise"],
                    H=int(model["H"]),
                    N=int(point["N"]),
                    gamma=gamma,
                    seed=int(seed),
                    x0=float(initial_x[int(seed)]),
                )
            )
    return runs


def audit_confirmation_matrix(runs: Sequence[RunSpec] | None = None) -> dict[str, Any]:
    runs = list(runs or build_confirmation_matrix())
    keys = [run.run_key for run in runs]
    return {
        "expected_runs": 32,
        "actual_runs": len(runs),
        "unique_run_keys": len(set(keys)),
        "settings": len({run.setting_key for run in runs}),
        "seeds": sorted({run.seed for run in runs}),
        "all_unique": len(keys) == len(set(keys)),
    }


def validate_confirmation_preconditions(config: dict[str, Any] | None = None) -> str:
    """Check the scientific preconditions without enforcing a historical branch name."""

    config = config or load_confirmation_config()
    if not CONFIRMATION_CONFIG_PATH.is_file():
        raise RuntimeError("Small-step confirmation configuration is missing")
    expected = b20_total(int(config["model"]["H"]))
    if not np.isclose(float(config["model"]["B_theory"]), expected):
        raise RuntimeError("Configured theory target disagrees with theoretical_bias.py")
    if PUBLICATION_REPORT.exists() and "CONTRADICTION_CANDIDATE" not in PUBLICATION_REPORT.read_text(encoding="utf-8"):
        raise RuntimeError("The preserved original contradiction result is not intact")
    return git_commit()


def _confirmation_base_config(base: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    merged = {**base}
    merged["protocol"] = {
        "burn_in_multiples": int(config["protocol"]["burn_in_multiples"]),
        "batch_length_multiples": int(config["protocol"]["batch_length_multiples"]),
        "min_batches": int(config["protocol"]["min_batches"]),
        "max_batches": int(config["protocol"]["max_batches"]),
        "extension_batches": int(config["protocol"]["extension_batches"]),
    }
    return merged


def run_confirmation() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    config = load_confirmation_config()
    protocol_commit = validate_confirmation_preconditions(config)
    base = _confirmation_base_config(load_configs()["base"], config)
    runs = build_confirmation_matrix(config)
    groups: dict[tuple[Any, ...], list[RunSpec]] = {}
    for run in runs:
        groups.setdefault(run.setting_key, []).append(run)
    all_run_rows: list[dict[str, Any]] = []
    all_batch_rows: list[dict[str, Any]] = []
    B = float(config["model"]["B_theory"])
    for index, setting in enumerate(groups.values(), start=1):
        sample = setting[0]
        print(
            f"[small-step-confirmation] setting {index}/4: H={sample.H} N={sample.N} gamma={sample.gamma:.10g}",
            flush=True,
        )
        run_rows, batch_rows = simulate_setting(setting, base, config)
        for row in run_rows:
            if row["git_commit"] != protocol_commit:
                raise RuntimeError("Formal result provenance differs from protocol commit")
            row["error_to_theory"] = error_to_theory(row["C_balance"], B)
            row["scaled_error"] = scaled_error(row["C_balance"], B, row["gamma"])
            row["protocol_commit"] = protocol_commit
        for row in batch_rows:
            row["protocol_commit"] = protocol_commit
        all_run_rows.extend(run_rows)
        all_batch_rows.extend(batch_rows)
        write_csv(all_run_rows, CONFIRMATION_RESULT_ROOT / "run_summary.csv")
        write_csv(all_batch_rows, CONFIRMATION_RESULT_ROOT / "batch_summary.csv")
        print(
            f"[small-step-confirmation] completed with {run_rows[0]['num_batches']} batches; "
            f"precision_reached={run_rows[0]['precision_reached']}",
            flush=True,
        )
    return all_run_rows, all_batch_rows


def _polynomial_fit(x: np.ndarray, y: np.ndarray, degree: int) -> np.ndarray:
    design = np.column_stack([x**power for power in range(degree + 1)])
    beta, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    return beta


def _bootstrap_polynomial(
    x: Sequence[float],
    chains: Sequence[np.ndarray],
    *,
    degree: int,
    repetitions: int,
    seed: int,
) -> dict[str, Any]:
    x_array = np.asarray(x, dtype=np.float64)
    chain_arrays = [np.asarray(values, dtype=np.float64) for values in chains]
    point = _polynomial_fit(x_array, np.array([np.mean(values) for values in chain_arrays]), degree)
    rng = np.random.default_rng(seed)
    boot = np.empty((repetitions, degree + 1), dtype=np.float64)
    for repetition in range(repetitions):
        means = np.array(
            [np.mean(rng.choice(values, size=values.size, replace=True)) for values in chain_arrays]
        )
        boot[repetition] = _polynomial_fit(x_array, means, degree)
    low, high = np.quantile(boot[:, 0], [0.025, 0.975])
    return {"beta": point, "intercept_ci_low": float(low), "intercept_ci_high": float(high)}


def build_fit_diagnostics(run_df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    groups = list(run_df.groupby("gamma", sort=True))
    gammas = [float(gamma) for gamma, _ in groups]
    chains = [group["C_balance"].to_numpy(float) for _, group in groups]
    repetitions = int(config["bootstrap"]["repetitions"])
    seed = int(config["bootstrap"]["seed"])
    linear = _bootstrap_polynomial(
        gammas, chains, degree=1, repetitions=repetitions, seed=seed
    )
    quadratic = _bootstrap_polynomial(
        gammas, chains, degree=2, repetitions=repetitions, seed=seed
    )
    B = float(config["model"]["B_theory"])
    return pd.DataFrame(
        [
            {
                "H": int(config["model"]["H"]),
                "B_theory": B,
                "bootstrap_repetitions": repetitions,
                "bootstrap_seed": seed,
                "linear_beta0": linear["beta"][0],
                "linear_beta0_ci_low": linear["intercept_ci_low"],
                "linear_beta0_ci_high": linear["intercept_ci_high"],
                "linear_beta1": linear["beta"][1],
                "linear_intercept_contains_theory": linear["intercept_ci_low"] <= B <= linear["intercept_ci_high"],
                "quadratic_beta0": quadratic["beta"][0],
                "quadratic_beta0_ci_low": quadratic["intercept_ci_low"],
                "quadratic_beta0_ci_high": quadratic["intercept_ci_high"],
                "quadratic_beta1": quadratic["beta"][1],
                "quadratic_beta2": quadratic["beta"][2],
                "quadratic_intercept_contains_theory": quadratic["intercept_ci_low"] <= B <= quadratic["intercept_ci_high"],
                "role": "SECONDARY_DIAGNOSTIC_ONLY",
            }
        ]
    )


def _absolute_interval(low: float, high: float) -> tuple[float, float]:
    if low <= 0.0 <= high:
        return 0.0, max(abs(low), abs(high))
    return min(abs(low), abs(high)), max(abs(low), abs(high))


def _overlap_fraction(first: tuple[float, float], second: tuple[float, float]) -> float:
    overlap = max(0.0, min(first[1], second[1]) - max(first[0], second[0]))
    smaller_width = min(first[1] - first[0], second[1] - second[0])
    if smaller_width <= 0.0:
        return 1.0 if overlap == 0.0 and first == second else 0.0
    return overlap / smaller_width


def adjudicate(setting_df: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str]]:
    ordered = setting_df.sort_values("gamma", ascending=False).reset_index(drop=True)
    validity_checks = {
        "finite_state": bool((ordered["finite_state_status"] == "pass").all()),
        "control_invariant": bool((ordered["control_invariant_status"] == "pass").all()),
        "estimator_agreement": bool((ordered["estimator_agreement_status"] == "pass").all()),
        "stationarity": bool((ordered["stationarity_status"] == "pass").all()),
        "precision": bool((ordered["precision_status"] == "reached").all()),
    }
    validity = all(validity_checks.values())
    rows: list[dict[str, Any]] = []
    for gate, passed in validity_checks.items():
        rows.append(
            {
                "gate_id": gate,
                "description": gate.replace("_", " "),
                "required": "PASS for all four settings",
                "observed": "PASS" if passed else "FAIL",
                "threshold": "frozen validity protocol",
                "status": "PASS" if passed else "FAIL",
                "notes": "Core validity gate",
            }
        )

    reversals: list[dict[str, Any]] = []
    multiplier = float(config["adjudication"]["directional_small_reversal_combined_se_multiplier"])
    overlap_min = float(config["adjudication"]["directional_ci_overlap_min_fraction"])
    for index in range(len(ordered) - 1):
        current = ordered.iloc[index]
        following = ordered.iloc[index + 1]
        current_abs = abs(float(current["error_to_theory"]))
        following_abs = abs(float(following["error_to_theory"]))
        if following_abs >= current_abs:
            gap = following_abs - current_abs
            combined_se = float(np.hypot(current["C_se"], following["C_se"]))
            current_interval = _absolute_interval(
                float(current["error_ci_low"]), float(current["error_ci_high"])
            )
            following_interval = _absolute_interval(
                float(following["error_ci_low"]), float(following["error_ci_high"])
            )
            overlap = _overlap_fraction(current_interval, following_interval)
            small_overlap = gap <= multiplier * combined_se and overlap >= overlap_min
            reversals.append(
                {
                    "pair": f"1/{round(1/current['gamma'])}->1/{round(1/following['gamma'])}",
                    "gap": gap,
                    "combined_se": combined_se,
                    "overlap_fraction": overlap,
                    "small_overlap": small_overlap,
                }
            )
    clear_reversals = sum(not reversal["small_overlap"] for reversal in reversals)
    if not reversals:
        directional = "PASS"
    elif len(reversals) == 1 and reversals[0]["small_overlap"]:
        directional = "INCONCLUSIVE"
    elif clear_reversals >= 2:
        directional = "FAIL"
    else:
        directional = "INCONCLUSIVE"
    rows.append(
        {
            "gate_id": "directional_convergence",
            "description": "Strict decrease of |C-B| over all four frozen points",
            "required": "Three strict decreases",
            "observed": directional,
            "threshold": f"small reversal <= {multiplier} combined SE and CI overlap >= {overlap_min}",
            "status": directional,
            "notes": f"reversals={reversals}",
        }
    )

    smallest = ordered.iloc[-1]
    relative_error = abs(float(smallest["error_to_theory"])) / abs(float(smallest["B_theory"]))
    relative_tolerance = float(config["adjudication"]["relative_tolerance"])
    proximity = "PASS" if relative_error <= relative_tolerance else "FAIL"
    rows.append(
        {
            "gate_id": "smallest_step_proximity",
            "description": "Relative coefficient error at gamma=1/192",
            "required": f"relative error <= {relative_tolerance}",
            "observed": relative_error,
            "threshold": relative_tolerance,
            "status": proximity,
            "notes": "Numerical adjudication tolerance, not a theorem error bound.",
        }
    )

    absolute_D = np.abs(ordered["scaled_error"].to_numpy(float))
    D_min = float(np.min(absolute_D))
    D_max = float(np.max(absolute_D))
    D_ratio = float(D_max / D_min) if D_min > 0.0 else float("inf")
    near_zero = bool(
        ((ordered["scaled_error_ci_low"] <= 0.0) & (ordered["scaled_error_ci_high"] >= 0.0)).any()
    )
    point_signs = np.sign(ordered["scaled_error"].to_numpy(float))
    same_sign = bool(np.all(point_signs == point_signs[0]) and point_signs[0] != 0.0)
    positive_precise = bool((ordered["scaled_error_ci_low"] > 0.0).any())
    negative_precise = bool((ordered["scaled_error_ci_high"] < 0.0).any())
    signs_compatible = same_sign or not (positive_precise and negative_precise)
    ratio_limit = float(config["adjudication"]["scaled_error_ratio_max"])
    if near_zero:
        o_gamma = "INCONCLUSIVE_NEAR_ZERO"
    elif D_ratio <= ratio_limit and signs_compatible:
        o_gamma = "PASS"
    else:
        o_gamma = "FAIL"
    rows.append(
        {
            "gate_id": "order_gamma_compatibility",
            "description": "Bounded and sign-compatible scaled errors E/gamma",
            "required": f"D_max/D_min <= {ratio_limit} and compatible signs",
            "observed": D_ratio,
            "threshold": ratio_limit,
            "status": o_gamma,
            "notes": f"D_min={D_min:.8g}; D_max={D_max:.8g}; signs_compatible={signs_compatible}; near_zero={near_zero}",
        }
    )

    smallest_two = ordered.tail(2)
    precise = bool(
        (
            ((smallest_two["error_ci_low"] > 0.0) | (smallest_two["error_ci_high"] < 0.0))
        ).all()
    )
    same_direction = bool(
        np.all(np.sign(smallest_two["error_to_theory"].to_numpy(float)) == np.sign(smallest_two["error_to_theory"].iloc[0]))
    )
    persistent_precise = precise and same_direction
    if not validity:
        status = "INVALID"
    elif directional == "PASS" and proximity == "PASS" and o_gamma == "PASS":
        status = "CONSISTENT_WITH_ASYMPTOTIC_COEFFICIENT"
    elif directional == "FAIL" and proximity == "FAIL" and persistent_precise:
        status = "PERSISTENT_DISCREPANCY"
    else:
        status = "INCONCLUSIVE"
    trigger = "YES" if status == "PERSISTENT_DISCREPANCY" else "NO"
    statuses = {
        "directional_convergence": directional,
        "smallest_step_proximity": proximity,
        "O_gamma_compatibility": o_gamma,
        "validity": "PASS" if validity else "FAIL",
        "SMALL_STEP_CONFIRMATION_STATUS": status,
        "TRIGGER_H4_THEOREM_REAUDIT": trigger,
    }
    return pd.DataFrame(rows), statuses


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    shown = frame[columns].copy()
    for column in shown.select_dtypes(include=["float"]).columns:
        shown[column] = shown[column].map(lambda value: f"{value:.9g}")
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(map(str, row)) + " |" for row in shown.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *body])


def build_report_text(
    setting_df: pd.DataFrame,
    gates: pd.DataFrame,
    fits: pd.DataFrame,
    statuses: dict[str, str],
    protocol_commit: str,
) -> str:
    ordered = setting_df.sort_values("gamma", ascending=False)
    status = statuses["SMALL_STEP_CONFIRMATION_STATUS"]
    if status == "CONSISTENT_WITH_ASYMPTOTIC_COEFFICIENT":
        interpretation = (
            "The new small-step confirmatory simulation is numerically consistent with the candidate H=4 "
            "asymptotic coefficient. The original coefficient-convergence discrepancy is therefore more plausibly attributable "
            "to finite-step extrapolation than to a persistent asymptotic discrepancy."
        )
    elif status == "PERSISTENT_DISCREPANCY":
        interpretation = (
            "The small-step confirmatory run retains a statistically precise discrepancy under the frozen "
            "primary gates. This triggers an H=4 theorem and implementation re-audit; it does not by itself "
            "establish that the candidate theorem is false."
        )
    elif status == "INVALID":
        interpretation = "A core validity gate failed, so no theorem interpretation is permitted."
    else:
        interpretation = (
            "The valid confirmatory run does not satisfy either preregistered decisive outcome. No additional "
            "runs are added, and the result remains inconclusive."
        )
    lines = [
        "# Small-Step H=4 Confirmation",
        "",
        "```text",
        "Original preregistered coefficient-convergence result:",
        "COEFFICIENT_CONVERGENCE_STATUS = CONTRADICTION_CANDIDATE",
        "",
        "This result is preserved and not overwritten.",
        "",
        "The small-step confirmation was designed after diagnosing",
        "that the original H=4 contradiction may be sensitive to finite-gamma",
        "linear extrapolation.",
        "```",
        "",
        "**Research status: CANDIDATE THEOREM. This simulation is not a proof.**",
        "",
        f"Frozen confirmation protocol commit: `{protocol_commit}`",
        "",
        "```text",
        *(f"{key} = {value}" for key, value in statuses.items()),
        "```",
        "",
        "## Four frozen point estimates",
        "",
        _markdown_table(
            ordered,
            ["gamma", "N", "C_mean", "C_ci_low", "C_ci_high", "error_to_theory", "scaled_error"],
        ),
        "",
        "## Preregistered gates",
        "",
        _markdown_table(gates, ["gate_id", "observed", "threshold", "status", "notes"]),
        "",
        "The 2% smallest-step threshold is a numerical adjudication tolerance, not a mathematical error bound.",
        "",
        "## Secondary diagnostic fits",
        "",
        _markdown_table(
            fits,
            [
                "linear_beta0",
                "linear_beta0_ci_low",
                "linear_beta0_ci_high",
                "quadratic_beta0",
                "quadratic_beta0_ci_low",
                "quadratic_beta0_ci_high",
                "B_theory",
                "role",
            ],
        ),
        "",
        "Neither diagnostic fit overrides the primary gates.",
        "",
        "## Interpretation",
        "",
        interpretation,
        "",
        "The original coefficient-convergence result remains `CONTRADICTION_CANDIDATE`; the confirmation does not rewrite its history or modify the candidate theorem.",
    ]
    return "\n".join(lines) + "\n"


def write_report_file(text: str, output_root: Path = CONFIRMATION_RESULT_ROOT) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / "confirmation_report.md"
    path.write_text(text, encoding="utf-8")
    return path


def summarize_confirmation() -> dict[str, Any]:
    config = load_confirmation_config()
    base = _confirmation_base_config(load_configs()["base"], config)
    run_path = CONFIRMATION_RESULT_ROOT / "run_summary.csv"
    batch_path = CONFIRMATION_RESULT_ROOT / "batch_summary.csv"
    if not run_path.exists() or not batch_path.exists():
        raise FileNotFoundError("Small-step confirmation raw results are missing")
    run_df = pd.read_csv(run_path, keep_default_na=False)
    batch_df = pd.read_csv(batch_path)
    protocol_commits = run_df["protocol_commit"].astype(str).unique()
    if len(protocol_commits) != 1:
        raise RuntimeError("Small-step confirmation rows do not share one frozen protocol commit")
    protocol_commit = str(protocol_commits[0])
    batch_df["protocol_commit"] = protocol_commit
    setting_df = build_setting_summary(run_df, base)
    B = float(config["model"]["B_theory"])
    setting_df["error_to_theory"] = setting_df["C_mean"] - B
    setting_df["error_se"] = setting_df["C_se"]
    setting_df["error_ci_low"] = setting_df["C_ci_low"] - B
    setting_df["error_ci_high"] = setting_df["C_ci_high"] - B
    setting_df["scaled_error"] = setting_df["error_to_theory"] / setting_df["gamma"]
    setting_df["scaled_error_se"] = setting_df["error_se"] / setting_df["gamma"]
    setting_df["scaled_error_ci_low"] = setting_df["error_ci_low"] / setting_df["gamma"]
    setting_df["scaled_error_ci_high"] = setting_df["error_ci_high"] / setting_df["gamma"]
    setting_df["protocol_commit"] = protocol_commit
    fits = build_fit_diagnostics(run_df, config)
    gates, statuses = adjudicate(setting_df, config)
    fits["protocol_commit"] = protocol_commit
    gates["protocol_commit"] = protocol_commit
    write_csv(run_df, run_path)
    write_csv(batch_df, batch_path)
    write_csv(setting_df, CONFIRMATION_RESULT_ROOT / "setting_summary.csv")
    write_csv(gates, CONFIRMATION_RESULT_ROOT / "adjudication_gates.csv")
    write_csv(fits, CONFIRMATION_RESULT_ROOT / "fit_diagnostics.csv")
    report = write_report_file(
        build_report_text(setting_df, gates, fits, statuses, protocol_commit)
    )
    return {
        "run_summary": run_df,
        "batch_summary": batch_df,
        "setting_summary": setting_df,
        "gates": gates,
        "fits": fits,
        "statuses": statuses,
        "report": report,
    }


def publication_report_sha256() -> str:
    return hashlib.sha256(PUBLICATION_REPORT.read_bytes()).hexdigest()
