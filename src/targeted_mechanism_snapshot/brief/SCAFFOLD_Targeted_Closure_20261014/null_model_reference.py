"""Analytical reference for proposed SCAFFOLD mechanism checks.

This file defines an objective and coefficient targets. It is not a production
simulation or evidence that any coefficient has been empirically verified.

Usage: python null_model_reference.py
Requires numpy. All targets use the manuscript's additive-noise model.
"""
from __future__ import annotations
import itertools
import json
import math
import numpy as np

ALPHA = 0.05
A = np.diag([1.0, 2.0])


def _points(x):
    a = np.asarray(x, dtype=float)
    if a.ndim < 1 or a.shape[-1] != 2 or not np.all(np.isfinite(a)):
        raise ValueError('Expected finite points with last dimension 2.')
    return a


def _sin_minus_x(t):
    """Stable sin(t)-t near the minimizer; no stochastic rescaling."""
    t = np.asarray(t, dtype=float)
    polynomial = t**3 * (-1/6 + t**2 * (1/120 + t**2 * (-1/5040 + t**2/362880)))
    return np.where(np.abs(t) < 0.01, polynomial, np.sin(t)-t)


def objective(x, alpha=ALPHA):
    x = _points(x)
    a, b = x[..., 0], x[..., 1]
    g = -4*_sin_minus_x(a) + _sin_minus_x(a+b) + _sin_minus_x(a-b)
    return 0.5*(a*a + 2*b*b) + alpha*g


def nonlinear_gradient(x, alpha=ALPHA):
    """q(x)=grad f(x)-Ax; stable form avoids subtracting cosines near zero."""
    x = _points(x)
    a, b = x[..., 0], x[..., 1]
    q1 = 4*alpha*(np.sin(a/2)**2 - np.cos(a)*np.sin(b/2)**2)
    q2 = -2*alpha*np.sin(a)*np.sin(b)
    return np.stack([q1, q2], axis=-1)


def gradient(x, alpha=ALPHA):
    x = _points(x)
    return x @ A.T + nonlinear_gradient(x, alpha)


def hessian(x, alpha=ALPHA):
    x = _points(x)
    a, b = x[..., 0], x[..., 1]
    h = np.empty(x.shape[:-1]+(2,2))
    h[..., 0, 0] = 1 + 2*alpha*np.sin(a)*(2-np.cos(b))
    h[..., 0, 1] = h[..., 1, 0] = -2*alpha*np.cos(a)*np.sin(b)
    h[..., 1, 1] = 2 - 2*alpha*np.sin(a)*np.cos(b)
    return h


def third_tensor_at_zero(alpha=ALPHA):
    t = np.zeros((2,2,2))
    t[0,0,0] = 2*alpha
    t[0,1,1] = t[1,0,1] = t[1,1,0] = -2*alpha
    return t


def contract(m, alpha=ALPHA):
    m = np.asarray(m, dtype=float)
    if m.shape != (2,2) or not np.allclose(m, m.T, atol=1e-14, rtol=0):
        raise ValueError('Expected symmetric 2 x 2 matrix.')
    return np.einsum('ijk,jk->i', third_tensor_at_zero(alpha), m)


def covariance(rho):
    if not np.isfinite(rho) or abs(rho) >= 1:
        raise ValueError('|rho| must be < 1.')
    return np.diag([1+rho, 1-rho])


def theory(rho, H=4, alpha=ALPHA):
    if H < 1 or int(H) != H or not (0 < alpha < 1/8):
        raise ValueError('Require integer H>=1 and 0<alpha<1/8.')
    c = covariance(rho)
    sc = np.diag([(1+rho)/2, (1-rho)/4])
    base = -np.linalg.solve(A, contract(c, alpha))
    b11 = -0.5*np.linalg.solve(A, contract(sc, alpha))
    mu, L = 1-8*alpha, 2+8*alpha
    return {
        'rho': float(rho), 'H': int(H), 'alpha': float(alpha),
        'A': A.tolist(), 'C': c.tolist(), 'S_C': sc.tolist(),
        'T_C': contract(c, alpha).tolist(),
        'T_S_C': contract(sc, alpha).tolist(), 'B11': b11.tolist(),
        'B20_scaffold': (((H-1)*(5*H-1)/(12*H))*base).tolist(),
        'B20_fedavg': (((H-1)/4)*base).tolist(),
        'B20_control': (((H-1)*(2*H-1)/(12*H))*base).tolist(),
        'mu_conservative': mu, 'L_conservative': L,
        'gamma_imported': min(1., 1/(48*L), 1/(24*H*(L+mu))),
        'gamma0_full_theorem_certified': False,
    }


def exact_noise_moments():
    laws = {
        'symmetric_rademacher': ([-1.,1.], [0.5,0.5]),
        'asymmetric_two_point': ([math.sqrt(2), -1/math.sqrt(2)], [1/3,2/3]),
    }
    out = {}
    for name,(values, probs) in laws.items():
        values, probs = np.asarray(values), np.asarray(probs)
        out[name] = {f'moment_{j}': float(np.dot(probs, values**j)) for j in range(1,7)}
    return out


def self_check():
    np.testing.assert_allclose(gradient([0,0]), [0,0], atol=1e-15)
    np.testing.assert_allclose(hessian([0,0]), A, atol=1e-15)
    rows=[]
    for rho in [-0.25,0.,0.25]:
        row=theory(rho)
        np.testing.assert_allclose(row['T_C'], [4*ALPHA*rho,0], atol=1e-15)
        np.testing.assert_allclose(row['B11'], [-ALPHA*(1+3*rho)/4,0], atol=1e-15)
        c, sc = np.array(row['C']), np.array(row['S_C'])
        np.testing.assert_allclose(A@sc+sc@A, c, atol=1e-15)
        np.testing.assert_allclose(np.array(row['B20_fedavg'])+row['B20_control'],
                                   row['B20_scaffold'], atol=1e-15)
        rows.append(row)
    assert np.linalg.norm(third_tensor_at_zero()) > 0
    np.testing.assert_allclose(theory(0)['B20_control'], [0,0], atol=1e-15)
    np.testing.assert_allclose(theory(0)['B11'], [-0.0125,0], atol=1e-15)
    moments=exact_noise_moments()
    for values in moments.values():
        np.testing.assert_allclose(values['moment_1'],0,atol=1e-15)
        np.testing.assert_allclose(values['moment_2'],1,atol=1e-15)
    np.testing.assert_allclose(moments['asymmetric_two_point']['moment_3'],1/math.sqrt(2),atol=1e-15)
    return {'status':'ANALYTICAL_REFERENCE_CHECKED_NOT_SIMULATED', 'targets':rows,
            'noise_moments': moments}

if __name__ == '__main__':
    print(json.dumps(self_check(), indent=2, allow_nan=False))
