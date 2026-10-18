"""Multidimensional FedAvg coefficient protocol and guarded execution."""

from __future__ import annotations

import hashlib
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ...core.artifacts import (
    create_staging_directory,
    rebase_staged_paths,
    replace_output_directory,
    require_complete_existing_output,
    validate_controlled_overwrite,
)
from ...core.inference.statistics import standard_error
from ...core.inference.validation import estimator_agreement, stationarity_check
from ...core.io import (
    REPO_ROOT,
    environment_manifest,
    gamma_token,
    load_yaml,
    write_csv,
    write_json,
)
from ..p2_multidimensional_validation.formal_inference import (
    evaluate_vector_precision,
)
from ..p2_multidimensional_validation.objective import RankOneVectorObjective
from .simulation import (
    FROZEN_A,
    FROZEN_B11_D,
    FROZEN_B20_FA,
    FROZEN_C,
    FROZEN_U,
    advance_block,
)
from .theory import fedavg_vector_theory_targets, normalize_fedavg_bias


P3_FORMAL_ROOT = REPO_ROOT / "workstreams" / "p3_multidimensional_fedavg_attribution"
P3_CONFIG_ROOT = P3_FORMAL_ROOT / "configs"
P3_PRIMARY_CONFIG_PATH = P3_CONFIG_ROOT / "d2_coefficient_primary.yaml"
P3_H4_CONFIG_PATH = P3_CONFIG_ROOT / "d2_h4_small_step_confirmation.yaml"
FORMAL_TARGETS = ("primary", "h4-small-step")
RUN_START_PROVENANCE = "run_start_provenance.json"
FORMAL_MANIFEST = "p3_formal_manifest.json"
RAW_RESULT_FILES = ("run_summary.csv", "batch_summary.csv")
ROW_PROVENANCE_FIELDS = {"source_commit", "source_dirty_at_run_start"}


@dataclass(frozen=True)
class FormalRunSpec:
    matrix_id: str
    target: str
    setting_id: str
    d: int
    H: int
    N: int
    gamma: float
    delta: float
    seed: int
    x0: np.ndarray

    @property
    def setting_key(self) -> tuple[int, int, float]:
        return self.H, self.N, self.gamma

    @property
    def run_id(self) -> str:
        return (
            f"p3__phase-formal__matrix-{self.matrix_id}__H{self.H}__N{self.N}"
            f"__g{gamma_token(self.gamma)}__seed{self.seed}"
        )


def formal_config_path(target: str) -> Path:
    if target == "primary":
        return P3_PRIMARY_CONFIG_PATH
    if target == "h4-small-step":
        return P3_H4_CONFIG_PATH
    raise ValueError(f"Unknown FedAvg coefficient target: {target}")


def load_formal_config(target: str) -> dict[str, Any]:
    return load_yaml(formal_config_path(target))


def formal_artifact_root(
    target: str, config: dict[str, Any] | None = None
) -> Path:
    config = config or load_formal_config(target)
    return REPO_ROOT / str(config["artifact_namespace"])


def _path_definition(
    target: str, config: dict[str, Any]
) -> tuple[list[int], list[dict[str, Any]]]:
    if target == "primary":
        item = config["primary_joint_path"]
        return [int(value) for value in item["H_values"]], list(item["path"])
    item = config["smaller_step_path"]
    return [int(item["H"])], list(item["path"])


def build_formal_run_matrix(
    target: str, config: dict[str, Any] | None = None
) -> list[FormalRunSpec]:
    config = config or load_formal_config(target)
    H_values, path = _path_definition(target, config)
    d = int(config["objective"]["d"])
    x0 = np.asarray(config["chains"]["initial_global_state"], dtype=np.float64)
    seeds = [int(seed) for seed in config["chains"]["seeds"]]
    matrix_id = str(config["matrix_identifier"])
    specs: list[FormalRunSpec] = []
    for H in H_values:
        for point in path:
            denominator = int(point["gamma_denominator"])
            N = int(point["N"])
            gamma = 1.0 / denominator
            delta = gamma + 1.0 / N
            setting_id = f"{matrix_id}__H{H}__N{N}__g{gamma_token(gamma)}"
            for seed in seeds:
                specs.append(
                    FormalRunSpec(
                        matrix_id=matrix_id,
                        target=target,
                        setting_id=setting_id,
                        d=d,
                        H=H,
                        N=N,
                        gamma=gamma,
                        delta=delta,
                        seed=seed,
                        x0=x0.copy(),
                    )
                )
    return specs


def audit_formal_run_matrix(
    target: str, runs: Sequence[FormalRunSpec] | None = None
) -> dict[str, Any]:
    runs = list(runs or build_formal_run_matrix(target))
    settings = sorted({item.setting_key for item in runs})
    run_ids = [item.run_id for item in runs]
    return {
        "matrix_id": runs[0].matrix_id if runs else "",
        "target": target,
        "settings": len(settings),
        "chains": len(runs),
        "chains_per_setting": sorted(
            sum(item.setting_key == setting for item in runs) for setting in settings
        ),
        "H_values": sorted({item.H for item in runs}),
        "N_values": sorted({item.N for item in runs}),
        "seeds": sorted({item.seed for item in runs}),
        "unique_run_ids": len(set(run_ids)),
        "all_unique": len(run_ids) == len(set(run_ids)),
        "gamma_equals_inverse_N": all(item.gamma == 1.0 / item.N for item in runs),
    }


def objective_from_formal_config(config: dict[str, Any]) -> RankOneVectorObjective:
    item = config["objective"]
    return RankOneVectorObjective(
        np.asarray(item["A"], dtype=np.float64),
        np.asarray(item["u"], dtype=np.float64),
        float(item["alpha"]),
    )


def covariance_from_formal_config(config: dict[str, Any]) -> np.ndarray:
    return np.asarray(config["noise"]["covariance"], dtype=np.float64)


def _assert_same_scientific_setting(
    primary: dict[str, Any], confirmation: dict[str, Any]
) -> None:
    for key in ("objective", "noise", "protocol", "per_setting_uncertainty", "precision_stopping", "extrapolation"):
        if primary[key] != confirmation[key]:
            raise RuntimeError(f"FedAvg coefficient configs disagree on {key}")
    if primary["theory"]["S_C"] != confirmation["theory"]["S_C"]:
        raise RuntimeError("Frozen S_C differs between FedAvg coefficient configs")
    if primary["theory"]["B11_d"] != confirmation["theory"]["B11_d"]:
        raise RuntimeError("Frozen B11_d differs between FedAvg coefficient configs")
    if primary["theory"]["by_H"][4]["B20_FA"] != confirmation["theory"]["B20_FA"]:
        raise RuntimeError("Frozen H=4 B20_FA differs between coefficient configs")


def check_formal_protocol() -> dict[str, Any]:
    """Validate all coefficient inputs without simulating or writing artifacts."""

    primary = load_formal_config("primary")
    confirmation = load_formal_config("h4-small-step")
    _assert_same_scientific_setting(primary, confirmation)
    objective = objective_from_formal_config(primary)
    covariance = covariance_from_formal_config(primary)
    if not np.array_equal(objective.A, FROZEN_A):
        raise RuntimeError("Frozen objective A changed")
    if not np.array_equal(objective.u, FROZEN_U) or objective.alpha != 0.25:
        raise RuntimeError("Frozen rank-one objective changed")
    if not np.array_equal(covariance, FROZEN_C):
        raise RuntimeError("Frozen covariance changed")
    if np.allclose(objective.A @ covariance, covariance @ objective.A):
        raise RuntimeError("Frozen A and C unexpectedly commute")
    if primary["chains"]["initial_global_state"] != primary["objective"]["x_star"]:
        raise RuntimeError("Primary initialization must equal objective x_star")
    if confirmation["chains"]["initial_global_state"] != confirmation["objective"]["x_star"]:
        raise RuntimeError("Confirmation initialization must equal objective x_star")
    if any(key in primary["protocol"] for key in ("max_abs_control_sum", "zero_sum_control")):
        raise RuntimeError("FedAvg protocol must not contain a control diagnostic")
    expected_protocol = {
        "mixing_mu": 0.85,
        "burn_in_multiples": 100,
        "batch_length_multiples": 20,
        "min_batches": 100,
        "max_batches": 400,
        "extension_batches": 50,
        "finite_state_required": True,
        "estimator_agreement_z": 3.0,
        "stationarity_z": 3.0,
        "stationarity_min_chains": 7,
    }
    for key, value in expected_protocol.items():
        if primary["protocol"].get(key) != value:
            raise RuntimeError(f"Frozen protocol value changed: {key}")
    if primary["estimators"] != {
        "primary": "stationary_mean_balance",
        "secondary_diagnostic": "direct_stationary_sample_mean",
        "primary_representation": "signed_coordinatewise",
        "norm_only_primary_forbidden": True,
    }:
        raise RuntimeError("Frozen estimator definition changed")
    uncertainty = primary["per_setting_uncertainty"]
    expected_uncertainty = {
        "degrees_of_freedom": 7,
        "familywise_confidence_level": 0.95,
        "simultaneous_coordinate_confidence_level": 0.975,
        "marginal_diagnostic_confidence_level": 0.95,
        "coordinates": 2,
        "pool_coordinates": False,
    }
    for key, value in expected_uncertainty.items():
        if uncertainty.get(key) != value:
            raise RuntimeError(f"Frozen uncertainty value changed: {key}")
    stopping = primary["precision_stopping"]
    for key, value in {
        "absolute_half_width": 0.0025,
        "relative_half_width": 0.10,
        "check_after_batches": 100,
        "extend_by_batches": 50,
        "stop_at_batches": 400,
        "stop_on_invalidity": True,
    }.items():
        if stopping.get(key) != value:
            raise RuntimeError(f"Frozen stopping value changed: {key}")
    if primary["bootstrap"]["seed"] != 3901 or confirmation["bootstrap"]["seed"] != 3902:
        raise RuntimeError("Frozen bootstrap seed changed")
    for config in (primary, confirmation):
        if config["bootstrap"]["repetitions"] != 2000:
            raise RuntimeError("Frozen bootstrap repetitions changed")
        if config["bootstrap"]["simultaneous_quantiles"] != [0.0125, 0.9875]:
            raise RuntimeError("Frozen simultaneous quantiles changed")
        if config["protocol_status"] != "frozen_not_executed":
            raise RuntimeError("Formal protocol is not frozen before execution")
    expected_audits = {
        "primary": {
            "matrix_id": "p3-d2-coefficient-primary",
            "target": "primary",
            "settings": 10,
            "chains": 80,
            "chains_per_setting": [8] * 10,
            "H_values": [2, 4],
            "N_values": [12, 16, 24, 32, 48],
            "seeds": list(range(1101, 1109)),
            "unique_run_ids": 80,
            "all_unique": True,
            "gamma_equals_inverse_N": True,
        },
        "h4-small-step": {
            "matrix_id": "p3-d2-h4-small-step-confirmation",
            "target": "h4-small-step",
            "settings": 4,
            "chains": 32,
            "chains_per_setting": [8] * 4,
            "H_values": [4],
            "N_values": [64, 96, 128, 192],
            "seeds": list(range(1201, 1209)),
            "unique_run_ids": 32,
            "all_unique": True,
            "gamma_equals_inverse_N": True,
        },
    }
    for target, expected in expected_audits.items():
        observed = audit_formal_run_matrix(target)
        if observed != expected:
            raise RuntimeError(f"{target} matrix differs from the frozen protocol")
    for H in (2, 4):
        targets = fedavg_vector_theory_targets(objective, covariance, H)
        configured = primary["theory"]["by_H"][H]["B20_FA"]
        for actual, expected, label in (
            (targets.S_C, primary["theory"]["S_C"], "S_C"),
            (targets.B11_d, primary["theory"]["B11_d"], "B11_d"),
            (targets.B20_FA, configured, f"H={H} B20_FA"),
            (targets.B11_d, FROZEN_B11_D, "frozen B11_d regression"),
            (targets.B20_FA, FROZEN_B20_FA[H], f"frozen H={H} regression"),
        ):
            if not np.allclose(actual, expected, rtol=0.0, atol=1.0e-14):
                raise RuntimeError(f"Frozen theory mismatch for {label}")
    return {
        "status": "PASS",
        "workstream": "p3",
        "component": "fedavg_coefficient",
        "phase": "formal_protocol_check",
        "primary": expected_audits["primary"],
        "h4_small_step": expected_audits["h4-small-step"],
        "bootstrap": {
            "primary_seed": 3901,
            "h4_small_step_seed": 3902,
            "repetitions": 2000,
        },
        "config_sha256": {
            target: hashlib.sha256(formal_config_path(target).read_bytes()).hexdigest()
            for target in FORMAL_TARGETS
        },
        "control_state": False,
    }


def formal_protocol_dimensions(
    spec: FormalRunSpec, config: dict[str, Any]
) -> dict[str, int]:
    protocol = config["protocol"]
    mixing_scale = math.ceil(
        1.0 / (float(protocol["mixing_mu"]) * spec.H * spec.gamma)
    )
    return {
        "mixing_scale": mixing_scale,
        "burn_in_rounds": int(protocol["burn_in_multiples"]) * mixing_scale,
        "batch_length": int(protocol["batch_length_multiples"]) * mixing_scale,
        "min_batches": int(protocol["min_batches"]),
        "max_batches": int(protocol["max_batches"]),
        "extension_batches": int(protocol["extension_batches"]),
    }


def _setting_groups(runs: Sequence[FormalRunSpec]) -> list[list[FormalRunSpec]]:
    groups: dict[tuple[int, int, float], list[FormalRunSpec]] = {}
    for item in runs:
        groups.setdefault(item.setting_key, []).append(item)
    return list(groups.values())


def _setting_diagnostics(
    direct_batches: np.ndarray,
    balance_batches: np.ndarray,
    *,
    gamma: float,
    N: int,
    B11_d: np.ndarray,
    B20_FA: np.ndarray,
    finite_flags: np.ndarray,
    config: dict[str, Any],
) -> dict[str, Any]:
    chain_direct = np.mean(direct_batches, axis=0)
    chain_balance = np.mean(balance_batches, axis=0)
    chain_C = normalize_fedavg_bias(
        chain_balance, gamma=gamma, N=N, B11_d=B11_d
    )
    precision = evaluate_vector_precision(
        chain_C,
        B20_FA,
        confidence_level=float(config["per_setting_uncertainty"]["simultaneous_coordinate_confidence_level"]),
        absolute=float(config["precision_stopping"]["absolute_half_width"]),
        relative=float(config["precision_stopping"]["relative_half_width"]),
    )
    chains, dimension = chain_balance.shape
    stationarity_flags = np.zeros((chains, dimension), dtype=bool)
    agreement_flags = np.zeros((chains, dimension), dtype=bool)
    for chain in range(chains):
        for coordinate in range(dimension):
            stationarity_flags[chain, coordinate] = stationarity_check(
                balance_batches[:, chain, coordinate],
                z=float(config["protocol"]["stationarity_z"]),
            ).passed
            agreement_flags[chain, coordinate] = estimator_agreement(
                chain_direct[chain, coordinate],
                chain_balance[chain, coordinate],
                standard_error(direct_batches[:, chain, coordinate]),
                standard_error(balance_batches[:, chain, coordinate]),
                z=float(config["protocol"]["estimator_agreement_z"]),
            )
    required = int(config["protocol"]["stationarity_min_chains"])
    stationarity_coordinate_pass = np.sum(stationarity_flags, axis=0) >= required
    finite_pass = bool(np.all(finite_flags))
    return {
        "chain_direct": chain_direct,
        "chain_balance": chain_balance,
        "chain_C_balance": chain_C,
        "precision": precision,
        "stationarity_flags": stationarity_flags,
        "stationarity_coordinate_pass": stationarity_coordinate_pass,
        "stationarity_pass": bool(np.all(stationarity_coordinate_pass)),
        "agreement_flags": agreement_flags,
        "finite_pass": finite_pass,
        "validity_pass": finite_pass and bool(np.all(stationarity_coordinate_pass)),
    }


def _result_row(
    item: FormalRunSpec,
    *,
    estimator: str,
    coordinate: int,
    bias: np.ndarray,
    normalized: np.ndarray,
    B11_d: np.ndarray,
    B20_FA: np.ndarray,
    batches_used: int,
    stopping_reason: str,
    diagnostics: dict[str, Any],
    provenance: dict[str, Any],
    batch_index: int | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "study": "p3",
        "phase": "formal",
        "matrix_id": item.matrix_id,
        "setting_id": item.setting_id,
        "run_id": item.run_id,
        "seed": item.seed,
        "d": item.d,
        "coordinate": coordinate,
        "H": item.H,
        "N": item.N,
        "gamma": item.gamma,
        "delta": item.delta,
        "estimator": estimator,
        "b_component": bias[coordinate],
        "B11_d_component": B11_d[coordinate],
        "C_component": normalized[coordinate],
        "B20_FA_component": B20_FA[coordinate],
        "normalized_error_component": normalized[coordinate] - B20_FA[coordinate],
        "batches_used": batches_used,
        "stopping_reason": stopping_reason,
        "validity_pass": diagnostics["validity_pass"],
        "finite_state_pass": diagnostics["finite_pass"],
        "stationarity_pass": diagnostics["stationarity_pass"],
        "direct_balance_agreement_pass": bool(
            diagnostics["agreement_flags"][list(provenance["seeds"]).index(item.seed), coordinate]
        ),
        "source_commit": provenance["source_commit"],
        "source_dirty_at_run_start": provenance["source_dirty_at_run_start"],
    }
    if batch_index is not None:
        row["batch_index"] = batch_index
    return row


def simulate_formal_setting(
    specs: Sequence[FormalRunSpec],
    config: dict[str, Any],
    *,
    run_start_provenance: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs = list(specs)
    if len(specs) != 8 or any(item.setting_key != specs[0].setting_key for item in specs):
        raise ValueError("A formal setting requires eight matching chains")
    spec = specs[0]
    objective = objective_from_formal_config(config)
    covariance = covariance_from_formal_config(config)
    targets = fedavg_vector_theory_targets(objective, covariance, spec.H)
    dimensions = formal_protocol_dimensions(spec, config)
    x = np.stack([item.x0 for item in specs])
    rngs = [np.random.default_rng(item.seed) for item in specs]
    finite_flags = np.ones(len(specs), dtype=bool)
    remaining = dimensions["burn_in_rounds"]
    while remaining:
        rounds = min(dimensions["batch_length"], remaining)
        x, stats = advance_block(
            x,
            rngs,
            rounds=rounds,
            gamma=spec.gamma,
            H=spec.H,
            N=spec.N,
            objective=objective,
            covariance=covariance,
            collect=False,
        )
        finite_flags &= stats["finite"].astype(bool)
        remaining -= rounds
        if not np.all(finite_flags):
            raise RuntimeError(f"Formal setting {spec.setting_id} became non-finite")

    direct_batches: list[np.ndarray] = []
    balance_batches: list[np.ndarray] = []
    raw_batches: list[tuple[int, np.ndarray, np.ndarray]] = []
    target_batches = dimensions["min_batches"]
    diagnostics: dict[str, Any] | None = None
    stopping_reason = "MAX_BATCHES_REACHED"
    while len(direct_batches) < dimensions["max_batches"]:
        while len(direct_batches) < target_batches:
            x, stats = advance_block(
                x,
                rngs,
                rounds=dimensions["batch_length"],
                gamma=spec.gamma,
                H=spec.H,
                N=spec.N,
                objective=objective,
                covariance=covariance,
                collect=True,
            )
            batch_index = len(direct_batches)
            direct_batches.append(stats["direct"].copy())
            balance_batches.append(stats["balance"].copy())
            raw_batches.append((batch_index, stats["direct"].copy(), stats["balance"].copy()))
            finite_flags &= stats["finite"].astype(bool)
        diagnostics = _setting_diagnostics(
            np.stack(direct_batches),
            np.stack(balance_batches),
            gamma=spec.gamma,
            N=spec.N,
            B11_d=targets.B11_d,
            B20_FA=targets.B20_FA,
            finite_flags=finite_flags,
            config=config,
        )
        if not diagnostics["validity_pass"] and config["precision_stopping"]["stop_on_invalidity"]:
            stopping_reason = "INVALID_SETTING"
            break
        if diagnostics["precision"]["joint_pass"]:
            stopping_reason = "PRECISION_REACHED"
            break
        target_batches = min(
            target_batches + dimensions["extension_batches"],
            dimensions["max_batches"],
        )
    if diagnostics is None:
        raise RuntimeError("Formal setting produced no diagnostics")

    batches_used = len(direct_batches)
    run_rows: list[dict[str, Any]] = []
    for estimator, values in (
        ("direct_sample_mean", diagnostics["chain_direct"]),
        ("stationary_mean_balance", diagnostics["chain_balance"]),
    ):
        normalized = normalize_fedavg_bias(
            values, gamma=spec.gamma, N=spec.N, B11_d=targets.B11_d
        )
        for chain, item in enumerate(specs):
            for coordinate in range(spec.d):
                run_rows.append(
                    _result_row(
                        item,
                        estimator=estimator,
                        coordinate=coordinate,
                        bias=values[chain],
                        normalized=normalized[chain],
                        B11_d=targets.B11_d,
                        B20_FA=targets.B20_FA,
                        batches_used=batches_used,
                        stopping_reason=stopping_reason,
                        diagnostics=diagnostics,
                        provenance=run_start_provenance,
                    )
                )
    batch_rows: list[dict[str, Any]] = []
    for batch_index, direct, balance in raw_batches:
        for estimator, values in (("direct_sample_mean", direct), ("stationary_mean_balance", balance)):
            normalized = normalize_fedavg_bias(
                values, gamma=spec.gamma, N=spec.N, B11_d=targets.B11_d
            )
            for chain, item in enumerate(specs):
                for coordinate in range(spec.d):
                    batch_rows.append(
                        _result_row(
                            item,
                            estimator=estimator,
                            coordinate=coordinate,
                            bias=values[chain],
                            normalized=normalized[chain],
                            B11_d=targets.B11_d,
                            B20_FA=targets.B20_FA,
                            batches_used=batches_used,
                            stopping_reason=stopping_reason,
                            diagnostics=diagnostics,
                            provenance=run_start_provenance,
                            batch_index=batch_index,
                        )
                    )
    return run_rows, batch_rows


def validate_formal_output_root(target_root: Path, expected_root: Path) -> None:
    if target_root.resolve() != expected_root.resolve():
        raise RuntimeError("Formal output root must equal its coefficient namespace")
    if P3_FORMAL_ROOT.resolve() not in target_root.resolve().parents:
        raise RuntimeError("Formal output root escaped the workstream")


def _capture_provenance(
    target: str, config: dict[str, Any], environment: dict[str, Any]
) -> dict[str, Any]:
    path = formal_config_path(target)
    return {
        "schema_version": 1,
        "capture_point": "before_any_p3_formal_output_write",
        "study": "p3",
        "phase": "formal",
        "matrix_id": config["matrix_identifier"],
        "source_commit": environment["git_commit"],
        "source_dirty_at_run_start": environment["git_dirty"],
        "environment": environment,
        "config_path": str(path.relative_to(REPO_ROOT)),
        "config_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "protocol_path": str(path.relative_to(REPO_ROOT)),
        "protocol_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "seeds": list(config["chains"]["seeds"]),
        "bootstrap_seed": int(config["bootstrap"]["seed"]),
        "bootstrap_repetitions": int(config["bootstrap"]["repetitions"]),
        "run_matrix": audit_formal_run_matrix(target),
        "expected_chain_count": len(build_formal_run_matrix(target, config)),
    }


def run_formal_matrix(target: str) -> dict[str, Any]:
    """Run a frozen matrix only from clean committed source."""

    check_formal_protocol()
    config = load_formal_config(target)
    environment = environment_manifest()
    if environment["git_dirty"] is not False or environment["git_commit"] == "NO_COMMIT":
        raise RuntimeError(
            "Formal coefficient execution requires a clean committed source tree"
        )
    target_root = formal_artifact_root(target, config)
    validate_formal_output_root(target_root, formal_artifact_root(target, config))
    require_complete_existing_output(
        target_root, required_files=[*RAW_RESULT_FILES, RUN_START_PROVENANCE]
    )
    staged_root = create_staging_directory(target_root)
    provenance = _capture_provenance(target, config, environment)
    try:
        write_json(provenance, staged_root / RUN_START_PROVENANCE)
        shutil.copy2(
            formal_config_path(target),
            staged_root / f"p3_{target.replace('-', '_')}_config_snapshot.yaml",
        )
        run_rows: list[dict[str, Any]] = []
        batch_rows: list[dict[str, Any]] = []
        for group in _setting_groups(build_formal_run_matrix(target, config)):
            setting_runs, setting_batches = simulate_formal_setting(
                group, config, run_start_provenance=provenance
            )
            run_rows.extend(setting_runs)
            batch_rows.extend(setting_batches)
        write_csv(run_rows, staged_root / "run_summary.csv")
        write_csv(batch_rows, staged_root / "batch_summary.csv")
        from .formal_analysis import analyze_formal_saved, build_formal_report_and_plots

        analyzed = analyze_formal_saved(target, staged_root)
        reported = build_formal_report_and_plots(target, staged_root)
        overwrite_audit = validate_controlled_overwrite(
            staged_root,
            target_root,
            raw_result_files=RAW_RESULT_FILES,
            provenance_filename=RUN_START_PROVENANCE,
            identity_fields=("config_sha256", "matrix_id"),
            excluded_row_fields=ROW_PROVENANCE_FIELDS,
        )
        replace_output_directory(staged_root, target_root)
    except BaseException:
        if staged_root.exists():
            shutil.rmtree(staged_root)
        raise
    outputs = rebase_staged_paths(
        {
            **analyzed,
            **reported,
            "run_rows": run_rows,
            "batch_rows": batch_rows,
        },
        staged_root,
        target_root,
    )
    outputs["overwrite_audit"] = overwrite_audit
    return outputs
