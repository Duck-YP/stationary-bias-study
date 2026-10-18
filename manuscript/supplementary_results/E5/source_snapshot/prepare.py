"""Verify portable E4 artifacts and copy only analysis inputs. Never trains."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def prepare(out, handoff, source, risk, brief):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    logs, hashes = [], []
    expected = {str(handoff): '8a1d9e0e5a4d8f05c117a998a4d780075c85583fc7b6065a1c7388b0a33b8f54',
                str(source): '50eb7c9ba9b0a2630bc662ce6ccb0c1941a3220045c132d7a328a89731168e9a'}
    for name in [handoff, source, risk, brief]:
        sha = digest(name)
        assert str(name) not in expected or sha == expected[str(name)], name
        hashes.append(dict(path=str(Path(name).resolve()), bytes=Path(name).stat().st_size, sha256=sha))
    roots = ['models.npz', 'RUN_MANIFEST.csv', 'SCIENTIFIC_SUMMARY.md', 'CLAIM_EVIDENCE_MAP.md',
             'PRACTICAL_IMPLICATIONS.csv', 'TEMPORAL_DIAGNOSTICS.csv', 'PILOT_AND_BUDGET.md',
             'BIAS_VARIANCE_MSE.csv', 'DECISIONS.json', 'E4_v1_PROTOCOL_FROZEN.json',
             'E4_v1_PROTOCOL_FROZEN.sha256', 'STATISTICAL_METHOD_RECEIPT.json',
             'MISSING_ITEMS.md', 'WINDOW_RESULTS.csv']
    with ZipFile(handoff) as z:
        assert z.testzip() is None
        manifest = {r['path']: r for r in csv.DictReader(io.StringIO(z.read('PACKAGE_MANIFEST.csv').decode()))}
        for entry in z.infolist():
            name = entry.filename
            selected = (name.startswith('inputs/') or name in roots or name.startswith('legacy_source/') or
                        (name.startswith('historical/') and Path(name).suffix in ['.md', '.csv', '.json', '.tex']))
            if not selected:
                continue
            payload = z.read(name)
            sha = hashlib.sha256(payload).hexdigest()
            assert name in manifest and manifest[name]['sha256'] == sha
            dest = out / ('inputs/models.npz' if name == 'models.npz' else name if name.startswith('inputs/')
                          else 'prior_e4/' + name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                assert digest(dest) == sha, f'Never overwrite changed input: {dest}'
            else:
                dest.write_bytes(payload)
            logs.append(dict(archive_member=name, local_path=dest.relative_to(out).as_posix(),
                             bytes=len(payload), sha256=sha, archived_manifest_match=True))
    input_dir = out / 'supplied'
    input_dir.mkdir(exist_ok=True)
    with ZipFile(risk) as z:
        assert z.testzip() is None
        for e in z.infolist():
            assert '/' not in e.filename and '\\' not in e.filename
            (input_dir / e.filename).write_bytes(z.read(e.filename))
    (input_dir / Path(brief).name).write_bytes(Path(brief).read_bytes())
    write_csv(out / 'INPUT_SHA256.csv', logs)
    write_csv(out / 'INPUT_ARCHIVES.csv', hashes)
    print(json.dumps(dict(status='PASS', verified_selected_files=len(logs), new_training=False)))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for key in ['out', 'handoff', 'source', 'risk', 'brief']:
        p.add_argument('--' + key, required=True)
    prepare(**vars(p.parse_args()))
