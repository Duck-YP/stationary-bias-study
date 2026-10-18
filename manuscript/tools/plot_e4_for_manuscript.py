#!/usr/bin/env python3
"""Render separate E4 panels from unchanged saved interval columns; no fitting."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'supplementary_results/E4/BIAS_VARIANCE_MSE.csv'
DEST = ROOT / 'figures/redrawn'
DATA = DEST / 'data'
DATA.mkdir(parents=True, exist_ok=True)
# Exact native width of the user's existing 0.49-textwidth standalone panels.
WIDTH = 221.12505 / 72.0
HEIGHT = 3.25
plt.rcParams.update({
    'text.usetex': True,
    'font.family': 'serif',
    'font.serif': ['Computer Modern Roman'],
    'text.latex.preamble': r'\usepackage[T1]{fontenc}\usepackage{lmodern}',
    'font.size': 10.0,
    'axes.labelsize': 10.5,
    'xtick.labelsize': 10.0,
    'ytick.labelsize': 10.0,
    'legend.fontsize': 10.0,
    'axes.linewidth': 0.65,
    'lines.linewidth': 1.35,
    'lines.markersize': 4.4,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'axes.unicode_minus': False,
})

def main():
    table = pd.read_csv(SOURCE, float_precision='round_trip')
    rows = table[(table['cell_id'] == 'E3_R0_p0_H4_N128_g0.196078431373')].copy()
    assert len(rows) == 14 and set(rows.K) == {1,2,4,8,16,32,64}
    reports = []
    for algorithm, slug, color in [('SCAFFOLD','scaffold','#1769AA'),('FedAvg','fedavg','#8E3B46')]:
        d = rows[rows.algorithm == algorithm].sort_values('K')
        fig, ax = plt.subplots(figsize=(WIDTH, HEIGHT))
        fig.subplots_adjust(left=.29, right=.975, bottom=.19, top=.81)
        ax.set_xscale('log', base=2)
        ax.set_yscale('symlog', linthresh=1e-5, linscale=.75, base=10)
        handles = []
        for key, label, marker, ls, c in [('U',r'Squared mean displacement ($U$)','o','-',color),
                                        ('V',r'Averaged variance ($V$)','s','--','#4F5965')]:
            y=d[key].to_numpy()
            low=d[key+'_lower_simultaneous'].to_numpy()
            high=d[key+'_upper_simultaneous'].to_numpy()
            assert np.all(low <= y) and np.all(y <= high)
            assert np.all(low >= -5.5e-5) and np.all(high <= 5e-4), 'Interval outside frozen display range'
            e=ax.errorbar(d.K,y,yerr=np.vstack([y-low,high-y]),marker=marker,
                         linestyle=ls,color=c,capsize=2.3,elinewidth=.95,capthick=.85,
                         markerfacecolor=c if key == 'U' else 'white',
                         markeredgewidth=.95,markersize=4.2 if key == 'U' else 4.8,
                         zorder=4 if key == 'U' else 3,label=label)
            handles.append(e)
        ax.axhline(0,color='#929292',linewidth=.8,zorder=0)
        ax.set_ylim(-5.5e-5,5e-4)
        ax.set_xlim(.80,80)
        ax.set_xticks([1,2,4,8,16,32,64], labels=['1','2','4','8','16','32','64'])
        # Full-size exponents keep the smallest embedded tick glyphs >= 9 pt.
        ax.set_yticks([-1e-5,0,1e-5,1e-4],
                     labels=[r'$-10^{\textstyle -5}$','0',r'$10^{\textstyle -5}$',r'$10^{\textstyle -4}$'])
        ax.xaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_minor_locator(NullLocator())
        ax.set_xlabel(r'Averaging window $K$ (batches)',labelpad=5)
        ax.set_ylabel('Parameter-error contribution',labelpad=6)
        ax.grid(axis='y',color='#E6E6E6',linewidth=.55)
        ax.set_axisbelow(True)
        ax.spines[['top','right']].set_visible(False)
        ax.tick_params(direction='out',width=.65,length=3)
        fig.legend(handles=handles,loc='upper left',bbox_to_anchor=(.18,.985),
                   frameon=False,handlelength=1.7,handletextpad=.55,labelspacing=.40,borderaxespad=0)
        name=f'e4_averaging_{slug}'
        # Do not use bbox_inches='tight': final-size geometry and font audit rely on the native canvas.
        fig.savefig(DEST/f'{name}.pdf',metadata={'Title':f'E4 finite-tail averaging: {algorithm}',
                     'Author':'Manuscript integration from saved E4 results','CreationDate':None,'ModDate':None})
        fig.savefig(DEST/f'{name}.png',dpi=200)
        plt.close(fig)
        cols=['cell_id','algorithm','H','N','m','gamma','K','checkpoint_count','independent_seeds',
              'U','U_lower_simultaneous','U_upper_simultaneous','V','V_lower_simultaneous','V_upper_simultaneous']
        # The frozen plotted sidecars use LF, including on Windows.
        d[cols].to_csv(DATA/f'{name}.csv',index=False,float_format='%.17g',lineterminator='\n')
        reports.append({'panel':name,'algorithm':algorithm,'points_per_curve':7,'curves':['U','V'],
             'source':str(SOURCE.relative_to(ROOT)), 'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'uncertainty':'saved approximate simultaneous 95% E4 primary-family intervals, 196 statistics',
             'native_width_inches':WIDTH,'native_height_inches':HEIGHT,'intended_width':'0.49\\textwidth',
             'signed_U_not_clipped':True,'refitting':False,
             'yscale':'symlog','linthresh':1e-5,'linscale':.75,
             'ylim':[-5.5e-5,5e-4],'xlim':[.8,80],
             'all_interval_endpoints_within_display':True,
             'typography':'T1 Latin Modern; full-size tick exponents',
             'markers':{'U':'filled circle, solid line','V':'open square, dashed line'}})
    (DATA/'e4_provenance.json').write_text(json.dumps(reports,indent=2)+'\n')
    print('Rendered two standalone E4 PDFs; saved plotted values and provenance.')

if __name__ == '__main__': main()
