#!/usr/bin/env python3
"""Final pass over history/sanborn/lost.geojson before rendering.

1. Drop slivers: footprints whose minimum rotated rectangle is more than 8x longer than wide
   and under 12 m wide, or over 100 m long and under 8 m wide on average (area / length,
   which catches bent strips whose bounding rectangle is wide). On the Sanborn sheets these are rail viaducts, sheds along tracks and
   street edges the color classifier took for buildings; extruded, they stand as walls.
2. Drop sprawls: footprints over 2,000 m² that fill under 45% of their convex hull. These are
   river shading and hatching on the overview sheets, not buildings.
3. Merge duplicates: where two footprints overlap by more than 85% (intersection over union),
   keep the earlier one and extend its life to the later one's end, so a building traced in
   two editions is drawn once.
4. Simplify outlines (Douglas-Peucker, 1.5 m) so pixel stair-steps do not draw as striped walls.

Usage: clean.py history/sanborn/lost.geojson   (rewrites in place; dropped ids -> clean-dropped.json)

`--shapes` runs only the shape pass, over every footprint (it ran over the cleaned file in
November 2026, the second time with the small-star rule added; a run after that trims a few
outlines again, by a little, and drops nothing more):

5. Drop strips: footprints filling under 30% of their minimum rotated rectangle and over 60 m
   long (a bent ribbon), or under 4 m wide at their widest (the diameter of the largest circle
   inside) and at least four times as long: a hatched bank, a track's edge or a viaduct, not a
   building.
6. Drop sawtooth strips: footprints at least 80 m long whose outline is over 1.35 times the
   length of their convex hull's and that fill under 70% of it: a hatched edge the classifier
   read tooth by tooth. The same outline on a footprint under 1,000 m² is a star of spikes
   around a small shed: dropped too.
7. Trim spikes: an opening of 1.5 m (shrink, then grow back, square corners) removes spikes and
   slivers under 3 m wide; the largest piece left, simplified at 1.5 m, replaces the outline,
   or, when under 60% of the area is left, the footprint is dropped.

Usage: clean.py --shapes history/sanborn/lost.geojson   (dropped and trimmed ids are added to
clean-shapes.json, with those of earlier runs)
"""
import json, math, sys
if sys.argv[1] == '--shapes':
    from shapely.geometry import shape, mapping
    from shapely import transform, maximum_inscribed_circle
    path = sys.argv[2]
    g = json.load(open(path))
    kx, ky = 111320 * math.cos(math.radians(37.54)), 110540
    keep, report = [], {'strip': [], 'sawtooth': [], 'spikes': [], 'trimmed': []}
    for f in g['features']:
        s = transform(shape(f['geometry']), lambda c: c * [kx, ky])
        c = list(s.minimum_rotated_rectangle.exterior.coords)
        a, b = math.dist(c[0], c[1]), math.dist(c[1], c[2])
        L = max(a, b)
        D = 2 * maximum_inscribed_circle(s, 0.2).length
        hull = s.convex_hull
        fid = f['properties'].get('id')
        if (s.area / (a * b) < 0.3 and L > 60) or (D < 4 and L >= 4 * D):
            report['strip'].append(fid); continue
        if (L >= 80 or s.area < 1000) and s.length / hull.length > 1.35 and s.area / hull.area < 0.7:
            report['sawtooth'].append(fid); continue
        o = s.buffer(-1.5, join_style=2).buffer(1.5, join_style=2)
        pieces = [] if o.is_empty else list(getattr(o, 'geoms', [o]))
        big = max(pieces, key=lambda x: x.area) if pieces else None
        kept = big.area / s.area if big is not None else 0
        if kept < 0.6:
            report['spikes'].append(fid); continue
        if kept < 0.98:
            t = big.simplify(1.5, preserve_topology=True)
            f['geometry'] = mapping(transform(t, lambda c: c / [kx, ky]))
            report['trimmed'].append(fid)
        keep.append(f)
    g['features'] = keep
    json.dump(g, open(path, 'w'))
    out = path.replace('lost.geojson', 'clean-shapes.json')
    try:
        earlier = json.load(open(out))
    except FileNotFoundError:
        earlier = {}
    report = {k: earlier.get(k, []) + [i for i in v if i not in earlier.get(k, [])] for k, v in report.items()}
    json.dump(report, open(out, 'w'), indent=1)
    print({k: len(v) for k, v in report.items()}, 'kept', len(keep))
    sys.exit(0)
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
