import geopandas as gpd, pandas as pd, numpy as np, re, collections, warnings, math
warnings.filterwarnings('ignore')
from scipy.spatial import cKDTree
exec(open('/tmp/chk/wv.py').read().split("st=sys.argv[1]")[0])
F={'WV':'54','KY':'21','NC':'37','TN':'47','SC':'45','MD':'24'}
def jstrict(roads,state):
    refs,deg,nref={}, collections.Counter(), collections.Counter()
    for hw,ref,geom in zip(roads.highway,roads.ref.fillna(''),roads.geometry):
        if hw not in MAINJ: continue
        toks=frozenset(t.strip().upper() for t in str(ref).split(';') if t.strip() and car(t,state))
        for g in getattr(geom,'geoms',[geom]):
            cs=[(round(x,1),round(y,1)) for x,y in g.coords]
            for k,c in enumerate(cs):
                deg[c]+=1 if k in(0,len(cs)-1) else 2
                if toks: refs.setdefault(c,set()).add(toks)
    out=[]
    for c,s in refs.items():
        if deg[c]<3 or len(s)<2: continue
        s=list(s)
        if any(not(a<=b) and not(b<=a) for i,a in enumerate(s) for b in s[i+1:]): out.append(c)
    return np.array(out)
d=pd.read_pickle('/tmp/chk/points.pkl')
e=pd.read_pickle('/tmp/chk/edge_dg.pkl'); full=pd.read_pickle('/tmp/chk/stores_full.pkl'); full['geoid']=full.geoid.astype(str)
e=e.drop(columns=['x','y']); e['geoid']=e.geoid.astype(str); e=e.merge(full[['id','geoid','x','y']],on=['id','geoid'])
gs=set(e.geoid)
r=d[(~d.is_store)&d.geoid.isin(gs)&(d.edge_dist>30)&(d.A_lead>1)&(d.A_lead<=2)].copy(); r['geoid']=r.geoid.astype(str)
pref=collections.defaultdict(collections.Counter)
rows=[];mis=0
for geoid,q in e.groupby('geoid'):
    st=str(q.state.iloc[0]); roads=gpd.read_file(f'/home/claude/ds/work_s{F[st]}/{geoid}/roads.gpkg')
    for hw,ref in zip(roads.highway,roads.ref.fillna('')):
        if hw in MAINJ:
            for t in str(ref).split(';'):
                m=re.match(r"^\s*([A-Za-z]+)",t); pref[st][(m.group(1).upper() if m else ('<none>' if not t.strip() else 'num'))]+=1
    J=jpts(roads,st); S=jstrict(roads,st); rn=r[r.geoid==geoid]
    f=lambda T,X: (cKDTree(T).query(X)[0] if len(T) else np.full(len(X),np.inf))
    ds=f(J,q[['x','y']].values); dss=f(S,q[['x','y']].values)
    mis+=int((np.abs(np.where(np.isinf(ds),1e9,ds)-np.where(np.isinf(q.junction_m),1e9,q.junction_m))>2).sum())
    pn=(f(J,rn[['x','y']].values)<=250).mean(); pns=(f(S,rn[['x','y']].values)<=250).mean(); pst=(rn.junction_m<=250).mean()
    for a,b in zip(ds,dss): rows.append((geoid,st,a<=250,b<=250,pn,pns,pst))
t=pd.DataFrame(rows,columns=['geoid','st','x','xs','p','ps','pstored'])
print('store junction_m mismatches vs stored (>2 m):',mis,'of',len(t))
print('orig rule: obs',t.x.sum(),'exp',t.p.sum().round(1),'| stored exp',t.pstored.sum().round(1),'| strict: obs',t['xs'].sum(),'exp',t.ps.sum().round(1))
def boot(df,col,n=10000):
    g=df.groupby('geoid')[col].agg(['sum','count']);rng=np.random.default_rng(3);k=len(g);idx=rng.integers(0,k,(n,k))
    v=g['sum'].values[idx].sum(1)/g['count'].values[idx].sum(1);return df[col].mean(),*np.percentile(v,[2.5,97.5])
t['d']=t.x-t.p; t['dsx']=t['xs'].astype(float)-t.ps
print('D orig',boot(t,'d'),'D strict',boot(t,'dsx'))
print(t.groupby('st').agg(n=('x','size'),x=('x','sum'),xs=('xs','sum'),p=('p','sum'),ps=('ps','sum')).round(1))
for s,c in pref.items(): print(s,c.most_common(14))
