"""Shared publication styling and deterministic figure export helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PAPER_FIGURE_SIZE = (6.4, 4.3)
PAPER_STYLE = {
    "font.family": "DejaVu Sans",
    "font.size": 15,
    "axes.titlesize": 18,
    "axes.labelsize": 15,
    "axes.linewidth": 1.0,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
    "lines.linewidth": 2.0,
}

POINT_COLOR = "#1769aa"
SCALED_ERROR_COLOR = "#2e7d32"
REFERENCE_COLOR = "#b3261e"


def paper_axes() -> tuple[plt.Figure, plt.Axes]:
    """Create one consistently sized publication panel."""

    return plt.subplots(figsize=PAPER_FIGURE_SIZE, layout="constrained")


def paper_errorbar(
    ax: plt.Axes,
    x: np.ndarray,
    mean: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    *,
    color: str = POINT_COLOR,
    label: str = "Mean and 95% CI",
) -> None:
    """Draw the common point-and-confidence-interval style."""

    yerr = np.vstack([mean - low, high - mean])
    ax.errorbar(
        x,
        mean,
        yerr=yerr,
        fmt="o",
        markersize=6,
        linestyle="none",
        capsize=4,
        capthick=1.6,
        elinewidth=1.6,
        color=color,
        label=label,
    )


def finish_paper_figure(fig: plt.Figure, png_path: Path) -> Path:
    """Write a 300 dpi PNG."""

    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        png_path,
        dpi=300,
        metadata={"Software": "stationary-bias-study"},
    )
    plt.close(fig)
    return png_path
