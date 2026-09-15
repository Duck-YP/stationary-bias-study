"""Isolated matched common-random-number simulation for P1."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np

from ...core.artifacts import (
    create_staging_directory,
    rebase_staged_paths as _rebase_staged_paths,
    replace_output_directory as _replace_output_directory,
    scientific_csv_content as _shared_scientific_csv_content,
    validate_controlled_overwrite,
)
from ...core.algorithms.scaffold import generate_noise_block, scaffold_round_many
from ...core.inference.statistics import (
    balance_round_value,
    standard_error,
    student_t_summary,
)
from ...core.inference.validation import (
    estimator_agreement,
    precision_threshold,
    stationarity_check,
)
from ...core.io import (
    P1_ARTIFACT_ROOT,
    P1_CONFIG_ROOT,
    config_hash,
    environment_manifest,
    gamma_token,
    load_configs,
    load_yaml,
    write_csv,
    write_json,
)
from ...core.models.noise import noise_variance
from ...core.models.objectives import get_objective
from ...core.theory.one_dimensional import b20_total, normalize_bias
from .fedavg import fedavg_round_many
from .theory import b20_fedavg, delta_b20_scaffold_minus_fedavg


P1_CONFIG_PATH = P1_CONFIG_ROOT / "matched_fedavg.yaml"
P1_RESULT_ROOT = P1_ARTIFACT_ROOT / "formal" / "p1-matched-fedavg-112-pairs"
P1_ARCHIVED_RESULT_ROOT = P1_ARTIFACT_ROOT / "archive" / "original_formal_snapshot"
P1_SMOKE_RESULT_ROOT = P1_ARTIFACT_ROOT / "smoke"
P1_RUN_START_PROVENANCE = "run_start_provenance.json"
P1_RAW_RESULT_FILES = (
    "run_summary.csv",
    "pair_summary.csv",
    "batch_summary.csv",
)
_ROW_PROVENANCE_FIELDS = {
    "git_commit",
    "source_git_dirty_at_run_start",
}
_CONTROLLED_OVERWRITE_FLOAT_FIELDS = {
    "b_direct",
    "se_direct",
    "b_balance",
    "se_balance",
    "C_direct",
    "C_balance",
    "error_to_target",
    "scaled_error",
    "control_sum_max_abs",
    "last_batch_max_abs_x",
    "C_scaffold",
    "C_fedavg",
    "error_FA",
    "scaled_error_FA",
    "Delta_C",
    "error_delta",
    "scaled_error_delta",
    "mean_x",
    "mean_b_balance_round",
    "mean_x2",
    "mean_x3",
    "mean_x4",
    "max_abs_x",
    "mean_control_second_moment",
    "max_abs_control_sum",
}
_CONTROLLED_OVERWRITE_NUMERIC_TOLERANCE = (5.0e-11, 2.0e-12)
_CONTROLLED_OVERWRITE_FIELD_TOLERANCES = {
    field: _CONTROLLED_OVERWRITE_NUMERIC_TOLERANCE
    for field in _CONTROLLED_OVERWRITE_FLOAT_FIELDS
}
# C_direct divides the direct-mean error by gamma squared and is diagnostic only.
_CONTROLLED_OVERWRITE_FIELD_TOLERANCES["C_direct"] = (5.0e-11, 2.0e-11)


@dataclass(frozen=True)
class P1RunSpec:
    grid_name: str
    H: int
    N: int
    gamma: float
    seed: int
    x0: float

    @property
    def setting_key(self) -> tuple[str, int, int, float]:
        return self.grid_name, self.H, self.N, self.gamma

    @property
    def pair_id(self) -> str:
        return (
            f"p1__grid-{self.grid_name}__H{self.H}__N{self.N}"
            f"__g{gamma_token(self.gamma)}__seed{self.seed}"
        )


def load_p1_config() -> dict[str, Any]:
    return load_yaml(P1_CONFIG_PATH)


def _specs_for_grid(
    *,
    grid_name: str,
    H_values: Sequence[int],
    grid: Sequence[dict[str, int]],
    seeds: Sequence[int],
    initial_x: dict[int, float],
) -> list[P1RunSpec]:
    return [
        P1RunSpec(
            grid_name=grid_name,
            H=int(H),
            N=int(point["N"]),
            gamma=1.0 / int(point["gamma_denominator"]),
            seed=int(seed),
            x0=float(initial_x[int(seed)]),
        )
        for H in H_values
        for point in grid
        for seed in seeds
    ]


def build_p1_run_matrix(
    config: dict[str, Any] | None = None, *, smoke: bool = False
) -> list[P1RunSpec]:
    config = config or load_p1_config()
    if smoke:
        item = config["smoke_test"]
        return [
            P1RunSpec(
                grid_name="smoke",
                H=int(item["H"]),
                N=int(item["N"]),
                gamma=float(item["gamma"]),
                seed=int(seed),
                x0=float(item["initial_x"][int(seed)]),
            )
            for seed in item["seeds"]
        ]

    primary = config["primary_coefficient_convergence"]
    small = config["small_step_h4_confirmation"]
    return [
        *_specs_for_grid(
            grid_name="primary",
            H_values=primary["H_values"],
            grid=primary["grid"],
            seeds=primary["seeds"],
            initial_x=primary["initial_x"],
        ),
        *_specs_for_grid(
            grid_name="small_step_h4",
            H_values=[small["H"]],
            grid=small["grid"],
            seeds=small["seeds"],
            initial_x=small["initial_x"],
        ),
    ]


def audit_p1_run_matrix(
    runs: Sequence[P1RunSpec] | None = None,
) -> dict[str, Any]:
    runs = list(runs or build_p1_run_matrix())
    pair_ids = [run.pair_id for run in runs]
    return {
        "total_pairs": len(runs),
        "primary_pairs": sum(run.grid_name == "primary" for run in runs),
        "small_step_h4_pairs": sum(
            run.grid_name == "small_step_h4" for run in runs
        ),
        "settings": len({run.setting_key for run in runs}),
        "unique_pair_ids": len(set(pair_ids)),
        "all_unique": len(pair_ids) == len(set(pair_ids)),
        "primary_seeds": sorted(
            {run.seed for run in runs if run.grid_name == "primary"}
        ),
        "small_step_h4_seeds": sorted(
            {run.seed for run in runs if run.grid_name == "small_step_h4"}
        ),
    }


def _capture_run_start_provenance(
    runs: Sequence[P1RunSpec],
    base: dict[str, Any],
    config: dict[str, Any],
    *,
    config_path: Path = P1_CONFIG_PATH,
    matrix_audit: Callable[[Sequence[P1RunSpec]], dict[str, Any]] = audit_p1_run_matrix,
) -> dict[str, Any]:
    """Capture source and environment identity before any P1 output write."""

    environment = environment_manifest()
    seeds_by_grid = {
        grid_name: sorted({run.seed for run in runs if run.grid_name == grid_name})
        for grid_name in sorted({run.grid_name for run in runs})
    }
    return {
        "schema_version": 1,
        "capture_point": "before_any_p1_output_write",
        "git_commit": environment["git_commit"],
        "source_git_dirty_at_run_start": environment["git_dirty"],
        "config_path": str(config_path),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "config_hash": config_hash(base, config),
        "environment": environment,
        "experiment_matrix_identifier": str(config["matrix_identifier"]),
        "phase": "smoke" if {run.grid_name for run in runs} == {"smoke"} else "formal",
        "seeds": seeds_by_grid,
        "run_matrix": matrix_audit(runs),
    }


def _advance_matched_block(
    x_scaffold: np.ndarray,
    xi_scaffold: np.ndarray,
    x_fedavg: np.ndarray,
    rngs: Sequence[np.random.Generator],
    *,
    rounds: int,
    gamma: float,
    H: int,
    N: int,
    objective_name: str,
    noise_name: str,
    collect: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Advance a matched pair block with the exact same noise object.

    Every round takes one slice from a block generated once from the pair RNGs.
    That same slice object is passed to the frozen SCAFFOLD kernel and the new
    FedAvg kernel.  Neither kernel owns or advances an RNG.
    """

    objective = get_objective(objective_name)
    noises = generate_noise_block(rngs, noise_name, rounds=rounds, H=H, N=N)
    pairs = x_scaffold.size
    sums = {
        algorithm: {
            "x": np.zeros(pairs),
            "z": np.zeros(pairs),
            "x2": np.zeros(pairs),
            "x3": np.zeros(pairs),
            "x4": np.zeros(pairs),
        }
        for algorithm in ("scaffold", "fedavg")
    }
    scaffold_control_second = np.zeros(pairs)
    maxima = {
        "scaffold_control_sum": np.zeros(pairs),
        "scaffold_abs_x": np.abs(x_scaffold).copy(),
        "fedavg_abs_x": np.abs(x_fedavg).copy(),
    }
    finite = {
        "scaffold": np.ones(pairs, dtype=bool),
        "fedavg": np.ones(pairs, dtype=bool),
    }
    noise_match_verified = True

    for round_index in range(rounds):
        scaffold_start = x_scaffold.copy()
        fedavg_start = x_fedavg.copy()
        epsilon_steps = noises[:, round_index, :, :]
        scaffold_epsilon = epsilon_steps
        fedavg_epsilon = epsilon_steps
        noise_match_verified &= scaffold_epsilon is fedavg_epsilon
        noise_match_verified &= np.array_equal(scaffold_epsilon, fedavg_epsilon)
        scaffold_result = scaffold_round_many(
            x_scaffold,
            xi_scaffold,
            gamma=gamma,
            H=H,
            objective=objective,
            epsilon_steps=scaffold_epsilon,
        )
        fedavg_result = fedavg_round_many(
            x_fedavg,
            gamma=gamma,
            H=H,
            objective=objective,
            epsilon_steps=fedavg_epsilon,
        )
        scaffold_z = np.asarray(
            balance_round_value(scaffold_result.qbar, gamma=gamma, a=objective.a)
        )
        fedavg_z = np.asarray(
            balance_round_value(fedavg_result.qbar, gamma=gamma, a=objective.a)
        )
        scaffold_finite = (
            np.isfinite(scaffold_result.x_new)
            & np.all(np.isfinite(scaffold_result.xi_new), axis=1)
            & np.all(np.isfinite(scaffold_result.qbar), axis=1)
            & np.isfinite(scaffold_z)
        )
        fedavg_finite = (
            np.isfinite(fedavg_result.x_new)
            & np.all(np.isfinite(fedavg_result.qbar), axis=1)
            & np.isfinite(fedavg_z)
        )
        finite["scaffold"] &= scaffold_finite
        finite["fedavg"] &= fedavg_finite
        maxima["scaffold_control_sum"] = np.maximum(
            maxima["scaffold_control_sum"], scaffold_result.abs_control_sum
        )
        maxima["scaffold_abs_x"] = np.maximum(
            maxima["scaffold_abs_x"], np.abs(scaffold_result.x_new)
        )
        maxima["fedavg_abs_x"] = np.maximum(
            maxima["fedavg_abs_x"], np.abs(fedavg_result.x_new)
        )
        if collect:
            for algorithm, starts, z_values in (
                ("scaffold", scaffold_start, scaffold_z),
                ("fedavg", fedavg_start, fedavg_z),
            ):
                sums[algorithm]["x"] += starts
                sums[algorithm]["z"] += z_values
                sums[algorithm]["x2"] += starts**2
                sums[algorithm]["x3"] += starts**3
                sums[algorithm]["x4"] += starts**4
            scaffold_control_second += np.mean(
                scaffold_result.xi_new * scaffold_result.xi_new, axis=1
            )
        x_scaffold = scaffold_result.x_new
        xi_scaffold = scaffold_result.xi_new
        x_fedavg = fedavg_result.x_new
        if not np.all(scaffold_finite & fedavg_finite):
            break

    stats: dict[str, Any] = {
        algorithm: {
            **{name: values / rounds for name, values in sums[algorithm].items()},
            "finite": finite[algorithm],
            "max_abs_x": maxima[f"{algorithm}_abs_x"],
        }
        for algorithm in ("scaffold", "fedavg")
    }
    stats["scaffold"]["control_second"] = scaffold_control_second / rounds
    stats["scaffold"]["max_control_sum"] = maxima["scaffold_control_sum"]
    stats["noise_match_verified"] = noise_match_verified
    return x_scaffold, xi_scaffold, x_fedavg, stats


def _algorithm_gate(
    direct_array: np.ndarray,
    balance_array: np.ndarray,
    *,
    gamma: float,
    N: int,
    a: float,
    tau: float,
    sigma2: float,
    B20_target: float,
    finite_flags: np.ndarray,
    base: dict[str, Any],
    max_control_sum: np.ndarray | None = None,
) -> dict[str, Any]:
    chain_direct = np.mean(direct_array, axis=0)
    chain_balance = np.mean(balance_array, axis=0)
    chain_C = np.asarray(
        normalize_bias(
            chain_balance,
            gamma=gamma,
            N=N,
            a=a,
            tau=tau,
            sigma2=sigma2,
        )
    )
    direct_summary = student_t_summary(chain_direct)
    balance_summary = student_t_summary(chain_balance)
    C_summary = student_t_summary(chain_C)
    agreement = estimator_agreement(
        direct_summary.mean,
        balance_summary.mean,
        direct_summary.se,
        balance_summary.se,
        z=float(base["thresholds"]["estimator_agreement_z"]),
    )
    stationarity_flags = np.array(
        [
            stationarity_check(
                balance_array[:, index],
                z=float(base["thresholds"]["stationarity_z"]),
            ).passed
            for index in range(balance_array.shape[1])
        ],
        dtype=bool,
    )
    required_stationary = min(
        int(base["thresholds"]["stationarity_min_chains"]),
        balance_array.shape[1],
    )
    stationarity = int(np.sum(stationarity_flags)) >= required_stationary
    half_width = (C_summary.ci_high - C_summary.ci_low) / 2.0
    precision = half_width <= precision_threshold(
        B20_target,
        absolute=float(base["thresholds"]["coefficient_ci_abs"]),
        relative=float(base["thresholds"]["coefficient_ci_relative"]),
    )
    control = True
    if max_control_sum is not None:
        control = bool(
            np.max(max_control_sum)
            <= float(base["thresholds"]["max_abs_control_sum"])
        )
    finite = bool(np.all(finite_flags))
    return {
        "gate_pass": finite and control and stationarity and agreement and precision,
        "finite_pass": finite,
        "control_pass": control,
        "stationarity_pass": stationarity,
        "stationarity_flags": stationarity_flags,
        "estimator_agreement_pass": agreement,
        "precision_reached": precision,
        "chain_C": chain_C,
    }


def simulate_matched_setting(
    specs: Sequence[P1RunSpec],
    base: dict[str, Any],
    config: dict[str, Any],
    *,
    protocol_override: dict[str, int] | None = None,
    run_start_provenance: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Simulate one matched setting using a joint pair-level stop rule."""

    if not specs or any(spec.setting_key != specs[0].setting_key for spec in specs):
        raise ValueError("simulate_matched_setting requires one non-empty setting")
    spec = specs[0]
    model = config["model"]
    objective = get_objective(str(model["objective"]))
    sigma2 = noise_variance(str(model["noise"]))
    protocol = base["protocol"].copy()
    if protocol_override:
        protocol.update(protocol_override)
    mixing_scale = math.ceil(1.0 / (objective.mu * spec.H * spec.gamma))
    burn_in_rounds = int(
        protocol.get("burn_in_rounds", protocol["burn_in_multiples"] * mixing_scale)
    )
    batch_length = int(
        protocol.get("batch_length", protocol["batch_length_multiples"] * mixing_scale)
    )
    min_batches = int(protocol["min_batches"])
    max_batches = int(protocol["max_batches"])
    extension_batches = int(protocol["extension_batches"])

    x_scaffold = np.array([item.x0 for item in specs], dtype=np.float64)
    xi_scaffold = np.zeros((len(specs), spec.N), dtype=np.float64)
    x_fedavg = x_scaffold.copy()
    rngs = [np.random.default_rng(item.seed) for item in specs]
    max_control_sum = np.zeros(len(specs))
    finite_flags = {
        "scaffold": np.ones(len(specs), dtype=bool),
        "fedavg": np.ones(len(specs), dtype=bool),
    }
    noise_match_verified = True

    remaining = burn_in_rounds
    while remaining:
        block_rounds = min(batch_length, remaining)
        x_scaffold, xi_scaffold, x_fedavg, stats = _advance_matched_block(
            x_scaffold,
            xi_scaffold,
            x_fedavg,
            rngs,
            rounds=block_rounds,
            gamma=spec.gamma,
            H=spec.H,
            N=spec.N,
            objective_name=str(model["objective"]),
            noise_name=str(model["noise"]),
            collect=False,
        )
        max_control_sum = np.maximum(
            max_control_sum, stats["scaffold"]["max_control_sum"]
        )
        for algorithm in finite_flags:
            finite_flags[algorithm] &= stats[algorithm]["finite"]
        noise_match_verified &= bool(stats["noise_match_verified"])
        remaining -= block_rounds
        if not np.all(finite_flags["scaffold"] & finite_flags["fedavg"]):
            break

    batch_values: dict[str, dict[str, list[np.ndarray]]] = {
        algorithm: {"direct": [], "balance": []}
        for algorithm in ("scaffold", "fedavg")
    }
    batch_rows: list[dict[str, Any]] = []
    last_max_abs_x = {
        "scaffold": np.full(len(specs), np.nan),
        "fedavg": np.full(len(specs), np.nan),
    }
    B_targets = {
        "scaffold": b20_total(
            spec.H, a=objective.a, tau=objective.tau, sigma2=sigma2
        ),
        "fedavg": b20_fedavg(
            spec.H, a=objective.a, tau=objective.tau, sigma2=sigma2
        ),
    }
    target_batches = min_batches
    gates: dict[str, dict[str, Any]] = {}
    provenance = run_start_provenance or _capture_run_start_provenance(
        specs, base, config
    )
    commit = str(provenance["git_commit"])
    source_dirty = provenance["source_git_dirty_at_run_start"]
    cfg_sha256 = str(provenance["config_sha256"])
    cfg_hash = str(provenance["config_hash"])
    matrix_identifier = str(provenance["experiment_matrix_identifier"])

    while (
        np.all(finite_flags["scaffold"] & finite_flags["fedavg"])
        and len(batch_values["scaffold"]["direct"]) < max_batches
    ):
        while len(batch_values["scaffold"]["direct"]) < target_batches:
            batch_index = len(batch_values["scaffold"]["direct"])
            x_scaffold, xi_scaffold, x_fedavg, stats = _advance_matched_block(
                x_scaffold,
                xi_scaffold,
                x_fedavg,
                rngs,
                rounds=batch_length,
                gamma=spec.gamma,
                H=spec.H,
                N=spec.N,
                objective_name=str(model["objective"]),
                noise_name=str(model["noise"]),
                collect=True,
            )
            max_control_sum = np.maximum(
                max_control_sum, stats["scaffold"]["max_control_sum"]
            )
            noise_match_verified &= bool(stats["noise_match_verified"])
            for algorithm in ("scaffold", "fedavg"):
                batch_values[algorithm]["direct"].append(stats[algorithm]["x"].copy())
                batch_values[algorithm]["balance"].append(stats[algorithm]["z"].copy())
                finite_flags[algorithm] &= stats[algorithm]["finite"]
                last_max_abs_x[algorithm] = stats[algorithm]["max_abs_x"].copy()
                for pair_index, item in enumerate(specs):
                    batch_rows.append(
                        {
                            "algorithm": algorithm,
                            "pair_id": item.pair_id,
                            "run_id": f"{item.pair_id}__algorithm-{algorithm}",
                            "seed": item.seed,
                            "grid_name": item.grid_name,
                            "H": item.H,
                            "N": item.N,
                            "gamma": item.gamma,
                            "batch_index": batch_index,
                            "round_start": burn_in_rounds + batch_index * batch_length,
                            "round_end": burn_in_rounds + (batch_index + 1) * batch_length,
                            "mean_x": stats[algorithm]["x"][pair_index],
                            "mean_b_balance_round": stats[algorithm]["z"][pair_index],
                            "mean_x2": stats[algorithm]["x2"][pair_index],
                            "mean_x3": stats[algorithm]["x3"][pair_index],
                            "mean_x4": stats[algorithm]["x4"][pair_index],
                            "max_abs_x": stats[algorithm]["max_abs_x"][pair_index],
                            "mean_control_second_moment": (
                                stats["scaffold"]["control_second"][pair_index]
                                if algorithm == "scaffold"
                                else ""
                            ),
                            "max_abs_control_sum": (
                                stats["scaffold"]["max_control_sum"][pair_index]
                                if algorithm == "scaffold"
                                else ""
                            ),
                            "noise_match_verified": noise_match_verified,
                            "git_commit": commit,
                            "source_git_dirty_at_run_start": source_dirty,
                            "config_sha256": cfg_sha256,
                            "config_hash": cfg_hash,
                            "experiment_matrix_identifier": matrix_identifier,
                        }
                    )
            if not np.all(finite_flags["scaffold"] & finite_flags["fedavg"]):
                break

        if batch_values["scaffold"]["direct"]:
            for algorithm in ("scaffold", "fedavg"):
                direct_array = np.stack(batch_values[algorithm]["direct"])
                balance_array = np.stack(batch_values[algorithm]["balance"])
                gates[algorithm] = _algorithm_gate(
                    direct_array,
                    balance_array,
                    gamma=spec.gamma,
                    N=spec.N,
                    a=objective.a,
                    tau=objective.tau,
                    sigma2=sigma2,
                    B20_target=B_targets[algorithm],
                    finite_flags=finite_flags[algorithm],
                    base=base,
                    max_control_sum=(
                        max_control_sum if algorithm == "scaffold" else None
                    ),
                )
        pair_gate = bool(
            gates
            and gates["scaffold"]["gate_pass"]
            and gates["fedavg"]["gate_pass"]
        )
        if pair_gate or target_batches >= max_batches:
            break
        target_batches = min(max_batches, target_batches + extension_batches)

    if not gates:
        raise RuntimeError("Matched simulation produced no post-burn batches")

    run_rows: list[dict[str, Any]] = []
    chain_values: dict[str, dict[str, np.ndarray]] = {}
    for algorithm in ("scaffold", "fedavg"):
        direct_array = np.stack(batch_values[algorithm]["direct"])
        balance_array = np.stack(batch_values[algorithm]["balance"])
        chain_values[algorithm] = {
            "direct": np.mean(direct_array, axis=0),
            "balance": np.mean(balance_array, axis=0),
        }
        chain_values[algorithm]["C_direct"] = np.asarray(
            normalize_bias(
                chain_values[algorithm]["direct"],
                gamma=spec.gamma,
                N=spec.N,
                a=objective.a,
                tau=objective.tau,
                sigma2=sigma2,
            )
        )
        chain_values[algorithm]["C_balance"] = np.asarray(
            normalize_bias(
                chain_values[algorithm]["balance"],
                gamma=spec.gamma,
                N=spec.N,
                a=objective.a,
                tau=objective.tau,
                sigma2=sigma2,
            )
        )
        for pair_index, item in enumerate(specs):
            b_direct = float(chain_values[algorithm]["direct"][pair_index])
            b_balance = float(chain_values[algorithm]["balance"][pair_index])
            C_direct = float(chain_values[algorithm]["C_direct"][pair_index])
            C_balance = float(chain_values[algorithm]["C_balance"][pair_index])
            per_chain_stationarity = bool(
                gates[algorithm]["stationarity_flags"][pair_index]
            )
            per_chain_agreement = estimator_agreement(
                b_direct,
                b_balance,
                standard_error(direct_array[:, pair_index]),
                standard_error(balance_array[:, pair_index]),
                z=float(base["thresholds"]["estimator_agreement_z"]),
            )
            run_rows.append(
                {
                    "phase": "smoke" if item.grid_name == "smoke" else "formal",
                    "algorithm": algorithm,
                    "pair_id": item.pair_id,
                    "run_id": f"{item.pair_id}__algorithm-{algorithm}",
                    "seed": item.seed,
                    "grid_name": item.grid_name,
                    "H": item.H,
                    "N": item.N,
                    "gamma": item.gamma,
                    "objective": str(model["objective"]),
                    "noise": str(model["noise"]),
                    "x0": item.x0,
                    "mixing_scale": mixing_scale,
                    "burn_in_rounds": burn_in_rounds,
                    "batch_length": batch_length,
                    "num_batches": direct_array.shape[0],
                    "post_burn_rounds": direct_array.shape[0] * batch_length,
                    "a": objective.a,
                    "tau": objective.tau,
                    "sigma2": sigma2,
                    "b_direct": b_direct,
                    "se_direct": standard_error(direct_array[:, pair_index]),
                    "b_balance": b_balance,
                    "se_balance": standard_error(balance_array[:, pair_index]),
                    "C_direct": C_direct,
                    "C_balance": C_balance,
                    "B20_target": B_targets[algorithm],
                    "error_to_target": C_balance - B_targets[algorithm],
                    "scaled_error": (C_balance - B_targets[algorithm]) / spec.gamma,
                    "gate_pass": bool(gates[algorithm]["gate_pass"]),
                    "finite_state_pass": bool(finite_flags[algorithm][pair_index]),
                    "stationarity_pass": per_chain_stationarity,
                    "estimator_agreement_pass": per_chain_agreement,
                    "precision_reached": bool(gates[algorithm]["precision_reached"]),
                    "control_invariant_pass": (
                        bool(gates["scaffold"]["control_pass"])
                        if algorithm == "scaffold"
                        else "NOT_APPLICABLE"
                    ),
                    "control_sum_max_abs": (
                        max_control_sum[pair_index] if algorithm == "scaffold" else ""
                    ),
                    "last_batch_max_abs_x": last_max_abs_x[algorithm][pair_index],
                    "noise_match_verified": noise_match_verified,
                    "git_commit": commit,
                    "source_git_dirty_at_run_start": source_dirty,
                    "config_sha256": cfg_sha256,
                    "config_hash": cfg_hash,
                    "experiment_matrix_identifier": matrix_identifier,
                }
            )

    pair_gate_pass = bool(
        gates["scaffold"]["gate_pass"] and gates["fedavg"]["gate_pass"]
    )
    delta_target = delta_b20_scaffold_minus_fedavg(
        spec.H, a=objective.a, tau=objective.tau, sigma2=sigma2
    )
    pair_rows: list[dict[str, Any]] = []
    for pair_index, item in enumerate(specs):
        C_scaffold = float(chain_values["scaffold"]["C_balance"][pair_index])
        C_fedavg = float(chain_values["fedavg"]["C_balance"][pair_index])
        delta_C = C_scaffold - C_fedavg
        pair_rows.append(
            {
                "pair_id": item.pair_id,
                "seed": item.seed,
                "grid_name": item.grid_name,
                "H": item.H,
                "N": item.N,
                "gamma": item.gamma,
                "C_scaffold": C_scaffold,
                "C_fedavg": C_fedavg,
                "B20_FA_target": B_targets["fedavg"],
                "error_FA": C_fedavg - B_targets["fedavg"],
                "scaled_error_FA": (C_fedavg - B_targets["fedavg"]) / spec.gamma,
                "Delta_C": delta_C,
                "Delta_B20_target": delta_target,
                "error_delta": delta_C - delta_target,
                "scaled_error_delta": (delta_C - delta_target) / spec.gamma,
                "scaffold_gate_pass": bool(gates["scaffold"]["gate_pass"]),
                "fedavg_gate_pass": bool(gates["fedavg"]["gate_pass"]),
                "pair_gate_pass": pair_gate_pass,
                "scaffold_stationarity_pass": bool(
                    gates["scaffold"]["stationarity_flags"][pair_index]
                ),
                "fedavg_stationarity_pass": bool(
                    gates["fedavg"]["stationarity_flags"][pair_index]
                ),
                "noise_match_verified": noise_match_verified,
                "git_commit": commit,
                "source_git_dirty_at_run_start": source_dirty,
                "config_sha256": cfg_sha256,
                "config_hash": cfg_hash,
                "experiment_matrix_identifier": matrix_identifier,
            }
        )
    return run_rows, pair_rows, batch_rows


def _group_settings(runs: Sequence[P1RunSpec]) -> list[list[P1RunSpec]]:
    groups: dict[tuple[str, int, int, float], list[P1RunSpec]] = {}
    for run in runs:
        groups.setdefault(run.setting_key, []).append(run)
    return list(groups.values())


def _scientific_csv_content(path: Path) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
    """Read deterministic scientific fields while excluding run provenance."""

    return _shared_scientific_csv_content(
        path, excluded_fields=_ROW_PROVENANCE_FIELDS
    )


def _validate_controlled_overwrite(
    staged_root: Path,
    current_root: Path,
    *,
    raw_result_files: Sequence[str] = P1_RAW_RESULT_FILES,
) -> dict[str, Any]:
    """Require an existing canonical result to match the staged scientific output."""

    return validate_controlled_overwrite(
        staged_root,
        current_root,
        raw_result_files=raw_result_files,
        provenance_filename=P1_RUN_START_PROVENANCE,
        identity_fields=(
            "config_sha256",
            "config_hash",
            "experiment_matrix_identifier",
        ),
        excluded_row_fields=_ROW_PROVENANCE_FIELDS,
        numeric_tolerances=_CONTROLLED_OVERWRITE_FIELD_TOLERANCES,
    )


def _run_matrix(
    runs: Sequence[P1RunSpec],
    *,
    output_root: Path,
    protocol_override: dict[str, int] | None = None,
    config: dict[str, Any] | None = None,
    config_path: Path = P1_CONFIG_PATH,
    matrix_audit: Callable[[Sequence[P1RunSpec]], dict[str, Any]] = audit_p1_run_matrix,
    run_start_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runs = list(runs)
    config = config or load_p1_config()
    base = load_configs()["base"]
    run_start_provenance = run_start_provenance or _capture_run_start_provenance(
        runs, base, config, config_path=config_path, matrix_audit=matrix_audit
    )
    write_json(
        run_start_provenance,
        output_root / P1_RUN_START_PROVENANCE,
    )
    all_run_rows: list[dict[str, Any]] = []
    all_pair_rows: list[dict[str, Any]] = []
    all_batch_rows: list[dict[str, Any]] = []
    groups = _group_settings(runs)
    for index, setting in enumerate(groups, start=1):
        sample = setting[0]
        print(
            f"[p1-matched-fedavg] setting {index}/{len(groups)}: "
            f"grid={sample.grid_name} H={sample.H} N={sample.N} gamma={sample.gamma:.10g}",
            flush=True,
        )
        run_rows, pair_rows, batch_rows = simulate_matched_setting(
            setting,
            base,
            config,
            protocol_override=protocol_override,
            run_start_provenance=run_start_provenance,
        )
        all_run_rows.extend(run_rows)
        all_pair_rows.extend(pair_rows)
        all_batch_rows.extend(batch_rows)
        write_csv(all_run_rows, output_root / "run_summary.csv")
        write_csv(all_pair_rows, output_root / "pair_summary.csv")
        write_csv(all_batch_rows, output_root / "batch_summary.csv")
        print(
            f"[p1-matched-fedavg] completed batches={run_rows[0]['num_batches']} "
            f"pair_gate_pass={pair_rows[0]['pair_gate_pass']}",
            flush=True,
        )
    return {
        "run_rows": all_run_rows,
        "pair_rows": all_pair_rows,
        "batch_rows": all_batch_rows,
        "output_root": output_root,
    }


def _run_controlled_formal_matrix(
    runs: Sequence[P1RunSpec],
    *,
    target_root: Path,
    config: dict[str, Any],
    config_path: Path,
    matrix_audit: Callable[[Sequence[P1RunSpec]], dict[str, Any]],
    finalize: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    """Build a formal result off-path, verify it, then replace its canonical copy."""

    runs = list(runs)
    base = load_configs()["base"]
    provenance = _capture_run_start_provenance(
        runs,
        base,
        config,
        config_path=config_path,
        matrix_audit=matrix_audit,
    )
    if (
        provenance["source_git_dirty_at_run_start"] is not False
        or provenance["git_commit"] == "NO_COMMIT"
    ):
        raise RuntimeError(
            "Formal P1 runs require a clean committed source tree at run start"
        )

    staged_root = create_staging_directory(target_root)
    try:
        outputs = _run_matrix(
            runs,
            output_root=staged_root,
            config=config,
            config_path=config_path,
            matrix_audit=matrix_audit,
            run_start_provenance=provenance,
        )
        outputs["analysis"] = finalize(staged_root)
        overwrite_audit = _validate_controlled_overwrite(staged_root, target_root)
        _replace_output_directory(staged_root, target_root)
    except BaseException:
        if staged_root.exists():
            shutil.rmtree(staged_root)
        raise

    outputs["overwrite_audit"] = overwrite_audit
    outputs = _rebase_staged_paths(outputs, staged_root, target_root)
    outputs["output_root"] = target_root
    return outputs


def run_p1_experiment() -> dict[str, Any]:
    audit = audit_p1_run_matrix()
    if audit != {
        "total_pairs": 112,
        "primary_pairs": 80,
        "small_step_h4_pairs": 32,
        "settings": 14,
        "unique_pair_ids": 112,
        "all_unique": True,
        "primary_seeds": list(range(301, 309)),
        "small_step_h4_seeds": list(range(401, 409)),
    }:
        raise RuntimeError(f"P1 matrix differs from the defined formal matrix: {audit}")
    config = load_p1_config()
    from .analysis import build_p1_outputs

    return _run_controlled_formal_matrix(
        build_p1_run_matrix(config),
        target_root=P1_RESULT_ROOT,
        config=config,
        config_path=P1_CONFIG_PATH,
        matrix_audit=audit_p1_run_matrix,
        finalize=build_p1_outputs,
    )


def run_p1_smoke() -> dict[str, Any]:
    config = load_p1_config()
    smoke = config["smoke_test"]
    num_batches = int(smoke["num_batches"])
    override = {
        "burn_in_rounds": int(smoke["burn_in_rounds"]),
        "batch_length": int(smoke["post_burn_rounds"] // num_batches),
        "min_batches": num_batches,
        "max_batches": num_batches,
        "extension_batches": num_batches,
    }
    outputs = _run_matrix(
        build_p1_run_matrix(config, smoke=True),
        output_root=P1_SMOKE_RESULT_ROOT,
        protocol_override=override,
    )
    from .analysis import build_p1_outputs

    outputs["analysis"] = build_p1_outputs(P1_SMOKE_RESULT_ROOT)
    return outputs
