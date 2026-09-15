"""P1-only figures built exclusively from saved matched result tables."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ...core.plotting import (
    PAPER_STYLE,
    REFERENCE_COLOR,
    finish_paper_figure,
    paper_axes,
    paper_errorbar,
)


def plot_fedavg_coefficient_convergence(
    algorithm_summary: pd.DataFrame, output_root: Path
) -> list[Path]:
    outputs: list[Path] = []
    data = algorithm_summary[algorithm_summary["algorithm"] == "fedavg"]
    for H in sorted(data["H"].unique()):
        subset = data[data["H"] == H].sort_values("gamma")
        with plt.rc_context(PAPER_STYLE):
            fig, ax = paper_axes()
            paper_errorbar(
                ax,
                subset["gamma"].to_numpy(float),
                subset["C_mean"].to_numpy(float),
                subset["C_ci_low"].to_numpy(float),
                subset["C_ci_high"].to_numpy(float),
                label="FedAvg mean and 95% paired-chain CI",
            )
            target = float(subset["B20_target"].iloc[0])
            ax.axhline(
                target,
                color=REFERENCE_COLOR,
                linestyle="--",
                label=rf"Theory $B_{{20}}^{{FA}}({int(H)})={target:g}$",
            )
            ax.set_xlabel(r"Step size $\gamma$")
            ax.set_ylabel(r"FedAvg normalized coefficient $C_{FA}$")
            ax.set_title(rf"Matched FedAvg coefficient ($H={int(H)}$)")
            ax.grid(alpha=0.25)
            ax.legend()
            outputs.append(
                finish_paper_figure(
                    fig, output_root / f"fedavg_coefficient_H{int(H)}.png"
                )
            )
    return outputs


def plot_matched_difference(
    pair_summary: pd.DataFrame, output_root: Path
) -> list[Path]:
    outputs: list[Path] = []
    for H in sorted(pair_summary["H"].unique()):
        subset = pair_summary[pair_summary["H"] == H].sort_values("gamma")
        with plt.rc_context(PAPER_STYLE):
            fig, ax = paper_axes()
            paper_errorbar(
                ax,
                subset["gamma"].to_numpy(float),
                subset["Delta_C_mean"].to_numpy(float),
                subset["Delta_C_ci_low"].to_numpy(float),
                subset["Delta_C_ci_high"].to_numpy(float),
                color="#6a1b9a",
                label="Paired difference and 95% CI",
            )
            target = float(subset["Delta_B20_target"].iloc[0])
            ax.axhline(
                target,
                color=REFERENCE_COLOR,
                linestyle="--",
                label=rf"Theory $\Delta B_{{20}}({int(H)})={target:g}$",
            )
            ax.set_xlabel(r"Step size $\gamma$")
            ax.set_ylabel(r"$\Delta C=C_{SCAFFOLD}-C_{FA}$")
            ax.set_title(rf"Matched algorithm difference ($H={int(H)}$)")
            ax.grid(alpha=0.25)
            ax.legend()
            outputs.append(
                finish_paper_figure(
                    fig, output_root / f"matched_difference_H{int(H)}.png"
                )
            )
    return outputs


def plot_p1_figures(
    algorithm_summary: pd.DataFrame,
    pair_summary: pd.DataFrame,
    output_root: Path,
) -> list[Path]:
    if algorithm_summary.empty or pair_summary.empty:
        raise ValueError("P1 summary tables must be non-empty")
    return [
        *plot_fedavg_coefficient_convergence(algorithm_summary, output_root),
        *plot_matched_difference(pair_summary, output_root),
    ]
