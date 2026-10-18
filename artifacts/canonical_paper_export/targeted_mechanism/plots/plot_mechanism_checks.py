"""Single-panel vector-PDF figures from the frozen targeted-study CSVs.

No refitting, exclusions, interval recomputation, or outcome-dependent selection.
Use the Python 3.12 executable recorded in ../ENVIRONMENT.json; packages are
loaded from supplementary_study/.deps. --mock-layout writes ONLY to scratch/.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
REPO = STUDY.parent
sys.path.insert(0, str(REPO / "supplementary_study/.deps"))
os.environ.setdefault("MPLCONFIGDIR", str(HERE / "scratch/mplconfig"))
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.text import Text

OBS = ["SCAFFOLD", "FedAvg", "difference"]
DISPLAY = {"SCAFFOLD": "SCAFFOLD", "FedAvg": "FedAvg", "difference": "SCAFFOLD - FedAvg"}
SHORT = {"SCAFFOLD": "SCAFFOLD", "FedAvg": "FedAvg", "difference": "Difference"}
CONDITIONS = ["rho_minus_symmetric", "rho_zero_symmetric", "rho_plus_symmetric", "rho_plus_asymmetric"]
RHO = dict(zip(CONDITIONS, [-.25, 0., .25, .25]))
BLUE, ORANGE, TEAL = "#205887", "#B06224", "#1F827A"
TARGET, GRID = "#222222", "#DDE2E7"
FIGSIZE = (3.20, 3.30)


def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.titlesize": 10.5, "axes.labelsize": 10.5,
        "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10,
        "axes.linewidth": .7, "lines.linewidth": 1.2, "lines.markersize": 4.5,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.spines.top": False, "axes.spines.right": False,
        "savefig.facecolor": "white", "figure.facecolor": "white",
        "axes.unicode_minus": True, "text.usetex": False,
    })


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def f(row, key):
    value = float(row[key])
    if not np.isfinite(value):
        raise ValueError(f"Nonfinite {key}: {row}")
    return value


def pick(rows, **keys):
    found = [r for r in rows if all(str(r.get(k)) == str(v) for k, v in keys.items())]
    if len(found) != 1:
        raise ValueError(f"Expected exactly one row for {keys}; got {len(found)}")
    return found[0]


def check_inputs(primary, fits, grid, protocol):
    if len(primary) != 36:
        raise ValueError(f"Expected all 36 primary-family rows, got {len(primary)}")
    if any(r["estimator"] != "balance" or r["grid"] != "full" for r in primary):
        raise ValueError("Primary-family file does not match the frozen primary estimator/grid")
    for c in CONDITIONS:
        for obs in OBS:
            for j in (1, 2):
                for subset in ("full", "omit_largest_gamma"):
                    pick(fits, kind="intercept", comparison=c, observable=obs,
                         coordinate=j, estimator="balance", grid=subset)
                for cell in (x for x in protocol["cells"] if x["condition"] == c):
                    candidates = [r for r in grid if r["condition"] == c and r["observable"] == obs
                        and int(r["coordinate"]) == j and r["estimator"] == "balance"
                        and int(r["N"]) == cell["N"] and float(r["gamma"]) == cell["gamma"]]
                    if len(candidates) != 1 or int(candidates[0]["count"]) != len(protocol["production_seeds"]):
                        raise ValueError(f"Incomplete grid: {c}, {obs}, coordinate {j}, {cell}")
    for r in primary:
        r2 = pick(fits, **{k:r[k] for k in ("kind", "comparison", "observable", "coordinate", "estimator", "grid")})
        for key in ("estimate", "target", "simultaneous_lower", "simultaneous_upper"):
            if f(r, key) != f(r2, key):
                raise ValueError(f"Primary/all-fit CSV disagreement: {key}")
        if not f(r, "simultaneous_lower") <= f(r, "estimate") <= f(r, "simultaneous_upper"):
            raise ValueError("Reversed or off-center simultaneous interval")


def canvas(title, ylabel, mock):
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_axes([.29, .31, .68, .48])
    # Figure-level title avoids renderer-specific automatic repositioning when
    # a scientific multiplier and a two-line mathematical title coexist.
    fig.text(.63,.97,title,ha="center",va="top",fontsize=10.5,linespacing=1.15)
    ax.set_ylabel(ylabel, labelpad=6)
    ax.grid(axis="y", color=GRID, lw=.55, zorder=0)
    ax.axhline(0, color="#A0A7AF", lw=.65, zorder=1)
    ax.tick_params(length=3, width=.6)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(-3,3), useOffset=False, useMathText=True)
    if mock:
        fig.text(.5, .50, "MOCK LAYOUT", transform=fig.transFigure, ha="center",
                 va="center", fontsize=19, rotation=28, alpha=.15, color="crimson", zorder=100)
    return fig, ax


def interval(ax, x, row, sensitivity=False):
    estimate, lo, hi = (f(row, k) for k in ("estimate", "simultaneous_lower", "simultaneous_upper"))
    color = ORANGE if sensitivity else BLUE
    ax.errorbar(x, estimate, yerr=np.array([[estimate-lo], [hi-estimate]]),
                fmt="s" if sensitivity else "o", color=color, ecolor=color,
                markerfacecolor="white" if sensitivity else color,
                capsize=2.5, capthick=1, elinewidth=1.2, zorder=4)


def limits(rows, include=()):
    values = list(include) + [f(r,k) for r in rows for k in ("simultaneous_lower", "simultaneous_upper", "target")]
    maximum = max(abs(v) for v in values) or .01
    return -1.18*maximum, 1.18*maximum


def fit_legend(fig, with_band=False):
    handles = [Line2D([], [], color=BLUE, marker="o", ls="none", label="Full grid"),
               Line2D([], [], color=ORANGE, marker="s", mfc="white", ls="none", label="Restricted grid"),
               Line2D([], [], color=TARGET, marker="x", ls="none", label="Theory target")]
    if with_band:
        handles.append(Patch(fc="#E1EFE8", ec="none", label="Resolution band"))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.54,.015 if not with_band else .005),
               ncol=2, frameon=False, handletextpad=.35, columnspacing=.65, borderaxespad=0)


def save(fig, stem, destination, record, caption, mock):
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    bounds=fig.bbox
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text():
            continue
        box=text.get_window_extent(renderer)
        if box.x0 < -.5 or box.y0 < -.5 or box.x1 > bounds.width+.5 or box.y1 > bounds.height+.5:
            raise RuntimeError(f"Clipped text in {stem}: {text.get_text()!r}; bounds={box.bounds}")
    path=destination / (stem+".pdf")
    destination.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, metadata={"Title":stem.replace("_", " "), "Author":"Targeted mechanism study",
        "Subject":"MOCK LAYOUT ONLY" if mock else "Prespecified coefficient summaries; sampling uncertainty only"})
    qa_dir = HERE / "scratch" / ("mock_qa" if mock else "final_qa")
    qa_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(qa_dir / (stem+".png"), dpi=160)
    record.append({"file":str(path.relative_to(HERE)),"caption":caption,
                   "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                   "single_axes":len(fig.axes)==1, "native_width_inches":FIGSIZE[0],
                   "minimum_font_pt":10,"mock":mock})
    plt.close(fig)


def covariance_controls(fits, destination, record, mock):
    for obs in OBS:
        for j in (1,2):
            fig, ax = canvas(f"{DISPLAY[obs]}\nCoordinate {j}", "Coefficient intercept", mock)
            plotted=[]
            for i,c in enumerate(CONDITIONS[:3]):
                for subset,shift in (("full",-.09),("omit_largest_gamma",.09)):
                    row=pick(fits,kind="intercept",comparison=c,observable=obs,coordinate=j,
                             estimator="balance",grid=subset)
                    plotted.append(row)
                    interval(ax,i+shift,row,sensitivity=subset!="full")
                ax.plot(i, f(plotted[-1],"target"), marker="x", color=TARGET, ms=6, mew=1.4, zorder=5)
            ax.set_xticks(range(3),[r"$-1/4$",r"$0$",r"$+1/4$"])
            ax.set_xlabel(r"Covariance parameter $\rho$", labelpad=5)
            ax.set_xlim(-.45,2.45); ax.set_ylim(*limits(plotted,include=[0]))
            fit_legend(fig)
            caption=(f"{DISPLAY[obs]}, coordinate {j}: unconstrained intercepts of the normalized balance observable "
                "under symmetric noise at the three covariance interventions. Filled circles use the full frozen grid; "
                "open squares omit only the largest step size. Whiskers are approximate 95% simultaneous sampling "
                "intervals for each analysis's 36-summary family; crosses are analytical targets. The intervals do not "
                "cover finite-grid remainder or burn-in error. The null is a normalized coefficient null, not a zero mean.")
            save(fig,f"covariance_controls_{obs.lower()}_coordinate_{j}",destination,record,caption,mock)


def matched_laws(fits, protocol, destination, record, mock):
    for j in (1,2):
        fig,ax=canvas(f"Matched noise laws\nCoordinate {j}","Law coefficient difference",mock)
        ax.set_position([.29,.26,.68,.53])
        plotted=[]
        for i,obs in enumerate(OBS):
            band=float(protocol["practical_margins"][obs])
            ax.add_patch(Rectangle((i-.37,-band),.74,2*band,facecolor="#E1EFE8",edgecolor="none",zorder=0))
            for subset,shift in (("full",-.09),("omit_largest_gamma",.09)):
                row=pick(fits,kind="law_contrast",comparison="rho_plus_symmetric minus rho_plus_asymmetric",
                         observable=obs,coordinate=j,estimator="balance",grid=subset)
                plotted.append(row); interval(ax,i+shift,row,sensitivity=subset!="full")
            ax.plot(i,f(plotted[-1],"target"),marker="x",color=TARGET,ms=6,mew=1.4,zorder=5)
        ax.set_xticks(range(3),[SHORT[x] for x in OBS]); ax.set_xlim(-.45,2.45)
        ax.set_ylim(*limits(plotted,include=list(protocol["practical_margins"].values())))
        fit_legend(fig,with_band=True)
        caption=(f"Coordinate {j}: symmetric-minus-asymmetric fitted coefficient differences at rho=+1/4, "
            "where the two noise laws have identical population mean and covariance. Difference denotes the matched "
            "SCAFFOLD-minus-FedAvg observable. Whiskers are approximate 95% simultaneous intervals across the "
            "36-summary family. Full and prespecified restricted grids are both shown. Green bands mark the frozen "
            "practical resolution margins (0.011875, 0.0075, 0.004375); crosses mark zero joint-limit targets. "
            "Sampling intervals do not include deterministic grid remainder or burn-in error. This comparison is not "
            "an equivalence proof and does not rule out finite-N law dependence.")
        save(fig,f"covariance_matched_laws_coordinate_{j}",destination,record,caption,mock)


def grid_panels(grid, destination, record, mock):
    for obs in OBS:
        for j in (1,2):
            allrows=[r for r in grid if r["estimator"]=="balance" and r["observable"]==obs and int(r["coordinate"])==j]
            extent=max(abs(f(r,k)) for r in allrows for k in ("lower","upper","target")) or .01
            for c in CONDITIONS:
                law="Asymmetric" if c.endswith("asymmetric") else "Symmetric"
                rholabel={-.25:"-1/4",0.:"0",.25:"+1/4"}[RHO[c]]
                fig,ax=canvas(f"{DISPLAY[obs]}\n{law}, " + r"$\rho="+rholabel+"$"+f", coord. {j}","Normalized coefficient",mock)
                for n,color,marker in ((64,BLUE,"o"),(128,TEAL,"s")):
                    rows=sorted([r for r in allrows if r["condition"]==c and int(r["N"])==n],key=lambda r:f(r,"gamma"))
                    xs=np.log2([f(r,"gamma")*2048 for r in rows]); ys=np.array([f(r,"mean") for r in rows])
                    errors=np.array([[f(r,"mean")-f(r,"lower") for r in rows],[f(r,"upper")-f(r,"mean") for r in rows]])
                    ax.errorbar(xs+(-.035 if n==64 else .035),ys,yerr=errors,color=color,
                                marker=marker,mfc="white" if n==128 else color,lw=1,capsize=2,label=f"N = {n}")
                target=f(rows[0],"target")
                ax.axhline(target,color=TARGET,ls="--",lw=1,label="Analytical target")
                ax.set_xticks([0,1,2],["1/2048","1/1024","1/512"])
                ax.set_xlabel(r"Step size $\gamma$",labelpad=5)
                ax.set_xlim(-.23,2.23); ax.set_ylim(-1.18*extent,1.18*extent)
                fig.legend(*ax.get_legend_handles_labels(),loc="lower center",bbox_to_anchor=(.53,.005),
                           ncol=2,frameon=False,columnspacing=.7,handlelength=1.5,handletextpad=.4)
                caption=(f"{DISPLAY[obs]}, coordinate {j}, {law.lower()} noise, rho={rholabel}: all six frozen "
                    "grid cells are shown, with N=64 and N=128 separated visually. Whiskers are ordinary 95% "
                    "marginal Student-t intervals from 12 independent paired runs, not simultaneous intervals. "
                    "The horizontal dashed line is the joint-limit coefficient target. Y limits are shared across "
                    "all four conditions for each observable/coordinate. Connecting lines are visual guides, not fitted "
                    "rates. Two N values do not identify a convergence rate.")
                save(fig,f"grid_{c}_{obs.lower()}_coordinate_{j}",destination,record,caption,mock)


def mock_data(protocol):
    """Synthetic, deliberately imperfect layout fixtures; never paper data."""
    fits=[]; grid=[]
    scales={"SCAFFOLD":-.2375,"FedAvg":-.15,"difference":-.0875}
    for subset in ("full","omit_largest_gamma"):
        for c in CONDITIONS:
            for obs in OBS:
                for j in (1,2):
                    target=scales[obs]*RHO[c] if j==1 else 0.
                    bias=.007*(1+OBS.index(obs))*(1 if j==1 else -1)
                    est=target+bias+(.004 if subset!="full" else 0.)
                    half=.012*(1+OBS.index(obs))*(1.4 if subset!="full" else 1.)
                    fits.append(dict(kind="intercept",comparison=c,observable=obs,coordinate=j,estimator="balance",
                        grid=subset,target=target,estimate=est,simultaneous_lower=est-half,simultaneous_upper=est+half))
        for kind,comparison in (("law_contrast","rho_plus_symmetric minus rho_plus_asymmetric"),
                                ("signed_covariance_contrast","rho_plus_symmetric minus rho_minus_symmetric")):
            for obs in OBS:
                for j in (1,2):
                    target=scales[obs]*.5 if kind=="signed_covariance_contrast" and j==1 else 0.
                    est=target+.004*(1+OBS.index(obs)); half=.018*(1+OBS.index(obs))*(1.4 if subset!="full" else 1.)
                    fits.append(dict(kind=kind,comparison=comparison,observable=obs,coordinate=j,estimator="balance",
                        grid=subset,target=target,estimate=est,simultaneous_lower=est-half,simultaneous_upper=est+half))
    for cell in protocol["cells"]:
        for obs in OBS:
            for j in (1,2):
                target=scales[obs]*cell["rho"] if j==1 else 0.
                mean=target+.2/cell["N"]+2*cell["gamma"]
                half=.007*(1+OBS.index(obs))
                grid.append(dict(condition=cell["condition"],N=cell["N"],gamma=cell["gamma"],observable=obs,
                    coordinate=j,estimator="balance",target=target,mean=mean,lower=mean-half,upper=mean+half,count=12))
    return [r for r in fits if r["grid"]=="full"],fits,grid


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock-layout",action="store_true",help="Synthetic layout only; all outputs under scratch/")
    args=parser.parse_args()
    protocol=json.loads((STUDY/"PROTOCOL_FROZEN.json").read_text(encoding="utf-8"))
    input_paths=[STUDY/"results"/name for name in ("primary_family_36.csv","intercepts_and_contrasts.csv","full_grid.csv")]
    if args.mock_layout:
        primary,fits,grid=mock_data(protocol)
        destination=HERE/"scratch/mock_layout"
    else:
        missing=[str(p) for p in input_paths if not p.is_file()]
        if missing:
            raise SystemExit("Final plotting requires all real CSVs; no outputs generated. Missing: "+", ".join(missing))
        primary,fits,grid=[read_csv(p) for p in input_paths]
        destination=HERE/"main"
    check_inputs(primary,fits,grid,protocol)
    style(); record=[]
    covariance_controls(fits,destination,record,args.mock_layout)
    matched_laws(fits,protocol,destination,record,args.mock_layout)
    supplementary=destination/"supplementary" if args.mock_layout else HERE/"supplementary"
    grid_panels(grid,supplementary,record,args.mock_layout)
    if len(record)!=32 or not all(r["single_axes"] for r in record):
        raise RuntimeError("Unexpected panel count or subplot")
    manifests=destination if args.mock_layout else HERE
    manifest={"mock":args.mock_layout,"panel_count":len(record),"main_panel_count":8,
        "supplementary_panel_count":24,"protocol_sha256":hashlib.sha256((STUDY/"PROTOCOL_FROZEN.json").read_bytes()).hexdigest(),
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256":{} if args.mock_layout else {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths},
        "fonts":"DejaVu Sans embedded as TrueType; minimum 10 pt at native 3.2-inch width",
        "integration":"Keep panels at natural width, or at least 95% of natural width to retain minimum 9.5-point text. LaTeX handles side-by-side composition.",
        "selection":"All three symmetric covariance conditions, both coordinates, all three observables; all law contrasts; all balance grid cells. No selection by outcome.",
        "panels":record}
    (manifests/"FIGURE_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    text=["# Figure captions\n", "Synthetic layout fixtures only.\n" if args.mock_layout else "All panels are separate vector PDFs. Whiskers show sampling uncertainty only.\n"]
    for r in record:
        text.extend(["## "+r["file"]+"\n",r["caption"]+"\n"])
    (manifests/"FIGURE_CAPTIONS.md").write_text("\n".join(text),encoding="utf-8")
    print(json.dumps({"mock":args.mock_layout,"panels":len(record),"destination":str(destination)},indent=2))


if __name__=="__main__":
    main()
