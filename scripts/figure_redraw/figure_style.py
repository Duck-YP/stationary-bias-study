"""Fixed physical canvases; TeX-backed font requests are measured in final PDFs."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

TEX_PT_PER_INCH = 72.27
PDF_PT_PER_INCH = 72.0
TEXTWIDTH_TEX_PT = 452.9679
BODY_TEX_PT = 10.95
HALF_WIDTH_INCH = 0.49 * TEXTWIDTH_TEX_PT / TEX_PT_PER_INCH
R0_WIDTH_INCH = 0.58 * TEXTWIDTH_TEX_PT / TEX_PT_PER_INCH
TICK_FONT = 9.7
LEGEND_FONT = 9.7
LABEL_FONT = 10.5
COORDINATES = [
    {"color": "#1769aa", "marker": "o", "linestyle": "-", "markerfacecolor": "#1769aa"},
    {"color": "#8e3b46", "marker": "s", "linestyle": "-.", "markerfacecolor": "white"},
]
ALGORITHMS = {
    "scaffold": {"color": "#1769aa", "marker": "o", "linestyle": "-"},
    "fedavg": {"color": "#8e3b46", "marker": "s", "linestyle": "--"},
}
RC = {
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
    "text.usetex": True,
    "text.latex.preamble": r"\usepackage[T1]{fontenc}\usepackage{lmodern}",
    "font.size": TICK_FONT,
    "axes.labelsize": LABEL_FONT,
    "xtick.labelsize": TICK_FONT,
    "ytick.labelsize": TICK_FONT,
    "legend.fontsize": LEGEND_FONT,
    "axes.linewidth": 0.65,
    "lines.linewidth": 1.3,
    "lines.markersize": 4.6,
    "savefig.facecolor": "white",
    "axes.facecolor": "white",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
}


def make_axes(*, real=False, legend_rows=3):
    width = R0_WIDTH_INCH if real else HALF_WIDTH_INCH
    height = 3.12
    fig = plt.figure(figsize=(width, height))
    top = 0.88 if legend_rows == 1 else (0.82 if legend_rows == 2 else 0.75)
    ax = fig.add_axes((0.225 if not real else 0.21, 0.18, 0.73 if not real else 0.74, top - 0.18))
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(width=0.65, length=3, pad=3)
    ax.grid(axis="y", color="#dddddd", linewidth=0.45, alpha=0.6)
    ax.set_axisbelow(True)
    return fig, ax


def coordinate_legend(fig, *, with_fit=True):
    handles = [Line2D([], [], **{**item, "linestyle": "none" if with_fit else item["linestyle"]},
                      label=f"Coord. {j+1} obs." if with_fit else f"Coord. {j+1}")
               for j, item in enumerate(COORDINATES)]
    if with_fit:
        handles += [
            Line2D([], [], color="#444444", linestyle=":", label="Finite-grid fit"),
            Line2D([], [], color="#444444", marker="D", markerfacecolor="white", linestyle="none", label="Fitted intercept"),
            Line2D([], [], color="#444444", linestyle="--", label="Theory target"),
        ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.52, 0.985), ncol=2,
               frameon=False, handlelength=1.5, columnspacing=0.7, handletextpad=0.45,
               borderaxespad=0.1, labelspacing=0.4)


def save_panel(fig, path):
    if len(fig.axes) != 1:
        raise AssertionError("Each panel must have exactly one scientific axes")
    ax = fig.axes[0]
    def coordinate_system(transform):
        if transform == ax.transData:
            return "data"
        if transform == ax.get_xaxis_transform():
            return "data_x_axes_y"
        if transform == ax.get_yaxis_transform():
            return "axes_x_data_y"
        return "other"
    geometry = {
        "panel_id": path.name,
        "canvas_inches": fig.get_size_inches().tolist(),
        "axes_bounds_fraction": list(ax.get_position().bounds),
        "xlim": list(ax.get_xlim()), "ylim": list(ax.get_ylim()),
        "xscale": ax.get_xscale(), "yscale": ax.get_yscale(),
        "lines": [{"coordinates": coordinate_system(line.get_transform()),
                   "x": [float(x) for x in line.get_xdata()],
                   "y": [float(y) for y in line.get_ydata()],
                   "marker": line.get_marker(), "linestyle": line.get_linestyle()}
                  for line in ax.lines],
        "interval_collections": [{"coordinates": coordinate_system(collection.get_transform()),
                                  "segments": [segment.tolist() for segment in collection.get_segments()]}
                                 for collection in ax.collections if hasattr(collection, "get_segments")],
    }
    geometry_path = path.parent / "data" / (path.name + "_geometry.json")
    geometry_path.parent.mkdir(parents=True, exist_ok=True)
    geometry_path.write_text(json.dumps(geometry, indent=2) + "\n", encoding="utf-8")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches=None, metadata={
        "Title": path.name, "Creator": "Frozen-data SCAFFOLD figure layout revision",
        "CreationDate": None, "ModDate": None,
    })
    fig.savefig(path.with_suffix(".png"), dpi=200, bbox_inches=None)
    plt.close(fig)
