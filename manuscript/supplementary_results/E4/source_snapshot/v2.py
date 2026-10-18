"""Separately versioned, cost-bounded E4_v2 pilot/production runner."""
import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from prepare import sha, write_csv


def freeze(root, source):
    root, source = Path(root), Path(source)
    path = root / 'E4_v2_PROTOCOL_FROZEN.json'
    if path.exists():
        raise RuntimeError('E4_v2 protocol exists; do not overwrite.')
    original = json.loads((root / 'E4_v1_PROTOCOL_FROZEN.json').read_text())
    cell = next(c.copy() for c in original['cells'] if c['id'] == original['primary_cell'])
    cell['id'] = 'E4_v2_R0_H4_N128_g0.196078431373'
    cell['roles'] = ['versioned_stationarity_precision_extension']
    cell.pop('schedule')
    cell.pop('estimated_single_run_seconds')
    src = root / 'legacy_source'
    src.mkdir(exist_ok=True)
    shutil.copytree(source / 'study', src / 'study', ignore=shutil.ignore_patterns('__pycache__'), dirs_exist_ok=True)
    for name in ['requirements.lock', 'run.py']:
        shutil.copy2(source / name, src / name)
    hashes = {p.relative_to(src).as_posix(): sha(p) for p in sorted(src.rglob('*')) if p.is_file()}
    expected = json.loads((root / 'inputs/PROTOCOL_FROZEN.json').read_text())['source_hashes']
    for name in ['study/kernels.py', 'study/model.py', 'study/data.py', 'study/engine.py']:
        assert hashes[name] == expected[name], name
    proto = dict(version='E4_v2', frozen_utc=datetime.now(timezone.utc).isoformat(), cell=cell,
                 pilot_seeds=[30001, 30002], production_seeds=list(range(31001, 31049)),
                 pilot_schedule=dict(burn=25600, batch_length=1280, batches=128, primary_batches=128),
                 production_schedule=dict(burn=25600, batch_length=1280, batches=1024, primary_batches=1024),
                 pilot_K=[1, 2, 4, 8, 16, 32, 64, 128],
                 production_K=[1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024],
                 source_hashes=hashes, arithmetic='UNCHANGED_FROZEN_V1_KERNEL_NO_ZERO_SUM_PROJECTION',
                 data_hashes={p.name: sha(p) for p in (root / 'inputs').iterdir() if p.name in
                              ['training_csr.npz', 'membership.npz', 'reference_optimizers.npz']},
                 root_seed_pooling=False, v1_primary_inference_unchanged=True,
                 pilot_scope='Two independent fresh paired runs for cost/stability diagnosis; R=2 cannot settle statistical significance',
                 production_scope='Single primary setting only; planned not executed by pilot command',
                 analysis='Same corrected U/V/MSE definitions, K-family paired bootstrap and temporal margins as v1; separate bootstrap seed202610095',
                 production_bootstrap_draws=19999, production_bootstrap_seed=202610095,
                 pilot_execution_budget_seconds=600,
                 decision='No selection of favorable seeds, no pooling pilot or v1 into production; full production requires separate explicit production invocation',
                 checkpoint='original engine.run_one deterministic indexed streams; --resume required')
    path.write_text(json.dumps(proto, indent=2)+'\n')
    path.with_suffix('.sha256').write_text(sha(path)+'\n')
    print(json.dumps({'protocol': str(path), 'sha256': sha(path), 'new_arithmetic': False}))


def run(root, phase, max_seconds, resume=False, seed=None):
    root = Path(root).resolve()
    p = json.loads((root / 'E4_v2_PROTOCOL_FROZEN.json').read_text())
    assert sha(root / 'E4_v2_PROTOCOL_FROZEN.json') == (root / 'E4_v2_PROTOCOL_FROZEN.sha256').read_text().strip()
    for name, digest in p['source_hashes'].items():
        assert sha(root / 'legacy_source' / name) == digest, ('SOURCE_HASH_MISMATCH', name)
    for name, digest in p['data_hashes'].items():
        assert sha(root / 'inputs' / name) == digest, ('DATA_HASH_MISMATCH', name)
    sys.path.insert(0, str(root / 'legacy_source'))
    from study.engine import run_one
    from scipy import sparse
    from study.tests import test_logistic_reference_production_h1_resume, test_r0_h1_allocation_identity
    if not (root / 'v2/NUMERICAL_PRECHECK.json').exists():
        test_logistic_reference_production_h1_resume()
        test_r0_h1_allocation_identity()
        (root / 'v2').mkdir(exist_ok=True)
        (root / 'v2/NUMERICAL_PRECHECK.json').write_text(json.dumps(dict(
            status='PASS', tests=['logistic reference/production common-noise and chunk-resume', 'short H1 cross-allocation'],
            source_sha256=p['source_hashes']['study/kernels.py'],
            historical_long_H1_identity_failures='UNRESOLVED_PRESERVED; no new H1 full-horizon rerun',
            changed_arithmetic=False), indent=2)+'\n')
    Z = sparse.load_npz(root / 'inputs/training_csr.npz')
    y = np.load(root / 'inputs/membership.npz')['labels']
    ref = dict(np.load(root / 'inputs/reference_optimizers.npz'))
    schedule = p[f'{phase}_schedule']
    seeds = p[f'{phase}_seeds']
    if seed is not None:
        assert seed in seeds
        seeds = [seed]
    deadline = time.monotonic()+max_seconds
    receipt = []
    for s in seeds:
        if time.monotonic() >= deadline:
            receipt.append(dict(seed=s, phase=phase, status='NOT_STARTED_BUDGET', completed=False))
            continue
        t0 = time.monotonic()
        completed = run_one(p['cell'], s, phase, schedule, root / 'v2', Z=Z, y=y, ref=ref,
                            resume=resume, deadline=deadline, max_memory_gb=4)
        receipt.append(dict(seed=s, phase=phase, status='COMPLETED' if completed else 'CHECKPOINTED_RESOURCE_LIMIT',
                            completed=bool(completed), wall_seconds=time.monotonic()-t0))
        print(json.dumps(receipt[-1]), flush=True)
    (root / f'v2/{phase.upper()}_EXECUTION_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


def pilot_summary(root):
    root = Path(root)
    p = json.loads((root / 'E4_v2_PROTOCOL_FROZEN.json').read_text())
    ref = np.load(root / 'inputs/reference_optimizers.npz')
    arrays, rows, manifests = {}, [], []
    for seed in p['pilot_seeds']:
        directory = root / 'v2/raw/pilot' / p['cell']['id'] / f'seed_{seed}'
        full = directory / 'result.npz'
        checkpoint = directory / 'checkpoint.npz'
        if not checkpoint.exists():
            continue
        z = np.load(full if full.exists() else checkpoint)
        valid = int(np.sum(z['batch_count'] == p['pilot_schedule']['batch_length']))
        compact = {k: z[k] for k in ['batch_raw_sum', 'batch_count', 'batch_sumsq', 'snapshot', 'max_zero_sum',
                                      'max_relative_zero_sum', 't', 'elapsed', 'key', 'total']}
        out = root / 'v2' / f'pilot_seed_{seed}_statistics.npz'
        np.savez_compressed(out, **compact)
        manifests.append(dict(seed=seed, completed=full.exists(), valid_batches=valid, total_batches=128,
                              current_round=int(z['t']), total_rounds=int(z['total']),
                              elapsed_seconds=float(z['elapsed']), source_path=str((full if full.exists() else checkpoint).resolve()),
                              source_sha256=sha(full if full.exists() else checkpoint), compact_sha256=sha(out),
                              max_zero_sum=float(z['max_zero_sum']), max_relative_zero_sum=float(z['max_relative_zero_sum']),
                              status='DIAGNOSTIC_PILOT_ONLY_NOT_POOLED'))
        for k in p['pilot_K']:
            if k > valid:
                continue
            end = valid
            y = z['batch_raw_sum'][end-k:end].sum(axis=0)/z['batch_count'][end-k:end].sum()
            arrays[f'seed_{seed}_K{k}'] = y
            for aa, alg in enumerate(['SCAFFOLD', 'FedAvg']):
                dd = y[aa]-ref['x_ref']
                rows.append(dict(seed=seed, algorithm=alg, K=k, start_batch=end-k+1, end_batch=end,
                                 checkpoint_count=int(z['batch_count'][end-k:end].sum()),
                                 model_array_key=f'v2/pilot_models.npz:seed_{seed}_K{k}[{aa},:]',
                                 squared_parameter_error=float(dd@dd), projection=float(dd@ref['direction']),
                                 completed_run=full.exists(), status='PILOT_R2_INSUFFICIENT_FOR_SIGNIFICANCE'))
    if rows:
        np.savez_compressed(root / 'v2/pilot_models.npz', **arrays)
        write_csv(root / 'v2/PILOT_WINDOW_RESULTS.csv', rows)
        write_csv(root / 'v2/PILOT_RUN_MANIFEST.csv', manifests)
    print(json.dumps({'pilot_runs': len(manifests), 'model_rows': len(rows), 'production_runs_completed': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['freeze', 'pilot', 'production', 'pilot_summary'])
    parser.add_argument('--root', required=True)
    parser.add_argument('--source')
    parser.add_argument('--max-seconds', type=float, default=600)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--seed', type=int)
    a = parser.parse_args()
    if a.command == 'freeze':
        freeze(a.root, a.source)
    elif a.command == 'pilot_summary':
        pilot_summary(a.root)
    else:
        run(a.root, a.command, a.max_seconds, a.resume, a.seed)
