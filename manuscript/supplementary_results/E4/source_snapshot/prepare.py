"""Read-only extraction of original chronological R0 sufficient statistics."""
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_csv(path, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def prepare(original, out):
    original, out = Path(original), Path(out)
    inputs = out / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((original / 'PROTOCOL_FROZEN.json').read_text())
    cells = sorted((c for c in frozen['cells'] if c['regime'] == 'R0'), key=lambda c: c['id'])
    seeds = frozen['production_seeds']
    arrays = {k: [] for k in ['batch_raw_sum', 'batch_count', 'batch_sumsq', 'snapshot',
                              'batch_ctrl', 'batch_ctrl_vector', 'max_zero_sum',
                              'max_relative_zero_sum', 'elapsed', 'rounds', 'key']}
    manifest, comparisons = [], []
    old = list(csv.DictReader((original / 'per_run_estimates.csv').open(newline='')))
    old = {(r['cell_id'], int(r['seed']), r['algorithm']): r for r in old if r['regime'] == 'R0'}
    for cell in cells:
        per_cell = {k: [] for k in arrays}
        for seed in seeds:
            path = original / 'raw' / 'production' / cell['id'] / f'seed_{seed}' / 'result.npz'
            meta_path = path.with_name('run.json')
            meta = json.loads(meta_path.read_text())
            assert meta['cell'] == cell and meta['schedule'] == cell['schedule']
            assert meta['seed'] == seed and meta['phase'] == 'production'
            digest = sha(path)
            with np.load(path, allow_pickle=False) as z:
                assert z['batch_raw_sum'].shape == (64, 2, 124)
                assert np.all(z['batch_count'] == cell['schedule']['batch_length'])
                assert int(z['seed']) == seed
                assert int(z['rounds']) == cell['schedule']['burn'] + 64 * cell['schedule']['batch_length']
                for k in arrays:
                    v = z[k]
                    assert np.isfinite(v).all(), (cell['id'], seed, k)
                    per_cell[k].append(v.copy())
                mean = z['batch_raw_sum'].sum(axis=0) / z['batch_count'].sum()
                second = z['batch_sumsq'].sum(axis=0) / z['batch_count'].sum()
                for a, name in enumerate(['scaffold', 'fedavg']):
                    row = old[cell['id'], seed, name]
                    assert row['raw_sha256'] == digest
                    differences = {
                        'saved_raw_mean': float(np.max(np.abs(mean[a] - z['raw_mean'][a]))),
                        'saved_mean': float(np.max(np.abs(mean[a] - z['mean'][a]))),
                        'old_csv_raw_mean': float(np.max(np.abs(mean[a] - np.array(json.loads(row['raw_mean_vector']))))),
                        'saved_second_moment': float(abs(second[a] - z['second_moment'][a])),
                        'old_csv_second_moment': float(abs(second[a] - float(row['raw_second_moment']))),
                        'actual_vs_primary_batch_sum': float(np.max(np.abs(z['batch_raw_sum'] - z['batch_sum']))),
                    }
                    assert max(differences.values()) < 2e-12, differences
                    comparisons.append(dict(cell_id=cell['id'], seed=seed, algorithm=name,
                                            status='PASS', **differences))
                manifest.append(dict(cell_id=cell['id'], seed=seed, original_path=str(path.resolve()),
                                     original_sha256=digest, original_bytes=path.stat().st_size,
                                     run_json_sha256=sha(meta_path), N=cell['N'], m=cell['m'],
                                     H=cell['H'], gamma=cell['gamma'], burn=cell['schedule']['burn'],
                                     batch_length=cell['schedule']['batch_length'], batches=64,
                                     rounds=int(z['rounds']), elapsed_seconds=float(z['elapsed']),
                                     execution_status='REUSED_COMPLETED_PRODUCTION', new_training=False,
                                     original_precision_status='SEE_HISTORICAL_FULL_RESULTS'))
        for k in arrays:
            arrays[k].append(np.stack(per_cell[k]))
    np.savez_compressed(inputs / 'batches.npz', **{k: np.stack(v) for k, v in arrays.items()},
                        cell_ids=np.array([c['id'] for c in cells]), seeds=np.array(seeds),
                        algorithms=np.array(['SCAFFOLD', 'FedAvg']))
    (inputs / 'R0_CONFIGS.json').write_text(json.dumps(cells, indent=2) + '\n')
    for name in ['PROTOCOL_FROZEN.json', 'DATA_MANIFEST.json', 'optimizer_certificates.json',
                 'reference_optimizers.npz', 'per_run_estimates.csv', 'full_results.csv',
                 'EXPERIMENT_REGISTRY.csv']:
        shutil.copy2(original / name, inputs / name)
    for name in ['training_csr.npz', 'membership.npz']:
        shutil.copy2(original / 'data' / name, inputs / name)
    # Preserve legacy H=4 and all historical records, not just favorable R0 cells.
    for name in ['ARTIFACT_MANIFEST.json', 'SOURCE_MANIFEST.json']:
        if (original / name).exists():
            shutil.copy2(original / name, inputs / name)
    write_csv(out / 'RUN_MANIFEST.csv', manifest)
    write_csv(out / 'PHASE0_RECONSTRUCTION.csv', comparisons)
    return cells


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--original', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    cells = prepare(a.original, a.out)
    print(json.dumps({'cells': len(cells), 'paired_runs': len(cells)*12,
                      'reconstruction': 'PASS', 'new_training': False}))
