"""Engineering smoke and shared paired simulation primitives for attribution."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ...core.io import REPO_ROOT, environment_manifest, load_yaml, write_csv, write_json
from ..p2_multidimensional_validation.inference import vector_balance_round_value
from ..p2_multidimensional_validation.objective import RankOneVectorObjective
from .paired_algorithm import indexed_noise_block, paired_round_many_vector
from .simulation import FROZEN_A, FROZEN_B11_D, FROZEN_B20_FA, FROZEN_C, FROZEN_U
from .theory import matched_vector_theory_targets, normalize_fedavg_bias


P3_ROOT = REPO_ROOT / "workstreams" / "p3_multidimensional_fedavg_attribution"
MATCHED_SMOKE_CONFIG_PATH = (
    P3_ROOT / "configs" / "d2_matched_attribution_smoke.yaml"
)
MATCHED_SMOKE_ARTIFACT_ROOT = P3_ROOT / "artifacts" / "smoke" / "matched-attribution"
FROZEN_B20_CTRL = {
    2: np.array([-0.0160013387984025, -0.0200016734980030]),
    4: np.array([-0.0560046857944088, -0.0700058572430111]),
}
FROZEN_B20_SCAF = {
    2: np.array([-0.0480040163952075, -0.0600050204940090]),
    4: np.array([-0.152012718584824, -0.190015898231030]),
}


def load_matched_smoke_config() -> dict[str, Any]:
    return load_yaml(MATCHED_SMOKE_CONFIG_PATH)


def objective_from_p3_config(config: dict[str, Any]) -> RankOneVectorObjective:
    item = config["objective"]
    return RankOneVectorObjective(
        np.asarray(item["A"], dtype=np.float64),
        np.asarray(item["u"], dtype=np.float64),
        float(item["alpha"]),
    )


def covariance_from_p3_config(config: dict[str, Any]) -> np.ndarray:
    return np.asarray(config["noise"]["covariance"], dtype=np.float64)


def check_matched_smoke_protocol() -> dict[str, Any]:
    config = load_matched_smoke_config()
    objective = objective_from_p3_config(config)
    covariance = covariance_from_p3_config(config)
    smoke = config["smoke"]
    if not np.array_equal(objective.A, FROZEN_A):
        raise RuntimeError("Matched smoke A differs from the multidimensional setting")
    if not np.array_equal(objective.u, FROZEN_U) or objective.alpha != 0.25:
        raise RuntimeError("Matched smoke objective differs from the established setting")
    if not np.array_equal(covariance, FROZEN_C):
        raise RuntimeError("Matched smoke covariance differs from the established setting")
    if (int(smoke["H"]), int(smoke["N"]), float(smoke["gamma"])) != (2, 4, 0.05):
        raise RuntimeError("Matched smoke setting changed")
    seeds = [int(value) for value in smoke["seeds"]]
    if len(seeds) != 3 or len(set(seeds)) != 3:
        raise RuntimeError("Matched smoke requires three unique paired seeds")
    targets = matched_vector_theory_targets(objective, covariance, 2)
    regressions = (
        (targets.B11_d, FROZEN_B11_D),
        (targets.B20_FA, FROZEN_B20_FA[2]),
        (targets.B20_SCAF, FROZEN_B20_SCAF[2]),
        (targets.B20_ctrl, FROZEN_B20_CTRL[2]),
    )
    if any(not np.allclose(a, b, rtol=0.0, atol=1.0e-14) for a, b in regressions):
        raise RuntimeError("Matched theory differs from frozen regressions")
    return {
        "status": "PASS",
        "workstream": "p3",
        "component": "matched_attribution",
        "phase": "engineering_smoke_check",
        "paired_seeds": seeds,
    }


def advance_paired_block(
    x_scaffold: np.ndarray,
    xi_scaffold: np.ndarray,
    x_fedavg: np.ndarray,
    seeds: Sequence[int],
    *,
    round_start: int,
    rounds: int,
    gamma: float,
    H: int,
    N: int,
    objective: RankOneVectorObjective,
    covariance: np.ndarray,
    collect: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Advance a paired block; one indexed noise block is shared by both kernels."""

    noises = indexed_noise_block(
        seeds,
        round_start=round_start,
        rounds=rounds,
        H=H,
        N=N,
        covariance=covariance,
    )
    pairs, dimension = x_scaffold.shape
    sums = {
        "scaffold_direct": np.zeros((pairs, dimension)),
        "fedavg_direct": np.zeros((pairs, dimension)),
        "scaffold_balance": np.zeros((pairs, dimension)),
        "fedavg_balance": np.zeros((pairs, dimension)),
    }
    finite_scaffold = np.ones(pairs, dtype=bool)
    finite_fedavg = np.ones(pairs, dtype=bool)
    crn_integrity = np.ones(pairs, dtype=bool)
    max_control_sum = np.zeros(pairs, dtype=np.float64)
    max_scaffold_norm = np.linalg.norm(x_scaffold, axis=1)
    max_fedavg_norm = np.linalg.norm(x_fedavg, axis=1)
    for offset in range(rounds):
        scaffold_start = x_scaffold.copy()
        fedavg_start = x_fedavg.copy()
        shared = noises[:, offset]
        result = paired_round_many_vector(
            x_scaffold,
            xi_scaffold,
            x_fedavg,
            gamma=gamma,
            H=H,
            objective=objective,
            epsilon_steps=shared,
        )
        scaffold_balance = vector_balance_round_value(
            result.scaffold.qbar, gamma=gamma, A=objective.A
        )
        fedavg_balance = vector_balance_round_value(
            result.fedavg.qbar, gamma=gamma, A=objective.A
        )
        finite_scaffold &= (
            np.all(np.isfinite(result.scaffold.x_new), axis=1)
            & np.all(np.isfinite(result.scaffold.xi_new), axis=(1, 2))
            & np.all(np.isfinite(scaffold_balance), axis=1)
        )
        finite_fedavg &= (
            np.all(np.isfinite(result.fedavg.x_new), axis=1)
            & np.all(np.isfinite(fedavg_balance), axis=1)
        )
        crn_integrity &= result.crn_integrity
        max_control_sum = np.maximum(
            max_control_sum, result.scaffold.max_abs_control_sum
        )
        max_scaffold_norm = np.maximum(
            max_scaffold_norm, np.linalg.norm(result.scaffold.x_new, axis=1)
        )
        max_fedavg_norm = np.maximum(
            max_fedavg_norm, np.linalg.norm(result.fedavg.x_new, axis=1)
        )
        if collect:
            sums["scaffold_direct"] += scaffold_start
            sums["fedavg_direct"] += fedavg_start
            sums["scaffold_balance"] += scaffold_balance
            sums["fedavg_balance"] += fedavg_balance
        x_scaffold = result.scaffold.x_new
        xi_scaffold = result.scaffold.xi_new
        x_fedavg = result.fedavg.x_new
    divisor = rounds if collect else 1
    stats = {name: values / divisor for name, values in sums.items()}
    stats.update(
        {
            "finite_scaffold": finite_scaffold,
            "finite_fedavg": finite_fedavg,
            "crn_integrity": crn_integrity,
            "max_control_sum": max_control_sum,
            "max_scaffold_norm": max_scaffold_norm,
            "max_fedavg_norm": max_fedavg_norm,
        }
    )
    return x_scaffold, xi_scaffold, x_fedavg, stats


def _paired_rows(
    *,
    seeds: Sequence[int],
    H: int,
    N: int,
    gamma: float,
    scaffold_balance: np.ndarray,
    fedavg_balance: np.ndarray,
    scaffold_direct: np.ndarray,
    fedavg_direct: np.ndarray,
    B11_d: np.ndarray,
    B20_ctrl: np.ndarray,
    batch_index: int | None = None,
) -> list[dict[str, Any]]:
    c_scaffold = normalize_fedavg_bias(
        scaffold_balance, gamma=gamma, N=N, B11_d=B11_d
    )
    c_fedavg = normalize_fedavg_bias(
        fedavg_balance, gamma=gamma, N=N, B11_d=B11_d
    )
    difference = c_scaffold - c_fedavg
    cancellation = (scaffold_balance - fedavg_balance) / gamma**2
    direct_difference = (scaffold_direct - fedavg_direct) / gamma**2
    if not np.allclose(difference, cancellation, rtol=5.0e-13, atol=5.0e-14):
        raise RuntimeError("Equivalent paired D_hat formulas disagree")
    rows: list[dict[str, Any]] = []
    for pair, seed in enumerate(seeds):
        for coordinate in range(B11_d.size):
            row: dict[str, Any] = {
                "pair_id": f"pair-{int(seed)}",
                "seed": int(seed),
                "H": H,
                "N": N,
                "gamma": gamma,
                "coordinate": coordinate,
                "scaffold_balance_bias": scaffold_balance[pair, coordinate],
                "fedavg_balance_bias": fedavg_balance[pair, coordinate],
                "scaffold_primary_coefficient": c_scaffold[pair, coordinate],
                "fedavg_primary_coefficient": c_fedavg[pair, coordinate],
                "paired_primary_difference": difference[pair, coordinate],
                "paired_cancellation_difference": cancellation[pair, coordinate],
                "scaffold_direct_bias": scaffold_direct[pair, coordinate],
                "fedavg_direct_bias": fedavg_direct[pair, coordinate],
                "paired_direct_difference": direct_difference[pair, coordinate],
                "B11_d_component": B11_d[coordinate],
                "B20_ctrl_component": B20_ctrl[coordinate],
            }
            if batch_index is not None:
                row["batch_index"] = batch_index
            rows.append(row)
    return rows


def simulate_p3_smoke(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_matched_smoke_config()
    check_matched_smoke_protocol()
    smoke = config["smoke"]
    seeds = [int(value) for value in smoke["seeds"]]
    H, N, gamma = int(smoke["H"]), int(smoke["N"]), float(smoke["gamma"])
    objective = objective_from_p3_config(config)
    covariance = covariance_from_p3_config(config)
    targets = matched_vector_theory_targets(objective, covariance, H)
    initial = np.stack(
        [np.asarray(smoke["initial_x"][seed], dtype=np.float64) for seed in seeds]
    )
    x_scaffold = initial.copy()
    x_fedavg = initial.copy()
    xi_scaffold = np.zeros((len(seeds), N, 2), dtype=np.float64)
    protocol = smoke["protocol"]
    mixing_scale = math.ceil(1.0 / (0.85 * H * gamma))
    burn_in = int(protocol["burn_in_multiples"]) * mixing_scale
    batch_length = int(protocol["batch_length_multiples"]) * mixing_scale
    num_batches = int(protocol["num_batches"])
    round_cursor = 0
    x_scaffold, xi_scaffold, x_fedavg, burn_stats = advance_paired_block(
        x_scaffold,
        xi_scaffold,
        x_fedavg,
        seeds,
        round_start=round_cursor,
        rounds=burn_in,
        gamma=gamma,
        H=H,
        N=N,
        objective=objective,
        covariance=covariance,
        collect=False,
    )
    round_cursor += burn_in
    collected: list[dict[str, np.ndarray]] = []
    batch_rows: list[dict[str, Any]] = []
    maxima = burn_stats
    for batch_index in range(num_batches):
        x_scaffold, xi_scaffold, x_fedavg, stats = advance_paired_block(
            x_scaffold,
            xi_scaffold,
            x_fedavg,
            seeds,
            round_start=round_cursor,
            rounds=batch_length,
            gamma=gamma,
            H=H,
            N=N,
            objective=objective,
            covariance=covariance,
            collect=True,
        )
        round_cursor += batch_length
        collected.append(stats)
        batch_rows.extend(
            _paired_rows(
                seeds=seeds,
                H=H,
                N=N,
                gamma=gamma,
                scaffold_balance=stats["scaffold_balance"],
                fedavg_balance=stats["fedavg_balance"],
                scaffold_direct=stats["scaffold_direct"],
                fedavg_direct=stats["fedavg_direct"],
                B11_d=targets.B11_d,
                B20_ctrl=targets.B20_ctrl,
                batch_index=batch_index,
            )
        )
        for flag in ("finite_scaffold", "finite_fedavg", "crn_integrity"):
            maxima[flag] &= stats[flag]
        maxima["max_control_sum"] = np.maximum(
            maxima["max_control_sum"], stats["max_control_sum"]
        )
    means = {
        name: np.mean(np.stack([item[name] for item in collected]), axis=0)
        for name in (
            "scaffold_direct",
            "fedavg_direct",
            "scaffold_balance",
            "fedavg_balance",
        )
    }
    run_rows = _paired_rows(
        seeds=seeds,
        H=H,
        N=N,
        gamma=gamma,
        B11_d=targets.B11_d,
        B20_ctrl=targets.B20_ctrl,
        **means,
    )
    threshold = float(protocol["max_abs_control_sum"])
    diagnostics = [
        {
            "pair_id": f"pair-{seed}",
            "seed": seed,
            "same_initial_global_state": True,
            "scaffold_control_state_exists": True,
            "fedavg_control_state_exists": False,
            "scaffold_finite_state_pass": bool(maxima["finite_scaffold"][index]),
            "fedavg_finite_state_pass": bool(maxima["finite_fedavg"][index]),
            "zero_sum_control_error": float(maxima["max_control_sum"][index]),
            "zero_sum_control_pass": bool(maxima["max_control_sum"][index] <= threshold),
            "crn_integrity_pass": bool(maxima["crn_integrity"][index]),
            "separate_algorithm_state": bool(
                not np.shares_memory(x_scaffold, x_fedavg)
                and not np.array_equal(x_scaffold[index], x_fedavg[index])
            ),
            "scientific_interpretation": "NOT_APPLICABLE_ENGINEERING_SMOKE",
        }
        for index, seed in enumerate(seeds)
    ]
    return {
        "run_rows": run_rows,
        "batch_rows": batch_rows,
        "diagnostic_rows": diagnostics,
        "metadata": {
            "S_C": targets.S_C,
            "B11_d": targets.B11_d,
            "B20_FA": targets.B20_FA,
            "B20_SCAF": targets.B20_SCAF,
            "B20_ctrl": targets.B20_ctrl,
            "burn_in_rounds": burn_in,
            "batch_length": batch_length,
        },
    }


def run_matched_smoke(
    output_root: Path = MATCHED_SMOKE_ARTIFACT_ROOT,
) -> dict[str, Any]:
    config = load_matched_smoke_config()
    validation = check_matched_smoke_protocol()
    environment = environment_manifest()
    outputs = simulate_p3_smoke(config)
    write_csv(outputs["run_rows"], output_root / "paired_run_summary.csv")
    write_csv(outputs["batch_rows"], output_root / "paired_batch_summary.csv")
    write_csv(outputs["diagnostic_rows"], output_root / "paired_diagnostic_summary.csv")
    manifest = {
        "schema_version": 1,
        "study": "p3_matched",
        "phase": "engineering_smoke",
        "source_commit": environment["git_commit"],
        "source_dirty_at_run_start": environment["git_dirty"],
        "config_path": str(MATCHED_SMOKE_CONFIG_PATH.relative_to(REPO_ROOT)),
        "config_sha256": hashlib.sha256(MATCHED_SMOKE_CONFIG_PATH.read_bytes()).hexdigest(),
        "scientific_interpretation": "NOT_APPLICABLE_ENGINEERING_SMOKE",
        "crn_design": "index_keyed_seed_round_client_local_step",
        "validation": validation,
        "objective": config["objective"],
        "noise": config["noise"],
        "theory": {
            name: np.asarray(outputs["metadata"][name]).tolist()
            for name in ("S_C", "B11_d", "B20_FA", "B20_SCAF", "B20_ctrl")
        },
        "rows": {
            "paired_coordinate_runs": len(outputs["run_rows"]),
            "paired_coordinate_batches": len(outputs["batch_rows"]),
            "pair_diagnostics": len(outputs["diagnostic_rows"]),
        },
        "artifacts": [
            "paired_run_summary.csv",
            "paired_batch_summary.csv",
            "paired_diagnostic_summary.csv",
            "p3_matched_smoke_manifest.json",
        ],
    }
    manifest_path = output_root / "p3_matched_smoke_manifest.json"
    write_json(manifest, manifest_path)
    return {**outputs, "output_root": output_root, "manifest": manifest_path}
