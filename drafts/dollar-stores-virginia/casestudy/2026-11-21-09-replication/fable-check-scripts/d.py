import pandas as pd, numpy as np, math
d=pd.read_pickle('/tmp/chk/points.pkl')
for c in ['set','state','kind','geoid','road','LSAD','FUNCSTAT']: d[c]=d[c].astype(str)
d['inc']=(d.LSAD!='57')&(d.FUNCSTAT=='A')
P=d[(d.set=='B')&d.inc&(d['pop']<25000)&(~d.joined)]
def boot(df,col,n=10000,seed=5):
    g=df.groupby('geoid')[col].agg(['sum','count']);rng=np.random.default_rng(seed);k=len(g);idx=rng.integers(0,k,(n,k))
    v=g['sum'].values[idx].sum(1)/g['count'].values[idx].sum(1);return round(df[col].mean(),3),*np.percentile(v,[2.5,97.5]).round(3)
nl=P[(~P.is_store)&(P.edge_dist>30)]; nb=nl[(nl.A_lead>1)&(nl.A_lead<=2)]
print('random band matched to HPMS',nb.aadt.notna().mean().round(3),'ranked',nb['rank'].notna().mean().round(3),'top2',(nb['rank']<=2).mean().round(3))
allst=d[d.is_store].sort_values('A_lead',kind='stable').drop_duplicates('id')
s=allst[(allst.set=='B')&allst.inc&(allst['pop']<25000)&(~allst.joined)&(allst.edge_dist>30)]
e=s[(s.kind=='Dollar General')&(s.A_lead>1)&(s.A_lead<=2)]
print('DG edge matched',e.aadt.notna().mean().round(3),'ranked',e['rank'].notna().mean().round(3))
# C1 among matched only
pm=nb[nb.aadt.notna()]; p=(pm['rank']<=2).groupby(pm.geoid).mean(); em=e[e.aadt.notna()].copy(); em['p']=em.geoid.map(p); em=em.dropna(subset=['p']); em['dx']=(em['rank']<=2)-em.p
print('C1 matched-only',len(em),int((em['rank']<=2).sum()),round(em.p.sum(),1),boot(em,'dx'))
# crossing roads count
cr=P.groupby('geoid').crossing_roads.first(); print('crossing roads per primary place: n places',len(cr),'total',cr.sum(),cr.describe().round(1).to_dict()); 
ec=e.geoid.map(cr); print('edge DG in places with <=2 crossing roads',(ec<=2).sum(),'0 crossing',(ec==0).sum())
# ratio CI for C2
p2=(nb.junction_m<=250).groupby(nb.geoid).mean(); e2=e.assign(p=e.geoid.map(p2),x=(e.junction_m<=250).astype(float)).dropna(subset=['p'])
g=e2.groupby('geoid')[['x','p']].sum();rng=np.random.default_rng(1);idx=rng.integers(0,len(g),(10000,len(g)));rat=g.x.values[idx].sum(1)/g.p.values[idx].sum(1);print('C2 ratio',e2.x.sum()/e2.p.sum(),np.percentile(rat,[2.5,97.5]))
p1=(nb['rank']<=2).groupby(nb.geoid).mean(); e1=e.assign(p=e.geoid.map(p1),x=(e['rank']<=2).astype(float)).dropna(subset=['p']); g=e1.groupby('geoid')[['x','p']].sum(); rat=g.x.values[idx].sum(1)/g.p.values[idx].sum(1);print('C1 ratio',e1.x.sum()/e1.p.sum(),np.percentile(rat,[2.5,97.5]))
# symmetric (non-deduped) sensitivity: every store row in primary places, like the null
sr=P[P.is_store&(P.edge_dist>30)&(P.kind=='Dollar General')]
eb=sr[(sr.A_lead>1)&(sr.A_lead<=2)]
print('non-deduped DG band rows',len(eb),'unique',eb.id.nunique())
for nm,f in [('C1',lambda q:(q['rank']<=2)),('C2',lambda q:q.junction_m<=250),('C3',lambda q:q.inside_limits)]:
    p=f(nb).astype(float).groupby(nb.geoid).mean(); t=eb.assign(x=f(eb).astype(float),p=eb.geoid.map(p)).dropna(subset=['p']); t['dx']=t.x-t.p
    print(' sym',nm,int(t.x.sum()),len(t),round(t.p.sum(),1),boot(t,'dx'))
s3=sr[sr.A_lead<=3]; n3=nl[nl.A_lead<=3]; p=((n3.A_lead>1)&(n3.A_lead<=2)).astype(float).groupby(n3.geoid).mean()
t=s3.assign(x=((s3.A_lead>1)&(s3.A_lead<=2)).astype(float),p=s3.geoid.map(p)).dropna(subset=['p']); t['dx']=t.x-t.p
print(' sym C5 lead',int(t.x.sum()),len(t),round(t.x.mean(),3),round(t.p.mean(),3),boot(t,'dx'))
# isolated places only: stores scored in exactly one place window with A<=3
# DG vs convenience difference C1
ec_=s[(s.kind=='convenience')&(s.A_lead>1)&(s.A_lead<=2)]
a=e.assign(k=1,x=(e['rank']<=2).astype(float),p=e.geoid.map(p1)); b=ec_.assign(k=0,x=(ec_['rank']<=2).astype(float),p=ec_.geoid.map(p1))
both=pd.concat([a,b]).dropna(subset=['p']); both['dx']=both.x-both.p
places=both.geoid.unique();rng=np.random.default_rng(2);gs=both.groupby(['geoid','k']).dx.agg(['sum','count']).unstack(fill_value=0)
S1,C1,S0,C0=gs[('sum',1)].values,gs[('count',1)].values,gs[('sum',0)].values,gs[('count',0)].values
idx=rng.integers(0,len(gs),(10000,len(gs)));v=S1[idx].sum(1)/C1[idx].sum(1)-S0[idx].sum(1)/C0[idx].sum(1)
print('C1 DG minus convenience D',S1.sum()/C1.sum()-S0.sum()/C0.sum(),np.percentile(v,[2.5,97.5]))
# drive-in recompute
g=allst[(allst.A_lead>0.75)&(allst.A_lead<=2)&allst['rank'].notna()]
gp=g[(g.set=='B')&g.inc&(g['pop']<25000)&(~g.joined)]
first=gp.sort_values('A_lead',ascending=False,kind='stable').groupby(['geoid','road']).head(1)
print('drive-in roads with a store',len(first),'first DG',(first.kind=='Dollar General').mean().round(3),'DG share',(gp.kind=='Dollar General').mean().round(3),'any DG',gp.groupby(['geoid','road']).kind.apply(lambda v:(v=='Dollar General').any()).mean().round(3),'first conv',(first.kind=='convenience').mean().round(3), 'conv share',(gp.kind=='convenience').mean().round(3))
anyd=gp.groupby(['geoid','road']).kind.apply(lambda v:(v=='Dollar General').any())
print('roads with any DG',anyd.sum(),'first DG',(first.kind=='Dollar General').sum(),'places',gp.geoid.nunique(),'total crossing roads in all primary places',cr.sum(),'in places w/ gateway store',cr[cr.index.isin(gp.geoid)].sum())
print('share of all crossing roads: any DG',anyd.sum()/cr.sum(),'first DG',(first.kind=='Dollar General').sum()/cr.sum())
n_per=gp.groupby(['geoid','road']).size(); print('stores per road stretch',n_per.describe().round(2).to_dict(),'single-store roads',(n_per==1).mean().round(3))
# first store outside the edge only (A>1) and how often the "first" is inside the edge
print('first store has A<=1 (inside edge):',(first.A_lead<=1).mean().round(3), 'first DG among those outside', (first[first.A_lead>1].kind=='Dollar General').mean().round(3), len(first[first.A_lead>1]))
g1=gp[gp.A_lead>1]; f1=g1.sort_values('A_lead',ascending=False).groupby(['geoid','road']).head(1)
print('band-only: roads',len(f1),'first DG',(f1.kind=='Dollar General').mean().round(3),'DG share',(g1.kind=='Dollar General').mean().round(3))
# place-cluster CI for first-is-DG minus share
first=first.assign(x=(first.kind=='Dollar General').astype(float)); print('first DG CI',boot(first,'x'))
# total DG classes
sd=allst[(allst.set=='B')&allst.inc&(allst['pop']<25000)&(~allst.joined)&(allst.kind=='Dollar General')]
print('DG classes: margin',(sd.edge_dist<=30).sum(),'town',((sd.edge_dist>30)&(sd.A_lead<=1)).sum(),'band',((sd.edge_dist>30)&(sd.A_lead>1)&(sd.A_lead<=2)).sum(),'beyond',((sd.edge_dist>30)&(sd.A_lead>2)).sum(),'total',len(sd))
