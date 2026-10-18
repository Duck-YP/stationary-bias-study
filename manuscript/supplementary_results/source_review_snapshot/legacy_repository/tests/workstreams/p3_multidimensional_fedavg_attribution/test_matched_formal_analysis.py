import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution import matched_formal
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.matched_formal_analysis import (
    _interpretation_lines,
    analyze_formal_saved,
    build_formal_report_and_plots,
    build_setting_summary,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.matched_simulation import (
    covariance_from_p3_config,
    objective_from_p3_config,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.theory import (
    matched_vector_theory_targets,
)


def _synthetic_primary(root: Path) -> pd.DataFrame:
    root.mkdir(parents=True, exist_ok=True)
    config = matched_formal.load_formal_config("primary")
    objective = objective_from_p3_config(config)
    covariance = covariance_from_p3_config(config)
    effects = dict(zip(config["pairs"]["seeds"], np.linspace(-0.001, 0.001, 8), strict=True))
    rows = []
    for spec in matched_formal.build_formal_run_matrix("primary", config):
        targets = matched_vector_theory_targets(objective, covariance, spec.H)
        for coordinate in range(2):
            difference = targets.B20_ctrl[coordinate] + 0.1 * (coordinate + 1) * spec.delta + effects[spec.seed]
            fedavg = targets.B20_FA[coordinate] + effects[spec.seed]
            scaffold = fedavg + difference
            row = {
                "pair_id": spec.pair_id, "seed": spec.seed, "H": spec.H,
                "N": spec.N, "gamma": spec.gamma, "delta": spec.delta,
                "coordinate": coordinate, "matrix_id": spec.matrix_id,
                "setting_id": spec.setting_id, "run_id": spec.run_id,
                "scaffold_balance_bias": scaffold * spec.gamma**2,
                "fedavg_balance_bias": fedavg * spec.gamma**2,
                "scaffold_primary_coefficient": scaffold,
                "fedavg_primary_coefficient": fedavg,
                "paired_primary_difference": difference,
                "paired_cancellation_difference": difference,
                "scaffold_direct_bias": (scaffold + 0.1) * spec.gamma**2,
                "fedavg_direct_bias": (fedavg + 0.1) * spec.gamma**2,
                "paired_direct_difference": difference,
                "B11_d_component": targets.B11_d[coordinate],
                "B20_ctrl_component": targets.B20_ctrl[coordinate],
                "scaffold_validity_pass": True, "fedavg_validity_pass": True,
                "scaffold_stationarity_pass": True, "fedavg_stationarity_pass": True,
                "zero_sum_control_error": 1.0e-15, "zero_sum_control_pass": True,
                "crn_integrity_pass": True, "pair_validity_pass": True,
                "batches_used": 100, "stopping_reason": "PRECISION_REACHED",
                "source_commit": "fixture", "source_dirty_at_run_start": False,
            }
            rows.append(row)
    frame = pd.DataFrame(rows)
    frame.to_csv(root / "paired_run_summary.csv", index=False)
    frame.assign(batch_index=0).to_csv(root / "paired_batch_summary.csv", index=False)
    provenance = {
        "matrix_id": config["matrix_identifier"], "source_commit": "fixture",
        "source_dirty_at_run_start": False, "config_sha256": "fixture",
    }
    (root / matched_formal.RUN_START_PROVENANCE).write_text(
        json.dumps(provenance), encoding="utf-8"
    )
    return frame


def test_paired_student_t_rejects_sixteen_algorithm_observations(tmp_path: Path) -> None:
    frame = _synthetic_primary(tmp_path)
    config = matched_formal.load_formal_config("primary")
    summary = build_setting_summary(frame, config)
    assert set(summary["paired_chain_count"]) == {8}
    assert set(summary["degrees_of_freedom"]) == {7}
    with pytest.raises(ValueError, match="eight pair differences"):
        build_setting_summary(pd.concat([frame, frame], ignore_index=True), config)


def test_paired_bootstrap_analysis_and_empirical_report(tmp_path: Path) -> None:
    _synthetic_primary(tmp_path)
    outputs = analyze_formal_saved("primary", tmp_path)
    assert len(outputs["paired_setting_summary"]) == 20
    assert len(outputs["paired_fit_summary"]) == 4
    assert set(outputs["paired_bootstrap_intercepts"]["bootstrap_unit"]) == {
        "paired_seed_label_block"
    }
    assert {"P3-F0", "P3-F1", "P3-F2", "P3-F3", "P3-F4", "P3-F5", "P3-F6", "P3-F7"} <= set(
        outputs["paired_falsification_summary"]["gate"]
    )
    reported = build_formal_report_and_plots("primary", tmp_path)
    text = reported["report"].read_text(encoding="utf-8")
    assert text.startswith("# Empirical numerical outcomes")
    assert "Simulation outcomes are not proven statements." in text
    assert "prove the decomposition" in text
    assert {path.name for path in reported["figures"]} == {
        "p3_matched_d2_H2_control_convergence.png",
        "p3_matched_d2_H4_control_convergence.png",
    }


def test_primary_report_does_not_turn_h4_coverage_false_into_gate_failure_or_coverage_claim(
    tmp_path: Path,
) -> None:
    _synthetic_primary(tmp_path)
    analyze_formal_saved("primary", tmp_path)
    fits_path = tmp_path / "paired_fit_summary.csv"
    fits = pd.read_csv(fits_path)
    fits.loc[fits["H"].astype(int) == 2, "theory_covered_simultaneous"] = True
    fits.loc[fits["H"].astype(int) == 4, "theory_covered_simultaneous"] = False
    fits.to_csv(fits_path, index=False)

    report = build_formal_report_and_plots("primary", tmp_path)["report"].read_text(
        encoding="utf-8"
    )

    assert "H=4 primary path is reporting-only" in report
    assert "coverage flags are False for coordinates 0 and 1" in report
    assert "Final H=4 adjudication is delegated" in report
    assert "covers the predicted B20_ctrl vector" not in report
    assert "H=4 primary path fails" not in report


def test_h4_small_step_interpretation_records_frozen_gate_failure() -> None:
    fits = pd.DataFrame(
        {
            "H": [4, 4],
            "coordinate": [0, 1],
            "theory_covered_simultaneous": [False, False],
        }
    )

    interpretation = " ".join(_interpretation_lines("h4-small-step", fits))

    assert "P3-F3 simultaneous-coverage criterion fails" in interpretation
    assert "H=4 coordinates 0 and 1" in interpretation
    assert "does not by itself contradict" in interpretation
