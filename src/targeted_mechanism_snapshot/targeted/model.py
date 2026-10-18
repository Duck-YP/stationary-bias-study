import math
import numpy as np
A = np.diag([1.,2.])
ALPHA = .05
def objective(x, alpha=ALPHA):
    u,v=x
    return .5*(u*u+2*v*v)+alpha*(-4*(np.sin(u)-u)+(np.sin(u+v)-u-v)+(np.sin(u-v)-u+v))
def gradient_reference(x, alpha=ALPHA):
    u,v=x
    return np.array([u+alpha*(-4*(np.cos(u)-1)+(np.cos(u+v)-1)+(np.cos(u-v)-1)),
                     2*v+alpha*(np.cos(u+v)-np.cos(u-v))])
def q_stable(x, alpha=ALPHA):
    u,v=x
    return np.array([4*alpha*(np.sin(u/2)**2-np.cos(u)*np.sin(v/2)**2),-2*alpha*np.sin(u)*np.sin(v)])
def operators(gamma,H):
    p=1-gamma*np.diag(A)
    weights=np.array([p**(H-1-h) for h in range(H)])
    B=-np.expm1(H*np.log1p(-gamma*np.diag(A)))
    return weights,B,p**H
def targets(rho,H=4):
    contraction=np.array([4*ALPHA*rho,0.])
    b11=np.array([-ALPHA*(1+3*rho)/4,0.])
    fed=-(H-1)/4*contraction
    increment=-(H-1)*(2*H-1)/(12*H)*contraction
    return {'B11':b11,'FedAvg':fed,'SCAFFOLD':fed+increment,'difference':increment}
def reference_round(x,controls,gamma,eps,alpha=ALPHA):
    """Straight objective-gradient Euler recursion, independent of compiled arithmetic."""
    H,N,_=eps.shape
    theta=np.repeat(x[:,None,:],N,axis=1)
    before=[]
    for h in range(H):
        before.append(theta.copy())
        for a in range(2):
            for c in range(N):
                g=gradient_reference(theta[a,c],alpha)+eps[h,c]
                if a==0: g=g+controls[c]
                theta[a,c]-=gamma*g
    new=theta.mean(axis=1)
    ctrl=controls+(theta[0]-new[0])/(gamma*H)
    return new,ctrl,np.array(before)
