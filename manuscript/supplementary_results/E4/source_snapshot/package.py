"""Content-based ordinary ZIP export and hash verification; no result filtering."""
import argparse
import csv
import io
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from prepare import sha, write_csv

CACHES = {'__pycache__', '.pytest_cache', 'numba_cache', 'mpl_cache', 'E0_pytest_tmp',
          'test_tmp_01', 'portable_replay', 'e4_test_tmp', 'test_tmp', 'compact_only_tmp'}
SOURCE_ROOTS = {'code', 'legacy_source', 'inputs', 'practical', 'statistical_review', 'independent_audit'}


def reason(root, p, source=False):
    rel = p.relative_to(root)
    if any(k in CACHES for k in rel.parts) or any(k.startswith('pytest_') for k in rel.parts):
        return 'GENERATED_CACHE_OR_TEST_TEMP'
    if p.name in ['PACKAGE_MANIFEST.csv', 'SOURCE_SHA256.csv', 'FILE_SELECTION.csv']:
        return 'GENERATED_PER_PACKAGE_MANIFEST'
    if p.name == 'PHASE0_IDENTITY_CHECKS.csv':
        return 'REDUNDANT_VECTOR_QA_LOG_ALL_CHECKS_IN_COMPACT_CSV_WITH_ORIGINAL_HASH'
    if p.suffix in ['.aux', '.pyc', '.nbi', '.nbc']:
        return 'GENERATED_COMPILE_CACHE'
    if p.name == 'checkpoint.npz' and p.with_name('result.npz').exists():
        return 'REDUNDANT_FINISHED_CHECKPOINT_FULL_RESULT_INCLUDED'
    if source:
        if len(rel.parts) == 1:
            if p.suffix in ['.md', '.json', '.sha256', '.lock', '.tex']:
                return None
            return 'DERIVED_EVIDENCE_IN_HANDOFF_NOT_SOURCE'
        if rel.parts[0] not in SOURCE_ROOTS:
            return 'DERIVED_OR_HISTORICAL_EVIDENCE_IN_HANDOFF_NOT_SOURCE'
        if rel.parts[0] in ['independent_audit', 'statistical_review'] and len(rel.parts) > 2:
            return 'DERIVED_AUDIT_RUN_IN_HANDOFF_NOT_SOURCE'
        if rel.parts[0] == 'practical' and len(rel.parts) > 2 and rel.parts[1] != 'inputs':
            return 'DERIVED_PRACTICAL_QA_IN_HANDOFF_NOT_SOURCE'
    return None


def csv_bytes(rows):
    f = io.StringIO(newline='')
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    return f.getvalue().encode('utf-8')


def export(root, dest):
    root, dest = Path(root), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    records = []
    for source, name in [(False, 'SIGNIFICANCE_E4_HANDOFF.zip'), (True, 'SOURCE_E4.zip')]:
        files = [p for p in sorted(root.rglob('*')) if p.is_file() and not reason(root, p, source)]
        manifest = [dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size, sha256=sha(p)) for p in files]
        sources = [r for r in manifest if Path(r['path']).suffix in ['.py', '.lock', '.tex'] or
                   'PROTOCOL_FROZEN' in r['path'] or 'CONFIGS' in r['path']]
        omitted = [dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size, reason=reason(root, p, source))
                   for p in sorted(root.rglob('*')) if p.is_file() and reason(root, p, source)]
        path = dest / name
        with ZipFile(path, 'w', compression=ZIP_DEFLATED, compresslevel=6) as z:
            for p in files:
                z.write(p, p.relative_to(root).as_posix())
            z.writestr('PACKAGE_MANIFEST.csv', csv_bytes(manifest))
            z.writestr('SOURCE_SHA256.csv', csv_bytes(sources))
            z.writestr('FILE_SELECTION.csv', csv_bytes(omitted))
        with ZipFile(path) as z:
            assert z.testzip() is None
            members = len(z.infolist())
        rec = dict(archive=name, bytes=path.stat().st_size, MB_decimal=path.stat().st_size/1e6,
                   sha256=sha(path), crc_status='PASS', members=members,
                   selected_uncompressed_bytes=sum(r['bytes'] for r in manifest),
                   independently_extractable=True, under_100MB=path.stat().st_size < 100_000_000)
        records.append(rec)
        if not source:
            write_csv(root / 'PACKAGE_MANIFEST.csv', manifest)
            write_csv(root / 'SOURCE_SHA256.csv', sources)
            write_csv(root / 'FILE_SELECTION.csv', omitted)
    (dest / 'ARCHIVE_QA.json').write_text(json.dumps(records, indent=2)+'\n')
    print(json.dumps(records))


def verify(root):
    root = Path(root)
    rows = list(csv.DictReader((root / 'PACKAGE_MANIFEST.csv').open()))
    for row in rows:
        p = root / row['path']
        assert p.exists() and p.stat().st_size == int(row['bytes']) and sha(p) == row['sha256'], row['path']
    print(json.dumps(dict(status='PASS', hash_verified_files=len(rows), scope='this package manifest')))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['export', 'verify'])
    p.add_argument('--root', required=True)
    p.add_argument('--dest')
    a = p.parse_args()
    if a.command == 'export':
        export(a.root, a.dest)
    else:
        verify(a.root)
