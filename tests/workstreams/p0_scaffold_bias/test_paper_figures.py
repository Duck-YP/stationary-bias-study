from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import stationary_bias.workstreams.p0_scaffold_bias.confirmation_figures as confirmation_figures
import stationary_bias.cli as cli
import stationary_bias.workstreams.p0_scaffold_bias.figures as figures
import stationary_bias.workstreams.p0_scaffold_bias.publication_figures as publication_figures
import stationary_bias.workstreams.p0_scaffold_bias.simulation as p0_simulation
from stationary_bias.core.plotting import PAPER_FIGURE_SIZE, PAPER_STYLE, finish_paper_figure


def _capture_figure(monkeypatch, module):
    captured = {}

    def capture(fig, path: Path) -> Path:
        captured["figure"] = fig
        captured["path"] = path
        return path

    monkeypatch.setattr(module, "finish_paper_figure", capture)
    return captured


def test_publication_export_writes_png_only(tmp_path: Path) -> None:
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    png_path = tmp_path / "figure.png"

    assert finish_paper_figure(fig, png_path) == png_path
    assert png_path.is_file()
    assert not png_path.with_suffix(".pdf").exists()


def test_publication_fonts_remain_legible_after_latex_scaling() -> None:
    assert PAPER_STYLE["axes.titlesize"] >= 18
    assert PAPER_STYLE["axes.labelsize"] >= 15
    assert PAPER_STYLE["xtick.labelsize"] >= 14
    assert PAPER_STYLE["ytick.labelsize"] >= 14
    assert PAPER_STYLE["legend.fontsize"] >= 14


def test_client_count_display_uses_n_without_adding_new_plot_elements(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(figures, "experiment_result_root", lambda _: tmp_path)
    captured = _capture_figure(monkeypatch, figures)
    clients = np.array([8, 16, 32, 64, 128])
    means = -0.19 + 0.16 / clients
    setting = pd.DataFrame(
        {
            "experiment": "client_count_scaling",
            "N": clients,
            "C_mean": means,
            "C_ci_low": means - 0.001,
            "C_ci_high": means + 0.001,
            "B_theory": -0.1875,
        }
    )

    figures.plot_client_count_scaling(setting)
    fig = captured["figure"]
    ax = fig.axes[0]
    mean_container = next(
        container for container in ax.containers if container.get_label() == "Mean and 95% CI"
    )
    mean_line = mean_container.lines[0]

    np.testing.assert_array_equal(mean_line.get_xdata(), clients)
    np.testing.assert_array_equal(mean_line.get_ydata(), means)
    assert not any(line.get_label().startswith("Fit in") for line in ax.lines)
    assert ax.get_xscale() == "log"
    assert ax.get_xlabel() == r"Number of clients $N$"
    assert tuple(fig.get_size_inches()) == PAPER_FIGURE_SIZE
    plt.close(fig)


def test_small_step_panels_plot_saved_values_without_recalculation(monkeypatch) -> None:
    gammas = np.array([1 / 192, 1 / 128, 1 / 96, 1 / 64])
    means = np.array([-0.5859, -0.5828, -0.5791, -0.5722])
    scaled = np.array([1.51, 1.40, 1.40, 1.38])
    setting = pd.DataFrame(
        {
            "gamma": gammas,
            "C_mean": means,
            "C_ci_low": means - 0.002,
            "C_ci_high": means + 0.002,
            "B_theory": -0.59375,
            "scaled_error": scaled,
            "scaled_error_ci_low": scaled - 0.2,
            "scaled_error_ci_high": scaled + 0.2,
        }
    )

    captured = _capture_figure(monkeypatch, confirmation_figures)
    confirmation_figures.plot_C(setting)
    normalized_ax = captured["figure"].axes[0]
    normalized_container = next(
        container
        for container in normalized_ax.containers
        if container.get_label() == "Mean and 95% CI"
    )
    normalized_line = normalized_container.lines[0]
    np.testing.assert_array_equal(normalized_line.get_ydata(), means)
    assert normalized_ax.get_title() == "Normalized residual"
    assert "confirmatory" not in " ".join(text.get_text() for text in normalized_ax.texts).lower()
    plt.close(captured["figure"])

    confirmation_figures.plot_scaled_error(setting)
    scaled_ax = captured["figure"].axes[0]
    scaled_container = next(
        container
        for container in scaled_ax.containers
        if container.get_label() == "Mean and 95% CI"
    )
    scaled_line = scaled_container.lines[0]
    np.testing.assert_array_equal(scaled_line.get_ydata(), scaled)
    assert scaled_ax.get_title() == "Scaled asymptotic error"
    assert tuple(captured["figure"].get_size_inches()) == PAPER_FIGURE_SIZE
    plt.close(captured["figure"])


def test_plot_paper_figures_cli_uses_the_plotting_only_entry_point(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(
        publication_figures,
        "plot_publication_figures",
        lambda: called.append(True) or [],
    )
    monkeypatch.setattr(
        p0_simulation,
        "run_experiment",
        lambda _: (_ for _ in ()).throw(AssertionError("simulation entry point was called")),
    )

    assert cli.main(["p0", "plot"]) == 0
    assert called == [True]
