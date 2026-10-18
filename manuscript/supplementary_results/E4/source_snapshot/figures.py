"""One scientific axis per independent PDF; LaTeX performs all arrangement."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np

from prepare import write_csv

PANELS = ['E4_bias_variance_vs_window', 'E4_bias_fraction_vs_window',
          'E4_matched_mean_difference', 'E4_objective_gap_vs_window']
COLORS = {'SCAFFOLD': '#187a57', 'FedAvg': '#bd4248'}
TEX_WIDTH = 452.9679


def numeric(rows, key):
    return np.array([float(r[key]) for r in rows])


def draw(root):
    root = Path(root)
    out = root / 'figures'
    out.mkdir(exist_ok=True)
    rows = list(csv.DictReader((root / 'BIAS_VARIANCE_MSE.csv').open()))
    primary = [r for r in rows if r['family'] == 'primary']
    plt.rcParams.update({'font.family': 'serif', 'font.size': 10.5,
                         'text.usetex': True, 'text.latex.preamble': r'\usepackage{lmodern}',
                         'axes.labelsize': 10.5, 'xtick.labelsize': 9.7, 'ytick.labelsize': 9.7,
                         'legend.fontsize': 9.7, 'axes.linewidth': .7,
                         'pdf.fonttype': 42, 'ps.fonttype': 42, 'savefig.dpi': 180})
    exports = {}
    for panel in PANELS:
        fig, ax = plt.subplots(figsize=(TEX_WIDTH/72.27, 3.5))
        top = .72 if panel == PANELS[0] else (.78 if panel == PANELS[1] else .83)
        fig.subplots_adjust(left=.145, right=.98, bottom=.18, top=top)
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', color='#dddddd', lw=.5)
        ax.set_xscale('log', base=2)
        ax.set_xticks([1, 2, 4, 8, 16, 32, 64], ['1', '2', '4', '8', '16', '32', '64'])
        ax.set_xlabel(r'Averaging window $K$ (batches; 1,280 rounds each)')
        used = []
        if panel == PANELS[0]:
            for alg in COLORS:
                rr = sorted([r for r in primary if r['algorithm'] == alg], key=lambda r: int(r['K']))
                x = numeric(rr, 'K')
                for metric, style, symbol in [('U', '-', 'squared-bias U'), ('V', '--', 'averaged variance')]:
                    y, lo, hi = (numeric(rr, metric+s) for s in ['', '_lower_simultaneous', '_upper_simultaneous'])
                    ax.plot(x, y, style, marker='o' if metric == 'U' else 's', ms=3.5,
                            color=COLORS[alg], lw=1.3, label=f'{alg}: {symbol}')
                    ax.fill_between(x, lo, hi, color=COLORS[alg], alpha=.10, linewidth=0)
                used += rr
            raw = np.mean([float(r['raw_checkpoint_variance']) for r in primary])
            ax.axhline(raw, color='#686868', ls=':', lw=1.1, label='Raw-checkpoint variance')
            ax.set_yscale('symlog', linthresh=1e-6)
            ax.set_yticks([-1e-5, 0, 1e-5, 1e-4, 1e-3], ['-0.00001', '0', '0.00001', '0.0001', '0.001'])
            ax.set_ylabel('Squared parameter-error contribution')
        elif panel == PANELS[1]:
            for alg in COLORS:
                rr = sorted([r for r in primary if r['algorithm'] == alg], key=lambda r: int(r['K']))
                x = numeric(rr, 'K')
                y, lo, hi = (100*numeric(rr, 'share'+s) for s in ['', '_lower_simultaneous', '_upper_simultaneous'])
                ax.plot(x, y, '-o', ms=3.5, color=COLORS[alg], lw=1.3, label=alg)
                ax.fill_between(x, lo, hi, color=COLORS[alg], alpha=.13, linewidth=0)
                used += rr
            ax.axhline(10, color='#777777', ls=':', lw=1, label=r'10\% materiality reference')
            ax.axhline(50, color='#777777', ls='--', lw=.8, label='Descriptive crossover share')
            ax.set_ylabel(r'Signed squared-bias estimate / MSE (\%)')
        elif panel == PANELS[2]:
            for n, color in [(128, '#187a57'), (32, '#416a9e'), (8, '#bd4248')]:
                rr = sorted([r for r in rows if r['N'] == str(n) and r['H'] == '4' and
                             r['gamma'] == str(0.196078431372549) and r['algorithm'] == 'SCAFFOLD'], key=lambda r: int(r['K']))
                x = numeric(rr, 'K')
                y, lo, hi = (1000*numeric(rr, 'delta_projection'+s) for s in ['', '_lower_simultaneous', '_upper_simultaneous'])
                ax.plot(x, y, '-o', ms=3.5, color=color, lw=1.3, label=rf'$N={n},\ m={256//n}$')
                ax.fill_between(x, lo, hi, color=color, alpha=.14, linewidth=0)
                used += rr
            ax.axhline(0, color='#777777', ls=':', lw=1)
            ax.set_ylabel('Projected mean difference (units of 0.001)')
        else:
            for alg in COLORS:
                rr = sorted([r for r in primary if r['algorithm'] == alg], key=lambda r: int(r['K']))
                x = numeric(rr, 'K')
                y, lo, hi = (1e6*numeric(rr, 'train_gap'+s) for s in ['', '_lower_simultaneous', '_upper_simultaneous'])
                ax.plot(x, y, '-o', ms=3.5, color=COLORS[alg], lw=1.3, label=alg)
                ax.fill_between(x, lo, hi, color=COLORS[alg], alpha=.13, linewidth=0)
                used += rr
            ax.set_ylabel('Mean objective gap (units of 0.000001)')
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.55, .985),
                   ncol=2 if panel in PANELS[:2] else 3, frameon=False,
                   columnspacing=1.1, handlelength=1.8, labelspacing=.55)
        fig.savefig(out / (panel+'.pdf'))
        fig.savefig(out / (panel+'.png'))
        plt.close(fig)
        write_csv(out / (panel+'.csv'), used)
        exports[panel] = dict(rows=len(used), one_axis=True, width_TeX_pt=TEX_WIDTH,
                              minimum_requested_TeX_pt=9.7, uncertainty='Named-family simultaneous paired-seed bands',
                              stationary_certified=False)
    (out / 'FIGURE_MANIFEST.json').write_text(json.dumps(exports, indent=2)+'\n')
    captions = {
        PANELS[0]: 'Primary R0 H=4,N=128,m=2. Solid curves are signed U-statistic squared-bias estimates; dashed curves are between-run variance of a single time-averaged model. The dotted reference is raw-checkpoint variance, a different estimand. Shading gives simultaneous primary-family intervals. Negative estimates are retained.',
        PANELS[1]: 'Primary signed squared-bias fraction with simultaneous intervals. The10 percent benchmark is researcher-chosen. A share exceeding50 percent is only descriptive unless uncertainty and temporal equivalence support the two-consecutive-window criterion.',
        PANELS[2]: 'Paired frozen-direction mean differences at all three prespecified allocation settings. Primary and secondary simultaneous families are separate. These are not MSE differences or an isolated homogeneous control coefficient.',
        PANELS[3]: "The frozen training objective evaluated at each run's own averaged model, then averaged over independent seeds. Bands are simultaneous. This is not objective loss averaged over checkpoints, nor the objective at the ensemble mean. Test-loss contrasts are reported separately in PRACTICAL\\_IMPLICATIONS.csv.",
    }
    tex = [r'\documentclass[11pt]{article}', r'\usepackage[margin=1in]{geometry}',
           r'\usepackage{graphicx,lmodern,caption}', r'\setlength{\textwidth}{452.9679pt}',
           r'\begin{document}']
    for i, panel in enumerate(PANELS):
        tex += [r'\begin{figure}[p]\centering', rf'\includegraphics[width=\textwidth]{{figures/{panel}.pdf}}',
                r'\caption{'+captions[panel]+r'}', r'\end{figure}\clearpage']
    tex += [r'\end{document}']
    (root / 'E4_FIGURES_GALLERY.tex').write_text('\n'.join(tex)+'\n')
    print(json.dumps(exports))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    draw(p.parse_args().root)
