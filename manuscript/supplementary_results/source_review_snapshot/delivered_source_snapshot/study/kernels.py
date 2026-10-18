"""Scalar reference and separately implemented compiled production recursions."""
import math
import numpy as np
from numba import njit
from .model import A, U, ALPHA, grad


def reference(x, xi, gamma, eps, scaffold=True, shifts=None, matrix=A, alpha=ALPHA, direction=U):
    H, N, d = eps.shape
    local = np.zeros((N,d))
    before = np.zeros((H,N,d))
    for c in range(N):
        theta = x.copy()
        for h in range(H):
            before[h,c] = theta
            z = float(theta @ direction)
            az = abs(z)
            lc = math.log1p(2*math.sinh(az/2)**2) if az < 15 else az+math.log1p(math.exp(-2*az))-math.log(2)
            g = np.zeros(d)
            for i in range(d):
                for j in range(d):
                    g[i] += matrix[i,j]*theta[j]
                g[i] += alpha*direction[i]*lc + eps[h,c,i]
                if shifts is not None:
                    g[i] += shifts[c,i]
                if scaffold:
                    g[i] += xi[c,i]
            theta -= gamma*g
        local[c] = theta
    new_x = sum(local[c] for c in range(N))/N
    new_xi = xi.copy()
    if scaffold:
        for c in range(N):
            new_xi[c] = xi[c] + (local[c]-new_x)/(gamma*H)
    return new_x, new_xi, local, before


@njit(cache=True)
def production_round(x, xi, gamma, eps, scaffold, shifts, matrix, alpha, direction):
    H,N,d = eps.shape
    theta = np.empty((N,d))
    before = np.empty((H,N,d))
    for c in range(N):
        theta[c] = x
    for h in range(H):
        before[h] = theta
        for c in range(N):
            z = 0.
            for j in range(d):
                z += theta[c,j]*direction[j]
            az = abs(z)
            lc = math.log1p(2*math.sinh(az/2)**2) if az < 15 else az+math.log1p(math.exp(-2*az))-math.log(2.)
            g = np.empty(d)
            for i in range(d):
                g[i] = alpha*direction[i]*lc+eps[h,c,i]+shifts[c,i]
                for j in range(d):
                    g[i] += matrix[i,j]*theta[c,j]
                if scaffold:
                    g[i] += xi[c,i]
            theta[c] -= gamma*g
    new_x = np.zeros(d)
    for c in range(N):
        new_x += theta[c]/N
    new_xi = xi.copy()
    if scaffold:
        for c in range(N):
            new_xi[c] += (theta[c]-new_x)/(gamma*H)
    return new_x, new_xi, theta, before


@njit(cache=True)
def mix64(v):
    v = np.uint64(v)
    v = (v ^ (v >> np.uint64(30))) * np.uint64(0xbf58476d1ce4e5b9)
    v = (v ^ (v >> np.uint64(27))) * np.uint64(0x94d049bb133111eb)
    return v ^ (v >> np.uint64(31))


@njit(cache=True)
def random_key(key, round_id, h, slot):
    # Indexed substreams: branch-independent and chunk/resume-independent.
    v = key ^ (np.uint64(round_id+1)*np.uint64(0x9e3779b97f4a7c15))
    v ^= np.uint64(h+1)*np.uint64(0xd1b54a32d192ed03)
    v ^= np.uint64(slot+1)*np.uint64(0x8cb92baa3f3d8dd7)
    return mix64(v)


@njit(cache=True)
def controlled_chunk(x, controls, key, start, count, N, H, gamma, weights, balance_solve, chol):
    d=2
    raw = np.zeros((count,2,d))
    bal = np.zeros_like(raw)
    ctrl = np.zeros(count)
    residual = np.zeros(count)
    control_sum = np.zeros((N,d))
    for t in range(count):
        theta = np.empty((2,N,d))
        qb = np.zeros((2,d))
        for a in range(2):
            for c in range(N):
                theta[a,c] = x[a]
        for h in range(H):
            qmean = np.zeros((2,d))
            for c in range(N):
                zz0 = 1. if (random_key(key,start+t,h,c*d) & np.uint64(1)) else -1.
                zz1 = 1. if (random_key(key,start+t,h,c*d+1) & np.uint64(1)) else -1.
                e0=chol[0,0]*zz0
                e1=chol[1,0]*zz0+chol[1,1]*zz1
                for a in range(2):
                    z=(theta[a,c,0]+theta[a,c,1])/math.sqrt(2.)
                    az=abs(z)
                    lc=math.log1p(2*math.sinh(az/2)**2) if az < 15 else az+math.log1p(math.exp(-2*az))-math.log(2.)
                    q=.25/math.sqrt(2.)*lc
                    qmean[a,0]+=q/N
                    qmean[a,1]+=q/N
                    g0=1.2*theta[a,c,0]+.2*theta[a,c,1]+q+e0
                    g1=.2*theta[a,c,0]+theta[a,c,1]+q+e1
                    if a==0:
                        g0+=controls[c,0]
                        g1+=controls[c,1]
                    theta[a,c,0]-=gamma*g0
                    theta[a,c,1]-=gamma*g1
            for a in range(2):
                qb[a]+=weights[h] @ qmean[a]
        x[:]=0.
        for c in range(N):
            x[0]+=theta[0,c]/N
            x[1]+=theta[1,c]/N
        for c in range(N):
            controls[c]+=(theta[0,c]-x[0])/(gamma*H)
        s=np.zeros(d)
        for c in range(N):
            ctrl[t]+=np.dot(controls[c],controls[c])/N
            s+=controls[c]
            control_sum[c]+=controls[c]
        residual[t]=np.sqrt(np.dot(s,s))
        raw[t]=x
        for a in range(2):
            bal[t,a]=-gamma*(balance_solve @ qb[a])
    return x,controls,raw,bal,ctrl,residual,control_sum


@njit(cache=True)
def logistic_chunk(x, controls, key, start, count, H, gamma, m, members, indptr, indices, values, labels):
    N,d=controls.shape
    raw=np.empty((count,2,d))
    ctrl=np.zeros(count)
    residual=np.zeros(count)
    control_sum=np.zeros((N,d))
    for t in range(count):
        theta=np.empty((2,N,d))
        for a in range(2):
            for c in range(N):
                theta[a,c]=x[a]
        for h in range(H):
            for c in range(N):
                g=np.zeros((2,d))
                for s in range(m):
                    # All R0 H=1 allocations map the same total index list.
                    k=random_key(key,start+t,h,c*m+s)
                    row=members[c,int(k % np.uint64(members.shape[1]))]
                    for a in range(2):
                        z=0.
                        for j in range(indptr[row],indptr[row+1]):
                            z+=values[j]*theta[a,c,indices[j]]
                        if z>=0:
                            p=1/(1+math.exp(-z))
                        else:
                            ez=math.exp(z)
                            p=ez/(1+ez)
                        err=(p-labels[row])/m
                        for j in range(indptr[row],indptr[row+1]):
                            g[a,indices[j]]+=err*values[j]
                for j in range(d):
                    theta[0,c,j]-=gamma*(g[0,j]+.01*theta[0,c,j]+controls[c,j])
                    theta[1,c,j]-=gamma*(g[1,j]+.01*theta[1,c,j])
        x[:]=0.
        for c in range(N):
            x[0]+=theta[0,c]/N
            x[1]+=theta[1,c]/N
        total=np.zeros(d)
        for c in range(N):
            controls[c]+=(theta[0,c]-x[0])/(gamma*H)
            total+=controls[c]
            ctrl[t]+=np.dot(controls[c],controls[c])/N
            control_sum[c]+=controls[c]
        residual[t]=np.sqrt(np.dot(total,total))
        raw[t]=x
    return x,controls,raw,ctrl,residual,control_sum


def stream_key(family, partition, seed, cell):
    import hashlib
    # Across-configuration CRN only for the explicit R0 H=1 allocation gate.
    return np.uint64(int.from_bytes(hashlib.sha256(f"{family}|{partition}|{seed}|{cell}".encode()).digest()[:8],"little"))
