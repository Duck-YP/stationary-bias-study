import json
from pathlib import Path

import numpy as np
import pandas as pd

from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution import formal
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.formal_analysis import (
    analyze_formal_saved,
    build_formal_report_and_plots,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.theory import (
    fedavg_vector_theory_targets,
)


def _write_synthetic_primary(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    config = formal.load_formal_config("primary")
    specs = formal.build_formal_run_matrix("primary", config)
    objective = formal.objective_from_formal_config(config)
    covariance = formal.covariance_from_formal_config(config)
    seed_effect = dict(
        zip(config["chains"]["seeds"], np.linspace(-0.002, 0.002, 8), strict=True)
    )
    rows = []
    for spec in specs:
        targets = fedavg_vector_theory_targets(objective, covariance, spec.H)
        for estimator in ("direct_sample_mean", "stationary_mean_balance"):
            for coordinate in range(2):
                C_value = (
                    targets.B20_FA[coordinate]
                    + 0.2 * (coordinate + 1) * spec.delta
                    + seed_effect[spec.seed]
                    + (0.0002 if estimator == "direct_sample_mean" else 0.0)
                )
                rows.append(
                    {
                        "study": "p3",
                        "phase": "formal",
                        "matrix_id": spec.matrix_id,
                        "setting_id": spec.setting_id,
                        "run_id": spec.run_id,
                        "seed": spec.seed,
                        "d": 2,
                        "coordinate": coordinate,
                        "H": spec.H,
                        "N": spec.N,
                        "gamma": spec.gamma,
                        "delta": spec.delta,
                        "estimator": estimator,
                        "b_component": spec.gamma**2 * C_value + (spec.gamma / spec.N) * targets.B11_d[coordinate],
                        "B11_d_component": targets.B11_d[coordinate],
                        "C_component": C_value,
                        "B20_FA_component": targets.B20_FA[coordinate],
                        "normalized_error_component": C_value - targets.B20_FA[coordinate],
                        "batches_used": 100,
                        "stopping_reason": "PRECISION_REACHED",
                        "validity_pass": True,
                        "finite_state_pass": True,
                        "stationarity_pass": True,
                        "direct_balance_agreement_pass": True,
                        "source_commit": "fixture",
                        "source_dirty_at_run_start": False,
                    }
                )
    frame = pd.DataFrame(rows)
    frame.to_csv(root / "run_summary.csv", index=False)
    frame.assign(batch_index=0).to_csv(root / "batch_summary.csv", index=False)
    provenance = {
        "schema_version": 1,
        "matrix_id": config["matrix_identifier"],
        "source_commit": "fixture",
        "source_dirty_at_run_start": False,
        "config_path": str(formal.formal_config_path("primary")),
        "config_sha256": "fixture",
        "protocol_path": str(formal.formal_config_path("primary")),
        "protocol_sha256": "fixture",
        "seeds": config["chains"]["seeds"],
    }
    (root / formal.RUN_START_PROVENANCE).write_text(
        json.dumps(provenance), encoding="utf-8"
    )


def test_saved_formal_analysis_and_report_are_empirical_only(tmp_path) -> None:
    _write_synthetic_primary(tmp_path)
    analyzed = analyze_formal_saved("primary", tmp_path)
    assert len(analyzed["setting_summary"]) == 40
    assert len(analyzed["fit_summary"]) == 4
    assert set(analyzed["falsification_summary"]["gate"]) == {
        "F0", "F1", "F2", "F3", "F4", "F5", "F6"
    }
    outputs = build_formal_report_and_plots("primary", tmp_path)
    report = outputs["report"].read_text(encoding="utf-8")
    assert report.startswith("# Empirical numerical outcomes")
    assert "Simulation outcomes are not proven statements." in report
    assert "SCAFFOLD-minus-FedAvg difference" in report
    assert {path.name for path in outputs["figures"]} == {
        "p3_d2_H2_coefficient_convergence.png",
        "p3_d2_H4_coefficient_convergence.png",
    }
