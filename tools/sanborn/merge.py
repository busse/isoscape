"""Merge an edition's traced parts (a key map and its sheets) into one file: earlier parts win
where footprints overlap, and the coverage is the union."""
import json, sys
import numpy as np
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree
from geo import to_m, to_ll
edition, out, parts = int(sys.argv[1]), sys.argv[2], sys.argv[3:]
def pm(r):
    r = np.asarray(r); x, y = to_m(r[:, 0], r[:, 1]); return Polygon(np.stack([x, y], 1)).buffer(0)
keep, polys, cov = [], [], []
for p in parts:
    fc = json.load(open(p))
    tree = STRtree(polys) if polys else None
    for f in fc['features']:
        g = pm(f['geometry']['coordinates'][0])
        if f['properties'].get('coverage'):
            cov.append(g); continue
        if g.is_empty: continue
        if tree is not None and any(polys[i].contains(g.representative_point()) for i in tree.query(g)):
            continue
        f['properties']['edition'] = edition
        keep.append(f); polys.append(g)
for c in unary_union(cov).geoms if unary_union(cov).geom_type != 'Polygon' else [unary_union(cov)]:
    x, y = c.exterior.xy; lon, lat = to_ll(np.array(x), np.array(y))
    keep.append({'type': 'Feature', 'properties': {'edition': edition, 'coverage': True},
                 'geometry': {'type': 'Polygon', 'coordinates': [list(zip(lon.round(7).tolist(), lat.round(7).tolist()))]}})
json.dump({'type': 'FeatureCollection', 'edition': edition, 'features': keep}, open(out, 'w'))
print(out, sum(1 for f in keep if not f['properties'].get('coverage')), 'buildings')
