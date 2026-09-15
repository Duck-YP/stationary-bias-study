"""One controlled d=2 engineering smoke run for P2."""

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
from .algorithm import scaffold_round_many_vector
from .inference import vector_balance_round_value
from .noise import CONTROLLED_COVARIANCE, generate_vector_noise_block
from .objective import (
    CONTROLLED_A,
    CONTROLLED_ALPHA,
    CONTROLLED_U,
    RankOneVectorObjective,
)
from .theory import normalize_vector_bias, vector_theory_targets


P2_ROOT = REPO_ROOT / "workstreams" / "p2_multidimensional_validation"
P2_CONFIG_PATH = P2_ROOT / "configs" / "d2_smoke.yaml"
P2_SMOKE_ARTIFACT_ROOT = P2_ROOT / "artifacts" / "smoke"


@dataclass(frozen=True)
class P2SmokeSpec:
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
            f"p2__setting-{self.setting_id}__d{self.d}__H{self.H}__N{self.N}"
            f"__g{gamma_token(self.gamma)}__seed{self.seed}"
        )


def load_p2_config() -> dict[str, Any]:
    return load_yaml(P2_CONFIG_PATH)


def objective_from_config(config: dict[str, Any]) -> RankOneVectorObjective:
    model = config["objective"]
    return RankOneVectorObjective(
        np.asarray(model["A"], dtype=np.float64),
        np.asarray(model["u"], dtype=np.float64),
        float(model["alpha"]),
    )


def covariance_from_config(config: dict[str, Any]) -> np.ndarray:
    return np.asarray(config["noise"]["covariance"], dtype=np.float64)


def build_smoke_specs(config: dict[str, Any] | None = None) -> list[P2SmokeSpec]:
    config = config or load_p2_config()
    smoke = config["smoke"]
    d = int(smoke["d"])
    return [
        P2SmokeSpec(
            setting_id=str(config["setting_id"]),
            d=d,
            H=int(smoke["H"]),
            N=int(smoke["N"]),
            gamma=float(smoke["gamma"]),
            seed=int(seed),
            x0=np.asarray(smoke["initial_x"][int(seed)], dtype=np.float64),
        )
        for seed in smoke["seeds"]
    ]


def check_p2() -> dict[str, Any]:
    config = load_p2_config()
    objective = objective_from_config(config)
    covariance = covariance_from_config(config)
    specs = build_smoke_specs(config)
    smoke = config["smoke"]
    if objective.dimension != 2 or not np.array_equal(objective.A, CONTROLLED_A):
        raise RuntimeError("P2 smoke objective matrix differs from the controlled d=2 matrix")
    if not np.array_equal(objective.u, CONTROLLED_U):
        raise RuntimeError("P2 smoke objective direction differs from the controlled direction")
    if objective.alpha != CONTROLLED_ALPHA:
        raise RuntimeError("P2 smoke objective alpha differs from the controlled value")
    if not np.array_equal(covariance, CONTROLLED_COVARIANCE):
        raise RuntimeError("P2 smoke covariance differs from the controlled covariance")
    if int(smoke["d"]) != 2 or int(smoke["H"]) != 2:
        raise RuntimeError("P2 smoke must use d=2 and H=2")
    if any(item.x0.shape != (2,) for item in specs):
        raise RuntimeError("Every P2 initial state must have shape [d]")
    if len({item.seed for item in specs}) != len(specs):
        raise RuntimeError("P2 smoke seeds must be unique")
    targets = vector_theory_targets(objective, covariance, specs[0].H)
    residual = float(
        np.linalg.norm(objective.A @ targets.S_C + targets.S_C @ objective.A - covariance)
    )
    if residual > 1.0e-12:
        raise RuntimeError("P2 Lyapunov solution failed its residual check")
    return {
        "status": "PASS",
        "workstream": "p2",
        "phase": "smoke",
        "setting_id": str(config["setting_id"]),
        "d": 2,
        "H": 2,
        "N": int(smoke["N"]),
        "gamma": float(smoke["gamma"]),
        "seeds": [item.seed for item in specs],
        "chains": len(specs),
        "batches": int(smoke["protocol"]["num_batches"]),
        "lyapunov_residual": residual,
    }


def _advance_block(
    x: np.ndarray,
    xi: np.ndarray,
    rngs: Sequence[np.random.Generator],
    *,
    rounds: int,
    gamma: float,
    H: int,
    N: int,
    objective: RankOneVectorObjective,
    covariance: np.ndarray,
    collect: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    noises = generate_vector_noise_block(
        rngs, covariance, rounds=rounds, H=H, N=N
    )
    chains, dimension = x.shape
    direct_sum = np.zeros((chains, dimension), dtype=np.float64)
    balance_sum = np.zeros((chains, dimension), dtype=np.float64)
    max_control_sum = np.zeros(chains, dtype=np.float64)
    max_state_norm = np.linalg.norm(x, axis=1)
    finite = np.ones(chains, dtype=bool)
    for round_index in range(rounds):
        x_start = x.copy()
        result = scaffold_round_many_vector(
            x,
            xi,
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
            & np.all(np.isfinite(result.xi_new), axis=(1, 2))
            & np.all(np.isfinite(result.qbar), axis=(1, 2))
            & np.all(np.isfinite(balance), axis=1)
        )
        finite &= chain_finite
        max_control_sum = np.maximum(
            max_control_sum, result.max_abs_control_sum
        )
        max_state_norm = np.maximum(
            max_state_norm, np.linalg.norm(result.x_new, axis=1)
        )
        if collect:
            direct_sum += x_start
            balance_sum += balance
        x, xi = result.x_new, result.xi_new
        if not np.all(chain_finite):
            break
    return x, xi, {
        "direct": direct_sum / rounds,
        "balance": balance_sum / rounds,
        "max_control_sum": max_control_sum,
        "max_state_norm": max_state_norm,
        "finite": finite,
    }


def simulate_p2_smoke(
    config: dict[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]] | dict[str, Any]]:
    config = config or load_p2_config()
    check_p2()
    specs = build_smoke_specs(config)
    spec = specs[0]
    objective = objective_from_config(config)
    covariance = covariance_from_config(config)
    targets = vector_theory_targets(objective, covariance, spec.H)
    protocol = config["smoke"]["protocol"]
    mixing_mu = float(np.min(np.linalg.eigvalsh(objective.A)))
    mixing_scale = math.ceil(1.0 / (mixing_mu * spec.H * spec.gamma))
    burn_in_rounds = int(protocol["burn_in_multiples"]) * mixing_scale
    batch_length = int(protocol["batch_length_multiples"]) * mixing_scale
    num_batches = int(protocol["num_batches"])

    x = np.stack([item.x0 for item in specs])
    xi = np.zeros((len(specs), spec.N, spec.d), dtype=np.float64)
    rngs = [np.random.default_rng(item.seed) for item in specs]
    max_control_sum = np.zeros(len(specs), dtype=np.float64)
    max_state_norm = np.linalg.norm(x, axis=1)
    finite = np.ones(len(specs), dtype=bool)

    remaining = burn_in_rounds
    while remaining:
        block_rounds = min(batch_length, remaining)
        x, xi, stats = _advance_block(
            x,
            xi,
            rngs,
            rounds=block_rounds,
            gamma=spec.gamma,
            H=spec.H,
            N=spec.N,
            objective=objective,
            covariance=covariance,
            collect=False,
        )
        max_control_sum = np.maximum(max_control_sum, stats["max_control_sum"])
        max_state_norm = np.maximum(max_state_norm, stats["max_state_norm"])
        finite &= stats["finite"].astype(bool)
        remaining -= block_rounds

    direct_batches: list[np.ndarray] = []
    balance_batches: list[np.ndarray] = []
    batch_rows: list[dict[str, Any]] = []
    for batch_index in range(num_batches):
        x, xi, stats = _advance_block(
            x,
            xi,
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
        max_control_sum = np.maximum(max_control_sum, stats["max_control_sum"])
        max_state_norm = np.maximum(max_state_norm, stats["max_state_norm"])
        finite &= stats["finite"].astype(bool)
        for estimator, values in (
            ("direct_sample_mean", stats["direct"]),
            ("stationary_mean_balance", stats["balance"]),
        ):
            normalized = normalize_vector_bias(
                values, gamma=spec.gamma, N=spec.N, B10=targets.B10
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
                            B10=targets.B10,
                            B20=targets.B20,
                            batch_index=batch_index,
                        )
                    )

    direct = np.mean(np.stack(direct_batches), axis=0)
    balance = np.mean(np.stack(balance_batches), axis=0)
    run_rows: list[dict[str, Any]] = []
    normalized_by_estimator: dict[str, np.ndarray] = {}
    for estimator, values in (
        ("direct_sample_mean", direct),
        ("stationary_mean_balance", balance),
    ):
        normalized = normalize_vector_bias(
            values, gamma=spec.gamma, N=spec.N, B10=targets.B10
        )
        normalized_by_estimator[estimator] = normalized
        for chain_index, item in enumerate(specs):
            for coordinate in range(spec.d):
                run_rows.append(
                    _coordinate_row(
                        item,
                        estimator=estimator,
                        coordinate=coordinate,
                        bias=values[chain_index],
                        normalized=normalized[chain_index],
                        B10=targets.B10,
                        B20=targets.B20,
                    )
                )

    diagnostics: list[dict[str, Any]] = []
    balance_normalized = normalized_by_estimator["stationary_mean_balance"]
    for chain_index, item in enumerate(specs):
        error = balance_normalized[chain_index] - targets.B20
        diagnostics.append(
            {
                "study": "p2_multidimensional_validation",
                "phase": "smoke",
                "setting_id": item.setting_id,
                "run_id": item.run_id,
                "seed": item.seed,
                "d": item.d,
                "H": item.H,
                "N": item.N,
                "gamma": item.gamma,
                "normalized_error_l2": float(np.linalg.norm(error)),
                "normalized_error_linf": float(np.max(np.abs(error))),
                "direct_balance_difference_l2": float(
                    np.linalg.norm(direct[chain_index] - balance[chain_index])
                ),
                "zero_sum_control_error": max_control_sum[chain_index],
                "max_state_norm": max_state_norm[chain_index],
                "batches_used": num_batches,
                "stopping_status": "FIXED_SMOKE_BATCHES",
                "finite_state_pass": bool(finite[chain_index]),
            }
        )
    metadata = {
        "mixing_mu": mixing_mu,
        "mixing_scale": mixing_scale,
        "burn_in_rounds": burn_in_rounds,
        "batch_length": batch_length,
        "num_batches": num_batches,
        "S_C": targets.S_C,
        "B10": targets.B10,
        "B20": targets.B20,
        "B20_local": targets.B20_local,
        "B20_ctrl": targets.B20_ctrl,
    }
    return {
        "run_rows": run_rows,
        "batch_rows": batch_rows,
        "diagnostic_rows": diagnostics,
        "metadata": metadata,
    }


def _coordinate_row(
    spec: P2SmokeSpec,
    *,
    estimator: str,
    coordinate: int,
    bias: np.ndarray,
    normalized: np.ndarray,
    B10: np.ndarray,
    B20: np.ndarray,
    batch_index: int | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "study": "p2_multidimensional_validation",
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
        "B10_component": B10[coordinate],
        "C_component": normalized[coordinate],
        "B20_component": B20[coordinate],
        "normalized_error_component": normalized[coordinate] - B20[coordinate],
    }
    if batch_index is not None:
        row["batch_index"] = batch_index
    return row


def run_p2_smoke(output_root: Path = P2_SMOKE_ARTIFACT_ROOT) -> dict[str, Any]:
    config = load_p2_config()
    validation = check_p2()
    environment = environment_manifest()
    base = load_configs()["base"]
    provenance = {
        "schema_version": 1,
        "capture_point": "before_any_p2_output_write",
        "environment": environment,
        "git_commit": environment["git_commit"],
        "source_git_dirty_at_run_start": environment["git_dirty"],
        "config_path": str(P2_CONFIG_PATH),
        "config_sha256": hashlib.sha256(P2_CONFIG_PATH.read_bytes()).hexdigest(),
        "config_hash": config_hash(base, config),
        "setting_id": str(config["setting_id"]),
        "phase": "smoke",
        "seeds": list(config["smoke"]["seeds"]),
    }
    outputs = simulate_p2_smoke(config)
    write_csv(outputs["run_rows"], output_root / "run_summary.csv")
    write_csv(outputs["batch_rows"], output_root / "batch_summary.csv")
    write_csv(outputs["diagnostic_rows"], output_root / "diagnostic_summary.csv")
    metadata = outputs["metadata"]
    manifest = {
        **provenance,
        "study": "p2-multidimensional-validation",
        "scientific_interpretation": "NOT_APPLICABLE_ENGINEERING_SMOKE",
        "validation": validation,
        "smoke": config["smoke"],
        "objective": config["objective"],
        "noise": config["noise"],
        "protocol": {
            "mixing_mu": metadata["mixing_mu"],
            "mixing_scale": metadata["mixing_scale"],
            "burn_in_rounds": metadata["burn_in_rounds"],
            "batch_length": metadata["batch_length"],
            "num_batches": metadata["num_batches"],
            "stopping_status": "FIXED_SMOKE_BATCHES",
        },
        "theory": {
            key: np.asarray(metadata[key]).tolist()
            for key in ("S_C", "B10", "B20", "B20_local", "B20_ctrl")
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
            "p2_smoke_manifest.json",
        ],
    }
    manifest_path = output_root / "p2_smoke_manifest.json"
    write_json(manifest, manifest_path)
    return {
        **outputs,
        "output_root": output_root,
        "manifest": manifest_path,
    }
