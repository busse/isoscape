import pandas as pd, numpy as np, geopandas as gpd
W='/home/claude/ds/'
p=pd.read_csv(W+'traffic/traffic_points.csv'); dg=p[(p.kind=='Dollar General')&p.is_town&(p.busiest_rank<=2)]
hp=gpd.read_file(W+'hpms/va2024.gpkg')
num=hp.route_number.fillna('').astype(str).str.strip(); name=hp.routename.fillna('').astype(str).str.strip().str.upper()
hp['road']=np.where(num!='','R'+num,np.where(name!='','N'+name,'S'+hp.index.astype(str)))
k=0
for _,s in dg.iterrows():
    b=gpd.read_file(W+f'work_all/{s.town}/builtup.gpkg'); e=b[b.setting=='lead'].geometry.iloc[0].boundary
    cr=hp[hp.intersects(e)].copy()
    cr['along']=cr.geometry.intersection(e.buffer(15)).length
    true=cr[cr.along<=100]
    rank=true.groupby('road').aadt.max().sort_values(ascending=False); order={r:i+1 for i,r in enumerate(rank.index)}
    print(s.town,s.road,'rank',s.busiest_rank,'of',s.crossing_roads,'| true-crossing rank',order.get(s.road),'of',len(order),'| signings on road',sorted(cr[cr.road==s.road].route_signing.unique()))
    k+= order.get(s.road,99)<=2
print('still top two after dropping edge-following sections:',k,'of',len(dg))
pl=gpd.read_file('zip:///mnt/user-data/uploads/ISO-TEST/isoscape-work/dollar-stores/raw/tl_2024_51_place.zip')
pl['slug']=pl.NAME.str.lower().str.replace(' ','-'); d=pl[pl.slug.duplicated(keep=False)]
inc=pl[pl.LSAD.isin(['43','25'])]
print('name slugs shared by 2+ VA places:',d.slug.nunique(),'; of those involving an incorporated place:',d[d.slug.isin(inc.slug)].slug.nunique(), sorted(d[d.slug.isin(inc.slug)].slug.unique())[:12])
