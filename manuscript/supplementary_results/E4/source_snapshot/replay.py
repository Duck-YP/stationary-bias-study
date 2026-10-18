"""Deployable within-run averaging and seed-level inference, without training."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

from prepare import write_csv

ALG = ['SCAFFOLD', 'FedAvg']
BASE = ['U', 'V', 'MSE', 'U_minus_V', 'U_minus_0.1MSE', 'projection',
        'train_gap', 'test_loss', 'share', 'V_minus_K1']
MATCHED = ['delta_U', 'delta_V', 'delta_MSE', 'delta_projection', 'delta_train',
           'delta_test', 'U_delta', 'C_cross']


def models(root):
    root = Path(root)
    p = json.loads((root / 'E4_v1_PROTOCOL_FROZEN.json').read_text())
    z = np.load(root / 'inputs/batches.npz')
    ref = np.load(root / 'inputs/reference_optimizers.npz')
    xs = np.stack([z['batch_raw_sum'][:, :, -k:].sum(axis=2) /
                   z['batch_count'][:, :, -k:].sum(axis=2)[:, :, None, None]
                   for k in p['K']], axis=3)
    counts = np.array([[c['schedule']['batch_length']*k for k in p['K']] for c in p['cells']])
    np.savez_compressed(root / 'models.npz', models=xs, deviations=xs-ref['x_ref'],
                        x_ref=ref['x_ref'], direction=ref['direction'],
                        cell_ids=z['cell_ids'], seeds=z['seeds'], K=np.array(p['K']),
                        counts=counts, algorithms=np.array(ALG))
    print(json.dumps({'model_shape': list(xs.shape), 'model_count': int(np.prod(xs.shape[:-1])),
                      'within_run_time_averaging': True, 'training': False}))


def features(d, train, test, direction, weights=None, population=False):
    """All functionals; exact bootstrap computation using per-seed Gram matrices."""
    r, a, k, dim = d.shape
    if weights is None:
        weights = np.ones((1, r))
    n = weights.sum(axis=1)
    gram = np.einsum('rakd,sakd->akrs', d, d, optimize=True)
    q = np.einsum('br,akrs,bs->bak', weights, gram, weights, optimize=True) / n[:, None, None]**2
    mse = np.einsum('br,rak->bak', weights, np.sum(d*d, axis=3), optimize=True) / n[:, None, None]
    if population:
        u, v = q, mse-q
    else:
        u = (n[:, None, None]*q-mse)/(n[:, None, None]-1)
        v = n[:, None, None]*(mse-q)/(n[:, None, None]-1)
    projection = np.einsum('br,rak->bak', weights, d @ direction)/n[:, None, None]
    tr = np.einsum('br,rak->bak', weights, train)/n[:, None, None]
    te = np.einsum('br,rak->bak', weights, test)/n[:, None, None]
    base = [u, v, mse, u-v, u-.1*mse, projection, tr, te,
            np.divide(u, mse, out=np.full_like(u, np.nan), where=mse != 0), v-v[:, :, :1]]
    delta = d[:, 0]-d[:, 1]
    dg = np.einsum('rkd,skd->krs', delta, delta, optimize=True)
    dq = np.einsum('br,krs,bs->bk', weights, dg, weights, optimize=True)/n[:, None]**2
    dmse = np.einsum('br,rk->bk', weights, np.sum(delta*delta, axis=2))/n[:, None]
    du = dq if population else (n[:, None]*dq-dmse)/(n[:, None]-1)
    # Sampling-corrected cross term makes Delta U = 2 C_U + U_delta exactly.
    cross = (u[:, 0]-u[:, 1]-du)/2
    paired = [u[:, 0]-u[:, 1], v[:, 0]-v[:, 1], mse[:, 0]-mse[:, 1],
              projection[:, 0]-projection[:, 1], tr[:, 0]-tr[:, 1], te[:, 0]-te[:, 1], du, cross]
    return np.concatenate([np.stack([b[:, aa] for b in base], axis=1) for aa in range(2)] +
                          [np.stack(paired, axis=1)], axis=1)


def jackknife(d, train, test, direction):
    r = len(d)
    theta = features(d, train, test, direction)[0]
    loo = np.stack([features(np.delete(d, i, axis=0), np.delete(train, i, axis=0),
                             np.delete(test, i, axis=0), direction)[0] for i in range(r)])
    pseudo = r*theta-(r-1)*loo
    se = np.std(pseudo, axis=0, ddof=1)/np.sqrt(r)
    return se, pseudo, loo


def temporal(root, weights):
    root = Path(root)
    p = json.loads((root / 'E4_v1_PROTOCOL_FROZEN.json').read_text())
    z = np.load(root / 'inputs/batches.npz')
    direction = np.load(root / 'inputs/reference_optimizers.npz')['direction']
    bm = z['batch_raw_sum']/z['batch_count'][:, :, :, None, None]
    defs = [('first_last', k, 0, 64-k) for k in p['K'] if k < 64]
    defs += [('middle_last', 8, 28, 56), ('middle_last', 16, 24, 48)]
    drifts, keys = [], []
    for ci, cell in enumerate(p['cells']):
        for aa, alg in enumerate(ALG):
            for name, k, start, end in defs:
                drift = bm[ci, :, end:end+k, aa].mean(axis=1)-bm[ci, :, start:start+k, aa].mean(axis=1)
                drifts.append(drift)
                keys.append((ci, aa, name, k, start, end))
    dd = np.stack(drifts)  # contrast, seed, coordinate
    r = dd.shape[1]
    mean = dd.mean(axis=1)
    centered = dd-mean[:, None]
    gram = np.einsum('crd,csd->crs', centered, centered, optimize=True)
    trace_se = np.sqrt(np.sum(centered*centered, axis=(1, 2))/(r-1)/r)
    norm_error = np.sqrt(np.maximum(0, np.einsum('br,crs,bs->bc', weights, gram, weights, optimize=True)/r**2))
    norm_standardized = np.divide(norm_error, trace_se[None], out=np.zeros_like(norm_error), where=trace_se[None] > 0)
    norm_max = np.max(norm_standardized, axis=1)
    proj = dd @ direction
    proj_mean = proj.mean(axis=1)
    proj_se = np.std(proj, axis=1, ddof=1)/np.sqrt(r)
    proj_error = weights @ (proj-proj_mean[:, None]).T/r
    projection_standardized = np.divide(np.abs(proj_error), proj_se[None], out=np.zeros_like(proj_error), where=proj_se[None] > 0)
    projection_max = np.max(projection_standardized, axis=1)
    assert np.isfinite(norm_standardized).all() and np.isfinite(projection_standardized).all()
    # Joint family across both equivalence gates, not two separate 95% families.
    joint_q = float(np.quantile(np.maximum(norm_max, projection_max), .95))
    qball = qp = joint_q
    rows, gate = [], {}
    for i, (ci, aa, name, k, start, end) in enumerate(keys):
        ub = float(np.linalg.norm(mean[i])+qball*trace_se[i])
        lo, hi = proj_mean[i]-qp*proj_se[i], proj_mean[i]+qp*proj_se[i]
        nondegenerate = trace_se[i] > 0 and proj_se[i] > 0
        passed = nondegenerate and ub <= p['temporal']['vector_norm_equivalence_margin'] and max(abs(lo), abs(hi)) <= p['temporal']['projection_equivalence_margin']
        drift_v = np.sum(centered[i]**2)/(r-1)
        rows.append(dict(cell_id=p['cells'][ci]['id'], algorithm=ALG[aa], contrast=name, K=k,
                         earlier_start_batch=start+1, later_start_batch=end+1,
                         mean_drift_norm=float(np.linalg.norm(mean[i])), norm_upper_simultaneous=ub,
                         vector_margin=.001, projection=float(proj_mean[i]), projection_lower_simultaneous=float(lo),
                         projection_upper_simultaneous=float(hi), projection_margin=.0001,
                         signed_drift_squared_U=float(mean[i]@mean[i]-drift_v/r),
                         temporal_equivalence=bool(passed), inferential_scale_status='NONDEGENERATE' if nondegenerate else 'ZERO_SCALE_NO_PRECISION_CLAIM', stationary_certified=False,
                         mean_drift_vector=json.dumps(mean[i].tolist())))
        if name == 'first_last':
            gate[ci, aa, k] = passed
    for ci in range(len(p['cells'])):
        for aa in range(2):
            gate[ci, aa, 64] = gate[ci, aa, 32]
    write_csv(root / 'TEMPORAL_DIAGNOSTICS.csv', rows)
    lagrows = []
    for ci, cell in enumerate(p['cells']):
        for aa in range(2):
            series = bm[ci, :, :, aa] @ direction
            for ri, seed in enumerate(p['seeds']):
                centered_series = series[ri]-series[ri].mean()
                for lag in [1, 2, 4, 8]:
                    # A descriptive finite-tail batch-mean autocorrelation proxy, not K_eff.
                    corr = float(centered_series[:-lag] @ centered_series[lag:] /
                                 np.sqrt((centered_series[:-lag]@centered_series[:-lag])*(centered_series[lag:]@centered_series[lag:])))
                    lagrows.append(dict(cell_id=cell['id'], algorithm=ALG[aa], seed=seed, lag_batches=lag,
                                        batch_projection_autocorrelation=corr, effective_K_assumed=False))
    write_csv(root / 'AUTOCORRELATION_PROXIES.csv', lagrows)
    return gate, dict(norm_max_critical=qball, projection_max_critical=qp, contrasts=len(keys))


def inference(root):
    root = Path(root)
    p = json.loads((root / 'E4_v1_PROTOCOL_FROZEN.json').read_text())
    z = np.load(root / 'models.npz')
    loss = np.load(root / 'practical/losses.npz')
    d = z['deviations']
    rng = np.random.default_rng(p['bootstrap']['seed'])
    weights = rng.multinomial(12, np.full(12, 1/12), size=p['bootstrap']['draws'])
    theta, population, boot, jkse, pseudos = [], [], [], [], []
    for ci in range(len(d)):
        args = (d[ci], loss['train_gap'][ci], loss['test_logloss'][ci], z['direction'])
        theta.append(features(*args)[0])
        population.append(features(*args, population=True)[0])
        boot.append(features(*args, weights=weights))
        se, pseudo, _ = jackknife(*args)
        jkse.append(se)
        pseudos.append(pseudo)
    theta, population, jkse = np.array(theta), np.array(population), np.array(jkse)
    boot = np.stack(boot, axis=1)  # bootstrap, cell, feature, K
    assert np.isfinite(theta).all() and np.isfinite(population).all() and np.isfinite(boot).all()
    bsse = np.std(boot, axis=0, ddof=1)
    lower, upper, jklower, jkupper = [np.empty_like(theta) for _ in range(4)]
    families, family_of = {}, {}
    for family, names in p['families'].items():
        idx = [list(z['cell_ids']).index(name) for name in names]
        active = bsse[idx] > 0
        err = boot[:, idx]-population[idx][None]
        standardized = np.divide(np.abs(err), bsse[idx][None], out=np.zeros_like(err), where=active[None])
        q = float(np.quantile(standardized.max(axis=(1, 2, 3)), .95))
        m = len(idx)*theta.shape[1]*theta.shape[2]
        jt = float(student_t.ppf(1-.05/(2*m), 11))
        lower[idx], upper[idx] = theta[idx]-q*bsse[idx], theta[idx]+q*bsse[idx]
        jklower[idx], jkupper[idx] = theta[idx]-jt*jkse[idx], theta[idx]+jt*jkse[idx]
        families[family] = dict(coordinates=m, bootstrap_max_critical=q, jackknife_Bonferroni_t=jt)
        for ci in idx:
            family_of[ci] = family
    gate, temporal_meta = temporal(root, weights)
    np.savez_compressed(root / 'inference_arrays.npz', theta=theta, empirical_population_center=population,
                        bootstrap_sd=bsse, jackknife_se=jkse, jackknife_pseudovalues=np.array(pseudos),
                        lower=lower, upper=upper, jackknife_lower=jklower, jackknife_upper=jkupper,
                        feature_names=np.array([f'{a}:{m}' for a in ALG for m in BASE]+MATCHED))
    batch = np.load(root / 'inputs/batches.npz')
    raw_mse = (batch['batch_sumsq'].sum(axis=2)/batch['batch_count'].sum(axis=2)[:, :, None]).mean(axis=1)
    statsrows, practicalrows, windowrows, decisions = [], [], [], []
    for ci, cell in enumerate(p['cells']):
        for ki, k in enumerate(p['K']):
            for aa, alg in enumerate(ALG):
                offset = aa*len(BASE)
                row = dict(cell_id=cell['id'], algorithm=alg, family=family_of[ci], H=cell['H'], N=cell['N'], m=cell['m'],
                           gamma=cell['gamma'], K=k, rounds_per_batch=cell['schedule']['batch_length'],
                           checkpoint_count=int(z['counts'][ci, ki]), independent_seeds=12,
                           mean_vector=json.dumps(d[ci, :, aa, ki].mean(axis=0).tolist()),
                           vector_array_key=f'models.npz:deviations[{ci},:,{aa},{ki},:]',
                           raw_checkpoint_MSE=float(raw_mse[ci, aa]),
                           raw_checkpoint_variance=float(raw_mse[ci, aa]-theta[ci, offset, -1]),
                           sample_decomposition_residual=float(theta[ci, offset+2, ki]-theta[ci, offset, ki]-theta[ci, offset+1, ki]),
                           temporal_equivalence=bool(gate[ci, aa, k]), stationary_certified=False)
                for mi, metric in enumerate(BASE):
                    ix = offset+mi
                    row[metric] = float(theta[ci, ix, ki])
                    row[metric+'_lower_simultaneous'] = float(lower[ci, ix, ki])
                    row[metric+'_upper_simultaneous'] = float(upper[ci, ix, ki])
                    row[metric+'_lower_jackknife_Bonferroni'] = float(jklower[ci, ix, ki])
                    row[metric+'_upper_jackknife_Bonferroni'] = float(jkupper[ci, ix, ki])
                for mi, metric in enumerate(MATCHED):
                    ix = 2*len(BASE)+mi
                    row[metric] = float(theta[ci, ix, ki])
                    row[metric+'_lower_simultaneous'] = float(lower[ci, ix, ki])
                    row[metric+'_upper_simultaneous'] = float(upper[ci, ix, ki])
                    row[metric+'_lower_jackknife_Bonferroni'] = float(jklower[ci, ix, ki])
                    row[metric+'_upper_jackknife_Bonferroni'] = float(jkupper[ci, ix, ki])
                pair = d[ci, :, 0, ki]-d[ci, :, 1, ki]
                row['Delta_mean_vector'] = json.dumps(pair.mean(axis=0).tolist())
                row['between_pair_variance'] = float(np.sum((pair-pair.mean(axis=0))**2)/11)
                row['bias_difference_identity_residual'] = float(row['delta_U']-2*row['C_cross']-row['U_delta'])
                def weak_scale(ix):
                    return bsse[ci, ix, ki] <= 0 or jkse[ci, ix, ki] <= 0 or jkse[ci, ix, ki] < 1e-3*bsse[ci, ix, ki]
                degenerate = weak_scale(offset)
                crossover_degenerate = weak_scale(offset+3)
                materiality_degenerate = weak_scale(offset+4)
                row['precision_status'] = 'WEAK_OR_ZERO_BIAS_IDENTIFICATION' if degenerate or lower[ci, offset, ki] <= 0 else 'FINITE_TAIL_BIAS_ESTIMABLE'
                row['U_jackknife_degenerate'] = bool(degenerate)
                row['crossover_jackknife_degenerate'] = bool(crossover_degenerate)
                row['materiality_jackknife_degenerate'] = bool(materiality_degenerate)
                row['zero_bootstrap_scale_metrics'] = json.dumps([m for mi, m in enumerate(BASE) if bsse[ci, offset+mi, ki] == 0])
                row['descriptive_crossover'] = bool(row['U'] >= row['V'])
                row['uncertainty_supported_at_K'] = bool(lower[ci, offset+3, ki] > 0 and jklower[ci, offset+3, ki] > 0 and gate[ci, aa, k] and not degenerate and not crossover_degenerate)
                row['materiality_supported_at_K'] = bool(lower[ci, offset+4, ki] > 0 and jklower[ci, offset+4, ki] > 0 and gate[ci, aa, k] and not degenerate and not materiality_degenerate)
                row['scope'] = 'POST_BURN_IN_FINITE_TAIL_ONLY;CONTROL_COEFFICIENT_NOT_ISOLATED_IN_REAL_DATA'
                statsrows.append(row)
                for ri, seed in enumerate(p['seeds']):
                    windowrows.append(dict(cell_id=cell['id'], algorithm=alg, seed=seed, H=cell['H'], N=cell['N'], m=cell['m'],
                                           gamma=cell['gamma'], K=k, start_batch=65-k, end_batch=64,
                                           start_round=cell['schedule']['burn']+(64-k)*cell['schedule']['batch_length']+1,
                                           end_round=int(batch['rounds'][ci, ri]), checkpoint_count=int(z['counts'][ci, ki]),
                                           model_array_key=f'models.npz:models[{ci},{ri},{aa},{ki},:]',
                                           displacement_projection=float(d[ci, ri, aa, ki]@z['direction']),
                                           squared_parameter_error=float(d[ci, ri, aa, ki]@d[ci, ri, aa, ki]),
                                           training_objective_gap=float(loss['train_gap'][ci, ri, aa, ki]),
                                           heldout_log_loss=float(loss['test_logloss'][ci, ri, aa, ki]),
                                           status='REPLAY_COMPLETED_FINITE_TAIL;HISTORICAL_RECORD_UNCHANGED'))
            total = cell['schedule']['burn']+64*cell['schedule']['batch_length']
            pr = dict(cell_id=cell['id'], family=family_of[ci], H=cell['H'], N=cell['N'], m=cell['m'], gamma=cell['gamma'], K=k,
                      checkpoint_count=int(z['counts'][ci, ki]), end_round=total,
                      existing_gradient_examples_per_algorithm=cell['N']*cell['m']*cell['H']*total,
                      window_gradient_examples_per_algorithm=cell['N']*cell['m']*cell['H']*int(z['counts'][ci, ki]),
                      existing_parameter_scalars_per_algorithm_proxy=cell['N']*124*total,
                      extra_scaffold_control_scalars_proxy=cell['N']*124*total,
                      additional_averaging_gradients=0, additional_averaging_communication=0,
                      online_accumulator_bytes=124*8+8,
                      train_at_ensemble_mean_S=float(loss['train_at_mean'][ci, 0, ki]),
                      train_at_ensemble_mean_F=float(loss['train_at_mean'][ci, 1, ki]),
                      ensemble_mean_is_not_deployable_time_average=True)
            for aa, alg in enumerate(ALG):
                for metric in ['train_gap', 'test_loss']:
                    ix = aa*len(BASE)+BASE.index(metric)
                    for name, arr in [('mean', theta), ('lower_simultaneous', lower), ('upper_simultaneous', upper)]:
                        pr[f'{alg}_{metric}_{name}'] = float(arr[ci, ix, ki])
            for metric in ['delta_train', 'delta_test', 'delta_MSE', 'delta_U', 'delta_V']:
                ix = 2*len(BASE)+MATCHED.index(metric)
                for name, arr in [('mean', theta), ('lower_simultaneous', lower), ('upper_simultaneous', upper)]:
                    pr[f'{metric}_{name}'] = float(arr[ci, ix, ki])
            practicalrows.append(pr)
        for aa, alg in enumerate(ALG):
            selected = [r for r in statsrows if r['cell_id'] == cell['id'] and r['algorithm'] == alg]
            supported = [r['uncertainty_supported_at_K'] for r in selected]
            consecutive = any(supported[i] and supported[i+1] for i in range(len(supported)-1))
            decisions.append(dict(cell_id=cell['id'], algorithm=alg, family=family_of[ci],
                                  descriptive_K=[r['K'] for r in selected if r['descriptive_crossover']],
                                  supported_K=[r['K'] for r in selected if r['uncertainty_supported_at_K']],
                                  materiality_K=[r['K'] for r in selected if r['materiality_supported_at_K']],
                                  finite_tail_crossover='SUPPORTED_FINITE_TAIL_CROSSOVER' if consecutive else 'NO_CERTIFIED_CROSSOVER',
                                  stationary_behavior='NOT_CERTIFIED'))
    write_csv(root / 'WINDOW_RESULTS.csv', windowrows)
    write_csv(root / 'BIAS_VARIANCE_MSE.csv', statsrows)
    write_csv(root / 'PRACTICAL_IMPLICATIONS.csv', practicalrows)
    (root / 'DECISIONS.json').write_text(json.dumps(decisions, indent=2)+'\n')
    (root / 'STATISTICAL_METHOD_RECEIPT.json').write_text(json.dumps(dict(families=families, temporal=temporal_meta,
                                                                      draws=len(weights), seed=p['bootstrap']['seed'],
                                                                      bootstrap_bias_center_corrected=True), indent=2)+'\n')
    print(json.dumps({'windows': len(windowrows), 'aggregate_rows': len(statsrows),
                      'families': families, 'primary_decisions': [d for d in decisions if d['family'] == 'primary']}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['models', 'inference'])
    p.add_argument('--root', required=True)
    a = p.parse_args()
    {'models': models, 'inference': inference}[a.command](a.root)
