"""Add contrast precision forecasts; do not modify the frozen protocol/horizon."""
import json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    p=json.loads((ROOT/'COST_PRECISION_FORECAST.json').read_text())
    items={(r['condition'],r['observable'],r['coordinate']):r for r in p['precision_forecasts']}
    rows=[]
    for kind,left,right in [('law_contrast','rho_plus_symmetric','rho_plus_asymmetric'),('signed_covariance_contrast','rho_plus_symmetric','rho_minus_symmetric')]:
        for obs in ['SCAFFOLD','FedAvg','difference']:
            for j in (1,2):
                a=items[(left,obs,j)]; b=items[(right,obs,j)]
                rows.append(dict(kind=kind,observable=obs,coordinate=j,forecast_se=math.hypot(a['initial_intercept_se'],b['initial_intercept_se']),
                    marginal_95_halfwidth=math.hypot(a['marginal_95_halfwidth'],b['marginal_95_halfwidth']),
                    bonferroni_36_halfwidth=math.hypot(a['bonferroni_36_halfwidth'],b['bonferroni_36_halfwidth']),resolution_margin=a['resolution_margin']))
    out=dict(scope='Derived additive forecast from the unchanged pre-production pilot forecasts; no production outcomes read; no protocol/horizon change.',
        variance_rule='Independent condition streams: SE contrast = sqrt(SE_left^2+SE_right^2). Same four-pilot-seed heuristic limitations apply.',forecasts=rows)
    (ROOT/'COST_PRECISION_CONTRAST_FORECAST.json').write_text(json.dumps(out,indent=2),encoding='utf8')
if __name__=='__main__': main()
