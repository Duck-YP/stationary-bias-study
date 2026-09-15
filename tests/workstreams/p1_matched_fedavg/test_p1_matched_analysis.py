from pathlib import Path

import numpy as np
import pandas as pd
from stationary_bias.workstreams.p1_matched_fedavg.analysis import (
    build_pair_setting_summary,
)
from stationary_bias.workstreams.p1_matched_fedavg.figures import plot_p1_figures
from stationary_bias.core.inference.statistics import student_t_summary


def test_delta_interval_uses_per_seed_paired_differences() -> None:
    fedavg = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0])
    paired_delta = np.array([-0.05, -0.06, -0.04, -0.05, -0.07, -0.03, -0.05, -0.05])
    frame = pd.DataFrame(
        {
            "pair_id": [f"pair-{seed}" for seed in range(8)],
            "seed": range(8),
            "grid_name": "synthetic",
            "H": 2,
            "N": 24,
            "gamma": 1.0 / 24.0,
            "C_scaffold": fedavg + paired_delta,
            "C_fedavg": fedavg,
            "Delta_C": paired_delta,
            "Delta_B20_target": -0.0625,
            "pair_gate_pass": True,
        }
    )
    observed = build_pair_setting_summary(frame).iloc[0]
    expected = student_t_summary(paired_delta)
    assert observed["Delta_C_mean"] == expected.mean
    assert observed["Delta_C_ci_low"] == expected.ci_low
    assert observed["Delta_C_ci_high"] == expected.ci_high


def test_p1_figures_read_saved_summary_values(tmp_path: Path) -> None:
    algorithm = pd.DataFrame(
        {
            "algorithm": ["fedavg"],
            "H": [2],
            "gamma": [0.05],
            "C_mean": [-0.12],
            "C_ci_low": [-0.14],
            "C_ci_high": [-0.10],
            "B20_target": [-0.125],
        }
    )
    pairs = pd.DataFrame(
        {
            "H": [2],
            "gamma": [0.05],
            "Delta_C_mean": [-0.06],
            "Delta_C_ci_low": [-0.08],
            "Delta_C_ci_high": [-0.04],
            "Delta_B20_target": [-0.0625],
        }
    )
    outputs = plot_p1_figures(algorithm, pairs, tmp_path)
    assert {path.name for path in outputs} == {
        "fedavg_coefficient_H2.png",
        "matched_difference_H2.png",
    }
    assert all(path.is_file() for path in outputs)
