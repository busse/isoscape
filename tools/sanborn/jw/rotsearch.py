"""rotsearch.py <50% scan> <lon> <lat> <u> <v> <m per full px> <out.json> <sheet> [th0,th1] [--bld]: for a sheet with one
surviving corner: scale from the scale bar, rotation and shift searched so that today's block outlines
(or, with --bld, OSM buildings standing today) land on the sheet's ink. Used for sheet 318, where the
Gilpin Court buildings of 1941-43 still stand."""
# rotsearch.py img50 lon lat u v(full) mpp_full out.json sheet: brute-force rotation (and shift +-24 m) with fixed scale,
# one tie point, scored by today's block outlines + street center lines landing on ink
import json, sys, math
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from geo import to_m, w2i
from ref import blocks
from georef import ink_dt, BLOCKS
img, lon, lat, u, v, mpp = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]) / 2, float(sys.argv[5]) / 2, float(sys.argv[6])
dt = ink_dt(img); H, W = dt.shape
s = 1 / (2 * mpp)
x0, y0 = to_m(lon, lat)
from geo import sample_lines
osm = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'osm-jw.json')))
lines = []
for o in osm:
    if 'building' in o['tags'] and len(o['g']) > 3:
        g = np.array(o['g']); X, Y = to_m(g[:, 0], g[:, 1]); lines.append(np.stack([X, Y], 1))
pts = sample_lines(lines, 1.0) if '--bld' in sys.argv else blocks(BLOCKS, 2.0)
near = pts[np.hypot(pts[:, 0] - x0, pts[:, 1] - y0) < 400]
TH = [float(a) for a in sys.argv[9].split(',')] if len(sys.argv) > 9 and sys.argv[9] != '--bld' else None
best = []
for th in np.radians(np.arange(TH[0], TH[1], 0.5) if TH else np.arange(0, 360, 2.0)):
    c, si = math.cos(th), math.sin(th)
    for dx in range(-24, 25, 3):
        for dy in range(-24, 25, 3):
            # u,v = s R (x, -y) + t ; place tie (x0+dx, y0+dy) at (u, v)
            X, Y = x0 + dx, -(y0 + dy)
            tu = u - s * (c * X - si * Y); tv = v - s * (si * X + c * Y)
            uv = w2i((tu, tv, th, s), near)
            k = (uv[:, 0] > 0) & (uv[:, 0] < W) & (uv[:, 1] > 0) & (uv[:, 1] < H)
            if k.sum() < 300: continue
            cost = ndimage.map_coordinates(dt, [uv[k, 1], uv[k, 0]], order=0).mean()
            best.append((cost, math.degrees(th), dx, dy, (tu, tv, th, s), int(k.sum())))
best.sort(key=lambda r: r[0])
for b in best[:8]: print(round(b[0], 3), round(b[1], 1), b[2], b[3], b[5])
json.dump({sys.argv[8]: {'params': [float(z) for z in best[0][4]], 'how': 'rotsearch'}}, open(sys.argv[7], 'w'))
