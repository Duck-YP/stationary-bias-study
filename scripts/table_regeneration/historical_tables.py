"""Saved historical table values; selectors never depend on target coverage."""
from __future__ import annotations

import math
from fractions import Fraction

BASE = "artifacts/canonical_paper_export/"
SUP = BASE + "supplementary/"
P2 = BASE + "original/p2_multidimensional_validation/artifacts/formal/"
P3 = BASE + "original/p3_multidimensional_fedavg_attribution/artifacts/formal/"


def unique(rows, **criteria):
    selected = [r for r in rows if all(str(r[k]) == str(v) for k, v in criteria.items())]
    if not selected:
        raise ValueError(f"Missing saved row: {criteria}")
    return selected


def consistent(rows, field):
    values = {r[field] for r in rows}
    if len(values) != 1:
        raise ValueError(f"Repeated fit records disagree in {field}: {values}")
    return rows[0][field]


def fixed(value, digits, scale=1):
    return f"{float(value) * scale:.{digits}f}"


def interval(row, low, high, digits, scale=1):
    return f"[{fixed(row[low], digits, scale)}, {fixed(row[high], digits, scale)}]"


def build_historical_tables(load_csv, load_json, load_text):
    tables = {}
    def put(number, headers, rows, sources, notes="", status="supported"):
        tables[number] = dict(headers=headers, rows=rows, sources=sources, notes=notes, status=status)

    fit_groups = [
        ("SCAFFOLD", "P", P2 + "p2-d2-coefficient-primary/fit_summary.csv", "B20_component", [2, 4]),
        ("SCAFFOLD", "S", P2 + "p2-d2-h4-small-step-confirmation/fit_summary.csv", "B20_component", [4]),
        ("FedAvg", "P", P3 + "p3-d2-coefficient-primary/fit_summary.csv", "B20_FA_component", [2, 4]),
        ("FedAvg", "S", P3 + "p3-d2-h4-small-step-confirmation/fit_summary.csv", "B20_FA_component", [4]),
        ("Paired difference", "P", P3 + "p3-d2-matched-attribution-primary/paired_fit_summary.csv", "B20_ctrl_component", [2, 4]),
        ("Paired difference", "S", P3 + "p3-d2-matched-attribution-h4-small-step-confirmation/paired_fit_summary.csv", "B20_ctrl_component", [4]),
    ]
    summary, intervals, fit_sources = [], [], []
    for algorithm, grid, path, target, hs in fit_groups:
        rows = load_csv(path)
        fit_sources.append(path)
        for h in hs:
            pairs = [unique(rows, H=h, coordinate=j) for j in (0, 1)]
            # P2 repeats identical fitted values at each input setting. Verify
            # equality before selecting one, rather than silently taking first.
            values = [{f: consistent(pair, f) for f in ("beta0", target, "simultaneous_ci_low", "simultaneous_ci_high")}
                      for pair in pairs]
            summary.append([algorithm, str(h), grid,
                            "(" + ", ".join(fixed(r[target], 7) for r in values) + ")",
                            "(" + ", ".join(fixed(r["beta0"], 7) for r in values) + ")"])
            digits = 7 if algorithm == "SCAFFOLD" else 10
            intervals.append([algorithm, str(h), grid, *[interval(r, "simultaneous_ci_low", "simultaneous_ci_high", digits) for r in values]])
    put(2, ["Study", "H", "Grid", "Target vector", "Estimated intercept vector"], summary, fit_sources,
        "Saved intercepts/targets; seven decimals. No regression is executed.")
    put(11, ["Study", "H", "Grid", "Coordinate 1 interval", "Coordinate 2 interval"], intervals, fit_sources,
        "Saved simultaneous interval endpoints; SCAFFOLD seven decimals, FedAvg/difference ten decimals.")

    path = SUP + "fitted_coefficients.csv"
    fits = load_csv(path)
    control = []
    for h in (2, 4, 8):
        for j in (0, 1):
            r, = unique(fits, experiment="E1b", H=h, coordinate=j, window="primary", term="0")
            control.append([str(h), str(j + 1), fixed(r["estimate"], 8), fixed(r["target"], 8),
                            interval(r, "ci_lower", "ci_upper", 8)])
    put(3, ["H", "Coordinate", "Estimate", "Target", "Nominal interval"], control, [path],
        "Primary E1b intercepts; nominal stored intervals (not adjusted or bootstrap alternatives).")
    leading = []
    for h in (1, 2, 4, 8):
        for algorithm in ("scaffold", "fedavg"):
            pair = [unique(fits, experiment="E1a", algorithm=algorithm, H=h, coordinate=j, window="primary", term="0")[0] for j in (0, 1)]
            leading.append([str(h), algorithm, fixed(pair[0]["estimate"], 6), interval(pair[0], "ci_lower", "ci_upper", 6),
                            fixed(pair[1]["estimate"], 6), interval(pair[1], "ci_lower", "ci_upper", 6)])
    put(15, ["H", "Algorithm", "Estimate 1", "Interval 1", "Estimate 2", "Interval 2"], leading, [path],
        "Primary E1a term 0; both algorithms and every H retained.")

    path = P3 + "p3-d2-matched-attribution-h4-diagnostic/scaling_summary.csv"
    rows = sorted(load_csv(path), key=lambda r: int(r["coordinate"]))
    diagnostic = [[str(int(r["coordinate"]) + 1), fixed(r["abs_e_Delta_at_delta_min"], 7),
                   fixed(r["abs_e_Delta_at_delta_max"], 7),
                   interval(r, "e_Delta_over_delta_min", "e_Delta_over_delta_max", 3), fixed(r["loglog_slope"], 3)] for r in rows]
    put(12, ["Coordinate", "Abs residual at minimum delta", "Abs residual at maximum delta", "Abs residual / delta range", "Saved log-log slope"], diagnostic, [path],
        "All values, including slopes, are read from the saved diagnostic; no trend is fitted.")
    path = P2 + "p2-d2-fixed-gamma-largeN-plateau/plateau_fit_summary.csv"
    rows = sorted(load_csv(path), key=lambda r: int(r["coordinate"]))
    put(13, ["Coordinate", "Simultaneous interval", "Intercept minus theory"],
        [[str(int(r["coordinate"]) + 1), interval(r, "simultaneous_ci_low", "simultaneous_ci_high", 7), fixed(r["beta0_minus_B20"], 7)] for r in rows], [path])
    path = P2 + "p2-d5-controlled-validation/fit_summary.csv"
    rows = load_csv(path)
    report_path = "docs/original/p2_multidimensional_validation/artifacts/formal/p2-d5-controlled-validation/p2_d5_controlled_validation_report.md"
    formatter_path = "src/stationary_bias/workstreams/p2_multidimensional_validation/formal_analysis.py"
    saved_report = load_text(report_path)
    formatter = load_text(formatter_path)
    if 'f"{value:.9g}"' not in formatter:
        raise ValueError("Historical nine-significant-digit report formatter is unavailable")
    five = []
    for h in (2, 4):
        for j in range(5):
            selected = unique(rows, H=h, coordinate=j)
            r = {f: consistent(selected, f) for f in ("beta0", "B20_component", "simultaneous_ci_low", "simultaneous_ci_high")}
            # The paper's CI endpoints use the saved report's .9g precision,
            # then ten decimal places. Verify that source representation;
            # do not infer the rounding rule from manuscript table values.
            endpoints = [format(float(r[f]), ".9g") for f in ("simultaneous_ci_low", "simultaneous_ci_high")]
            if any("| " + value + " |" not in saved_report for value in endpoints):
                raise ValueError("Five-dimensional interval is absent from the saved nine-significant-digit report")
            saved_interval = "[" + ", ".join(fixed(value, 10) for value in endpoints) + "]"
            five.append([str(h), str(j + 1), fixed(r["beta0"], 10), fixed(r["B20_component"], 10), saved_interval])
    put(14, ["H", "Coordinate", "Intercept", "Theory", "Simultaneous interval"], five, [path, report_path, formatter_path],
        "Intercepts and targets use raw saved fits at ten decimals. CI endpoints preserve the archived report's documented .9g precision, then display ten decimals; each formatted endpoint is verified in the saved report. No fitting or manuscript-number substitution.")

    path = SUP + "full_results.csv"
    results = load_csv(path)
    gamma_base = max(float(r["gamma"]) for r in results if r["regime"] == "R0")
    policy = []
    for h, ratio in ((4, 1.), (4, .5), (4, .25), (2, 1.)):
        pair = [next(r for r in results if r["regime"] == "R0" and r["N"] == "32" and r["H"] == str(h)
                     and r["algorithm"] == a and math.isclose(float(r["gamma"]) / gamma_base, ratio)) for a in ("scaffold", "fedavg")]
        policy.append([f"H={h}; gamma/base={Fraction(ratio)}", *[fixed(r["signed_projection"], 4, 1000) for r in pair],
                       *[fixed(r["raw_variance_trace"], 4, 1000) for r in pair]])
    put(5, ["Setting", "Signed projection S x1000", "Signed projection F x1000", "Raw variance S x1000", "Raw variance F x1000"], policy, [path])
    allocation = []
    for regime in ("R0", "R1", "R2"):
        for n in (8, 32, 128):
            for algorithm in ("scaffold", "fedavg"):
                selected = [r for r in results if r["regime"] == regime and int(r["N"]) == n and r["H"] == "4"
                            and r["algorithm"] == algorithm and "allocation" in r["roles"].split(";")
                            and math.isclose(float(r["gamma"]), gamma_base)]
                r, = selected
                allocation.append([regime, str(n), algorithm,
                                   fixed(r["signed_projection"], 6) if regime != "R0" else "",
                                   interval(r, "ci_lower", "ci_upper", 6) if regime != "R0" else "",
                                   fixed(r["total_parameter_MSE"], 4, 1000), fixed(r["heldout_log_loss"], 6)])
    put(21, ["Regime", "N", "Algorithm", "Signed projection", "Nominal interval", "Raw MSE x1000", "Test loss"], allocation, [path],
        "Same cells as the two paper subtables, in normalized long form. R0 projections are deliberately blank because this table reports only R0 MSE/loss.")

    path = P3 + "p3-d2-coefficient-primary/run_summary.csv"
    rows = load_csv(path)
    discrepancies = []
    # The four failures are the published diagnostic selection, not a new
    # target-inclusion screen. Both algorithms/estimators retain their source.
    failed = [r for r in rows if r["estimator"] == "direct_sample_mean" and r["direct_balance_agreement_pass"] == "False"]
    for direct in sorted(failed, key=lambda r: (int(r["H"]), int(r["N"]), int(r["coordinate"]))):
        balance, = unique(rows, run_id=direct["run_id"], coordinate=direct["coordinate"], estimator="stationary_mean_balance")
        difference = abs(float(direct["b_component"]) - float(balance["b_component"]))
        discrepancies.append([direct["H"], direct["N"], str(int(direct["coordinate"]) + 1),
                              fixed(balance["C_component"], 7), fixed(direct["C_component"], 6), fixed(difference, 8), "UNAVAILABLE", direct["seed"]])
    assert len(discrepancies) == 4
    put(18, ["H", "N", "Coordinate", "Balance coefficient", "Direct coefficient", "Absolute mean difference", "3 x combined SE", "Source seed"], discrepancies, [path],
        "Partial: saved per-run summaries supply coefficients and means, but not the original per-run combined-SE threshold. No uncertainty is recomputed. H=4,N=16,j=2 formats to -0.1080237 from the saved value; the paper displays -0.1080240, consistent with six-place rounding followed by a trailing zero, but no saved formatting rule establishes that history.", "partial")
    return tables
