"""Nonrecursive final delivery sidecars; archives never contain their own hashes."""
import argparse
import csv
import hashlib
import io
import json
import shutil
from pathlib import Path
from zipfile import ZipFile

from prepare import digest, write_json


def finish(root, dest):
    root, dest = Path(root), Path(dest)
    archives = json.loads((dest / 'ARCHIVE_QA.json').read_text())
    replay = json.loads((root / 'PORTABLE_REPLAY_QA.json').read_text())
    assert replay['status'] == 'PASS'
    payload_counts = {}
    for rec in archives:
        path = dest / rec['archive']
        assert digest(path) == rec['sha256'] and path.stat().st_size == rec['bytes']
        assert rec['under_100MB']
        with ZipFile(path) as z:
            assert z.testzip() is None
            manifest = list(csv.DictReader(io.StringIO(z.read('PACKAGE_MANIFEST.csv').decode())))
            for row in manifest:
                content = z.read(row['path'])
                assert len(content) == int(row['bytes']) and hashlib.sha256(content).hexdigest() == row['sha256']
            payload_counts[rec['archive']] = len(manifest)
            if rec['archive'] == 'E5_SOURCE_AUDIT.zip':
                for row in replay['source_files']:
                    assert hashlib.sha256(z.read(row['path'])).hexdigest() == row['sha256'], row['path']
            else:
                for row in replay['files'] + replay['figure_data']:
                    assert hashlib.sha256(z.read(row['path'])).hexdigest() == row['sha256'], row['path']
    preservation = json.loads((dest / 'POST_PACKAGE_PRESERVATION.json').read_text())
    assert preservation['status'] == 'PASS'
    for name in ['SCIENTIFIC_SUMMARY.md', 'REVIEWER_RISK_DECISION.md', 'CLAIM_EVIDENCE_MAP.md',
                 'SCOPE_AND_LIMITATIONS.md', 'HANDOFF.md', 'MISSING_ITEMS.md']:
        shutil.copy2(root / name, dest / name)
    size_lines = ['# E5 file-size report', '', 'Ordinary independent ZIPs; decimal MB. No split volumes.', '',
                  '| Archive | Bytes | MB | Payload files |', '|---|---:|---:|---:|']
    size_lines += [f"| {r['archive']} | {r['bytes']} | {r['MB_decimal']:.3f} | {r['payload_files']} |" for r in archives]
    size_lines += ['', 'The handoff retains all nine cells, all seven K windows, all paired seeds, full 124-vectors and batch summaries.',
                   'Selection is content-based. Generated caches and duplicate compilation intermediates are excluded, not scientific cells.',
                   'Each archive contains PACKAGE_MANIFEST.csv, SOURCE_SHA256.csv and FILE_SELECTION.csv. The source includes processed input data so numerical replay needs no network download.',
                   'Full size inventory: FULL_E5_FILE_SIZE_INVENTORY.csv. SHA-256 and CRC verification: ARCHIVE_QA.json and FINAL_DELIVERY_QA.json.']
    (dest / 'FILE_SIZE_REPORT.md').write_text('\n'.join(size_lines)+'\n', encoding='utf-8')
    (dest / 'UPLOAD_ORDER.md').write_text('# Review order\n\n1. SCIENTIFIC_SUMMARY.md and REVIEWER_RISK_DECISION.md.\n2. CLAIM_EVIDENCE_MAP.md and SCOPE_AND_LIMITATIONS.md.\n3. E5_ANALYTIC_BRIDGE_HANDOFF.zip for complete evidence and figures.\n4. E5_SOURCE_AUDIT.zip for independent reproduction.\n\nAll work remains local. This is a suggested reading/upload order only; nothing has been uploaded.\n', encoding='utf-8')
    result = dict(status='PASS', archives=archives, independently_verified_payload_counts=payload_counts,
                  final_source_code_matches_successful_fresh_replay=True,
                  final_handoff_primary_results_and_figure_data_match_successful_fresh_replay=True,
                  fresh_final_archives_extracted_and_verified=True,
                  protected_original_file_count=preservation['checked_files'], original_files_unchanged=True,
                  manuscript_edits=0, new_training_runs=0, new_optimizer_runs=0,
                  classification='BRIDGE_DESCRIPTIVE_ONLY', stop_after_handoff=True,
                  root_final_audit_sha256=digest(root / 'FINAL_AUDIT.json'),
                  portable_replay_receipt_sha256=digest(root / 'PORTABLE_REPLAY_QA.json'))
    write_json(dest / 'FINAL_DELIVERY_QA.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--dest', required=True)
    finish(**vars(p.parse_args()))
