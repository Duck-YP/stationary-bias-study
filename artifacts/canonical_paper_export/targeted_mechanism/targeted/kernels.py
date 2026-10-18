"""Explicit trigonometric model kernel; float64, no fastmath, no control projection.

Controls use the algebraically equivalent mean-control + centered summed-oracle
form. This preserves the incoming mean control, rather than forcing it to zero.
Server state is updated by averaged accumulated increments (no subtraction of
nearly equal local endpoints in the control update).
"""
import math
import numpy as np
from numba import njit

@njit(cache=True)
def q_compiled(u,v,alpha):
    return (4*alpha*(math.sin(u/2)**2-math.cos(u)*math.sin(v/2)**2),
            -2*alpha*math.sin(u)*math.sin(v))

@njit(cache=True)
def mix(v):
    v=(v^(v>>np.uint64(30)))*np.uint64(0xbf58476d1ce4e5b9)
    v=(v^(v>>np.uint64(27)))*np.uint64(0x94d049bb133111eb)
    return v^(v>>np.uint64(31))

@njit(cache=True)
def noise_word(key,t,h,slot):
    return mix(key ^ (np.uint64(t+1)*np.uint64(0x9e3779b97f4a7c15)) ^
               (np.uint64(h+1)*np.uint64(0xd1b54a32d192ed03)) ^
               (np.uint64(slot+1)*np.uint64(0x8cb92baa3f3d8dd7)))

@njit(cache=True)
def scalar_noise(key,t,h,slot,asymmetric):
    v=noise_word(key,t,h,slot)
    if not asymmetric: return 1. if v & np.uint64(1) else -1.
    # Rejection makes 3 equiprobable outcomes under ideal uniform 64-bit words.
    counter=np.uint64(0)
    while v==np.uint64(0xffffffffffffffff):
        counter+=np.uint64(1)
        v=mix(v ^ key ^ counter*np.uint64(0xa24baed4963ee407))
    return math.sqrt(2.) if v % np.uint64(3)==0 else -1/math.sqrt(2.)

@njit(cache=True)
def explicit_round(x,controls,gamma,eps,weights,B,PH,alpha=.05):
    H,N,_=eps.shape
    theta=np.empty((2,N,2)); oracle_sum=np.zeros((N,2))
    total=np.zeros((2,N,2)); qb=np.zeros((2,2)); eta=np.zeros(2)
    oldmean=np.zeros(2)
    for c in range(N):
        oldmean+=controls[c]/N
        theta[0,c]=x[0]; theta[1,c]=x[1]
    for h in range(H):
        for c in range(N):
            eta-=gamma*weights[h]*eps[h,c]/N
            for a in range(2):
                u,v=theta[a,c,0],theta[a,c,1]
                q0,q1=q_compiled(u,v,alpha)
                qb[a,0]+=weights[h,0]*q0/N
                qb[a,1]+=weights[h,1]*q1/N
                g0=u+q0+eps[h,c,0]; g1=2*v+q1+eps[h,c,1]
                if a==0:
                    oracle_sum[c,0]+=g0; oracle_sum[c,1]+=g1
                    g0+=controls[c,0]; g1+=controls[c,1]
                total[a,c,0]+=g0; total[a,c,1]+=g1
                theta[a,c,0]-=gamma*g0; theta[a,c,1]-=gamma*g1
    mean_oracle=np.zeros(2); mean_total=np.zeros((2,2))
    for c in range(N):
        mean_oracle+=oracle_sum[c]/N
        mean_total+=total[:,c,:]/N
    new=x-gamma*mean_total
    ctrl=np.empty_like(controls)
    for c in range(N): ctrl[c]=oldmean+(mean_oracle-oracle_sum[c])/H
    bal=-gamma*qb/B
    # Residual of zero-sum ideal recursion includes actual finite control mean.
    res=new-(x*PH+eta-gamma*qb)
    return new,ctrl,bal,eta,res

@njit(cache=True)
def trigonometric_chunk(x,controls,key,start,count,N,H,gamma,weights,B,PH,rho,asymmetric,alpha=.05):
    raw=np.empty((count,2,2)); bal=np.empty_like(raw)
    etas=np.empty((count,2)); residual=np.empty_like(raw); ctrlmean=np.empty((count,2))
    scales=np.array([math.sqrt(1+rho),math.sqrt(1-rho)])
    eps=np.empty((H,N,2))
    for t in range(count):
        for h in range(H):
            for c in range(N):
                for j in range(2): eps[h,c,j]=scales[j]*scalar_noise(key,start+t,h,c*2+j,asymmetric)
        x,controls,z,eta,res=explicit_round(x,controls,gamma,eps,weights,B,PH,alpha)
        raw[t]=x; bal[t]=z; etas[t]=eta; residual[t]=res
        ctrlmean[t]=0.
        for c in range(N): ctrlmean[t]+=controls[c]/N
    return x,controls,raw,bal,etas,residual,ctrlmean
