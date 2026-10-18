"""Analysis-only regression tests, including complete exported data coverage."""
import csv
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from bridge import kappa, logistic_reference


ROOT = Path(__file__).resolve().parents[1]


def rows(name):
    return list(csv.DictReader((ROOT / name).open(encoding='utf-8')))


def test_factor_and_h1():
    assert kappa(1) == 0
    assert kappa(4)/kappa(2) == 3.5
    assert kappa(2) == .125
    assert kappa(4) == .4375


@pytest.mark.parametrize('seed', [13, 17, 29])
def test_independent_small_objective_directional_differences(seed):
    rng = np.random.default_rng(seed)
    Z = sparse.csr_matrix(rng.normal(size=(120, 6)))
    y = rng.integers(0, 2, size=120)
    x = rng.normal(size=6)/4
    v = rng.normal(size=6)
    v /= np.linalg.norm(v)
    a = logistic_reference(Z, y, x)
    eps = 1e-4
    plus = logistic_reference(Z, y, x+eps*v)
    minus = logistic_reference(Z, y, x-eps*v)
    assert abs((plus['objective']-minus['objective'])/(2*eps)-a['gradient'] @ v) < 1e-8
    np.testing.assert_allclose((plus['gradient']-minus['gradient'])/(2*eps), a['A'] @ v, rtol=2e-7, atol=1e-9)
    trace_fd = np.sum((plus['A']-minus['A'])*a['Sigma'])/(2*eps)
    assert abs(trace_fd-a['T'] @ v) < 1e-8
    np.testing.assert_allclose(a['A'] @ a['q'], -a['T'], atol=1e-14)


def test_all_cells_windows_and_h1_missing_not_nan():
    rr = rows('ALL_CELLS_ALL_WINDOWS.csv')
    assert len(rr) == 63
    assert len(set(r['cell_id'] for r in rr)) == 9
    for cell in set(r['cell_id'] for r in rr):
        assert sorted(int(r['K']) for r in rr if r['cell_id'] == cell) == [1, 2, 4, 8, 16, 32, 64]
    for r in rr:
        assert int(r['independent_seeds']) == 12 and int(r['dimension']) == 124
        if r['H'] == '1':
            assert float(r['proxy_norm']) == 0
            assert r['undefined_ratio_status'] == 'UNDEFINED_ZERO_PROXY'
            for name in ['cosine', 'norm_ratio', 'projection_ratio', 'relative_residual']:
                assert r[name] == ''
        assert r['status'] == 'EXPLORATORY_FINITE_TAIL_NOT_STATIONARY'


def test_no_nonfinite_primary_csv_numbers():
    for path in ROOT.glob('*.csv'):
        if path.name in ['INPUT_ARCHIVES.csv', 'INPUT_SHA256.csv']:
            continue
        for row in csv.DictReader(path.open(encoding='utf-8')):
            for key, text in row.items():
                if not text:
                    continue
                try:
                    value = float(text)
                except ValueError:
                    continue
                assert np.isfinite(value), (path.name, key, text)


def test_full_vectors_and_seed_coverage():
    v = np.load(ROOT / 'VECTORS.npz')
    assert v['paired'].shape == (63, 12, 124)
    assert v['paired_early_late'].shape == (54, 12, 124)
    rr = rows('PAIRED_SEED_RESULTS.csv')
    assert len(rr) == 756
    assert set(int(r['seed']) for r in rr) == set(range(20001, 20013))
    for a in v.files:
        if np.issubdtype(v[a].dtype, np.number):
            assert np.isfinite(v[a]).all()


def test_actual_mean_residual_directly():
    v = np.load(ROOT / 'VECTORS.npz')
    rr = rows('ALL_CELLS_ALL_WINDOWS.csv')
    for j, r in enumerate(rr):
        delta = v['paired'][j].mean(axis=0)
        p = v['proxy'][j]
        np.testing.assert_allclose(float(r['observed_norm']), np.linalg.norm(delta), rtol=1e-12)
        np.testing.assert_allclose(float(r['residual_norm']), np.linalg.norm(delta-p), rtol=1e-11)
        np.testing.assert_allclose(float(r['observed_projection']), delta @ v['direction'], rtol=1e-11, atol=1e-25)


def test_all_original_failed_gates_and_decisions_retained():
    rr = rows('prior_e4/TEMPORAL_DIAGNOSTICS.csv')
    assert len(rr) == 144
    assert all(r['temporal_equivalence'] == 'False' and r['stationary_certified'] == 'False' for r in rr)
    decision = json.loads((ROOT / 'prior_e4/DECISIONS.json').read_text())
    assert all(r['finite_tail_crossover'] == 'NO_CERTIFIED_CROSSOVER' for r in decision)
    assert all(r['stationary_behavior'] == 'NOT_CERTIFIED' for r in decision)


def test_common_seed_weights_and_no_fit():
    a = np.load(ROOT / 'INFERENCE_ARRAYS.npz')
    assert a['weights'].shape == (19999, 12)
    np.testing.assert_array_equal(a['weights'].sum(axis=1), np.full(19999, 12))
    expected = np.random.default_rng(202610096).multinomial(12, np.full(12, 1/12), size=19999)
    np.testing.assert_array_equal(expected, a['weights'])
    receipt = json.loads((ROOT / 'STATISTICAL_METHOD_RECEIPT.json').read_text())
    assert receipt['new_training'] is False and receipt['fitted_parameters'] == 0
    assert receipt['vector_family_size'] == 117 and receipt['scalar_family_size'] == 1068


def test_all_scaling_and_window_diagnostics():
    rr = rows('SCALING_COMPARISONS.csv')
    assert len(rr) == 49
    assert len(rows('EARLY_LATE_PAIRED_DIAGNOSTICS.csv')) == 54
    for r in rr:
        if r['kind'] == 'H':
            assert float(r['proxy_ratio']) == 3.5
    assert all(r['passed'] == 'True' for r in rows('NUMERICAL_CROSSCHECKS.csv'))
