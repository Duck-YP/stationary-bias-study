"""Independent scalar-round, timing, and active-path checks.

This checker does not import targeted.model, targeted.tests, or coefficient
targets. It derives weights directly from A=diag(1,2), evaluates scalar
objective derivatives, and follows original endpoint/control recursions.
Outputs remain in certificate/. Run with numpy and numba available.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import numba

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from targeted.kernels import explicit_round, q_compiled, scalar_noise, trigonometric_chunk


def independently_derived_gradient(x, alpha):
    u, v = x
    return np.array([u+alpha*(-4*(math.cos(u)-1)+(math.cos(u+v)-1)+(math.cos(u-v)-1)),
                     2*v+alpha*(math.cos(u+v)-math.cos(u-v))])


def own_operators(gamma, H):
    p = np.array([1-gamma, 1-2*gamma])
    # Repeated multiplication, independently of the stable log1p/expm1 path.
    weights = np.ones((H, 2))
    for h in range(H-2, -1, -1):
        weights[h] = weights[h+1]*p
    PH = weights[0]*p
    return weights, 1-PH, PH


def scalar_original_round(x, ctrl, gamma, eps, alpha):
    H, N, _ = eps.shape
    weights, B, PH = own_operators(gamma, H)
    local = np.tile(x[:, None, :], (1, N, 1))
    q_sum = np.zeros((2, 2))
    noise_sum = np.zeros(2)
    for h in range(H):
        for c in range(N):
            noise_sum += weights[h]*eps[h, c]/N
            for algorithm in (0, 1):
                grad = independently_derived_gradient(local[algorithm, c], alpha)
                nonlinear = grad - np.array([1., 2.])*local[algorithm, c]
                q_sum[algorithm] += weights[h]*nonlinear/N
                force = grad + eps[h, c]
                if algorithm == 0:
                    force = force + ctrl[c]
                local[algorithm, c] -= gamma*force
    server = np.mean(local, axis=1)
    new_controls = ctrl + (local[0]-server[0])/(gamma*H)
    balance = np.array([-gamma*np.linalg.solve(np.diag(B), q_sum[a]) for a in (0, 1)])
    return server, new_controls, balance, -gamma*noise_sum


def measure_close(a, b, tolerance):
    difference = float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
    assert difference <= tolerance, (difference, tolerance)
    return difference


def main():
    rng = np.random.default_rng(202610140932)
    stats = {"state_max_abs_difference": 0., "control_max_abs_difference": 0.,
             "balance_max_abs_difference": 0., "eta_max_abs_difference": 0.,
             "control_mean_max_abs_drift": 0., "gradient_max_abs_difference": 0.}
    rows = []
    for point in rng.uniform(-3, 3, size=(120, 2)):
        q = np.array(q_compiled(*point, .05))
        stats["gradient_max_abs_difference"] = max(stats["gradient_max_abs_difference"],
            measure_close(q+np.array([1., 2.])*point, independently_derived_gradient(point, .05), 2e-15))
    for N, H, gamma, alpha, mean in [
        (3, 1, 1/512, .05, (0., 0.)),
        (7, 4, 1/512, .05, (0., 0.)),
        (7, 4, 1/2048, .05, (.13, -.21)),
        (11, 4, 1/1024, 0., (0., 0.)),
        (11, 4, 1/2048, 0., (.07, .11)),
    ]:
        x = rng.normal(size=(2, 2))*.3
        controls = rng.normal(size=(N, 2))*.2
        # Test-data construction only. The kernel must not project its controls.
        controls -= controls.mean(axis=0)
        controls += np.array(mean)
        initial_control_mean = controls.mean(axis=0)
        weights, B, PH = own_operators(gamma, H)
        for t in range(19):
            eps = rng.choice(np.array([-1., 1.]), size=(H, N, 2)) * np.sqrt([1.25, .75])
            expect = scalar_original_round(x, controls, gamma, eps, alpha)
            got = explicit_round(x.copy(), controls.copy(), gamma, eps, weights, B, PH, alpha)
            for key, a, b, tol in [
                ("state_max_abs_difference", got[0], expect[0], 3e-15),
                ("control_max_abs_difference", got[1], expect[1], 5e-12),
                ("balance_max_abs_difference", got[2], expect[2], 2e-15),
                ("eta_max_abs_difference", got[3], expect[3], 2e-17),
                ("control_mean_max_abs_drift", got[1].mean(axis=0), initial_control_mean, 3e-15),
            ]:
                stats[key] = max(stats[key], measure_close(a, b, tol))
            # With nonzero mean controls the ideal zero-sum recursion has a
            # known residual; preservation rather than projection is tested.
            analytic_residual = np.zeros((2, 2))
            analytic_residual[0] = -gamma*np.sum(weights, axis=0)*controls.mean(axis=0)
            measure_close(got[4], analytic_residual, 3e-15)
            if alpha == 0:
                assert np.array_equal(got[2], np.zeros((2, 2)))
            x, controls = got[0], got[1]
        rows.append({"N": N, "H": H, "gamma": gamma, "alpha": alpha,
                     "initial_control_mean": list(mean), "rounds": 19, "status": "PASS"})

    # H=1 has an exact algorithm-global-state identity when the starts coincide.
    N, H, gamma = 9, 1, 1/1024
    ops = own_operators(gamma, H)
    x = np.array([[.23, -.11], [.23, -.11]])
    ctrl = rng.normal(size=(N, 2)); ctrl -= ctrl.mean(axis=0)
    h1_max = 0.
    for t in range(31):
        eps = rng.normal(size=(H, N, 2))
        x, ctrl, *_ = explicit_round(x, ctrl, gamma, eps, *ops, .05)
        h1_max = max(h1_max, measure_close(x[0], x[1], 5e-15))

    # Deterministic identical starts remain identical, with no fabricated bias.
    N, H, gamma = 5, 4, 1/512
    ops = own_operators(gamma, H)
    x = np.array([[.3, -.1], [.3, -.1]]); ctrl = np.zeros((N, 2))
    for t in range(27):
        x, ctrl, *_ = explicit_round(x, ctrl, gamma, np.zeros((H, N, 2)), *ops, .05)
        measure_close(x[0], x[1], 1e-16)
        measure_close(ctrl, np.zeros_like(ctrl), 3e-15)

    # Independent reconstruction of active indexed path, both noise marginals,
    # nonzero initial states and controls; split run/reload is bitwise identical.
    N, H, gamma, T = 8, 4, 1/2048, 79
    ops = own_operators(gamma, H)
    x0 = np.array([[.13, -.17], [-.11, .23]])
    c0 = rng.normal(size=(N, 2))*.1; c0 -= c0.mean(axis=0)
    key = np.uint64(871232961)
    indexed = []
    for asymmetric in (False, True):
        all_at_once = trigonometric_chunk(x0.copy(), c0.copy(), key, 0, T, N, H, gamma,
                                          *ops, .25, asymmetric, .05)
        first = trigonometric_chunk(x0.copy(), c0.copy(), key, 0, 29, N, H, gamma,
                                    *ops, .25, asymmetric, .05)
        checkpoint = HERE / ("kernel_checkpoint_asymmetric.npz" if asymmetric else "kernel_checkpoint_symmetric.npz")
        np.savez(checkpoint, x=first[0], controls=first[1], next_round=29, key=key)
        with np.load(checkpoint) as saved:
            last = trigonometric_chunk(saved["x"], saved["controls"], np.uint64(saved["key"]),
                                       int(saved["next_round"]), T-29, N, H, gamma, *ops, .25, asymmetric, .05)
        for i in (0, 1):
            np.testing.assert_array_equal(all_at_once[i], last[i])
        for i in range(2, 7):
            np.testing.assert_array_equal(all_at_once[i], np.concatenate((first[i], last[i])))
        ownx, ownctrl = x0.copy(), c0.copy()
        active_max = 0.
        for t in range(T):
            eps = np.empty((H, N, 2))
            for h in range(H):
                for c in range(N):
                    for j in range(2):
                        eps[h, c, j] = scalar_noise(key, t, h, 2*c+j, asymmetric)*math.sqrt((1.25, .75)[j])
            ownx, ownctrl, *_ = scalar_original_round(ownx, ownctrl, gamma, eps, .05)
            active_max = max(active_max, measure_close(ownx, all_at_once[2][t], 2e-12))
        # Both finite-window conventions, including recorded arithmetic/control
        # residuals. We check arbitrary nonstationary initial conditions.
        raw, balance, etas, rec_res = all_at_once[2:6]
        pre = np.concatenate((x0[None, :, :], raw[:-1]))
        delta = (raw[-1]-x0)/T
        rpre = ops[1]*(pre.mean(axis=0)-balance.mean(axis=0))-etas.mean(axis=0)+delta-rec_res.mean(axis=0)
        rpost = ops[1]*(raw.mean(axis=0)-balance.mean(axis=0))-etas.mean(axis=0)+ops[2]*delta-rec_res.mean(axis=0)
        paired = ops[1]*((raw[:,0]-raw[:,1]).mean(axis=0)-(balance[:,0]-balance[:,1]).mean(axis=0))
        paired += ops[2]*(delta[0]-delta[1])-(rec_res[:,0]-rec_res[:,1]).mean(axis=0)
        preerr = measure_close(rpre, np.zeros_like(rpre), 3e-17)
        posterr = measure_close(rpost, np.zeros_like(rpost), 3e-17)
        pairerr = measure_close(paired, np.zeros_like(paired), 3e-17)
        indexed.append({"asymmetric": asymmetric, "rounds": T, "checkpoint_round": 29,
                        "bitwise_resume_equal": True, "active_scalar_path_max_abs_difference": active_max,
                        "pre_window_identity_max_abs_residual": preerr,
                        "post_window_identity_max_abs_residual": posterr,
                        "paired_post_window_identity_max_abs_residual": pairerr})
    source = HERE.parent / "targeted" / "kernels.py"
    report = {"status": "PASS_INDEPENDENT_KERNEL_CHECKS", "unit_round_cases": rows,
              "maxima": stats, "H1_global_identity_max_abs_difference": h1_max,
              "deterministic_rounds": 27, "indexed_path_cases": indexed,
              "source_sha256": {"targeted/kernels.py": hashlib.sha256(source.read_bytes()).hexdigest(),
                                "certificate/independent_kernel_checks.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              "environment": {"python": sys.version, "executable": sys.executable,
                              "numpy": np.__version__, "numba": numba.__version__, "platform": platform.platform()},
              "noise_generator_assessment": "Deterministic indexed pseudorandom hash with fixed key and disjoint round/step/client-coordinate indices. Within-condition algorithms share the same explicit array. Symmetric mapping has one bit; asymmetric mapping rejects 2^64-1 and maps modulo 3. Exact support moments are separately verified. This is a simulation PRNG assumption, not a mathematical independence certificate for a finite keyed generator.",
              "scope": "No coefficient targets were imported or injected. Tests verify recursions, selected model, control preservation, timing and checkpoint state; they do not establish stationarity or asymptotic coefficients."}
    output = HERE / "independent_kernel_checks.json"
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
