"""Independent reference-point bridge and finite-tail paired-seed audit. No training."""
import argparse
import csv
import json
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy import sparse
from scipy.special import expit
from scipy.stats import t as student_t

from prepare import digest, write_csv, write_json


def logistic_reference(Z, y, x, lam=0.01):
    n = len(y)
    eta = Z @ x
    p = expit(eta)
    g = np.asarray(Z.T @ (p-y)).ravel()/n + lam*x
    A = (Z.T @ Z.multiply((p*(1-p))[:, None])).toarray()/n + lam*np.eye(len(x))
    centered_mean = np.asarray(Z.T @ (p-y)).ravel()/n
    second = (Z.T @ Z.multiply(((p-y)**2)[:, None])).toarray()/n
    Sigma = second - np.outer(centered_mean, centered_mean)
    quad = np.asarray(Z.multiply(Z @ Sigma).sum(axis=1)).ravel()
    T = np.asarray(Z.T @ (p*(1-p)*(1-2*p)*quad)).ravel()/n
    q = np.linalg.solve(A, -T)
    f = np.mean(np.logaddexp(0, eta)-y*eta) + lam/2*np.dot(x, x)
    return dict(objective=f, gradient=g, A=A, Sigma=Sigma, T=T, q=q)


def kappa(H):
    return (H-1)*(2*H-1)/(12*H)


def compute(root):
    root = Path(root)
    spec = json.loads((root / 'E5_POSTHOC_ANALYSIS_SPEC.json').read_text())
    checks = []

    def check(name, err, tol=0.0, details=''):
        ok = bool(np.isfinite(err) and err <= tol)
        checks.append(dict(check=name, error=float(err), tolerance=tol, passed=ok, details=details))
        if not ok:
            write_csv(root / 'NUMERICAL_CROSSCHECKS.csv', checks)
            raise AssertionError((name, err, tol))

    for row in csv.DictReader((root / 'INPUT_SHA256.csv').open()):
        check('input_sha256:' + row['local_path'], float(digest(root / row['local_path']) != row['sha256']))
    cells = json.loads((root / 'inputs/R0_CONFIGS.json').read_text())
    z = np.load(root / 'inputs/models.npz')
    b = np.load(root / 'inputs/batches.npz')
    ref = np.load(root / 'inputs/reference_optimizers.npz')
    Z = sparse.load_npz(root / 'inputs/training_csr.npz')
    y = np.load(root / 'inputs/membership.npz')['labels']
    K = np.array(spec['K'])
    check('model_shape_9_12_2_7_124', float(z['models'].shape != (9, 12, 2, 7, 124)))
    check('seeds_20001_through_20012', float(not np.array_equal(z['seeds'], np.arange(20001, 20013))))
    for zz, label in [(z, 'models'), (b, 'batches')]:
        check(label + '_cell_order', float(list(zz['cell_ids']) != [c['id'] for c in cells]))
        check(label + '_algorithm_order', float(list(zz['algorithms']) != ['SCAFFOLD', 'FedAvg']))
        check(label + '_seed_order', float(not np.array_equal(zz['seeds'], z['seeds'])))
        for key in zz.files:
            if np.issubdtype(zz[key].dtype, np.number):
                check(label + '_finite_' + key, float(not np.isfinite(zz[key]).all()))
    check('all_K', float(not np.array_equal(z['K'], K)))
    check('dimension_and_rows', float(Z.shape != (32512, 124)))
    check('intercept_last_column_is_one', np.max(np.abs(Z[:, -1].toarray()-1)))
    check('deviations_semantics', np.max(np.abs(z['models'] - ref['x_ref'] - z['deviations'])))
    check('models_reference', np.max(np.abs(z['x_ref']-ref['x_ref'])))
    replay = np.stack([b['batch_raw_sum'][:, :, -int(k):].sum(axis=2) /
                       b['batch_count'][:, :, -int(k):].sum(axis=2)[:, :, None, None] for k in K], axis=3)
    check('exact_all_1512_vector_replay', np.max(np.abs(replay-z['models'])))
    for ci, cell in enumerate(cells):
        schedule = cell['schedule']
        check(cell['id']+'_counts', np.max(np.abs(b['batch_count'][ci]-schedule['batch_length'])))
        check(cell['id']+'_rounds', np.max(np.abs(b['rounds'][ci]-(schedule['burn']+64*schedule['batch_length']))))
        check(cell['id']+'_window_counts', np.max(np.abs(z['counts'][ci]-K*schedule['batch_length'])))
        check(cell['id']+'_budget_256', abs(cell['N']*cell['m']-256))
    # The full deterministic ridge term cancels in centered sampling covariance.
    f = logistic_reference(Z, y, ref['x_ref'])
    check('gradient_first_order', np.linalg.norm(f['gradient']), 1e-12)
    check('A_recomputed', np.max(np.abs(f['A']-ref['A_ref'])), 2e-14)
    check('Sigma_recomputed', np.max(np.abs(f['Sigma']-ref['Sigma_ref'])), 2e-14)
    check('Sigma_symmetric', np.max(np.abs(f['Sigma']-f['Sigma'].T)), 2e-14)
    check('Sigma_PSD_violation', max(0., -np.linalg.eigvalsh(f['Sigma']).min()), 2e-14)
    check('ridge_min_eigenvalue', max(0., .01-np.linalg.eigvalsh(f['A']).min()), 2e-14)
    unit = f['q']/np.linalg.norm(f['q'])
    check('frozen_direction_normalization', abs(np.linalg.norm(ref['direction'])-1), 1e-13)
    check('frozen_direction_matches_negative_A_inverse_T', np.max(np.abs(unit-ref['direction'])), 1e-12)
    check('H1_zero', abs(kappa(1)))
    check('H4_H2_factor_3point5', abs(kappa(4)/kappa(2)-3.5))
    alpha = np.array([c['gamma']**2*kappa(c['H'])/c['m'] for c in cells])
    proxies = alpha[:, None]*f['q']
    check('H1_all_124_proxy_coordinates_zero', np.max(np.abs(proxies[[c['H'] == 1 for c in cells]])))
    # j indexes a cell-window, r a genuinely independent paired seed, d a coordinate.
    paired = (z['models'][:, :, 0]-z['models'][:, :, 1]).transpose(0, 2, 1, 3).reshape(63, 12, 124)
    metas = []
    for ci, c in enumerate(cells):
        for ki, k in enumerate(K):
            metas.append(dict(cell_id=c['id'], H=c['H'], N=c['N'], m=c['m'], gamma=c['gamma'], K=int(k),
                              independent_seeds=12, dimension=124, primary=bool(k == 64),
                              batch_length=c['schedule']['batch_length'], checkpoint_count=int(z['counts'][ci, ki]),
                              burn=c['schedule']['burn'], first_batch=65-int(k), last_batch=64,
                              end_round=int(b['rounds'][ci, 0]), status='EXPLORATORY_FINITE_TAIL_NOT_STATIONARY'))
    drift, driftmeta = [], []
    for ci, c in enumerate(cells):
        for k in K[:-1]:
            early = b['batch_raw_sum'][ci, :, :k].sum(axis=1)/b['batch_count'][ci, :, :k].sum(axis=1)[:, None, None]
            late = b['batch_raw_sum'][ci, :, -k:].sum(axis=1)/b['batch_count'][ci, :, -k:].sum(axis=1)[:, None, None]
            drift.append((late[:, 0]-late[:, 1])-(early[:, 0]-early[:, 1]))
            driftmeta.append(dict(cell_id=c['id'], H=c['H'], N=c['N'], m=c['m'], gamma=c['gamma'], K=int(k),
                                  earlier_first_batch=1, later_first_batch=65-int(k), independent_seeds=12,
                                  status='PAIRED_DIFFERENCE_WINDOW_DIAGNOSTIC_NOT_E4_STATIONARITY_TEST'))
    dd = np.concatenate([paired, np.array(drift)], axis=0)
    pred = np.concatenate([np.repeat(proxies, 7, axis=0), np.zeros((54, 124))])
    prednorm = np.linalg.norm(pred, axis=1)
    direction = ref['direction']
    comparators = {'frozen_x_ref': ref['x_ref']/np.linalg.norm(ref['x_ref']),
                   'negative_T_Sigma': -f['T']/np.linalg.norm(f['T'])}
    projection = dd @ direction
    gram = np.einsum('jrd,jsd->jrs', dd, dd, optimize=True)
    preddot = np.einsum('jrd,jd->jr', dd, pred)
    compdot = {name: dd @ v for name, v in comparators.items()}

    def metric_arrays(weights):
        w = weights / weights.sum(axis=1, keepdims=True)
        sq = np.maximum(0, np.einsum('br,jrs,bs->bj', w, gram, w, optimize=True))
        norm = np.sqrt(sq)
        proj = w @ projection.T
        dot = w @ preddot.T
        residual = np.sqrt(np.maximum(0, sq+prednorm**2-2*dot))
        parallel = proj - pred @ direction
        orth = np.sqrt(np.maximum(0, sq-proj**2))
        result = dict(observed_norm=norm, observed_projection=proj, residual_norm=residual,
                      parallel_residual=parallel, orthogonal_residual_norm=orth)
        active = prednorm > 0
        for name, value in [('cosine', proj[:, active]/norm[:, active]),
                            ('norm_ratio', norm[:, active]/prednorm[active]),
                            ('projection_ratio', proj[:, active]/prednorm[active]),
                            ('relative_residual', residual[:, active]/prednorm[active])]:
            result[name] = (np.flatnonzero(active), value)
        for name, dots in compdot.items():
            result[name+'_cosine'] = (np.arange(63), (w @ dots[:63].T)/norm[:, :63])
        return result

    # All contrasts are fixed by input identities, not by observed outcomes.
    def cell_index(H, N, factor=1):
        base = float(ref['gamma_base'])
        return next(i for i, c in enumerate(cells) if c['H'] == H and c['N'] == N and np.isclose(c['gamma'], base*factor, rtol=1e-13, atol=0))

    comparisons = []
    for small, big in [(.25, .5), (.5, 1), (.25, 1)]:
        comparisons.append(('gamma', cell_index(4, 32, big), cell_index(4, 32, small)))
    comparisons.append(('H', cell_index(4, 32), cell_index(2, 32)))
    for small, big in [(8, 32), (32, 128), (8, 128)]:
        comparisons.append(('allocation_N_and_m', cell_index(4, big), cell_index(4, small)))
    scaling_meta = []
    for typ, num, den in comparisons:
        for ki, k in enumerate(K):
            scaling_meta.append(dict(comparison=f'{typ}:{cells[num]["id"]}/{cells[den]["id"]}:K{k}',
                                     kind=typ, numerator_cell=cells[num]['id'], denominator_cell=cells[den]['id'], K=int(k),
                                     numerator_index=num*7+ki, denominator_index=den*7+ki,
                                     proxy_ratio=float(alpha[num]/alpha[den]),
                                     gamma_ratio=cells[num]['gamma']/cells[den]['gamma'],
                                     scope='EXPLORATORY_FINITE_GRID;NOT_FIXED_C_N_THEOREM' if typ.startswith('allocation') else 'EXPLORATORY_FINITE_GRID'))

    feature_keys = []

    def flatten(weights, first=False):
        arr = metric_arrays(weights)
        parts, keys = [], []
        for name, values in arr.items():
            idx, values = values if isinstance(values, tuple) else (np.arange(len(dd)), values)
            parts.append(values)
            keys.extend([('vector', int(j), name) for j in idx])
        for si, sc in enumerate(scaling_meta):
            a, d = sc['numerator_index'], sc['denominator_index']
            pp, nn = arr['observed_projection'], arr['observed_norm']
            if np.any(pp[:, d] <= 0) or np.any(pp[:, a] <= 0):
                raise ValueError('Unresolved positive-projection scaling: no silent dropping or epsilons')
            ratio = pp[:, a]/pp[:, d]
            vals = dict(projection_ratio=ratio, norm_ratio=nn[:, a]/nn[:, d], relative_to_proxy=ratio/sc['proxy_ratio'])
            if sc['kind'] == 'gamma':
                vals['projection_log_slope'] = np.log(ratio)/np.log(sc['gamma_ratio'])
                vals['norm_log_slope'] = np.log(vals['norm_ratio'])/np.log(sc['gamma_ratio'])
            for name, v in vals.items():
                parts.append(v[:, None])
                keys.append(('scaling', si, name))
        if first:
            feature_keys.extend(keys)
        else:
            assert keys == feature_keys
        result = np.concatenate(parts, axis=1)
        assert np.isfinite(result).all()
        return result

    theta = flatten(np.ones((1, 12)), first=True)[0]
    rng = np.random.default_rng(spec['bootstrap']['seed'])
    weights = rng.multinomial(12, np.full(12, 1/12), size=spec['bootstrap']['draws'])
    boot = flatten(weights)
    loo = flatten(np.ones((12, 12))-np.eye(12))
    bse = boot.std(axis=0, ddof=1)
    pseudo = 12*theta-11*loo
    jse = pseudo.std(axis=0, ddof=1)/np.sqrt(12)
    standardized = np.divide(np.abs(boot-theta), bse, out=np.zeros_like(boot), where=bse > 0)
    critical = float(np.quantile(standardized.max(axis=1), .95))
    tcrit = float(student_t.ppf(1-.05/(2*len(theta)), 11))
    low, high = theta-critical*bse, theta+critical*bse
    jlow, jhigh = theta-tcrit*jse, theta+tcrit*jse
    pctlow, pcthigh = np.quantile(boot, [.025, .975], axis=0)
    lookup = {k: i for i, k in enumerate(feature_keys)}
    sensitivity = []
    for i, (typ, j, name) in enumerate(feature_keys):
        meta = (metas+driftmeta)[j] if typ == 'vector' else scaling_meta[j]
        sensitivity.append(dict(target_type=typ, target_index=j, cell_id=meta.get('cell_id', ''), K=meta['K'],
                                comparison=meta.get('comparison', ''), metric=name, estimate=theta[i],
                                bootstrap_sd=bse[i], lower_simultaneous=low[i], upper_simultaneous=high[i],
                                jackknife_se=jse[i], lower_jackknife_Bonferroni=jlow[i], upper_jackknife_Bonferroni=jhigh[i],
                                percentile_nominal_lower=pctlow[i], percentile_nominal_upper=pcthigh[i],
                                bootstrap_mean_minus_estimate=float(boot[:, i].mean()-theta[i]),
                                jackknife_bias_estimate=float(11*(loo[:, i].mean()-theta[i])),
                                scale_status='REGULARITY_NOT_GUARANTEED' if bse[i] > 0 and jse[i] > 0 else 'DEGENERATE_SCALE_NO_PRECISION_CLAIM',
                                family_size=len(theta), simultaneous_critical=critical, independent_seeds=12,
                                scope='EXPLORATORY_CONDITIONAL_NO_PROXY_REMAINDER_COVERAGE'))
    write_csv(root / 'PAIRED_BOOTSTRAP_SENSITIVITY.csv', sensitivity)
    # Mean-vector confidence balls retain the entire 124-vector dependence.
    mu = dd.mean(axis=1)
    centered = dd-mu[:, None]
    cg = np.einsum('jrd,jsd->jrs', centered, centered, optimize=True)
    errornorm = np.sqrt(np.maximum(0, np.einsum('br,jrs,bs->bj', weights/12, cg, weights/12, optimize=True)))
    vector_se = np.sqrt(np.sum(centered**2, axis=(1, 2))/11/12)
    vstandard = np.divide(errornorm, vector_se, out=np.zeros_like(errornorm), where=vector_se > 0)
    vcritical = float(np.quantile(vstandard.max(axis=1), .95))
    radius = vcritical*vector_se

    def add_stats(row, typ, idx, metric):
        i = lookup[typ, idx, metric]
        row[metric] = float(theta[i])
        row[metric+'_lower_simultaneous'] = float(low[i])
        row[metric+'_upper_simultaneous'] = float(high[i])
        row[metric+'_lower_jackknife_Bonferroni'] = float(jlow[i])
        row[metric+'_upper_jackknife_Bonferroni'] = float(jhigh[i])

    rows = []
    for j, meta in enumerate(metas):
        row = dict(meta, proxy_norm=float(prednorm[j]), proxy_projection=float(pred[j] @ direction),
                   undefined_ratio_status='UNDEFINED_ZERO_PROXY' if prednorm[j] == 0 else 'DEFINED',
                   vector_ball_radius=float(radius[j]), vector_ball_family_size=len(dd))
        for name in ['observed_norm', 'observed_projection', 'residual_norm', 'parallel_residual', 'orthogonal_residual_norm']:
            add_stats(row, 'vector', j, name)
        if prednorm[j] > 0:
            for name in ['cosine', 'norm_ratio', 'projection_ratio', 'relative_residual']:
                add_stats(row, 'vector', j, name)
            angle = np.arccos(np.clip(row['cosine'], -1, 1))
            if radius[j] < row['observed_norm']:
                da = np.arcsin(radius[j]/row['observed_norm'])
                row['cosine_vector_ball_lower'] = float(np.cos(min(np.pi, angle+da)))
                row['cosine_vector_ball_upper'] = float(np.cos(max(0, angle-da)))
            else:
                row['cosine_vector_ball_lower'], row['cosine_vector_ball_upper'] = -1., 1.
            row['norm_ratio_vector_ball_lower'] = max(0., row['observed_norm']-radius[j])/prednorm[j]
            row['norm_ratio_vector_ball_upper'] = (row['observed_norm']+radius[j])/prednorm[j]
        row['norm_vector_ball_lower'] = max(0., row['observed_norm']-radius[j])
        row['norm_vector_ball_upper'] = row['observed_norm']+radius[j]
        row['residual_vector_ball_lower'] = max(0., row['residual_norm']-radius[j])
        row['residual_vector_ball_upper'] = row['residual_norm']+radius[j]
        check(f'residual_decomposition_{j}', abs(row['residual_norm']**2-row['parallel_residual']**2-row['orthogonal_residual_norm']**2), 1e-15)
        rows.append(row)
    write_csv(root / 'ALL_CELLS_ALL_WINDOWS.csv', rows)
    write_csv(root / 'FULL_VECTOR_ALIGNMENT.csv', rows)
    temporal_rows = []
    for i, meta in enumerate(driftmeta):
        j = 63+i
        row = dict(meta, vector_ball_radius=float(radius[j]), E4_temporal_classification_changed=False)
        for name in ['observed_norm', 'observed_projection']:
            add_stats(row, 'vector', j, name)
        row['norm_ball_lower'] = max(0., row['observed_norm']-radius[j])
        row['norm_ball_upper'] = row['observed_norm']+radius[j]
        temporal_rows.append(row)
    write_csv(root / 'EARLY_LATE_PAIRED_DIAGNOSTICS.csv', temporal_rows)
    scaling_rows = []
    for si, sc in enumerate(scaling_meta):
        row = dict(sc)
        for name in ['projection_ratio', 'norm_ratio', 'relative_to_proxy']:
            add_stats(row, 'scaling', si, name)
        if sc['kind'] == 'gamma':
            for name in ['projection_log_slope', 'norm_log_slope']:
                add_stats(row, 'scaling', si, name)
        n, d = sc['numerator_index'], sc['denominator_index']
        ni, di = lookup['vector', n, 'observed_projection'], lookup['vector', d, 'observed_projection']
        if min(low[ni], low[di]) > 0:
            lo, hi = low[ni]/high[di], high[ni]/low[di]
            row['denominator_status'] = 'POSITIVE_IN_GLOBAL_SIMULTANEOUS_BAND'
            row['projection_ratio_interval_transform_lower'], row['projection_ratio_interval_transform_upper'] = float(lo), float(hi)
            if sc['kind'] == 'gamma':
                row['log_slope_interval_transform_lower'] = float(np.log(lo)/np.log(sc['gamma_ratio']))
                row['log_slope_interval_transform_upper'] = float(np.log(hi)/np.log(sc['gamma_ratio']))
        else:
            row['denominator_status'] = 'UNRESOLVED_NO_BOUNDED_TRANSFORM_INTERVAL'
        row['proxy_ratio_discrepancy'] = row['projection_ratio']-sc['proxy_ratio']
        scaling_rows.append(row)
    write_csv(root / 'SCALING_COMPARISONS.csv', scaling_rows)
    controls = []
    for j, meta in enumerate(metas):
        if meta['H'] == 1:
            controls.append(dict(meta, comparator='H1_zero_proxy', amplitude_comparison=True,
                                 residual_norm=rows[j]['residual_norm'], projection=rows[j]['observed_projection'],
                                 status='ABSOLUTE_ONLY;HISTORICAL_NUMERICAL_DRIFT_RETAINED'))
        controls.append(dict(meta, comparator='zero_vector_amplitude_null', amplitude_comparison=True,
                             residual_norm=rows[j]['observed_norm'], proxy_residual_norm=rows[j]['residual_norm'],
                             status='NO_SCALE_FIT'))
        for name in comparators:
            i = lookup['vector', j, name+'_cosine']
            controls.append(dict(meta, comparator=name, amplitude_comparison=False, cosine=float(theta[i]),
                                 cosine_lower_simultaneous=float(low[i]), cosine_upper_simultaneous=float(high[i]),
                                 status='DIRECTION_ONLY;NO_OUTCOME_DEPENDENT_ORIENTATION_OR_SCALE'))
    write_csv(root / 'NEGATIVE_CONTROLS.csv', controls)
    per_seed = []
    for j, meta in enumerate(metas):
        for ri, seed in enumerate(z['seeds']):
            per_seed.append(dict(meta, seed=int(seed), paired_projection=float(paired[j, ri] @ direction),
                                 paired_norm=float(np.linalg.norm(paired[j, ri])), vector_key=f'VECTORS.npz:paired[{j},{ri},:]'))
    write_csv(root / 'PAIRED_SEED_RESULTS.csv', per_seed)
    # Compare saved historical exploratory values, not its inference implementation.
    exploratory = list(csv.DictReader(next((root / 'supplied').glob('*Exploratory_*.csv')).open()))
    explchecks = []
    for er in exploratory:
        ident = er.get('cell_id', er.get('cell'))
        row = next(r for r in rows if r['cell_id'] == ident and r['K'] == 64)
        explchecks.append(dict(cell_id=ident, exact_gamma=row['gamma'], rounded_id_gamma=float(ident.split('_g')[-1]),
                               relative_squared_gamma_difference=(float(ident.split('_g')[-1])/row['gamma'])**2-1,
                               original_csv=json.dumps(er, sort_keys=True)))
    write_csv(root / 'EXPLORATORY_SCRIPT_CROSSCHECK.csv', explchecks)
    np.savez_compressed(root / 'VECTORS.npz', paired=paired, paired_early_late=np.array(drift), observed=mu,
                        proxy=pred, q=f['q'], T_Sigma=f['T'], A=f['A'], Sigma=f['Sigma'], x_ref=ref['x_ref'],
                        direction=direction, seeds=z['seeds'], K=K, cell_ids=z['cell_ids'])
    np.savez_compressed(root / 'INFERENCE_ARRAYS.npz', weights=weights.astype(np.int8), theta=theta, bootstrap_sd=bse,
                        jackknife_se=jse, loo=loo, lower=low, upper=high, vector_radius=radius,
                        feature_keys=np.array([json.dumps(k) for k in feature_keys]))
    write_csv(root / 'NUMERICAL_CROSSCHECKS.csv', checks)
    write_json(root / 'STATISTICAL_METHOD_RECEIPT.json', dict(spec_sha256=digest(root / 'E5_POSTHOC_ANALYSIS_SPEC.json'),
                draws=len(weights), seed=spec['bootstrap']['seed'], scalar_family_size=len(theta), scalar_critical=critical,
                jackknife_Bonferroni_t=tcrit, vector_family_size=len(dd), vector_critical=vcritical,
                scalar_and_vector_families_separately_95_percent_not_joint=True,
                undefined_scaling_draws=0, fitted_parameters=0, new_training=False))
    write_json(root / 'ENVIRONMENT.json', dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                numpy=np.__version__, scipy=scipy.__version__, independent_seed_count=12,
                bootstrap_seed=spec['bootstrap']['seed'], thread_limits='OPENBLAS_NUM_THREADS=1;OMP_NUM_THREADS=1'))
    print(json.dumps(dict(status='PASS', checks=len(checks), all_cell_windows=len(rows), scaling_rows=len(scaling_rows),
                         scalar_family_size=len(theta), scalar_critical=critical, vector_critical=vcritical,
                         q_norm=float(np.linalg.norm(f['q'])), training=False)))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    compute(p.parse_args().root)
