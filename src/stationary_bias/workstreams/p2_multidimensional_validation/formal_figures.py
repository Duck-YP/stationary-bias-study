"""Coefficient-convergence figures rendered from saved setting summaries."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ...core.plotting import PAPER_STYLE, REFERENCE_COLOR, finish_paper_figure


def _plot_H(
    frame: pd.DataFrame, *, H: int, d: int, title: str, path: Path
) -> Path:
    selected = frame[
        (frame["H"].astype(int) == H)
        & (frame["estimator"] == "stationary_mean_balance")
    ]
    coordinates = list(range(d))
    if selected.empty or set(selected["coordinate"].astype(int)) != set(coordinates):
        raise ValueError(f"Saved setting summary lacks all {d} balance coordinates for H={H}")
    colors = ["#1769aa", "#8e3b46", "#2e7d32", "#7b1fa2", "#ef6c00"]
    markers = ["o", "s", "^", "D", "v"]
    linestyles = ["-", "-.", ":", "--", "-"]
    with plt.rc_context(PAPER_STYLE):
        fig, ax = plt.subplots(figsize=(7.2, 5.0), layout="constrained")
        for coordinate in coordinates:
            group = selected[selected["coordinate"].astype(int) == coordinate].sort_values(
                "delta"
            )
            x = group["delta"].to_numpy(float)
            mean = group["C_mean"].to_numpy(float)
            low = group["simultaneous_ci_low"].to_numpy(float)
            high = group["simultaneous_ci_high"].to_numpy(float)
            target = float(group["B20_component"].iloc[0])
            style = {
                "color": colors[coordinate % len(colors)],
                "marker": markers[coordinate % len(markers)],
                "linestyle": linestyles[coordinate % len(linestyles)],
            }
            ax.errorbar(
                x,
                mean,
                yerr=np.vstack([mean - low, high - mean]),
                label=f"Coordinate {coordinate + 1}",
                capsize=3,
                linewidth=1.4,
                markersize=5,
                **style,
            )
            ax.axhline(
                target,
                color=style["color"],
                linestyle="--" if coordinate % 2 == 0 else ":",
                alpha=0.72,
                label=f"Coordinate {coordinate + 1} theory",
            )
        ax.axvline(0.0, color=REFERENCE_COLOR, linewidth=0.8, alpha=0.4)
        ax.set_xlabel(r"Path variable $\delta=\gamma+1/N$")
        ax.set_ylabel(r"Balance normalized coefficient $\widehat C_j$")
        ax.set_title(title)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=9)
        return finish_paper_figure(fig, path)


def plot_saved_formal_summaries(
    target: str, setting_summary: pd.DataFrame, output_root: Path
) -> list[Path]:
    """Create only the figures associated with one saved formal summary."""

    if target == "primary":
        return [
            _plot_H(
                setting_summary,
                H=2,
                d=2,
                title="Coefficient convergence, d=2, H=2",
                path=output_root / "p2_d2_H2_coefficient_convergence.png",
            ),
            _plot_H(
                setting_summary,
                H=4,
                d=2,
                title="Coefficient convergence, d=2, H=4",
                path=output_root / "p2_d2_H4_coefficient_convergence.png",
            ),
        ]
    if target == "h4-small-step":
        return [
            _plot_H(
                setting_summary,
                H=4,
                d=2,
                title="Smaller-step confirmation, d=2, H=4",
                path=output_root / "p2_d2_H4_small_step_confirmation.png",
            )
        ]
    if target == "d5":
        return [
            _plot_H(
                setting_summary,
                H=2,
                d=5,
                title="Controlled coefficient convergence, d=5, H=2",
                path=output_root / "p2_d5_H2_coefficient_convergence.png",
            ),
            _plot_H(
                setting_summary,
                H=4,
                d=5,
                title="Controlled coefficient convergence, d=5, H=4",
                path=output_root / "p2_d5_H4_coefficient_convergence.png",
            ),
        ]
    raise ValueError(f"Unknown formal target: {target}")
