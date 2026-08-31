"""Single command-line interface for checking, running, and reporting the study."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .confirmation_figures import plot_confirmation_all
from .figures import plot_all
from .publication_figures import plot_publication_figures
from .project_io import (
    CONFIG_ROOT,
    EXPERIMENT_CONFIG_ROOT,
    REPO_ROOT,
    RESULT_ROOT,
    environment_manifest,
    load_configs,
    load_yaml,
    write_json,
)
from .result_tables import summarize_all
from .simulation import build_run_matrix, matrix_audit, run_experiment, run_smoke
from .small_step_confirmation import (
    CONFIRMATION_CONFIG_PATH,
    audit_confirmation_matrix,
    build_confirmation_matrix,
    load_confirmation_config,
    run_confirmation,
    summarize_confirmation,
)


PUBLIC_TO_INTERNAL = {
    "coefficient-convergence": "p3a",
    "client-count-scaling": "p3b",
    "negative-controls": "p3c",
}
RUN_CHOICES = [*PUBLIC_TO_INTERNAL, "small-step-confirmation", "all"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_study() -> dict[str, Any]:
    configs = load_configs()
    original = matrix_audit(build_run_matrix(configs))
    confirmation_config = load_confirmation_config()
    confirmation = audit_confirmation_matrix(build_confirmation_matrix(confirmation_config))

    expected_original = {
        "coefficient_convergence": 80,
        "client_count_scaling": 40,
        "negative_controls": 48,
        "total": 168,
        "controls": {
            "no_stochastic_noise": 16,
            "no_nonlinear_conversion": 16,
            "h1_boundary_sanity": 16,
        },
        "unique_run_keys": 168,
        "all_unique": True,
    }
    if original != expected_original:
        raise RuntimeError(f"Original experiment matrix differs from the frozen protocol: {original}")
    if not (
        confirmation["actual_runs"] == 32
        and confirmation["unique_run_keys"] == 32
        and confirmation["settings"] == 4
        and confirmation["all_unique"]
    ):
        raise RuntimeError(f"Confirmation matrix differs from the frozen protocol: {confirmation}")

    config_paths = [
        CONFIG_ROOT / "simulation_defaults.yaml",
        EXPERIMENT_CONFIG_ROOT / "coefficient_convergence.yaml",
        EXPERIMENT_CONFIG_ROOT / "client_count_scaling.yaml",
        EXPERIMENT_CONFIG_ROOT / "negative_controls.yaml",
        CONFIRMATION_CONFIG_PATH,
    ]
    for path in config_paths:
        load_yaml(path)
    return {
        "status": "PASS",
        "original_experiments": original,
        "small_step_confirmation": confirmation,
        "config_sha256": {str(path.relative_to(REPO_ROOT)): _sha256(path) for path in config_paths},
    }


def _write_run_manifest(action: str, details: dict[str, Any] | None = None) -> Path:
    payload = {
        "schema_version": 1,
        "study": "stationary-bias-study",
        "action": action,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": environment_manifest(),
        "validation": check_study(),
        "details": details or {},
    }
    path = RESULT_ROOT / "run_manifest.json"
    write_json(payload, path)
    return path


def run_named_experiment(name: str) -> None:
    if name in PUBLIC_TO_INTERNAL:
        run_experiment(PUBLIC_TO_INTERNAL[name])
        return
    if name == "small-step-confirmation":
        run_confirmation()
        return
    if name == "all":
        for internal_name in PUBLIC_TO_INTERNAL.values():
            run_experiment(internal_name)
        run_confirmation()
        return
    raise ValueError(f"Unknown experiment: {name}")


def build_reports() -> dict[str, Any]:
    original = summarize_all()
    original_figures = plot_all()
    confirmation = summarize_confirmation()
    confirmation_figures = plot_confirmation_all()
    relative = lambda path: Path(path).relative_to(REPO_ROOT).as_posix()
    return {
        "final_report": relative(original["report"]),
        "original_figures": [relative(path) for path in original_figures],
        "confirmation_report": relative(confirmation["report"]),
        "confirmation_figures": [relative(path) for path in confirmation_figures],
    }


def run_tests() -> None:
    subprocess.run([sys.executable, "-m", "pytest"], cwd=REPO_ROOT, check=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python run.py",
        description="Reproduce the stationary-bias numerical study.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="Validate all frozen configs and run matrices.")
    subparsers.add_parser("smoke-test", help="Run a short deterministic simulation.")

    run_parser = subparsers.add_parser("run", help="Run one formal experiment or all experiments.")
    run_parser.add_argument("experiment", choices=RUN_CHOICES)

    subparsers.add_parser("build-report", help="Rebuild summaries, reports, and figures from raw CSV files.")
    subparsers.add_parser(
        "plot-paper-figures",
        help="Rebuild only the publication figures from saved summary and fit CSV files.",
    )
    subparsers.add_parser("test", help="Run the automated test suite.")
    subparsers.add_parser(
        "reproduce",
        help="Run tests, validate configs, run all experiments, and rebuild every report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "check":
        print(json.dumps(check_study(), indent=2, sort_keys=True))
    elif args.command == "smoke-test":
        run_rows, batch_rows = run_smoke()
        print(json.dumps({"status": "PASS", "run_rows": len(run_rows), "batch_rows": len(batch_rows)}, indent=2))
    elif args.command == "run":
        run_named_experiment(args.experiment)
        manifest = _write_run_manifest("run", {"experiment": args.experiment})
        print(f"manifest={manifest}")
    elif args.command == "plot-paper-figures":
        outputs = plot_publication_figures()
        relative = [Path(path).relative_to(REPO_ROOT).as_posix() for path in outputs]
        print(json.dumps({"figures": relative}, indent=2))
    elif args.command == "build-report":
        outputs = build_reports()
        manifest = _write_run_manifest("build-report", outputs)
        print(json.dumps({**outputs, "manifest": str(manifest)}, indent=2))
    elif args.command == "test":
        run_tests()
    elif args.command == "reproduce":
        run_tests()
        check_study()
        run_named_experiment("all")
        outputs = build_reports()
        manifest = _write_run_manifest("reproduce", outputs)
        print(json.dumps({"status": "PASS", **outputs, "manifest": str(manifest)}, indent=2))
    return 0
