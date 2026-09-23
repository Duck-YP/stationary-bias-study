"""Signed-coordinate convergence figures for the FedAvg coefficient."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..p2_multidimensional_validation.formal_figures import _plot_H


def plot_saved_formal_summaries(
    target: str, setting_summary: pd.DataFrame, output_root: Path
) -> list[Path]:
    if target == "primary":
        return [
            _plot_H(
                setting_summary.rename(columns={"B20_FA_component": "B20_component"}),
                H=2,
                d=2,
                title="FedAvg coefficient convergence, d=2, H=2",
                path=output_root / "p3_d2_H2_coefficient_convergence.png",
            ),
            _plot_H(
                setting_summary.rename(columns={"B20_FA_component": "B20_component"}),
                H=4,
                d=2,
                title="FedAvg coefficient convergence, d=2, H=4",
                path=output_root / "p3_d2_H4_coefficient_convergence.png",
            ),
        ]
    if target == "h4-small-step":
        return [
            _plot_H(
                setting_summary.rename(columns={"B20_FA_component": "B20_component"}),
                H=4,
                d=2,
                title="FedAvg smaller-step confirmation, d=2, H=4",
                path=output_root / "p3_d2_H4_small_step_confirmation.png",
            )
        ]
    raise ValueError(f"Unknown FedAvg coefficient target: {target}")
