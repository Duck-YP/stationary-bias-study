"""Workstream-first command-line interface for the research repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .core.io import (
    EXPERIMENT_CONFIG_FILES,
    P0_PUBLICATION_ARTIFACT_ROOT,
    REPO_ROOT,
    SHARED_CONFIG_ROOT,
    environment_manifest,
    load_configs,
    load_yaml,
    write_json,
)


P0_PUBLIC_TO_EXPERIMENT = {
    "coefficient-convergence": "coefficient_convergence",
    "client-count-scaling": "client_count_scaling",
    "negative-controls": "negative_controls",
}

WORKSTREAMS = {
    "p0": {
        "slug": "p0_scaffold_bias",
        "question": "Original publication SCAFFOLD stationary-bias study.",
    },
    "p1": {
        "slug": "p1_matched_fedavg",
        "question": "Matched FedAvg versus SCAFFOLD coefficient attribution.",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_p0() -> dict[str, Any]:
    from .workstreams.p0_scaffold_bias.confirmation import (
        CONFIRMATION_CONFIG_PATH,
        audit_confirmation_matrix,
        build_confirmation_matrix,
        load_confirmation_config,
    )
    from .workstreams.p0_scaffold_bias.simulation import (
        build_run_matrix,
        matrix_audit,
    )

    configs = load_configs()
    publication = matrix_audit(build_run_matrix(configs))
    confirmation_config = load_confirmation_config()
    confirmation = audit_confirmation_matrix(
        build_confirmation_matrix(confirmation_config)
    )
    expected_publication = {
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
    if publication != expected_publication:
        raise RuntimeError(
            f"P0 matrix differs from the frozen protocol: {publication}"
        )
    if not (
        confirmation["actual_runs"] == 32
        and confirmation["unique_run_keys"] == 32
        and confirmation["settings"] == 4
        and confirmation["all_unique"]
    ):
        raise RuntimeError(
            f"P0 confirmation matrix differs from the frozen protocol: {confirmation}"
        )
    config_paths = [
        SHARED_CONFIG_ROOT / "simulation_defaults.yaml",
        *EXPERIMENT_CONFIG_FILES.values(),
        CONFIRMATION_CONFIG_PATH,
    ]
    for path in config_paths:
        load_yaml(path)
    return {
        "status": "PASS",
        "workstream": "p0",
        "publication_experiments": publication,
        "small_step_confirmation": confirmation,
        "config_sha256": {
            str(path.relative_to(REPO_ROOT)): _sha256(path) for path in config_paths
        },
    }


def check_p1() -> dict[str, Any]:
    from .workstreams.p1_matched_fedavg.plateau import check_plateau_matrix
    from .workstreams.p1_matched_fedavg.simulation import audit_p1_run_matrix

    audit = audit_p1_run_matrix()
    expected = {
        "total_pairs": 112,
        "primary_pairs": 80,
        "small_step_h4_pairs": 32,
        "settings": 14,
        "unique_pair_ids": 112,
        "all_unique": True,
        "primary_seeds": list(range(301, 309)),
        "small_step_h4_seeds": list(range(401, 409)),
    }
    if audit != expected:
        raise RuntimeError(f"P1 matrix differs from the defined formal matrix: {audit}")
    return {
        "status": "PASS",
        "workstream": "p1",
        "matched_fedavg_matrix": audit,
        "fixed_gamma_large_n_matrix": check_plateau_matrix(),
    }


def check_all() -> dict[str, Any]:
    return {"status": "PASS", "p0": check_p0(), "p1": check_p1()}


def _write_p0_manifest(action: str, details: dict[str, Any] | None = None) -> Path:
    payload = {
        "schema_version": 1,
        "workstream": "p0",
        "action": action,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": environment_manifest(),
        "validation": check_p0(),
        "details": details or {},
    }
    path = P0_PUBLICATION_ARTIFACT_ROOT / "run_manifest.json"
    write_json(payload, path)
    return path


def run_p0_experiment(name: str) -> None:
    from .workstreams.p0_scaffold_bias.confirmation import run_confirmation
    from .workstreams.p0_scaffold_bias.simulation import run_experiment

    if name in P0_PUBLIC_TO_EXPERIMENT:
        run_experiment(P0_PUBLIC_TO_EXPERIMENT[name])
        return
    if name == "small-step-confirmation":
        run_confirmation()
        return
    if name == "all":
        for experiment in P0_PUBLIC_TO_EXPERIMENT.values():
            run_experiment(experiment)
        run_confirmation()
        return
    raise ValueError(f"Unknown P0 experiment: {name}")


def build_p0_reports() -> dict[str, Any]:
    from .workstreams.p0_scaffold_bias.analysis import summarize_all
    from .workstreams.p0_scaffold_bias.confirmation import summarize_confirmation
    from .workstreams.p0_scaffold_bias.confirmation_figures import (
        plot_confirmation_all,
    )
    from .workstreams.p0_scaffold_bias.figures import plot_all

    publication = summarize_all()
    publication_figures = plot_all()
    confirmation = summarize_confirmation()
    confirmation_figures = plot_confirmation_all()

    def relative(path: Path) -> str:
        return Path(path).relative_to(REPO_ROOT).as_posix()

    return {
        "final_report": relative(publication["report"]),
        "publication_figures": [relative(path) for path in publication_figures],
        "confirmation_report": relative(confirmation["report"]),
        "confirmation_figures": [relative(path) for path in confirmation_figures],
    }


def run_tests() -> None:
    subprocess.run([sys.executable, "-m", "pytest"], cwd=REPO_ROOT, check=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python run.py",
        description="Run one clearly identified stationary-bias workstream.",
    )
    root = parser.add_subparsers(dest="command", required=True)
    root.add_parser("list", help="List implemented research workstreams.")
    root.add_parser("check", help="Validate every implemented workstream matrix.")
    root.add_parser("test", help="Run the complete automated test suite.")

    p0 = root.add_parser("p0", help="Frozen original publication SCAFFOLD study.")
    p0_actions = p0.add_subparsers(dest="action", required=True)
    p0_actions.add_parser("check")
    p0_actions.add_parser("smoke")
    p0_run = p0_actions.add_parser("run")
    p0_run.add_argument(
        "experiment",
        choices=[*P0_PUBLIC_TO_EXPERIMENT, "small-step-confirmation", "all"],
    )
    p0_actions.add_parser("report")
    p0_actions.add_parser("plot")
    p0_actions.add_parser("reproduce")

    p1 = root.add_parser("p1", help="Matched FedAvg versus SCAFFOLD study.")
    p1_actions = p1.add_subparsers(dest="action", required=True)
    p1_actions.add_parser("check")
    p1_actions.add_parser("smoke")
    p1_actions.add_parser("run")
    p1_actions.add_parser("report")
    p1_plateau = p1_actions.add_parser(
        "plateau", help="Fixed-gamma, large-N matched plateau experiment."
    )
    p1_plateau_actions = p1_plateau.add_subparsers(
        dest="plateau_action", required=True
    )
    p1_plateau_actions.add_parser("check")
    p1_plateau_actions.add_parser("smoke")
    p1_plateau_actions.add_parser("run")
    p1_plateau_actions.add_parser("report")
    return parser


def _run_p0_action(args: argparse.Namespace) -> None:
    if args.action == "check":
        print(json.dumps(check_p0(), indent=2, sort_keys=True))
    elif args.action == "smoke":
        from .workstreams.p0_scaffold_bias.simulation import run_smoke

        run_rows, batch_rows = run_smoke()
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "run_rows": len(run_rows),
                    "batch_rows": len(batch_rows),
                },
                indent=2,
            )
        )
    elif args.action == "run":
        run_p0_experiment(args.experiment)
        manifest = _write_p0_manifest("run", {"experiment": args.experiment})
        print(f"manifest={manifest}")
    elif args.action == "report":
        outputs = build_p0_reports()
        manifest = _write_p0_manifest("report", outputs)
        print(json.dumps({**outputs, "manifest": str(manifest)}, indent=2))
    elif args.action == "plot":
        from .workstreams.p0_scaffold_bias.publication_figures import (
            plot_publication_figures,
        )

        outputs = plot_publication_figures()
        print(
            json.dumps(
                {
                    "figures": [
                        str(Path(path).relative_to(REPO_ROOT)) for path in outputs
                    ]
                },
                indent=2,
            )
        )
    elif args.action == "reproduce":
        run_tests()
        check_p0()
        run_p0_experiment("all")
        outputs = build_p0_reports()
        manifest = _write_p0_manifest("reproduce", outputs)
        print(
            json.dumps(
                {"status": "PASS", **outputs, "manifest": str(manifest)},
                indent=2,
            )
        )


def _run_p1_action(args: argparse.Namespace) -> None:
    if args.action == "plateau":
        _run_p1_plateau_action(args)
        return

    from .workstreams.p1_matched_fedavg.analysis import build_p1_outputs
    from .workstreams.p1_matched_fedavg.simulation import (
        P1_ARCHIVED_RESULT_ROOT,
        P1_RESULT_ROOT,
        run_p1_experiment,
        run_p1_smoke,
    )

    if args.action == "check":
        print(json.dumps(check_p1(), indent=2, sort_keys=True))
    elif args.action == "smoke":
        outputs = run_p1_smoke()
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "algorithm_run_rows": len(outputs["run_rows"]),
                    "pair_rows": len(outputs["pair_rows"]),
                    "batch_rows": len(outputs["batch_rows"]),
                    "pair_gate_pass": bool(
                        all(row["pair_gate_pass"] for row in outputs["pair_rows"])
                    ),
                    "scientific_interpretation": "NOT_APPLICABLE_SMOKE",
                    "output_root": str(outputs["output_root"]),
                },
                indent=2,
            )
        )
    elif args.action == "run":
        outputs = run_p1_experiment()
        print(
            json.dumps(
                {
                    "output_root": str(P1_RESULT_ROOT),
                    "overwrite_audit": outputs["overwrite_audit"],
                },
                indent=2,
            )
        )
    elif args.action == "report":
        current_raw = P1_RESULT_ROOT / "run_summary.csv"
        archived_report = P1_ARCHIVED_RESULT_ROOT / "p1_report.md"
        archived_manifest = P1_ARCHIVED_RESULT_ROOT / "p1_manifest.json"
        if (
            not current_raw.exists()
            and archived_report.exists()
            and archived_manifest.exists()
        ):
            print(
                json.dumps(
                    {
                        "status": "ARCHIVED_FORMAL_SNAPSHOT",
                        "report": str(archived_report),
                        "manifest": str(archived_manifest),
                        "figures": [
                            str(path)
                            for path in sorted(P1_ARCHIVED_RESULT_ROOT.glob("*.png"))
                        ],
                    },
                    indent=2,
                )
            )
            return
        outputs = build_p1_outputs()
        print(
            json.dumps(
                {
                    "report": str(outputs["report"]),
                    "manifest": str(outputs["manifest"]),
                    "figures": [str(path) for path in outputs["figures"]],
                },
                indent=2,
            )
        )


def _run_p1_plateau_action(args: argparse.Namespace) -> None:
    from .workstreams.p1_matched_fedavg.plateau import (
        PLATEAU_RESULT_ROOT,
        check_plateau_matrix,
        run_plateau_experiment,
        run_plateau_smoke,
    )

    if args.plateau_action == "check":
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "workstream": "p1",
                    "experiment": "fixed_gamma_large_n_plateau",
                    "formal_matrix": check_plateau_matrix(),
                },
                indent=2,
                sort_keys=True,
            )
        )
    elif args.plateau_action == "smoke":
        outputs = run_plateau_smoke()
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "algorithm_run_rows": len(outputs["run_rows"]),
                    "pair_rows": len(outputs["pair_rows"]),
                    "batch_rows": len(outputs["batch_rows"]),
                    "pair_gate_pass": bool(
                        all(row["pair_gate_pass"] for row in outputs["pair_rows"])
                    ),
                    "scientific_interpretation": "NOT_APPLICABLE_SMOKE",
                    "output_root": str(outputs["output_root"]),
                },
                indent=2,
            )
        )
    elif args.plateau_action == "run":
        outputs = run_plateau_experiment()
        print(
            json.dumps(
                {
                    "output_root": str(PLATEAU_RESULT_ROOT),
                    "overwrite_audit": outputs["overwrite_audit"],
                },
                indent=2,
            )
        )
    elif args.plateau_action == "report":
        from .workstreams.p1_matched_fedavg.plateau_analysis import (
            build_plateau_outputs,
        )

        outputs = build_plateau_outputs()
        print(
            json.dumps(
                {
                    "report": str(outputs["report"]),
                    "manifest": str(outputs["manifest"]),
                    "figure": str(outputs["figure"]),
                },
                indent=2,
            )
        )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "list":
        print(json.dumps(WORKSTREAMS, indent=2, sort_keys=True))
    elif args.command == "check":
        print(json.dumps(check_all(), indent=2, sort_keys=True))
    elif args.command == "test":
        run_tests()
    elif args.command == "p0":
        _run_p0_action(args)
    elif args.command == "p1":
        _run_p1_action(args)
    return 0
