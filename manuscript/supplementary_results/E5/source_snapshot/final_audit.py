"""Final completed-artifact gate, separate from the inferential calculations."""
import argparse
import csv
import json
from pathlib import Path

from prepare import digest, write_json


def audit(root):
    root = Path(root)
    required = ['SCIENTIFIC_SUMMARY.md', 'REVIEWER_RISK_DECISION.md', 'CLAIM_EVIDENCE_MAP.md',
                'SCOPE_AND_LIMITATIONS.md', 'HANDOFF.md', 'MISSING_ITEMS.md', 'PROTOCOL_AND_POSTHOC_STATUS.md',
                'ALL_CELLS_ALL_WINDOWS.csv', 'FULL_VECTOR_ALIGNMENT.csv', 'SCALING_COMPARISONS.csv',
                'PAIRED_BOOTSTRAP_SENSITIVITY.csv', 'NEGATIVE_CONTROLS.csv', 'NUMERICAL_CROSSCHECKS.csv',
                'REPRODUCE.ps1', 'SOURCE_VERSION.json', 'FINAL_FONT_AUDIT.csv', 'E5_FIGURES_GALLERY.pdf']
    for name in required:
        assert (root / name).is_file() and (root / name).stat().st_size > 0, name
    reports = {}
    for name in ['independent_formula/qa/FORMULA_AUDIT_SUMMARY.json',
                 'independent_formula/crosscheck/PRIMARY_CROSSCHECK_SUMMARY.json',
                 'independent_audit/INDEPENDENT_OUTPUT_AUDIT.json',
                 'independent_audit/FINAL_VISUAL_QA_RECEIPT.json',
                 'reviewer_audit/INDEPENDENT_ASSESSMENT_QA.json',
                 'reviewer_audit/PROTECTION_FINAL.json',
                 'FIGURE_NUMERIC_PRESERVATION.json', 'PORTABLE_REPLAY_QA.json']:
        r = json.loads((root / name).read_text())
        assert r['status'] == 'PASS', (name, r)
        reports[name] = dict(sha256=digest(root / name), status=r['status'], checks=r.get('checks', r.get('scalar_value_checks')))
    with (root / 'NUMERICAL_CROSSCHECKS.csv').open() as stream:
        numeric = list(csv.DictReader(stream))
    assert all(r['passed'] == 'True' for r in numeric)
    with (root / 'FINAL_FONT_AUDIT.csv').open() as stream:
        fonts = list(csv.DictReader(stream))
    assert len(fonts) == 6 and all(r['status'] == 'PASS' and float(r['minimum_final_TeX_pt']) >= 9 for r in fonts)
    for r in fonts:
        assert (root / 'figures' / (r['panel']+'.pdf')).exists()
        assert (root / 'FIGURE_DATA' / (r['panel']+'.csv')).exists()
    configs = json.loads((root / 'inputs/R0_CONFIGS.json').read_text())
    figure_manifest = json.loads((root / 'figures/FIGURE_MANIFEST.json').read_text())
    caption = figure_manifest['E5_all_windows_diagnostics']['caption'].replace(',', '')
    assert all(str(c['schedule']['batch_length']) in caption for c in configs), 'Caption must disclose every frozen batch length'
    result = dict(status='PASS', required_files=len(required), primary_numerical_checks=len(numeric),
                  independent_receipts=reports, figures=6, final_minimum_font_TeX_pt=min(float(r['minimum_final_TeX_pt']) for r in fonts),
                  classification='BRIDGE_DESCRIPTIVE_ONLY', new_training_runs=0, new_optimizer_runs=0,
                  preserved_E4_failed_temporal_gates=144, E4_crossover_classification='NO_CERTIFIED_CROSSOVER',
                  E4_overall_classification='INCONCLUSIVE_PRECISION_OR_STATIONARITY',
                  source_version_sha256=digest(root / 'SOURCE_VERSION.json'),
                  manuscript_edited=False, stop_after_handoff=True)
    write_json(root / 'FINAL_AUDIT.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    audit(p.parse_args().root)
