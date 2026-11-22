"""Count the buildings on the traced 1952 sheets inside the highway's footprint.

    python3 count.py <edition file> <footprint.geojson> [counted-ids.json]

With a third argument, the ids counted in each polygon are written there, innermost first and
without repeats (a building in the paved polygon is listed under "paved" only), for the count
picture's highlight (`ids` in the history switch), so the picture roofs exactly what is counted.

A building counts as inside when its center (a point inside its outline) falls in the polygon.
Outlines under 12 m2 (the region's minBuildingArea: sheds and privies the map does not draw) and
records marked notBuilding (a correction-table box) are not counted, so the count picture draws
every building counted (count_restore.py puts back the ones the cleaning dropped).
Counts are of outlines traced from the sheets, not of households, families or people.

The output's `sensitivity` block gives the same count by other rules (centroid, half or more of
the outline inside, any overlap) and with each polygon's edge moved 5 m in and out, and the share
of each polygon that lies beyond the traced sheets; the story states them as ranges."""
import json, sys, os, csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import Polygon, shape
from shapely.ops import transform
from collections import Counter
from geo import to_m
ed, fp = sys.argv[1], sys.argv[2]
tm = lambda x, y, z=None: to_m(x, y)
polys = {f['properties']['name']: transform(tm, shape(f['geometry'])) for f in json.load(open(fp))['features']}
fs = [f for f in json.load(open(ed))['features'] if not f['properties'].get('coverage') and not f['properties'].get('notBuilding')]
out = {}
for name, P in [('all traced', None)] + list(polys.items()):
    sel = []
    for f in fs:
        g = transform(tm, shape(f['geometry'])).buffer(0)
        if g.area < 12: continue
        if P is None or P.contains(g.representative_point()): sel.append(f)
    pr = [f['properties'] for f in sel]
    kind = Counter(('colored ' + p['material']) if p['color'] == 'colored' else 'uncolored outline (frame, by inference)' for p in pr)
    big = sum(1 for p in pr if p['area'] >= 30)
    out[name] = dict(buildings=len(sel), at_least_30m2=big, by_kind=dict(kind.most_common()),
                     named=sorted({p['name'] for p in pr if p.get('name')}), named_uses=dict(Counter(p['use'] for p in pr if p.get('use'))),
                     uses_read=dict(Counter(p['use'] for p in pr if p.get('printed')).most_common()), stories_read=sum(1 for p in pr if p.get('storeysFrom') == 'sheet'),
                     sheets=dict(sorted(Counter(p['sheet'] for p in pr).items())))
# How much the rule and the polygon's edge matter (the published counts stay the rule above):
# the same outlines counted by their centroid, by half or more of their area inside, by any
# overlap at all, and with each polygon's edge moved 5 m in and 5 m out; and how much of each
# polygon lies beyond the traced 1952 sheets (the edition file's coverage outline), where no
# building can be counted.
cov = [transform(tm, shape(f['geometry'])).buffer(0) for f in json.load(open(ed))['features'] if f['properties'].get('coverage')]
from shapely.ops import unary_union
cov = unary_union(cov)
geoms = [g for g in (transform(tm, shape(f['geometry'])).buffer(0) for f in fs) if g.area >= 12]
sens = {}
for name, P in polys.items():
    r = dict(published=sum(1 for g in geoms if P.contains(g.representative_point())),
             centroid=sum(1 for g in geoms if P.contains(g.centroid)),
             half_or_more=sum(1 for g in geoms if g.intersection(P).area >= 0.5 * g.area),
             any_overlap=sum(1 for g in geoms if g.intersection(P).area > 0),
             edge_in_5m=sum(1 for g in geoms if P.buffer(-5).contains(g.representative_point())),
             edge_out_5m=sum(1 for g in geoms if P.buffer(5).contains(g.representative_point())))
    off = P.difference(cov)
    r['area_m2'] = round(P.area)
    r['beyond_traced_m2'] = round(off.area)
    r['beyond_traced_share'] = round(off.area / P.area, 3)
    c = off.centroid
    from geo import to_ll
    r['beyond_traced_center_lonlat'] = [round(float(v), 5) for v in to_ll(c.x, c.y)]
    sens[name] = r
out['sensitivity'] = sens
print(json.dumps(out, indent=1))
if len(sys.argv) > 3:
    lists, seen = {}, set()
    for name, P in polys.items():
        ids = []
        for f in fs:
            g = transform(tm, shape(f['geometry'])).buffer(0)
            if g.area >= 12 and P.contains(g.representative_point()) and f['properties']['id'] not in seen:
                ids.append(f['properties']['id']); seen.add(f['properties']['id'])
        lists[name] = ids
    json.dump(lists, open(sys.argv[3], 'w'), indent=0)
