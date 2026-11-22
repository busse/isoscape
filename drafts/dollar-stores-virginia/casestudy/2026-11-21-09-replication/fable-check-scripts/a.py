import pandas as pd, numpy as np, math
d=pd.read_pickle('/tmp/chk/points.pkl')
disc=pd.read_csv('/home/claude/ds/pool_all/stores.csv')
used=set(disc.loc[disc.A_lead<=3,'id'])
d['inc']=(d.LSAD.astype(str)!='57')&(d.FUNCSTAT.astype(str)=='A')
st=d[d.is_store].sort_values('A_lead',kind='stable').drop_duplicates('id')
print('stores unique',len(st), 'ids null',st.id.isna().sum())
prim=lambda q:(q.set.astype(str)=='B')&q.inc&(q['pop']<25000)&(~q.joined)
def boot(df,col,n=10000,seed=1):
    g=df.groupby('geoid',observed=True)[col].agg(['sum','count'])
    rng=np.random.default_rng(seed);k=len(g)
    idx=rng.integers(0,k,(n,k))
    v=g['sum'].values[idx].sum(1)/g['count'].values[idx].sum(1)
    return df[col].mean(),*np.percentile(v,[2.5,97.5])
def wil(k,n,z=1.96):
    p=k/n;dd=1+z*z/n;c=(p+z*z/(2*n))/dd;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/dd;return c-h,c+h
nl=d[(~d.is_store)&prim(d)&(d.edge_dist>30)]
nb=nl[(nl.A_lead>1)&(nl.A_lead<=2)]
print('null band pts',len(nb),'places',nb.geoid.nunique())
for kind in ['Dollar General','convenience']:
    s=st[prim(st)&(st.kind.astype(str)==kind)&(st.edge_dist>30)&(~st.id.isin(used))]
    e=s[(s.A_lead>1)&(s.A_lead<=2)].copy()
    print(kind,'edge',len(e),'places',e.geoid.nunique())
    for nm,f in [('C1',lambda q:(q['rank']<=2)),('C2',lambda q:q.junction_m<=250),('C3',lambda q:q.inside_limits)]:
        p=f(nb).astype(float).groupby(nb.geoid,observed=True).mean()
        e['x']=f(e).astype(float); e['p']=e.geoid.astype(str).map(dict(zip(p.index.astype(str),p.values)))
        ee=e.dropna(subset=['p']); ee=ee.assign(dx=ee.x-ee.p)
        est,lo,hi=boot(ee,'dx'); k=int(ee.x.sum()); n=len(ee)
        print(nm,k,n,round(k/n,3),'wilson %.3f-%.3f'%wil(k,n),'exp',round(ee.p.sum(),1),round(ee.p.mean(),3),'D %.3f %.3f %.3f'%(est,lo,hi),'ratio',round(k/ee.p.sum(),2))
    n6=nb[nb.aadt>0]; m=np.log(n6.aadt).groupby(n6.geoid,observed=True).mean()
    e6=e[e.aadt>0].copy(); e6['p']=e6.geoid.astype(str).map(dict(zip(m.index.astype(str),m.values))); e6=e6.dropna(subset=['p']); e6['dl']=np.log(e6.aadt)-e6.p
    est,lo,hi=boot(e6,'dl'); print('C6',len(e6),e6.geoid.nunique(),'%.3f %.3f %.3f x%.2f'%(est,lo,hi,math.exp(est)))
    if kind=='Dollar General':
        for col in ['A_lead','A_loose']:
            s3=s[s[col]<=3].copy(); n3=nl[nl[col]<=3]
            p=((n3[col]>1)&(n3[col]<=2)).astype(float).groupby(n3.geoid,observed=True).mean()
            s3['x']=((s3[col]>1)&(s3[col]<=2)).astype(float); s3['p']=s3.geoid.astype(str).map(dict(zip(p.index.astype(str),p.values)))
            s3=s3.dropna(subset=['p']); s3['dx']=s3.x-s3.p
            est,lo,hi=boot(s3,'dx'); print('C5',col,int(s3.x.sum()),len(s3),round(s3.x.mean(),3),'exp',round(s3.p.sum(),1),round(s3.p.mean(),3),'D %.3f %.3f %.3f'%(est,lo,hi))
        # C4
        t=s[s.A_lead<=1]; a=e.dropna(subset=['auth_year']); b=t.dropna(subset=['auth_year'])
        print('C4 edge',len(a),(a.auth_year>2005).mean(),'town',len(b),(b.auth_year>2005).mean(), 'auth missing edge',e.auth_year.isna().sum())
        print('in town',len(t),'beyond2', (s.A_lead>2).sum(), 'margin', ((st[prim(st)&(st.kind.astype(str)=="Dollar General")].edge_dist<=30)).sum())
        print(e.groupby(e.state.astype(str)).apply(lambda q: pd.Series({'n':len(q),'c1':(q['rank']<=2).mean(),'c2':(q.junction_m<=250).mean(),'in':q.inside_limits.mean(),'matched':q.aadt.notna().mean(),'ranked':q['rank'].notna().mean()})))
        e.to_pickle('/tmp/chk/edge_dg.pkl')
        # discovery-excluded stores count
        s_all=st[prim(st)&(st.kind.astype(str)==kind)&(st.edge_dist>30)]
        print('excluded as discovery-used',(s_all.id.isin(used)).sum(), 'in band', (s_all.id.isin(used)&(s_all.A_lead>1)&(s_all.A_lead<=2)).sum())
