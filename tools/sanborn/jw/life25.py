"""Lifespans for the Jackson Ward buildings traced from the 1925 printing of volume 3
(history/sanborn/jackson-ward-1925.geojson), written as a lost-buildings file the history loads
beside the 1952 one (history/sanborn/jackson-ward-1925-lost.geojson).

Each traced 1925 building is, in this order:
  1. left out if a point inside it falls in a building of the earlier downtown tracing
     (history/sanborn/lost.geojson) that stands in 1925 (from <= 1925 < to): that tracing already
     draws it. The exception is the downtown tracing's buildings from volume 1's small-scale key
     map (sheet "cbd") whose center falls inside these sheets' coverage: they are coarse and often
     misplaced here (one of them, a six-story block, covers the Leigh Street Memorial church and
     its neighbors), so they are listed (written to <out>.leaveout.json) for the history's
     sanborn.leaveOut, left out before 1952, and these sheets draw those blocks instead;
  2. left out if today's buildings cover half or more of it and one of them is dated 1925 or
     earlier: the scene draws today's building there;
  3. otherwise drawn from 1925 until the first of
       - 1952, if the 1952 tracing (history/sanborn/jackson-ward-1952.geojson) has a building
         covering half of it or holding a point inside it: from 1952 on that tracing draws it
         (why "continues": the same building, drawn from the 1952 sheet);
       - 1952, if the 1952 sheets map the spot without it (why "map": gone by 1952, when within
         1925-52 not known; on the Gilpin Court blocks the clearance of 1941 is given instead,
         why "cleared", see below);
       - the year built of a building standing on half or more of it today, if earlier.
Apostle Town: a building gone by 1952 whose center falls in the 1952 Gilpin Court site
(the hull of the buildings the 1952 sheets name as the U.S.H.A. project, grown by 20 m) ends in
1941, the year its clearance began (Library of Virginia; see history/jackson-ward.json).

    python3 life25.py <1925 edition> <1952 edition> <history/sanborn/lost.geojson> <today.json> <out>"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import Polygon, MultiPoint
from shapely.strtree import STRtree
from geo import to_m

Y = 1925
NEXT = 1952
GILPIN = 1941


def pm(ring):
    r = np.asarray(ring); x, y = to_m(r[:, 0], r[:, 1]); return Polygon(np.stack([x, y], 1)).buffer(0)


def main(ed25, ed52, older, today, out):
    ed25f = json.load(open(ed25))['features']
    from shapely.ops import unary_union
    cov25 = unary_union([pm(f['geometry']['coordinates'][0]) for f in ed25f if f['properties'].get('coverage')])
    olds, coarse = [], []
    for f in json.load(open(older))['features']:
        pr = f['properties']
        if not (pr['from'] <= Y < pr['to']): continue
        q = pm(f['geometry']['coordinates'][0])
        if pr.get('sheet') == 'cbd' and cov25.contains(q.representative_point()):
            coarse.append(pr['id']); continue
        olds.append(q)
    json.dump(coarse, open(out + '.leaveout.json', 'w'))
    otree = STRtree(olds)
    f52 = [f for f in json.load(open(ed52))['features'] if not f['properties'].get('coverage')]
    p52 = [pm(f['geometry']['coordinates'][0]) for f in f52]
    t52 = STRtree(p52)
    cov52 = [pm(f['geometry']['coordinates'][0]) for f in json.load(open(ed52))['features'] if f['properties'].get('coverage')]
    gil = [p52[i].centroid for i, f in enumerate(f52) if 'U.S.H.A' in (f['properties'].get('name') or '') or 'Gilpin' in (f['properties'].get('name') or '')]
    gsite = MultiPoint(gil).convex_hull.buffer(20) if gil else None
    tb = [b for b in json.load(open(today)) if len(b['ring']) >= 3]
    tp = [pm(b['ring']) for b in tb]
    k = [i for i, p in enumerate(tp) if not p.is_empty]; tb = [tb[i] for i in k]; tp = [tp[i] for i in k]
    ttree = STRtree(tp)
    feats, n = [], {'downtown': 0, 'today': 0, 'continues': 0, 'map': 0, 'cleared': 0, 'rebuilt': 0, 'unmapped52': 0}
    for f in ed25f:
        pr = f['properties']
        if pr.get('coverage'): continue
        p = pm(f['geometry']['coordinates'][0])
        if p.is_empty or p.area < 4: continue
        c = p.representative_point()
        if any(olds[i].contains(c) for i in otree.query(c)):
            n['downtown'] += 1; continue
        on = [j for j in ttree.query(p) if tp[j].intersection(p).area > 0.05 * p.area]
        cover = sum(tp[j].intersection(p).area for j in on) / p.area
        years = [tb[j]['year'] for j in on]
        if cover >= 0.5 and any(y is not None and y <= Y for y in years):
            n['today'] += 1; continue
        same = [i for i in t52.query(p) if p52[i].contains(c) or p52[i].intersection(p).area >= 0.5 * p.area]
        if same:
            to, end = NEXT, 'continues'
        elif any(q.contains(c) for q in cov52):
            if gsite is not None and gsite.contains(c):
                to, end = GILPIN, 'cleared'
            else:
                to, end = NEXT, 'map'
        else:
            to, end = NEXT, 'unmapped52'  # outside what the 1952 sheets traced: taken to stand until then
        rebuilt = [y for y in years if y is not None and Y < y < to] if cover >= 0.5 else []
        if rebuilt:
            to, end = min(rebuilt), 'rebuilt'
        n[end] += 1
        # the renderer knows four ends (map, rebuilt, highway, assumed); the finer reason is kept in why
        props = {'id': pr['id'], 'from': Y, 'lastSeen': Y, 'to': to, 'why': end,
                 'end': {'continues': 'map', 'map': 'map', 'cleared': 'rebuilt', 'rebuilt': 'rebuilt', 'unmapped52': 'assumed'}[end], 'material': pr['material'],
                 'storeys': pr['storeys'], 'storeysFrom': pr.get('storeysFrom', 'assumed'), 'sheet': pr['sheet'],
                 'edition': Y, 'color': pr['color']}
        for key in ('name', 'use', 'byEye'):
            if key in pr: props[key] = pr[key]
        feats.append({'type': 'Feature', 'properties': props, 'geometry': f['geometry']})
    json.dump({'type': 'FeatureCollection', 'editions': [Y], 'features': feats}, open(out, 'w'))
    print(len(feats), 'drawn in 1925;', n, len(coarse), 'coarse downtown buildings to leave out before 1952')


if __name__ == '__main__':
    main(*sys.argv[1:])
