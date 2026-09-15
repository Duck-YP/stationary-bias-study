"""Isolated fixed-gamma, large-N matched plateau experiment for P1."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Sequence

from ...core.io import P1_ARTIFACT_ROOT, P1_CONFIG_ROOT, load_yaml
from ...core.theory.one_dimensional import b20_total
from .simulation import P1RunSpec, _run_controlled_formal_matrix, _run_matrix
from .theory import b20_fedavg, delta_b20_scaffold_minus_fedavg


PLATEAU_CONFIG_PATH = P1_CONFIG_ROOT / "fixed_gamma_large_n.yaml"
PLATEAU_MATRIX_ID = "p1-fixed-gamma-large-n-h2-gamma-1over24"
PLATEAU_RESULT_ROOT = P1_ARTIFACT_ROOT / "formal" / PLATEAU_MATRIX_ID
PLATEAU_SMOKE_RESULT_ROOT = P1_ARTIFACT_ROOT / "smoke" / "fixed-gamma-large-n"
PLATEAU_CONFIG_SNAPSHOT = "fixed_gamma_large_n_config_snapshot.yaml"


def load_plateau_config() -> dict[str, Any]:
    return load_yaml(PLATEAU_CONFIG_PATH)


def build_plateau_run_matrix(
    config: dict[str, Any] | None = None, *, smoke: bool = False
) -> list[P1RunSpec]:
    config = config or load_plateau_config()
    if smoke:
        item = config["smoke_test"]
        return [
            P1RunSpec(
                grid_name="smoke",
                H=int(item["H"]),
                N=int(N),
                gamma=float(item["gamma"]),
                seed=int(seed),
                x0=float(item["initial_x"][int(seed)]),
            )
            for N in item["N_values"]
            for seed in item["seeds"]
        ]

    item = config["fixed_gamma_large_n"]
    gamma = 1.0 / int(item["gamma_denominator"])
    return [
        P1RunSpec(
            grid_name="fixed_gamma_large_n",
            H=int(item["H"]),
            N=int(N),
            gamma=gamma,
            seed=int(seed),
            x0=float(item["initial_x"][int(seed)]),
        )
        for N in item["N_values"]
        for seed in item["seeds"]
    ]


def audit_plateau_run_matrix(
    runs: Sequence[P1RunSpec] | None = None,
) -> dict[str, Any]:
    runs = list(runs or build_plateau_run_matrix())
    pair_ids = [run.pair_id for run in runs]
    settings = sorted({(run.H, run.N, run.gamma) for run in runs})
    return {
        "matrix_identifier": PLATEAU_MATRIX_ID,
        "total_pairs": len(runs),
        "settings": len(settings),
        "pairs_per_setting": sorted(
            sum(run.H == H and run.N == N and run.gamma == gamma for run in runs)
            for H, N, gamma in settings
        ),
        "H_values": sorted({run.H for run in runs}),
        "N_values": sorted({run.N for run in runs}),
        "gamma_values": sorted({run.gamma for run in runs}),
        "seeds": sorted({run.seed for run in runs}),
        "unique_pair_ids": len(set(pair_ids)),
        "all_unique": len(pair_ids) == len(set(pair_ids)),
    }


def expected_plateau_audit() -> dict[str, Any]:
    return {
        "matrix_identifier": PLATEAU_MATRIX_ID,
        "total_pairs": 40,
        "settings": 5,
        "pairs_per_setting": [8, 8, 8, 8, 8],
        "H_values": [2],
        "N_values": [8, 16, 32, 64, 128],
        "gamma_values": [1.0 / 24.0],
        "seeds": list(range(601, 609)),
        "unique_pair_ids": 40,
        "all_unique": True,
    }


def check_plateau_matrix() -> dict[str, Any]:
    config = load_plateau_config()
    if config["matrix_identifier"] != PLATEAU_MATRIX_ID:
        raise RuntimeError("Plateau config matrix identifier is not the stable ID")
    audit = audit_plateau_run_matrix()
    expected = expected_plateau_audit()
    if audit != expected:
        raise RuntimeError(f"P1 plateau matrix differs from its formal protocol: {audit}")
    theory = config["theory"]
    expected_theory = {
        "B20_fedavg": b20_fedavg(2),
        "B20_scaffold": b20_total(2),
        "Delta_B20_scaffold_minus_fedavg": delta_b20_scaffold_minus_fedavg(2),
    }
    for key, value in expected_theory.items():
        if float(theory[key]) != value:
            raise RuntimeError(f"P1 plateau theory constant {key} changed")
    return audit


def _save_config_snapshot(output_root: Path) -> Path:
    destination = output_root / PLATEAU_CONFIG_SNAPSHOT
    shutil.copyfile(PLATEAU_CONFIG_PATH, destination)
    return destination


def run_plateau_experiment() -> dict[str, Any]:
    check_plateau_matrix()
    config = load_plateau_config()

    def finalize(output_root: Path) -> dict[str, Any]:
        _save_config_snapshot(output_root)
        from .plateau_analysis import build_plateau_outputs

        return build_plateau_outputs(output_root)

    return _run_controlled_formal_matrix(
        build_plateau_run_matrix(config),
        target_root=PLATEAU_RESULT_ROOT,
        config=config,
        config_path=PLATEAU_CONFIG_PATH,
        matrix_audit=audit_plateau_run_matrix,
        finalize=finalize,
    )


def run_plateau_smoke() -> dict[str, Any]:
    config = load_plateau_config()
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
        build_plateau_run_matrix(config, smoke=True),
        output_root=PLATEAU_SMOKE_RESULT_ROOT,
        protocol_override=override,
        config=config,
        config_path=PLATEAU_CONFIG_PATH,
        matrix_audit=audit_plateau_run_matrix,
    )
    outputs["config_snapshot"] = _save_config_snapshot(PLATEAU_SMOKE_RESULT_ROOT)
    from .plateau_analysis import build_plateau_outputs

    outputs["analysis"] = build_plateau_outputs(PLATEAU_SMOKE_RESULT_ROOT)
    return outputs
