"""Exactly two coordinate figures for the fixed-gamma plateau."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ...core.plotting import PAPER_STYLE, POINT_COLOR, REFERENCE_COLOR, finish_paper_figure


def _coordinate_figure(
    coordinate: int,
    setting_summary: pd.DataFrame,
    fit_summary: pd.DataFrame,
    fit_curve: pd.DataFrame,
    output_root: Path,
) -> Path:
    settings = setting_summary[
        (setting_summary["estimator"] == "stationary_mean_balance")
        & (setting_summary["coordinate"].astype(int) == coordinate)
    ].sort_values("inverse_N")
    fit = fit_summary[fit_summary["coordinate"].astype(int) == coordinate]
    curve = fit_curve[fit_curve["coordinate"].astype(int) == coordinate].sort_values(
        "inverse_N"
    )
    if len(settings) != 5 or len(fit) != 1 or len(curve) != 5:
        raise ValueError(f"Plateau coordinate {coordinate + 1} data are incomplete")
    fit_row = fit.iloc[0]
    x = settings["inverse_N"].to_numpy(float)
    means = settings["C_mean"].to_numpy(float)
    low = settings["simultaneous_ci_low"].to_numpy(float)
    high = settings["simultaneous_ci_high"].to_numpy(float)
    x_line = np.linspace(0.0, float(np.max(x)) * 1.04, 200)
    fitted = float(fit_row["beta0"]) + float(fit_row["beta1"]) * x_line
    with plt.rc_context(PAPER_STYLE):
        fig, ax = plt.subplots(figsize=(7.2, 5.0), layout="constrained")
        ax.errorbar(
            x,
            means,
            yerr=np.vstack([means - low, high - means]),
            fmt="o",
            markersize=6,
            capsize=4,
            capthick=1.5,
            elinewidth=1.5,
            color=POINT_COLOR,
            label="Per-N estimate and simultaneous CI",
        )
        ax.plot(x_line, fitted, color=POINT_COLOR, alpha=0.75, label=r"Fit $\beta_0+\beta_1/N$")
        beta0 = float(fit_row["beta0"])
        ax.errorbar(
            [0.0],
            [beta0],
            yerr=np.array(
                [
                    [beta0 - float(fit_row["simultaneous_ci_low"])],
                    [float(fit_row["simultaneous_ci_high"]) - beta0],
                ]
            ),
            fmt="D",
            color="#6a1b9a",
            capsize=4,
            markersize=6,
            label=r"Extrapolated $\beta_0$ and simultaneous CI",
        )
        target = float(fit_row["B20_component"])
        ax.axhline(
            target,
            color=REFERENCE_COLOR,
            linestyle="--",
            label=rf"Theory $B_{{20,{coordinate + 1}}}={target:.5g}$",
        )
        ax.axvline(0.0, color="black", linewidth=0.8, alpha=0.35)
        ax.set_xlabel(r"Inverse client count $1/N$")
        ax.set_ylabel(rf"Normalized residual $\widehat C_{{{coordinate + 1}}}$")
        ax.set_title(f"Fixed-gamma plateau: coordinate {coordinate + 1}")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=9)
        return finish_paper_figure(
            fig,
            output_root
            / f"p2_d2_fixed_gamma_largeN_coordinate_{coordinate + 1}.png",
        )


def plot_plateau_figures(
    setting_summary: pd.DataFrame,
    fit_summary: pd.DataFrame,
    fit_curve: pd.DataFrame,
    output_root: Path,
) -> list[Path]:
    return [
        _coordinate_figure(
            coordinate, setting_summary, fit_summary, fit_curve, output_root
        )
        for coordinate in (0, 1)
    ]
