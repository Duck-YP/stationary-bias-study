"""Read-only size inventory; no experiment or report code is executed."""
from pathlib import Path
import csv
import hashlib
import json
import zipfile
import argparse

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'supplementary_study/results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF.zip'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    folders = {}
    for path in (ROOT / 'supplementary_study').rglob('*'):
        if path.is_file():
            relative = path.relative_to(ROOT).as_posix()
            size = path.stat().st_size
            files.append({'path': relative, 'bytes': size})
            group = '/'.join(path.relative_to(ROOT).parts[:2])
            folders[group] = folders.get(group, 0) + size
    with (OUT / 'FILESYSTEM_SIZE_INVENTORY.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['path', 'bytes'])
        writer.writeheader()
        writer.writerows(sorted(files, key=lambda x: -x['bytes']))
    groups = {}
    entries = []
    with zipfile.ZipFile(ARCHIVE) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            parts = Path(info.filename).parts
            relative = '/'.join(parts[1:])
            if relative.startswith('raw/'):
                group = '/'.join(parts[1:3]) + '/' + Path(relative).name
            else:
                group = parts[1] if len(parts) > 2 else '(root reports)'
            item = {'path': info.filename, 'bytes': info.file_size,
                    'compressed_bytes': info.compress_size, 'group': group}
            entries.append(item)
            total = groups.setdefault(group, {'bytes': 0, 'compressed_bytes': 0, 'files': 0})
            for key in ('bytes', 'compressed_bytes'):
                total[key] += item[key]
            total['files'] += 1
    with (OUT / 'ZIP_MEMBER_SIZE_INVENTORY.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['path', 'bytes', 'compressed_bytes', 'group'])
        writer.writeheader()
        writer.writerows(sorted(entries, key=lambda x: -x['bytes']))
    hashes = {p.name: {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}
              for p in (ARCHIVE, ARCHIVE.parent / 'source.zip')}
    (OUT / 'ORIGINAL_ARCHIVES_BEFORE.json').write_text(json.dumps(hashes, indent=2) + '\n', encoding='utf-8')
    lines = ['# File Size Report', '', 'Inventory completed before selecting review content.',
             'Sizes use decimal MB (1 MB = 1,000,000 bytes). Original files are read-only inputs.', '',
             '## Original Archives', '', '| Archive | Bytes | MB | SHA-256 |', '|---|---:|---:|---|']
    for name, value in hashes.items():
        lines.append(f"| {name} | {value['bytes']} | {value['bytes']/1e6:.3f} | `{value['sha256']}` |")
    lines += ['', f"Full ZIP: {len(entries)} files, {sum(e['bytes'] for e in entries):,} uncompressed bytes, "
              f"{sum(e['compressed_bytes'] for e in entries):,} compressed member bytes.", '',
              '## Workspace Folder Totals', '', '| Folder | Bytes | MB |', '|---|---:|---:|']
    for name, size in sorted(folders.items(), key=lambda x: -x[1]):
        lines.append(f'| {name} | {size} | {size/1e6:.3f} |')
    lines += ['', '## Archive Content Totals', '', '| Content group | Files | Uncompressed MB | Compressed MB |',
              '|---|---:|---:|---:|']
    for group, values in sorted(groups.items(), key=lambda x: -x[1]['compressed_bytes']):
        lines.append(f"| {group} | {values['files']} | {values['bytes']/1e6:.3f} | {values['compressed_bytes']/1e6:.3f} |")
    lines += ['', '## Largest 30 Members', '', '| Member | Uncompressed bytes | Compressed bytes |',
              '|---|---:|---:|']
    for entry in sorted(entries, key=lambda x: -x['bytes'])[:30]:
        lines.append(f"| {entry['path']} | {entry['bytes']} | {entry['compressed_bytes']} |")
    lines += ['', '## Content Diagnosis', '',
              'The measured raw result and checkpoint groups dominate the archive; each checkpoint stores '
              'the state and batch arrays also present in the corresponding result. This is duplicate '
              'state/batch storage, not evidence that every round of client trajectories was saved.',
              'Array-level inventory and selection rationale are recorded separately in ARRAY_KEY_INVENTORY.csv '
              'and BATCH_SCHEMA.md after inspecting actual NPZ contents.',
              'The archive includes dataset copies and test-temporary artifacts. Environment dependencies '
              'exist in the workspace but are not assumed to be part of the original archive.',
              'Original ZIP and expanded results are retained. Review exports omit duplicate checkpoints, '
              'downloadable training data, redundant SVG renderings, and non-primary temporary test states; '
              'exact omissions are recorded in RAW_ARCHIVE_MANIFEST.csv.', '']
    (OUT / 'FILE_SIZE_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'archives': hashes, 'groups': groups, 'files': len(entries)}, indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--workspace',type=Path)
    parser.add_argument('--export-dir',type=Path)
    args=parser.parse_args()
    if args.workspace:ROOT=args.workspace.resolve()
    if args.export_dir:OUT=args.export_dir.resolve()
    ARCHIVE=ROOT/'supplementary_study/results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF.zip'
    assert OUT.resolve()!=ROOT.resolve() and not OUT.resolve().is_relative_to((ROOT/'supplementary_study').resolve())
    main()
