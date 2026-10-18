"""Descriptive R=2 v2 pilot only; never pooled into v1 significance inference."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from prepare import write_csv


def analyze(root):
    root = Path(root)
    p = json.loads((root / 'E4_v2_PROTOCOL_FROZEN.json').read_text())
    ref = np.load(root / 'inputs/reference_optimizers.npz')
    train = sparse.load_npz(root / 'inputs/training_csr.npz')
    labels = np.load(root / 'inputs/membership.npz')['labels']
    test = sparse.load_npz(root / 'practical/inputs/test_csr.npz')
    ty = np.load(root / 'practical/inputs/test_labels.npz')['labels']
    def loss(Z, y, x):
        v = Z @ x
        return float(np.mean(np.logaddexp(0, v)-y*v))
    fref = loss(train, labels, ref['x_ref'])+.005*(ref['x_ref']@ref['x_ref'])
    per = list(__import__('csv').DictReader((root / 'v2/PILOT_WINDOW_RESULTS.csv').open()))
    models = np.load(root / 'v2/pilot_models.npz')
    for row in per:
        seed, k = int(row['seed']), int(row['K'])
        aa = ['SCAFFOLD', 'FedAvg'].index(row['algorithm'])
        x = models[f'seed_{seed}_K{k}'][aa]
        row['training_objective_gap'] = loss(train, labels, x)+.005*(x@x)-fref
        row['heldout_log_loss'] = loss(test, ty, x)
    write_csv(root / 'v2/PILOT_WINDOW_RESULTS.csv', per)
    rows = []
    for aa, alg in enumerate(['SCAFFOLD', 'FedAvg']):
        for k in p['pilot_K']:
            xs = np.stack([models[f'seed_{s}_K{k}'][aa] for s in p['pilot_seeds']])
            d = xs-ref['x_ref']
            b = d.mean(axis=0)
            v = float(np.sum((d-b)**2)/(len(d)-1))
            u = float(b@b-v/len(d))
            mse = float(np.mean(np.sum(d*d, axis=1)))
            rows.append(dict(algorithm=alg, K=k, independent_seeds=2, U=u, V=v, MSE=mse,
                             sample_decomposition_residual=mse-u-v, signed_share=u/mse,
                             mean_projection=float(b@ref['direction']), mean_vector=json.dumps(b.tolist()),
                             inference_status='PILOT_R2_INSUFFICIENT_FOR_SIGNIFICANCE', stationary_certified=False))
    write_csv(root / 'v2/PILOT_BIAS_VARIANCE_MSE.csv', rows)
    driftrows = []
    for s in p['pilot_seeds']:
        z = np.load(root / 'v2' / f'pilot_seed_{s}_statistics.npz')
        for k in [8, 16, 32, 64]:
            first = z['batch_raw_sum'][:k].sum(axis=0)/z['batch_count'][:k].sum()
            last = z['batch_raw_sum'][-k:].sum(axis=0)/z['batch_count'][-k:].sum()
            for aa, alg in enumerate(['SCAFFOLD', 'FedAvg']):
                dd = last[aa]-first[aa]
                driftrows.append(dict(seed=s, algorithm=alg, K=k, first_last_norm=float(np.linalg.norm(dd)),
                                      first_last_projection=float(dd@ref['direction']),
                                      inference_status='PILOT_DESCRIPTIVE_NO_EQUIVALENCE_CLAIM'))
    write_csv(root / 'v2/PILOT_TEMPORAL_DIAGNOSTICS.csv', driftrows)
    manifests = list(__import__('csv').DictReader((root / 'v2/PILOT_RUN_MANIFEST.csv').open()))
    median = float(np.median([float(r['elapsed_seconds']) for r in manifests]))
    cost = median*(25600+1024*1280)/(25600+128*1280)*48/3600
    receipt = dict(pilot_completed_pairs=2, pilot_elapsed_median_seconds=median,
                   production_planned_pairs=48, production_completed_pairs=0,
                   pilot_updated_production_serial_hours=cost,
                   original_pre_run_estimate_serial_hours=11.672,
                   precision_status='R2_UNPOWERED_PILOT;NOT_POOLED',
                   stationary_status='NOT_CERTIFIED', all_models_finite=True,
                   max_control_zero_sum=max(float(r['max_zero_sum']) for r in manifests))
    (root / 'v2/PILOT_ANALYSIS_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    analyze(parser.parse_args().root)
