"""Freeze E4 analysis choices before computing window outcomes."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def freeze(root):
    root = Path(root)
    path = root / 'E4_v1_PROTOCOL_FROZEN.json'
    if path.exists():
        raise RuntimeError('Frozen E4 protocol already exists; never overwrite it.')
    cells = json.loads((root / 'inputs/R0_CONFIGS.json').read_text())
    primary = 'E3_R0_p0_H4_N128_g0.196078431373'
    secondary = ['E3_R0_p0_H4_N8_g0.196078431373', 'E3_R0_p0_H4_N32_g0.196078431373']
    proto = {
        'version': 'E4_v1_existing_run_replay',
        'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'no_training': True, 'no_manuscript_changes': True,
        'cells': cells, 'seeds': list(range(20001, 20013)),
        'K': [1, 2, 4, 8, 16, 32, 64], 'same_end_batch': 64,
        'model_source': 'batch_raw_sum of actual post-update global iterates / batch_count',
        'algorithms': ['SCAFFOLD', 'FedAvg'],
        'primary_cell': primary, 'secondary_cells': secondary,
        'families': {'primary': [primary], 'secondary': secondary,
                     'diagnostic': [c['id'] for c in cells if c['id'] not in [primary] + secondary]},
        'bootstrap': {'draws': 19999, 'seed': 202610094, 'coverage': 0.95,
                      'unit': 'paired independent seed label; one multinomial count vector across all cells/algorithms/K',
                      'method': 'standardized max absolute empirical-population-centered bootstrap deviation',
                      'centering': 'U0=||b_hat||^2; V0=(R-1)/R V_hat; MSE0=MSE_hat; all derived functionals use these centers',
                      'scalar_family_per_cell': ['both algorithms all K: U,V,MSE,U_minus_V,U_minus_0.1MSE,projection,train_gap,test_loss,share,V_minus_K1',
                                                 'all K: delta_U,delta_V,delta_MSE,delta_projection,delta_train,delta_test,U_delta,C_cross'],
                      'limits': 'Approximate finite-R bootstrap, not exact coverage or a stationary-law certificate'},
        'sensitivity': {'method': 'delete-one seed jackknife-t; Bonferroni within same scalar family',
                        'decision': 'positive crossover/materiality needs both max-bootstrap and nondegenerate jackknife sensitivity lower bounds >0',
                        'degeneracy': 'jackknife SE <1e-3 bootstrap SD is weak precision, never strong evidence'},
        'materiality': {'MSE_share': 0.10, 'scope': 'researcher-chosen parameter-error benchmark, not predictive-harm threshold'},
        'temporal': {'contrasts': 'first vs last K batches for K=1,2,4,8,16,32; middle vs last at K=8,16; K64 inherits first/last32 only',
                     'projection_equivalence_margin': 1e-4, 'vector_norm_equivalence_margin': 1e-3,
                     'family': 'all R0 cells, both algorithms, all declared temporal contrasts',
                     'vector_bound': '||mean paired drift|| + q95 * sqrt(trace(sample covariance)/R); q95 from paired bootstrap max standardized norm deviation',
                     'projection_bound': 'simultaneous standardized absolute bootstrap deviations',
                     'gate': 'both vector and frozen-projection equivalence pass for own first/last K (K64 uses K32)',
                     'interpretation': 'operational finite-tail equivalence only; no non-rejection-as-stability; no stationary certificate'},
        'crossover': {'descriptive': 'signed U>=V',
                      'uncertainty_supported': 'U-V lower bounds >0 under primary/secondary family bootstrap AND jackknife; temporal gate; >=2 consecutive declared K',
                      'stationary_behavior': 'NOT_CERTIFIED, irrespective of finite-tail crossover'},
        'objective': {'lambda': 0.01, 'all_124_coordinates_regularized': True,
                      'train': 'frozen retained32512 uniform rows', 'test': 'frozen a9a.t16281 rows with same row normalization and intercept',
                      'evaluate': 'each individual run model Y, not mean checkpoint losses',
                      'prediction_claim': 'no claim of consequential predictive harm from parameter share alone; report absolute and baseline-relative test change'},
        'raw_checkpoint_baseline': 'batch_sumsq/count estimates mean ||x-x_ref||^2; raw variance = rawMSE - signed full-tail U, not averaged-model V',
        'controlled_bridge': 'NOT_EXECUTED; CONTROL_COEFFICIENT_NOT_ISOLATED_IN_REAL_DATA',
        'phase4_trigger': 'missing reconstructible averages OR insufficient evidence for a stationary interpretation; cost and separate v2 before any training',
        'inputs_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted((root / 'inputs').iterdir()) if p.is_file()},
    }
    path.write_text(json.dumps(proto, indent=2) + '\n', encoding='utf-8')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_suffix('.sha256').write_text(digest + '\n')
    print(json.dumps({'frozen_protocol': str(path), 'sha256': digest, 'before_window_analysis': True}))


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    freeze(p.parse_args().root)
