"""The highway's footprint in today's OSM: motorway and motorway_link ways between Belvidere
Street and 7th/8th Street, each buffered by half its paved width (lanes x 3.65 m, plus 3 m of
shoulder each side), the gaps between carriageways and in the loops closed (a 20 m closing), as
lon/lat GeoJSON. A second polygon adds 15 m each side for the cut slopes and walls."""
import json, math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import LineString, box, mapping, Polygon
from shapely.ops import unary_union
from geo import to_m, to_ll
d = json.load(open(os.environ.get('JW_OSM', os.path.join(os.path.dirname(__file__), 'osm-jw.json'))))
W, E, S, N = -77.4505, -77.4295, 37.5450, 37.5575
parts = []; used = []
for o in d:
    t = o['tags']
    if t.get('highway') not in ('motorway', 'motorway_link'): continue
    g = np.array(o['g'])
    x, y = to_m(g[:, 0], g[:, 1])
    l = LineString(np.stack([x, y], 1))
    try: lanes = int(str(t.get('lanes', '1' if t['highway'].endswith('link') else '3')).split(';')[0])
    except ValueError: lanes = 1
    parts.append(l.buffer(lanes * 3.65 / 2 + 3.0, cap_style=2)); used.append(o['id'])
fp = unary_union(parts).buffer(10, join_style=2).buffer(-10, join_style=2)
x0, y0 = to_m(W, S); x1, y1 = to_m(E, N)
fp = fp.intersection(box(float(x0), float(y0), float(x1), float(y1)))
# west of the Belvidere ramps the road leaves Jackson Ward to the north-west: stop it there
xa, ya = to_m(-77.4462, 37.5543)
fp = fp.difference(box(float(x0) - 10, float(ya), float(xa), float(y1) + 10))
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
print('paved m2', round(fp.area), 'corridor m2', round(wide.area), 'ways', len(used))
