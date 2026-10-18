"""Independent differentiation and direct original-update checks (short trajectories only)."""
import json, os, sys
from pathlib import Path
import numpy as np
import sympy as s
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'audit'
os.environ['NUMBA_CACHE_DIR']=str(ROOT/'test_env/cache')
sys.path.insert(0,str(ROOT/'test_env'))
from targeted.kernels import explicit_round, q_compiled
x,y,rho=s.symbols('x y rho', real=True); alpha=s.Rational(1,20)
f=(x*x+2*y*y)/2+alpha*(-4*(s.sin(x)-x)+s.sin(x+y)-(x+y)+s.sin(x-y)-(x-y))
grad=s.Matrix([s.diff(f,z) for z in (x,y)]); A=s.hessian(f,(x,y)).subs({x:0,y:0})
T=[[[s.diff(f,zi,zj,zk).subs({x:0,y:0}) for zk in (x,y)] for zj in (x,y)] for zi in (x,y)]
C=s.diag(1+rho,1-rho); SC=s.Matrix(2,2,lambda i,j:C[i,j]/(A[i,i]+A[j,j]))
contract=lambda M:s.Matrix([sum(T[i][j][k]*M[j,k] for j in range(2) for k in range(2)) for i in range(2)])
b11=s.simplify(-A.inv()*contract(SC)/2);v=s.simplify(A.inv()*contract(C))
assert A==s.diag(1,2);assert contract(s.eye(2))==s.zeros(2,1)
assert b11.subs(rho,0)==s.Matrix([-s.Rational(1,80),0])
assert s.simplify(f.subs(y,-y)-f)==0
moments={}
for law,support,prob in [('symmetric',[1,-1],[s.Rational(1,2)]*2),('asymmetric',[s.sqrt(2),-1/s.sqrt(2)],[s.Rational(1,3),s.Rational(2,3)])]:
    ms=[s.simplify(sum(p*z**k for z,p in zip(support,prob))) for k in range(1,5)]
    assert ms[:2]==[0,1];moments[law]=[str(z) for z in ms]
# Operator-norm bound: absolute ridge coefficient times squared ridge norm.
hessian_perturbation=alpha*(4+2+2)
assert 1-hessian_perturbation==s.Rational(3,5) and 2+hessian_perturbation==s.Rational(12,5)
G=s.lambdify((x,y),grad,'numpy'); rng=np.random.default_rng(1073)
maxstate=maxctrl=maxbal=maxg=maxmean=0.; cases=0
for H in (1,4):
 for N in (5,11):
  for g in (1/512,1/2048):
   for law in (0,1):
    xx=rng.normal(scale=.04,size=(2,2));controls=rng.normal(scale=.06,size=(N,2));controls-=controls.mean(0)
    if law:controls+=np.array([.017,-.009])
    for t in range(8):
      eps=rng.choice([1.,-1.],size=(H,N,2)) if not law else np.where(rng.integers(0,3,(H,N,2))==0,np.sqrt(2),-1/np.sqrt(2))
      eps*=np.sqrt([1.25,.75])
      p=1-g*np.array([1.,2.]);weights=np.array([p**(H-1-h) for h in range(H)])
      B=-np.expm1(H*np.log1p(-g*np.array([1.,2.])));PH=p**H
      th=np.repeat(xx[:,None,:],N,axis=1);qb=np.zeros((2,2))
      for h in range(H):
        gg=np.array([[np.asarray(G(*th[a,c]),dtype=float).ravel() for c in range(N)] for a in range(2)])
        q=gg-th*np.array([1.,2.]);qb+=q.mean(1)*weights[h]
        th[0]-=g*(gg[0]+controls+eps[h]);th[1]-=g*(gg[1]+eps[h])
      xr=th.mean(1);cr=controls+(th[0]-xr[0])/(g*H);br=-g*qb/B
      xn,cn,bn,eta,res=explicit_round(xx.copy(),controls.copy(),g,eps,weights,B,PH,.05)
      maxstate=max(maxstate,float(abs(xn-xr).max())); maxctrl=max(maxctrl,float(abs(cn-cr).max()));maxbal=max(maxbal,float(abs(bn-br).max()))
      maxmean=max(maxmean,float(abs(cn.mean(0)-controls.mean(0)).max()))
      assert np.allclose(xn,xr,atol=3e-14,rtol=1e-12)
      assert np.allclose(cn,cr,atol=3e-12,rtol=1e-11)
      assert np.allclose(bn,br,atol=2e-14,rtol=1e-10)
      # Reflection of all second coordinates must commute with both updates.
      J=np.array([1.,-1.]);z2=explicit_round(xx*J,controls*J,g,eps*J,weights,B,PH,.05)
      assert np.allclose(z2[0],xn*J,atol=1e-15,rtol=0)
      assert np.allclose(z2[1],cn*J,atol=1e-15,rtol=0)
      xx,controls=xn,cn;cases+=1
out=dict(A=str(A),T_nonzero={f'{i+1}{j+1}{k+1}':str(T[i][j][k]) for i in range(2) for j in range(2) for k in range(2) if T[i][j][k]!=0},
         TC=str(contract(C)),B11=str(b11),H4_FedAvg=str(-s.Rational(3,4)*v),H4_difference=str(-s.Rational(7,16)*v),
         noise_moments=moments,global_hessian_bounds=['3/5','12/5'],short_round_comparisons=cases,max_state_error=maxstate,max_control_error=maxctrl,max_balance_error=maxbal,max_mean_control_drift=maxmean,
         reflection_identity='f(x1,-x2)=f(x1,x2); original updates commute with joint x2/control2/noise2 sign reflection. With symmetric diagonal noise and zero starts, ideal finite-time E[x2]=0. This is an additional algebraic interpretation, not a new empirical test.')
(OUT/'independent_model_kernel.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
