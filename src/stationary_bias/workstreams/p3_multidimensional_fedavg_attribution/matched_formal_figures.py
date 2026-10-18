"""Signed coordinatewise convergence figures for matched attribution."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..p2_multidimensional_validation.formal_figures import _plot_H


def plot_saved_formal_summaries(
    target: str, setting_summary: pd.DataFrame, output_root: Path
) -> list[Path]:
    frame = setting_summary.rename(
        columns={"D_mean": "C_mean", "B20_ctrl_component": "B20_component"}
    ).copy()
    frame["estimator"] = "stationary_mean_balance"
    if target == "primary":
        return [
            _plot_H(
                frame,
                H=H,
                d=2,
                title=f"Matched attribution: d=2, H={H}",
                path=output_root / f"p3_matched_d2_H{H}_control_convergence.png",
            )
            for H in (2, 4)
        ]
    if target == "h4-small-step":
        return [
            _plot_H(
                frame,
                H=4,
                d=2,
                title="Matched H=4 smaller-step check",
                path=output_root / "p3_matched_d2_H4_small_step_confirmation.png",
            )
        ]
    raise ValueError(f"Unknown matched-attribution target: {target}")
