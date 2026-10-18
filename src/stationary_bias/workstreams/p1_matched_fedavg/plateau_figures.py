"""Fixed-gamma large-client plateau figure built from saved summaries."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ...core.plotting import PAPER_STYLE, REFERENCE_COLOR, finish_paper_figure


def _errorbar(
    ax: plt.Axes,
    frame: pd.DataFrame,
    *,
    mean: str,
    low: str,
    high: str,
    target: float,
    ylabel: str,
    title: str,
    color: str,
) -> None:
    ordered = frame.sort_values("N", ascending=False)
    x = 1.0 / ordered["N"].to_numpy(float)
    values = ordered[mean].to_numpy(float)
    yerr = np.vstack(
        [values - ordered[low].to_numpy(float), ordered[high].to_numpy(float) - values]
    )
    ax.errorbar(
        x,
        values,
        yerr=yerr,
        fmt="o",
        markersize=5,
        capsize=3,
        capthick=1.3,
        elinewidth=1.3,
        color=color,
        label="Estimate and 95% CI",
    )
    design = np.column_stack([np.ones(x.size), x])
    beta, _, _, _ = np.linalg.lstsq(design, values, rcond=None)
    x_line = np.linspace(0.0, float(np.max(x)) * 1.04, 100)
    ax.plot(x_line, beta[0] + beta[1] * x_line, color=color, alpha=0.7, label="Linear fit")
    ax.axhline(
        target,
        color=REFERENCE_COLOR,
        linestyle="--",
        label=f"Theory {target:g}",
    )
    ax.set_xlabel(r"Inverse client count $1/N$")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=10)


def plot_plateau_figure(
    algorithm_summary: pd.DataFrame,
    pair_summary: pd.DataFrame,
    output_root: Path,
) -> Path:
    if algorithm_summary.empty or pair_summary.empty:
        raise ValueError("Plateau summary tables must be non-empty")
    fedavg = algorithm_summary[algorithm_summary["algorithm"] == "fedavg"]
    scaffold = algorithm_summary[algorithm_summary["algorithm"] == "scaffold"]
    with plt.rc_context(PAPER_STYLE):
        fig, axes = plt.subplots(1, 3, figsize=(16.0, 4.7), layout="constrained")
        _errorbar(
            axes[0],
            fedavg,
            mean="C_mean",
            low="C_ci_low",
            high="C_ci_high",
            target=-0.125,
            ylabel=r"$C_{FA}$",
            title="FedAvg",
            color="#1769aa",
        )
        _errorbar(
            axes[1],
            scaffold,
            mean="C_mean",
            low="C_ci_low",
            high="C_ci_high",
            target=-0.1875,
            ylabel=r"$C_{SCAFFOLD}$",
            title="SCAFFOLD",
            color="#2e7d32",
        )
        _errorbar(
            axes[2],
            pair_summary,
            mean="Delta_C_mean",
            low="Delta_C_ci_low",
            high="Delta_C_ci_high",
            target=-0.0625,
            ylabel=r"$\Delta C=C_{SCAFFOLD}-C_{FA}$",
            title="Matched difference",
            color="#6a1b9a",
        )
        fig.suptitle(r"Fixed $\gamma=1/24$, $H=2$: large-$N$ matched plateau")
        return finish_paper_figure(
            fig, output_root / "fixed_gamma_large_n_plateau.png"
        )
