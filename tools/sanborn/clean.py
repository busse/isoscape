#!/usr/bin/env python3
"""Final pass over history/sanborn/lost.geojson before rendering.

1. Drop slivers: footprints whose minimum rotated rectangle is more than 8x longer than wide
   and under 12 m wide. On the Sanborn sheets these are rail viaducts, sheds along tracks and
   street edges the colour classifier took for buildings; extruded, they stand as walls.
2. Simplify outlines (Douglas-Peucker, 1.5 m) so pixel stair-steps do not draw as striped walls.

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
    if L / max(W, 0.1) > ASPECT and W < WIDTH:
        dropped.append({'id': f['properties'].get('id'), 'length': round(L), 'width': round(W, 1), 'edition': f['properties'].get('edition')})
        continue
    t = s.simplify(TOL, preserve_topology=True)
    if t.is_empty or t.area < 0.5 * s.area: t = s
    before += len(s.exterior.coords); after += len(t.exterior.coords)
    f['geometry'] = mapping(transform(to_deg, t))
    keep.append(f)
g['features'] = keep
json.dump(g, open(path, 'w'))
json.dump(dropped, open(path.replace('lost.geojson', 'clean-dropped.json'), 'w'), indent=1)
print(f'kept {len(keep)}, dropped {len(dropped)} slivers, outline points {before} -> {after}')
