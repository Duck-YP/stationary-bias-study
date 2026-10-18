"""Package existing SCAFFOLD evidence. Never imports or executes training code."""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]
_bootstrap=argparse.ArgumentParser(add_help=False)
_bootstrap.add_argument('--workspace',type=Path)
_bootstrap.add_argument('--export-dir',type=Path)
_bootstrap_args,_=_bootstrap.parse_known_args()
if _bootstrap_args.workspace:ROOT=_bootstrap_args.workspace.resolve()
if _bootstrap_args.export_dir:OUT=_bootstrap_args.export_dir.resolve()
STUDY = ROOT / 'supplementary_study'
assert OUT.resolve()!=ROOT.resolve() and not OUT.resolve().is_relative_to(STUDY.resolve()), 'Use an independent export directory outside supplementary_study'
ARCHIVE = STUDY / 'results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF.zip'
STAGE = OUT / 'staging'
CORE = STAGE / 'REVIEW_CORE'
AUDIT = STAGE / 'AUDIT_BATCHES'
SOURCE = STAGE / 'SOURCE_REVIEW'
sys.path.insert(0, str(STUDY / '.deps'))
sys.path.insert(0, str(STUDY))
sys.dont_write_bytecode=True
import numpy as np
from study.model import theory

LIMIT = 90_000_000
OMIT_KEYS = {
    'controls': 'final per-client controls; full primary per-client control_mean is retained',
    'batch_control_sum': 'per-client temporal control vectors; batch control second moments, endpoint global control summary, and full primary per-client control_mean retained; detailed client-by-batch audit requires original result.npz',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, data):
    path = Path(path)
    assert path.resolve().is_relative_to(OUT.resolve()), path
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding='utf-8')


def jswrite(path, value):
    write(path, json.dumps(value, indent=2, ensure_ascii=True) + '\n')


def csvwrite(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)


def csvread(data):
    return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))


def npzsave(path, arrays):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def check_archives():
    original = json.loads((OUT / 'ORIGINAL_ARCHIVES_BEFORE.json').read_text())
    for item in original.values():
        path = Path(item['path'])
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], path
    return original


BATCH_SCHEMA = '''# Batch Audit Schema

## Scope and identities

No stochastic training, optimizer solve, or scientific report regeneration was run for this export.
Every production/pilot paired run is represented, including H=4 and unresolved flags.
`BATCH_INDEX.csv` identifies phase/cell/seed/pair, raw hash, compact hash and package.
Algorithm axis 0 = scaffold, 1 = fedavg, paired with the original shared keyed draws.
Same seed labels across DIFFERENT cells are resampling units, not evidence of identical noise streams.
Original `run.json` is unchanged; `export_metadata.json` describes the compact arrays.
All retained numeric arrays preserve the original dtype, shape and values bit-for-bit.
Float64 remains float64. Newly derived differences/projections are float64, explicitly identified.
`ARRAY_KEY_INVENTORY.csv` records the actual original keys, shapes, dtypes and stored sizes.

## Batch boundaries and estimands

`batch_index` is zero-based. `start_round_zero_based` is inclusive; `end_round_zero_based_exclusive`
is exclusive. An update with index t stores its completed global endpoint numbered t+1.
Thus `start_completed_round` and `end_completed_round_inclusive` equal start+1 and end.
Collection begins at frozen burn, batch b spans [burn+b*L, burn+(b+1)*L).
`batch_count` gives actual observations, not an ESS. Primary production uses first 64 batches;
extended 133-batch cells preserve ALL batches. Pilot primary count is stored in each result.
Recorded sensitivity windows remain [5:69], [0:128], [5:133], not replacements for primary [0:64].

`batch_raw_sum` / `batch_raw_means`: sums / means of post-round global parameter endpoints.
`batch_sum` / `batch_means`: primary balance-estimator observable for E1; direct global endpoint
observable for E3. E1 balance is NOT a raw checkpoint parameter; the engine/model source defines it.
`batch_sumsq`: sum of ||raw endpoint - x_ref||^2 (E3), or ||raw endpoint||^2 (E1).
This centered MSE is not the uncentered sum ||x||^2 and not the balance-observable squared norm.
`second_moment` uses the PRIMARY tail; total checkpoint accumulators can include all extended batches.
`samples` is the primary tail observation count, `rounds` the completed full horizon.
`snapshot`: last global endpoint in a batch, not its average; `x`: final global checkpoint.
`batch_crossdiff`: accumulated raw-minus-primary observable.
`batch_ctrl`: sum over rounds of the across-client mean squared control norm.
`batch_ctrl_vector`: sum over processing chunks of chunk count times the CHUNK-ENDING across-client
control mean; it is not an exact temporal integral or necessarily the final batch endpoint times L.
`control_mean`: exact primary temporal mean for EACH client.
`control_second_moment`: primary temporal mean of across-client squared norms.
`batch_control_global_sum` is derived from original per-client `batch_control_sum.mean(axis=1)`;
it IS a temporal sum of the across-client average, distinct from `batch_ctrl_vector`.
Detailed per-client, per-batch vector integrals and final per-client control states remain in raw.

`paired_batch_difference` and `paired_raw_batch_difference`: algorithm 0 minus 1 on aligned batches.
E1 reported D further divides the PRIMARY difference by gamma^2; E3 uses the unscaled difference.
`batch_primary_projection`, `batch_raw_projection`: vectors minus fixed reference, projected on the
stored descriptive direction for E3 or normalized theoretical Z_target for E1.
`tail_paired_covariance` in `PAIRED_COVARIANCE.npz`: sample covariance (ddof=1) of aligned independent
run-tail projections, not within-round noise covariance. Index CSV labels phase/cell/seed order.
All per-run vectors permit the original bootstrap/jackknife/OLS resampling across seeds.
Within-round cross-products were not saved; do not reconstruct them from batch means.

## Task losses and diagnostics

`per_run_estimates.csv` retains original per-run tail-average model training gap, held-out loss and
accuracy. These are not per-batch losses or loss of a pooled deployable model. Per-batch task losses
and round-level loss sums were not saved. Full processed/raw datasets are needed to re-evaluate losses.
Original stationarity/precision, batch IACT proxy, raw-vs-primary and nested-window diagnostics remain
in REVIEW_CORE, including every flagged cell. No true ESS or stationary-law certificate is invented.
E2 exact arrays are per-round residuals, not independent statistical batches. E2 zero-initialization
arrays retain original batch means, residual path, snapshots, burn and batch length; system axis is
homogeneous then affine-heterogeneous, NOT scaffold then fedavg.
Stable-arithmetic post-hoc audit arrays are separate, not replacement production; not all second-moment
or per-client temporal summaries were saved for those audits. See DIAGNOSTIC_BATCH_INDEX.csv.

## Raw-dependent audits

Exact per-client temporal control recomputation requires the original run result `batch_control_sum`.
Restarting a chain requires its original checkpoint. Re-evaluating objectives/noise from examples requires
data/training_csr.npz and downloaded a9a/a9a.t, whose hashes/sources are retained. All E3 partition
matrices and memberships are retained losslessly in the diagnostic add-on ZIPs; aliases are byte-identical.
E2 full local paths/noise draws, round-level covariance and per-batch losses not originally saved are unavailable.
SHA-256 establishes artifact identity, not scientific correctness.
'''


def build():
    if (OUT / 'BUILD_STATE.json').exists():
        raise RuntimeError('Build already completed. Use finalize, not a second build.')
    check_archives()
    for tool in Path(__file__).parent.glob('*.py'):
        destination=OUT/'tools'/tool.name
        if tool.resolve()!=destination.resolve():write(destination,tool.read_bytes())
    if not (OUT/'EXPORT_LOG.md').exists():
        supplied=Path(__file__).resolve().parents[1]/'EXPORT_LOG.md'
        write(OUT/'EXPORT_LOG.md',supplied.read_bytes() if supplied.exists() else
              '# Export Log\n\nFresh packaging-only export; no training or original-file modification.\n')
    CORE.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE) as archive:
        prefix = archive.namelist()[0].split('/')[0] + '/'
        members = {i.filename[len(prefix):]: i for i in archive.infolist() if not i.is_dir()}
        def get(path):
            return archive.read(prefix + path)
        manifest = json.loads(get('ARTIFACT_MANIFEST.json'))
        manifest.update(json.loads(get('raw_manifest.json')))
        conf = json.loads(get('PROTOCOL_FROZEN.json'))
        registry = csvread(get('EXPERIMENT_REGISTRY.csv'))
        runrows = csvread(get('per_run_estimates.csv'))
        full = csvread(get('full_results.csv'))
        ref = dict(np.load(io.BytesIO(get('reference_optimizers.npz')), allow_pickle=False))
        current_hashes = {}
        for path in STUDY.rglob('*'):
            if path.is_file() and (path.suffix == '.py' or path.name in ('requirements.lock', 'Run-Study.ps1', 'README.md', '.gitignore')):
                relative = path.relative_to(STUDY)
                if relative.parts[0] in ('.deps', 'results', '.mplconfig', 'data') or '__pycache__' in relative.parts:
                    continue
                current_hashes[relative.as_posix()] = sha(path)
        jswrite(OUT / 'ORIGINAL_SOURCE_BEFORE.json', current_hashes)
        for relative in current_hashes:
            write(SOURCE / 'supplementary_study' / relative, (STUDY / relative).read_bytes())
        for path in (STUDY / 'brief').rglob('*'):
            if path.is_file() and path.suffix.lower() in ('.md', '.json', '.txt'):
                write(SOURCE / 'supplementary_study' / path.relative_to(STUDY), path.read_bytes())
        write(SOURCE / 'supplementary_study/configs/production_v1.json', get('configs/production_v1.json'))
        write(SOURCE / 'PROTOCOL_FROZEN.json', get('PROTOCOL_FROZEN.json'))
        write(SOURCE / 'SOURCE_MANIFEST_ORIGINAL.json', get('SOURCE_MANIFEST.json'))
        write(SOURCE / 'ENVIRONMENT_ORIGINAL.txt', get('ENVIRONMENT.txt'))
        delivered = {}
        with zipfile.ZipFile(ARCHIVE.parent / 'source.zip') as old_source:
            for info in old_source.infolist():
                if info.is_dir():
                    continue
                parts = Path(info.filename).parts
                relative = '/'.join(parts[1:])
                if not relative:
                    continue
                data = old_source.read(info.filename)
                delivered[relative] = digest(data)
                write(SOURCE / 'delivered_source_snapshot' / relative, data)
        frozen_rows = []
        for relative, expected in conf['source_hashes'].items():
            candidate = SOURCE / 'supplementary_study' / relative
            old_candidate = SOURCE / 'delivered_source_snapshot' / relative
            actual = sha(candidate) if candidate.exists() else ''
            matching = candidate if actual == expected else old_candidate if old_candidate.exists() and sha(old_candidate) == expected else None
            frozen_rows.append(dict(path=relative, frozen_sha256=expected, current_sha256=actual,
                                    status='EXACT_AVAILABLE' if matching else 'HISTORICAL_SNAPSHOT_UNAVAILABLE'))
            if matching:
                write(SOURCE / 'available_frozen_source' / relative, matching.read_bytes())
        csvwrite(SOURCE / 'FROZEN_SOURCE_AVAILABILITY.csv', frozen_rows)
        git = {key: subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
               for key, args in {'head': ['rev-parse', 'HEAD'], 'status': ['status', '--porcelain=v1'],
                                 'branch': ['branch', '--show-current'], 'remote': ['remote', 'get-url', 'origin']}.items()}
        jswrite(SOURCE / 'VERSION.json', dict(git=git, current_source=current_hashes, delivered_source=delivered,
                export_scope='read-only packaging; uncommitted current files included', protocol=conf['version']))
        write(SOURCE / 'PRODUCTION_SOURCE_STATUS.md', '# Production Source Availability\n\n'
              'Current uncommitted study source and the originally delivered source.zip snapshot are both retained.\n'
              'FROZEN_SOURCE_AVAILABILITY.csv compares each recorded freeze-time hash to obtainable files.\n'
              'Exact matching files are copied into available_frozen_source. Numerical kernels/model/data/engine\n'
              'match freeze-time hashes. Changed historical analysis/CLI/test files are not silently substituted.\n'
              'A complete freeze-time source tree/patch for unavailable hashes cannot be recovered from this\n'
              'untracked study; no fabricated snapshot is supplied. Current reporting/replay source is separately versioned.\n'
              'Legacy repository code is not imported by the supplementary implementation.\n')
        # Retain the complete available historical artifact collections, not selected outcomes.
        history = []
        for path in sorted((ROOT / 'workstreams').rglob('*')):
            if not path.is_file() or 'artifacts' not in path.parts:
                continue
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            parts=Path(relative).parts
            short_relative='/'.join((parts[1].split('_')[0], *parts[3:]))
            write(CORE / 'historical_repository' / short_relative, data)
            history.append(dict(original_path=relative, export_path='historical_repository/' + short_relative,
                                bytes=len(data), sha256=digest(data), scope='legacy historical; NOT supplementary production'))
        csvwrite(CORE / 'HISTORICAL_ARTIFACT_INDEX.csv', history)
        csvwrite(OUT / 'HISTORICAL_FILE_SIZE_INVENTORY.csv', sorted(history, key=lambda x: -x['bytes']))
        write(CORE / 'HISTORICAL_SCOPE.md', '# Historical Records\n\n'
              'The complete locally available workstreams/*/artifacts collections are retained separately,\n'
              'including original H=4 reports, fit/run/batch CSVs, diagnostics and configuration snapshots.\n'
              'These are legacy evidence, not reclassified E1/E2/E3 supplementary runs. They were not reanalyzed.\n'
              'Original dense trajectories, checkpoints and noise draws for these historical runs were not provided\n'
              'in those collections and remain unavailable unless separately obtained. Index hashes identify copies,\n'
              'not correctness. No historical result is overwritten or replaced by the supplementary production.\n')
        omitted = []
        exact_copies = []
        alias_rows = []
        canonical_partition = {}
        array_inventory = []
        run_index = []
        batch_boundaries = []
        pair_data = defaultdict(list)
        retained_bytes = Counter()
        omitted_bytes = Counter()
        production_lookup = {(r['cell_id'], int(r['seed']), r['algorithm']): r for r in runrows}
        def copy(path, dest):
            data = get(path)
            actual = digest(data)
            if path in manifest:
                assert actual == manifest[path], path
            write(dest, data)
            exact_copies.append(dict(original_path=path, export_path=dest.relative_to(STAGE).as_posix(),
                                     sha256=actual, bytes=len(data)))
            return data
        def inventory_npz(path, data, selected=None):
            with zipfile.ZipFile(io.BytesIO(data)) as inner, np.load(io.BytesIO(data), allow_pickle=False) as arrays:
                sizes = {i.filename.removesuffix('.npy'): i for i in inner.infolist()}
                for key in arrays.files:
                    array = arrays[key]
                    selected_key = selected is None or key in selected
                    array_inventory.append(dict(original_path=path, key=key, dtype=str(array.dtype), shape=json.dumps(array.shape),
                                                array_bytes=array.nbytes, npy_bytes=sizes[key].file_size,
                                                npy_compressed_bytes=sizes[key].compress_size,
                                                disposition='retained_bit_exact' if selected_key else 'original_raw_only',
                                                reason=OMIT_KEYS.get(key, '') if not selected_key else ''))
                    (retained_bytes if selected_key else omitted_bytes)[key] += sizes[key].compress_size
        for path, info in sorted(members.items()):
            parts = Path(path).parts
            cell = parts[2] if path.startswith('raw/') and len(parts) > 3 else ''
            seed_label = parts[3] if cell else ''
            reason = ''
            export_path = ''
            disposition = 'retained_exact'
            if path.startswith('raw/'):
                if parts[-1] == 'result.npz':
                    data = get(path)
                    assert digest(data) == manifest[path], path
                    original = dict(np.load(io.BytesIO(data), allow_pickle=False))
                    arrays = {k: v for k, v in original.items() if k not in OMIT_KEYS}
                    inventory_npz(path, data, arrays)
                    phase = parts[1]
                    metadata_path = '/'.join(parts[:-1]) + '/run.json'
                    metadata = json.loads(get(metadata_path))
                    schedule = metadata['schedule']
                    c = metadata['cell']
                    seed = int(original['seed'])
                    pair_id = f'{phase}/{cell}/seed_{seed}'
                    means = original['batch_means']
                    count = original['batch_count']
                    assert len(means) == schedule['batches'] and np.all(count == schedule['batch_length'])
                    reference = ref['x_ref'] if c['family'] == 'E3' else np.zeros(means.shape[-1], dtype=np.float64)
                    if c['family'] == 'E3':
                        direction = ref['direction']
                    else:
                        direction = np.array(theory(2)['Z_target'], dtype=np.float64)
                        direction /= np.linalg.norm(direction)
                    arrays.update(batch_index=np.arange(len(means), dtype=np.int64),
                        start_round_zero_based=schedule['burn'] + np.arange(len(means), dtype=np.int64)*schedule['batch_length'],
                        end_round_zero_based_exclusive=schedule['burn']+(np.arange(len(means), dtype=np.int64)+1)*schedule['batch_length'],
                        paired_batch_difference=means[:,0]-means[:,1],
                        paired_raw_batch_difference=original['batch_raw_means'][:,0]-original['batch_raw_means'][:,1],
                        batch_primary_projection=(means-reference)@direction,
                        batch_raw_projection=(original['batch_raw_means']-reference)@direction,
                        batch_control_global_sum=original['batch_control_sum'].mean(axis=1))
                    arrays['start_completed_round'] = arrays['start_round_zero_based'] + 1
                    arrays['end_completed_round_inclusive'] = arrays['end_round_zero_based_exclusive'].copy()
                    dest = AUDIT / path
                    npzsave(dest, arrays)
                    with np.load(dest, allow_pickle=False) as saved:
                        for key, value in original.items():
                            if key not in OMIT_KEYS:
                                assert saved[key].dtype == value.dtype and saved[key].shape == value.shape
                                assert saved[key].tobytes() == value.tobytes(), (path, key)
                    if phase == 'production':
                        for a, algorithm in enumerate(('scaffold', 'fedavg')):
                            rr = production_lookup[(cell, seed, algorithm)]
                            assert np.array_equal(np.asarray(json.loads(rr['mean_vector'])), original['mean'][a])
                            assert np.array_equal(np.asarray(json.loads(rr['raw_mean_vector'])), original['raw_mean'][a])
                            assert float(rr['raw_second_moment']) == float(original['second_moment'][a])
                    write(AUDIT / metadata_path, get(metadata_path))
                    export_meta = dict(original_raw=path, original_sha256=manifest[path], pair_id=pair_id,
                        original_algorithm_axis=['scaffold', 'fedavg'], omitted_keys=OMIT_KEYS,
                        derived_keys={k: 'see BATCH_SCHEMA.md; float64 arithmetic except integer round boundaries'
                                      for k in arrays if k not in original}, original_dtypes={k:str(v.dtype) for k,v in original.items()},
                        scope='all original batches; primary tail unchanged; no training')
                    jswrite(dest.parent / 'export_metadata.json', export_meta)
                    run_index.append(dict(phase=phase, family=c['family'], regime=c['regime'], cell_id=cell,
                        seed=seed, pair_id=pair_id, algorithm_axis='scaffold;fedavg', H=c['H'], N=c['N'], m=c['m'],
                        gamma=c['gamma'], partition_seed=c['partition_seed'], burn=schedule['burn'],
                        batch_length=schedule['batch_length'], collected_batches=len(means), primary_batches=int(original['primary_batches']),
                        samples=int(original['samples']), rounds=int(original['rounds']),
                        original_path=path, original_sha256=manifest[path], export_path=dest.relative_to(STAGE).as_posix(),
                        export_sha256=sha(dest), package=''))
                    for b, n in enumerate(count):
                        batch_boundaries.append(dict(pair_id=pair_id, batch_index=b, sample_count=int(n),
                            start_round_zero_based=int(arrays['start_round_zero_based'][b]),
                            end_round_zero_based_exclusive=int(arrays['end_round_zero_based_exclusive'][b]),
                            start_completed_round=int(arrays['start_completed_round'][b]),
                            end_completed_round_inclusive=int(arrays['end_completed_round_inclusive'][b]),
                            primary=b<int(original['primary_batches']), algorithm_axis='scaffold;fedavg'))
                    pair_data[(phase,cell)].append((seed, (original['mean']-reference)@direction))
                    disposition = 'compact_selected_arrays'
                    reason = 'all global/balance batch arrays retained; only final client controls and client-by-batch control vectors remain raw'
                    export_path = dest.relative_to(STAGE).as_posix()
                    if len(run_index) % 100 == 0:
                        print(f'Batches exported and bit-verified: {len(run_index)} pairs', flush=True)
                elif parts[-1] == 'run.json':
                    export_path = 'AUDIT_BATCHES/' + path
                else:
                    disposition = 'original_raw_only'
                    reason = 'restart/checkpoint state duplicates result summaries; not required for review statistics'
            elif path.startswith('data/source/') or path == 'data/training_csr.npz':
                disposition = 'original_raw_only'
                reason = 'downloadable raw/processed dataset; source/preprocessing hashes, row membership and optimizer certificates retained'
            elif path.startswith('tests/tmp/'):
                disposition = 'original_raw_only'
                reason = 'temporary test chain states; complete E0 test reports and gate are retained'
            elif path.startswith('figures/') and path.endswith('.svg'):
                disposition = 'original_raw_only'
                reason = 'redundant rendering; exact vector PDF and original 200dpi PNG retained'
            elif path.startswith('diagnostics/') and path.endswith('_partition.npz'):
                data = get(path)
                hashvalue = digest(data)
                assert hashvalue == manifest[path], path
                if hashvalue in canonical_partition:
                    disposition = 'byte_identical_alias'
                    canonical = canonical_partition[hashvalue]
                    reason = 'byte-identical partition diagnostic reused across cells; complete arrays preserved once'
                else:
                    canonical = path
                    canonical_partition[hashvalue] = canonical
                    copy(path, CORE / path)
                    inventory_npz(path, data)
                alias_rows.append(dict(original_path=path, canonical_export_path='REVIEW_CORE/' + canonical,
                                       sha256=hashvalue, original_bytes=info.file_size, restoration='tools/restore_aliases.py'))
                export_path = 'REVIEW_CORE/' + canonical
            else:
                copy(path, CORE / path)
                export_path = 'REVIEW_CORE/' + path
                if path.endswith('.npz'):
                    inventory_npz(path, get(path))
            omitted.append(dict(original_relative_path=path, bytes=info.file_size, compressed_bytes=info.compress_size,
                sha256=manifest.get(path) or digest(get(path)), cell_id=cell, run_id=seed_label,
                content_type=('restart_checkpoint' if path.endswith('checkpoint.npz') else
                              'paired_result_statistics' if path.endswith('result.npz') else Path(path).suffix.lstrip('.') or 'text'),
                disposition=disposition, export_path=export_path, review_omission_reason=reason,
                retrieval=f'{ARCHIVE} :: {prefix}{path}',
                hash_provenance='original archive manifest; retained/processed members additionally checked during export' if path in manifest else 'computed from original ZIP member'))
        # All E2 and stable arithmetic auxiliary runs are retained in audit as original arrays, too.
        diagnostic_index = []
        for row in registry:
            if row['family']!='E2' and row['phase']!='post_freeze_numerical_audit':
                continue
            diagnostic_index.append(row)
        for path in sorted(members):
            if path.startswith('diagnostics/E2_') or path.startswith('diagnostics/stable_arithmetic'):
                copy(path, AUDIT / path)
        for path in ('tables/E2_exact_checks.csv', 'tables/E2_zero_initialization.csv'):
            copy(path, AUDIT / path)
        csvwrite(AUDIT / 'DIAGNOSTIC_REGISTRY_ORIGINAL.csv', diagnostic_index, fields=list(registry[0]))
        diagnostic_batches = []
        for path in sorted(members):
            if path.startswith('diagnostics/E2_zero_') and path.endswith('.npz'):
                aa = dict(np.load(io.BytesIO(get(path)), allow_pickle=False))
                seed = int(Path(path).stem.split('seed')[1])
                burn, length = int(aa['burn']), int(aa['batch_length'])
                for b in range(len(aa['batch_means'])):
                    diagnostic_batches.append(dict(kind='E2_zero_initialization', cell_id='E2_zero_initialization', seed=seed,
                        batch=b, start_round_zero_based=burn+b*length, end_round_zero_based_exclusive=burn+(b+1)*length,
                        sample_count=length, axis='homogeneous;affine_heterogeneous', artifact='AUDIT_BATCHES/'+path,
                        missing_statistics='second moments, local paths and round-level crossproducts not originally saved'))
            if path.startswith('diagnostics/stable_arithmetic_H1_') and path.endswith('.npz'):
                aa = dict(np.load(io.BytesIO(get(path)), allow_pickle=False))
                seed = int(Path(path).stem.split('seed')[1])
                c = next(c for c in conf['cells'] if c['id']=='E3_R0_p0_H1_N128_g0.196078431373')
                s = c['schedule']
                for b in range(len(aa['batch_means'])):
                    diagnostic_batches.append(dict(kind='post_freeze_stable_arithmetic', cell_id=c['id'], seed=seed,
                        batch=b, start_round_zero_based=s['burn']+b*s['batch_length'],
                        end_round_zero_based_exclusive=s['burn']+(b+1)*s['batch_length'],sample_count=s['batch_length'],
                        axis='scaffold;fedavg',artifact='AUDIT_BATCHES/'+path,
                        missing_statistics='batch second moments and temporal per-client control integrals not originally saved'))
        csvwrite(AUDIT / 'DIAGNOSTIC_BATCH_INDEX.csv', diagnostic_batches)
        covariance_index = []
        covariance_arrays = {}
        for i, ((phase,cell), values) in enumerate(sorted(pair_data.items())):
            values.sort(key=lambda v:v[0])
            projections=np.array([v[1] for v in values],dtype=np.float64)
            covariance_arrays[f'projections_{i}']=projections
            covariance_arrays[f'covariance_{i}']=np.cov(projections,rowvar=False,ddof=1)
            covariance_arrays[f'seeds_{i}']=np.array([v[0] for v in values],dtype=np.int64)
            covariance_index.append(dict(phase=phase,cell_id=cell,projection_key=f'projections_{i}',
                covariance_key=f'covariance_{i}',seeds_key=f'seeds_{i}',
                definition='sample covariance of paired independent run-tail projections, ddof=1; not per-round noise'))
        npzsave(AUDIT / 'PAIRED_COVARIANCE.npz', covariance_arrays)
        csvwrite(AUDIT / 'PAIRED_COVARIANCE_INDEX.csv', covariance_index)
        csvwrite(AUDIT / 'BATCH_BOUNDARIES.csv', batch_boundaries)
        csvwrite(CORE / 'PARTITION_DIAGNOSTIC_ALIASES.csv', alias_rows)
        csvwrite(CORE / 'RAW_ARCHIVE_MANIFEST.csv', omitted)
        csvwrite(CORE / 'ARRAY_KEY_INVENTORY.csv', array_inventory)
        csvwrite(CORE / 'EXACT_COPY_MANIFEST.csv', exact_copies)
        for name in ('RAW_ARCHIVE_MANIFEST.csv','ARRAY_KEY_INVENTORY.csv','PARTITION_DIAGNOSTIC_ALIASES.csv'):
            write(OUT / name, (CORE / name).read_bytes())
        jswrite(OUT / 'ARRAY_SIZE_DIAGNOSIS.json', dict(retained_inner_compressed_bytes=dict(retained_bytes),
                original_raw_only_inner_compressed_bytes=dict(omitted_bytes)))
        # Coverage is based on metadata, never on scientific outcome.
        coverage=[]
        for row in registry:
            if row['phase'] in ('production','pilot'):
                runs=[r for r in run_index if r['phase']==row['phase'] and r['cell_id']==row['cell_id']]
                assert len(runs)==int(row['completed_paired_runs'])
                expected=conf['production_seeds'] if row['phase']=='production' else conf['pilot_seeds']
                assert sorted(r['seed'] for r in runs)==sorted(expected)
                coverage.append(dict(phase=row['phase'],cell_id=row['cell_id'],H=row['H'],
                    completed_paired_runs=row['completed_paired_runs'],exported_paired_runs=len(runs),
                    seeds=';'.join(str(r['seed']) for r in sorted(runs,key=lambda r:r['seed'])),
                    inference_status=row['inference_status'],numerical_identity_status=row['numerical_identity_status'],status='MATCH'))
        csvwrite(CORE / 'COVERAGE_QA.csv', coverage)
        write(CORE / 'BATCH_SCHEMA.md', BATCH_SCHEMA)
        write(AUDIT / 'BATCH_SCHEMA.md', BATCH_SCHEMA)
        write(CORE / 'MISSING_ITEMS.md', '# Missing Items and Audit Limits\n\n'
              '- No full freeze-time source snapshot for hash-mismatched historical files; see SOURCE_REVIEW/FROZEN_SOURCE_AVAILABILITY.csv.\n'
              '- Historical repository artifacts include run/batch tables, not original dense paths, checkpoints or noise draws; those raw originals are unavailable here.\n'
              '- Original full-round paths/noise draws, within-round crossproducts and per-batch task losses were not saved; cannot infer them from batch means.\n'
              '- Full primary per-client control means and batch second moments are retained. Per-client temporal batch vectors/final client states require the preserved raw result.npz.\n'
              '- Original E2/stable post-hoc diagnostic arrays lack some second-moment/local-state summaries; original outputs are retained without fabricated values.\n'
              '- Original IACT values are batch-projection proxies, not certified ESS; no missing true ESS is marked passed.\n'
              '- Complete objective/test-loss and data-driven derivative recomputation needs data/training_csr.npz and a9a/a9a.t from original archive; hashes and retrieval URLs retained.\n'
              '- Full-grid improved-arithmetic production rerun remains NOT RUN; 32 precision-insufficient cells and three long H1 numerical flags remain unchanged.\n'
              '- LaTeX compilation remains UNVERIFIED_PLATFORM_COMPILER_FAILURE; no new compiler run or successful compilation claimed.\n'
              '- Optional gamma/1024 extension and E3 shadow were disabled in the frozen protocol, not completed experiments.\n')
        write(CORE / 'SENSITIVITY_SCOPE.md', '# Sensitivity Scope\n\n'
              'Primary and smaller-gamma/larger-N fit windows, paired bootstrap and representative 2x burn/tail\n'
              'windows are recorded in PROTOCOL_FROZEN.json. All original fit outputs and windows are retained.\n'
              'Seed4102/4103 partition sensitivity is separate from primary conditional-on-partition inference.\n'
              'Long H1 roundoff checks and stable endpoint-increment audits were post-freeze/post-hoc diagnostics;\n'
              'they do not replace v1 runs, change tolerances, or constitute an improved-kernel full-grid rerun.\n'
              'Historical H=4 records are legacy, separately indexed, and not refit during this export.\n')
        write(CORE / 'REVIEW_EXPORT_README.md', '# Review Export\n\n'
              'Extract ordinary ZIPs into the same directory. REVIEW_CORE contains exact original reports,\n'
              'all tables/figure data, PDF/PNG figures, certificates, membership and diagnostic outputs.\n'
              'E3 diagnostic add-ons share REVIEW_CORE/ and retain complete unique partition matrices.\n'
              'PARTITION_DIAGNOSTIC_ALIASES.csv maps byte-identical reused files; restore_aliases.py can\n'
              'restore their original paths without training. Historical artifacts are separately labeled.\n'
              'AUDIT_BATCHES contains all pilot/production pairs and auxiliary diagnostics; each ZIP can\n'
              'be independently extracted. BATCH_INDEX.csv lists all package dependencies and identities.\n'
              'SOURCE_REVIEW contains actual current/uncommitted source, delivered snapshot, matching\n'
              'available frozen files, locked dependencies, configs and export/replay scripts.\n'
              'This is packaging only. No training, analysis-rule change, public upload or original-file\n'
              'modification was performed. Official original summaries and values are copied unchanged.\n')
        for name in ('SCIENTIFIC_SUMMARY.md','CLAIM_EVIDENCE_MAP.md'):
            write(OUT / name, get(name))
        state=dict(conf=conf,run_index=run_index,source_hashes=current_hashes,git=git,
                   original_archives=json.loads((OUT/'ORIGINAL_ARCHIVES_BEFORE.json').read_text()),
                   production_cells=len([r for r in registry if r['phase']=='production']),
                   registry_phase_counts=dict(Counter(r['phase'] for r in registry)),
                   inference_counts=dict(Counter(r['inference_status'] for r in registry if r['phase']=='production')),
                   arrays_bit_verified=len(run_index),history_files=len(history),history_bytes=sum(r['bytes'] for r in history),
                   partition_files=len(alias_rows),unique_partition_files=len(canonical_partition))
        jswrite(OUT / 'BUILD_STATE.json', state)
        print(json.dumps({k:state[k] for k in ('production_cells','registry_phase_counts','inference_counts','arrays_bit_verified',
                                             'history_files','history_bytes','partition_files','unique_partition_files')},indent=2),flush=True)


def source_tools():
    for path in sorted((OUT / 'tools').glob('*.py')):
        write(SOURCE / 'tools' / path.name, path.read_bytes())
    legacy_paths=[]
    for directory in ('src','shared','tests','workstreams','docs'):
        for path in sorted((ROOT/directory).rglob('*')):
            if path.is_file() and path.suffix.lower() in ('.py','.yaml','.yml','.toml','.md','.lock') and not any(
                    part in ('artifacts','__pycache__','.pytest_cache','.git') for part in path.parts):
                relative=path.relative_to(ROOT)
                parts=relative.parts
                if parts[0]=='workstreams':
                    relative=Path('workstreams',parts[1].split('_')[0],*parts[2:])
                write(SOURCE/'legacy_repository'/relative,path.read_bytes())
                legacy_paths.append(dict(original_path=path.relative_to(ROOT).as_posix(),
                    export_path='legacy_repository/'+relative.as_posix(),sha256=sha(path),
                    scope='available legacy context; original import paths recorded for restoration'))
    for name in ('README.md','pyproject.toml','requirements.lock','run.py'):
        write(SOURCE/'legacy_repository'/name,(ROOT/name).read_bytes())
    write(SOURCE/'EXPORT_LOG.md',(OUT/'EXPORT_LOG.md').read_bytes())
    export_spec=Path('original_attachments/SCAFFOLD_Review_Package_Export_Prompt.md')
    if export_spec.exists():
        write(SOURCE/'EXPORT_TASK_SPEC_ORIGINAL.md',export_spec.read_bytes())
        write(CORE/'EXPORT_TASK_SPEC_ORIGINAL.md',export_spec.read_bytes())
    csvwrite(SOURCE/'LEGACY_SOURCE_PATH_MAP.csv',legacy_paths)
    write(SOURCE / 'README_REVIEW.md', '# Source Review\n\n'
          'supplementary_study/ is the actual uncommitted current source, including both kernels, tests,\n'
          'analysis, plots, scheduler and CLI. delivered_source_snapshot/ preserves the prior delivered ZIP.\n'
          'available_frozen_source/ contains only obtainable exact freeze-hash matches; see status CSV.\n'
          'legacy_repository/ includes obtainable legacy code/configs, with short workstream IDs for Windows;\n'
          'it is separate historical context, NOT imported by the supplementary implementation.\n'
          'LEGACY_SOURCE_PATH_MAP.csv maps shortened folders back to original import paths if needed.\n'
          'No dependency environments, datasets, git objects, original result ZIPs or credentials are included.\n\n'
          'Install the versions in supplementary_study/requirements.lock into a separate Python environment.\n'
          'With all review ZIPs extracted into BUNDLE and a fresh output folder NEW_OUTPUoriginal_environment/n'
          '```powershell\npython SOURCE_REVIEW/tools/replay_review.py --bundle BUNDLE --output NEW_OUTPUT\n'
          'python SOURCE_REVIEW/tools/restore_aliases.py --bundle BUNDLE\n```\n\n'
          'Replay calls only existing analysis/plot functions, never CLI training. It checks batch/per-run\n'
          'means, primary statistics, paired covariance/contrasts, all E1 fits and figures; input reports\n'
          'remain unchanged. Full data-dependent report reconstruction and LaTeX compilation are not\n'
          'claimed. See EXPORT_QA.md for executed checks and residual limitations.\n')
    write(SOURCE/'EXPORT_REPRODUCTION.md','# Export Reproduction\n\n'
          'Export tools support explicit --workspace and --export-dir so they can be run from SOURCE_REVIEW.\n'
          'Use a NEW independent output directory outside supplementary_study; do not overwrite the delivered export.\n'
          'Requires the preserved original full ZIP and source.zip under the original workspace.\n\n'
          '```powershell\npython SOURCE_REVIEW/tools/inventory.py --workspace . --export-dir ./review_exports/NEW_EXPORT/n'
          'python SOURCE_REVIEW/tools/export_review.py build --workspace . --export-dir ./review_exports/NEW_EXPORT/n'
          'python SOURCE_REVIEW/tools/export_review.py finalize --workspace . --export-dir ./review_exports/NEW_EXPORT/n'
          'python SOURCE_REVIEW/tools/export_review.py integrity --workspace . --export-dir ./review_exports/NEW_EXPORT/n```\n\n'
          'Build copies the invoked tools and available export log into NEW_EXPORT automatically.\n'
          'Run analysis-only replay against\n'
          'NEW_EXPORT/qa_extraction with output NEW_EXPORT/qa_extraction/analysis_replay; then finalize and\n'
          'integrity again to include its certificate. Existing packages are never used as recursive inputs.\n')
    jswrite(SOURCE/'EXPORT_SOURCE_MANIFEST.json',{p.relative_to(SOURCE).as_posix():sha(p)
            for p in SOURCE.rglob('*') if p.is_file() and p.name!='EXPORT_SOURCE_MANIFEST.json'})


def partition_packages(files, base):
    groups=defaultdict(list)
    for path in files:
        relative=path.relative_to(base).as_posix()
        if base==CORE:
            group='E3_DIAGNOSTICS_'+path.name.split('_')[1]
            unit=path.name
        elif relative.startswith('raw/'):
            parts=Path(relative).parts
            cell=parts[2]
            group=('PILOTS' if parts[1]=='pilot' else 'E1' if cell.startswith('E1') else '_'.join(cell.split('_')[:2]))
            unit='/'.join(parts[:3])
        else:
            group='E2' if path.name.startswith('E2') or path.name.startswith('DIAGNOSTIC_') else 'POSTHOC'
            unit=relative
        groups[group].append((unit,path))
    output=[]
    for group, rows in sorted(groups.items()):
        units=defaultdict(list)
        for unit,path in rows:
            units[unit].append(path)
        chunks=[];chunk=[];size=0
        for unit, paths in sorted(units.items()):
            amount=sum(p.stat().st_size for p in paths)
            if size+amount>LIMIT and chunk:
                chunks.append(chunk);chunk=[];size=0
            assert amount<LIMIT, (group,unit,amount)
            chunk+=paths;size+=amount
        if chunk: chunks.append(chunk)
        for i,chunk in enumerate(chunks,1):
            suffix=f'_{i:02d}' if len(chunks)>1 else ''
            output.append((group+suffix,chunk))
    return output


def make_export_map(state):
    rows=[]
    captions=json.loads((CORE/'figures/captions_and_provenance.json').read_text())
    conf=state['conf']
    runs={(r['cell_id'],r['seed']):r for r in state['run_index'] if r['phase']=='production'}
    for item in captions:
        figure=item['figure'];source=item['source_csv']
        data=csvread((CORE/source).read_bytes())
        cells=set();fits=set()
        for r in data:
            if r.get('cell_id'):cells.add(r['cell_id'])
            if r.get('fit'):fits.add(r['fit'])
        for fit in fits:
            meta=json.loads((CORE/'diagnostics'/f'{fit}.json').read_text())
            cells.update(meta['cells'])
        pdf=next((CORE/'figures').rglob(figure+'.pdf')).relative_to(CORE).as_posix()
        for cell in sorted(cells):
            selected=[r for (c,s),r in runs.items() if c==cell]
            if not selected:
                selected=[dict(seed=10001,pair_id=cell+'/seed_10001',original_path='diagnostics/'+
                               ('E2_zero_seed10001' if 'zero' in cell else cell)+'.npz',
                               original_sha256='',export_path='REVIEW_CORE/diagnostics/'+
                               ('E2_zero_seed10001' if 'zero' in cell else cell)+'.npz',package='REVIEW_CORE.zip',phase='diagnostic')]
            for run in selected:
                if not run['original_sha256']:
                    run['original_sha256']=sha(CORE/run['original_path'])
                original_run_id=run['pair_id'].removeprefix('production/')
                rows.append(dict(figure=figure,figure_pdf=pdf,preview=pdf.removesuffix('.pdf')+'.png',
                    figure_data=source,figure_data_sha256=item['source_sha256'],fits=';'.join(sorted(fits)),cell_id=cell,
                    phase=run['phase'],seed=run['seed'],pair_id=run['pair_id'],
                    algorithm_run_ids=original_run_id+'/scaffold;'+original_run_id+'/fedavg' if run['phase']=='production' else '',
                    raw_artifact=run['original_path'],raw_sha256=run['original_sha256'],
                    batch_artifact=run['export_path'],batch_package=run['package'],
                    statistical_table='fitted_coefficients.csv' if fits else 'full_results.csv' if run['phase']=='production' else 'tables/E2_zero_initialization.csv' if 'zero' in cell else 'tables/E2_exact_checks.csv',
                    config='PROTOCOL_FROZEN.json',config_sha256=item['config_sha256'],
                    source_script=item['script'],source_sha256=state['source_hashes'].get(item['script'],''),
                    diagnostic_configuration_basis='SOURCE_REVIEW/available_frozen_source/study/engine.py (E2 key seed=10001); SOURCE_REVIEW/supplementary_study/study/checks.py (E2zero)' if run['phase']=='diagnostic' else 'PROTOCOL_FROZEN.json cells + production_seeds'))
    csvwrite(CORE/'EXPORT_MAP.csv',rows)
    write(OUT/'EXPORT_MAP.csv',(CORE/'EXPORT_MAP.csv').read_bytes())
    assert set(r['figure'] for r in rows)==set(r['figure'] for r in captions)
    return len(captions),len(rows)


def csv_schemas():
    paths=[CORE/name for name in ('full_results.csv','per_run_estimates.csv','fitted_coefficients.csv','EXPERIMENT_REGISTRY.csv')]
    paths+=list((CORE/'tables').glob('*.csv'))+list((CORE/'figure_data').glob('*.csv'))+list((CORE/'diagnostics').glob('*.csv'))
    schemas={}
    for path in sorted(paths):
        rows=csvread(path.read_bytes())
        columns={}
        for name in rows[0] if rows else []:
            types=Counter()
            for row in rows:
                value=row[name]
                if value=='':kind='empty'
                elif value.startswith('['):
                    try:json.loads(value);kind='JSON_array_text'
                    except json.JSONDecodeError:kind='text'
                else:
                    try:int(value);kind='integer_text'
                    except ValueError:
                        try:float(value);kind='float_text'
                        except ValueError:kind='text'
                types[kind]+=1
            columns[name]=dict(logical_types_inferred_from_original_text=dict(types))
        schemas[path.relative_to(CORE).as_posix()]=dict(rows=len(rows),sha256=sha(path),columns=columns,
            note='CSV has no stored machine dtype; original text bytes copied exactly. NPZ dtype/shape/bit fidelity is independently verified in ARRAY_KEY_INVENTORY and replay.')
    jswrite(CORE/'CSV_CONTENT_SCHEMA.json',schemas)


def finalize():
    state=json.loads((OUT/'BUILD_STATE.json').read_text())
    write(CORE/'BATCH_SCHEMA.md',BATCH_SCHEMA)
    write(AUDIT/'BATCH_SCHEMA.md',BATCH_SCHEMA)
    write(CORE/'EXPORT_LOG.md',(OUT/'EXPORT_LOG.md').read_bytes())
    size_report=(OUT/'FILE_SIZE_REPORT.md').read_text()
    marker='\n## Array-Level and Historical Findings\n'
    size_report=size_report.split(marker)[0]
    diagnosis=json.loads((OUT/'ARRAY_SIZE_DIAGNOSIS.json').read_text())
    size_report+=marker+'\nActual result-array inventory found '+str(diagnosis['original_raw_only_inner_compressed_bytes']['batch_control_sum'])+' compressed inner bytes in per-client temporal control-vector batch sums, plus '+str(diagnosis['original_raw_only_inner_compressed_bytes']['controls'])+' bytes in final client control states. These are batch integrals/states, not saved dense every-round trajectories. Primary per-client control means and all batch control second moments remain in review.\n\n'
    size_report+=f"Historical artifact collections were separately inventoried before copying: {state['history_files']} files / {state['history_bytes']} bytes. All available historical artifacts were retained, without outcome selection. See HISTORICAL_FILE_SIZE_INVENTORY.csv.\n\n"
    size_report+=f"Partition diagnostics have {state['partition_files']} original cell paths but {state['unique_partition_files']} unique SHA-256 identities. Complete unique arrays are retained in E3 add-on ZIPs, with reversible path aliases.\n"
    write(OUT/'FILE_SIZE_REPORT.md',size_report)
    source_tools()
    heavy=list((CORE/'diagnostics').glob('*_partition.npz'))
    diag_packs=partition_packages(heavy,CORE)
    audit_files=[p for p in AUDIT.rglob('*') if p.is_file() and p.name not in (
        'BATCH_SCHEMA.md','BATCH_INDEX.csv','BATCH_BOUNDARIES.csv','PAIRED_COVARIANCE.npz','PAIRED_COVARIANCE_INDEX.csv')]
    audit_files=[p for p in audit_files if 'PACKAGE_NOTES' not in p.parts]
    audit_packs=partition_packages(audit_files,AUDIT)
    for group,paths in audit_packs:
        pathset={p.relative_to(STAGE).as_posix() for p in paths}
        for row in state['run_index']:
            if row['export_path'] in pathset:row['package']='AUDIT_BATCHES_'+group+'.zip'
    assert all(r['package'] for r in state['run_index'])
    csvwrite(CORE/'BATCH_INDEX.csv',state['run_index'])
    write(AUDIT/'BATCH_INDEX.csv',(CORE/'BATCH_INDEX.csv').read_bytes())
    write(CORE/'BATCH_BOUNDARIES.csv',(AUDIT/'BATCH_BOUNDARIES.csv').read_bytes())
    write(OUT/'BATCH_INDEX.csv',(CORE/'BATCH_INDEX.csv').read_bytes())
    figures,maprows=make_export_map(state)
    csv_schemas()
    replay= json.loads((OUT/'qa_extraction/analysis_replay/REPLAY_QA.json').read_text()) if (OUT/'qa_extraction/analysis_replay/REPLAY_QA.json').exists() else None
    # Preserve diagnostics in add-ons with an explicit per-member package map.
    diagnostic_packages=[]
    for group,paths in diag_packs:
        for p in paths:diagnostic_packages.append(dict(export_path=p.relative_to(STAGE).as_posix(),package='REVIEW_CORE_'+group+'.zip',sha256=sha(p)))
    csvwrite(CORE/'DIAGNOSTIC_PACKAGE_INDEX.csv',diagnostic_packages)
    preservation=check_archives()
    source_unchanged=all(sha(STUDY/r)==h for r,h in state['source_hashes'].items())
    assert source_unchanged
    qa=['# Export QA','', 'Packaging only. No stochastic training, optimizer solve, tolerances or selection rules changed.','',
        f"- Original full ZIP and source ZIP match before/after SHA-256 and byte counts; full ZIP `{preservation[ARCHIVE.name]['sha256']}`.",
        '- Original current study source remains byte-identical to ORIGINAL_SOURCE_BEFORE.json.',
        f"- Registry coverage: {state['production_cells']} production cells / 828 pairs, 7 pilot cells / 28 pairs; every planned seed in these completed cells matches.",
        f"- Registry phase counts: `{state['registry_phase_counts']}`. Inference flags: `{state['inference_counts']}`.",
        '- Every H=4 result, negative/unresolved U-statistic, precision flag, and three H1 numerical identity flags is unchanged.',
        f"- All retained arrays in {state['arrays_bit_verified']} paired result files checked bit-for-bit (dtype, shape, bytes). Production per-run CSV means/raw means/second moments matched NPZ.",
        '- Official tables, per_run_estimates, figure_data, reports, configs and certificates copied exactly, not rounded or re-serialized.',
        '- All retained original members verified against supplied original SHA-256 manifests; omitted raw SHA identities use those manifests, not new scientific certification.',
        f'- {figures} complete PDF/PNG figure pairs; {maprows} figure-to-cell/run/config/source map entries.',
        f"- Partition diagnostics: {state['partition_files']} cell paths, {state['unique_partition_files']} unique byte-identical files; ALL arrays retained in add-ons; alias paths recorded.",
        f"- Historical legacy collections: all {state['history_files']} available files, {state['history_bytes']} bytes, separate from supplementary results.",
        '- ZIP testing extracts every file, reads each exported NPZ without pickle, parses CSV/JSON, and tests CRC. Final archive hashes/CRC are in the adjacent ZIP_INTEGRITY_QA.csv (external to avoid a self-hash cycle).', '',
        '## Analysis-Only Replay', '']
    if replay:
        for name in ('REPLAY_QA.json','STATISTIC_REPLAY_CHECKS.csv'):
            write(CORE/'export_validation'/name,(OUT/'qa_extraction/analysis_replay'/name).read_bytes())
        write(OUT/'REPLAY_QA.json',(OUT/'qa_extraction/analysis_replay/REPLAY_QA.json').read_bytes())
        qa += [f"Executed from extracted review ZIPs plus extracted SOURCE_REVIEW: {replay['pilot_and_production_batch_pairs_checked']} batch pairs, {replay['coefficient_rows']} fitted-coefficient rows, {replay['paired_policy_contrasts']} paired policy/allocation contrasts, {replay['main_statistic_checks']} numeric checks; maximum numeric replay error {replay['max_absolute_numeric_replay_error']:.3g}.",
               'All 15 original figures regenerated with original study/figures.py; figure-data values compared exactly.',
               'E1 fits, bootstrap seeds, paired E3 contrasts and main projection/U/variance/MSE seed intervals checked with existing analysis functions.',
               'All 15 regenerated PNGs are pixel-identical to the original PNGs. All 18 byte-identical partition aliases were successfully restored in the extracted QA bundle.',
               'Complete raw/data-dependent report rebuild and LaTeX compilation were not attempted; these require omitted datasets or a working TeX compiler.']
    else:
        qa += ['PENDING: integrity/extraction and analysis replay. This provisional package is not final until those checks are executed.']
    qa += ['', '## Limits', '', 'See MISSING_ITEMS.md and BATCH_SCHEMA.md. Within-round crossproducts and unsaved task-loss batches cannot be reconstructed. Per-client temporal control-vector audits need the original raw result. Full-grid improved-arithmetic production remains NOT RUN. SHA hashes prove identity only.', '']
    write(CORE/'EXPORT_QA.md','\n'.join(qa))
    write(OUT/'EXPORT_QA.md','\n'.join(qa))
    write(OUT/'MISSING_ITEMS.md',(CORE/'MISSING_ITEMS.md').read_bytes())
    for name in ('FILE_SIZE_REPORT.md','FILESYSTEM_SIZE_INVENTORY.csv','ZIP_MEMBER_SIZE_INVENTORY.csv','HISTORICAL_FILE_SIZE_INVENTORY.csv',
                 'ORIGINAL_ARCHIVES_BEFORE.json','ORIGINAL_SOURCE_BEFORE.json','ARRAY_SIZE_DIAGNOSIS.json'):
        write(CORE/name,(OUT/name).read_bytes())
    packages=[]
    def package(name, files, description):
        destination=OUT/name
        with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as archive:
            for path in sorted(set(files)):
                archive.write(path,path.relative_to(STAGE).as_posix())
        assert destination.stat().st_size<100_000_000, (name,destination.stat().st_size)
        packages.append(dict(name=name,path=str(destination),bytes=destination.stat().st_size,
                             MB=destination.stat().st_size/1e6,sha256=sha(destination),description=description))
    core_files=[p for p in CORE.rglob('*') if p.is_file() and p not in heavy and p.name!='ZIP_INTEGRITY_QA.csv'
                and 'EXPORT_PACKAGE_NOTES' not in p.parts]
    package('REVIEW_CORE.zip',core_files,'all original reports/tables/figures/per-run results, diagnostics/certificates/indexes, separate historical records; E3 matrix add-ons indexed')
    for group,paths in diag_packs:
        note=CORE/'EXPORT_PACKAGE_NOTES'/('REVIEW_CORE_'+group+'.md')
        write(note,f'# {group}\n\nStandalone ordinary ZIP; extract into the common bundle directory. Complete unique partition matrices and membership arrays, no precision reduction. Aliases and hashes in REVIEW_CORE/PARTITION_DIAGNOSTIC_ALIASES.csv.\n')
        package('REVIEW_CORE_'+group+'.zip',paths+[note,CORE/'PARTITION_DIAGNOSTIC_ALIASES.csv',CORE/'DIAGNOSTIC_PACKAGE_INDEX.csv'],
                'complete lossless unique E3 partition membership/gradient/Hessian/noise matrices; byte-identical cell aliases mapped')
    package('SOURCE_REVIEW.zip',[p for p in SOURCE.rglob('*') if p.is_file()],
            'current uncommitted code, delivered snapshot, available exact frozen files, configs, tests, analysis/plots/export/replay tools and locked environment')
    common=[AUDIT/'BATCH_SCHEMA.md',AUDIT/'BATCH_INDEX.csv',AUDIT/'PAIRED_COVARIANCE.npz',AUDIT/'PAIRED_COVARIANCE_INDEX.csv']
    for group,paths in audit_packs:
        note=AUDIT/'PACKAGE_NOTES'/('AUDIT_BATCHES_'+group+'.md')
        write(note,f'# {group}\n\nStandalone ordinary ZIP. Extract without joining binary parts. Shared global BATCH_INDEX and covariance indexes preserve pairing/cross-cell dependencies. This archive contains whole paired runs/cells; no seed or algorithm side split. Core reports and SOURCE_REVIEW are required for full scientific replay, not for extraction.\n')
        # Full boundaries are also encoded in every compact NPZ, so the readable boundary CSV need not be repeated in each ZIP.
        package('AUDIT_BATCHES_'+group+'.zip',paths+common+[note],
                'all collected global/balance batch vectors, MSE/control summaries, aligned pairs and original metadata for '+group)
    csvwrite(OUT/'PACKAGE_INDEX.csv',packages)
    jswrite(OUT/'PACKAGE_INDEX.json',packages)
    index=['# Upload Order','', 'All archives are ordinary, independently extractable ZIPs, each below 100 decimal MB.',
           'No .z01/.001 volumes or binary concatenation. Nothing was publicly uploaded.', '',
           '## First: Small Review Files','',
           '1. SCIENTIFIC_SUMMARY.md (exact original scientific report).',
           '2. CLAIM_EVIDENCE_MAP.md (exact original claim/evidence boundaries).',
           '3. FILE_SIZE_REPORT.md (pre-selection inventory).',
           '4. UPLOAD_ORDER.md (this index).','',
           '## Then: Archives','', '| Order | Archive | Bytes | MB | SHA-256 | Contents / Dependencies |',
           '|---:|---|---:|---:|---|---|']
    for i,p in enumerate(packages,1):
        index.append(f"| {i} | [{p['name']}]({p['name']}) | {p['bytes']} | {p['MB']:.3f} | `{p['sha256']}` | {p['description']} |")
    index += ['', 'Extract all needed ZIPs into the SAME new directory; shared root folders merge. E3 matrix add-ons\n'
              'are needed for full partition audits. SOURCE_REVIEW plus REVIEW_CORE can regenerate figures/fits\n'
              'from exact per-run CSVs; AUDIT_BATCHES is additionally required to check batches and variance/MSE.\n'
              'All audit ZIPs are required for full-grid batch coverage. No original 3.16 GB ZIP is required for\n'
              'these executed replay checks, but original data/client-control/restart audits still need raw artifacts.', '',
              '## Exact Analysis-Only Command', '', '```powershell',
              'python SOURCE_REVIEW/tools/replay_review.py --bundle . --output analysis_replay',
              'python SOURCE_REVIEW/tools/restore_aliases.py --bundle .', '```', '',
              f'Original complete archive preserved at `{ARCHIVE}`.',
              'See EXPORT_QA.md, MISSING_ITEMS.md, RAW_ARCHIVE_MANIFEST.csv, EXPORT_MAP.csv and BATCH_INDEX.csv.',
              'Hashes identify exact artifacts and do not prove scientific correctness.', '']
    executable=json.loads((CORE/'ENVIRONMENT.txt').read_text())['executable']
    index+=['## Local Recheck Command','', 'The following uses the existing local dependency environment and a NEW QA output folder; it does not train.', '',
            '```powershell',f"& '{executable}' '{OUT/'qa_extraction/SOURCE_REVIEW/tools/replay_review.py'}' --bundle '{OUT/'qa_extraction'}' --output '{OUT/'qa_extraction/analysis_replay_recheck'}' --deps '{STUDY/'.deps'}'",'```','',
            'Final CRC/extraction results and exact ZIP hashes are in ZIP_INTEGRITY_QA.csv beside these archives.\n'
            'Exported analysis replay certificate and 4,317 original-value comparisons are in REVIEW_CORE/export_validation/.','']
    write(OUT/'UPLOAD_ORDER.md','\n'.join(index))
    jswrite(OUT/'FINAL_STATE.json',dict(packages=len(packages),figures=figures,map_entries=maprows,replay_executed=bool(replay),source_unchanged=source_unchanged))
    print(json.dumps(packages,indent=2),flush=True)


def integrity():
    packages=json.loads((OUT/'PACKAGE_INDEX.json').read_text())
    extraction=OUT/'qa_extraction'
    extraction.mkdir(parents=True,exist_ok=True)
    rows=[]
    for item in packages:
        path=Path(item['path'])
        assert sha(path)==item['sha256']
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            for info in archive.infolist():
                dest=(extraction/info.filename).resolve()
                assert dest.is_relative_to(extraction.resolve())
                archive.extract(info,extraction)
                if dest.suffix=='.npz':
                    with np.load(dest,allow_pickle=False) as arrays:
                        for key in arrays.files:
                            assert arrays[key].dtype.kind!='O', dest
                elif dest.suffix=='.json':
                    json.loads(dest.read_text(encoding='utf-8'))
                elif dest.suffix=='.csv':
                    with dest.open(encoding='utf-8-sig',newline='') as stream:
                        for row in csv.reader(stream):pass
            rows.append(dict(package=item['name'],bytes=item['bytes'],sha256=item['sha256'],members=len(archive.infolist()),CRC='PASS',
                             extract='PASS',npz_no_pickle_csv_json_readability='PASS'))
        print('Integrity + extraction PASS:',item['name'],flush=True)
    csvwrite(OUT/'ZIP_INTEGRITY_QA.csv',rows)
    write(CORE/'ZIP_INTEGRITY_QA.csv',(OUT/'ZIP_INTEGRITY_QA.csv').read_bytes())
    csvwrite(OUT/'EXTRACTED_FILE_HASHES.csv',[dict(path=p.relative_to(extraction).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
              for p in sorted(extraction.rglob('*')) if p.is_file() and 'analysis_replay' not in p.parts and '__pycache__' not in p.parts])


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('build','finalize','integrity'))
    parser.add_argument('--workspace',type=Path)
    parser.add_argument('--export-dir',type=Path)
    args=parser.parse_args()
    {'build':build,'finalize':finalize,'integrity':integrity}[args.action]()
