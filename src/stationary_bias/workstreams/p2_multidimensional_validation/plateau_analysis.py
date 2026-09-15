"""Analysis, gates, report, and manifest for the P2 fixed-gamma plateau."""

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
from .formal import P2_ROW_PROVENANCE_FIELDS, P2_RUN_START_PROVENANCE
from .formal_analysis import build_setting_diagnostics, build_setting_summary
from .formal_inference import seed_block_bootstrap
from .plateau import (
    P2_PLATEAU_CONFIG_PATH,
    P2_PLATEAU_MANIFEST,
    P2_PLATEAU_MATRIX_ID,
    P2_PLATEAU_PROTOCOL_PATH,
    P2_PLATEAU_RAW_RESULT_FILES,
    audit_plateau_run_matrix,
    build_plateau_run_matrix,
    load_plateau_config,
    plateau_artifact_root,
)


def _required_paths(output_root: Path, names: tuple[str, ...]) -> list[Path]:
    paths = [output_root / name for name in names]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing P2 plateau artifact: " + ", ".join(missing))
    return paths


def _strict_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.astype(object).where(pd.notna(frame), None)
    return clean.to_dict(orient="records")


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    mapped = series.astype(str).str.lower().map({"true": True, "false": False})
    if mapped.isna().any():
        raise ValueError(f"Invalid Boolean values in {series.name}")
    return mapped.astype(bool)


def validate_saved_plateau(
    output_root: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    config = load_plateau_config()
    snapshot_name = str(config["config_snapshot_filename"])
    run_path, batch_path, provenance_path, snapshot_path = _required_paths(
        output_root,
        (
            "run_summary.csv",
            "batch_summary.csv",
            P2_RUN_START_PROVENANCE,
            snapshot_name,
        ),
    )
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    config_sha = hashlib.sha256(P2_PLATEAU_CONFIG_PATH.read_bytes()).hexdigest()
    protocol_sha = hashlib.sha256(P2_PLATEAU_PROTOCOL_PATH.read_bytes()).hexdigest()
    snapshot_sha = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
    if provenance.get("matrix_id") != P2_PLATEAU_MATRIX_ID:
        raise RuntimeError("P2 plateau provenance matrix identity changed")
    if provenance.get("source_dirty_at_run_start") is not False:
        raise RuntimeError("P2 plateau provenance must identify a clean source tree")
    if provenance.get("source_commit") in (None, "", "NO_COMMIT"):
        raise RuntimeError("P2 plateau provenance lacks a source commit")
    if config_sha != snapshot_sha or provenance.get("config_sha256") != config_sha:
        raise RuntimeError("P2 plateau config or snapshot changed after run start")
    if provenance.get("protocol_sha256") != protocol_sha:
        raise RuntimeError("P2 plateau protocol changed after run start")
    if provenance.get("run_matrix") != audit_plateau_run_matrix():
        raise RuntimeError("P2 plateau provenance lacks the frozen 40-chain matrix")

    run_df = pd.read_csv(run_path, keep_default_na=False)
    batch_df = pd.read_csv(batch_path, keep_default_na=False)
    expected_specs = build_plateau_run_matrix(config)
    expected_ids = {item.run_id for item in expected_specs}
    observed_ids = set(run_df["run_id"].astype(str))
    if observed_ids != expected_ids or len(run_df) != 160:
        raise ValueError("F1 plateau run summary is not the exact frozen matrix")
    expected_row_keys = {
        (item.run_id, estimator, coordinate)
        for item in expected_specs
        for estimator in ("direct_sample_mean", "stationary_mean_balance")
        for coordinate in range(2)
    }
    observed_row_keys = {
        (str(row.run_id), str(row.estimator), int(row.coordinate))
        for row in run_df.itertuples(index=False)
    }
    if observed_row_keys != expected_row_keys:
        raise ValueError("F1 plateau run summary has missing or duplicate estimator rows")
    if set(batch_df["run_id"].astype(str)) != expected_ids:
        raise ValueError("F1 plateau batch summary omits a frozen chain")

    source_commit = str(provenance["source_commit"])
    if set(run_df["source_commit"].astype(str)) != {source_commit}:
        raise ValueError("P2 plateau run rows do not match captured source provenance")
    if _bool_series(run_df["source_dirty_at_run_start"]).any():
        raise ValueError("P2 plateau run rows record a dirty source tree")
    expected_sha = str(provenance["config_sha256"])
    if set(run_df["config_sha256"].astype(str)) != {expected_sha}:
        raise ValueError("P2 plateau run rows do not match the frozen config")

    for row in run_df.itertuples(index=False):
        expected_gamma = 1.0 / 24.0
        expected_delta = expected_gamma + 1.0 / int(row.N)
        if int(row.H) != 2 or not np.isclose(
            float(row.gamma), expected_gamma, rtol=0.0, atol=1.0e-15
        ):
            raise ValueError("P2 plateau changed H or gamma across N")
        if not np.isclose(float(row.delta), expected_delta, rtol=0.0, atol=1.0e-15):
            raise ValueError("P2 plateau raw path coordinate is inconsistent")
        normalized = (
            float(row.b_component)
            - (float(row.gamma) / int(row.N)) * float(row.B10_component)
        ) / float(row.gamma) ** 2
        if not np.isclose(
            normalized, float(row.C_component), rtol=1.0e-12, atol=1.0e-13
        ):
            raise ValueError("P2 plateau C_hat does not use the frozen B10 subtraction")
    return run_df, batch_df, provenance, config


def build_plateau_fits(
    run_df: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    balance = run_df[run_df["estimator"] == "stationary_mean_balance"].copy()
    seeds = np.asarray(config["chains"]["seeds"], dtype=int)
    settings = (
        balance[["setting_id", "N", "gamma"]]
        .drop_duplicates()
        .assign(inverse_N=lambda frame: 1.0 / frame["N"].astype(float))
        .sort_values("inverse_N")
        .reset_index(drop=True)
    )
    coordinates = [0, 1]
    values = np.empty((len(settings), len(seeds), len(coordinates)), dtype=float)
    for setting_index, setting in enumerate(settings.itertuples(index=False)):
        for seed_index, seed in enumerate(seeds):
            for coordinate_index, coordinate in enumerate(coordinates):
                match = balance[
                    (balance["setting_id"] == setting.setting_id)
                    & (balance["seed"].astype(int) == int(seed))
                    & (balance["coordinate"].astype(int) == coordinate)
                ]
                if len(match) != 1:
                    raise ValueError("F1 requires one plateau row per N, seed, and coordinate")
                values[setting_index, seed_index, coordinate_index] = float(
                    match["C_component"].iloc[0]
                )

    repetitions = int(config["bootstrap"]["repetitions"])
    bootstrap_seed = int(config["bootstrap"]["seed"])
    result = seed_block_bootstrap(
        settings["inverse_N"].to_numpy(float),
        values,
        seeds,
        repetitions=repetitions,
        bootstrap_seed=bootstrap_seed,
    )
    intercepts = np.asarray(result["intercepts"], dtype=float)
    marginal = config["bootstrap"]["marginal_diagnostic_quantiles"]
    simultaneous = config["bootstrap"]["simultaneous_quantiles"]
    targets = np.asarray(config["theory"]["B20"]["value"], dtype=float)
    gamma = float(settings["gamma"].iloc[0])
    fit_rows: list[dict[str, Any]] = []
    curve_rows: list[dict[str, Any]] = []
    bootstrap_rows: list[dict[str, Any]] = []
    setting_means = np.asarray(result["setting_means"], dtype=float)
    for coordinate_index, coordinate in enumerate(coordinates):
        fit = result["fits"][coordinate_index]
        low = float(np.quantile(intercepts[:, coordinate_index], simultaneous[0]))
        high = float(np.quantile(intercepts[:, coordinate_index], simultaneous[1]))
        marginal_low = float(np.quantile(intercepts[:, coordinate_index], marginal[0]))
        marginal_high = float(np.quantile(intercepts[:, coordinate_index], marginal[1]))
        discrepancy = float(fit.beta0 - targets[coordinate_index])
        fit_rows.append(
            {
                "coordinate": coordinate,
                "H": 2,
                "gamma": gamma,
                "fit_variable": "inverse_N",
                "num_settings": len(settings),
                "beta0": fit.beta0,
                "beta1": fit.beta1,
                "marginal_ci_low": marginal_low,
                "marginal_ci_high": marginal_high,
                "simultaneous_ci_low": low,
                "simultaneous_ci_high": high,
                "B20_component": float(targets[coordinate_index]),
                "beta0_minus_B20": discrepancy,
                "beta0_minus_B20_over_gamma": discrepancy / gamma,
                "B20_covered_simultaneous_diagnostic": bool(
                    low <= targets[coordinate_index] <= high
                ),
                "bootstrap_seed": bootstrap_seed,
                "bootstrap_repetitions": repetitions,
            }
        )
        for setting_index, setting in enumerate(settings.itertuples(index=False)):
            curve_rows.append(
                {
                    "coordinate": coordinate,
                    "setting_id": setting.setting_id,
                    "N": int(setting.N),
                    "inverse_N": float(setting.inverse_N),
                    "gamma": float(setting.gamma),
                    "observed_setting_mean": float(
                        setting_means[setting_index, coordinate_index]
                    ),
                    "fitted_value": float(fit.fitted[setting_index]),
                    "residual": float(fit.residuals[setting_index]),
                }
            )
        for replicate in range(repetitions):
            bootstrap_rows.append(
                {
                    "replicate": replicate,
                    "coordinate": coordinate,
                    "beta0": float(intercepts[replicate, coordinate_index]),
                }
            )
    return pd.DataFrame(fit_rows), pd.DataFrame(curve_rows), pd.DataFrame(bootstrap_rows)


def build_plateau_gates(
    run_df: pd.DataFrame,
    setting_summary: pd.DataFrame,
    diagnostics: pd.DataFrame,
    fit_summary: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, str]:
    rows: list[dict[str, Any]] = []
    f0 = bool(_bool_series(diagnostics["validity_pass"]).all())
    rows.append(
        {
            "gate": "F0",
            "scope": "all_N_settings",
            "passed": f0,
            "scientific_warning": False,
            "detail": "finite_state_zero_sum_control_and_stationarity",
        }
    )
    expected = audit_plateau_run_matrix()
    f1 = (
        run_df["run_id"].astype(str).nunique() == expected["chains"]
        and run_df["setting_id"].astype(str).nunique() == expected["settings"]
        and sorted(run_df["seed"].astype(int).unique()) == expected["seeds"]
    )
    rows.append(
        {
            "gate": "F1",
            "scope": "frozen_matrix",
            "passed": f1,
            "scientific_warning": False,
            "detail": "all_five_N_settings_and_all_eight_seeds_present",
        }
    )

    primary = setting_summary[
        setting_summary["estimator"] == "stationary_mean_balance"
    ]
    thresholds = config["warning_thresholds"]
    f3_values: list[bool] = []
    f6_warnings: list[bool] = []
    f2_values: list[bool] = []
    f4_values: list[bool] = []
    for fit in fit_summary.itertuples(index=False):
        coordinate = int(fit.coordinate)
        fit_numbers = np.array(
            [fit.beta0, fit.beta1, fit.simultaneous_ci_low, fit.simultaneous_ci_high],
            dtype=float,
        )
        f2 = bool(np.all(np.isfinite(fit_numbers)))
        f2_values.append(f2)
        rows.append(
            {
                "gate": "F2",
                "scope": f"coordinate_{coordinate + 1}",
                "passed": f2,
                "scientific_warning": False,
                "detail": "finite_intercept_and_bootstrap_interval",
            }
        )

        coordinate_settings = primary[
            primary["coordinate"].astype(int) == coordinate
        ].sort_values("N")
        means = coordinate_settings["C_mean"].to_numpy(float)
        Ns = coordinate_settings["N"].to_numpy(int)
        if Ns.tolist() != [8, 16, 32, 64, 128]:
            raise ValueError("F1 plateau setting summary changed the frozen N order")
        nonzero_interval = bool(
            float(fit.simultaneous_ci_high) < 0.0
            or float(fit.simultaneous_ci_low) > 0.0
        )
        consistent_sign = bool(np.all(np.sign(means) == np.sign(float(fit.beta0))))
        closer_at_large_N = bool(
            abs(means[-1] - float(fit.beta0)) < abs(means[0] - float(fit.beta0))
        )
        f3 = nonzero_interval and consistent_sign and closer_at_large_N
        f3_values.append(f3)
        rows.append(
            {
                "gate": "F3",
                "scope": f"coordinate_{coordinate + 1}",
                "passed": f3,
                "scientific_warning": not f3,
                "detail": json.dumps(
                    {
                        "simultaneous_interval_excludes_zero": nonzero_interval,
                        "per_N_sign_consistent": consistent_sign,
                        "N128_closer_to_beta0_than_N8": closer_at_large_N,
                    },
                    sort_keys=True,
                ),
            }
        )

        discrepancy_values = np.array(
            [fit.beta0_minus_B20, fit.beta0_minus_B20_over_gamma], dtype=float
        )
        f4 = bool(np.all(np.isfinite(discrepancy_values)))
        f4_values.append(f4)
        rows.append(
            {
                "gate": "F4",
                "scope": f"coordinate_{coordinate + 1}",
                "passed": f4,
                "scientific_warning": False,
                "detail": (
                    f"beta0_minus_B20={fit.beta0_minus_B20:.17g};"
                    f"scaled={fit.beta0_minus_B20_over_gamma:.17g}"
                ),
            }
        )
        rows.append(
            {
                "gate": "F5",
                "scope": f"coordinate_{coordinate + 1}",
                "passed": "",
                "scientific_warning": False,
                "detail": (
                    "diagnostic_only_B20_coverage="
                    f"{bool(fit.B20_covered_simultaneous_diagnostic)}"
                ),
            }
        )

        target = float(fit.B20_component)
        sign_changes = int(np.sum(np.sign(means[1:]) != np.sign(means[:-1])))
        warning_reasons = {
            "near_zero_intercept": bool(
                abs(float(fit.beta0))
                < float(thresholds["near_zero_relative_to_B20"]) * abs(target)
            ),
            "theory_sign_reversed": bool(
                np.sign(float(fit.beta0)) != np.sign(target)
            ),
            "repeated_per_N_sign_changes": bool(
                sign_changes >= int(thresholds["repeated_sign_changes"])
            ),
            "large_N_magnitude_excess": bool(
                abs(means[-1])
                > float(thresholds["large_N_magnitude_multiple_of_B20"])
                * abs(target)
            ),
        }
        warning = any(warning_reasons.values())
        f6_warnings.append(warning)
        rows.append(
            {
                "gate": "F6",
                "scope": f"coordinate_{coordinate + 1}",
                "passed": not warning,
                "scientific_warning": warning,
                "detail": json.dumps(warning_reasons, sort_keys=True),
            }
        )

    hard_pass = f0 and f1 and all(f2_values) and all(f4_values)
    if not hard_pass:
        verdict = "FAIL"
    elif not all(f3_values) or any(f6_warnings):
        verdict = "WARNING"
    else:
        verdict = "PASS"
    return pd.DataFrame(rows), verdict


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


def _report_text(
    provenance: dict[str, Any],
    setting_summary: pd.DataFrame,
    diagnostics: pd.DataFrame,
    fit_summary: pd.DataFrame,
    gates: pd.DataFrame,
    verdict: str,
    figures: list[Path],
) -> str:
    primary = setting_summary[
        setting_summary["estimator"] == "stationary_mean_balance"
    ]
    return "\n".join(
        [
            "# P2 d=2 fixed-gamma large-N plateau",
            "",
            f"Verdict: **{verdict}**",
            "",
            f"Source commit: `{provenance['source_commit']}`",
            f"Matrix: `{provenance['matrix_id']}`",
            "Primary estimator: `stationary_mean_balance`; direct sample means are "
            "diagnostic only.",
            "",
            "The fit is `C_hat_j(N) = beta0_j + beta1_j/N`. Because gamma is fixed at 1/24,",
            "the empirical plateau is compared with `B20(H=2) + O(gamma)`; exact B20 interval",
            "coverage is reported only as a diagnostic and is not a PASS requirement.",
            "",
            "## Per-N primary estimates",
            "",
            _markdown_table(
                primary,
                [
                    "N",
                    "inverse_N",
                    "coordinate",
                    "C_mean",
                    "simultaneous_ci_low",
                    "simultaneous_ci_high",
                    "B20_component",
                ],
            ),
            "",
            "## Fixed-gamma large-N intercepts",
            "",
            _markdown_table(
                fit_summary,
                [
                    "coordinate",
                    "B20_component",
                    "beta0",
                    "simultaneous_ci_low",
                    "simultaneous_ci_high",
                    "beta0_minus_B20",
                    "beta0_minus_B20_over_gamma",
                    "beta1",
                    "B20_covered_simultaneous_diagnostic",
                ],
            ),
            "",
            "## Validity diagnostics",
            "",
            _markdown_table(
                diagnostics,
                [
                    "N",
                    "coordinate",
                    "finite_state_pass",
                    "zero_sum_control_pass",
                    "stationarity_chain_count",
                    "stationarity_pass",
                    "validity_pass",
                    "stopping_reason",
                    "max_batches_used",
                ],
            ),
            "",
            "## Falsification gates",
            "",
            _markdown_table(
                gates,
                ["gate", "scope", "passed", "scientific_warning", "detail"],
            ),
            "",
            "## Figures",
            "",
            *[f"- `{path.name}`" for path in figures],
            "",
            "## Interpretation boundary",
            "",
            "This is an empirical fixed-gamma consistency test. It is not a proof and does not",
            "require beta0 confidence intervals to contain the asymptotic B20 value exactly.",
            "The finite-gamma discrepancy is shown explicitly above.",
            "",
        ]
    )


def build_plateau_outputs(output_root: Path) -> dict[str, Any]:
    """Build every derived plateau artifact strictly from saved raw tables."""

    run_df, batch_df, provenance, config = validate_saved_plateau(output_root)
    setting_summary = build_setting_summary(run_df, config)
    setting_summary.insert(
        setting_summary.columns.get_loc("N") + 1,
        "inverse_N",
        1.0 / setting_summary["N"].astype(float),
    )
    diagnostics = build_setting_diagnostics(run_df, setting_summary, config)
    diagnostics.insert(
        diagnostics.columns.get_loc("N") + 1,
        "inverse_N",
        1.0 / diagnostics["N"].astype(float),
    )
    fit_summary, fit_curve, bootstrap = build_plateau_fits(run_df, config)
    gates, verdict = build_plateau_gates(
        run_df, setting_summary, diagnostics, fit_summary, config
    )
    frames = {
        "setting_summary": setting_summary,
        "setting_diagnostics": diagnostics,
        "plateau_fit_summary": fit_summary,
        "plateau_fit_curve": fit_curve,
        "bootstrap_intercepts": bootstrap,
        "falsification_summary": gates,
    }
    for name, frame in frames.items():
        write_csv(frame, output_root / f"{name}.csv")

    from .plateau_figures import plot_plateau_figures

    figures = plot_plateau_figures(setting_summary, fit_summary, fit_curve, output_root)
    if len(figures) != 2 or not all(path.is_file() for path in figures):
        raise RuntimeError("P2 plateau must create exactly two physical figure files")
    report = output_root / "p2_d2_fixed_gamma_largeN_plateau_report.md"
    report.write_text(
        _report_text(
            provenance,
            setting_summary,
            diagnostics,
            fit_summary,
            gates,
            verdict,
            figures,
        ),
        encoding="utf-8",
    )

    manifest_path = output_root / P2_PLATEAU_MANIFEST
    manifest = {
        "schema_version": 1,
        "study": "p2_multidimensional_validation",
        "phase": "formal_fixed_gamma_large_N_plateau",
        "matrix_id": P2_PLATEAU_MATRIX_ID,
        "verdict": verdict,
        "source_commit": provenance["source_commit"],
        "source_dirty": provenance["source_dirty_at_run_start"],
        "environment": provenance["environment"],
        "config_path": provenance["config_path"],
        "config_snapshot": provenance["config_snapshot"],
        "config_sha256": provenance["config_sha256"],
        "protocol_path": provenance["protocol_path"],
        "protocol_sha256": provenance["protocol_sha256"],
        "commands": provenance["commands"],
        "seeds": provenance["seeds"],
        "run_matrix": provenance["run_matrix"],
        "expected_chain_count": provenance["expected_chain_count"],
        "observed_chain_count": run_df["run_id"].astype(str).nunique(),
        "observed_rows": {
            "run_summary": len(run_df),
            "batch_summary": len(batch_df),
        },
        "estimators": config["estimators"],
        "normalization": config["theory"]["normalization"],
        "theory": config["theory"],
        "fit_model": config["extrapolation"],
        "uncertainty_protocol": {
            "per_setting": config["per_setting_uncertainty"],
            "bootstrap": config["bootstrap"],
        },
        "stopping_protocol": config["precision_stopping"],
        "gate_definitions": config["gates"],
        "gate_results": _strict_records(gates),
        "plateau_fits": _strict_records(fit_summary),
        "figures": [path.name for path in figures],
        "report": report.name,
        "artifact_namespace": config["artifact_namespace"],
        "artifact_filenames": config["artifact_filenames"],
        "interpretation_boundary": config["interpretation_boundary"],
    }
    expected_before_manifest = set(config["artifact_filenames"]) - {P2_PLATEAU_MANIFEST}
    missing = sorted(
        name
        for name in expected_before_manifest
        if not (output_root / name).is_file()
    )
    if missing:
        raise RuntimeError(
            "P2 plateau derived artifact inventory is incomplete: "
            + ", ".join(missing)
        )
    write_json(manifest, manifest_path)
    return {
        "output_root": output_root,
        "run_summary": run_df,
        "batch_summary": batch_df,
        **frames,
        "verdict": verdict,
        "figures": figures,
        "report": report,
        "manifest": manifest_path,
    }


def rebuild_plateau_outputs() -> dict[str, Any]:
    """Transactionally rebuild derived outputs without invoking the simulator."""

    target_root = plateau_artifact_root()
    staged_root = stage_existing_directory(target_root)
    try:
        outputs = build_plateau_outputs(staged_root)
        overwrite_audit = validate_controlled_overwrite(
            staged_root,
            target_root,
            raw_result_files=P2_PLATEAU_RAW_RESULT_FILES,
            provenance_filename=P2_RUN_START_PROVENANCE,
            identity_fields=("config_sha256", "protocol_sha256", "matrix_id"),
            excluded_row_fields=P2_ROW_PROVENANCE_FIELDS,
        )
        replace_output_directory(staged_root, target_root)
    except BaseException:
        if staged_root.exists():
            shutil.rmtree(staged_root)
        raise
    return {
        **rebase_staged_paths(outputs, staged_root, target_root),
        "overwrite_audit": overwrite_audit,
    }
