"""Frozen d=2 fixed-gamma, large-N plateau experiment for P2."""

from __future__ import annotations

import hashlib
import shutil
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
from ...core.io import (
    REPO_ROOT,
    environment_manifest,
    gamma_token,
    load_yaml,
    write_csv,
    write_json,
)
from .formal import (
    P2_ROW_PROVENANCE_FIELDS,
    P2_RUN_START_PROVENANCE,
    FormalRunSpec,
    load_formal_config,
    objective_from_formal_config,
    covariance_from_formal_config,
    simulate_formal_setting,
)
from .theory import vector_theory_targets


P2_PLATEAU_MATRIX_ID = "p2-d2-fixed-gamma-largeN-plateau"
P2_PLATEAU_ROOT = REPO_ROOT / "workstreams" / "p2_multidimensional_validation"
P2_PLATEAU_CONFIG_PATH = (
    P2_PLATEAU_ROOT / "configs" / "d2_fixed_gamma_largeN_plateau.yaml"
)
P2_PLATEAU_PROTOCOL_PATH = (
    P2_PLATEAU_ROOT / "d2_fixed_gamma_largeN_plateau_protocol.md"
)
P2_PLATEAU_MANIFEST = "plateau_manifest.json"
P2_PLATEAU_RAW_RESULT_FILES = ("run_summary.csv", "batch_summary.csv")


def load_plateau_config() -> dict[str, Any]:
    return load_yaml(P2_PLATEAU_CONFIG_PATH)


def plateau_artifact_root(config: dict[str, Any] | None = None) -> Path:
    config = config or load_plateau_config()
    return REPO_ROOT / str(config["artifact_namespace"])


def build_plateau_run_matrix(
    config: dict[str, Any] | None = None,
) -> list[FormalRunSpec]:
    config = config or load_plateau_config()
    matrix = config["fixed_gamma_large_N"]
    gamma = 1.0 / int(matrix["gamma_denominator"])
    H = int(matrix["H"])
    d = int(matrix["d"])
    x0 = np.asarray(config["objective"]["x_star"], dtype=np.float64)
    matrix_id = str(config["matrix_identifier"])
    return [
        FormalRunSpec(
            matrix_id=matrix_id,
            target="plateau",
            setting_id=(
                f"{matrix_id}__H{H}__N{int(N)}__g{gamma_token(gamma)}"
            ),
            d=d,
            H=H,
            N=int(N),
            gamma=gamma,
            delta=gamma + 1.0 / int(N),
            seed=int(seed),
            x0=x0.copy(),
        )
        for N in matrix["N_values"]
        for seed in config["chains"]["seeds"]
    ]


def audit_plateau_run_matrix(
    runs: Sequence[FormalRunSpec] | None = None,
) -> dict[str, Any]:
    runs = list(runs or build_plateau_run_matrix())
    run_ids = [item.run_id for item in runs]
    settings = sorted({item.setting_key for item in runs})
    gamma_values = sorted({item.gamma for item in runs})
    return {
        "matrix_id": runs[0].matrix_id if runs else "",
        "settings": len(settings),
        "chains": len(runs),
        "chains_per_setting": sorted(
            sum(item.setting_key == setting for item in runs) for setting in settings
        ),
        "d_values": sorted({item.d for item in runs}),
        "H_values": sorted({item.H for item in runs}),
        "N_values": sorted({item.N for item in runs}),
        "gamma_values": gamma_values,
        "gamma_fixed": len(gamma_values) == 1,
        "seeds": sorted({item.seed for item in runs}),
        "unique_run_ids": len(set(run_ids)),
        "all_unique": len(run_ids) == len(set(run_ids)),
    }


def expected_plateau_audit() -> dict[str, Any]:
    return {
        "matrix_id": P2_PLATEAU_MATRIX_ID,
        "settings": 5,
        "chains": 40,
        "chains_per_setting": [8, 8, 8, 8, 8],
        "d_values": [2],
        "H_values": [2],
        "N_values": [8, 16, 32, 64, 128],
        "gamma_values": [1.0 / 24.0],
        "gamma_fixed": True,
        "seeds": list(range(1301, 1309)),
        "unique_run_ids": 40,
        "all_unique": True,
    }


def check_plateau_protocol() -> dict[str, Any]:
    """Verify that the new matrix reuses P2 d=2 science and changes only N."""

    config = load_plateau_config()
    primary = load_formal_config("primary")
    if config["matrix_identifier"] != P2_PLATEAU_MATRIX_ID:
        raise RuntimeError("P2 plateau matrix identifier changed")
    audit = audit_plateau_run_matrix()
    if audit != expected_plateau_audit():
        raise RuntimeError(f"P2 plateau matrix differs from its frozen protocol: {audit}")
    for key in ("objective", "noise", "protocol", "per_setting_uncertainty", "precision_stopping"):
        if config[key] != primary[key]:
            raise RuntimeError(f"P2 plateau does not reuse the primary d=2 {key}")

    targets = vector_theory_targets(
        objective_from_formal_config(config), covariance_from_formal_config(config), 2
    )
    theory = config["theory"]
    expected_theory = {
        "S_C": targets.S_C,
        "B10": targets.B10,
        "B20.value": targets.B20,
        "B20.local": targets.B20_local,
        "B20.control": targets.B20_ctrl,
    }
    configured_theory = {
        "S_C": theory["S_C"],
        "B10": theory["B10"],
        "B20.value": theory["B20"]["value"],
        "B20.local": theory["B20"]["local"],
        "B20.control": theory["B20"]["control"],
    }
    for name, expected in expected_theory.items():
        if not np.allclose(
            configured_theory[name], expected, rtol=0.0, atol=1.0e-14
        ):
            raise RuntimeError(f"P2 plateau theory value changed: {name}")
    if config["extrapolation"]["fit_variable"] != "inverse_N":
        raise RuntimeError("P2 plateau regression variable must be inverse_N")
    if config["theory"]["exact_B20_CI_coverage_required"] is not False:
        raise RuntimeError("Exact B20 coverage cannot be a fixed-gamma plateau gate")

    used_seeds: set[int] = set()
    for target in ("primary", "h4-small-step", "d5"):
        used_seeds.update(int(value) for value in load_formal_config(target)["chains"]["seeds"])
    rotation = load_yaml(P2_PLATEAU_ROOT / "configs" / "d2_rotation_invariance.yaml")
    used_seeds.update(int(value) for value in rotation["paired_matrix"]["seeds"])
    plateau_seeds = set(audit["seeds"])
    if plateau_seeds & used_seeds:
        raise RuntimeError("P2 plateau seed block overlaps a previous formal experiment")

    return {
        "status": "PASS",
        "workstream": "p2",
        "phase": "fixed_gamma_large_N_plateau_check_only",
        "matrix": audit,
        "fresh_seed_block": True,
        "fit_variable": "1/N",
        "primary_estimator": config["estimators"]["primary"],
        "config_sha256": hashlib.sha256(P2_PLATEAU_CONFIG_PATH.read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(P2_PLATEAU_PROTOCOL_PATH.read_bytes()).hexdigest(),
        "scientific_execution": "NOT_RUN",
    }


def _capture_plateau_provenance(
    runs: Sequence[FormalRunSpec], config: dict[str, Any]
) -> dict[str, Any]:
    environment = environment_manifest()
    return {
        "schema_version": 1,
        "capture_point": "before_any_p2_plateau_output_write",
        "study": "p2_multidimensional_validation",
        "phase": "formal_fixed_gamma_large_N_plateau",
        "matrix_id": config["matrix_identifier"],
        "source_commit": environment["git_commit"],
        "source_dirty_at_run_start": environment["git_dirty"],
        "environment": environment,
        "config_path": str(P2_PLATEAU_CONFIG_PATH.relative_to(REPO_ROOT)),
        "config_sha256": hashlib.sha256(P2_PLATEAU_CONFIG_PATH.read_bytes()).hexdigest(),
        "protocol_path": str(P2_PLATEAU_PROTOCOL_PATH.relative_to(REPO_ROOT)),
        "protocol_sha256": hashlib.sha256(P2_PLATEAU_PROTOCOL_PATH.read_bytes()).hexdigest(),
        "config_snapshot": config["config_snapshot_filename"],
        "seeds": sorted({item.seed for item in runs}),
        "bootstrap_seed": int(config["bootstrap"]["seed"]),
        "bootstrap_repetitions": int(config["bootstrap"]["repetitions"]),
        "run_matrix": audit_plateau_run_matrix(runs),
        "expected_chain_count": len(runs),
        "planned_coordinate_run_rows": len(runs) * 2 * int(config["objective"]["d"]),
        "commands": config["commands"],
        "artifact_namespace": config["artifact_namespace"],
    }


def _setting_groups(runs: Sequence[FormalRunSpec]) -> list[list[FormalRunSpec]]:
    grouped: dict[tuple[int, int, float], list[FormalRunSpec]] = {}
    for run in runs:
        grouped.setdefault(run.setting_key, []).append(run)
    return list(grouped.values())


def run_plateau_experiment() -> dict[str, Any]:
    """Run all 40 frozen chains and install one complete artifact transaction."""

    check_plateau_protocol()
    config = load_plateau_config()
    runs = build_plateau_run_matrix(config)
    target_root = plateau_artifact_root(config)
    provenance = _capture_plateau_provenance(runs, config)
    if (
        provenance["source_dirty_at_run_start"] is not False
        or provenance["source_commit"] == "NO_COMMIT"
    ):
        raise RuntimeError(
            "Formal P2 plateau runs require a clean committed source tree at run start"
        )
    require_complete_existing_output(
        target_root,
        required_files=(*P2_PLATEAU_RAW_RESULT_FILES, P2_RUN_START_PROVENANCE),
    )

    staged_root = create_staging_directory(target_root)
    try:
        write_json(provenance, staged_root / P2_RUN_START_PROVENANCE)
        shutil.copyfile(
            P2_PLATEAU_CONFIG_PATH,
            staged_root / str(config["config_snapshot_filename"]),
        )
        all_run_rows: list[dict[str, Any]] = []
        all_batch_rows: list[dict[str, Any]] = []
        groups = _setting_groups(runs)
        for index, setting in enumerate(groups, start=1):
            item = setting[0]
            print(
                f"[p2-plateau] setting {index}/{len(groups)}: "
                f"H={item.H} N={item.N} gamma={item.gamma:.10g}",
                flush=True,
            )
            run_rows, batch_rows = simulate_formal_setting(
                setting, config, run_start_provenance=provenance
            )
            all_run_rows.extend(run_rows)
            all_batch_rows.extend(batch_rows)
            write_csv(all_run_rows, staged_root / "run_summary.csv")
            write_csv(all_batch_rows, staged_root / "batch_summary.csv")

        from .plateau_analysis import build_plateau_outputs

        derived = build_plateau_outputs(staged_root)
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

    return rebase_staged_paths(
        {
            "output_root": target_root,
            "run_rows": all_run_rows,
            "batch_rows": all_batch_rows,
            "overwrite_audit": overwrite_audit,
            **derived,
        },
        staged_root,
        target_root,
    )
