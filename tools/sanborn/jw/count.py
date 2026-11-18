"""Count the buildings on the traced 1952 sheets inside the highway's footprint.

    python3 count.py <edition file> <footprint.geojson> [counted-ids.json]

With a third argument, the ids counted in each polygon are written there, innermost first and
without repeats (a building in the paved polygon is listed under "paved" only), for the count
picture's highlight (`ids` in the history switch), so the picture roofs exactly what is counted.

A building counts as inside when its center (a point inside its outline) falls in the polygon.
Outlines under 12 m2 (the region's minBuildingArea: sheds and privies the map does not draw) and
records marked notBuilding (a correction-table box) are not counted, so the count picture draws
every building counted (count_restore.py puts back the ones the cleaning dropped).
Counts are of outlines traced from the sheets, not of households, families or people."""
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
