"""Paired SCAFFOLD/FedAvg attribution protocol and guarded execution."""

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
from ...core.inference.validation import stationarity_check
from ...core.io import REPO_ROOT, environment_manifest, gamma_token, load_yaml, write_csv, write_json
from ..p2_multidimensional_validation.formal_inference import evaluate_vector_precision
from .matched_simulation import (
    FROZEN_B20_CTRL,
    FROZEN_B20_SCAF,
    advance_paired_block,
    covariance_from_p3_config,
    objective_from_p3_config,
    _paired_rows,
)
from .simulation import FROZEN_A, FROZEN_B11_D, FROZEN_B20_FA, FROZEN_C, FROZEN_U
from .theory import matched_vector_theory_targets


MATCHED_ROOT = REPO_ROOT / "workstreams" / "p3_multidimensional_fedavg_attribution"
MATCHED_CONFIG_ROOT = MATCHED_ROOT / "configs"
MATCHED_PRIMARY_CONFIG_PATH = MATCHED_CONFIG_ROOT / "d2_matched_attribution_primary.yaml"
MATCHED_H4_CONFIG_PATH = MATCHED_CONFIG_ROOT / "d2_matched_attribution_h4_small_step.yaml"
MATCHED_FORMAL_TARGETS = ("primary", "h4-small-step")
RUN_START_PROVENANCE = "run_start_provenance.json"
FORMAL_MANIFEST = "p3_matched_formal_manifest.json"
RAW_RESULT_FILES = ("paired_run_summary.csv", "paired_batch_summary.csv")
ROW_PROVENANCE_FIELDS = {"source_commit", "source_dirty_at_run_start"}


@dataclass(frozen=True)
class MatchedFormalRunSpec:
    matrix_id: str
    target: str
    setting_id: str
    pair_id: str
    seed: int
    H: int
    N: int
    gamma: float
    delta: float
    x0: np.ndarray

    @property
    def setting_key(self) -> tuple[int, int, float]:
        return self.H, self.N, self.gamma

    @property
    def run_id(self) -> str:
        return (
            f"p3-matched__matrix-{self.matrix_id}__H{self.H}__N{self.N}"
            f"__g{gamma_token(self.gamma)}__pair-{self.seed}"
        )


def formal_config_path(target: str) -> Path:
    if target == "primary":
        return MATCHED_PRIMARY_CONFIG_PATH
    if target == "h4-small-step":
        return MATCHED_H4_CONFIG_PATH
    raise ValueError(f"Unknown matched-attribution target: {target}")


def load_formal_config(target: str) -> dict[str, Any]:
    return load_yaml(formal_config_path(target))


def formal_artifact_root(target: str, config: dict[str, Any] | None = None) -> Path:
    config = config or load_formal_config(target)
    return REPO_ROOT / str(config["artifact_namespace"])


def _path_definition(target: str, config: dict[str, Any]) -> tuple[list[int], list[dict[str, Any]]]:
    if target == "primary":
        path = config["primary_joint_path"]
        return [int(value) for value in path["H_values"]], list(path["path"])
    path = config["smaller_step_path"]
    return [int(path["H"])], list(path["path"])


def build_formal_run_matrix(
    target: str, config: dict[str, Any] | None = None
) -> list[MatchedFormalRunSpec]:
    config = config or load_formal_config(target)
    H_values, path = _path_definition(target, config)
    seeds = [int(seed) for seed in config["pairs"]["seeds"]]
    x0 = np.asarray(config["pairs"]["initial_global_state"], dtype=np.float64)
    matrix: list[MatchedFormalRunSpec] = []
    for H in H_values:
        for point in path:
            N = int(point["N"])
            gamma = 1.0 / int(point["gamma_denominator"])
            delta = int(point["delta_numerator"]) / int(point["delta_denominator"])
            setting_id = f"{config['matrix_identifier']}__H{H}__N{N}"
            for seed in seeds:
                matrix.append(
                    MatchedFormalRunSpec(
                        matrix_id=str(config["matrix_identifier"]),
                        target=target,
                        setting_id=setting_id,
                        pair_id=f"pair-{seed}",
                        seed=seed,
                        H=H,
                        N=N,
                        gamma=gamma,
                        delta=delta,
                        x0=x0.copy(),
                    )
                )
    return matrix


def audit_formal_run_matrix(target: str) -> dict[str, Any]:
    matrix = build_formal_run_matrix(target)
    groups: dict[tuple[int, int, float], list[MatchedFormalRunSpec]] = {}
    for item in matrix:
        groups.setdefault(item.setting_key, []).append(item)
    return {
        "matrix_id": matrix[0].matrix_id,
        "target": target,
        "settings": len(groups),
        "paired_chains": len(matrix),
        "pairs_per_setting": sorted(len(group) for group in groups.values()),
        "H_values": sorted({item.H for item in matrix}),
        "N_values": sorted({item.N for item in matrix}),
        "seeds": sorted({item.seed for item in matrix}),
        "unique_run_ids": len({item.run_id for item in matrix}),
        "all_unique": len({item.run_id for item in matrix}) == len(matrix),
        "gamma_equals_inverse_N": all(item.gamma == 1.0 / item.N for item in matrix),
    }


def _assert_same_setting(primary: dict[str, Any], confirmation: dict[str, Any]) -> None:
    for key in ("objective", "noise", "protocol", "per_setting_uncertainty", "precision_stopping", "extrapolation"):
        if primary[key] != confirmation[key]:
            raise RuntimeError(f"Matched-attribution configs disagree on {key}")
    for key in ("S_C", "B11_d"):
        if primary["theory"][key] != confirmation["theory"][key]:
            raise RuntimeError(f"Matched-attribution configs disagree on theory {key}")
    for key in ("B20_FA", "B20_SCAF", "B20_ctrl"):
        if primary["theory"]["by_H"][4][key] != confirmation["theory"][key]:
            raise RuntimeError(f"Matched H4 theory differs for {key}")


def check_matched_formal_protocol() -> dict[str, Any]:
    """Validate paired-attribution inputs without simulation or artifact writes."""

    primary = load_formal_config("primary")
    confirmation = load_formal_config("h4-small-step")
    _assert_same_setting(primary, confirmation)
    objective = objective_from_p3_config(primary)
    covariance = covariance_from_p3_config(primary)
    if not np.array_equal(objective.A, FROZEN_A) or not np.array_equal(objective.u, FROZEN_U):
        raise RuntimeError("Matched objective differs from the multidimensional setting")
    if objective.alpha != 0.25 or not np.array_equal(covariance, FROZEN_C):
        raise RuntimeError("Matched objective/noise differs from the established setting")
    if np.allclose(objective.A @ covariance, covariance @ objective.A):
        raise RuntimeError("Matched attribution requires noncommuting A and C")
    if primary["protocol"]["max_abs_control_sum"] != 1.0e-10:
        raise RuntimeError("Matched attribution must use the zero-sum threshold")
    expected_protocol = {
        "mixing_mu": 0.85,
        "burn_in_multiples": 100,
        "batch_length_multiples": 20,
        "min_batches": 100,
        "max_batches": 400,
        "extension_batches": 50,
        "stationarity_z": 3.0,
        "stationarity_min_chains": 7,
    }
    for key, value in expected_protocol.items():
        if primary["protocol"].get(key) != value:
            raise RuntimeError(f"Frozen matched protocol changed: {key}")
    for config, seed in ((primary, 4901), (confirmation, 4902)):
        if config["protocol_status"] != "frozen_not_executed":
            raise RuntimeError("Matched formal protocol identity changed")
        if config["bootstrap"]["unit"] != "paired_seed_label_block":
            raise RuntimeError("Matched bootstrap must preserve paired labels")
        if config["bootstrap"]["repetitions"] != 2000 or config["bootstrap"]["seed"] != seed:
            raise RuntimeError("Frozen matched bootstrap changed")
        if config["per_setting_uncertainty"]["degrees_of_freedom"] != 7:
            raise RuntimeError("Matched inference must use eight paired differences")
        if config["estimators"] != {
            "primary": "paired_signed_coordinatewise_stationary_mean_balance",
            "secondary_diagnostic": "paired_direct_stationary_sample_mean_difference",
            "norm_only_primary_forbidden": True,
        }:
            raise RuntimeError("Frozen matched estimator definition changed")
    expected = {
        "primary": {
            "matrix_id": "p3-d2-matched-attribution-primary",
            "target": "primary",
            "settings": 10,
            "paired_chains": 80,
            "pairs_per_setting": [8] * 10,
            "H_values": [2, 4],
            "N_values": [12, 16, 24, 32, 48],
            "seeds": list(range(2101, 2109)),
            "unique_run_ids": 80,
            "all_unique": True,
            "gamma_equals_inverse_N": True,
        },
        "h4-small-step": {
            "matrix_id": "p3-d2-matched-attribution-h4-small-step-confirmation",
            "target": "h4-small-step",
            "settings": 4,
            "paired_chains": 32,
            "pairs_per_setting": [8] * 4,
            "H_values": [4],
            "N_values": [64, 96, 128, 192],
            "seeds": list(range(2201, 2209)),
            "unique_run_ids": 32,
            "all_unique": True,
            "gamma_equals_inverse_N": True,
        },
    }
    for target in MATCHED_FORMAL_TARGETS:
        if audit_formal_run_matrix(target) != expected[target]:
            raise RuntimeError(f"Frozen matched {target} matrix changed")
    for H in (2, 4):
        targets = matched_vector_theory_targets(objective, covariance, H)
        for actual, frozen, label in (
            (targets.B11_d, FROZEN_B11_D, "B11_d"),
            (targets.B20_FA, FROZEN_B20_FA[H], "B20_FA"),
            (targets.B20_SCAF, FROZEN_B20_SCAF[H], "B20_SCAF"),
            (targets.B20_ctrl, FROZEN_B20_CTRL[H], "B20_ctrl"),
        ):
            if not np.allclose(actual, frozen, rtol=0.0, atol=1.0e-14):
                raise RuntimeError(f"Matched theory regression changed: H={H} {label}")
    return {
        "status": "PASS",
        "workstream": "p3",
        "component": "matched_attribution",
        "phase": "formal_protocol_check",
        "primary": expected["primary"],
        "h4_small_step": expected["h4-small-step"],
        "bootstrap": {"primary_seed": 4901, "h4_small_step_seed": 4902, "repetitions": 2000},
        "crn_design": "index_keyed_seed_round_client_local_step",
    }


def formal_protocol_dimensions(spec: MatchedFormalRunSpec, config: dict[str, Any]) -> dict[str, int]:
    protocol = config["protocol"]
    mixing_scale = math.ceil(1.0 / (float(protocol["mixing_mu"]) * spec.H * spec.gamma))
    return {
        "mixing_scale": mixing_scale,
        "burn_in_rounds": int(protocol["burn_in_multiples"]) * mixing_scale,
        "batch_length": int(protocol["batch_length_multiples"]) * mixing_scale,
        "min_batches": int(protocol["min_batches"]),
        "max_batches": int(protocol["max_batches"]),
        "extension_batches": int(protocol["extension_batches"]),
    }


def _setting_groups(
    runs: Sequence[MatchedFormalRunSpec],
) -> list[list[MatchedFormalRunSpec]]:
    groups: dict[tuple[int, int, float], list[MatchedFormalRunSpec]] = {}
    for item in runs:
        groups.setdefault(item.setting_key, []).append(item)
    return list(groups.values())


def _diagnostics(
    batches: list[dict[str, np.ndarray]],
    *,
    target: np.ndarray,
    config: dict[str, Any],
) -> dict[str, Any]:
    s_balance = np.stack([item["scaffold_balance"] for item in batches])
    f_balance = np.stack([item["fedavg_balance"] for item in batches])
    s_direct = np.stack([item["scaffold_direct"] for item in batches])
    f_direct = np.stack([item["fedavg_direct"] for item in batches])
    gamma = float(batches[0]["gamma_scalar"][0])
    d_batches = (s_balance - f_balance) / gamma**2
    d_chain = np.mean(d_batches, axis=0)
    precision = evaluate_vector_precision(
        d_chain,
        target,
        confidence_level=float(config["per_setting_uncertainty"]["simultaneous_coordinate_confidence_level"]),
        absolute=float(config["precision_stopping"]["absolute_half_width"]),
        relative=float(config["precision_stopping"]["relative_half_width"]),
    )
    pairs, dimension = d_chain.shape
    s_stationary = np.zeros((pairs, dimension), dtype=bool)
    f_stationary = np.zeros((pairs, dimension), dtype=bool)
    for pair in range(pairs):
        for coordinate in range(dimension):
            s_stationary[pair, coordinate] = stationarity_check(
                s_balance[:, pair, coordinate], z=float(config["protocol"]["stationarity_z"])
            ).passed
            f_stationary[pair, coordinate] = stationarity_check(
                f_balance[:, pair, coordinate], z=float(config["protocol"]["stationarity_z"])
            ).passed
    required = int(config["protocol"]["stationarity_min_chains"])
    stationarity_pass = bool(
        np.all(np.sum(s_stationary, axis=0) >= required)
        and np.all(np.sum(f_stationary, axis=0) >= required)
    )
    finite_s = np.logical_and.reduce([item["finite_scaffold"] for item in batches])
    finite_f = np.logical_and.reduce([item["finite_fedavg"] for item in batches])
    crn = np.logical_and.reduce([item["crn_integrity"] for item in batches])
    max_control = np.maximum.reduce([item["max_control_sum"] for item in batches])
    control_pass = max_control <= float(config["protocol"]["max_abs_control_sum"])
    scaffold_validity = finite_s & control_pass & np.all(s_stationary, axis=1)
    fedavg_validity = finite_f & np.all(f_stationary, axis=1)
    pair_validity = scaffold_validity & fedavg_validity & crn
    validity = bool(np.all(pair_validity))
    return {
        "scaffold_balance": np.mean(s_balance, axis=0),
        "fedavg_balance": np.mean(f_balance, axis=0),
        "scaffold_direct": np.mean(s_direct, axis=0),
        "fedavg_direct": np.mean(f_direct, axis=0),
        "paired_difference": d_chain,
        "precision": precision,
        "scaffold_stationarity": s_stationary,
        "fedavg_stationarity": f_stationary,
        "finite_scaffold": finite_s,
        "finite_fedavg": finite_f,
        "crn_integrity": crn,
        "max_control_sum": max_control,
        "control_pass": control_pass,
        "scaffold_validity": scaffold_validity,
        "fedavg_validity": fedavg_validity,
        "pair_validity": pair_validity,
        "stationarity_pass": stationarity_pass,
        "validity_pass": validity,
    }


def _augment_rows(
    rows: list[dict[str, Any]],
    specs: Sequence[MatchedFormalRunSpec],
    diagnostics: dict[str, Any],
    provenance: dict[str, Any],
    *,
    stopping_reason: str,
    batches_used: int,
) -> None:
    by_seed = {item.seed: item for item in specs}
    seeds = [item.seed for item in specs]
    for row in rows:
        item = by_seed[int(row["seed"])]
        pair = seeds.index(item.seed)
        coordinate = int(row["coordinate"])
        row.update(
            {
                "study": "p3_matched",
                "phase": "formal",
                "matrix_id": item.matrix_id,
                "setting_id": item.setting_id,
                "run_id": item.run_id,
                "delta": item.delta,
                "scaffold_validity_pass": bool(diagnostics["scaffold_validity"][pair]),
                "fedavg_validity_pass": bool(diagnostics["fedavg_validity"][pair]),
                "scaffold_stationarity_pass": bool(diagnostics["scaffold_stationarity"][pair, coordinate]),
                "fedavg_stationarity_pass": bool(diagnostics["fedavg_stationarity"][pair, coordinate]),
                "zero_sum_control_error": float(diagnostics["max_control_sum"][pair]),
                "zero_sum_control_pass": bool(diagnostics["control_pass"][pair]),
                "crn_integrity_pass": bool(diagnostics["crn_integrity"][pair]),
                "pair_validity_pass": bool(diagnostics["pair_validity"][pair]),
                "batches_used": batches_used,
                "stopping_reason": stopping_reason,
                "source_commit": provenance["source_commit"],
                "source_dirty_at_run_start": provenance["source_dirty_at_run_start"],
            }
        )


def simulate_formal_setting(
    specs: Sequence[MatchedFormalRunSpec],
    config: dict[str, Any],
    *,
    run_start_provenance: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs = list(specs)
    if len(specs) != 8 or any(item.setting_key != specs[0].setting_key for item in specs):
        raise ValueError("A matched formal setting requires eight paired chains")
    spec = specs[0]
    seeds = [item.seed for item in specs]
    objective = objective_from_p3_config(config)
    covariance = covariance_from_p3_config(config)
    targets = matched_vector_theory_targets(objective, covariance, spec.H)
    dimensions = formal_protocol_dimensions(spec, config)
    initial = np.stack([item.x0 for item in specs])
    x_s, x_f = initial.copy(), initial.copy()
    xi = np.zeros((8, spec.N, 2), dtype=np.float64)
    cursor = 0
    remaining = dimensions["burn_in_rounds"]
    burn_finite_scaffold = np.ones(8, dtype=bool)
    burn_finite_fedavg = np.ones(8, dtype=bool)
    burn_crn = np.ones(8, dtype=bool)
    burn_max_control = np.zeros(8, dtype=np.float64)
    while remaining:
        rounds = min(remaining, dimensions["batch_length"])
        x_s, xi, x_f, stats = advance_paired_block(
            x_s, xi, x_f, seeds, round_start=cursor, rounds=rounds,
            gamma=spec.gamma, H=spec.H, N=spec.N,
            objective=objective, covariance=covariance, collect=False,
        )
        if not np.all(stats["finite_scaffold"]) or not np.all(stats["finite_fedavg"]):
            raise RuntimeError(f"Matched burn-in became non-finite: {spec.setting_id}")
        burn_finite_scaffold &= stats["finite_scaffold"]
        burn_finite_fedavg &= stats["finite_fedavg"]
        burn_crn &= stats["crn_integrity"]
        burn_max_control = np.maximum(burn_max_control, stats["max_control_sum"])
        cursor += rounds
        remaining -= rounds
    batches: list[dict[str, np.ndarray]] = []
    target_batches = dimensions["min_batches"]
    diagnostics: dict[str, Any] | None = None
    stopping_reason = "MAX_BATCHES_REACHED"
    while len(batches) < dimensions["max_batches"]:
        while len(batches) < target_batches:
            x_s, xi, x_f, stats = advance_paired_block(
                x_s, xi, x_f, seeds, round_start=cursor,
                rounds=dimensions["batch_length"], gamma=spec.gamma,
                H=spec.H, N=spec.N, objective=objective,
                covariance=covariance, collect=True,
            )
            stats["gamma_scalar"] = np.array([spec.gamma])
            batches.append(stats)
            cursor += dimensions["batch_length"]
        diagnostics = _diagnostics(batches, target=targets.B20_ctrl, config=config)
        diagnostics["finite_scaffold"] &= burn_finite_scaffold
        diagnostics["finite_fedavg"] &= burn_finite_fedavg
        diagnostics["crn_integrity"] &= burn_crn
        diagnostics["max_control_sum"] = np.maximum(
            diagnostics["max_control_sum"], burn_max_control
        )
        diagnostics["control_pass"] = diagnostics["max_control_sum"] <= float(
            config["protocol"]["max_abs_control_sum"]
        )
        diagnostics["scaffold_validity"] = (
            diagnostics["finite_scaffold"]
            & diagnostics["control_pass"]
            & np.all(diagnostics["scaffold_stationarity"], axis=1)
        )
        diagnostics["fedavg_validity"] = (
            diagnostics["finite_fedavg"]
            & np.all(diagnostics["fedavg_stationarity"], axis=1)
        )
        diagnostics["pair_validity"] = (
            diagnostics["scaffold_validity"]
            & diagnostics["fedavg_validity"]
            & diagnostics["crn_integrity"]
        )
        diagnostics["validity_pass"] = bool(np.all(diagnostics["pair_validity"]))
        if not diagnostics["validity_pass"] and config["precision_stopping"]["stop_on_invalidity"]:
            stopping_reason = "INVALID_PAIRED_SETTING"
            break
        if diagnostics["precision"]["joint_pass"]:
            stopping_reason = "PRECISION_REACHED"
            break
        target_batches = min(
            dimensions["max_batches"], target_batches + dimensions["extension_batches"]
        )
    if diagnostics is None:
        raise RuntimeError("Matched formal setting produced no diagnostics")
    run_rows = _paired_rows(
        seeds=seeds, H=spec.H, N=spec.N, gamma=spec.gamma,
        scaffold_balance=diagnostics["scaffold_balance"],
        fedavg_balance=diagnostics["fedavg_balance"],
        scaffold_direct=diagnostics["scaffold_direct"],
        fedavg_direct=diagnostics["fedavg_direct"],
        B11_d=targets.B11_d, B20_ctrl=targets.B20_ctrl,
    )
    batch_rows: list[dict[str, Any]] = []
    for batch_index, batch in enumerate(batches):
        batch_rows.extend(
            _paired_rows(
                seeds=seeds, H=spec.H, N=spec.N, gamma=spec.gamma,
                scaffold_balance=batch["scaffold_balance"],
                fedavg_balance=batch["fedavg_balance"],
                scaffold_direct=batch["scaffold_direct"],
                fedavg_direct=batch["fedavg_direct"],
                B11_d=targets.B11_d, B20_ctrl=targets.B20_ctrl,
                batch_index=batch_index,
            )
        )
    for rows in (run_rows, batch_rows):
        _augment_rows(
            rows, specs, diagnostics, run_start_provenance,
            stopping_reason=stopping_reason, batches_used=len(batches),
        )
    return run_rows, batch_rows


def _capture_provenance(target: str, config: dict[str, Any]) -> dict[str, Any]:
    environment = environment_manifest()
    path = formal_config_path(target)
    objective = objective_from_p3_config(config)
    covariance = covariance_from_p3_config(config)
    H_values, _ = _path_definition(target, config)
    return {
        "schema_version": 1,
        "capture_point": "before_any_p3_matched_formal_output_write",
        "study": "p3_matched",
        "matrix_id": config["matrix_identifier"],
        "source_commit": environment["git_commit"],
        "source_dirty_at_run_start": environment["git_dirty"],
        "environment": environment,
        "config_path": str(path.relative_to(REPO_ROOT)),
        "config_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "paired_seeds": list(config["pairs"]["seeds"]),
        "objective": config["objective"],
        "covariance": config["noise"]["covariance"],
        "theory_targets": {
            str(H): {
                "B20_FA": matched_vector_theory_targets(objective, covariance, H).B20_FA.tolist(),
                "B20_SCAF": matched_vector_theory_targets(objective, covariance, H).B20_SCAF.tolist(),
                "B20_ctrl": matched_vector_theory_targets(objective, covariance, H).B20_ctrl.tolist(),
            }
            for H in H_values
        },
        "bootstrap": config["bootstrap"],
        "gates": config["gates"],
        "run_matrix": audit_formal_run_matrix(target),
    }


def run_formal_matrix(target: str) -> dict[str, Any]:
    """Execute attribution only from clean committed source."""

    check_matched_formal_protocol()
    config = load_formal_config(target)
    provenance = _capture_provenance(target, config)
    if provenance["source_dirty_at_run_start"] is not False or provenance["source_commit"] == "NO_COMMIT":
        raise RuntimeError(
            "Formal matched execution requires a clean committed source tree"
        )
    target_root = formal_artifact_root(target, config)
    require_complete_existing_output(
        target_root, required_files=[*RAW_RESULT_FILES, RUN_START_PROVENANCE]
    )
    staged_root = create_staging_directory(target_root)
    try:
        write_json(provenance, staged_root / RUN_START_PROVENANCE)
        shutil.copy2(formal_config_path(target), staged_root / f"p3_matched_{target.replace('-', '_')}_config_snapshot.yaml")
        run_rows: list[dict[str, Any]] = []
        batch_rows: list[dict[str, Any]] = []
        for group in _setting_groups(build_formal_run_matrix(target, config)):
            setting_runs, setting_batches = simulate_formal_setting(
                group, config, run_start_provenance=provenance
            )
            run_rows.extend(setting_runs)
            batch_rows.extend(setting_batches)
            write_csv(run_rows, staged_root / RAW_RESULT_FILES[0])
            write_csv(batch_rows, staged_root / RAW_RESULT_FILES[1])
        from .matched_formal_analysis import analyze_formal_saved, build_formal_report_and_plots

        analysis = analyze_formal_saved(target, staged_root)
        reported = build_formal_report_and_plots(target, staged_root)
        overwrite = validate_controlled_overwrite(
            staged_root, target_root,
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
    return rebase_staged_paths(
        {**analysis, **reported, "run_rows": run_rows, "batch_rows": batch_rows, "overwrite_audit": overwrite},
        staged_root,
        target_root,
    )
