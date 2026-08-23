import pandas as pd

from stationary_bias.objectives import MAIN_OBJECTIVE
from stationary_bias.result_tables import build_negative_control_audit
from stationary_bias.theoretical_bias import (
    b20_control,
    b20_local,
    b20_total,
    leading_bias_coefficient,
    normalize_bias,
)


def test_h1_coefficient_identity_keeps_nonzero_leading_bias() -> None:
    assert b20_local(1) == 0.0
    assert b20_control(1) == 0.0
    assert b20_total(1) == 0.0
    B10 = leading_bias_coefficient(MAIN_OBJECTIVE.a, MAIN_OBJECTIVE.tau, 1.0)
    assert B10 != 0.0
    gamma = 1.0 / 24.0
    N = 24
    b = 0.001
    observed = normalize_bias(
        b,
        gamma=gamma,
        N=N,
        a=MAIN_OBJECTIVE.a,
        tau=MAIN_OBJECTIVE.tau,
        sigma2=1.0,
    )
    assert observed == (b - B10 * gamma / N) / gamma**2


def _synthetic_frames(
    *,
    control_name: str = "no_nonlinear_conversion",
    direct_low: float,
    direct_high: float,
    validity: str = "VALID",
    frozen_status: str = "PASS",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    objective = "quadratic" if control_name == "no_nonlinear_conversion" else "nonlinear_main"
    tau = 0.0 if objective == "quadratic" else 0.5
    H = 1 if control_name == "h1_boundary_sanity" else 2
    setting = pd.DataFrame(
        [
            {
                "experiment": "p3c",
                "control_name": control_name,
                "objective": objective,
                "noise": "rademacher",
                "gamma": 1.0 / 24.0,
                "N": 24,
                "H": H,
                "b_direct_mean": (direct_low + direct_high) / 2.0,
                "b_direct_ci_low": direct_low,
                "b_direct_ci_high": direct_high,
                "b_balance_mean": 0.0,
                "b_balance_ci_low": 0.0,
                "b_balance_ci_high": 0.0,
                "C_mean": 0.0,
                "C_ci_low": -0.01,
                "C_ci_high": 0.01,
                "estimator_agreement_status": "pass",
                "stationarity_status": "pass",
                "overall_validity": validity,
            }
        ]
    )
    run = pd.DataFrame(
        [
            {
                "experiment": "p3c",
                "control_name": control_name,
                "gamma": 1.0 / 24.0,
                "N": 24,
                "a": 1.0,
                "tau": tau,
                "sigma2": 1.0,
                "last_batch_max_abs_x": 0.0,
            }
        ]
    )
    frozen = pd.DataFrame(
        [
            {
                "control_name": control_name,
                "gamma": 1.0 / 24.0,
                "N": 24,
                "H": H,
                "status": frozen_status,
            }
        ]
    )
    return run, setting, frozen


def test_quadratic_balance_zero_cannot_cause_automatic_pass() -> None:
    frames = _synthetic_frames(direct_low=0.1, direct_high=0.2)
    audit = build_negative_control_audit(*frames)
    assert bool(audit.iloc[0]["balance_is_structurally_zero"])
    assert audit.iloc[0]["audit_status"] == "FLAG"


def test_quadratic_valid_direct_ci_containing_zero_passes() -> None:
    frames = _synthetic_frames(direct_low=-0.1, direct_high=0.1)
    audit = build_negative_control_audit(*frames)
    assert bool(audit.iloc[0]["direct_ci_contains_zero"])
    assert audit.iloc[0]["audit_status"] == "PASS"


def test_invalid_setting_cannot_pass_direct_audit() -> None:
    frames = _synthetic_frames(
        direct_low=-0.1, direct_high=0.1, validity="INVALID_STATIONARITY"
    )
    audit = build_negative_control_audit(*frames)
    assert audit.iloc[0]["audit_status"] == "FLAG"


def test_h1_audit_uses_boundary_sanity_semantics_only() -> None:
    frames = _synthetic_frames(
        control_name="h1_boundary_sanity",
        direct_low=-0.1,
        direct_high=0.1,
        frozen_status="PASS",
    )
    audit = build_negative_control_audit(*frames)
    assert audit.iloc[0]["audit_status"] == "SANITY_FLAG"
    assert audit.iloc[0]["audit_status"] not in {"PASS", "FAIL"}
    assert audit.iloc[0]["B10"] != 0.0
