"""Simplify the drawn 1925 Jackson Ward outlines (history/sanborn/jackson-ward-1925-lost.geojson),
as ../clean.py simplified the 1952 ones, but within a tighter limit and with nothing dropped or
merged.

trace25.py keeps the pixel stair-steps of the colored fills (1.2 px Douglas-Peucker on a half-size
scan, about 0.3 m): a median of 14 corners a building against 4 in the cleaned 1952 layer. Each
corner is an edge and a dot in the view, so the 1925 blocks read as hatching. Here each outline is:

  1. simplified (Douglas-Peucker, topology kept) at TOL m, or, if the result strays more than MOVE m
     from the traced outline either way (Hausdorff), at 0.75, 0.5 or 0.3 m, the first that does not:
     no wall moves more than MOVE;
  2. squared where the sheet plainly shows a rectilinear building: every edge is within ANGLE
     degrees of the outline's main axis or its normal. Edges are turned onto the axes about their
     middles, corners re-found where neighbors meet, and runs of edges on one line joined. The
     squared outline is kept only if it lies within MOVE m of the original outline both ways
     (Hausdorff) and its area is within 5%; otherwise the step-1 outline stands;
  3. cleared of points on a straight line (under 0.05 m off it).

A result that comes out empty, invalid or under half the area keeps the original outline. The
1925 edition file (history/sanborn/jackson-ward-1925.geojson) keeps the outlines as traced, as the
1952 edition file does.

    python3 simplify25.py <lost.geojson> [TOL=1.0] [MOVE=1.0]   (rewrites in place; prints counts)"""
import json, math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import Polygon
from geo import to_m, to_ll

ANGLE = 12


def drop_collinear(pts, eps=0.05):
    pts = list(pts)
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = np.array(pts[i - 1]), np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
            ac = c - a; L = np.hypot(*ac)
            d = abs(ac[0] * (b - a)[1] - ac[1] * (b - a)[0]) / L if L > 1e-9 else np.hypot(*(b - a))
            if d < eps:
                del pts[i]; changed = True; break
    return pts


def square(pts):
    """Turn every edge onto the main axes; None if any edge is off by more than ANGLE."""
    P = np.array(pts); n = len(P)
    E = np.roll(P, -1, 0) - P
    Ls = np.hypot(E[:, 0], E[:, 1])
    ang = np.arctan2(E[:, 1], E[:, 0]) % (math.pi / 2)
    # main axis: length-weighted mean of edge angles mod 90 degrees
    th = math.atan2((Ls * np.sin(4 * ang)).sum(), (Ls * np.cos(4 * ang)).sum()) / 4
    u, v = np.array([math.cos(th), math.sin(th)]), np.array([-math.sin(th), math.cos(th)])
    lines = []  # (direction, offset): an edge on the line {p : p . normal = offset}
    for i in range(n):
        if Ls[i] < 1e-9: continue
        e = E[i] / Ls[i]
        if abs(e @ u) >= abs(e @ v):
            off = abs(math.degrees(math.acos(min(1, abs(e @ u)))))
            d, nrm = 'u', v
        else:
            off = abs(math.degrees(math.acos(min(1, abs(e @ v)))))
            d, nrm = 'v', u
        if off > ANGLE: return None
        mid = (P[i] + P[(i + 1) % n]) / 2
        lines.append((d, float(mid @ nrm)))
    # join runs on one axis into one line (length-weighted would be finer; the mean is enough here)
    merged = []
    for d, o in lines:
        if merged and merged[-1][0] == d:
            merged[-1] = (d, merged[-1][1] + [o])
        else:
            merged.append((d, [o]))
    if len(merged) > 1 and merged[0][0] == merged[-1][0]:
        merged[0] = (merged[0][0], merged[-1][1] + merged[0][1]); merged.pop()
    if len(merged) < 4 or len(merged) % 2: return None
    out = []
    for k in range(len(merged)):
        (d1, o1), (d2, o2) = merged[k - 1], merged[k]
        a, b = float(np.mean(o1)), float(np.mean(o2))
        # the corner where line k-1 meets line k: one is along u (offset on v), the other along v
        if d1 == 'u': out.append(b * u + a * v)
        else: out.append(a * u + b * v)
    return [tuple(p) for p in out]


TRIES = (1.0, 0.75, 0.5, 0.3)


def hd(a, b):
    return max(a.exterior.hausdorff_distance(b.exterior), b.exterior.hausdorff_distance(a.exterior))


def outline(s, tol, move):
    """Step 1 and 2 at one tolerance: (points, 1 if squared) or (None, 0)."""
    t = s.simplify(tol, preserve_topology=True)
    if t.geom_type != 'Polygon' or t.is_empty or not t.is_valid or t.area < 0.5 * s.area:
        return None, 0
    best = drop_collinear(list(t.exterior.coords)[:-1])
    if len(best) < 3: return None, 0
    q = square(best) if len(best) >= 4 else None
    if q is not None:
        qp = Polygon(q)
        if qp.is_valid and abs(qp.area - s.area) <= 0.05 * s.area and hd(qp, s) <= move:
            return drop_collinear(q), 1
    return best, 0


def ring_m(coords):
    r = np.asarray(coords)[:-1]; x, y = to_m(r[:, 0], r[:, 1]); return Polygon(np.stack([x, y], 1))


def main(path, tol=1.0, move=1.0):
    tol, move = float(tol), float(move)
    g = json.load(open(path))
    before = after = squared = kept_orig = 0; worst = 0.0; worst_id = None
    for f in g['features']:
        cs = f['geometry']['coordinates']
        s = ring_m(cs[0]); before += len(cs[0]) - 1
        if not s.is_valid: s = s.buffer(0)
        ccw = Polygon(np.asarray(cs[0])[:-1]).exterior.is_ccw
        best = None
        for tt in [x for x in TRIES if x <= tol]:
            cand, sq = outline(s, tt, move)
            if cand is not None and hd(Polygon(cand), s) <= move:
                best = cand; squared += sq; break
        if best is None or len(best) < 3:
            kept_orig += 1; after += len(cs[0]) - 1; continue
        bp = Polygon(best)
        if bp.exterior.is_ccw != ccw: best = best[::-1]; bp = Polygon(best)
        h = hd(bp, s)
        if h > worst: worst, worst_id = h, f['properties'].get('id')
        B = np.array(best); lon, lat = to_ll(B[:, 0], B[:, 1])
        ring = [[round(float(a), 7), round(float(b), 7)] for a, b in zip(lon, lat)]
        f['geometry']['coordinates'] = [ring + [ring[0]]]
        after += len(best)
    json.dump(g, open(path, 'w'))
    n = len(g['features'])
    print(f'{n} outlines; corners {before} -> {after} (mean {before / n:.1f} -> {after / n:.1f}); '
          f'squared {squared}; left as traced {kept_orig}; largest move {worst:.2f} m ({worst_id})')


if __name__ == '__main__':
    main(*sys.argv[1:])
