"""After ../lifespans.py: give each lost Jackson Ward building back what the edition file records
(its id, color, name, use, stories read off the sheet), and leave out any whose center falls in a
footprint already drawn from the 1950-52 volume 1 sheets (history/sanborn/lost.geojson, edition
1950), so the two tracings do not draw one building twice.

    python3 finish.py <lifespans out> <edition file> <history/sanborn/lost.geojson> <out>"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from geo import to_m

def pm(r):
    r = np.asarray(r); x, y = to_m(r[:, 0], r[:, 1]); return Polygon(np.stack([x, y], 1)).buffer(0)

if sys.argv[1] == '--restore':
    pre, cleaned = sys.argv[2:4]
    g = json.load(open(cleaned)); have = {f['properties']['id'] for f in g['features']}
    back = [f for f in json.load(open(pre))['features'] if f['properties'].get('name') and f['properties']['id'] not in have]
    g['features'] += back; json.dump(g, open(cleaned, 'w'))
    print('restored', [f['properties']['name'] for f in back]); sys.exit()
lost, ed, old, out = sys.argv[1:5]
src = {json.dumps(f['geometry']['coordinates'][0][:3]): f['properties'] for f in json.load(open(ed))['features'] if not f['properties'].get('coverage')}
olds = [pm(f['geometry']['coordinates'][0]) for f in json.load(open(old))['features'] if f['properties'].get('edition') == 1950 or f['properties'].get('lastSeen') == 1950]
tree = STRtree(olds)
keep, dup = [], 0
for f in json.load(open(lost))['features']:
    p = src[json.dumps(f['geometry']['coordinates'][0][:3])]
    c = pm(f['geometry']['coordinates'][0]).representative_point()
    if any(olds[i].contains(c) for i in tree.query(c)):
        dup += 1; continue
    pr = f['properties']
    pr['id'] = p['id']
    for k in ('color', 'name', 'use', 'storeysFrom', 'byEye'):
        if k in p: pr[k] = p[k]
    pr['storeys'] = p['storeys']
    keep.append(f)
json.dump({'type': 'FeatureCollection', 'editions': [1952], 'features': keep}, open(out, 'w'))
print(len(keep), 'kept;', dup, 'left out as already drawn from the 1950-52 volume 1 sheets')

# python3 finish.py --restore <pre-clean file> <cleaned file>: buildings named on the sheet that
# ../clean.py --shapes dropped for a spiky outline (a chapel, a community center) are put back as
# traced: a named building is checked by eye, so its outline stands.
