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


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = REPO_ROOT / "configs"
EXPERIMENT_CONFIG_ROOT = CONFIG_ROOT / "experiments"
RESULT_ROOT = REPO_ROOT / "results"

EXPERIMENT_CONFIG_FILES = {
    "p3a": EXPERIMENT_CONFIG_ROOT / "coefficient_convergence.yaml",
    "p3b": EXPERIMENT_CONFIG_ROOT / "client_count_scaling.yaml",
    "p3c": EXPERIMENT_CONFIG_ROOT / "negative_controls.yaml",
}

RESULT_DIRECTORIES = {
    "p3a": "coefficient-convergence",
    "p3b": "client-count-scaling",
    "p3c": "negative-controls",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping in {path}")
    return loaded


def load_configs() -> dict[str, dict[str, Any]]:
    """Load the original preregistered study under stable internal keys.

    The short keys are retained only inside the numerical engine so the
    historical CSV schema remains reproducible. Public paths and CLI commands
    use descriptive experiment names.
    """

    return {
        "base": load_yaml(CONFIG_ROOT / "simulation_defaults.yaml"),
        **{key: load_yaml(path) for key, path in EXPERIMENT_CONFIG_FILES.items()},
    }


def experiment_result_root(internal_name: str) -> Path:
    try:
        return RESULT_ROOT / RESULT_DIRECTORIES[internal_name]
    except KeyError as exc:
        raise ValueError(f"Unknown internal experiment name: {internal_name}") from exc


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
