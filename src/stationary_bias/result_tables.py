"""Setting summaries, falsification gates, bootstrap fits, and P3 report."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .validation_checks import estimator_agreement
from .statistical_analysis import chain_level_bootstrap_fit, student_t_summary
from .project_io import RESULT_ROOT, experiment_result_root, load_configs, write_csv
from .theoretical_bias import leading_bias_coefficient


SETTING_KEYS = ["experiment", "control_name", "objective", "noise", "H", "N", "gamma"]


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().map({"true": True, "false": False}).fillna(False)


def load_formal_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    run_frames: list[pd.DataFrame] = []
    batch_frames: list[pd.DataFrame] = []
    for experiment in ("p3a", "p3b", "p3c"):
        experiment_root = experiment_result_root(experiment)
        run_path = experiment_root / "run_summary.csv"
        batch_path = experiment_root / "batch_summary.csv"
        if not run_path.exists() or not batch_path.exists():
            raise FileNotFoundError(f"Missing formal raw output for {experiment}")
        run_frames.append(pd.read_csv(run_path, keep_default_na=False))
        batch_frames.append(pd.read_csv(batch_path))
    run_df = pd.concat(run_frames, ignore_index=True)
    batch_df = pd.concat(batch_frames, ignore_index=True)
    return run_df, batch_df


def build_setting_summary(run_df: pd.DataFrame, base: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    threshold = float(base["thresholds"]["max_abs_control_sum"])
    min_stationary = int(base["thresholds"]["stationarity_min_chains"])
    agreement_z = float(base["thresholds"]["estimator_agreement_z"])
    for key, group in run_df.groupby(SETTING_KEYS, sort=False, dropna=False):
        b_balance = student_t_summary(group["b_balance"].to_numpy(float))
        b_direct = student_t_summary(group["b_direct"].to_numpy(float))
        C = student_t_summary(group["C_balance"].to_numpy(float))
        agreement = estimator_agreement(
            b_direct.mean,
            b_balance.mean,
            b_direct.se,
            b_balance.se,
            z=agreement_z,
        )
        finite = bool(_bool_series(group["finite_state_pass"]).all())
        control = bool(np.max(group["control_sum_max_abs"].to_numpy(float)) <= threshold)
        stationary_count = int(_bool_series(group["stationarity_pass"]).sum())
        stationary = stationary_count >= min_stationary
        if not finite:
            validity = "INVALID_NONFINITE"
        elif not control:
            validity = "INVALID_RECURSION"
        elif not stationary:
            validity = "INVALID_STATIONARITY"
        elif not agreement:
            validity = "INCONCLUSIVE_ESTIMATOR_DISAGREEMENT"
        else:
            validity = "VALID"
        precision = bool(_bool_series(group["precision_reached"]).all())
        B = float(group["B_theory"].iloc[0])
        row = dict(zip(SETTING_KEYS, key, strict=True))
        row.update(
            {
                "num_chains": len(group),
                "b_balance_mean": b_balance.mean,
                "b_balance_std": b_balance.std,
                "b_balance_se": b_balance.se,
                "b_balance_ci_low": b_balance.ci_low,
                "b_balance_ci_high": b_balance.ci_high,
                "b_direct_mean": b_direct.mean,
                "b_direct_std": b_direct.std,
                "b_direct_se": b_direct.se,
                "b_direct_ci_low": b_direct.ci_low,
                "b_direct_ci_high": b_direct.ci_high,
                "C_mean": C.mean,
                "C_std": C.std,
                "C_se": C.se,
                "C_ci_low": C.ci_low,
                "C_ci_high": C.ci_high,
                "B_theory": B,
                "C_minus_B": C.mean - B,
                "precision_status": "reached" if precision else "not_reached",
                "stationarity_status": "pass" if stationary else "fail",
                "stationarity_chains_passed": stationary_count,
                "estimator_agreement_status": "pass" if agreement else "fail",
                "finite_state_status": "pass" if finite else "fail",
                "control_invariant_status": "pass" if control else "fail",
                "control_sum_max_abs": float(group["control_sum_max_abs"].max()),
                "overall_validity": validity,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def build_p3a_fit_summary(
    run_df: pd.DataFrame, setting_df: pd.DataFrame, base: dict[str, Any]
) -> pd.DataFrame:
    repetitions = int(base["inference"]["bootstrap_repetitions"])
    seed = int(base["inference"]["bootstrap_seed"])
    rows: list[dict[str, Any]] = []
    for H in sorted(run_df.loc[run_df["experiment"] == "p3a", "H"].unique()):
        subset = run_df[(run_df["experiment"] == "p3a") & (run_df["H"] == H)]
        grouped = list(subset.groupby("gamma", sort=True))
        gammas = [float(gamma) for gamma, _ in grouped]
        chains = [group["C_balance"].to_numpy(float) for _, group in grouped]
        fit = chain_level_bootstrap_fit(
            gammas, chains, repetitions=repetitions, seed=seed
        )
        B = float(subset["B_theory"].iloc[0])
        low = float(fit["intercept_ci_low"])
        high = float(fit["intercept_ci_high"])
        contains = low <= B <= high
        sign_matches = bool(float(fit["intercept"]) * B > 0.0)
        summaries = setting_df[
            (setting_df["experiment"] == "p3a") & (setting_df["H"] == H)
        ].sort_values("gamma")
        all_valid = bool((summaries["overall_validity"] == "VALID").all())
        smallest = summaries.head(2)
        smallest_precise = bool((smallest["precision_status"] == "reached").all())
        same_side = bool(
            ((smallest["C_ci_low"] > B).all()) or ((smallest["C_ci_high"] < B).all())
        )
        half_width = (high - low) / 2.0
        contradiction = (
            all_valid
            and smallest_precise
            and not contains
            and half_width <= 0.10 * abs(B)
            and same_side
        )
        if contradiction:
            status = "CONTRADICTION_CANDIDATE"
        elif all_valid and smallest_precise and contains and sign_matches:
            status = "SUPPORT"
        else:
            status = "INCONCLUSIVE"
        rows.append(
            {
                "H": int(H),
                "beta0": fit["intercept"],
                "beta0_ci_low": low,
                "beta0_ci_high": high,
                "beta1": fit["slope"],
                "B_theory": B,
                "intercept_contains_theory": contains,
                "intercept_sign_matches_theory": sign_matches,
                "smallest_two_precision_reached": smallest_precise,
                "validity_gates_pass": all_valid,
                "bootstrap_repetitions": repetitions,
                "bootstrap_seed": seed,
                "p3a_status": status,
            }
        )
    return pd.DataFrame(rows)


def build_p3b_fit_summary(
    run_df: pd.DataFrame, setting_df: pd.DataFrame, base: dict[str, Any]
) -> pd.DataFrame:
    repetitions = int(base["inference"]["bootstrap_repetitions"])
    seed = int(base["inference"]["bootstrap_seed"])
    subset = run_df[run_df["experiment"] == "p3b"]
    grouped = list(subset.groupby("N", sort=True))
    inverse_N = [1.0 / float(N) for N, _ in grouped]
    chains = [group["C_balance"].to_numpy(float) for _, group in grouped]
    fit = chain_level_bootstrap_fit(
        inverse_N, chains, repetitions=repetitions, seed=seed
    )
    low = float(fit["intercept_ci_low"])
    high = float(fit["intercept_ci_high"])
    excludes_zero = high < 0.0 or low > 0.0
    summaries = setting_df[setting_df["experiment"] == "p3b"]
    all_valid = bool((summaries["overall_validity"] == "VALID").all())
    large_N = summaries[summaries["N"].isin([64, 128])]
    points_negative = len(large_N) == 2 and bool((large_N["C_mean"] < 0.0).all())
    point_cis_exclude_zero = len(large_N) == 2 and bool((large_N["C_ci_high"] < 0.0).all())
    support = (
        all_valid
        and points_negative
        and point_cis_exclude_zero
        and excludes_zero
        and float(fit["intercept"]) < 0.0
        and high < 0.0
    )
    return pd.DataFrame(
        [
            {
                "H": int(subset["H"].iloc[0]),
                "gamma": float(subset["gamma"].iloc[0]),
                "alpha0": fit["intercept"],
                "alpha0_ci_low": low,
                "alpha0_ci_high": high,
                "alpha1": fit["slope"],
                "intercept_excludes_zero": excludes_zero,
                "validity_gates_pass": all_valid,
                "N64_N128_negative": points_negative,
                "N64_N128_ci_exclude_zero": point_cis_exclude_zero,
                "bootstrap_repetitions": repetitions,
                "bootstrap_seed": seed,
                "p3b_status": "SUPPORT_N_NONVANISHING" if support else "INCONCLUSIVE",
            }
        ]
    )


def build_negative_control_summary(
    run_df: pd.DataFrame, setting_df: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    controls = setting_df[setting_df["experiment"] == "p3c"]
    for _, setting in controls.iterrows():
        name = setting["control_name"]
        run_group = run_df[
            (run_df["experiment"] == "p3c")
            & (run_df["control_name"] == name)
            & (run_df["N"] == setting["N"])
            & np.isclose(run_df["gamma"], setting["gamma"])
        ]
        valid = setting["overall_validity"] == "VALID"
        if name == "no_stochastic_noise":
            estimate = float(setting["b_balance_mean"])
            low = float(setting["b_balance_ci_low"])
            high = float(setting["b_balance_ci_high"])
            final_x = float(run_group["last_batch_max_abs_x"].max())
            passed = valid and abs(estimate) <= 1.0e-10 and final_x <= 1.0e-10
            status = "PASS" if passed else "FAIL_IMPLEMENTATION_OR_BURNIN"
            notes = f"b gate 1e-10; last-batch max_abs_x={final_x:.6g}"
        elif name == "no_nonlinear_conversion":
            estimate = float(setting["b_balance_mean"])
            low = float(setting["b_balance_ci_low"])
            high = float(setting["b_balance_ci_high"])
            C = float(setting["C_mean"])
            C_se = float(setting["C_se"])
            passed = valid and low <= 0.0 <= high and abs(C) <= max(3.0 * C_se, 0.02)
            status = "PASS" if passed else "FLAG"
            notes = f"C_quad={C:.6g}; 3SE_C={3.0 * C_se:.6g}"
        elif name == "h1_boundary_sanity":
            estimate = float(setting["C_mean"])
            low = float(setting["C_ci_low"])
            high = float(setting["C_ci_high"])
            C_se = float(setting["C_se"])
            passed = valid and abs(estimate) <= max(3.0 * C_se, 0.02)
            status = "SANITY_CONSISTENT" if passed else "SANITY_FLAG"
            notes = "Boundary-only H=1 check; never a theorem-domain failure."
        else:
            continue
        rows.append(
            {
                "control_name": name,
                "gamma": setting["gamma"],
                "N": int(setting["N"]),
                "H": int(setting["H"]),
                "target": 0.0,
                "estimate": estimate,
                "ci_low": low,
                "ci_high": high,
                "status": status,
                "notes": notes,
            }
        )
    rows.append(
        {
            "control_name": "no_persistent_control_fluctuation",
            "gamma": "",
            "N": "",
            "H": "",
            "target": "",
            "estimate": "",
            "ci_low": "",
            "ci_high": "",
            "status": "NOT_RUN_MISSING_APPROVED_RECURSION",
            "notes": "NC4 was not run because no approved modified recursion is frozen.",
        }
    )
    return pd.DataFrame(rows)


def _frozen_negative_control_status(
    negative: pd.DataFrame, *, control_name: str, gamma: float, N: int, H: int
) -> str:
    candidates = negative[negative["control_name"] == control_name]
    for _, row in candidates.iterrows():
        try:
            same_setting = (
                np.isclose(float(row["gamma"]), gamma)
                and int(float(row["N"])) == N
                and int(float(row["H"])) == H
            )
        except (TypeError, ValueError):
            continue
        if same_setting:
            return str(row["status"])
    return "MISSING_FROZEN_STATUS"


def build_negative_control_audit(
    run_df: pd.DataFrame,
    setting_df: pd.DataFrame,
    frozen_negative: pd.DataFrame,
) -> pd.DataFrame:
    """Build a post-hoc direct-estimator audit from existing P3-C raw rows only."""

    controls = setting_df[setting_df["experiment"] == "p3c"].copy()
    h1 = controls[controls["control_name"] == "h1_boundary_sanity"].sort_values("gamma")
    if len(h1) >= 2 and abs(float(h1.iloc[0]["C_mean"])) < abs(float(h1.iloc[-1]["C_mean"])):
        h1_trend = "smaller_gamma_closer_to_zero"
    else:
        h1_trend = "no_smaller_gamma_improvement"

    rows: list[dict[str, Any]] = []
    for _, setting in controls.iterrows():
        name = str(setting["control_name"])
        gamma = float(setting["gamma"])
        N = int(setting["N"])
        H = int(setting["H"])
        run_group = run_df[
            (run_df["experiment"] == "p3c")
            & (run_df["control_name"] == name)
            & (run_df["N"] == N)
            & np.isclose(run_df["gamma"], gamma)
        ]
        if run_group.empty:
            raise ValueError(f"Missing raw P3-C rows for {name}, N={N}, gamma={gamma}")
        raw = run_group.iloc[0]
        B10 = leading_bias_coefficient(float(raw["a"]), float(raw["tau"]), float(raw["sigma2"]))
        direct_low = float(setting["b_direct_ci_low"])
        direct_high = float(setting["b_direct_ci_high"])
        direct_contains_zero = direct_low <= 0.0 <= direct_high
        frozen_status = _frozen_negative_control_status(
            frozen_negative, control_name=name, gamma=gamma, N=N, H=H
        )
        final_x = float(run_group["last_batch_max_abs_x"].max())
        valid = setting["overall_validity"] == "VALID"
        structural_zero = bool(
            name == "no_nonlinear_conversion"
            and setting["objective"] == "quadratic"
            and float(setting["b_balance_mean"]) == 0.0
            and float(setting["b_balance_ci_low"]) == 0.0
            and float(setting["b_balance_ci_high"]) == 0.0
        )

        if name == "no_stochastic_noise":
            frozen_sanity_pass = frozen_status == "PASS" and final_x <= 1.0e-10
            audit_id = "NC1_DIRECT_AUDIT"
            audit_status = "PASS" if valid and direct_contains_zero and frozen_sanity_pass else "FLAG"
            descriptive_trend = "not_applicable"
            notes = "Direct CI is independent; deterministic convergence sanity remains frozen."
        elif name == "no_nonlinear_conversion":
            audit_id = "NC2_DIRECT_AUDIT"
            audit_status = "PASS" if valid and direct_contains_zero else "FLAG"
            descriptive_trend = "not_applicable"
            notes = (
                "The balance estimator is structurally zero because q(x)=grad(x)-a*x is identically zero; "
                "it cannot cause this direct audit to pass."
            )
        elif name == "h1_boundary_sanity":
            audit_id = "NC3_BOUNDARY_SANITY"
            audit_status = (
                frozen_status
                if frozen_status in {"SANITY_CONSISTENT", "SANITY_FLAG"}
                else "SANITY_FLAG"
            )
            descriptive_trend = h1_trend
            notes = (
                "Boundary sanity only: C_balance=(b_balance-B10*gamma/N)/gamma^2; "
                "raw stationary bias is not targeted to zero."
            )
        else:
            continue

        rows.append(
            {
                "audit_scope": "POST_HOC_NEGATIVE_CONTROL_ESTIMATOR_ROBUSTNESS",
                "audit_id": audit_id,
                "control_name": name,
                "gamma": gamma,
                "N": N,
                "H": H,
                "B10": B10,
                "b_direct_mean": float(setting["b_direct_mean"]),
                "b_direct_ci_low": direct_low,
                "b_direct_ci_high": direct_high,
                "direct_ci_contains_zero": direct_contains_zero,
                "b_balance_mean": float(setting["b_balance_mean"]),
                "b_balance_ci_low": float(setting["b_balance_ci_low"]),
                "b_balance_ci_high": float(setting["b_balance_ci_high"]),
                "balance_is_structurally_zero": structural_zero,
                "C_balance": float(setting["C_mean"]),
                "C_balance_ci_low": float(setting["C_ci_low"]),
                "C_balance_ci_high": float(setting["C_ci_high"]),
                "last_batch_max_abs_x": final_x,
                "estimator_agreement_status": setting["estimator_agreement_status"],
                "stationarity_status": setting["stationarity_status"],
                "overall_validity": setting["overall_validity"],
                "frozen_status": frozen_status,
                "descriptive_trend": descriptive_trend,
                "audit_status": audit_status,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows)


def aggregate_statuses(
    setting_df: pd.DataFrame,
    p3a_fit: pd.DataFrame,
    p3b_fit: pd.DataFrame,
    negative: pd.DataFrame,
) -> dict[str, str]:
    p3a_values = set(p3a_fit["p3a_status"])
    if "CONTRADICTION_CANDIDATE" in p3a_values:
        p3a = "CONTRADICTION_CANDIDATE"
    elif p3a_values == {"SUPPORT"}:
        p3a = "SUPPORT"
    else:
        p3a = "INCONCLUSIVE"
    p3b = str(p3b_fit["p3b_status"].iloc[0])
    nc1_rows = negative[negative["control_name"] == "no_stochastic_noise"]
    nc2_rows = negative[negative["control_name"] == "no_nonlinear_conversion"]
    nc3_rows = negative[negative["control_name"] == "h1_boundary_sanity"]
    nc1 = "PASS" if len(nc1_rows) == 2 and (nc1_rows["status"] == "PASS").all() else "FAIL_IMPLEMENTATION_OR_BURNIN"
    nc2 = "PASS" if len(nc2_rows) == 2 and (nc2_rows["status"] == "PASS").all() else "FLAG"
    nc3 = (
        "SANITY_CONSISTENT"
        if len(nc3_rows) == 2 and (nc3_rows["status"] == "SANITY_CONSISTENT").all()
        else "SANITY_FLAG"
    )
    nc4 = "NOT_RUN_MISSING_APPROVED_RECURSION"
    invalid_prefixes = ("INVALID_NONFINITE", "INVALID_RECURSION", "INVALID_STATIONARITY")
    invalid = setting_df["overall_validity"].astype(str).str.startswith(invalid_prefixes).any()
    if invalid:
        overall = "INVALID"
    elif p3a == "CONTRADICTION_CANDIDATE":
        overall = "CONTRADICTION_CANDIDATE"
    elif p3a == "SUPPORT" and p3b == "SUPPORT_N_NONVANISHING" and nc1 == "PASS" and nc2 == "PASS":
        overall = "SUPPORT"
    else:
        overall = "INCONCLUSIVE"
    return {
        "P3A_STATUS": p3a,
        "P3B_STATUS": p3b,
        "NC1_STATUS": nc1,
        "NC2_STATUS": nc2,
        "NC3_STATUS": nc3,
        "NC4_STATUS": nc4,
        "OVERALL_P3_STATUS": overall,
    }


def build_falsification_gates(
    setting_df: pd.DataFrame,
    p3a_fit: pd.DataFrame,
    p3b_fit: pd.DataFrame,
    negative: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, setting in setting_df.iterrows():
        label = (
            f"{setting['experiment']}:H{int(setting['H'])}:N{int(setting['N'])}:"
            f"g{float(setting['gamma']):.10g}"
        )
        checks = [
            ("G-V1", "Finite-state sanity", setting["finite_state_status"], "all states/statistics finite"),
            ("G-V2", "Zero-sum control invariant", setting["control_invariant_status"], "max <= 1e-10"),
            ("G-V3", "Direct-vs-balance agreement", setting["estimator_agreement_status"], "difference <= 3 combined SE"),
            ("G-V4", "Post-burn stationarity", setting["stationarity_status"], ">= 7/8 chains"),
        ]
        for gate_id, description, observed, threshold in checks:
            rows.append(
                {
                    "gate_id": f"{gate_id}:{label}",
                    "experiment": setting["experiment"],
                    "description": description,
                    "required": "pass",
                    "observed": observed,
                    "threshold": threshold,
                    "status": "PASS" if observed == "pass" else "FAIL",
                    "notes": setting["overall_validity"],
                }
            )
        rows.append(
            {
                "gate_id": f"G-PRECISION:{label}",
                "experiment": setting["experiment"],
                "description": "Frozen coefficient CI half-width gate",
                "required": "main coefficient inference",
                "observed": setting["precision_status"],
                "threshold": "max(0.02, 0.10 |B20(H)|)",
                "status": "PASS" if setting["precision_status"] == "reached" else "INCONCLUSIVE",
                "notes": "Precision controls extension only; it is not a truth criterion.",
            }
        )
    for _, fit in p3a_fit.iterrows():
        rows.append(
            {
                "gate_id": f"P3A-SUPPORT:H{int(fit['H'])}",
                "experiment": "p3a",
                "description": "Joint coefficient-convergence support/contradiction logic",
                "required": "pre-registered composite gate",
                "observed": fit["p3a_status"],
                "threshold": "P3-A specification",
                "status": (
                    "PASS"
                    if fit["p3a_status"] == "SUPPORT"
                    else "FAIL"
                    if fit["p3a_status"] == "CONTRADICTION_CANDIDATE"
                    else "INCONCLUSIVE"
                ),
                "notes": (
                    f"beta0 CI [{fit['beta0_ci_low']:.6g}, {fit['beta0_ci_high']:.6g}]; "
                    f"contains B20={fit['intercept_contains_theory']}"
                ),
            }
        )
    fit = p3b_fit.iloc[0]
    rows.append(
        {
            "gate_id": "P3B-N-NONVANISHING",
            "experiment": "p3b",
            "description": "Negative, nonzero large-N plateau",
            "required": "pre-registered composite gate",
            "observed": fit["p3b_status"],
            "threshold": "P3-B specification",
            "status": "PASS" if fit["p3b_status"] == "SUPPORT_N_NONVANISHING" else "INCONCLUSIVE",
            "notes": f"alpha0 CI [{fit['alpha0_ci_low']:.6g}, {fit['alpha0_ci_high']:.6g}]",
        }
    )
    for _, row in negative.iterrows():
        status = row["status"]
        if status in {"PASS", "SANITY_CONSISTENT"}:
            gate_status = "PASS"
        elif status == "NOT_RUN_MISSING_APPROVED_RECURSION":
            gate_status = "NOT_RUN"
        else:
            gate_status = "FAIL"
        rows.append(
            {
                "gate_id": f"P3C:{row['control_name']}:N{row['N']}:g{row['gamma']}",
                "experiment": "p3c",
                "description": "Negative-control or boundary-sanity gate",
                "required": row["control_name"] != "no_persistent_control_fluctuation",
                "observed": status,
                "threshold": row["target"],
                "status": gate_status,
                "notes": row["notes"],
            }
        )
    return pd.DataFrame(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    shown = frame[columns].copy()
    for column in shown.select_dtypes(include=["float"]).columns:
        shown[column] = shown[column].map(lambda value: f"{value:.8g}")
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(map(str, row)) + " |" for row in shown.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *body])


def write_report(
    run_df: pd.DataFrame,
    setting_df: pd.DataFrame,
    p3a_fit: pd.DataFrame,
    p3b_fit: pd.DataFrame,
    negative: pd.DataFrame,
    negative_audit: pd.DataFrame,
    statuses: dict[str, str],
) -> Path:
    expected = 168
    completed = len(run_df)
    invalid_chains = int(
        (~_bool_series(run_df["finite_state_pass"])
        | (run_df["control_sum_max_abs"].to_numpy(float) > 1.0e-10)).sum()
    )
    precision_not_reached = int((~_bool_series(run_df["precision_reached"])).sum())
    status_block = "\n".join(f"{key} = {value}" for key, value in statuses.items())
    p3a_points = setting_df[setting_df["experiment"] == "p3a"].sort_values(["H", "gamma"])
    p3b_points = setting_df[setting_df["experiment"] == "p3b"].sort_values("N")
    contradiction = statuses["OVERALL_P3_STATUS"] == "CONTRADICTION_CANDIDATE"
    reaudit = "YES" if contradiction else "NO"
    audit_rows: list[dict[str, str]] = []
    for _, row in negative_audit.iterrows():
        setting_label = f"gamma={float(row['gamma']):.8g}, N={int(row['N'])}, H={int(row['H'])}"
        if row["control_name"] == "no_stochastic_noise":
            frozen_statistic = (
                f"b_balance={float(row['b_balance_mean']):.4g}; "
                f"last max|x|={float(row['last_batch_max_abs_x']):.4g}"
            )
            direct_audit = (
                f"b_direct={float(row['b_direct_mean']):.4g}, 95% CI "
                f"[{float(row['b_direct_ci_low']):.4g}, {float(row['b_direct_ci_high']):.4g}], "
                f"contains 0={bool(row['direct_ci_contains_zero'])}"
            )
            control_label = "NC1 deterministic"
        elif row["control_name"] == "no_nonlinear_conversion":
            frozen_statistic = "b_balance=0 structurally because q(x) is identically zero"
            direct_audit = (
                f"b_direct={float(row['b_direct_mean']):.4g}, 95% CI "
                f"[{float(row['b_direct_ci_low']):.4g}, {float(row['b_direct_ci_high']):.4g}], "
                f"contains 0={bool(row['direct_ci_contains_zero'])}"
            )
            control_label = "NC2 quadratic"
        else:
            frozen_statistic = (
                f"normalized C_balance={float(row['C_balance']):.4g}, 95% CI "
                f"[{float(row['C_balance_ci_low']):.4g}, {float(row['C_balance_ci_high']):.4g}]"
            )
            direct_audit = (
                f"b_direct={float(row['b_direct_mean']):.4g}; agreement="
                f"{row['estimator_agreement_status']}; trend={row['descriptive_trend']}"
            )
            control_label = "NC3 H=1 boundary"
        audit_rows.append(
            {
                "Control": control_label,
                "Setting": setting_label,
                "Frozen statistic": frozen_statistic,
                "Independent/direct audit": direct_audit,
                "Verdict": str(row["audit_status"]),
            }
        )
    audit_table = pd.DataFrame(audit_rows)
    lines = [
        "# Stationary-Bias Numerical Falsification Report",
        "",
        "**Research status: CANDIDATE THEOREM.** This simulation is a falsification attempt, not a proof.",
        "",
        "```text",
        status_block,
        "```",
        "",
        "## Formal run ledger",
        "",
        f"- Expected independent chains: {expected}",
        f"- Completed independent chains: {completed}",
        f"- Invalid chains (nonfinite or control invariant): {invalid_chains}",
        f"- Precision-not-reached chains: {precision_not_reached}",
        "",
        "## Coefficient convergence (thesis reference: P3-A)",
        "",
        _markdown_table(
            p3a_points,
            ["H", "gamma", "N", "C_mean", "C_ci_low", "C_ci_high", "B_theory", "precision_status", "overall_validity"],
        ),
        "",
        _markdown_table(
            p3a_fit,
            ["H", "beta0", "beta0_ci_low", "beta0_ci_high", "beta1", "B_theory", "p3a_status"],
        ),
        "",
        "## Client-count scaling (thesis reference: P3-B)",
        "",
        _markdown_table(
            p3b_points,
            ["N", "gamma", "C_mean", "C_ci_low", "C_ci_high", "overall_validity"],
        ),
        "",
        _markdown_table(
            p3b_fit,
            ["H", "gamma", "alpha0", "alpha0_ci_low", "alpha0_ci_high", "alpha1", "p3b_status"],
        ),
        "",
        "## Negative controls and boundary sanity (thesis reference: P3-C)",
        "",
        _markdown_table(
            negative,
            ["control_name", "gamma", "N", "H", "target", "estimate", "ci_low", "ci_high", "status"],
        ),
        "",
        "## Post-hoc negative-control estimator robustness audit",
        "",
        "This audit was added after the frozen numerical protocol and is reported as a robustness check, not as a pre-registered falsification gate.",
        "",
        _markdown_table(
            audit_table,
            ["Control", "Setting", "Frozen statistic", "Independent/direct audit", "Verdict"],
        ),
        "",
        "The balance estimator is structurally zero for the quadratic objective because q(x) is identically zero; therefore the independent direct stationary-mean estimator is used as the robustness check.",
        "",
        "For H=1, this is a boundary sanity check. The relevant quantity is the normalized residual after subtracting B10*gamma/N, not the raw stationary bias.",
        "",
        "## Research interpretation",
        "",
        f"1. What the simulations support: coefficient convergence is `{statuses['P3A_STATUS']}` and client-count scaling is `{statuses['P3B_STATUS']}` under the frozen gates.",
        f"2. What remains inconclusive: any setting or fit explicitly marked `INCONCLUSIVE`, plus NC4, whose status is `{statuses['NC4_STATUS']}`.",
        f"3. Any numerical contradiction: {'A strict contradiction candidate was triggered.' if contradiction else 'No strict contradiction candidate was triggered.'}",
        "4. Any implementation concern: consult `falsification_gates.csv`; failed recursion, finite-state, stationarity, or estimator-agreement gates are never treated as theorem evidence.",
        f"5. Whether a human theorem re-audit is triggered: {reaudit} by the pre-registered contradiction rule. Independent human/advisor verification remains required regardless.",
        "",
        "Allowed claim boundary: these numerical results may be described as consistent, inconclusive, or as a discrepancy requiring audit. They do not prove the candidate theorem and do not by themselves establish that it is false.",
    ]
    path = RESULT_ROOT / "final_report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def summarize_all() -> dict[str, Any]:
    configs = load_configs()
    run_df, batch_df = load_formal_raw()
    setting_df = build_setting_summary(run_df, configs["base"])
    p3a_fit = build_p3a_fit_summary(run_df, setting_df, configs["base"])
    p3b_fit = build_p3b_fit_summary(run_df, setting_df, configs["base"])
    negative = build_negative_control_summary(run_df, setting_df)
    negative_audit = build_negative_control_audit(run_df, setting_df, negative)
    statuses = aggregate_statuses(setting_df, p3a_fit, p3b_fit, negative)
    gates = build_falsification_gates(setting_df, p3a_fit, p3b_fit, negative)

    write_csv(run_df, RESULT_ROOT / "run_summary.csv")
    write_csv(batch_df, RESULT_ROOT / "batch_summary.csv")
    write_csv(setting_df, RESULT_ROOT / "setting_summary.csv")
    write_csv(p3a_fit, RESULT_ROOT / "coefficient_convergence_fit.csv")
    write_csv(p3b_fit, RESULT_ROOT / "client_count_scaling_fit.csv")
    write_csv(negative, RESULT_ROOT / "negative_control_summary.csv")
    write_csv(negative_audit, RESULT_ROOT / "negative_control_audit.csv")
    write_csv(gates, RESULT_ROOT / "falsification_gates.csv")
    report = write_report(
        run_df, setting_df, p3a_fit, p3b_fit, negative, negative_audit, statuses
    )
    return {
        "statuses": statuses,
        "report": report,
        "run_summary": run_df,
        "batch_summary": batch_df,
        "setting_summary": setting_df,
        "coefficient_convergence_fit": p3a_fit,
        "client_count_scaling_fit": p3b_fit,
        "negative_control_summary": negative,
        "negative_control_audit": negative_audit,
        "falsification_gates": gates,
    }
