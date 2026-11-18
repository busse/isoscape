"""Place the names read off the 1925 sheets (names1925.py: where each label was read, on the
1925 half-size scan or on the warped frame) and write named1925.csv: sheet, a point inside the
building (lon, lat; u50, v50 in the warped frame, which geo1952.json places), the name or use as
printed, stories where printed, a note, and whether the point falls inside a traced outline.

    python3 place25.py"""
import sys, os, json, csv
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(0, os.path.join(here, '..'))
import numpy as np
from shapely.geometry import Polygon, Point
from reg25map import h2w
from geo import i2w, to_ll
from names1925 import R, H, W, Q, Q305

g = json.load(open(os.path.join(here, 'geo1952.json')))
rows = []
def add(sh, hx, hy, wx, wy, name, use, st, note):
    if wx is None: wx, wy = h2w(sh, np.array([[hx, hy]], float))[0]
    xy = i2w(g[sh]['params'], np.array([[wx, wy]])); lon, lat = to_ll(xy[:, 0], xy[:, 1])
    t = json.load(open(os.path.join(here, f'traced25/{sh}.json')))['buildings']
    d = min(Polygon(b['uv']).buffer(0).distance(Point(wx, wy)) for b in t)
    rows.append(dict(edition=1925, sheet=sh, lon=round(float(lon[0]), 7), lat=round(float(lat[0]), 7), u50=round(float(wx), 1), v50=round(float(wy), 1),
                     name=name, use=use, stories=st, note=note, in_outline='yes' if d == 0 else f'no ({d:.0f} px)'))
for sh, q, x, y, name, use, st, note in R:
    off = (Q305 if sh == '305' else Q)[q]; add(sh, off[0] + x * 1.05, off[1] + y * 1.05, None, None, name, use, st, note)
for sh, x, y, name, use, st, note in H: add(sh, x, y, None, None, name, use, st, note)
for sh, x, y, name, use, st, note in W: add(sh, None, None, x, y, name, use, st, note)
w = csv.DictWriter(open(os.path.join(here, 'named1925.csv'), 'w'), fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), 'names')
