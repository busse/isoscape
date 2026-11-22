import pandas as pd, numpy as np
d=pd.read_pickle('/tmp/chk/points.pkl')
d['inc']=(d.LSAD.astype(str)!='57')&(d.FUNCSTAT.astype(str)=='A')
B=d[(d.set.astype(str)=='B')]
B=B.assign(state=B.state.astype(str))
print('places by state with junction_m inf (no junction tree):')
g=B.groupby(['state','geoid'],observed=True).junction_m.min()
print(g.groupby('state').apply(lambda v: pd.Series({'places':len(v),'no_junction_in_window':np.isinf(v).sum(),'min>2km':(v>2000).sum()})).unstack())
r=B[~B.is_store & (B.edge_dist>30)]
for nm,q in [('all random A<=3',r),('band random',r[(r.A_lead>1)&(r.A_lead<=2)]),('in town random',r[r.A_lead<=1])]:
    print(nm); print(q.groupby('state').junction_m.apply(lambda v: pd.Series({'n':len(v),'<=250':(v<=250).mean(),'<=500':(v<=500).mean(),'median':np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else np.nan,'inf':np.isinf(v).mean()})).unstack().round(3))
prim=B[B.inc&(B['pop']<25000)&(~B.joined)]
rp=prim[~prim.is_store&(prim.edge_dist>30)]
print('primary band random'); q=rp[(rp.A_lead>1)&(rp.A_lead<=2)]
print(q.groupby('state').junction_m.apply(lambda v: pd.Series({'n':len(v),'<=250':(v<=250).mean(),'inf':np.isinf(v).mean()})).unstack().round(3))
print('primary in-town random'); q=rp[(rp.A_lead<=1)]
print(q.groupby('state').junction_m.apply(lambda v: pd.Series({'n':len(v),'<=250':(v<=250).mean()})).unstack().round(3))
s=prim[prim.is_store].sort_values('A_lead',kind='stable').drop_duplicates('id')
s=s[s.edge_dist>30]
for k in ['Dollar General','convenience','grocery']:
    q=s[s.kind.astype(str)==k]
    print(k,'stores in town <=250 by state'); print(pd.concat([q[q.A_lead<=1].groupby('state').junction_m.apply(lambda v:(v<=250).mean()).round(3).rename('town'),q[q.A_lead<=1].groupby('state').size().rename('n_town'),q[(q.A_lead>1)&(q.A_lead<=2)].groupby('state').junction_m.apply(lambda v:(v<=250).mean()).round(3).rename('edge'),q[(q.A_lead>1)&(q.A_lead<=2)].groupby('state').size().rename('n_edge')],axis=1))
e=pd.read_pickle('/tmp/chk/edge_dg.pkl'); w=e[e.state.astype(str)=='WV']
print(w[['id','name','geoid','A_lead','edge_dist','junction_m','aadt','road','rank','inside_limits','pop']].to_string())
