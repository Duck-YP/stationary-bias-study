"""Configuration, provenance, deterministic identifiers, and CSV helpers."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSTREAM_ROOT = REPO_ROOT / "workstreams"
SHARED_CONFIG_ROOT = REPO_ROOT / "shared" / "configs"
P0_ROOT = WORKSTREAM_ROOT / "p0_scaffold_bias"
P1_ROOT = WORKSTREAM_ROOT / "p1_matched_fedavg"
P0_CONFIG_ROOT = P0_ROOT / "configs"
P1_CONFIG_ROOT = P1_ROOT / "configs"
P0_ARTIFACT_ROOT = P0_ROOT / "artifacts"
P1_ARTIFACT_ROOT = P1_ROOT / "artifacts"
P0_PUBLICATION_ARTIFACT_ROOT = P0_ARTIFACT_ROOT / "publication_snapshot"
P0_CONFIRMATION_ARTIFACT_ROOT = P0_ARTIFACT_ROOT / "small_step_confirmation"
P0_SMOKE_ARTIFACT_ROOT = P0_ARTIFACT_ROOT / "smoke"

EXPERIMENT_CONFIG_FILES = {
    "coefficient_convergence": P0_CONFIG_ROOT / "coefficient_convergence.yaml",
    "client_count_scaling": P0_CONFIG_ROOT / "client_count_scaling.yaml",
    "negative_controls": P0_CONFIG_ROOT / "negative_controls.yaml",
}

RESULT_DIRECTORIES = {
    "coefficient_convergence": "coefficient-convergence",
    "client_count_scaling": "client-count-scaling",
    "negative_controls": "negative-controls",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping in {path}")
    return loaded


def load_configs() -> dict[str, dict[str, Any]]:
    """Load the frozen baseline study under descriptive experiment identifiers."""

    return {
        "base": load_yaml(SHARED_CONFIG_ROOT / "simulation_defaults.yaml"),
        **{key: load_yaml(path) for key, path in EXPERIMENT_CONFIG_FILES.items()},
    }


def experiment_result_root(experiment_name: str) -> Path:
    try:
        return P0_PUBLICATION_ARTIFACT_ROOT / RESULT_DIRECTORIES[experiment_name]
    except KeyError as exc:
        raise ValueError(f"Unknown experiment name: {experiment_name}") from exc


def config_hash(base: dict[str, Any], experiment: dict[str, Any]) -> str:
    payload = json.dumps(
        {"base": base, "experiment": experiment}, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "-c", f"safe.directory={REPO_ROOT}", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "NO_COMMIT"


def git_is_dirty() -> bool | None:
    try:
        output = subprocess.run(
            ["git", "-c", f"safe.directory={REPO_ROOT}", "status", "--porcelain", "--", "."],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return bool(output.strip())
    except (OSError, subprocess.CalledProcessError):
        return None


def environment_manifest() -> dict[str, Any]:
    import matplotlib
    import numpy
    import pandas
    import yaml as pyyaml

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {
            "numpy": numpy.__version__,
            "pandas": pandas.__version__,
            "PyYAML": pyyaml.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "git_commit": git_commit(),
        "git_dirty": git_is_dirty(),
    }


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def gamma_token(gamma: float) -> str:
    return f"{gamma:.10f}".replace("-", "m").replace(".", "p")


def make_run_key(
    *,
    experiment: str,
    objective: str,
    noise: str,
    H: int,
    N: int,
    gamma: float,
    seed: int,
    control_name: str = "",
) -> str:
    control = f"__ctrl-{control_name}" if control_name else ""
    return (
        f"{experiment}{control}__obj-{objective}__noise-{noise}__H{H}__N{N}"
        f"__g{gamma_token(gamma)}__seed{seed}"
    )


def write_csv(rows: Iterable[dict[str, Any]] | pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows))
    frame.to_csv(path, index=False, lineterminator="\n")
