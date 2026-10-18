"""Redraw seven active panels from immutable saved CSVs, never simulate or fit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FormatStrFormatter, NullLocator, MaxNLocator

import figure_style as style

FIELDS = [
    "panel_id", "record_type", "source_file", "source_sha256", "source_row", "row_id",
    "coordinate", "display_coordinate", "algorithm", "H", "N", "m", "gamma",
    "x_column", "y_column", "ci_low_column", "ci_high_column", "target_column",
    "x_original", "y_original", "ci_low_original", "ci_high_original", "target_original",
    "x_display", "y_display", "ci_low_display", "ci_high_display", "target_display",
    "x_scale", "y_scale", "x_transform", "y_transform", "beta0", "beta1",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Records:
    def __init__(self, root, out):
        self.root = root
        self.out = out
        self.rows = {}
        self.inputs = {}

    def read(self, relative):
        path = self.root / relative
        self.inputs[relative] = {"sha256": sha(path), "bytes": path.stat().st_size}
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return [{**r, "_source_file": relative, "_source_row": i} for i, r in enumerate(csv.DictReader(handle), 1)]

    def add(self, panel, kind, row, *, x, y_column, x_column="", low="", high="", target="", y=None,
            scale=1, transform="identity", display_x=None, beta=False):
        val = lambda col: float(row[col]) if col and row.get(col, "") != "" else ""
        raw_y = val(y_column) if y is None else y
        disp = lambda v: "" if v == "" else (abs(v) if transform == "abs" else v) * scale
        rec = {"panel_id": panel, "record_type": kind, "source_file": row["_source_file"],
               "source_sha256": self.inputs[row["_source_file"]]["sha256"], "source_row": row["_source_row"],
               "row_id": row.get("setting_id", row.get("cell_id", f"H={row.get('H','4')};coordinate={row.get('coordinate','')}")),
               "coordinate": row.get("coordinate", ""),
               "display_coordinate": int(row["coordinate"])+1 if "coordinate" in row else "",
               "algorithm": row.get("algorithm", "matched"), "H": row.get("H", ""),
               "N": row.get("N", ""), "m": row.get("m", ""), "gamma": row.get("gamma", ""),
               "x_column": x_column, "y_column": y_column, "ci_low_column": low, "ci_high_column": high,
               "target_column": target, "x_original": x, "y_original": raw_y,
               "ci_low_original": val(low), "ci_high_original": val(high), "target_original": val(target),
               "x_display": x if display_x is None else display_x, "y_display": disp(raw_y),
               "ci_low_display": disp(val(low)), "ci_high_display": disp(val(high)), "target_display": disp(val(target)),
               "x_scale": 1, "y_scale": scale, "x_transform": "identity" if display_x is None else "categorical",
               "y_transform": transform if scale == 1 else "scale", "beta0": val("beta0") if beta else "",
               "beta1": val("beta1") if beta else ""}
        self.rows.setdefault(panel, []).append(rec)
        return rec

    def write(self):
        data = self.out / "data"
        data.mkdir(parents=True, exist_ok=True)
        for panel, rows in self.rows.items():
            with (data / f"{panel}.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
        provenance = {"inputs": self.inputs, "panels": {p: len(r) for p, r in self.rows.items()},
                      "method": "Read saved records and saved fit coefficients only; no simulations, bootstrap or regression.",
                      "display": {"R0_y": "signed_projection * 1000, including nominal CI endpoints",
                                  "R0_x": "Categorical index for N=8,32,128; fixed +/-0.045 marker dodge only",
                                  "log_y": "abs(saved e_Delta); nine saved points per coordinate; no new fit"},
                      "font": {"text": "Latin Modern Roman via TeX T1/lmodern; no fallback permitted",
                               "requested_tick_TeX_pt": style.TICK_FONT,
                               "requested_legend_TeX_pt": style.LEGEND_FONT,
                               "requested_label_TeX_pt": style.LABEL_FONT,
                               "units_note": "usetex converts these TeX point requests to PDF points; FINAL_FONT_AUDIT measures actual sizes"},
                      "physical": {"textwidth_TeX_pt": style.TEXTWIDTH_TEX_PT,
                                   "paired_width_inch": style.HALF_WIDTH_INCH, "R0_width_inch": style.R0_WIDTH_INCH,
                                   "TeX_pt_per_inch": 72.27, "PDF_pt_per_inch": 72},
                      "single_axes_asserted": True}
        (data / "provenance.json").write_text(json.dumps(provenance, indent=2)+"\n", encoding="utf-8")


def errors(ax, records, **kwargs):
    x = [r["x_display"] for r in records]
    y = np.array([r["y_display"] for r in records])
    lo = np.array([r["ci_low_display"] for r in records])
    hi = np.array([r["ci_high_display"] for r in records])
    if np.any(lo > y) or np.any(hi < y):
        raise AssertionError("Source CI does not contain its saved estimate")
    return ax.errorbar(x, y, yerr=np.vstack((y-lo, hi-y)), capsize=2.7, capthick=1.0,
                       elinewidth=1.1, **kwargs)


def matched(db, group, H, panel):
    settings = db.read(f"inputs/{group}/paired_setting_summary.csv")
    fits = db.read(f"inputs/{group}/paired_fit_summary.csv")
    fig, ax = style.make_axes()
    for coord in (0, 1):
        rows = sorted((r for r in settings if int(r["H"]) == H and int(r["coordinate"]) == coord), key=lambda r: float(r["delta"]))
        fit, = [r for r in fits if int(r["H"]) == H and int(r["coordinate"]) == coord]
        expected = 4 if group == "p3_smallstep" else 5
        assert len(rows) == expected
        coords = style.COORDINATES[coord]
        points = [db.add(panel, "point", r, x=float(r["delta"]), x_column="delta", y_column="D_mean",
                         low="simultaneous_ci_low", high="simultaneous_ci_high", target="B20_ctrl_component") for r in rows]
        errors(ax, points, **{**coords, "linestyle": "none"}, markersize=4.6, zorder=4)
        intercept = db.add(panel, "intercept", fit, x=0., y_column="beta0", low="simultaneous_ci_low",
                           high="simultaneous_ci_high", target="B20_ctrl_component", beta=True)
        errors(ax, [intercept], color=coords["color"], marker="D", markerfacecolor="white",
               markeredgewidth=1.1, linestyle="none", markersize=4.8, zorder=5)
        fitpoints = [db.add(panel, "fit_curve", fit, x=x, y_column="beta0+beta1*x",
                            y=float(fit["beta0"])+float(fit["beta1"])*x, beta=True)
                     for x in [0., *[float(r["delta"]) for r in rows]]]
        ax.plot([r["x_display"] for r in fitpoints], [r["y_display"] for r in fitpoints],
                color=coords["color"], linestyle=":", linewidth=1.35, zorder=2)
        target = db.add(panel, "target", fit, x=0., y_column="B20_ctrl_component", target="B20_ctrl_component", beta=True)
        ax.axhline(target["y_display"], color=coords["color"], linestyle="--", linewidth=1.2, zorder=1)
    ax.axvline(0, color="#aaaaaa", linewidth=0.6)
    ax.set_xlim(-max(float(r["delta"]) for r in rows)*0.065, max(float(r["delta"]) for r in rows)*1.055)
    ax.xaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 2.5, 5, 10]))
    ax.yaxis.set_major_locator(MaxNLocator(5, steps=[1, 2, 5, 10]))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f" if group != "p3_smallstep" else "%.3f"))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    ax.set_xlabel(r"$\delta = \gamma + 1/N$")
    ax.set_ylabel("Matched coefficient estimate")
    style.coordinate_legend(fig)
    style.save_panel(fig, db.out / panel)


def plateau(db, coord, panel):
    settings = db.read("inputs/p2_plateau/setting_summary.csv")
    fits = db.read("inputs/p2_plateau/plateau_fit_summary.csv")
    curves = db.read("inputs/p2_plateau/plateau_fit_curve.csv")
    rows = sorted((r for r in settings if r["estimator"] == "stationary_mean_balance" and int(r["coordinate"]) == coord), key=lambda r: float(r["inverse_N"]))
    fit, = [r for r in fits if int(r["coordinate"]) == coord]
    curve = sorted((r for r in curves if int(r["coordinate"]) == coord), key=lambda r: float(r["inverse_N"]))
    assert len(rows) == len(curve) == 5
    fig, ax = style.make_axes(legend_rows=2)
    coords = style.COORDINATES[coord]
    points = [db.add(panel, "point", r, x=float(r["inverse_N"]), x_column="inverse_N", y_column="C_mean",
                     low="simultaneous_ci_low", high="simultaneous_ci_high", target="B20_component") for r in rows]
    errors(ax, points, color=coords["color"], marker=coords["marker"], markerfacecolor=coords["markerfacecolor"],
           linestyle="none", label="Observations", zorder=4)
    intercept = db.add(panel, "intercept", fit, x=0., y_column="beta0", low="simultaneous_ci_low",
                       high="simultaneous_ci_high", target="B20_component", beta=True)
    errors(ax, [intercept], color=coords["color"], marker="D", markerfacecolor="white", markeredgewidth=1.1,
           linestyle="none", label="Fitted intercept", zorder=5)
    fitpoints = [db.add(panel, "fit_curve", fit, x=0., y_column="beta0", beta=True)]
    fitpoints += [db.add(panel, "fit_curve", r, x=float(r["inverse_N"]), x_column="inverse_N", y_column="fitted_value") for r in curve]
    ax.plot([r["x_display"] for r in fitpoints], [r["y_display"] for r in fitpoints],
            color=coords["color"], linestyle=":", linewidth=1.35, label="Finite-grid fit", zorder=2)
    target = db.add(panel, "target", fit, x=0., y_column="B20_component", target="B20_component", beta=True)
    ax.axhline(target["y_display"], color="#444444", linestyle="--", linewidth=1.2, label="Joint-limit target", zorder=1)
    ax.axvline(0, color="#aaaaaa", linewidth=0.6)
    ax.set_xlim(-0.008, .132)
    ax.set_xticks([0, .04, .08, .12])
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    # Shared physical range relative to each coordinate's theory reference.
    ax.set_ylim(target["y_display"]-.0018, target["y_display"]+.0072)
    ax.yaxis.set_major_locator(MaxNLocator(5))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    ax.set_xlabel(r"Inverse client count $1/N$")
    ax.set_ylabel("Normalized mean-bias remainder")
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.52, .985), ncol=2, frameon=False,
               handlelength=1.5, columnspacing=.7, handletextpad=.45, labelspacing=.4)
    style.save_panel(fig, db.out / panel)


def residual(db, panel):
    rows = db.read("inputs/p3_diagnostic/pointwise_diagnostics.csv")
    db.read("inputs/p3_diagnostic/scaling_summary.csv")
    fig, ax = style.make_axes(legend_rows=1)
    for coord in (0, 1):
        selected = sorted((r for r in rows if int(r["coordinate"]) == coord), key=lambda r: float(r["delta"]))
        assert len(selected) == 9
        points = [db.add(panel, "point", r, x=float(r["delta"]), x_column="delta", y_column="e_Delta", transform="abs") for r in selected]
        ax.plot([r["x_display"] for r in points], [r["y_display"] for r in points], **style.COORDINATES[coord])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(.0085, .195)
    ax.set_ylim(.00125, .034)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_minor_locator(NullLocator())
        axis.set_major_formatter(FormatStrFormatter("%.3g"))
    ax.xaxis.set_major_locator(FixedLocator([.01, .02, .05, .1]))
    ax.yaxis.set_major_locator(FixedLocator([.002, .005, .01, .02]))
    ax.set_xlabel(r"$\delta = \gamma + 1/N$")
    ax.set_ylabel("Absolute matched residual")
    style.coordinate_legend(fig, with_fit=False)
    style.save_panel(fig, db.out / panel)


def real_allocation(db, panel):
    allrows = db.read("inputs/supplement/E3_allocation_signed_projection.csv")
    rows = [r for r in allrows if r["regime"] == "R0" and "allocation" in r["roles"].split(";")
            and int(r["H"]) == 4 and int(r["N"]) in (8, 32, 128)
            and math.isclose(float(r["gamma"]), .1/.51, rel_tol=0, abs_tol=1e-15)]
    assert len(rows) == 6
    assert {(int(r["N"]), int(r["m"])) for r in rows} == {(8, 32), (32, 8), (128, 2)}
    fig, ax = style.make_axes(real=True, legend_rows=1)
    for algo in ("scaffold", "fedavg"):
        ordered = sorted((r for r in rows if r["algorithm"] == algo), key=lambda r: int(r["N"]))
        points = [db.add(panel, "point", r, x=int(r["N"]), x_column="N", y_column="signed_projection",
                         low="ci_lower", high="ci_upper", scale=1000., display_x=i) for i, r in enumerate(ordered)]
        # Dodge is a visual separation at categorical locations, not another N value.
        shifted = [{**r, "x_display": r["x_display"]+(-.045 if algo == "scaffold" else .045)} for r in points]
        errors(ax, shifted, **style.ALGORITHMS[algo], label="SCAFFOLD" if algo == "scaffold" else "FedAvg")
    ax.set_xlim(-.22, 2.22)
    ax.set_xticks([0, 1, 2], ["(8, 32)", "(32, 8)", "(128, 2)"])
    ax.set_ylim(0., 3.9)
    ax.set_yticks([0., 1., 2., 3.])
    ax.set_xlabel(r"Client/minibatch allocation $(N,m)$")
    ax.set_ylabel("Signed projected mean displacement\n" + r"($\times 1000$)")
    fig.legend(*ax.get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(.54, .985),
               ncol=2, frameon=False, handlelength=1.6, handletextpad=.5, columnspacing=1.2)
    style.save_panel(fig, db.out / panel)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True,
                        help="Frozen plotting snapshot root containing the ten inputs/*.csv files")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    db = Records(args.input_root, args.output)
    with plt.rc_context(style.RC):
        matched(db, "p3_primary", 2, "hist_matched_H2")
        matched(db, "p3_primary", 4, "hist_matched_H4")
        plateau(db, 0, "hist_fixed_gamma_coord1")
        plateau(db, 1, "hist_fixed_gamma_coord2")
        real_allocation(db, "real_R0_allocation")
        matched(db, "p3_smallstep", 4, "hist_H4_smallstep")
        residual(db, "hist_H4_loglog_residual")
    db.write()
    print(json.dumps({"status": "DRAWN_FROM_SAVED_RECORDS", "panels": len(db.rows), "output": str(args.output)}))


if __name__ == "__main__":
    main()
