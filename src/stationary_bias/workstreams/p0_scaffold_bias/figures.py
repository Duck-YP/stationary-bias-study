"""Required uncertainty-aware figures for the original study."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ...core.inference.statistics import student_t_critical_95
from ...core.io import P0_PUBLICATION_ARTIFACT_ROOT, experiment_result_root
from ...core.plotting import (
    PAPER_STYLE,
    REFERENCE_COLOR,
    finish_paper_figure,
    paper_axes,
    paper_errorbar,
)


def _finish(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def _errorbar(ax: plt.Axes, x: np.ndarray, mean: np.ndarray, low: np.ndarray, high: np.ndarray, **kwargs: object) -> None:
    yerr = np.vstack([mean - low, high - mean])
    ax.errorbar(x, mean, yerr=yerr, fmt="o", capsize=4, linestyle="none", **kwargs)


def plot_coefficient_convergence(setting: pd.DataFrame, H: int) -> Path:
    data = setting[(setting["experiment"] == "coefficient_convergence") & (setting["H"] == H)].sort_values("gamma")
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
            label=rf"Theory $B_{{20}}({H})={target:g}$",
        )
        ax.set_xlabel(r"Step size $\gamma$")
        ax.set_ylabel("Debiased normalized\nresidual\n" + r"$C_{\gamma,N,H}$")
        ax.set_title(rf"Normalized residual ($H={H}$)")
        ax.grid(alpha=0.25)
        ax.legend(loc="upper left")
        return finish_paper_figure(
            fig,
            experiment_result_root("coefficient_convergence") / f"coefficient_convergence_H{H}.png",
        )


def plot_client_count_scaling(setting: pd.DataFrame) -> Path:
    data = setting[setting["experiment"] == "client_count_scaling"].copy()
    data = data.sort_values("N")
    clients = data["N"].to_numpy(float)

    with plt.rc_context(PAPER_STYLE):
        fig, ax = paper_axes()
        paper_errorbar(
            ax,
            clients,
            data["C_mean"].to_numpy(float),
            data["C_ci_low"].to_numpy(float),
            data["C_ci_high"].to_numpy(float),
        )
        target = float(data["B_theory"].iloc[0])
        ax.axhline(
            target,
            color=REFERENCE_COLOR,
            linestyle="--",
            label=rf"Theory $B_{{20}}(2)={target:g}$",
        )
        ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
        ax.set_xscale("log", base=2)
        ax.set_xticks(clients, [str(int(value)) for value in clients])
        ax.set_xlim(clients.min() / 1.15, clients.max() * 1.15)
        ax.set_xlabel(r"Number of clients $N$")
        ax.set_ylabel("Debiased normalized\nresidual\n" + r"$C_{\gamma,N,2}$")
        ax.set_title(r"Client-count scaling at $\gamma=1/24$")
        ax.grid(alpha=0.25)
        ax.legend(loc="center right")
        return finish_paper_figure(
            fig,
            experiment_result_root("client_count_scaling") / "client_count_scaling.png",
        )


def plot_negative_controls(setting: pd.DataFrame) -> Path:
    data = setting[setting["experiment"] == "negative_controls"].copy().sort_values(["control_name", "gamma"])
    labels = [
        f"{name}\nH={int(H)}, N={int(N)}\ng={gamma:.5f}"
        for name, H, N, gamma in zip(data["control_name"], data["H"], data["N"], data["gamma"], strict=True)
    ]
    x = np.arange(len(data))
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    _errorbar(
        ax,
        x,
        data["C_mean"].to_numpy(float),
        data["C_ci_low"].to_numpy(float),
        data["C_ci_high"].to_numpy(float),
        color="#5b4b8a",
        label="Normalized estimate and 95% t CI",
    )
    ax.axhline(0.0, color="#b3261e", linestyle="--", label="Zero target")
    ax.set_xticks(x, labels, rotation=25, ha="right")
    ax.set_xlabel("Frozen negative-control setting")
    ax.set_ylabel(r"Normalized coefficient $C$")
    ax.set_title("Negative controls and H=1 boundary sanity")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    return _finish(fig, experiment_result_root("negative_controls") / "negative_controls.png")


def plot_estimator_agreement(setting: pd.DataFrame) -> Path:
    data = setting.sort_values(["experiment", "H", "N", "gamma"]).copy()
    difference = data["b_direct_mean"].to_numpy(float) - data["b_balance_mean"].to_numpy(float)
    combined_se = np.sqrt(
        data["b_direct_se"].to_numpy(float) ** 2 + data["b_balance_se"].to_numpy(float) ** 2
    )
    half = student_t_critical_95(7) * combined_se
    labels = [
        f"{experiment}{('/' + control) if control else ''}:H{int(H)}:N{int(N)}"
        for experiment, control, H, N in zip(
            data["experiment"], data["control_name"], data["H"], data["N"], strict=True
        )
    ]
    x = np.arange(len(data))
    fig, ax = plt.subplots(figsize=(13.5, 5.5))
    ax.errorbar(x, difference, yerr=half, fmt="o", capsize=3, linestyle="none", color="#1769aa")
    ax.axhline(0.0, color="#b3261e", linestyle="--", label="Exact agreement target")
    ax.set_xticks(x, labels, rotation=65, ha="right", fontsize=7)
    ax.set_xlabel("Formal setting")
    ax.set_ylabel(r"$\hat b_{direct}-\hat b_{balance}$ (95% combined CI)")
    ax.set_title("Direct-vs-balance stationary-mean agreement")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    return _finish(fig, P0_PUBLICATION_ARTIFACT_ROOT / "estimator_agreement.png")


def plot_all() -> list[Path]:
    path = P0_PUBLICATION_ARTIFACT_ROOT / "setting_summary.csv"
    if not path.exists():
        raise FileNotFoundError("Run `python run.py build-report` before plotting")
    setting = pd.read_csv(path, keep_default_na=False)
    return [
        plot_coefficient_convergence(setting, 2),
        plot_coefficient_convergence(setting, 4),
        plot_client_count_scaling(setting),
        plot_negative_controls(setting),
        plot_estimator_agreement(setting),
    ]
