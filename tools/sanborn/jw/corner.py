"""corner.py "A" "B": OSM center-line crossings of the streets whose names contain A and B
(case-insensitive), points within 25 m merged; the control points' ground positions. Reads the
streets cut out of the streetcars cache by osmcut.py (osm-jw.json)."""
# corner.py "A" "B" [lon lat]: OSM centerline intersections of streets whose names contain A and B
# (case-insensitive); with --extend, lines are extended 60 m at their ends (for streets cut by the highway).
import json, sys, math
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
import os
OSM = os.environ.get('JW_OSM', os.path.join(os.path.dirname(__file__), 'osm-jw.json'))
d = json.load(open(OSM))
KX = 111320*math.cos(math.radians(37.55)); KY = 110574; L0, B0 = -77.44, 37.55
m = lambda p: ((p[0]-L0)*KX, (p[1]-B0)*KY)
ll = lambda q: (q[0]/KX+L0, q[1]/KY+B0)
STREET = {'primary','secondary','tertiary','residential','unclassified','living_street','service','trunk','pedestrian'}
def lines(name):
    out = []
    for o in d:
        t = o['tags']; n = (t.get('name') or '').lower()
        if t.get('highway') in STREET and name.lower() in n and len(o['g']) > 1:
            out.append(LineString([m(p) for p in o['g']]))
    return out
def extend(l, e=60):
    c = list(l.coords); a, b = c[0], c[1]; y, z = c[-2], c[-1]
    def ext(p, q):
        dx, dy = p[0]-q[0], p[1]-q[1]; n = math.hypot(dx, dy) or 1; return (p[0]+dx/n*e, p[1]+dy/n*e)
    return LineString([ext(a, b)] + c + [ext(z, y)])
def corners(a, b, ext=False):
    A = unary_union([extend(x) if ext else x for x in lines(a)]); B = unary_union([extend(x) if ext else x for x in lines(b)])
    i = A.intersection(B)
    pts = [i] if i.geom_type == 'Point' else [g for g in getattr(i, 'geoms', []) if g.geom_type == 'Point']
    # merge points closer than 25 m (divided streets)
    groups = []
    for p in pts:
        for g in groups:
            if g[0].distance(p) < 25: g.append(p); break
        else: groups.append([p])
    return [ll((sum(p.x for p in g)/len(g), sum(p.y for p in g)/len(g))) for g in groups]
if __name__ == '__main__':
    ext = '--extend' in sys.argv; args = [a for a in sys.argv[1:] if a != '--extend']
    for c in corners(args[0], args[1], ext): print(f'{c[0]:.7f} {c[1]:.7f}')
