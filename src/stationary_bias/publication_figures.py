"""Plot only the publication panels from already saved numerical outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .confirmation_figures import plot_C, plot_scaled_error
from .figures import plot_client_count_scaling, plot_coefficient_convergence
from .project_io import RESULT_ROOT
from .small_step_confirmation import CONFIRMATION_RESULT_ROOT


def plot_publication_figures() -> list[Path]:
    """Rebuild the requested paper panels without simulation or reanalysis."""

    original_path = RESULT_ROOT / "setting_summary.csv"
    small_step_path = CONFIRMATION_RESULT_ROOT / "setting_summary.csv"
    for path in (original_path, small_step_path):
        if not path.exists():
            raise FileNotFoundError(f"Required saved plotting input is missing: {path}")

    original = pd.read_csv(original_path, keep_default_na=False)
    small_step = pd.read_csv(small_step_path, keep_default_na=False)
    return [
        plot_coefficient_convergence(original, 2),
        plot_coefficient_convergence(original, 4),
        plot_client_count_scaling(original),
        plot_C(small_step),
        plot_scaled_error(small_step),
    ]
