"""Independent ordinary ZIP archives, exhaustive selection logs, and portable QA."""
import argparse
import csv
import io
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from prepare import digest, write_csv, write_json


def reason(root, p, source):
    rel = p.relative_to(root)
    if any(x in ['__pycache__', '.pytest_cache', 'mpl_cache', 'tex.cache', 'qa_extracted'] for x in rel.parts):
        return 'GENERATED_CACHE_OR_PORTABLE_REPLAY'
    if p.suffix in ['.pyc', '.aux', '.toc']:
        return 'GENERATED_CACHE'
    if 'gallery_build' in rel.parts and p.suffix != '.log':
        return 'REDUNDANT_GALLERY_COMPILE_INTERMEDIATE;FINAL_PDF_AT_ROOT'
    if p.name in ['PACKAGE_MANIFEST.csv', 'FILE_SELECTION.csv', 'SOURCE_SHA256.csv']:
        return 'PER_ARCHIVE_MANIFEST_GENERATED_SEPARATELY'
    if source:
        if rel.parts[0] in ['inputs', 'prior_e4', 'supplied', 'code']:
            return None
        if p.suffix in ['.py', '.md', '.json', '.txt', '.tex', '.ps1']:
            return None
        if p.name in ['INPUT_SHA256.csv', 'INPUT_ARCHIVES.csv', 'PROTECTED_PRE_E5_SHA256.csv']:
            return None
        return 'DERIVED_NUMERICAL_OR_FIGURE_EVIDENCE_IN_HANDOFF;REPRODUCIBLE_FROM_INCLUDED_INPUTS'
    return None


def csv_bytes(rows):
    stream = io.StringIO(newline='')
    w = csv.DictWriter(stream, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    return stream.getvalue().encode('utf-8')


def export(root, dest):
    root, dest = Path(root).resolve(), Path(dest).resolve()
    assert root not in dest.parents, 'Delivery destination must not recurse into source snapshot'
    dest.mkdir(parents=True, exist_ok=True)
    allfiles = [p for p in sorted(root.rglob('*')) if p.is_file()]
    inventory = [dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size) for p in allfiles]
    write_csv(dest / 'FULL_E5_FILE_SIZE_INVENTORY.csv', inventory)
    qa = []
    for source, name in [(False, 'E5_ANALYTIC_BRIDGE_HANDOFF.zip'), (True, 'E5_SOURCE_AUDIT.zip')]:
        files = [p for p in allfiles if reason(root, p, source) is None]
        manifest = [dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size, sha256=digest(p)) for p in files]
        excluded = [dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size, reason=reason(root, p, source))
                    for p in allfiles if reason(root, p, source)]
        sources = [r for r in manifest if Path(r['path']).suffix in ['.py', '.json', '.txt', '.ps1', '.tex']]
        archive = dest / name
        with ZipFile(archive, 'w', ZIP_DEFLATED, compresslevel=6) as z:
            for p in files:
                z.write(p, p.relative_to(root).as_posix())
            z.writestr('PACKAGE_MANIFEST.csv', csv_bytes(manifest))
            z.writestr('FILE_SELECTION.csv', csv_bytes(excluded))
            z.writestr('SOURCE_SHA256.csv', csv_bytes(sources))
        with ZipFile(archive) as z:
            assert z.testzip() is None
            for r in manifest:
                import hashlib
                payload = z.read(r['path'])
                assert len(payload) == r['bytes'] and hashlib.sha256(payload).hexdigest() == r['sha256']
        qa.append(dict(archive=name, bytes=archive.stat().st_size, MB_decimal=archive.stat().st_size/1e6,
                       sha256=digest(archive), payload_files=len(manifest), payload_bytes=sum(r['bytes'] for r in manifest),
                       CRC_and_all_payload_sha256='PASS', independently_extractable=True,
                       under_100MB=archive.stat().st_size < 100000000))
    write_json(dest / 'ARCHIVE_QA.json', qa)
    print(json.dumps(qa))


def verify(root):
    root = Path(root)
    rows = list(csv.DictReader((root / 'PACKAGE_MANIFEST.csv').open(encoding='utf-8')))
    for r in rows:
        p = root / r['path']
        assert p.is_file() and p.stat().st_size == int(r['bytes']) and digest(p) == r['sha256'], r['path']
    print(json.dumps(dict(status='PASS', verified_payload_files=len(rows))))


def extract(archive, out):
    out = Path(out).resolve()
    assert not out.exists(), 'Use a fresh verification directory; do not overwrite prior audits'
    with ZipFile(archive) as z:
        for member in z.namelist():
            path = (out / member).resolve()
            assert path.is_relative_to(out), member
        z.extractall(out)
    verify(out)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['export', 'verify', 'extract'])
    p.add_argument('--root')
    p.add_argument('--dest')
    p.add_argument('--archive')
    a = p.parse_args()
    if a.command == 'export':
        export(a.root, a.dest)
    elif a.command == 'verify':
        verify(a.root)
    else:
        extract(a.archive, a.dest)
