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
    "p2": {
        "slug": "p2_multidimensional_validation",
        "question": "Multidimensional homogeneous SCAFFOLD validation.",
    },
    "p3": {
        "slug": "p3_multidimensional_fedavg_attribution",
        "question": "Multidimensional matched FedAvg versus SCAFFOLD attribution.",
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
            f"Publication matrix differs from the frozen protocol: {publication}"
        )
    if not (
        confirmation["actual_runs"] == 32
        and confirmation["unique_run_keys"] == 32
        and confirmation["settings"] == 4
        and confirmation["all_unique"]
    ):
        raise RuntimeError(
            f"Confirmation matrix differs from the frozen protocol: {confirmation}"
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
    from .workstreams.p1_matched_fedavg.artifact_audit import (
        audit_archived_config_closure,
    )
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
        raise RuntimeError(f"Matrix differs from the defined formal matrix: {audit}")
    return {
        "status": "PASS",
        "workstream": "p1",
        "matched_fedavg_matrix": audit,
        "fixed_gamma_large_n_matrix": check_plateau_matrix(),
        "archive_config": audit_archived_config_closure(),
    }


def check_all() -> dict[str, Any]:
    return {
        "status": "PASS",
        "p0": check_p0(),
        "p1": check_p1(),
        "p2": check_p2_all(),
        "p3": check_p3_all(),
    }


def check_p2_all() -> dict[str, Any]:
    """Validate every implemented matrix and its saved formal evidence."""

    from .workstreams.p2_multidimensional_validation.artifact_audit import (
        audit_saved_p2_artifacts,
    )
    from .workstreams.p2_multidimensional_validation.formal import (
        check_d5_protocol,
        check_formal_protocol,
    )
    from .workstreams.p2_multidimensional_validation.rotation import (
        check_rotation_protocol,
    )
    from .workstreams.p2_multidimensional_validation.plateau import (
        check_plateau_protocol,
    )
    from .workstreams.p2_multidimensional_validation.simulation import check_p2

    return {
        "status": "PASS",
        "workstream": "p2",
        "smoke": check_p2(),
        "formal_d2": check_formal_protocol(),
        "rotation_d2": check_rotation_protocol(),
        "formal_d5": check_d5_protocol(),
        "fixed_gamma_large_N_d2": check_plateau_protocol(),
        "artifacts": audit_saved_p2_artifacts(),
    }


def check_p3_all() -> dict[str, Any]:
    """Validate third-workstream protocols and formal evidence without simulation."""

    from .workstreams.p3_multidimensional_fedavg_attribution.artifact_audit import (
        audit_saved_p3_artifacts,
    )
    from .workstreams.p3_multidimensional_fedavg_attribution.formal import (
        check_formal_protocol,
    )
    from .workstreams.p3_multidimensional_fedavg_attribution.simulation import (
        check_smoke_protocol,
    )
    from .workstreams.p3_multidimensional_fedavg_attribution.matched_formal import (
        check_matched_formal_protocol,
    )
    from .workstreams.p3_multidimensional_fedavg_attribution.matched_simulation import (
        check_matched_smoke_protocol,
    )

    return {
        "status": "PASS",
        "workstream": "p3",
        "fedavg_coefficient": {
            "smoke": check_smoke_protocol(),
            "formal": check_formal_protocol(),
        },
        "matched_attribution": {
            "smoke": check_matched_smoke_protocol(),
            "formal": check_matched_formal_protocol(),
        },
        "artifacts": audit_saved_p3_artifacts(),
    }


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
    raise ValueError(f"Unknown baseline experiment: {name}")


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

    p2 = root.add_parser("p2", help="Multidimensional homogeneous SCAFFOLD study.")
    p2_actions = p2.add_subparsers(dest="action", required=True)
    p2_actions.add_parser("check")
    p2_actions.add_parser("smoke")
    p2_d5 = p2_actions.add_parser(
        "d5", help="Frozen controlled d=5 coefficient pipeline."
    )
    p2_d5_actions = p2_d5.add_subparsers(dest="d5_action", required=True)
    p2_d5_actions.add_parser("check")
    p2_d5_actions.add_parser("run")
    p2_d5_actions.add_parser("analyze")
    p2_d5_actions.add_parser("report")
    p2_formal = p2_actions.add_parser(
        "formal", help="Frozen d=2 coefficient pipeline."
    )
    p2_formal_targets = p2_formal.add_subparsers(
        dest="formal_target", required=True
    )
    p2_formal_targets.add_parser("check")
    for target in ("primary", "h4-small-step"):
        target_parser = p2_formal_targets.add_parser(target)
        target_actions = target_parser.add_subparsers(
            dest="formal_action", required=True
        )
        target_actions.add_parser("run")
        target_actions.add_parser("analyze")
        target_actions.add_parser("report")
    p2_rotation = p2_actions.add_parser(
        "rotation", help="Frozen d=2 coordinate-equivariance pipeline."
    )
    p2_rotation_actions = p2_rotation.add_subparsers(
        dest="rotation_action", required=True
    )
    p2_rotation_actions.add_parser("check")
    p2_rotation_actions.add_parser("run")
    p2_rotation_actions.add_parser("report")
    p2_plateau = p2_actions.add_parser(
        "plateau", help="Frozen d=2 fixed-gamma, large-N plateau pipeline."
    )
    p2_plateau_actions = p2_plateau.add_subparsers(
        dest="plateau_action", required=True
    )
    p2_plateau_actions.add_parser("check")
    p2_plateau_actions.add_parser("run")
    p2_plateau_actions.add_parser("analyze")
    p2_plateau_actions.add_parser("report")

    p3 = root.add_parser(
        "p3", help="Multidimensional matched FedAvg versus SCAFFOLD attribution."
    )
    p3_actions = p3.add_subparsers(dest="action", required=True)
    p3_actions.add_parser("check")
    p3_fedavg = p3_actions.add_parser(
        "fedavg-coefficient", help="Multidimensional FedAvg coefficient pipeline."
    )
    p3_fedavg_actions = p3_fedavg.add_subparsers(
        dest="fedavg_action", required=True
    )
    p3_fedavg_actions.add_parser("check")
    p3_fedavg_actions.add_parser("smoke")
    p3_fedavg_formal = p3_fedavg_actions.add_parser("formal")
    p3_fedavg_formal_targets = p3_fedavg_formal.add_subparsers(
        dest="formal_target", required=True
    )
    p3_fedavg_formal_targets.add_parser("check")
    for target in ("primary", "h4-small-step"):
        target_parser = p3_fedavg_formal_targets.add_parser(target)
        target_actions = target_parser.add_subparsers(
            dest="formal_action", required=True
        )
        target_actions.add_parser("run")
        target_actions.add_parser("analyze")
        target_actions.add_parser("report")
    p3_matched = p3_actions.add_parser(
        "matched-attribution", help="Matched SCAFFOLD-FedAvg control attribution."
    )
    p3_matched_actions = p3_matched.add_subparsers(
        dest="matched_action", required=True
    )
    p3_matched_actions.add_parser("check")
    p3_matched_actions.add_parser("smoke")
    p3_matched_actions.add_parser(
        "diagnostic",
        help="Rebuild the post-hoc H=4 discrepancy diagnostic from saved artifacts.",
    )
    p3_matched_formal = p3_matched_actions.add_parser("formal")
    p3_matched_targets = p3_matched_formal.add_subparsers(
        dest="matched_formal_target", required=True
    )
    p3_matched_targets.add_parser("check")
    for target in ("primary", "h4-small-step"):
        target_parser = p3_matched_targets.add_parser(target)
        target_actions = target_parser.add_subparsers(
            dest="matched_formal_action", required=True
        )
        target_actions.add_parser("run")
        target_actions.add_parser("analyze")
        target_actions.add_parser("report")
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


def _run_p2_formal_action(args: argparse.Namespace) -> None:
    from .workstreams.p2_multidimensional_validation.formal import (
        check_formal_protocol,
        run_formal_matrix,
    )

    if args.formal_target == "check":
        print(json.dumps(check_formal_protocol(), indent=2, sort_keys=True))
        return

    target = str(args.formal_target)
    if args.formal_action == "run":
        outputs = run_formal_matrix(target)
        print(
            json.dumps(
                {
                    "status": "FORMAL_OUTPUT_WRITTEN",
                    "output_root": str(outputs["output_root"]),
                    "run_rows": len(outputs["run_rows"]),
                    "batch_rows": len(outputs["batch_rows"]),
                    "report": str(outputs["report"]),
                    "figures": [str(path) for path in outputs["figures"]],
                    "overwrite_audit": outputs["overwrite_audit"],
                },
                indent=2,
            )
        )
    elif args.formal_action == "analyze":
        from .workstreams.p2_multidimensional_validation.formal_analysis import (
            rebuild_formal_analysis,
        )

        outputs = rebuild_formal_analysis(target)
        print(
            json.dumps(
                {
                    "status": "ANALYSIS_WRITTEN",
                    "output_root": str(outputs["output_root"]),
                    "setting_rows": len(outputs["setting_summary"]),
                    "fit_rows": len(outputs["fit_summary"]),
                    "manifest": str(outputs["manifest"]),
                },
                indent=2,
            )
        )
    elif args.formal_action == "report":
        from .workstreams.p2_multidimensional_validation.formal_analysis import (
            rebuild_formal_report,
        )

        outputs = rebuild_formal_report(target)
        print(
            json.dumps(
                {
                    "status": "REPORT_WRITTEN",
                    "report": str(outputs["report"]),
                    "figures": [str(path) for path in outputs["figures"]],
                },
                indent=2,
            )
        )


def _run_p2_d5_action(args: argparse.Namespace) -> None:
    from .workstreams.p2_multidimensional_validation.formal import (
        check_d5_protocol,
        run_formal_matrix,
    )

    if args.d5_action == "check":
        print(json.dumps(check_d5_protocol(), indent=2, sort_keys=True))
    elif args.d5_action == "run":
        outputs = run_formal_matrix("d5")
        print(
            json.dumps(
                {
                    "status": "FORMAL_OUTPUT_WRITTEN",
                    "output_root": str(outputs["output_root"]),
                    "run_rows": len(outputs["run_rows"]),
                    "batch_rows": len(outputs["batch_rows"]),
                    "report": str(outputs["report"]),
                    "figures": [str(path) for path in outputs["figures"]],
                    "overwrite_audit": outputs["overwrite_audit"],
                },
                indent=2,
            )
        )
    elif args.d5_action == "analyze":
        from .workstreams.p2_multidimensional_validation.formal_analysis import (
            rebuild_formal_analysis,
        )

        outputs = rebuild_formal_analysis("d5")
        print(
            json.dumps(
                {
                    "status": "ANALYSIS_WRITTEN",
                    "output_root": str(outputs["output_root"]),
                    "setting_rows": len(outputs["setting_summary"]),
                    "fit_rows": len(outputs["fit_summary"]),
                    "manifest": str(outputs["manifest"]),
                },
                indent=2,
            )
        )
    elif args.d5_action == "report":
        from .workstreams.p2_multidimensional_validation.formal_analysis import (
            rebuild_formal_report,
        )

        outputs = rebuild_formal_report("d5")
        print(
            json.dumps(
                {
                    "status": "REPORT_WRITTEN",
                    "report": str(outputs["report"]),
                    "figures": [str(path) for path in outputs["figures"]],
                },
                indent=2,
            )
        )


def _run_p2_rotation_action(args: argparse.Namespace) -> None:
    from .workstreams.p2_multidimensional_validation.rotation import (
        check_rotation_protocol,
        report_rotation_formal,
        run_rotation_matrix,
    )

    if args.rotation_action == "check":
        print(json.dumps(check_rotation_protocol(), indent=2, sort_keys=True))
    elif args.rotation_action == "run":
        outputs = run_rotation_matrix()
        print(
            json.dumps(
                {
                    "status": "FORMAL_ROTATION_OUTPUT_WRITTEN",
                    "output_root": str(outputs["output_root"]),
                    "pair_rows": len(outputs["pair_rows"]),
                    "theory_rows": len(outputs["theory_rows"]),
                    "manifest": str(outputs["manifest"]),
                    "report": str(outputs["output_root"] / "p2_d2_rotation_report.md"),
                },
                indent=2,
            )
        )
    elif args.rotation_action == "report":
        report = report_rotation_formal()
        print(json.dumps({"status": "REPORT_WRITTEN", "report": str(report)}, indent=2))


def _run_p2_plateau_action(args: argparse.Namespace) -> None:
    from .workstreams.p2_multidimensional_validation.plateau import (
        check_plateau_protocol,
        run_plateau_experiment,
    )

    if args.plateau_action == "check":
        print(json.dumps(check_plateau_protocol(), indent=2, sort_keys=True))
        return
    if args.plateau_action == "run":
        outputs = run_plateau_experiment()
    else:
        from .workstreams.p2_multidimensional_validation.plateau_analysis import (
            rebuild_plateau_outputs,
        )

        outputs = rebuild_plateau_outputs()
    print(
        json.dumps(
            {
                "status": (
                    "FORMAL_PLATEAU_OUTPUT_WRITTEN"
                    if args.plateau_action == "run"
                    else "PLATEAU_DERIVED_OUTPUTS_REBUILT"
                ),
                "verdict": outputs["verdict"],
                "output_root": str(outputs["output_root"]),
                "report": str(outputs["report"]),
                "figures": [str(path) for path in outputs["figures"]],
                "manifest": str(outputs["manifest"]),
                "overwrite_audit": outputs["overwrite_audit"],
            },
            indent=2,
        )
    )


def _run_p3_fedavg_formal_action(args: argparse.Namespace) -> None:
    from .workstreams.p3_multidimensional_fedavg_attribution.formal import (
        check_formal_protocol,
        run_formal_matrix,
    )

    if args.formal_target == "check":
        print(json.dumps(check_formal_protocol(), indent=2, sort_keys=True))
        return
    target = str(args.formal_target)
    if args.formal_action == "run":
        outputs = run_formal_matrix(target)
        print(
            json.dumps(
                {
                    "status": "FORMAL_OUTPUT_WRITTEN",
                    "output_root": str(outputs["output_root"]),
                    "run_rows": len(outputs["run_rows"]),
                    "batch_rows": len(outputs["batch_rows"]),
                    "report": str(outputs["report"]),
                    "figures": [str(path) for path in outputs["figures"]],
                    "overwrite_audit": outputs["overwrite_audit"],
                },
                indent=2,
            )
        )
    elif args.formal_action == "analyze":
        from .workstreams.p3_multidimensional_fedavg_attribution.formal_analysis import (
            rebuild_formal_analysis,
        )

        outputs = rebuild_formal_analysis(target)
        print(
            json.dumps(
                {
                    "status": "ANALYSIS_WRITTEN",
                    "output_root": str(outputs["output_root"]),
                    "setting_rows": len(outputs["setting_summary"]),
                    "fit_rows": len(outputs["fit_summary"]),
                    "manifest": str(outputs["manifest"]),
                },
                indent=2,
            )
        )
    elif args.formal_action == "report":
        from .workstreams.p3_multidimensional_fedavg_attribution.formal_analysis import (
            rebuild_formal_report,
        )

        outputs = rebuild_formal_report(target)
        print(
            json.dumps(
                {
                    "status": "REPORT_WRITTEN",
                    "report": str(outputs["report"]),
                    "figures": [str(path) for path in outputs["figures"]],
                },
                indent=2,
            )
        )


def _run_p3_matched_action(args: argparse.Namespace) -> None:
    from .workstreams.p3_multidimensional_fedavg_attribution.matched_formal import (
        check_matched_formal_protocol,
        formal_artifact_root,
        run_formal_matrix,
    )
    from .workstreams.p3_multidimensional_fedavg_attribution.matched_simulation import (
        check_matched_smoke_protocol,
        run_matched_smoke,
    )

    if args.matched_action == "check":
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "workstream": "p3",
                    "smoke": check_matched_smoke_protocol(),
                    "formal": check_matched_formal_protocol(),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.matched_action == "smoke":
        outputs = run_matched_smoke()
        diagnostics = outputs["diagnostic_rows"]
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "paired_coordinate_run_rows": len(outputs["run_rows"]),
                    "paired_coordinate_batch_rows": len(outputs["batch_rows"]),
                    "pair_diagnostics": len(diagnostics),
                    "crn_integrity_pass": all(row["crn_integrity_pass"] for row in diagnostics),
                    "zero_sum_control_pass": all(row["zero_sum_control_pass"] for row in diagnostics),
                    "scientific_interpretation": "NOT_APPLICABLE_ENGINEERING_SMOKE",
                    "output_root": str(outputs["output_root"]),
                    "manifest": str(outputs["manifest"]),
                },
                indent=2,
            )
        )
        return
    if args.matched_action == "diagnostic":
        from .workstreams.p3_multidimensional_fedavg_attribution.matched_diagnostic import (
            rebuild_h4_diagnostic,
        )

        outputs = rebuild_h4_diagnostic()
        print(
            json.dumps(
                {
                    "status": "DIAGNOSTIC_WRITTEN",
                    "classification": outputs["classification"],
                    "new_production_simulation": False,
                    "output_root": str(outputs["output_root"]),
                    "pointwise_rows": len(outputs["pointwise_diagnostics"]),
                    "nested_window_rows": len(outputs["nested_window_linear_summary"]),
                    "model_comparison_rows": len(outputs["linear_quadratic_comparison"]),
                    "report": str(outputs["report"]),
                    "manifest": str(outputs["manifest"]),
                    "controlled_overwrite": outputs["controlled_overwrite"],
                },
                indent=2,
            )
        )
        return
    if args.matched_formal_target == "check":
        print(json.dumps(check_matched_formal_protocol(), indent=2, sort_keys=True))
        return
    target = str(args.matched_formal_target)
    if args.matched_formal_action == "run":
        outputs = run_formal_matrix(target)
        print(
            json.dumps(
                {
                    "status": "FORMAL_OUTPUT_WRITTEN",
                    "output_root": str(formal_artifact_root(target)),
                    "paired_run_rows": len(outputs["run_rows"]),
                    "paired_batch_rows": len(outputs["batch_rows"]),
                    "report": str(outputs["report"]),
                    "overwrite_audit": outputs["overwrite_audit"],
                },
                indent=2,
            )
        )
        return
    from .workstreams.p3_multidimensional_fedavg_attribution.matched_formal_analysis import (
        rebuild_formal_analysis,
        rebuild_formal_report,
    )

    output_root = formal_artifact_root(target)
    if args.matched_formal_action == "analyze":
        outputs = rebuild_formal_analysis(target)
        print(
            json.dumps(
                {
                    "status": "ANALYSIS_WRITTEN",
                    "output_root": str(output_root),
                    "setting_rows": len(outputs["paired_setting_summary"]),
                    "fit_rows": len(outputs["paired_fit_summary"]),
                    "manifest": str(outputs["manifest"]),
                    "overwrite_audit": outputs["overwrite_audit"],
                },
                indent=2,
            )
        )
    else:
        outputs = rebuild_formal_report(target)
        print(
            json.dumps(
                {
                    "status": "REPORT_WRITTEN",
                    "report": str(outputs["report"]),
                    "figures": [str(path) for path in outputs["figures"]],
                    "overwrite_audit": outputs["overwrite_audit"],
                },
                indent=2,
            )
        )


def _run_p3_action(args: argparse.Namespace) -> None:
    if args.action == "matched-attribution":
        _run_p3_matched_action(args)
        return
    if args.action == "check":
        print(json.dumps(check_p3_all(), indent=2, sort_keys=True))
        return
    if args.fedavg_action == "formal":
        _run_p3_fedavg_formal_action(args)
        return
    if args.fedavg_action == "check":
        from .workstreams.p3_multidimensional_fedavg_attribution.formal import (
            check_formal_protocol,
        )
        from .workstreams.p3_multidimensional_fedavg_attribution.simulation import (
            check_smoke_protocol,
        )

        print(
            json.dumps(
                {
                    "status": "PASS",
                    "workstream": "p3",
                    "smoke": check_smoke_protocol(),
                    "formal": check_formal_protocol(),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    from .workstreams.p3_multidimensional_fedavg_attribution.simulation import (
        run_smoke,
    )

    outputs = run_smoke()
    diagnostics = outputs["diagnostic_rows"]
    print(
        json.dumps(
            {
                "status": "PASS",
                "coordinate_run_rows": len(outputs["run_rows"]),
                "coordinate_batch_rows": len(outputs["batch_rows"]),
                "diagnostic_rows": len(diagnostics),
                "finite_state_pass": all(
                    row["finite_state_pass"] for row in diagnostics
                ),
                "no_control_state": all(
                    row["no_control_state"] for row in diagnostics
                ),
                "scientific_interpretation": "NOT_APPLICABLE_ENGINEERING_SMOKE",
                "output_root": str(outputs["output_root"]),
                "manifest": str(outputs["manifest"]),
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
    elif args.command == "p2":
        if args.action == "d5":
            _run_p2_d5_action(args)
            return 0
        if args.action == "formal":
            _run_p2_formal_action(args)
            return 0
        if args.action == "rotation":
            _run_p2_rotation_action(args)
            return 0
        if args.action == "plateau":
            _run_p2_plateau_action(args)
            return 0
        from .workstreams.p2_multidimensional_validation.simulation import run_p2_smoke

        if args.action == "check":
            print(json.dumps(check_p2_all(), indent=2, sort_keys=True))
        elif args.action == "smoke":
            outputs = run_p2_smoke()
            diagnostics = outputs["diagnostic_rows"]
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "coordinate_run_rows": len(outputs["run_rows"]),
                        "coordinate_batch_rows": len(outputs["batch_rows"]),
                        "diagnostic_rows": len(diagnostics),
                        "finite_state_pass": all(
                            row["finite_state_pass"] for row in diagnostics
                        ),
                        "scientific_interpretation": "NOT_APPLICABLE_ENGINEERING_SMOKE",
                        "output_root": str(outputs["output_root"]),
                        "manifest": str(outputs["manifest"]),
                    },
                    indent=2,
                )
            )
    elif args.command == "p3":
        _run_p3_action(args)
    return 0
