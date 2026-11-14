#!/usr/bin/env python3
"""Final pass over history/sanborn/lost.geojson before rendering.

1. Drop slivers: footprints whose minimum rotated rectangle is more than 8x longer than wide
   and under 12 m wide, or over 100 m long and under 8 m wide on average (area / length,
   which catches bent strips whose bounding rectangle is wide). On the Sanborn sheets these are rail viaducts, sheds along tracks and
   street edges the colour classifier took for buildings; extruded, they stand as walls.
2. Drop sprawls: footprints over 2,000 m² that fill under 45% of their convex hull. These are
   river shading and hatching on the overview sheets, not buildings.
3. Merge duplicates: where two footprints overlap by more than 85% (intersection over union),
   keep the earlier one and extend its life to the later one's end, so a building traced in
   two editions is drawn once.
4. Simplify outlines (Douglas-Peucker, 1.5 m) so pixel stair-steps do not draw as striped walls.

Usage: clean.py history/sanborn/lost.geojson   (rewrites in place; dropped ids -> clean-dropped.json)
"""
import json, math, sys
from shapely.geometry import shape, mapping
from shapely.ops import transform

ASPECT, WIDTH, TOL = 8, 12, 1.5
path = sys.argv[1]
g = json.load(open(path))
lat = 37.54
kx, ky = 111320 * math.cos(math.radians(lat)), 110540
to_m = lambda x, y, z=None: (x * kx, y * ky)
to_deg = lambda x, y, z=None: (x / kx, y / ky)
keep, dropped, before, after = [], [], 0, 0
for f in g['features']:
    s = transform(to_m, shape(f['geometry']))
    c = list(s.minimum_rotated_rectangle.exterior.coords)
    a, b = math.dist(c[0], c[1]), math.dist(c[1], c[2])
    L, W = max(a, b), min(a, b)
    sprawl = s.area > 2000 and s.area / s.convex_hull.area < 0.45
    if sprawl or (L / max(W, 0.1) > ASPECT and W < WIDTH) or (L > 100 and s.area / L < 8):
        dropped.append({'id': f['properties'].get('id'), 'length': round(L), 'width': round(W, 1), 'edition': f['properties'].get('edition')})
        continue
    t = s.simplify(TOL, preserve_topology=True)
    if t.is_empty or t.area < 0.5 * s.area: t = s
    before += len(s.exterior.coords); after += len(t.exterior.coords)
    f['geometry'] = mapping(transform(to_deg, t))
    keep.append(f)
from shapely.strtree import STRtree
geo = [transform(to_m, shape(f['geometry'])) for f in keep]
keep.sort(key=lambda f: f['properties'].get('from') or 9999)
geo = [transform(to_m, shape(f['geometry'])) for f in keep]
tree, gone, merged = STRtree(geo), set(), 0
for i, a in enumerate(geo):
    if i in gone: continue
    for j in map(int, tree.query(a)):
        if j <= i or j in gone: continue
        inter = a.intersection(geo[j]).area
        if inter / (a.area + geo[j].area - inter) > 0.85:
            pi, pj = keep[i]['properties'], keep[j]['properties']
            if (pj.get('to') or 0) > (pi.get('to') or 0):
                for k in ('to', 'end', 'lastSeen'):
                    if k in pj: pi[k] = pj[k]
            gone.add(j); merged += 1
keep = [f for i, f in enumerate(keep) if i not in gone]
print(f'merged {merged} duplicate footprints')
g['features'] = keep
json.dump(g, open(path, 'w'))
json.dump(dropped, open(path.replace('lost.geojson', 'clean-dropped.json'), 'w'), indent=1)
print(f'kept {len(keep)}, dropped {len(dropped)} slivers, outline points {before} -> {after}')
