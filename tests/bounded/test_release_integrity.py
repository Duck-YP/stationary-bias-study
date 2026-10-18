import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_current_manuscript_and_complete_saved_evidence():
    spec = importlib.util.spec_from_file_location("release_validation", ROOT / "scripts/validate_release.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.validate()
    assert result["status"] == "PASS"
    assert result["current_manuscript_copy_verified"]
    if result["current_manuscript_version"] == "20261018_V2":
        assert result["current_pdf_unchanged_from_previous"]
        assert result["current_pdf_source_tex_correspondence_verified"] is False
        assert result["current_pdf_matches_current_tex"] is False
        assert result["current_retained_local_files"] == 1
    elif result["current_manuscript_version"] == "20261018_FIGURE_LAYOUT":
        assert result["current_pdf_unchanged_from_previous"] is False
        assert result["current_pdf_source_tex_correspondence_verified"] is True
        assert result["current_pdf_matches_current_tex"] is True
        assert result["current_retained_local_files"] == 1
        assert result["current_layout_receipts_verified"]
        assert result["current_final_font_panels"] == result["current_active_graphics"] == 9
        assert result["current_minimum_panel_font_TeX_pt"] >= 9.-.005
        assert result["current_e4_saved_column_checks"] == 210
    assert result["targeted_configurations"] == 24
    assert result["targeted_paired_runs"] == 288
    assert result["targeted_primary_summaries"] == 36
    assert result["targeted_estimator_grid_families"] == 4
    assert result["scientific_recomputation"] == "NONE"
    assert "not a build" in result["historical_build_receipt_scope"]


def test_closed_form_coefficient_decomposition():
    from stationary_bias.core.theory.one_dimensional import b20_control, b20_local, b20_total
    for h in (1, 2, 4, 8):
        assert abs(b20_control(h) + b20_local(h) - b20_total(h)) < 1e-14


def test_supplementary_lyapunov_and_matched_coefficients():
    import numpy as np
    from scipy.linalg import solve_continuous_lyapunov
    from study.model import A, C, theory
    s = solve_continuous_lyapunov(A, C)
    np.testing.assert_allclose(A @ s + s @ A, C, atol=1e-14, rtol=0)
    for h in (1, 2, 4, 8):
        result = theory(h)
        np.testing.assert_allclose(np.array(result["B20_scaf"]) - result["B20_fa"],
                                   result["B20_ctrl"], atol=1e-14, rtol=0)
    assert theory(4)["kappa"] / theory(2)["kappa"] == 3.5
