import geopandas as gpd, pandas as pd, numpy as np, re, sys, collections, os, warnings
warnings.filterwarnings('ignore')
from scipy.spatial import cKDTree
sys.path.insert(0,'/home/claude/isoscape/tools/stories/dollar-stores')
MAINJ={"trunk","primary","secondary","tertiary","trunk_link","primary_link","tertiary_link","secondary_link","motorway","motorway_link"}
def car(token,state):
    m=re.match(r"^\s*([A-Za-z]+)[\s\-]*(\d+)",token)
    if not m: return False
    pre,num=m.group(1).upper(),int(m.group(2))
    if pre in("I","US"): return True
    if pre=="SR": return state=="TN"
    if pre=="KY": return num<1000
    return pre in {"VA","NC","TN","KY","WV","MD","SC","GA","AL","MS","OH","IN","IL","MO","AR","PA","DE","DC","NJ"}
def jpts(roads,state,rule=car):
    refs,deg={}, collections.Counter()
    for hw,ref,geom in zip(roads.highway,roads.ref.fillna(''),roads.geometry):
        if hw not in MAINJ: continue
        toks=frozenset(t.strip().upper() for t in str(ref).split(';') if t.strip() and rule(t,state))
        for g in getattr(geom,'geoms',[geom]):
            cs=[(round(x,1),round(y,1)) for x,y in g.coords]
            for k,c in enumerate(cs):
                deg[c]+=1 if k in(0,len(cs)-1) else 2
                if toks: refs.setdefault(c,set()).add(toks)
    return np.array([c for c,s in refs.items() if len(s)>=2 and len(set().union(*s))>=2 and deg[c]>=3])
st=sys.argv[1]; fips={'WV':'54','KY':'21','NC':'37','TN':'47','SC':'45','MD':'24'}[st]
e=pd.read_pickle('/tmp/chk/edge_dg.pkl'); full=pd.read_pickle('/tmp/chk/stores_full.pkl'); e=e.drop(columns=['x','y']).merge(full[['id','geoid','x','y']].assign(geoid=lambda q:q.geoid.astype(str)),on=['id','geoid'].copy() if False else None, left_on=[e.id,e.geoid.astype(str)], right_on=['id','geoid'], suffixes=('','_f')) if False else e
full=pd.read_pickle('/tmp/chk/stores_full.pkl'); full['geoid']=full.geoid.astype(str); e=e.drop(columns=['x','y']); e['geoid']=e.geoid.astype(str); e=e.merge(full[['id','geoid','x','y']],on=['id','geoid']); w=e[e.state.astype(str)==st]
pref=collections.Counter(); hwref=collections.Counter(); tot=0
res=[]
for geoid,q in w.groupby(w.geoid.astype(str)):
    f=f'/home/claude/ds/work_s{fips}/{geoid}/roads.gpkg'
    r=gpd.read_file(f)
    for hw,ref in zip(r.highway,r.ref.fillna('')):
        if hw in MAINJ:
            tot+=1
            for t in str(ref).split(';'):
                m=re.match(r"^\s*([A-Za-z]+)",t); pref[(m.group(1).upper() if m else ('<none>' if not t.strip() else 'num:'+t.strip()[:6]))]+=1
    J=jpts(r,st)
    J2=jpts(r,st,rule=lambda t,s: bool(re.match(r"^\s*([A-Za-z]+)[\s\-]*(\d+)",t)))  # any lettered ref incl CR
    for _,s in q.iterrows():
        d1=cKDTree(J).query([s.x,s.y])[0] if len(J) else np.inf
        d2=cKDTree(J2).query([s.x,s.y])[0] if len(J2) else np.inf
        res.append((geoid,int(s.id),float(s.junction_m),float(d1),float(d2),len(J),len(J2)))
print(st,'ways',tot,pref.most_common(25))
print(pd.DataFrame(res,columns=['geoid','id','stored','recomputed','anyref_rule','nJ','nJ_any']).round(0).to_string())
