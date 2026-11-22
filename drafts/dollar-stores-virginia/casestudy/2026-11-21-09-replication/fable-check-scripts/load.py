import pandas as pd, numpy as np
cols=['is_store','id','name','kind','auth_year','x','y','A_lead','A_loose','edge_dist','inside_limits','junction_m','aadt','road','rank','rank_100','rank_side','crossing_roads','reentries','geoid','state','set','pop','joined','gap_fallback','LSAD','FUNCSTAT','match_m']
parts=[]
for ch in pd.read_csv('/home/claude/ds/conf_all/points.csv.gz',usecols=cols,chunksize=400000,low_memory=False,dtype={'geoid':str,'LSAD':str,'road':str,'name':str}):
    for c in ['x','y','A_lead','A_loose','edge_dist','junction_m','aadt','rank','rank_100','rank_side','auth_year']:
        ch[c]=ch[c].astype('float32') if c not in('x','y') else ch[c]
    for c in ['kind','state','set','LSAD','FUNCSTAT','geoid','road']:
        ch[c]=ch[c].astype('category')
    ch.loc[~ch.is_store.astype(bool),'name']=None
    parts.append(ch)
d=pd.concat(parts,ignore_index=True)
for c in ['kind','state','set','LSAD','FUNCSTAT','geoid','road']:
    d[c]=d[c].astype(str).astype('category')
d.to_pickle('/tmp/chk/points.pkl')
print(d.shape); print(d.dtypes)
for c in ['is_store','kind','state','set','LSAD','FUNCSTAT','joined','gap_fallback']: print(d[c].value_counts(dropna=False).head(12))
print(d.geoid.nunique())
