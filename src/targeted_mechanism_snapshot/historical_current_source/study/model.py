import numpy as np
from scipy.linalg import solve_continuous_lyapunov
from scipy.special import expit
from scipy.integrate import quad

A = np.array([[1.2, .2], [.2, 1.]])
C = np.array([[1., .2], [.2, .7]])
U = np.ones(2) / np.sqrt(2.)
ALPHA = .25
LAM = .01


def logcosh(z):
    # log1p avoids cancellation near zero; tanh is bounded at large z.
    t = np.abs(np.asarray(z))
    return t + np.log1p(np.exp(-2*t)) - np.log(2.) if np.any(t > 15) else np.log1p(2*np.sinh(t/2)**2)


def grad(x):
    return x @ A.T + ALPHA * logcosh(x @ U)[..., None] * U


def hessian(x):
    return A + ALPHA * np.tanh(x @ U) * np.outer(U, U)


def third_contract(x, matrix):
    return ALPHA / np.cosh(x @ U)**2 * U * (U @ matrix @ U)


def objective(x):
    return .5*x @ A @ x + ALPHA*quad(lambda z: float(logcosh(z)), 0, x @ U, epsabs=1e-13)[0]


def theory(H):
    sc = solve_continuous_lyapunov(A, C)
    tc = third_contract(np.zeros(2), C)
    base = -np.linalg.solve(A, tc)
    mu = float(np.linalg.eigvalsh(A - ALPHA*np.outer(U,U))[0])
    L = float(np.linalg.eigvalsh(A + ALPHA*np.outer(U,U))[-1])
    k = (H-1)*(2*H-1)/(12*H)
    return dict(B11=(-.5*np.linalg.solve(A, third_contract(np.zeros(2),sc))).tolist(),
                B20_fa=((H-1)/4*base).tolist(), B20_ctrl=(k*base).tolist(),
                B20_scaf=((H-1)*(5*H-1)/(12*H)*base).tolist(),
                Z_target=base.tolist(), kappa=k, mu=mu, L=L,
                gamma_imp=min(1.,1/(48*L),1/(24*H*(L+mu))))


def logistic(Z, y, x):
    p = expit(Z @ x)
    g = Z.T @ (p-y)/len(y) + LAM*x
    h = (Z.T*(p*(1-p))) @ Z/len(y) + LAM*np.eye(Z.shape[1])
    f = np.mean(np.logaddexp(0, Z @ x)-y*(Z @ x)) + LAM/2*(x @ x)
    return f, g, h
