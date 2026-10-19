"""CRR exercise and access-gate model for the interactive construction page."""
from math import exp
from finance import Model

def build(S,K,T,n,r,sigma,yield_q=0.,kind='Call',style='European',gates=None):
    # Calibrate pricing weights with the carry rate, discount with r.
    m=Model(S=S,T=T,n=n,r=r-yield_q,sigma=sigma,mode='crr')
    terms=m.terms();terms['R']=exp(r*terms['dt'])
    gates=gates or {};nodes={}
    for i in range(n,-1,-1):
        for j in range(i+1):
            s=S*terms['u']**(i-j)*terms['d']**j
            intrinsic=max(0.,s-K if kind=='Call' else K-s)
            variables={'S':s,'K':K}
            payoff='max(0,S-K)' if kind=='Call' else 'max(0,K-S)'
            if i==n:
                value=intrinsic;expr=payoff;action='Exercise' if value>0 else 'Expire';continuation=None
            else:
                up=nodes[i+1,j]['value'];down=nodes[i+1,j+1]['value']
                continuation=(terms['p']*up+(1-terms['p'])*down)/terms['R']
                G=gates.get(i,0.);net=continuation-G
                variables.update(p=terms['p'],R=terms['R'],Vu=up,Vd=down)
                expr='(p*Vu+(1-p)*Vd)/R'
                if i in gates: variables['G']=G;expr=f'max(0,{expr}-G)'
                value=max(0.,net) if i in gates else continuation
                action=('Continue' if net>0 else 'Abandon') if i in gates else 'Hold'
                if style=='American':
                    expr=f'max({payoff},{expr})'
                    if intrinsic>value+1e-10: value=intrinsic;action='Exercise'
            nodes[i,j]=dict(S=s,value=value,expr=expr,vars=variables,action=action,continuation=continuation,net=None if i==n else continuation-gates.get(i,0.))
    return terms,nodes

def ready(node,answers,n):
    i,j=node
    return i==n or all(f'{i+1},{k}' in answers for k in (j,j+1))
