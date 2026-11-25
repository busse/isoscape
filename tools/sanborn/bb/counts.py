"""Count the traced buildings on each corner's half-block (Broad to the alley), per edition, and
today's buildings there. Half-blocks are drawn on the 1924 sheets in sheet pixels (50% scans)."""
import json, sys
import numpy as np
from shapely.geometry import Polygon, Point
sys.path.insert(0, '..')
from geo import to_m, i2w, to_ll
HALF = {  # sheet, corner, pixel box (u0, v0, u1, v1) on the 1924 50% scan
    'NW': ('33', (2540, 720, 2934, 1196)), 'SW': ('33', (1930, 1504, 2774, 1940)),
    'NE': ('34', (344, 700, 1180, 1144)), 'SE': ('34', (244, 1500, 1152, 1930))}
geo = json.load(open('geo1924.json'))
areas = {}
for k, (sh, (u0, v0, u1, v1)) in HALF.items():
    xy = i2w(geo[sh]['params'], np.array([[u0, v0], [u1, v0], [u1, v1], [u0, v1]], float))
    areas[k] = Polygon(xy)
def cnt(fc, pick=None):
    out = {k: 0 for k in areas}
    for f in fc:
        r = np.asarray(f['ring']); x, y = to_m(r[:, 0], r[:, 1]); c = Polygon(np.stack([x, y], 1)).buffer(0).representative_point()
        for k, a in areas.items():
            if a.contains(c) and (pick is None or pick(f)): out[k] += 1
    return out
res = {}
for ed in ('1924', '1952'):
    fc = [dict(ring=f['geometry']['coordinates'][0], **f['properties']) for f in json.load(open(f'bb-{ed}.geojson'))['features'] if not f['properties'].get('coverage')]
    res[ed] = cnt(fc)
today = json.load(open(sys.argv[1]))
res['today'] = cnt(today)
res['today_built_by_1952'] = cnt(today, lambda f: f['year'] is not None and f['year'] <= 1952)
res['half_blocks_lonlat'] = {k: [list(map(float, to_ll(*p))) for p in a.exterior.coords] for k, a in areas.items()}
res['area_m2'] = {k: round(a.area) for k, a in areas.items()}
json.dump(res, open('counts.json', 'w'), indent=1)
for k in ('1924', '1952', 'today', 'today_built_by_1952', 'area_m2'): print(k, res[k])
