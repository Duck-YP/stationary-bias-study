"""Engineering smoke pipeline for the multidimensional FedAvg coefficient."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ...core.io import (
    REPO_ROOT,
    config_hash,
    environment_manifest,
    gamma_token,
    load_configs,
    load_yaml,
    write_csv,
    write_json,
)
from ..p2_multidimensional_validation.inference import vector_balance_round_value
from ..p2_multidimensional_validation.noise import generate_vector_noise_block
from ..p2_multidimensional_validation.objective import RankOneVectorObjective
from .algorithm import fedavg_round_many_vector
from .theory import fedavg_vector_theory_targets, normalize_fedavg_bias


P3_ROOT = REPO_ROOT / "workstreams" / "p3_multidimensional_fedavg_attribution"
P3_SMOKE_CONFIG_PATH = P3_ROOT / "configs" / "d2_smoke.yaml"
P3_SMOKE_ARTIFACT_ROOT = P3_ROOT / "artifacts" / "smoke"
FROZEN_A = np.array([[1.2, 0.2], [0.2, 1.0]], dtype=np.float64)
FROZEN_U = np.array([1.0, 1.0], dtype=np.float64) / np.sqrt(2.0)
FROZEN_C = np.array([[1.0, 0.2], [0.2, 0.7]], dtype=np.float64)
FROZEN_B11_D = np.array([-0.024459428167733, -0.030574285209666])
FROZEN_B20_FA = {
    2: np.array([-0.032002677596805, -0.040003346996006]),
    4: np.array([-0.096008032790415, -0.120010040988019]),
}


@dataclass(frozen=True)
class SmokeSpec:
    setting_id: str
    d: int
    H: int
    N: int
    gamma: float
    seed: int
    x0: np.ndarray

    @property
    def run_id(self) -> str:
        return (
            f"p3__phase-smoke__setting-{self.setting_id}__d{self.d}"
            f"__H{self.H}__N{self.N}__g{gamma_token(self.gamma)}__seed{self.seed}"
        )


def load_smoke_config() -> dict[str, Any]:
    return load_yaml(P3_SMOKE_CONFIG_PATH)


def objective_from_config(config: dict[str, Any]) -> RankOneVectorObjective:
    item = config["objective"]
    return RankOneVectorObjective(
        np.asarray(item["A"], dtype=np.float64),
        np.asarray(item["u"], dtype=np.float64),
        float(item["alpha"]),
    )


def covariance_from_config(config: dict[str, Any]) -> np.ndarray:
    return np.asarray(config["noise"]["covariance"], dtype=np.float64)


def build_smoke_specs(config: dict[str, Any] | None = None) -> list[SmokeSpec]:
    config = config or load_smoke_config()
    smoke = config["smoke"]
    return [
        SmokeSpec(
            setting_id=str(config["setting_id"]),
            d=int(smoke["d"]),
            H=int(smoke["H"]),
            N=int(smoke["N"]),
            gamma=float(smoke["gamma"]),
            seed=int(seed),
            x0=np.asarray(smoke["initial_x"][int(seed)], dtype=np.float64),
        )
        for seed in smoke["seeds"]
    ]


def check_smoke_protocol() -> dict[str, Any]:
    config = load_smoke_config()
    objective = objective_from_config(config)
    covariance = covariance_from_config(config)
    specs = build_smoke_specs(config)
    if not np.array_equal(objective.A, FROZEN_A):
        raise RuntimeError("Smoke A differs from the frozen multidimensional d=2 matrix")
    if not np.array_equal(objective.u, FROZEN_U) or objective.alpha != 0.25:
        raise RuntimeError("Smoke rank-one objective differs from the frozen setting")
    if not np.array_equal(covariance, FROZEN_C):
        raise RuntimeError("Smoke covariance differs from the coefficient covariance")
    if np.allclose(objective.A @ covariance, covariance @ objective.A):
        raise RuntimeError("Smoke covariance must not commute with A")
    smoke = config["smoke"]
    if (int(smoke["d"]), int(smoke["H"]), int(smoke["N"]), float(smoke["gamma"])) != (2, 2, 4, 0.05):
        raise RuntimeError("Smoke setting changed")
    if len({item.seed for item in specs}) != len(specs):
        raise RuntimeError("Smoke seeds must be unique")
    if any(item.x0.shape != (2,) for item in specs):
        raise RuntimeError("Smoke initial states must have dimension two")
    targets = fedavg_vector_theory_targets(objective, covariance, 2)
    if not np.allclose(targets.B11_d, FROZEN_B11_D, rtol=0.0, atol=1.0e-14):
        raise RuntimeError("Calculated B11_d differs from the frozen regression")
    if not np.allclose(targets.B20_FA, FROZEN_B20_FA[2], rtol=0.0, atol=1.0e-14):
        raise RuntimeError("Calculated H=2 B20_FA differs from the frozen regression")
    return {
        "status": "PASS",
        "workstream": "p3",
        "component": "fedavg_coefficient",
        "phase": "engineering_smoke_check",
        "setting_id": config["setting_id"],
        "chains": len(specs),
        "seeds": [item.seed for item in specs],
        "no_control_state": True,
    }


def advance_block(
    x: np.ndarray,
    rngs: Sequence[np.random.Generator],
    *,
    rounds: int,
    gamma: float,
    H: int,
    N: int,
    objective: RankOneVectorObjective,
    covariance: np.ndarray,
    collect: bool,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    noises = generate_vector_noise_block(
        rngs, covariance, rounds=rounds, H=H, N=N
    )
    chains, dimension = x.shape
    direct_sum = np.zeros((chains, dimension), dtype=np.float64)
    balance_sum = np.zeros((chains, dimension), dtype=np.float64)
    max_state_norm = np.linalg.norm(x, axis=1)
    finite = np.ones(chains, dtype=bool)
    for round_index in range(rounds):
        x_start = x.copy()
        result = fedavg_round_many_vector(
            x,
            gamma=gamma,
            H=H,
            objective=objective,
            epsilon_steps=noises[:, round_index, :, :, :],
        )
        balance = vector_balance_round_value(
            result.qbar, gamma=gamma, A=objective.A
        )
        chain_finite = (
            np.all(np.isfinite(result.x_new), axis=1)
            & np.all(np.isfinite(result.qbar), axis=(1, 2))
            & np.all(np.isfinite(result.theta_final), axis=(1, 2))
            & np.all(np.isfinite(balance), axis=1)
        )
        finite &= chain_finite
        max_state_norm = np.maximum(
            max_state_norm, np.linalg.norm(result.x_new, axis=1)
        )
        if collect:
            direct_sum += x_start
            balance_sum += balance
        x = result.x_new
        if not np.all(chain_finite):
            break
    divisor = rounds if collect else 1
    return x, {
        "direct": direct_sum / divisor,
        "balance": balance_sum / divisor,
        "max_state_norm": max_state_norm,
        "finite": finite,
    }


def _coordinate_row(
    spec: SmokeSpec,
    *,
    estimator: str,
    coordinate: int,
    bias: np.ndarray,
    normalized: np.ndarray,
    B11_d: np.ndarray,
    B20_FA: np.ndarray,
    batch_index: int | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "study": "p3",
        "phase": "smoke",
        "setting_id": spec.setting_id,
        "run_id": spec.run_id,
        "seed": spec.seed,
        "d": spec.d,
        "coordinate": coordinate,
        "H": spec.H,
        "N": spec.N,
        "gamma": spec.gamma,
        "estimator": estimator,
        "b_component": bias[coordinate],
        "B11_d_component": B11_d[coordinate],
        "C_component": normalized[coordinate],
        "B20_FA_component": B20_FA[coordinate],
        "normalized_error_component": normalized[coordinate] - B20_FA[coordinate],
    }
    if batch_index is not None:
        row["batch_index"] = batch_index
    return row


def simulate_smoke(
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_smoke_config()
    check_smoke_protocol()
    specs = build_smoke_specs(config)
    spec = specs[0]
    objective = objective_from_config(config)
    covariance = covariance_from_config(config)
    targets = fedavg_vector_theory_targets(objective, covariance, spec.H)
    protocol = config["smoke"]["protocol"]
    mixing_mu = float(np.min(np.linalg.eigvalsh(objective.A)))
    mixing_scale = math.ceil(1.0 / (mixing_mu * spec.H * spec.gamma))
    burn_in_rounds = int(protocol["burn_in_multiples"]) * mixing_scale
    batch_length = int(protocol["batch_length_multiples"]) * mixing_scale
    num_batches = int(protocol["num_batches"])
    x = np.stack([item.x0 for item in specs])
    rngs = [np.random.default_rng(item.seed) for item in specs]
    max_state_norm = np.linalg.norm(x, axis=1)
    finite = np.ones(len(specs), dtype=bool)

    remaining = burn_in_rounds
    while remaining:
        rounds = min(batch_length, remaining)
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
        max_state_norm = np.maximum(max_state_norm, stats["max_state_norm"])
        finite &= stats["finite"].astype(bool)
        remaining -= rounds

    direct_batches: list[np.ndarray] = []
    balance_batches: list[np.ndarray] = []
    batch_rows: list[dict[str, Any]] = []
    for batch_index in range(num_batches):
        x, stats = advance_block(
            x,
            rngs,
            rounds=batch_length,
            gamma=spec.gamma,
            H=spec.H,
            N=spec.N,
            objective=objective,
            covariance=covariance,
            collect=True,
        )
        direct_batches.append(stats["direct"].copy())
        balance_batches.append(stats["balance"].copy())
        max_state_norm = np.maximum(max_state_norm, stats["max_state_norm"])
        finite &= stats["finite"].astype(bool)
        for estimator, values in (
            ("direct_sample_mean", stats["direct"]),
            ("stationary_mean_balance", stats["balance"]),
        ):
            normalized = normalize_fedavg_bias(
                values, gamma=spec.gamma, N=spec.N, B11_d=targets.B11_d
            )
            for chain_index, item in enumerate(specs):
                for coordinate in range(spec.d):
                    batch_rows.append(
                        _coordinate_row(
                            item,
                            estimator=estimator,
                            coordinate=coordinate,
                            bias=values[chain_index],
                            normalized=normalized[chain_index],
                            B11_d=targets.B11_d,
                            B20_FA=targets.B20_FA,
                            batch_index=batch_index,
                        )
                    )

    direct = np.mean(np.stack(direct_batches), axis=0)
    balance = np.mean(np.stack(balance_batches), axis=0)
    run_rows: list[dict[str, Any]] = []
    for estimator, values in (
        ("direct_sample_mean", direct),
        ("stationary_mean_balance", balance),
    ):
        normalized = normalize_fedavg_bias(
            values, gamma=spec.gamma, N=spec.N, B11_d=targets.B11_d
        )
        for chain_index, item in enumerate(specs):
            for coordinate in range(spec.d):
                run_rows.append(
                    _coordinate_row(
                        item,
                        estimator=estimator,
                        coordinate=coordinate,
                        bias=values[chain_index],
                        normalized=normalized[chain_index],
                        B11_d=targets.B11_d,
                        B20_FA=targets.B20_FA,
                    )
                )
    diagnostics = [
        {
            "study": "p3",
            "phase": "smoke",
            "setting_id": item.setting_id,
            "run_id": item.run_id,
            "seed": item.seed,
            "d": item.d,
            "H": item.H,
            "N": item.N,
            "gamma": item.gamma,
            "max_state_norm": max_state_norm[index],
            "batches_used": num_batches,
            "finite_state_pass": bool(finite[index]),
            "no_control_state": True,
            "stopping_status": "FIXED_SMOKE_BATCHES",
        }
        for index, item in enumerate(specs)
    ]
    return {
        "run_rows": run_rows,
        "batch_rows": batch_rows,
        "diagnostic_rows": diagnostics,
        "metadata": {
            "mixing_mu": mixing_mu,
            "mixing_scale": mixing_scale,
            "burn_in_rounds": burn_in_rounds,
            "batch_length": batch_length,
            "num_batches": num_batches,
            "S_C": targets.S_C,
            "B11_d": targets.B11_d,
            "B20_FA": targets.B20_FA,
        },
    }


def run_smoke(output_root: Path = P3_SMOKE_ARTIFACT_ROOT) -> dict[str, Any]:
    config = load_smoke_config()
    validation = check_smoke_protocol()
    environment = environment_manifest()
    outputs = simulate_smoke(config)
    write_csv(outputs["run_rows"], output_root / "run_summary.csv")
    write_csv(outputs["batch_rows"], output_root / "batch_summary.csv")
    write_csv(outputs["diagnostic_rows"], output_root / "diagnostic_summary.csv")
    metadata = outputs["metadata"]
    manifest = {
        "schema_version": 1,
        "capture_point": "before_any_p3_smoke_output_write",
        "study": "p3",
        "phase": "smoke",
        "environment": environment,
        "source_commit": environment["git_commit"],
        "source_dirty_at_run_start": environment["git_dirty"],
        "config_path": str(P3_SMOKE_CONFIG_PATH.relative_to(REPO_ROOT)),
        "config_sha256": hashlib.sha256(P3_SMOKE_CONFIG_PATH.read_bytes()).hexdigest(),
        "config_hash": config_hash(load_configs()["base"], config),
        "scientific_interpretation": "NOT_APPLICABLE_ENGINEERING_SMOKE",
        "validation": validation,
        "algorithm": {"name": "FedAvg", "control_state": False},
        "objective": config["objective"],
        "noise": config["noise"],
        "smoke": config["smoke"],
        "theory": {
            key: np.asarray(metadata[key]).tolist()
            for key in ("S_C", "B11_d", "B20_FA")
        },
        "rows": {
            "coordinate_runs": len(outputs["run_rows"]),
            "coordinate_batches": len(outputs["batch_rows"]),
            "chain_diagnostics": len(outputs["diagnostic_rows"]),
        },
        "artifacts": [
            "run_summary.csv",
            "batch_summary.csv",
            "diagnostic_summary.csv",
            "p3_smoke_manifest.json",
        ],
    }
    manifest_path = output_root / "p3_smoke_manifest.json"
    write_json(manifest, manifest_path)
    return {**outputs, "output_root": output_root, "manifest": manifest_path}
