"""The highway's footprint in today's OSM: the motorway and motorway_link ways that the series
are the Turnpike (named Richmond-Petersburg Turnpike or carrying I 95) and the ramps beside it
(ramps running mostly beside I-64, built in the 1970s, are left out), between the Belvidere
Street ramps (cut along a line north-west of -77.4462, 37.5543) and the line of 8th Street, each buffered by half its paved width (lanes x 3.65 m, plus 3 m of
shoulder each side), the gaps between carriageways and in the loops closed (a 20 m closing), as
lon/lat GeoJSON. A second polygon adds 15 m each side for the cut slopes and walls."""
import json, math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import LineString, box, mapping, Polygon
from shapely.ops import unary_union
from geo import to_m, to_ll
d = json.load(open(os.environ.get('JW_OSM', os.path.join(os.path.dirname(__file__), 'osm-jw.json'))))
W, E, S, N = -77.4505, -77.4200, 37.5450, 37.5600
# which ways are the Turnpike (1958): main-line ways named Richmond-Petersburg Turnpike or
# carrying I 95; I-64 east of the interchange (built in the 1970s) is left out, and so is any ramp
# that runs mostly beside it. Today's ramps stand in for the 1958 ones: not the same.
def ml(o):
    g = np.array(o['g']); x, y = to_m(g[:, 0], g[:, 1]); return LineString(np.stack([x, y], 1))
mot = [o for o in d if o['tags'].get('highway') in ('motorway', 'motorway_link')]
tp = [o for o in mot if o['tags'].get('highway') == 'motorway' and ('Turnpike' in o['tags'].get('name', '') or 'I 95' in o['tags'].get('ref', ''))]
i64 = [o for o in mot if o['tags'].get('highway') == 'motorway' and o not in tp]
TP = unary_union([ml(o).buffer(25) for o in tp]); I64 = unary_union([ml(o).buffer(25) for o in i64])
parts = []; used = []; later = []
for o in mot:
    t = o['tags']; l = ml(o)
    if o in i64: later.append(o['id']); continue
    if o not in tp:
        if l.intersection(I64).length > 0.3 * l.length or not l.intersects(TP):
            later.append(o['id']); continue
    try: lanes = int(str(t.get('lanes', '1' if t['highway'].endswith('link') else '3')).split(';')[0])
    except ValueError: lanes = 1
    parts.append(l.buffer(lanes * 3.65 / 2 + 3.0, cap_style=2)); used.append(o['id'])
fp = unary_union(parts).buffer(10, join_style=2).buffer(-10, join_style=2)
x0, y0 = to_m(W, S); x1, y1 = to_m(E, N)
fp = fp.intersection(box(float(x0), float(y0), float(x1), float(y1)))
# west of the Belvidere ramps the road leaves Jackson Ward to the north-west: stop it there
xa, ya = to_m(-77.4462, 37.5543)
fp = fp.difference(box(float(x0) - 10, float(ya), float(xa), float(y1) + 10))
# east of 8th Street's line (8th & Leigh to 8th & Jackson in OSM, carried on north-east) the road
# leaves Jackson Ward for the Shockoe valley: stop it there
ax, ay = to_m(-77.4320997, 37.5441346); bx, by = to_m(-77.4311821, 37.5450919)
dx, dy = float(bx - ax), float(by - ay); n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
far = 3000
east = Polygon([(ax - dx * far, ay - dy * far), (ax + dx * far, ay + dy * far),
                (ax + dx * far + dy * far, ay + dy * far - dx * far), (ax - dx * far + dy * far, ay - dy * far - dx * far)])
fp = fp.difference(east)
wide = fp.buffer(15)
def ll(geom):
    geoms = [geom] if geom.geom_type == 'Polygon' else list(geom.geoms)
    cs = []
    for p in geoms:
        rs = []
        for r in [p.exterior] + list(p.interiors):
            lon, lat = to_ll(*np.array(r.xy)); rs.append([[round(float(a), 7), round(float(b), 7)] for a, b in zip(lon, lat)])
        cs.append(rs)
    return {'type': 'MultiPolygon', 'coordinates': cs}
fc = {'type': 'FeatureCollection', 'features': [
    {'type': 'Feature', 'properties': {'name': 'paved', 'area_m2': round(fp.area), 'note': __doc__}, 'geometry': ll(fp)},
    {'type': 'Feature', 'properties': {'name': 'corridor', 'area_m2': round(wide.area), 'note': 'paved + 15 m each side'}, 'geometry': ll(wide)}]}
json.dump(fc, open(sys.argv[1], 'w'))
print('paved m2', round(fp.area), 'corridor m2', round(wide.area), 'ways', len(used), 'left out as later or undated', len(later))
