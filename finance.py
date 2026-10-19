"""Small no-payout binomial lattices. j counts DOWN moves; n never exceeds four."""
from dataclasses import dataclass
from math import exp, sqrt, log, erf, isfinite


@dataclass(frozen=True)
class Model:
    S: float = 100.
    n: int = 2
    T: float = 2.
    r: float = log(1.05)
    u: float = 1.2
    d: float = .8
    sigma: float = .3
    mode: str = 'manual'

    def terms(self):
        if type(self.n) is not int or not 1 <= self.n <= 4:
            raise ValueError('Choose one to four periods.')
        if not all(isfinite(x) for x in (self.S,self.T,self.r,self.u,self.d,self.sigma)):
            raise ValueError('Inputs must be finite numbers.')
        if self.S <= 0 or self.T <= 0 or not -.5 <= self.r <= 1:
            raise ValueError('Use positive value and time, and a rate between -50% and 100%.')
        dt=self.T/self.n
        if self.mode not in ('manual','crr'): raise ValueError('Unknown calibration.')
        if self.mode=='crr' and self.sigma<=0: raise ValueError('Volatility must be positive.')
        u=exp(self.sigma*sqrt(dt)) if self.mode=='crr' else self.u
        d=1/u if self.mode=='crr' else self.d
        R=exp(self.r*dt)
        if not 0<d<R<u: raise ValueError('No-arbitrage requires 0 < d < R < u. Change the rate, moves, or step length.')
        return dict(dt=dt,u=u,d=d,R=R,p=(R-d)/(u-d))


def lattice(m, costs):
    q=m.terms()
    if m.n not in costs: raise ValueError('Specify the final investment cost.')
    if any(type(i) is not int or i<0 or i>m.n or not isfinite(k) or k<0 for i,k in costs.items()):
        raise ValueError('Gate dates must lie on the grid and costs must be finite and nonnegative.')
    nodes={}
    for i in range(m.n,-1,-1):
        for j in range(i+1):
            S=m.S*q['u']**(i-j)*q['d']**j
            C=S if i==m.n else (q['p']*nodes[i+1,j]['F']+(1-q['p'])*nodes[i+1,j+1]['F'])/q['R']
            gate=i in costs;K=costs.get(i,0.);net=C-K;F=max(net,0.) if gate else C
            action=('Proceed' if net>1e-10 else 'Stop' if net < -1e-10 else 'Indifferent') if gate else 'Carry value'
            nodes[i,j]=dict(S=S,C=C,F=F,net=net,K=K,gate=gate,action=action)
    return q,nodes


def black_scholes(S,K,T,r,sigma):
    if K==0:return S
    N=lambda z:(1+erf(z/sqrt(2)))/2
    d1=(log(S/K)+(r+.5*sigma*sigma)*T)/(sigma*sqrt(T))
    return S*N(d1)-K*exp(-r*T)*N(d1-sigma*sqrt(T))


def commitment(m,costs):
    R=m.terms()['R']
    return m.S-sum(k/R**i for i,k in costs.items())


def european_lattice(m,K,kind='call'):
    """European exercise only at maturity; no interim investment gates."""
    if kind not in ('call','put') or not isfinite(K) or K<0:
        raise ValueError('Choose call or put and a finite nonnegative strike.')
    q=m.terms();nodes={}
    for i in range(m.n,-1,-1):
        for j in range(i+1):
            S=m.S*q['u']**(i-j)*q['d']**j
            value=max(0.,S-K if kind=='call' else K-S) if i==m.n else (q['p']*nodes[i+1,j]['F']+(1-q['p'])*nodes[i+1,j+1]['F'])/q['R']
            nodes[i,j]=dict(S=S,C=value,F=value,gate=False,action='Maturity payoff' if i==m.n else 'Carry value')
    return q,nodes
