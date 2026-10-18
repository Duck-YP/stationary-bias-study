"""Compare independently extracted source replay to the finished local analysis."""
import argparse
import json
from pathlib import Path

import numpy as np

from prepare import digest, write_json


def compare(original, replay, receipt, archive=None):
    original, replay = Path(original), Path(replay)
    names = ['ALL_CELLS_ALL_WINDOWS.csv', 'FULL_VECTOR_ALIGNMENT.csv', 'SCALING_COMPARISONS.csv',
             'PAIRED_BOOTSTRAP_SENSITIVITY.csv', 'NEGATIVE_CONTROLS.csv', 'NUMERICAL_CROSSCHECKS.csv',
             'PAIRED_SEED_RESULTS.csv', 'EARLY_LATE_PAIRED_DIAGNOSTICS.csv',
             'EXPLORATORY_SCRIPT_CROSSCHECK.csv', 'STATISTICAL_METHOD_RECEIPT.json',
             'SCIENTIFIC_SUMMARY.md', 'REVIEWER_RISK_DECISION.md', 'CLAIM_EVIDENCE_MAP.md',
             'SCOPE_AND_LIMITATIONS.md', 'MISSING_ITEMS.md', 'SUGGESTED_MANUSCRIPT_INSERT.tex']
    checked = []
    for name in names:
        assert digest(original / name) == digest(replay / name), name
        checked.append(dict(path=name, sha256=digest(original / name), exact_bytes=True))
    figure_files = []
    if (replay / 'FIGURE_DATA').exists():
        for p in sorted((original / 'FIGURE_DATA').glob('*.csv')):
            relative = p.relative_to(original)
            assert digest(p) == digest(replay / relative), relative
            figure_files.append(dict(path=relative.as_posix(), sha256=digest(p), exact_bytes=True))
    arrays = []
    for name in ['VECTORS.npz', 'INFERENCE_ARRAYS.npz']:
        with np.load(original / name) as a, np.load(replay / name) as b:
            assert a.files == b.files
            for k in a.files:
                assert np.array_equal(a[k], b[k]), (name, k)
                arrays.append(dict(path=name, key=k, shape=list(a[k].shape), exact_elements=True))
    source_files = []
    for folder in ['code', 'independent_formula', 'independent_audit', 'reviewer_audit']:
        for p in sorted((original / folder).rglob('*.py')):
            relative = p.relative_to(original)
            assert digest(p) == digest(replay / relative), relative
            source_files.append(dict(path=relative.as_posix(), sha256=digest(p)))
    for name in ['REPRODUCE.ps1', 'E5_POSTHOC_ANALYSIS_SPEC.json', 'requirements.txt']:
        assert digest(original / name) == digest(replay / name), name
        source_files.append(dict(path=name, sha256=digest(original / name)))
    value = dict(status='PASS', mode='fresh_source_zip_extraction_then_full_numerical_replay',
                 files=checked, arrays=arrays, source_files=source_files, figure_data=figure_files,
                 archive_at_replay_sha256=digest(archive) if archive else None,
                 original=str(original.resolve()), replay=str(replay.resolve()),
                 no_training=True, same_library_environment=True,
                 path_dependent_audit_receipts_not_required_byte_identical=True)
    write_json(receipt, value)
    print(json.dumps(dict(status='PASS', exact_files=len(checked), exact_arrays=len(arrays), no_training=True)))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--original', required=True)
    p.add_argument('--replay', required=True)
    p.add_argument('--receipt', required=True)
    p.add_argument('--archive')
    compare(**vars(p.parse_args()))
