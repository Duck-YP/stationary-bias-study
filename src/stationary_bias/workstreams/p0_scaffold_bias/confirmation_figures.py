"""Figures for the isolated small-step confirmation experiment."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ...core.inference.statistics import student_t_critical_95
from ...core.plotting import (
    PAPER_STYLE,
    REFERENCE_COLOR,
    SCALED_ERROR_COLOR,
    finish_paper_figure,
    paper_axes,
    paper_errorbar,
)
from .confirmation import CONFIRMATION_RESULT_ROOT


def _finish(fig: plt.Figure, name: str, protocol_commit: str) -> Path:
    path = CONFIRMATION_RESULT_ROOT / name
    fig.text(0.995, 0.005, f"Protocol: {protocol_commit[:12]}", ha="right", va="bottom", fontsize=6, color="#555555")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def _points(
    ax: plt.Axes,
    x: np.ndarray,
    mean: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    *,
    label: str,
    color: str = "#1769aa",
) -> None:
    yerr = np.vstack([mean - low, high - mean])
    ax.errorbar(x, mean, yerr=yerr, fmt="o", linestyle="none", capsize=4, color=color, label=label)


def plot_C(setting: pd.DataFrame) -> Path:
    data = setting.sort_values("gamma")
    with plt.rc_context(PAPER_STYLE):
        fig, ax = paper_axes()
        paper_errorbar(
            ax,
            data["gamma"].to_numpy(float),
            data["C_mean"].to_numpy(float),
            data["C_ci_low"].to_numpy(float),
            data["C_ci_high"].to_numpy(float),
        )
        target = float(data["B_theory"].iloc[0])
        ax.axhline(
            target,
            color=REFERENCE_COLOR,
            linestyle="--",
            label=rf"Theory $B_{{20}}(4)={target:g}$",
        )
        ax.set_xlabel(r"Step size $\gamma$")
        ax.set_ylabel(r"$C_{\gamma,1/\gamma,4}$")
        ax.set_title("Normalized residual")
        ax.grid(alpha=0.25)
        ax.legend(loc="upper left")
        return finish_paper_figure(fig, CONFIRMATION_RESULT_ROOT / "coefficient_vs_step_size.png")


def plot_error(setting: pd.DataFrame) -> Path:
    data = setting.sort_values("gamma")
    fig, ax = plt.subplots(figsize=(6.6, 4.5))
    _points(
        ax,
        data["gamma"].to_numpy(float),
        data["error_to_theory"].to_numpy(float),
        data["error_ci_low"].to_numpy(float),
        data["error_ci_high"].to_numpy(float),
        label="Error and 95% t CI",
        color="#5b4b8a",
    )
    ax.axhline(0.0, color="#b3261e", linestyle="--", label="Theory agreement target")
    ax.set_xlabel(r"Step size $\gamma$")
    ax.set_ylabel(r"Coefficient error $E(\gamma)=C-B_{20}(4)$")
    ax.set_title("Error to the H=4 candidate coefficient")
    ax.grid(alpha=0.25)
    ax.legend()
    return _finish(fig, "error_vs_step_size.png", str(data["protocol_commit"].iloc[0]))


def plot_scaled_error(setting: pd.DataFrame) -> Path:
    data = setting.sort_values("gamma")
    with plt.rc_context(PAPER_STYLE):
        fig, ax = paper_axes()
        paper_errorbar(
            ax,
            data["gamma"].to_numpy(float),
            data["scaled_error"].to_numpy(float),
            data["scaled_error_ci_low"].to_numpy(float),
            data["scaled_error_ci_high"].to_numpy(float),
            color=SCALED_ERROR_COLOR,
        )
        ax.axhline(0.0, color=REFERENCE_COLOR, linestyle="--", label="Zero reference")
        ax.set_xlabel(r"Step size $\gamma$")
        ax.set_ylabel(r"$\frac{C_{\gamma,1/\gamma,4}-B_{20}(4)}{\gamma}$")
        ax.set_title("Scaled asymptotic error")
        ax.grid(alpha=0.25)
        ax.legend(loc="center right")
        return finish_paper_figure(fig, CONFIRMATION_RESULT_ROOT / "scaled_error_vs_step_size.png")


def plot_estimator_agreement(setting: pd.DataFrame) -> Path:
    data = setting.sort_values("gamma")
    difference = data["b_direct_mean"].to_numpy(float) - data["b_balance_mean"].to_numpy(float)
    combined_se = np.hypot(
        data["b_direct_se"].to_numpy(float), data["b_balance_se"].to_numpy(float)
    )
    half = student_t_critical_95(7) * combined_se
    labels = [f"1/{round(1/gamma)}\nN={int(N)}" for gamma, N in zip(data["gamma"], data["N"], strict=True)]
    x = np.arange(len(data))
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    ax.errorbar(x, difference, yerr=half, fmt="o", linestyle="none", capsize=4, color="#1769aa")
    ax.axhline(0.0, color="#b3261e", linestyle="--", label="Exact agreement target")
    ax.set_xticks(x, labels)
    ax.set_xlabel("Frozen small-step setting")
    ax.set_ylabel(r"$\hat b_{direct}-\hat b_{balance}$ (95% combined CI)")
    ax.set_title("Small-step direct-vs-balance estimator agreement")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    return _finish(fig, "estimator_agreement.png", str(data["protocol_commit"].iloc[0]))


def plot_confirmation_all() -> list[Path]:
    path = CONFIRMATION_RESULT_ROOT / "setting_summary.csv"
    if not path.exists():
        raise FileNotFoundError("Build the small-step confirmation report before plotting")
    setting = pd.read_csv(path, keep_default_na=False)
    return [
        plot_C(setting),
        plot_error(setting),
        plot_scaled_error(setting),
        plot_estimator_agreement(setting),
    ]
