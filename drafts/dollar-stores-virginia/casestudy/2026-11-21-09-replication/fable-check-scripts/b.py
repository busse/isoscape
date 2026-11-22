import pandas as pd, numpy as np
parts=[]
for ch in pd.read_csv('/home/claude/ds/conf_all/points.csv.gz',chunksize=400000,low_memory=False,dtype={'geoid':str,'LSAD':str}):
    parts.append(ch[ch.is_store])
s=pd.concat(parts,ignore_index=True); s.to_pickle('/tmp/chk/stores_full.pkl')
print(len(s), s.id.nunique())
s['inc']=(s.LSAD!='57')&(s.FUNCSTAT=='A')
s['unit']=np.where(s.joined,'joined',np.where(~s.inc,'CDP',np.where(s['pop']<25000,'small','large')))
# ties in lowest A across places
g=s.groupby('id')
mn=g.A_lead.transform('min')
tie=s[s.A_lead==mn]
tc=tie.groupby('id').agg(n=('geoid','nunique'),units=('unit',lambda v:'|'.join(sorted(set(v)))),sets=('set',lambda v:'|'.join(sorted(set(v)))),kind=('kind','first'),A=('A_lead','first'))
t2=tc[tc.n>1]
print('stores tied at lowest A across places',len(t2)); print(t2.groupby(['kind']).size()); print(t2[(t2.units.str.contains(r'\|'))|(t2.sets.str.contains(r'\|'))].groupby(['units','sets']).size())
print(t2[(t2.kind=='Dollar General')&(t2.A>1)&(t2.A<=2)])
# their dedupe
a=s.sort_values('A_lead').drop_duplicates('id'); b=s.sort_values('A_lead',kind='stable').drop_duplicates('id')
f=lambda q:q[(q.set=='B')&(q.unit=='small')&(q.kind=='Dollar General')&(q.edge_dist>30)&(q.A_lead>1)&(q.A_lead<=2)]
A,B=f(a),f(b); print(len(A),len(B)); 
print(A[~A.id.isin(B.id)][['id','name','A_lead','geoid','NAME','state','edge_dist']]); print(B[~B.id.isin(A.id)][['id','A_lead','geoid','NAME']])
x=s[s.id.isin(A[~A.id.isin(B.id)].id)][['id','A_lead','A_loose','geoid','NAME','unit','set','edge_dist','pop','joined']]; print(x.sort_values(['id','A_lead']).to_string())
# near-boundary A
print('A_lead decimals check', (np.abs(s.A_lead*100-np.round(s.A_lead*100))>1e-6).sum())
# M7 proxy: set B/A-assigned stores that also appear in any discovery folder
dids=set(s[s.set=='discovery'].id)
for nm,q in [('their',a)]:
    hb=q[(q.set!='discovery')&q.id.isin(dids)]
    print('held-out-assigned stores that appear in a discovery window',len(hb)); print(hb.groupby(['set','state','unit','kind']).size().to_string())
    hh=hb[(hb.kind=='Dollar General')]; print(hh[['id','name','A_lead','NAME','state','set','unit','edge_dist']].to_string())
