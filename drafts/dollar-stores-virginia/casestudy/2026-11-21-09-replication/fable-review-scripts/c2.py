import pandas as pd, numpy as np, glob, math
W='/home/claude/ds/'
p=pd.read_csv(W+'traffic/traffic_points.csv'); t=pd.read_csv(W+'pool_all/towns.csv'); st=pd.read_csv(W+'pool_all/stores.csv')
pop=dict(zip(t.town,t.people_2020)); p['pop']=p.town.map(pop); p['small']=p['pop']<25000
dg=p[p.kind=='Dollar General']; rn=p[p.kind=='random']
def wil(k,n,z=1.96):
    ph=k/n; d=1+z*z/n; c=(ph+z*z/(2*n))/d; h=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/d; return round(c-h,2),round(c+h,2)
print(pd.crosstab(dg.is_town,dg.small))
print('pop of city edge-store places', dg[~dg.is_town].groupby('town')['pop'].first().sort_values().to_dict())
for lab,s,r in [('small<25k',dg[dg.small],rn[rn.small]),('big',dg[~dg.small],rn[~rn.small]),('<10k',dg[dg['pop']<10000],rn[rn['pop']<10000]),('<5k',dg[dg['pop']<5000],rn[rn['pop']<5000])]:
    n=len(s)
    for nm,f in [('top2',lambda d:d.busiest_rank<=2),('junc',lambda d:d.near_junction.astype(bool)),('outside',lambda d:d.outside_limits.astype(bool))]:
        k=int(f(s).sum()); print(lab,nm,k,n,round(k/n,2),wil(k,n),'random',round(f(r).mean(),3))
    print(lab,'median aadt',s.aadt.median(),'random',r.aadt.median())
# A-bin-matched expectation for legal-town stores
bins=[1,1.1,1.25,1.5,2]
s=dg[dg.is_town].copy(); r=rn[rn.is_town].copy()
s['bin']=pd.cut(s.A_lead,bins); r['bin']=pd.cut(r.A_lead,bins)
print(s.bin.value_counts().sort_index().to_dict())
for nm,f in [('top2',lambda d:d.busiest_rank<=2),('junc',lambda d:d.near_junction.astype(bool)),('outside',lambda d:d.outside_limits.astype(bool))]:
    rate=f(r).groupby(r.bin).mean(); print(nm,'A-matched random share',round(s.bin.map(rate).astype(float).mean(),3),'unmatched',round(f(r).mean(),3),'stores',round(f(s).mean(),3))
r2=r.copy(); print('A-matched random median aadt approx by bin', r.groupby('bin').aadt.median().to_dict())
# distance beyond edge in meters for edge DG
e=st[(st.kind=='Dollar General')&(~st.metro)&(st.A_lead>1)&(st.A_lead<=2)]
beyond=(e.dist_m-e.edge_lead_m)
print('edge DG metres beyond edge: quantiles',beyond.quantile([0,.1,.25,.5,.75]).tolist(),' <100m:',(beyond<100).sum(),' <200m:',(beyond<200).sum(),'of',len(e))
it=st[(st.kind=='Dollar General')&(~st.metro)&(st.A_lead<=1)]
ins=(it.edge_lead_m-it.dist_m); print('in-town DG within 100 m inside edge:',(ins<100).sum(),' within 200:',(ins<200).sum(),'of',len(it))
# impervious-only in-town
d=st[(st.kind=='Dollar General')&(~st.metro)]
print('DG in town by lead but beyond loose edge (in town only via impervious):',((d.A_lead<=1)&(d.A_loose>1)).sum(),' of which loose-band 1-2:',((d.A_lead<=1)&(d.A_loose>1)&(d.A_loose<=2)).sum())
print('DG fringe share under loose edge:',((d.A_loose>1)&(d.A_loose<=2)).sum(),'of',(d.A_loose<=3).sum())
# geocode check
c=pd.concat([pd.read_csv(f) for f in glob.glob(W+'work_all/*/osm_check.csv')]); c=c[c.chain=='Dollar General'].dropna()
print('OSM DG vs nearest SNAP DG, n',len(c),'median',c.nearest_snap_m.median(),'q75',c.nearest_snap_m.quantile(.75),'q90',c.nearest_snap_m.quantile(.9),'share>60m',(c.nearest_snap_m>60).mean().round(2),'>100',(c.nearest_snap_m>100).mean().round(2),'>250',(c.nearest_snap_m>250).mean().round(2))
# name collisions
import geopandas as gpd
pl=gpd.read_file('zip:///home/claude/ds/'+'x') if False else None
