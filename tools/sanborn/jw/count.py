"""Count the buildings on the traced 1952 sheets inside the highway's footprint.

    python3 count.py <edition file> <footprint.geojson> [named.csv]

A building counts as inside when its center (a point inside its outline) falls in the polygon.
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
fs = [f for f in json.load(open(ed))['features'] if not f['properties'].get('coverage')]
out = {}
for name, P in [('all traced', None)] + list(polys.items()):
    sel = []
    for f in fs:
        g = transform(tm, shape(f['geometry'])).buffer(0)
        if P is None or P.contains(g.representative_point()): sel.append(f)
    pr = [f['properties'] for f in sel]
    kind = Counter(('colored ' + p['material']) if p['color'] == 'colored' else 'uncolored outline (frame, by inference)' for p in pr)
    big = sum(1 for p in pr if p['area'] >= 30)
    out[name] = dict(buildings=len(sel), at_least_30m2=big, by_kind=dict(kind.most_common()),
                     named=sorted({p['name'] for p in pr if p.get('name')}), named_uses=dict(Counter(p['use'] for p in pr if p.get('use'))),
                     sheets=dict(sorted(Counter(p['sheet'] for p in pr).items())))
print(json.dumps(out, indent=1))
