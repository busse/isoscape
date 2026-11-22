import pandas as pd, numpy as np, glob, geopandas as gpd, json
W='/home/claude/ds/'
c=pd.concat([pd.read_csv(f) for f in glob.glob(W+'work_all/*/osm_check.csv')]); c=c[c.chain=='Dollar General'].dropna().drop_duplicates('osm')
m=c[c.nearest_snap_m<500]; print('OSM-SNAP DG pairs <500m n',len(m),'median',m.nearest_snap_m.median(),'q75',m.nearest_snap_m.quantile(.75),'q90',m.nearest_snap_m.quantile(.9),'>60m',(m.nearest_snap_m>60).mean().round(2))
p=pd.read_csv(W+'traffic/traffic_points.csv'); dg=p[(p.kind=='Dollar General')&p.is_town]
hp=gpd.read_file(W+'hpms/va2024.gpkg'); print(hp.columns.tolist()); print(hp.crs.to_epsg(), len(hp))
num=hp.route_number.fillna('').astype(str).str.strip(); print('route_number blank',(num=='').mean().round(3),'zero',(num.isin(['0','0.0'])).mean().round(3)); print(num.value_counts().head(5).to_dict())
for col in ['route_signing','route_qualifier','f_system']:
    if col in hp: print(col,hp[col].value_counts(dropna=False).head(8).to_dict())
tot=al=0; rows=[]
for t in dg.town:
    b=gpd.read_file(W+f'work_all/{t}/builtup.gpkg'); e=b[b.setting=='lead'].geometry.iloc[0].boundary
    cr=hp[hp.intersects(e)]
    along=cr.geometry.intersection(e.buffer(15)).length
    frac=(along/cr.length.clip(lower=1))
    # sections that run along the edge: >100 m within 15 m of it
    a=(along>100)
    # null spike
    nl=pd.read_csv(W+f'work_all/{t}/null.csv'); band=nl[(nl.A_lead>0.9)&(nl.A_lead<=1.1)]
    rows.append((t,len(cr),int(a.sum()),round(((nl.A_lead>0.99)&(nl.A_lead<=1.01)).sum()/max(len(band),1),2)))
    tot+=len(cr); al+=a.sum()
print(rows); print('crossing sections',tot,'running >100 m along the edge',al)
import zipfile
