"""Produce transparent tables and measured cost ledger after fixed analysis."""
import sys,pathlib,json,csv
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'supplementary_study/.deps'))
import numpy as np
def main():
    with (ROOT/'results/primary_family_36.csv').open(encoding='utf8') as f: rows=list(csv.DictReader(f))
    with (ROOT/'results/intercepts_and_contrasts.csv').open(encoding='utf8') as f: allrows=list(csv.DictReader(f))
    text=['# Complete primary coefficient summaries','',
        'All intervals below are the approximate 95% simultaneous sampling intervals for the frozen family of 36 scalar summaries. '
        'Marginal Student-t/bootstrap intervals and Bonferroni-t sensitivity are retained in CSV. '
        'Sampling intervals omit burn-in and deterministic grid remainder.','',
        '| Comparison | Observable | Coordinate | Estimate | Interval | Target | Practical resolution / control |',
        '|---|---|---:|---:|---|---:|---|']
    for r in rows:
        text.append(f"| {r['comparison']} | {r['observable']} | {r['coordinate']} | {float(r['estimate']):.8g} | [{float(r['simultaneous_lower']):.8g}, {float(r['simultaneous_upper']):.8g}] | {float(r['target']):.8g} | {r['resolution_band_result']} |")
    text+=['','## Prespecified restricted-grid sensitivity','',
        'The omitted-step sensitivity is displayed alongside the primary; it never replaces it.', '',
        '| Comparison | Observable | Coordinate | Full intercept | Omit-largest-step intercept | Change |',
        '|---|---|---:|---:|---:|---:|']
    for r in rows:
        q=next(v for v in allrows if v['comparison']==r['comparison'] and v['observable']==r['observable'] and v['coordinate']==r['coordinate'] and v['estimator']=='balance' and v['grid']=='omit_largest_gamma')
        text.append(f"| {r['comparison']} | {r['observable']} | {r['coordinate']} | {float(r['estimate']):.8g} | {float(q['estimate']):.8g} | {float(q['estimate'])-float(r['estimate']):.5g} |")
    (ROOT/'results/RESULT_TABLES.md').write_text('\n'.join(text)+'\n',encoding='utf8')
    forecasts=json.loads((ROOT/'COST_PRECISION_FORECAST.json').read_text())
    costs={}
    for phase in ['pilot','production']:
        cpu=0.; wall=0.; count=0; rounds=0
        for p in (ROOT/'local'/phase).glob('*/seed_*/result.npz'):
            with np.load(p) as d: cpu+=float(d['cpu']); wall+=float(d['wall']); rounds+=int(d['t']); count+=1
        costs[phase]=dict(completed_runs=count,measured_simulation_cpu_seconds=cpu,simulation_cpu_hours=cpu/3600,sum_per_run_kernel_wall_seconds=wall,paired_rounds=rounds)
    costs['total_simulation_cpu_hours']=sum(costs[p]['simulation_cpu_hours'] for p in ['pilot','production'])
    costs['cap_cpu_hours']=6.;costs['forecast_cpu_hours']=forecasts['total_projected_cpu_hours']; costs['cap_met']=costs['total_simulation_cpu_hours']<6
    costs['measurement_scope']='process_time around compiled simulation chunks, accumulated across all workers; includes first-use kernel loading within a chunk. Python checkpoint I/O, compilation warmup, analysis and unit tests are separate from simulation timing; the 25% pre-production reserve covered engineering overhead. Two 2000-round microbenchmarks additionally measured 0.109375 CPU seconds total.'
    costs['decisions']='Executed complete frozen 24-cell x 12-run study after measured feasible forecast. No horizon extension, condition removal, or target-dependent refitting. No RESOURCE_LIMITED configurations.'
    (ROOT/'ACTUAL_COST_AND_DECISIONS.json').write_text(json.dumps(costs,indent=2),encoding='utf8')
    (ROOT/'requirements.lock').write_text('\n'.join(k+'=='+v for k,v in json.loads((ROOT/'ENVIRONMENT.json').read_text())['packages'].items())+'\nsympy==1.14.0\n',encoding='utf8')
    print(json.dumps(costs,indent=2))
if __name__=='__main__': main()
