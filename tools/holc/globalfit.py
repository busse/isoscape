"""Coarse step before reading control points: fit the scan to today's street grid as a whole.

    python3 -I globalfit.py <scan.jpg> <osm.json> <georef in.json> <georef out.json>

Today's streets (OpenStreetMap; residential and larger, no service roads, no motorways, which
the 1923 base map lacks) inside the map frame are sampled every 8 m. Starting from the rough
fit, an affine transform is adjusted so that the samples sit as near the printed ink as
possible (mean distance to ink, capped at CAP px on a half-size copy; Powell's method), first
with a wide cap, then a narrow one. This only gives the control-point reader (snapcp.py) a
start within a few meters; the transform used is fitted to the control points (georef.py).
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage, optimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import georef  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
INK = 105
KEEP = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'trunk'}
FRAME = (440, 500, 9390, 7370)


def street_samples(osm, t, step=8.0):
    d = json.load(open(osm))
    pts = []
    for e in d['elements']:
        tg = e.get('tags', {})
        if e['type'] != 'way' or tg.get('highway') not in KEEP or tg.get('bridge') or tg.get('tunnel'):
            continue
        g = [p for p in (e.get('geometry') or []) if p]
        if len(g) < 2:
            continue
        x, y = georef.to_m([p['lon'] for p in g], [p['lat'] for p in g])
        for i in range(len(x) - 1):
            a, b = np.array([x[i], y[i]]), np.array([x[i + 1], y[i + 1]])
            n = max(int(np.hypot(*(b - a)) / step), 1)
            for s in np.linspace(0, 1, n, endpoint=False):
                pts.append(a + (b - a) * s)
    P = np.array(pts)
    return P


def main(scan, osm, gin, gout):
    t0 = json.load(open(gin))['transform']
    gray = np.asarray(Image.open(scan).convert('L'))[::2, ::2]
    P = street_samples(osm, t0)
    uv = georef.inverse(t0, P)
    m = (uv[:, 0] > FRAME[0]) & (uv[:, 0] < FRAME[2]) & (uv[:, 1] > FRAME[1]) & (uv[:, 1] < FRAME[3])
    P = P[m]
    print(len(P), 'street samples in frame')
    dt_full = ndimage.distance_transform_edt(gray >= INK)
    # affine from meters to px (half-size): u = a0 + a1 x + a2 y ; v = b0 + b1 x + b2 y
    A = np.c_[np.ones(len(P)), P]
    p0 = np.r_[np.linalg.lstsq(A, uv[m, 0] / 2, rcond=None)[0], np.linalg.lstsq(A, uv[m, 1] / 2, rcond=None)[0]]
    xs = (P - P.mean(0)) / 1000.0
    An = np.c_[np.ones(len(P)), xs]
    q0 = np.r_[np.linalg.lstsq(An, uv[m, 0] / 2, rcond=None)[0], np.linalg.lstsq(An, uv[m, 1] / 2, rcond=None)[0]]
    H, W = dt_full.shape

    def cost(q, dt):
        u = An @ q[:3]
        v = An @ q[3:]
        ui = np.clip(np.round(u).astype(int), 0, W - 1)
        vi = np.clip(np.round(v).astype(int), 0, H - 1)
        return float(dt[vi, ui].mean())

    q = q0
    for cap in (25.0, 10.0, 5.0, 3.0):
        dt = np.minimum(dt_full, cap)
        print(f'cap {cap}: start {cost(q, dt):.3f}', end=' ')
        r = optimize.minimize(cost, q, args=(dt,), method='Powell', options={'xtol': 1e-3, 'ftol': 1e-5, 'maxfev': 20000})
        q = r.x
        print(f'end {cost(q, dt):.3f}')
    # back to a georef transform (px full-size -> meters), via an exact affine fit on a grid
    gu, gv = np.meshgrid(np.linspace(FRAME[0], FRAME[2], 12), np.linspace(FRAME[1], FRAME[3], 10))
    UV = np.c_[gu.ravel(), gv.ravel()]
    # invert the meters->px affine
    M = np.array([[q[1], q[2]], [q[4], q[5]]]) / 1000.0
    c = np.array([q[0], q[3]]) - M @ P.mean(0)
    XY = np.linalg.solve(M, (UV / 2 - c).T).T
    t = georef.fit(UV, XY, 'affine')
    sx = np.hypot(*np.linalg.inv(M)[:, 0]) / 2
    print(f'meters per px (full size): {sx:.4f}')
    json.dump({'use': 'affine', 'transform': t, 'note': 'globalfit.py: affine fitted to all streets'}, open(gout, 'w'), indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:])
