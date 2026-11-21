import pandas as pd, numpy as np, json, glob, os
W='/home/claude/ds/'
p=pd.read_csv(W+'traffic/traffic_points.csv')
dg=p[p.kind=='Dollar General']; rn=p[p.kind=='random']
print('DG edge n',len(dg),'towns(places)',dg.town.nunique(),'is_town',dg.is_town.sum(), 'places among town stores', dg[dg.is_town].town.nunique())
print(dg[dg.is_town].town.value_counts().to_dict())
print('match rate store',dg.aadt.notna().mean(),'random',rn.aadt.notna().mean())
print('match_m store median',dg.match_m.median(),'random',rn.match_m.median(), rn.match_m.quantile(.9))
print('busiest_rank notna: store',dg.busiest_rank.notna().mean(),'random',rn.busiest_rank.notna().mean())
print('town-only: store',dg[dg.is_town].busiest_rank.notna().mean(),'random',rn[rn.is_town].busiest_rank.notna().mean())
print('crossing roads per place (DG places):'); print(dg.groupby('town').crossing_roads.first().describe())
print(dg[dg.is_town][['town','A_lead','road','busiest_rank','crossing_roads','aadt','match_m','near_junction','outside_limits','on_approach_road']].to_string())
# A distribution within band
print('A_lead in band: store q',dg.A_lead.quantile([.25,.5,.75]).tolist(),'random',rn.A_lead.quantile([.25,.5,.75]).tolist())
print('town stores A',dg[dg.is_town].A_lead.quantile([.25,.5,.75]).tolist(),'random town',rn[rn.is_town].A_lead.quantile([.25,.5,.75]).tolist())
# random outcomes by A bin (towns)
r=rn[rn.is_town].copy(); r['bin']=pd.cut(r.A_lead,[1,1.1,1.25,1.5,2])
r['top2']=r.busiest_rank<=2
print(r.groupby('bin')[['top2','near_junction','outside_limits','on_approach_road']].mean().round(3), r.groupby('bin').size())
r['aad']=r.aadt
print(r.groupby('bin').aadt.median())
# spike near 1
print('random share with A in (1,1.02]:',((rn.A_lead>1)&(rn.A_lead<=1.02)).mean())
# road ids
print(p.road.astype(str).str[:2].value_counts().head(8)); print((p.road=='R0').sum(), p.road.value_counts().head(8))
# Poisson-binomial style place-conditional expectation for town stores
for col,f in [('top2',lambda d:d.busiest_rank<=2),('junction',lambda d:d.near_junction.astype(bool)),('outside',lambda d:d.outside_limits.astype(bool))]:
    s=dg[dg.is_town]; x=f(s).values
    pi=np.array([f(rn[rn.town==t]).mean() for t in s.town])
    rng=np.random.default_rng(1); sim=(rng.random((100000,len(pi)))<pi).sum(1)
    print(col,'obs',x.sum(),'exp',pi.sum().round(2),'P(sim>=obs)',(sim>=x.sum()).mean(),'P(sim<=obs)',(sim<=x.sum()).mean())
    # cluster bootstrap by place of difference
    towns=s.town.unique(); d=[]
    for _ in range(5000):
        tt=rng.choice(towns,len(towns)); xs=np.concatenate([x[s.town.values==t] for t in tt]); ps=np.concatenate([pi[s.town.values==t] for t in tt])
        d.append(xs.mean()-ps.mean())
    print('  cluster boot diff 95%',np.percentile(d,[2.5,97.5]).round(3))
