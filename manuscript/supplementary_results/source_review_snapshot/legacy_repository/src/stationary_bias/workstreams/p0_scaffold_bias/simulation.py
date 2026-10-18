"""Frozen run matrix and execution engine for the publication baseline."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from ...core.algorithms.scaffold import generate_noise_block, scaffold_round_many
from ...core.inference.statistics import (
    balance_round_value,
    standard_error,
    student_t_summary,
)
from ...core.inference.validation import (
    all_finite,
    estimator_agreement,
    precision_threshold,
    stationarity_check,
)
from ...core.io import (
    EXPERIMENT_CONFIG_FILES,
    P0_SMOKE_ARTIFACT_ROOT,
    SHARED_CONFIG_ROOT,
    config_hash,
    experiment_result_root,
    git_commit,
    load_configs,
    make_run_key,
    write_csv,
)
from ...core.models.noise import noise_variance
from ...core.models.objectives import get_objective
from ...core.theory.one_dimensional import (
    b20_control,
    b20_local,
    b20_total,
    normalize_bias,
)


@dataclass(frozen=True)
class RunSpec:
    experiment: str
    control_name: str
    objective: str
    noise: str
    H: int
    N: int
    gamma: float
    seed: int
    x0: float

    @property
    def setting_key(self) -> tuple[Any, ...]:
        return (
            self.experiment,
            self.control_name,
            self.objective,
            self.noise,
            self.H,
            self.N,
            self.gamma,
        )

    @property
    def run_key(self) -> str:
        return make_run_key(
            experiment=self.experiment,
            control_name=self.control_name,
            objective=self.objective,
            noise=self.noise,
            H=self.H,
            N=self.N,
            gamma=self.gamma,
            seed=self.seed,
        )


def _seed_specs(
    base: dict[str, Any],
    *,
    experiment: str,
    control_name: str = "",
    objective: str,
    noise: str,
    H: int,
    N: int,
    gamma: float,
) -> list[RunSpec]:
    seeds = base["chains"]["seeds"]
    initial_x = base["chains"]["initial_x"]
    return [
        RunSpec(
            experiment=experiment,
            control_name=control_name,
            objective=objective,
            noise=noise,
            H=int(H),
            N=int(N),
            gamma=float(gamma),
            seed=int(seed),
            x0=float(initial_x[int(seed)]),
        )
        for seed in seeds
    ]


def build_run_matrix(configs: dict[str, dict[str, Any]] | None = None) -> list[RunSpec]:
    configs = configs or load_configs()
    base = configs["base"]
    runs: list[RunSpec] = []

    convergence = configs["coefficient_convergence"]
    for H in convergence["H_values"]:
        for point in convergence["path"]:
            runs.extend(
                _seed_specs(
                    base,
                    experiment="coefficient_convergence",
                    objective=convergence["objective"],
                    noise=convergence["noise"],
                    H=H,
                    N=point["N"],
                    gamma=1.0 / point["gamma_denominator"],
                )
            )

    scaling = configs["client_count_scaling"]
    for N in scaling["N_values"]:
        runs.extend(
            _seed_specs(
                base,
                experiment="client_count_scaling",
                objective=scaling["objective"],
                noise=scaling["noise"],
                H=scaling["H"],
                N=N,
                gamma=1.0 / scaling["gamma_denominator"],
            )
        )

    controls = configs["negative_controls"]
    for control in controls["controls"]:
        if "settings" not in control:
            continue
        for point in control["settings"]:
            runs.extend(
                _seed_specs(
                    base,
                    experiment="negative_controls",
                    control_name=control["name"],
                    objective=control["objective"],
                    noise=control["noise"],
                    H=control["H"],
                    N=point["N"],
                    gamma=1.0 / point["gamma_denominator"],
                )
            )
    return runs


def matrix_audit(runs: Sequence[RunSpec]) -> dict[str, Any]:
    keys = [run.run_key for run in runs]
    controls: dict[str, int] = {}
    for run in runs:
        if run.control_name:
            controls[run.control_name] = controls.get(run.control_name, 0) + 1
    counts = {
        "coefficient_convergence": sum(
            run.experiment == "coefficient_convergence" for run in runs
        ),
        "client_count_scaling": sum(
            run.experiment == "client_count_scaling" for run in runs
        ),
        "negative_controls": sum(
            run.experiment == "negative_controls" for run in runs
        ),
        "total": len(runs),
    }
    return {
        **counts,
        "controls": controls,
        "unique_run_keys": len(set(keys)),
        "all_unique": len(set(keys)) == len(keys),
    }


def assert_formal_configs_available() -> None:
    """Validate the explicit protocol files without counting unrelated YAML files."""

    required = [
        SHARED_CONFIG_ROOT / "simulation_defaults.yaml",
        *EXPERIMENT_CONFIG_FILES.values(),
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing required configuration files: {missing}")
    load_configs()


def _advance_block(
    x: np.ndarray,
    xi: np.ndarray,
    rngs: Sequence[np.random.Generator],
    *,
    rounds: int,
    gamma: float,
    H: int,
    N: int,
    objective_name: str,
    noise_name: str,
    collect: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    objective = get_objective(objective_name)
    noises = generate_noise_block(rngs, noise_name, rounds=rounds, H=H, N=N)
    chains = x.size
    sums = {
        "x": np.zeros(chains),
        "z": np.zeros(chains),
        "control_second": np.zeros(chains),
        "x2": np.zeros(chains),
        "x3": np.zeros(chains),
        "x4": np.zeros(chains),
    }
    maxima = {
        "control_sum": np.zeros(chains),
        "abs_x": np.abs(x).copy(),
    }
    finite = np.ones(chains, dtype=bool)

    for round_index in range(rounds):
        x_start = x.copy()
        result = scaffold_round_many(
            x,
            xi,
            gamma=gamma,
            H=H,
            objective=objective,
            epsilon_steps=noises[:, round_index, :, :],
        )
        z = np.asarray(balance_round_value(result.qbar, gamma=gamma, a=objective.a))
        chain_finite = (
            np.isfinite(result.x_new)
            & np.all(np.isfinite(result.xi_new), axis=1)
            & np.all(np.isfinite(result.qbar), axis=1)
            & np.isfinite(z)
        )
        finite &= chain_finite
        maxima["control_sum"] = np.maximum(maxima["control_sum"], result.abs_control_sum)
        maxima["abs_x"] = np.maximum(maxima["abs_x"], np.abs(result.x_new))
        if collect:
            sums["x"] += x_start
            sums["z"] += z
            sums["control_second"] += np.mean(result.xi_new * result.xi_new, axis=1)
            sums["x2"] += x_start**2
            sums["x3"] += x_start**3
            sums["x4"] += x_start**4
        x, xi = result.x_new, result.xi_new
        if not np.all(chain_finite):
            break

    stats = {
        **{name: values / rounds for name, values in sums.items()},
        "max_control_sum": maxima["control_sum"],
        "max_abs_x": maxima["abs_x"],
        "finite": finite,
    }
    return x, xi, stats


def simulate_setting(
    specs: Sequence[RunSpec],
    base: dict[str, Any],
    experiment_config: dict[str, Any],
    *,
    protocol_override: dict[str, int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Simulate all independent chains in one setting under a joint stop rule."""

    if not specs or any(spec.setting_key != specs[0].setting_key for spec in specs):
        raise ValueError("simulate_setting requires one non-empty setting")
    spec = specs[0]
    objective = get_objective(spec.objective)
    sigma2 = noise_variance(spec.noise)
    protocol = base["protocol"].copy()
    if protocol_override:
        protocol.update(protocol_override)

    mixing_scale = math.ceil(1.0 / (objective.mu * spec.H * spec.gamma))
    burn_in_rounds = int(
        protocol.get("burn_in_rounds", protocol["burn_in_multiples"] * mixing_scale)
    )
    if "batch_length" in protocol:
        batch_length = int(protocol["batch_length"])
    else:
        batch_length = int(protocol["batch_length_multiples"] * mixing_scale)
    min_batches = int(protocol["min_batches"])
    max_batches = int(protocol["max_batches"])
    extension_batches = int(protocol["extension_batches"])

    x = np.array([item.x0 for item in specs], dtype=np.float64)
    xi = np.zeros((len(specs), spec.N), dtype=np.float64)
    rngs = [np.random.default_rng(item.seed) for item in specs]
    max_control_sum = np.zeros(len(specs))
    finite_flags = np.ones(len(specs), dtype=bool)

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
            objective_name=spec.objective,
            noise_name=spec.noise,
            collect=False,
        )
        max_control_sum = np.maximum(max_control_sum, stats["max_control_sum"])
        finite_flags &= stats["finite"]
        remaining -= block_rounds
        if not np.all(finite_flags):
            break

    batch_rows: list[dict[str, Any]] = []
    batch_direct: list[np.ndarray] = []
    batch_balance: list[np.ndarray] = []
    last_batch_max_abs_x = np.full(len(specs), np.nan)
    B_total = b20_total(spec.H, a=objective.a, tau=objective.tau, sigma2=sigma2)
    B_local = b20_local(spec.H, a=objective.a, tau=objective.tau, sigma2=sigma2)
    B_ctrl = b20_control(spec.H, a=objective.a, tau=objective.tau, sigma2=sigma2)
    target_batches = min_batches
    precision_reached = False

    while np.all(finite_flags) and len(batch_direct) < max_batches:
        while len(batch_direct) < target_batches:
            batch_index = len(batch_direct)
            x, xi, stats = _advance_block(
                x,
                xi,
                rngs,
                rounds=batch_length,
                gamma=spec.gamma,
                H=spec.H,
                N=spec.N,
                objective_name=spec.objective,
                noise_name=spec.noise,
                collect=True,
            )
            batch_direct.append(stats["x"].copy())
            batch_balance.append(stats["z"].copy())
            max_control_sum = np.maximum(max_control_sum, stats["max_control_sum"])
            finite_flags &= stats["finite"]
            last_batch_max_abs_x = stats["max_abs_x"].copy()
            for chain_index, item in enumerate(specs):
                batch_rows.append(
                    {
                        "run_key": item.run_key,
                        "batch_index": batch_index,
                        "round_start": burn_in_rounds + batch_index * batch_length,
                        "round_end": burn_in_rounds + (batch_index + 1) * batch_length,
                        "mean_x": stats["x"][chain_index],
                        "mean_b_balance_round": stats["z"][chain_index],
                        "mean_control_second_moment": stats["control_second"][chain_index],
                        "max_abs_control_sum": stats["max_control_sum"][chain_index],
                        "mean_x2": stats["x2"][chain_index],
                        "mean_x3": stats["x3"][chain_index],
                        "mean_x4": stats["x4"][chain_index],
                        "max_abs_x": stats["max_abs_x"][chain_index],
                    }
                )
            if not np.all(finite_flags):
                break

        direct_array = np.stack(batch_direct) if batch_direct else np.empty((0, len(specs)))
        balance_array = np.stack(batch_balance) if batch_balance else np.empty((0, len(specs)))
        if direct_array.size:
            chain_balance = np.mean(balance_array, axis=0)
            chain_C = np.asarray(
                normalize_bias(
                    chain_balance,
                    gamma=spec.gamma,
                    N=spec.N,
                    a=objective.a,
                    tau=objective.tau,
                    sigma2=sigma2,
                )
            )
            C_summary = student_t_summary(chain_C)
            half_width = (C_summary.ci_high - C_summary.ci_low) / 2.0
            threshold = precision_threshold(
                B_total,
                absolute=float(base["thresholds"]["coefficient_ci_abs"]),
                relative=float(base["thresholds"]["coefficient_ci_relative"]),
            )
            precision_reached = bool(np.all(finite_flags) and half_width <= threshold)
        if precision_reached or target_batches >= max_batches or not np.all(finite_flags):
            break
        target_batches = min(max_batches, target_batches + extension_batches)

    direct_array = np.stack(batch_direct) if batch_direct else np.empty((0, len(specs)))
    balance_array = np.stack(batch_balance) if batch_balance else np.empty((0, len(specs)))
    run_rows: list[dict[str, Any]] = []
    commit = git_commit()
    cfg_hash = config_hash(base, experiment_config)
    for chain_index, item in enumerate(specs):
        direct_batches = direct_array[:, chain_index]
        balance_batches = balance_array[:, chain_index]
        b_direct = float(np.mean(direct_batches)) if direct_batches.size else float("nan")
        b_balance = float(np.mean(balance_batches)) if balance_batches.size else float("nan")
        se_direct = standard_error(direct_batches)
        se_balance = standard_error(balance_batches)
        C_direct = float(
            normalize_bias(
                b_direct,
                gamma=spec.gamma,
                N=spec.N,
                a=objective.a,
                tau=objective.tau,
                sigma2=sigma2,
            )
        )
        C_balance = float(
            normalize_bias(
                b_balance,
                gamma=spec.gamma,
                N=spec.N,
                a=objective.a,
                tau=objective.tau,
                sigma2=sigma2,
            )
        )
        stationarity = stationarity_check(
            balance_batches, z=float(base["thresholds"]["stationarity_z"])
        )
        agreement = estimator_agreement(
            b_direct,
            b_balance,
            se_direct,
            se_balance,
            z=float(base["thresholds"]["estimator_agreement_z"]),
        )
        run_rows.append(
            {
                "phase": "formal" if item.experiment != "smoke" else "smoke",
                "experiment": item.experiment,
                "control_name": item.control_name,
                "objective": item.objective,
                "noise": item.noise,
                "H": item.H,
                "N": item.N,
                "gamma": item.gamma,
                "seed": item.seed,
                "x0": item.x0,
                "num_clients": item.N,
                "mixing_scale": mixing_scale,
                "burn_in_rounds": burn_in_rounds,
                "batch_length": batch_length,
                "num_batches": direct_array.shape[0],
                "post_burn_rounds": direct_array.shape[0] * batch_length,
                "a": objective.a,
                "tau": objective.tau,
                "sigma2": sigma2,
                "mu": objective.mu,
                "L": objective.L,
                "b_direct": b_direct,
                "se_direct": se_direct,
                "b_balance": b_balance,
                "se_balance": se_balance,
                "C_direct": C_direct,
                "C_balance": C_balance,
                "B_theory": B_total,
                "B_local_theory": B_local,
                "B_ctrl_theory": B_ctrl,
                "C_minus_B": C_balance - B_total,
                "control_sum_max_abs": max_control_sum[chain_index],
                "stationarity_pass": stationarity.passed,
                "stationarity_first_half_mean": stationarity.first_half_mean,
                "stationarity_second_half_mean": stationarity.second_half_mean,
                "stationarity_first_half_se": stationarity.first_half_se,
                "stationarity_second_half_se": stationarity.second_half_se,
                "estimator_agreement_pass": agreement,
                "precision_reached": precision_reached,
                "finite_state_pass": bool(finite_flags[chain_index]),
                "last_batch_max_abs_x": last_batch_max_abs_x[chain_index],
                "git_commit": commit,
                "config_hash": cfg_hash,
                "run_key": item.run_key,
            }
        )
    return run_rows, batch_rows


def _group_settings(runs: Iterable[RunSpec]) -> list[list[RunSpec]]:
    groups: dict[tuple[Any, ...], list[RunSpec]] = {}
    for run in runs:
        groups.setdefault(run.setting_key, []).append(run)
    return list(groups.values())


def run_experiment(experiment: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if experiment not in EXPERIMENT_CONFIG_FILES:
        raise ValueError(f"Unknown baseline experiment: {experiment}")
    assert_formal_configs_available()
    configs = load_configs()
    runs = [run for run in build_run_matrix(configs) if run.experiment == experiment]
    all_run_rows: list[dict[str, Any]] = []
    all_batch_rows: list[dict[str, Any]] = []
    output_dir = experiment_result_root(experiment)
    display_name = output_dir.name
    for index, setting in enumerate(_group_settings(runs), start=1):
        sample = setting[0]
        print(
            f"[{display_name}] setting {index}/{len(_group_settings(runs))}: "
            f"control={sample.control_name or '-'} H={sample.H} N={sample.N} gamma={sample.gamma:.10g}",
            flush=True,
        )
        run_rows, batch_rows = simulate_setting(
            setting, configs["base"], configs[experiment]
        )
        all_run_rows.extend(run_rows)
        all_batch_rows.extend(batch_rows)
        write_csv(all_run_rows, output_dir / "run_summary.csv")
        write_csv(all_batch_rows, output_dir / "batch_summary.csv")
        print(
            f"[{display_name}] completed with {run_rows[0]['num_batches']} batches; "
            f"precision_reached={run_rows[0]['precision_reached']}",
            flush=True,
        )
    return all_run_rows, all_batch_rows


def run_smoke() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    configs = load_configs()
    smoke = configs["base"]["smoke_test"]
    spec = RunSpec(
        experiment="smoke",
        control_name="",
        objective=smoke["objective"],
        noise=smoke["noise"],
        H=int(smoke["H"]),
        N=int(smoke["N"]),
        gamma=float(smoke["gamma"]),
        seed=int(smoke["seed"]),
        x0=float(smoke["x0"]),
    )
    num_batches = int(smoke["num_batches"])
    batch_length = int(smoke["post_burn_rounds"] // num_batches)
    override = {
        "burn_in_rounds": int(smoke["burn_in_rounds"]),
        "batch_length": batch_length,
        "min_batches": num_batches,
        "max_batches": num_batches,
        "extension_batches": num_batches,
    }
    run_rows, batch_rows = simulate_setting(
        [spec], configs["base"], {"experiment": "smoke", **smoke}, protocol_override=override
    )
    output_dir = P0_SMOKE_ARTIFACT_ROOT
    write_csv(run_rows, output_dir / "run_summary.csv")
    write_csv(batch_rows, output_dir / "batch_summary.csv")
    return run_rows, batch_rows
